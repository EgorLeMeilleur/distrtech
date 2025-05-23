import os
import json
import time
import requests
import psycopg2
import backoff
import threading
from pathlib import Path
from collections import deque
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from communication.socket import find_free_port, get_ip_in_network
from services.config import (
    POSTGRES_ADDR, POSTGRES_PORT, POSTGRES_USER,
    POSTGRES_PASS, POSTGRES_DB, CONSUL_ADDR, CONSUL_PORT
)

PIPE_BASE    = '/tmp/agg_pipes'
SERVICE_NAME = 'aggregator'
READ_INTERVAL = 0.1
AGG_INTERVAL  = 3.0

@backoff.on_exception(backoff.expo, requests.RequestException, max_time=60)
def register_to_consul(service_id, host, port, meta):
    url = f"http://{CONSUL_ADDR}:{CONSUL_PORT}/v1/agent/service/register"
    payload = {"Name": SERVICE_NAME, "ID": service_id,
               "Address": host, "Port": port, "Meta": meta}
    resp = requests.put(url, json=payload, timeout=5)
    resp.raise_for_status()
    print(f"Registered in Consul: {service_id}@{host}:{port}")


def start_consul_registration(service_id, host, port, meta):
    def loop():
        while True:
            try:
                register_to_consul(service_id, host, port, meta)
                break
            except Exception:
                time.sleep(10)
    t = threading.Thread(target=loop, daemon=True)
    t.start()


def deregister_from_consul(service_id):
    url = f"http://{CONSUL_ADDR}:{CONSUL_PORT}/v1/agent/service/deregister/{service_id}"
    try:
        requests.put(url, timeout=5).raise_for_status()
        print(f"Deregistered from Consul: {service_id}")
    except Exception as e:
        print(f"Consul deregistration failed: {e}")

def reader_thread(pipe_paths, queues, stop_event):

    fds = {}
    for key, path in pipe_paths.items():
        if key == 'base': continue
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        fds[key] = fd

    while not stop_event.is_set():
        for key, fd in fds.items():
            try:
                raw = os.read(fd, 4096)
                if raw:
                    try:
                        msg = json.loads(raw.decode('utf-8'))
                        queues[key].append(msg['value'])
                        print(f"Enqueued {key}: {msg['value']}")
                    except Exception as e:
                        print(f"Failed parse JSON from {key}: {e}")
            except BlockingIOError:
                pass
            except Exception as e:
                print(f"Error reading FIFO {key}: {e}")
        time.sleep(READ_INTERVAL)

def main():
    host = get_ip_in_network()
    port = find_free_port()
    service_id = f"{SERVICE_NAME}_{port}"
    instance_dir = os.path.join(PIPE_BASE, service_id)

    pipe_paths = {
        'base':       instance_dir,
        'pipe_temp':  os.path.join(instance_dir, 'pipe_temp'),
        'pipe_humid': os.path.join(instance_dir, 'pipe_humid'),
        'pipe_video': os.path.join(instance_dir, 'pipe_video'),
    }

    Path(pipe_paths['base']).mkdir(parents=True, exist_ok=True)
    for key, path in pipe_paths.items():
        if key == 'base': continue
        if not os.path.exists(path):
            os.mkfifo(path)
            print(f"Created FIFO: {path}")

    meta = {k: v for k, v in pipe_paths.items() if k != 'base'}
    start_consul_registration(service_id, host, port, meta)

    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB, user=POSTGRES_USER,
            password=POSTGRES_PASS, host=POSTGRES_ADDR,
            port=POSTGRES_PORT
        )
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                id SERIAL PRIMARY KEY,
                result DOUBLE PRECISION,
                ts TIMESTAMP WITH TIME ZONE,
                temp DOUBLE PRECISION,
                humid DOUBLE PRECISION,
                video DOUBLE PRECISION
            )''')
        conn.commit()
    except Exception as e:
        print(f"Postgres connection failed: {e}")
        deregister_from_consul(service_id)
        return

    queues = {k: deque() for k in ('pipe_temp','pipe_humid','pipe_video')}
    stop_event = threading.Event()

    t_reader = threading.Thread(
        target=reader_thread,
        args=(pipe_paths, queues, stop_event),
        daemon=True
    )
    t_reader.start()

    print("Aggregator started")
    last_agg = time.time()

    try:
        while True:
            now = time.time()
            if now - last_agg >= AGG_INTERVAL:
                last_agg = now
                vals = [queues[key].popleft() if queues[key] else None
                        for key in ('pipe_temp','pipe_humid','pipe_video')]
                non_null = [v for v in vals if v is not None]
                result = sum(non_null)/len(non_null) if non_null else None
                cur.execute(
                    "INSERT INTO readings(result, ts, temp, humid, video) VALUES (%s,%s,%s,%s,%s)",
                    (result, datetime.utcnow(), vals[0], vals[1], vals[2])
                )
                conn.commit()
                print(f"Aggregated {vals} -> {result}")

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Shutting down")
    finally:
        stop_event.set()
        t_reader.join(timeout=1)
        deregister_from_consul(service_id)
        conn.close()
        print("Aggregator stopped")

if __name__ == '__main__':
    main()
