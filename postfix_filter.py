#!/usr/bin/python3
try:
    import base64
    import email
    import logging
    import os
    import quopri
    import re
    import sys
    import syslog
    import time
    from subprocess import Popen, PIPE

    import jwt
    import requests
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        filename="/tmp/gesasso-mkmail-filter.log",
        filemode="a",
    )
except Exception as e:
    syslog.syslog(syslog.LOG_ERR, str(e))
    print(str(e), file=sys.stderr)
    sys.exit(75)  # EX_TEMPFAIL


def reinjectMail(mail):
    newMail = mail.as_bytes()
    command = ["/usr/sbin/sendmail", "-G", "-i", "-f", mail["from"], mail["to"]]
    process = Popen(command, stdin=PIPE)
    (stdout, stderr) = process.communicate(newMail)
    retval = process.wait()
    if retval == 0:
        logging.debug(
            "Mail resent via sendmail, stdout: %s, stderr: %s" % (stdout, stderr)
        )
        sys.exit(0)
    else:
        raise Exception("retval not zero - %s" % retval)


def extractMultipartPayload(mail):
    ret = {"text": "", "attachements": []}
    if mail.is_multipart():
        for payload in mail.get_payload():
            extracted = extractMultipartPayload(payload)
            ret["text"] += extracted["text"]
            ret["attachements"].extend(extracted["attachements"])
    elif mail.get_content_type() in ["text/plain", "text/html"]:
        content = mail.get_payload(decode=True).decode("utf-8", errors="replace")
        ret["text"] += content
    else:
        attachement = {
            "name": mail.get_filename(),
            "content": mail.get_payload(),
            "type": mail.get_content_type(),
        }
        ret["attachements"].append(attachement)
    return ret


def encoded_words_to_text(encoded_words):
    encoded_word_regex = r"=\?{1}(.+)\?{1}([B|Q])\?{1}(.+)\?{1}=(.*)"
    byte_string = ""
    match = re.match(encoded_word_regex, encoded_words)
    if match:
        charset, encoding, encoded_text, next = match.groups()
        if encoding == "B":
            byte_string = base64.b64decode(encoded_text)
        elif encoding == "Q":
            byte_string = quopri.decodestring(encoded_text)
        return byte_string.decode(charset) + next
    return encoded_words.encode("utf-8", errors="replace").decode("utf-8")


def is_simde_email(mail):
    if os.environ.get("HANDLE_ALL_MAILS", "False").lower() in ("true", "1", "t"):
        return True
    return "assos.utc.fr" in mail and (
        mail.startswith("simde")
        or mail.startswith("payutc")
        or mail.startswith("woolly")
    )


def main():
    try:
        b = email.message_from_file(sys.stdin)
        mail_to = encoded_words_to_text(b["to"])
        mail_from = encoded_words_to_text(b["from"])
        mail_subject = encoded_words_to_text(b["subject"])

        syslog.syslog(
            "From: {} -> To: {} -> Subject: {}".format(
                mail_from,
                mail_to,
                mail_subject,
            )
        )
        if is_simde_email(mail_to):
            body = extractMultipartPayload(b)
            encoded = jwt.encode(
                payload={
                    "iss": "MK_MAIL",
                    "aud": "MK_ULTRA",
                    "iat": int(time.time()),
                    "subject": mail_subject,
                    "from": mail_from,
                    "to": mail_to,
                    "body": BeautifulSoup(
                        body["text"], features="html.parser"
                    ).get_text(),
                    "attachements": body["attachements"],
                },
                key=os.environ.get("PRIVATE_KEY"),
                algorithm="RS256",
            )
            payload = {"token": encoded}
            r = requests.post(os.environ.get("GESASSO_LISTENER_URL"), data=payload)
            ret = r.json()
            if "[GAR_{}]".format(ret["id"]) not in mail_subject:
                del b["subject"]
                b["subject"] = "[GAR_{}]".format(ret["id"]) + mail_subject
        reinjectMail(b)
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, str(e))
        print(str(e), file=sys.stderr)
        sys.exit(75)  # EX_TEMPFAIL
    finally:
        syslog.syslog("Mail filter finished")


if __name__ == "__main__":
    main()
