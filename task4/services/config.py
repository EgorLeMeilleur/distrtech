import json
import os

_conf_path = os.getenv('CONFIG_PATH', 'config.json')
with open(_conf_path) as f:
    _conf = json.load(f)

CONSUL_ADDR = _conf['consul']['address']
CONSUL_PORT = _conf['consul']['port']
POSTGRES_ADDR = _conf['postgres']['address']
POSTGRES_PORT = _conf['postgres']['port']
POSTGRES_USER = _conf['postgres']['user']
POSTGRES_PASS = _conf['postgres']['password']
POSTGRES_DB = _conf['postgres']['database']
RABBIT_ADDR = _conf['rabbitmq']['address']
RABBIT_PORT = _conf['rabbitmq']['port']
RABBIT_USER = _conf['rabbitmq']['user']
RABBIT_PASS = _conf['rabbitmq']['password']