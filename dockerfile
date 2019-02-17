FROM python:3.7-slim

COPY requirements.txt ./requirements.txt

RUN apt-get update && \
    apt-get install -y \
    curl \
    wget && \
    curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-6.5.4-amd64.deb && \
    dpkg -i filebeat-6.5.4-amd64.deb && \
    rm filebeat-6.5.4-amd64.deb && \
    wget https://raw.githubusercontent.com/logzio/public-certificates/master/COMODORSADomainValidationSecureServerCA.crt && \
    mkdir -p /etc/pki/tls/certs && \
    cp COMODORSADomainValidationSecureServerCA.crt /etc/pki/tls/certs/ && \
    rm COMODORSADomainValidationSecureServerCA.crt && \
    pip install -r requirements.txt && \
    rm requirements.txt

COPY default_filebeat.yml ./default_filebeat.yml
COPY filebeat-yml-script.py ./filebeat-yml-script.py

CMD ["python","filebeat-yml-script.py"]
