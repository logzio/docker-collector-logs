# docker-collector-logs

docker-collector-logs is a Docker container that uses Filebeat to collect logs from other Docker containers and forward those logs to your Logz.io account.

To use this container, you'll set environment variables in your `docker run` command.
docker-collector-logs uses those environment variables to generate a valid Filebeat configuration for the container.
docker-collector-logs mounts docker.sock and the Docker logs directory to the container itself, allowing Filebeat to collect the logs and metadata.

docker-collector-logs ships logs only.
If you want to ship metrics to Logz.io, see [docker-collector-metrics](https://github.com/logzio/docker-collector-metrics).


## docker-collector-logs setup

### 1. Pull the Docker image

Download the logzio/docker-collector-logs image:

```shell
docker pull logzio/docker-collector-logs
```

### 2. Run the Docker image

For a complete list of options, see the parameters below the code block.👇

```shell
docker run logzio/docker-collector-logs
--name docker-collector-logs \
--env LOGZIO_TOKEN="<ACCOUNT-TOKEN>" \
--env LOGZIO_URL="<LISTENER-URL>:5015" \
-v /var/run/docker.sock:/var/run/docker.sock:ro \
-v /var/lib/docker/containers:/var/lib/docker/containers \
```

#### Parameters

| Parameter | Description |
|---|---|
| **LOGZIO_TOKEN** | **Required**. Your Logz.io account token. Replace `<ACCOUNT-TOKEN>` with the [token](https://app.logz.io/#/dashboard/settings/general) of the account you want to ship to. |
| **LOGZIO_URL** | **Required**. Logz.io listener URL to ship the logs to. This URL changes depending on the region your account is hosted in. For example, accounts in the US region ship to `listener.logz.io`, and accounts in the EU region ship to `listener-eu.logz.io`. <br /> For more information, see [Account region](https://docs.logz.io/user-guide/accounts/account-region.html) on the Logz.io Docs. |
| **matchContainerName** | Comma-separated list of containers you want to collect the logs from. If a container's name partially matches a name on the list, that container's logs are shipped. Otherwise, its logs are ignored. <br /> **Note**: Can't be used with `skipContainerName` |
| **skipContainerName** | Comma-separated list of containers you want to ignore. If a container's name partially matches a name on the list, that container's logs are ignored. Otherwise, its logs are shipped. <br /> **Note**: Can't be used with `matchContainerName` |

**Note**: By default, logs from `docker-collector-logs` and `docker-collector-metrics` containers are ignored.

### 3. Check Logz.io for your logs

Spin up your Docker containers if you haven’t done so already. Give your logs a few minutes to get from your system to ours, and then open [Kibana](https://app.logz.io/#/dashboard/kibana).