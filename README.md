# docker-collector-logs

docker-collector-logs is a Docker container that uses Filebeat to collect logs from other Docker containers and forward those logs to your Logz.io account.

To use this container, you'll set environment variables in your `docker run` command.
docker-collector-logs uses those environment variables to generate a valid Filebeat configuration for the container.
docker-collector-logs mounts docker.sock and the Docker logs directory to the container itself, allowing Filebeat to collect the logs and metadata.

docker-collector-logs ships logs only.
If you want to ship metrics to Logz.io, see [docker-collector-metrics](https://github.com/logzio/docker-collector-metrics).

**Note:**
- Upgrading to a newer version of a docker-collector-logs while it is already running will cause it to resend logs that are within the `ignoreOlder` timeframe. You can minimize log duplicates by setting the `ignoreOlder` parameter of the new docker to a lower value (for example, `20m`).
- This integration supports **ARM architecture** as of `logzio/docker-collector-logs:0.1.6`.



## docker-collector-logs setup

### 1. Pull the Docker image

Download the logzio/docker-collector-logs image:

```shell
docker pull logzio/docker-collector-logs
```

### 2. Run the container

For a complete list of options, see the parameters below the code block.👇

```shell
docker run --name docker-collector-logs \
--env LOGZIO_TOKEN="<ACCOUNT-TOKEN>" \
-v /var/run/docker.sock:/var/run/docker.sock:ro \
-v /var/lib/docker/containers:/var/lib/docker/containers \
logzio/docker-collector-logs
```

#### Parameters

| Parameter              | Description                                                                                                                                                                                                                                                                                                                                                                                                       |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **LOGZIO_TOKEN**       | **Required**. Your Logz.io account token. Replace `<ACCOUNT-TOKEN>` with the [token](https://app.logz.io/#/dashboard/settings/general) of the account you want to ship to.                                                                                                                                                                                                                                        |
| **LOGZIO_REGION**      | **Default**: US region.<br> Logz.io region code to ship the logs to. This region code changes depending on the region your account is hosted in. For example, accounts in the EU region have region code `eu`.<br /> For more information, see [Account region](https://docs.logz.io/user-guide/accounts/account-region.html) on the Logz.io Docs.                                                                |
| **LOGZIO_TYPE**        | **Default**: Docker image name <br> The log type you'll use with this Docker. This is shown in your logs under the `type` field in Kibana. <br> Logz.io applies parsing based on `type`.                                                                                                                                                                                                                          |
| **LOGZIO_CODEC**       | **Default**: `plain`<br> Set to `json` if shipping JSON logs. Otherwise, set to `plain`.                                                                                                                                                                                                                                                                                                                          |
| **matchContainerName** | Comma-separated list of containers you want to collect the logs from. If a container's name partially matches a name on the list, that container's logs are shipped. Otherwise, its logs are ignored. <br /> **Note**: Can't be used with `skipContainerName`                                                                                                                                                     |
| **skipContainerName**  | Comma-separated list of containers you want to ignore. If a container's name partially matches a name on the list, that container's logs are ignored. Otherwise, its logs are shipped. <br /> **Note**: Can't be used with `matchContainerName`                                                                                                                                                                   |
| **additionalFields**   | Include additional fields with every message sent, formatted as `"fieldName1=fieldValue1;fieldName2=fieldValue2"`. <br /> To use an environment variable, format as `"fieldName1=fieldValue1;fieldName2=$ENV_VAR_NAME"`. In that case, the environment variable should be the only value in the field. In case the environment variable can't be resolved, the field will be omitted.                             |
| **excludeLines**       | Comma-separated list of regular expressions to match the lines that you want Filebeat to exclude. <br /> **Note**: Does not behave well with regular expressions containing commas `,`                                                                                                                                                                                                                            |
| **includeLines**       | Comma-separated list of regular expressions to match the lines that you want Filebeat to include. <br /> **Note**: Does not behave well with regular expressions containing commas `,`                                                                                                                                                                                                                            |
| **ignoreOlder**        | **Default** `3h` <br> Logs older than this will be ignored                                                                                                                                                                                                                                                                                                                                                        |
| **renameFields**       | Rename fields with every message sent, formatted as `"oldName,newName;oldName2,newName2"`. <br /> To use an environment variable, format as `"oldName,newName;oldName2,$ENV_VAR_NAME"`. In that case, the environment variable should be the only value in the field. In case the environment variable can't be resolved, the field will be omitted.                                                              |
| **HOSTNAME**           | **Default** `''` <br> Insert your host name if you want it to appear under the field `agent.name`. If no value entered,  `agent.name` will show the container's id.                                                                                                                                                                                                                                               |
| **multilinePattern**   | **Default** `''` <br> Insert your regex pattern. See [Filebeat's official documentation](https://www.elastic.co/guide/en/beats/filebeat/7.12/multiline-examples.html#multiline) for further info.                                                                                                                                                                                                                 |
| **multilineNegate**    | **Default** `'false'` <br> Insert `'true'` to negate the pattern. <br /> **Note**: Cannot be used without multilinePattern. See [Filebeat's official documentation](https://www.elastic.co/guide/en/beats/filebeat/7.12/multiline-examples.html#multiline) for further info.                                                                                                                                      |
| **multilineMatch**     | **Default** `'after'` <br>  Specifies how Filebeat combines matching lines into an event. The settings are `after` or `before`. The behavior of these settings depends on what you specify for negate. <br /> **Note**: Cannot be used without multilinePattern. See [Filebeat's official documentation](https://www.elastic.co/guide/en/beats/filebeat/7.12/multiline-examples.html#multiline) for further info. |
| **LOG_LEVEL**          | **Default** `info`. Set log level for the collector. Allowed values are: `debug`, `info`, `warning`, `error`.                                                                                                                                                                                                                                                                                                     |


**Note**: By default, logs from `docker-collector-logs` and `docker-collector-metrics` containers are ignored.

### 3. Check Logz.io for your logs

Spin up your Docker containers if you haven’t done so already. Give your logs a few minutes to get from your system to ours, and then open [Kibana](https://app.logz.io/#/dashboard/kibana).

### Change log

- 0.3.0:
  - Upgrade to Filebeat 8.3.3.
- 0.2.0:
  - Allow changing log level.
  - Upgrade base image to python 3.11.
- 0.1.6:
    Support ARM architecture.
- 0.1.5:
    Added rename processors.
- 0.1.4:
    - **BREAKING CHANGES**:
        - Upgrade to Filebeat 7.12.1.
    - Added multiline variables for support of multiline patterns.
- 0.1.3: Processors were moved to root level of the yml to allow rename of filebeat metadata fields.
- 0.1.2: Add rename processor ("renameFields") to specify a list of fields to rename.
- 0.1.1: Fixed script to match Filebeat 7.9 changes.
- 0.1.0:
    - **BREAKING CHANGES**:
        - Upgrade to Filebeat 7.9.0.
        - Deprecated `LOGZIO_URL`. Use `LOGZIO_REGION` instead.
    - Update default_filebeat.yml configuration to match newer Filebeat version.
    - Support adding hostname.
- 0.0.6: Updated new public SSL certificate in Docker image & Filebeat configuration.
- 0.0.4: Added options to include or exclude lines
- 0.0.3: Support additional fields
- 0.0.2: Add an option to configure logzio_codec and logzio_type
