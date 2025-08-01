import logging
import os
import socket
from ruamel.yaml import YAML


def get_log_level():
    default_level = "info"
    log_level_from_user = os.getenv("LOG_LEVEL", default_level).lower()
    levels_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }

    if log_level_from_user not in levels_map:
        log_level_from_user = default_level

    return log_level_from_user, levels_map[log_level_from_user]


# set vars and consts
LOGZIO_LISTENER_ADDRESS = "listener.logz.io:5015"
PROCESSORS_AVAILABLE_INDEX = 3
FILEBEAT_INPUT_FIELD = "filebeat.inputs"
FILEBEAT_PARSER_FIELD = "parsers"
FILEBEAT_PROCESSORS_FIELD = "processors"
DEFAULT_CONTAINER_NAME = "docker-collector-logs"

logzio_url = LOGZIO_LISTENER_ADDRESS
log_level_filebeat, log_level_logger = get_log_level()
logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(message)s', level=log_level_logger)
logzio_url_arr = logzio_url.split(":")
logzio_token = os.getenv("LOGZIO_TOKEN")
if not logzio_token:
    logging.error("LOGZIO_TOKEN is not set")
    raise ValueError("LOGZIO_TOKEN is not set")
logzio_type = os.getenv("LOGZIO_TYPE", "docker-collector-logs")
logzio_region = os.getenv("LOGZIO_REGION", "")
logzio_codec = os.getenv("LOGZIO_CODEC", "plain").lower()
logzio_codec_list = ["plain", "json"]
input_encoding = os.getenv("INPUT_ENCODING", "utf-8").lower()
disable_default_drop_events = os.getenv("DISABLE_DEFAULT_DROP_EVENTS", "false").lower()
if logzio_codec not in logzio_codec_list:
    logging.warning(f"LOGZIO_CODEC={logzio_codec} not supported. Make sure you use one of following: "
                    f"{logzio_codec_list}. Falling back to default LOGZIO_CODEC=plain")
    logzio_codec = "plain"

FILEBEAT_CONF_PATH = f"{os.getcwd()}/filebeat.yml"
SOCKET_TIMEOUT = 3
FIRST_CHAR = 0


def get_listener_url(region):
    return LOGZIO_LISTENER_ADDRESS.replace("listener.", "listener{}.".format(get_region_code(region)))


def get_region_code(region):
    if region != "us" and region != "":
        return "-{}".format(region)
    return ""


def _set_url():
    global logzio_url
    global logzio_url_arr
    region = ""
    is_region = False
    if 'LOGZIO_REGION' in os.environ:
        region = os.environ['LOGZIO_REGION']
        is_region = True
        if 'LOGZIO_URL' in os.environ:
            logging.warning("Both LOGZIO_REGION and LOGZIO_URL were entered! Using LOGZIO_REGION.")
    else:
        if 'LOGZIO_URL' in os.environ and os.environ['LOGZIO_URL'] != "":
            logzio_url = os.environ['LOGZIO_URL']
            logging.warning("Please note that LOGZIO_URL is deprecated! In future versions use LOGZIO_REGION.")
        else:
            is_region = True

    if is_region:
        logzio_url = get_listener_url(region)
    logzio_url_arr = logzio_url.split(":")


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
    _validate_encoding()
    with open("docker-collector-logs/default_filebeat.yml") as default_filebeat_yml:
        config_dic = yaml.load(default_filebeat_yml)

    config_dic["output"]["logstash"]["hosts"].append(logzio_url)
    config_dic[FILEBEAT_INPUT_FIELD][0]["fields"] = {}
    config_dic[FILEBEAT_INPUT_FIELD][0]["fields"]["token"] = logzio_token
    config_dic[FILEBEAT_INPUT_FIELD][0]["fields"]["logzio_codec"] = logzio_codec
    config_dic[FILEBEAT_INPUT_FIELD][0]["fields"]["type"] = logzio_type
    config_dic[FILEBEAT_INPUT_FIELD][0]["ignore_older"] = _get_ignore_older()
    config_dic[FILEBEAT_INPUT_FIELD][0]["encoding"] = input_encoding
    config_dic["logging.level"] = log_level_filebeat

    hostname = _get_host_name()
    if hostname != '':
        config_dic["name"] = hostname

    additional_field = _get_additional_fields()
    for key in additional_field:
        config_dic[FILEBEAT_INPUT_FIELD][0]["fields"][key] = additional_field[key]

    with open(FILEBEAT_CONF_PATH, "w+") as filebeat_yml:
        yaml.dump(config_dic, filebeat_yml)


def _get_ignore_older():
    return os.getenv("ignoreOlder", "3h")


def _get_multiline_type():
    return os.getenv("multilineType", 'pattern')


def _get_multiline_pattern():
    return os.getenv("multilinePattern", '')


def _get_multiline_negate():
    return os.getenv("multilineNegate", 'false')


def _get_multiline_match():
    return os.getenv("multilineMatch", 'after')


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
                fields[key] = os.environ[value[FIRST_CHAR + 1:]]
            except KeyError:
                continue
        else:
            fields[key] = value

    return fields


def _add_rename_fields():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    fields = []
    for entry in os.environ["renameFields"].split(";"):
        fields.append(get_rename_field(entry, ","))

    rename_fields = {"rename": {"fields": fields}}
    config_dic[FILEBEAT_PROCESSORS_FIELD].append(rename_fields)

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


