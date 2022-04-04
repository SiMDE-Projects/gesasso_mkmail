#!/usr/bin/python3
import email
import sys

f = open("/tmp/postfixtest1", "a")
b = email.message_from_file(sys.stdin)
if b["subject"].contains("[GAR_"):
    f.write("\nET NOUS AVONS UN VAINCEUR\n")

body = ""
if b.is_multipart():
    for payload in b.get_payload():
        # if payload.is_multipart(): ...
        body += payload.get_payload()
else:
    body = b.get_payload()
f.write(str(body))
f.write("\n")
f.close()
