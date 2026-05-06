import time 
import requests
from collections import deque 
from src.config import SERVICE_PORTS, SERVICES, WINDOW_SIZE, POLL_INTERVAL_SECONDS

_windows - { 
    service: deque(maxlen=WINDOW_SIZE)
    for serice in SERVICES
}

def collect_once():
    
    for service in SERVICES:
        port = SERVICE_PORTS[service]
        try:
            response = requests.get(f"http://localhost:{port}/metrics", timeout=3)
            snapshot = response.json()
            _windows[service].append(snapshot)
        except Exception as e:
            print(f"[collector] failed to reach {service}: {e}")

def get_window(service: str) -> list:
    
    return list(_windows[service])

def get_all_windows() -> dict:
    ``
    return {service: get_window(service) for service in SERVICES}

