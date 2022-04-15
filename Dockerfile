FROM docker.io/mailserver/docker-mailserver:latest
MAINTAINER Cesar Richard <cesar.richard2@gmail.com>

ENV PYTHONUNBUFFERED 1

WORKDIR /srv/gesasso_mkmail
RUN apt-get update && apt-get install -y nano python3 python3-distutils wget --no-install-recommends #&& rm -r /var/lib/apt/lists/*
RUN cd /tmp && wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py

ADD requirements.txt /srv/gesasso_mkmail/
RUN pip install --no-cache-dir -r requirements.txt
ADD . /srv/gesasso_mkmail/
