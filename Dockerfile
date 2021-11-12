FROM python:3.11.0a2-alpine

ENV PACKAGE=filebeat-7.12.1-linux-x86_64.tar.gz


RUN mkdir -p /opt/filebeat/docker-colletor-logs && \
    mkdir -p /etc/pki/tls/certs

WORKDIR /opt/filebeat

COPY requirements.txt docker-collector-logs/requirements.txt
COPY default_filebeat.yml docker-collector-logs/default_filebeat.yml
COPY filebeat-yml-script.py docker-collector-logs/filebeat-yml-script.py

RUN apk add --update --no-cache libc6-compat wget tar && \
    wget https://artifacts.elastic.co/downloads/beats/filebeat/$PACKAGE && \
    tar --strip-components=1 -zxf /opt/filebeat/"$PACKAGE" && \
    rm -f "$PACKAGE" && \
    wget -P /etc/pki/tls/certs/ https://raw.githubusercontent.com/logzio/public-certificates/master/SectigoRSADomainValidationSecureServerCA.crt && \
    pip3 install -r ./docker-collector-logs/requirements.txt --user && \
    rm -f ./docker-collector-logs/requirements.txt

CMD [ "python3", "docker-collector-logs/filebeat-yml-script.py" ]
