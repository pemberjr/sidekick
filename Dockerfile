FROM openjdk:11
FROM python:3.6
FROM oraclelinux:7-slim

ENV HTTP_PROXY="http://proxy.sce.com:80"
ENV HTTPS_PROXY="http://proxy.sce.com:80"

RUN yum -y install oraclelinux-developer-release-el7 oracle-instantclient-release-el7 && \
    yum -y install python3 \
            python3-libs \
            python3-pip \
            python3-setuptools \
            python36-cx_Oracle && \
    rm -rf /var/cache/yum/*

RUN yum -y install expect && \
    yum -y install install openssh-clients && \
    yum -y install java-1.8.0-openjdk

WORKDIR /sidekick

COPY . .

RUN pip3 install -r requirements.txt

EXPOSE 5051

CMD ["python3", "./src/app.py", "5051"]
