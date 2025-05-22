import os
import requests

CONSUL_ADDR = os.getenv("CONSUL_ADDR", "http://localhost:8500")

def register_service(name: str, service_id: str, address: str, port: int):
    payload = {
        "Name": name,
        "ID": service_id,
        "Address": address,
        "Port": port,
        "Check": {
            "HTTP": f"http://{address}:{port}/health",
            "Interval": "10s"
        }
    }
    r = requests.put(f"{CONSUL_ADDR}/v1/agent/service/register", json=payload)
    r.raise_for_status()

def discover_service(name: str) -> list[tuple[str,int]]:
    r = requests.get(f"{CONSUL_ADDR}/v1/catalog/service/{name}")
    r.raise_for_status()
    services = r.json()
    return [(item.get("ServiceAddress") or item["Address"], item["ServicePort"])
            for item in services]

def deregister_service(service_id: str):
    r = requests.put(f"{CONSUL_ADDR}/v1/agent/service/deregister/{service_id}")
    r.raise_for_status()