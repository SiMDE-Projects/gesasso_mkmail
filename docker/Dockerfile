FROM docker.io/mailserver/docker-mailserver:latest
MAINTAINER Cesar Richard <cesar.richard2@gmail.com>

ENV PYTHONUNBUFFERED 1

WORKDIR /srv/gesasso_mkmail
RUN apt-get update && apt-get install -y nano python3 python3-distutils wget --no-install-recommends #&& rm -r /var/lib/apt/lists/*
RUN cd /tmp && wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py && rm -r /tmp/get-pip.py

ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ADD ./docker/config/postfix-accounts.cf /tmp/docker-mailserver/
ADD ./docker/config/postfix-aliases.cf /tmp/docker-mailserver/
ADD ./docker/config/postfix-master.cf /tmp/docker-mailserver/
ADD ./docker/config/postfix-virtual.cf /tmp/docker-mailserver/
ADD ./docker/config/master.cf /etc/postfix/master.cf
ADD ./test_postfix_filter.py /srv/gesasso_mkmail/
ADD ./postfix_filter.py /srv/gesasso_mkmail/
