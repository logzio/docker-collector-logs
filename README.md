# docker-collector-logs

This forwards your docker logs to your [Logz.io](https://app.logz.io/) account using a filebeat container.
With this collector you can also exclude or include certain containers.
You can also ship docker metrics with our [Docker-collector-metrics](https://github.com/logzio/docker-collector-metrics).  
*This docker collector excludes filebeat logs by default*

## How to use the docker collector

To run the docker collector use this command:  
```
docker run --name filebeat-docker-collector --env LOGZIO_TOKEN="{{LOGZIO_TOKEN}}" --env LOGZIO_URL="listener.logz.io:5015" -v /var/run/docker.sock:/var/run/docker.sock:ro -v /var/lib/docker/containers:/var/lib/docker/containers logzio/docker-collector-logs
```
*Change the {{LOGZIO_TOKEN}} to your shipping token*  
*If your account is in the eu region change the LOGZIO_URL enviorenment variable to listener-eu.logz.io:5015*

### Supported enviornment variable

- LOGZIO_TOKEN - your logz.io shipping token
- LOGZIO_URL - either listener-eu.logz.io:5015 or listener.logz.io:5015
- matchContainerName (optional)- a comma separated list of the **only** containers you want the collector to collect the logs from
- skipConatinerName (optional) - a comma separated list of containers you want to exclude
*Only one of match or skip container name can be used*  
*The filtering is done based on a contain operator so you can match part of a value,i.e skipContainerName = "apache,nginx" will skip logs from any container that it's name contains apache or nginx*  


### Examples of possible commands

Shipping logs from containers that their name contains "apache" or "nginx"
```
docker run --name filebeat-docker-collector --env LOGZIO_TOKEN="{{LOGZIO_TOKEN}}" --env LOGZIO_URL="listener.logz.io:5015" --env matchContainerName="nginx, apache" -v /var/run/docker.sock:/var/run/docker.sock:ro -v /var/lib/docker/containers:/var/lib/docker/containers logzio/docker-collector-logs
```

Shipping logs from all containers except containers that their name contains "jenkins"
```
docker run --name filebeat-docker-collector --env LOGZIO_TOKEN="{{LOGZIO_TOKEN}}" --env LOGZIO_URL="listener.logz.io:5015" --env skipContainerName="jenkins" -v /var/run/docker.sock:/var/run/docker.sock:ro -v /var/lib/docker/containers:/var/lib/docker/containers logzio/docker-collector-logs
```
## How it works
This docker container is using a python script to generate a valid filebeat configuration file based on your enviornment variables, and then starts the service.  
The container mounts the docker sock the docker logs to the docker collector container itself so filebeat will be able to collect the logs and the metadata.
