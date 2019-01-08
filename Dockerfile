FROM debian:stretch-slim

LABEL MAINTAINER="Chad Jones <cj@patientsky.com>"

WORKDIR /app

COPY ping.py /app

RUN apt-get -qq update \
    && apt-get -yqq upgrade \
    && apt-get -yqq install \
        iproute2 \
        python-pip \
        python-yaml \
        fping \
    && pip install prometheus-client

ENTRYPOINT [ "/app/ping.py" ]