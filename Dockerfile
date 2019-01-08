FROM python:3.7-alpine3.8

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV LC_LANG=es_ES.UTF-8

LABEL MAINTAINER="Chad Jones <cj@patientsky.com>"

WORKDIR /app

COPY ping.py /app
RUN apk update \
    && apk add \
        iproute2=4.13.0-r0 \
        tzdata=2018f-r0 \
        bash=4.4.19-r1 \
        fping=4.0-r0 \
    && rm  -rf /tmp/* /var/cache/apk/*

## Customize
RUN pip3 install --upgrade pip
RUN pip3 install setuptools==40.4.3
RUN pip3 install \
    pyyaml==3.13 \
    prometheus_client==0.5.0

ENTRYPOINT [ "/app/ping.py" ]