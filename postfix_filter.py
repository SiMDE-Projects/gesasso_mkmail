#!/usr/bin/python
import base64
import email
import os
import quopri
import re
import sys
import time

import jwt
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import syslog

load_dotenv()


def extractPayload(mail):
    ret = ""
    if mail.is_multipart():
        for payload in mail.get_payload():
            ret += extractPayload(payload)
    elif mail.get_content_type() in ["text/plain", "text/html"]:
        return mail.get_payload(decode=True).decode("utf-8", errors="ignore")
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


try:
    b = email.message_from_file(sys.stdin)
    mail_to = encoded_words_to_text(b["to"])
    mail_from = encoded_words_to_text(b["from"])
    mail_subject = encoded_words_to_text(b["subject"])

    print("From: " + mail_from)
    print("To: " + mail_to)
    print("Subject: " + mail_subject)
    syslog.syslog(f"From: {mail_from} -> To: {mail_to} -> Subject: {mail_subject}")
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
                "body": BeautifulSoup(body, features="html.parser").get_text("\n"),
            },
            key=os.environ.get("PRIVATE_KEY"),
            algorithm="RS256",
        )
        payload = {"token": encoded}
        r = requests.post(os.environ.get("GESASSO_LISTENER_URL"), data=payload)
except Exception as e:
    syslog.syslog(syslog.LOG_ERR, str(e))
finally:
    syslog.syslog("Mail filter finished")