def get_rename_field(entry, delimiter):
    try:
        old_key, new_key = entry.split(delimiter)
    except ValueError:
        raise ValueError(
            "Your 'renameField' format isn't correct please check in the documentation for the right format: {}".format(
                entry))

    if old_key == '' or new_key == '':
        raise ValueError(
            "Your 'renameField' format isn't correct please check in the documentation for the right format: {}".format(
                entry))

    return {"from": old_key, "to": new_key}


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

    base_exclude_list = []
    if disable_default_drop_events == "false":
        base_exclude_list = [DEFAULT_CONTAINER_NAME]

    try:
        exclude_list = base_exclude_list + [container.strip() for container in
                                               os.environ["skipContainerName"].split(",")]
    except KeyError:
        exclude_list = base_exclude_list

    if exclude_list:
        drop_event = {"drop_event": {"when": {"or": []}}}

        for container_name in exclude_list:
            contains = {"contains": {"container.name": container_name}}
            drop_event["drop_event"]["when"]["or"].append(contains)
        config_dic[FILEBEAT_PROCESSORS_FIELD].append(drop_event)

        with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
            yaml.dump(config_dic, updated_filebeat_yml)


def _include_containers():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yml:
        config_dic = yaml.load(filebeat_yml)

    include_list = [container.strip() for container in os.environ["matchContainerName"].split(",")]

    drop_event = {"drop_event": {"when": {"and": []}}}
    config_dic[FILEBEAT_PROCESSORS_FIELD].append(drop_event)

    for container_name in include_list:
        contains = {"not":{"contains": {"container.name": container_name}}}
        config_dic[FILEBEAT_PROCESSORS_FIELD][PROCESSORS_AVAILABLE_INDEX]["drop_event"]["when"]["and"].append(contains)

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


def _exclude_lines():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    regexes = [expr.strip() for expr in os.environ["excludeLines"].split(',')]
    config_dic[FILEBEAT_INPUT_FIELD][0]["exclude_lines"] = regexes

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


def _include_lines():
    yaml = YAML()
    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    regexes = [expr.strip() for expr in os.environ["includeLines"].split(',')]
    config_dic[FILEBEAT_INPUT_FIELD][0]["include_lines"] = regexes

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


def _add_multiline_type():
    yaml = YAML()
    yaml.preserve_quotes = True

    with open(FILEBEAT_CONF_PATH) as filebeat_yaml:
        config_dic = yaml.load(filebeat_yaml)

    multiline_conf = {
        "multiline": {
            "type": _get_multiline_type(),
            "pattern": _get_multiline_pattern(),
            "negate": _get_multiline_negate(),
            "match": _get_multiline_match()
        }
    }
    config_dic[FILEBEAT_INPUT_FIELD][0][FILEBEAT_PARSER_FIELD].append(multiline_conf)

    with open(FILEBEAT_CONF_PATH, "w+") as updated_filebeat_yml:
        yaml.dump(config_dic, updated_filebeat_yml)


def _get_host_name():
    return os.getenv("HOSTNAME", '')


def _validate_encoding():
    global input_encoding
    # According to https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-input-container.html#_encoding
    valid_encodings = ["plain", "utf-8", "utf8", "gbk", "iso8859-6e", "iso8859-6i", "iso8859-8e", "iso8859-8i",
                       "iso8859-1", "iso8859-2", "iso8859-3", "iso8859-4", "iso8859-5", "iso8859-6", "iso8859-7",
                       "iso8859-8", "iso8859-9", "iso8859-10", "iso8859-13", "iso8859-14", "iso8859-15", "iso8859-16",
                       "cp437", "cp850", "cp852", "cp855", "cp858", "cp860", "cp862", "cp863", "cp865", "cp866",
                       "ebcdic-037", "ebcdic-1040", "ebcdic-1047", "koi8r", "koi8u", "macintosh", "macintosh-cyrillic",
                       "windows1250", "windows1251", "windows1252", "windows1253", "windows1254", "windows1255",
                       "windows1256", "windows1257", "windows1258", "windows874", "utf-16-bom", "utf-16be-bom",
                       "utf-16le-bom"]
    if input_encoding not in valid_encodings:
        logging.info(f"Your input_encoding {input_encoding} is invalid. Reverting to default utf-8")
        input_encoding = "utf-8"


_set_url()

HOST = logzio_url_arr[0]
PORT = int(logzio_url_arr[1])

_is_open()
_add_shipping_data()


if "matchContainerName" in os.environ and "skipContainerName" in os.environ:
    logging.error("Can have only one of skipContainerName or matchContainerName")
    raise KeyError
elif "matchContainerName" in os.environ:
    _include_containers()
else:
    _exclude_containers()

if ("multilineType" in os.environ or "multilineNegate" in os.environ or "multilineMatch" in os.environ) and "multilinePattern" not in os.environ:
    raise ValueError("Please insert multilinePattern as well")
elif "multilinePattern" in os.environ:
    _add_multiline_type()


if "excludeLines" in os.environ:
    _exclude_lines()

if "includeLines" in os.environ:
    _include_lines()

if "renameFields" in os.environ:
    _add_rename_fields()


os.system(f"{os.getcwd()}/filebeat -e -c {FILEBEAT_CONF_PATH}")
