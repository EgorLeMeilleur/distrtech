import os
import json
import requests
from services.config import CONSUL_ADDR, CONSUL_PORT
import errno
BASE_URL = f"http://{CONSUL_ADDR}:{CONSUL_PORT}"

def get_aggregator_pipe(pipe_key):
    url = f"{BASE_URL}/v1/catalog/service/aggregator"
    try:
        resp = requests.get(url, timeout=2)
        resp.raise_for_status()
        entries = resp.json()
    except Exception as e:
        print(f"[AggregatorPipe] Consul catalog fetch failed: {e}")
        return None

    if not entries:
        print("[AggregatorPipe] No aggregator instances in catalog")
        return None
    
    paths = []
    for entry in entries:
        meta = entry.get("ServiceMeta", {})
        path = meta.get(pipe_key)
        if not path:
            print(f"[AggregatorPipe] Meta key '{pipe_key}' missing in ServiceMeta")
            return None
        paths.append(path)
    return paths
