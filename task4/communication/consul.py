import os
import requests
from services.config import CONSUL_ADDR, CONSUL_PORT

def register_service(name: str, service_id: str, address: str, port: int):
    payload = {
        "Name": name,
        "ID": service_id,
        "Address": address,
        "Port": port,
    }
    r = requests.put(f"http://{CONSUL_ADDR}:{CONSUL_PORT}/v1/agent/service/register", json=payload)
    r.raise_for_status()

def discover_service(name: str) -> list[tuple[str,int]]:
    r = requests.get(f"http://{CONSUL_ADDR}:{CONSUL_PORT}/v1/catalog/service/{name}")
    r.raise_for_status()
    services = r.json()
    return [(item.get("ServiceAddress") or item["Address"], item["ServicePort"])
            for item in services]

def deregister_service(service_id: str):
    r = requests.put(f"http://{CONSUL_ADDR}:{CONSUL_PORT}/v1/agent/service/deregister/{service_id}")
    r.raise_for_status()