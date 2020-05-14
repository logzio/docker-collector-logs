FROM python:3.7-alpine

ENV PACKAGE=filebeat-6.5.4-linux-x86_64.tar.gz


RUN mkdir -p /opt/filebeat/docker-colletor-logs && \
    mkdir -p /etc/pki/tls/certs

WORKDIR /opt/filebeat

COPY requirements.txt docker-colletor-logs/requirements.txt
COPY default_filebeat.yml docker-colletor-logs/default_filebeat.yml
COPY filebeat-yml-script.py docker-colletor-logs/filebeat-yml-script.py

RUN apk add --update --no-cache libc6-compat wget tar && \
    wget https://artifacts.elastic.co/downloads/beats/filebeat/$PACKAGE && \
    tar --strip-components=1 -zxf /opt/filebeat/"$PACKAGE" && \
    rm -f "$PACKAGE" && \
    wget -P /etc/pki/tls/certs/ https://raw.githubusercontent.com/logzio/public-certificates/master/TrustExternalCARoot_and_USERTrustRSAAAACA.crt && \
    pip3 install -r ./docker-colletor-logs/requirements.txt --user && \
    rm -f ./docker-colletor-logs/requirements.txt

CMD [ "python3", "docker-colletor-logs/filebeat-yml-script.py" ]
