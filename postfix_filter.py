#!/usr/bin/python3
import email
import os
import sys
import jwt
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

b = email.message_from_file(sys.stdin)
body = ""
if b.is_multipart():
    for payload in b.get_payload():
        body += payload.get_payload()
else:
    body = b.get_payload()
encoded = jwt.encode(
    {
        "subject": b["subject"],
        "from": b["from"],
        "to": b["to"],
        "body": BeautifulSoup(body, features="html.parser").get_text("\n"),
    },
    os.environ.get("PRIVATE_KEY"),
    algorithm="RS256",
)
payload = {"agent": "MK_MAIL", "token": encoded}
requests.post(os.environ.get("GESASSO_LISTENER_URL"), data=payload)
