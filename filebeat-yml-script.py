import logging
import os
from ruamel.yaml import YAML
import socket

logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(message)s', level=logging.DEBUG)

# set vars and consts
logzio_url = os.environ["LOGZIO_URL"]
logzio_url_arr = logzio_url.split(":")
logzio_token = os.environ["LOGZIO_TOKEN"]
logzio_type = os.getenv("LOGZIO_TYPE", "docker-collector-logs")

logzio_codec = os.getenv("LOGZIO_CODEC", "plain").lower()
logzio_codec_list = ["plain", "json"]
if logzio_codec not in logzio_codec_list:
    logging.warning(f"LOGZIO_CODEC={logzio_codec} not supported. Make sure you use one of following: "
                    f"{logzio_codec_list}. Falling back to default LOGZIO_CODEC=plain")
    logzio_codec = "plain"


HOST = logzio_url_arr[0]
PORT = int(logzio_url_arr[1])
FILEBEAT_CONF_PATH = f"{os.getcwd()}/filebeat.yml"
SOCKET_TIMEOUT = 3
FIRST_CHAR = 0


def _is_open():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOCKET_TIMEOUT)

    result = sock.connect_ex((HOST, PORT))
    if result == 0:
        logging.info("Connection Established")
    else:
        logging.error("Can't connect to the listener, "
                      "please remove any firewall settings to host:{} port:{}".format(HOST, str(PORT)))
        raise ConnectionError


def _add_shipping_data():
    yaml = YAML()
    with open("docker-colletor-logs/default_filebeat.yml") as default_filebeat_yml:
        config_dic = yaml.load(default_filebeat_yml)

    config_dic["output"]["logstash"]["hosts"].append(logzio_url)
    config_dic["filebeat.inputs"][0]["fields"] = {}
    config_dic["filebeat.inputs"][0]["fields"]["token"] = logzio_token
    config_dic["filebeat.inputs"][0]["fields"]["logzio_codec"] = logzio_codec
    config_dic["filebeat.inputs"][0]["fields"]["type"] = logzio_type
    config_dic["filebeat.inputs"][0]["ignore_older"] = _get_ignore_older()

    additional_field = _get_additional_fields()
    for key in additional_field:
        config_dic["filebeat.inputs"][0]["fields"][key] = additional_field[key]

    with open(FILEBEAT_CONF_PATH, "w+") as filebeat_yml:
        yaml.dump(config_dic, filebeat_yml)


def _get_ignore_older():
    return os.getenv("ignoreOlder", "3h")


def _get_additional_fields():
    try:
        additional_fields = os.environ["additionalFields"]
    except KeyError:
        return {}

    fields = {}
    filtered = dict(parse_entry(entry) for entry in additional_fields.split(";"))

    for key, value in filtered.items():
        if value[FIRST_CHAR] == '$':
            try:
                fields[key] = os.environ[value[FIRST_CHAR+1:]]
            except KeyError:
                continue
        else:
            fields[key] = value

    return fields


def parse_entry(entry):
    try:
        key, value = entry.split("=")
    except ValueError:
        raise ValueError("Failed to parse entry: {}".format(entry))

    if key == '' or value == '':
        raise ValueError("Failed to parse entry: {}".format(entry))
    return key, value


def _exclude_containers():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    try:
        exclude_list = ["docker-collector"] + [container.strip() for container in os.environ["skipContainerName"].split(",")]
    except KeyError:
        exclude_list = ["docker-collector"]

    drop_event = {"drop_event": {"when": {"or": []}}}
    config_dic["filebeat.inputs"][0]["processors"].append(drop_event)

    for container_name in exclude_list:
        contains = {"contains": {"docker.container.name": container_name}}
        config_dic["filebeat.inputs"][0]["processors"][1]["drop_event"]["when"]["or"].append(contains)

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


def _include_containers():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yml:
        config_dic = yaml.load(filebeat_yml)

    include_list = [container.strip() for container in os.environ["matchContainerName"].split(",")]

    drop_event = {"drop_event": {"when": {"and": []}}}
    config_dic["filebeat.inputs"][0]["processors"].append(drop_event)

    for container_name in include_list:
        contains = {"not":{"contains": {"docker.container.name": container_name}}}
        config_dic["filebeat.inputs"][0]["processors"][1]["drop_event"]["when"]["and"].append(contains)

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


def _exclude_lines():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    regexes = [expr.strip() for expr in os.environ["excludeLines"].split(',')]
    config_dic["filebeat.inputs"][0]["exclude_lines"] = regexes

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)

        
def _include_lines():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    regexes = [expr.strip() for expr in os.environ["includeLines"].split(',')]
    config_dic["filebeat.inputs"][0]["include_lines"] = regexes

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)

        
_is_open()
_add_shipping_data()

if "matchContainerName" in os.environ and "skipContainerName" in os.environ:
    logging.error("Can have only one of skipContainerName or matchContainerName")
    raise KeyError
elif "matchContainerName" in os.environ:
    _include_containers()
else:
    _exclude_containers()

if "excludeLines" in os.environ:
    _exclude_lines()

if "includeLines" in os.environ:
    _include_lines()

os.system(f"{os.getcwd()}/filebeat -e -c {FILEBEAT_CONF_PATH}")
