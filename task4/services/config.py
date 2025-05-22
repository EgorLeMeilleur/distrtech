import json
import os

_conf_path = os.getenv('CONFIG_PATH', 'config.json')
with open(_conf_path) as f:
    _conf = json.load(f)

CONSUL_ADDR = _conf['consul']['address']
RABBIT_ADDR = _conf['rabbitmq']['address']
POSTGRES_DSN = _conf['postgres']['dsn']
AGG_HOST = _conf['aggregator']['host']
AGG_PORT = _conf['aggregator']['port']