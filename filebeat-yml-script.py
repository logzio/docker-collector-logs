import logging
import os
from ruamel.yaml import YAML
import socket

# set vars and consts

logzio_url = os.environ["LOGZIO_URL"]
logzio_url_arr = logzio_url.split(":")
logzio_token = os.environ["LOGZIO_TOKEN"]

HOST = logzio_url_arr[0]
PORT = int(logzio_url_arr[1])
FILEBEAT_CONF_PATH = "/etc/filebeat/filebeat.yml"
SOCKET_TIMEOUT = 3

logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(message)s', level=logging.DEBUG)


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
    with open("default_filebeat.yml") as default_filebeat_yml:
        config_dic = yaml.load(default_filebeat_yml)

    config_dic["output"]["logstash"]["hosts"].append(logzio_url)
    config_dic["filebeat.inputs"][0]["fields"]["token"] = logzio_token

    with open(FILEBEAT_CONF_PATH, "w+") as filebeat_yml:
        yaml.dump(config_dic, filebeat_yml)


def _exclude_containers():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    try:
        exclude_list = ["filebeat"] + os.environ["skipContainerName"].split(",")
    except KeyError:
        exclude_list = ["filebeat"]

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

    include_list = os.environ["matchContainerName"].split(",")
    drop_event = {"drop_event": {"when": {"and": []}}}
    config_dic["filebeat.inputs"][0]["processors"].append(drop_event)

    for container_name in include_list:
        contains = {"not":{"contains": {"docker.container.name": container_name}}}
        config_dic["filebeat.inputs"][0]["processors"][1]["drop_event"]["when"]["and"].append(contains)

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


_is_open()
_add_shipping_data()

if "matchContainerName" in os.environ and "skipContainerName" in os.environ:
    logging.error("Can have only one of skipContainerName or matchContainerName")
    raise KeyError
elif "matchContainerName" in os.environ:
    _include_containers()
elif "skipContainerName" in os.environ:
    _exclude_containers()

os.system("filebeat -e")
