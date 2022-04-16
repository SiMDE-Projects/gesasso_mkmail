#!/usr/bin/python3
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


def extractPayload(mail):
    ret = ""
    if mail.is_multipart():
        for payload in mail.get_payload():
            ret += extractPayload(payload)
    elif mail.get_content_type() in ["text/plain", "text/html"]:
        return "\n[{}]\n{}\n\n----------".format(
            mail.get_content_type(),
            mail.get_payload(decode=True),
        )
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
    return encoded_words


def main():
    try:
        b = email.message_from_file(sys.stdin)
        mail_to = str(encoded_words_to_text(b["to"]).encode("utf-8", errors="replace"))
        mail_from = str(
            encoded_words_to_text(b["from"]).encode("utf-8", errors="replace")
        )
        mail_subject = str(
            encoded_words_to_text(b["subject"]).encode("utf-8", errors="replace")
        )
        syslog.syslog(
            "From: {} -> To: {} -> Subject: {}".format(
                mail_from,
                mail_to,
                mail_subject,
            )
        )
        logging.info(
            "From: {} -> To: {} -> Subject: {}".format(
                mail_from,
                mail_to,
                mail_subject,
            )
        )
        if "assos.utc.fr" in mail_to and (
            "simde" in mail_to or "payutc" in mail_to or "zapputc" in mail_to
        ):
            body = extractPayload(b)
            encoded = jwt.encode(
                payload={
                    "iss": "MK_MAIL",
                    "aud": "MK_ULTRA",
                    "iat": int(time.time()),
                    "subject": mail_subject,
                    "from": mail_from,
                    "to": mail_to,
                    "body": BeautifulSoup(body, features="html.parser").get_text(),
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
        sys.exit(75)  # EX_TEMPFAIL
    finally:
        syslog.syslog("Mail filter finished")


if __name__ == "__main__":
    main()
