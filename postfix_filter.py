#!/usr/bin/python3
import sys
import fileinput
import email
f = open("/tmp/postfixtest1", "a")
#f.write("The arguments are: {}\n\n".format(str(sys.argv)))
#for line in sys.stdin.readlines():
#    f.write(line)
b = email.message_from_file(sys.stdin)
#f.write(b['subject'])
f.write('\n')
body = ""

if b.is_multipart():
    for payload in b.get_payload():
        # if payload.is_multipart(): ...
        body = payload.get_payload()
else:
    body = b.get_payload()
f.write(str(body))
f.write('\n')
f.close()
