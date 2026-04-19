import os
import time
import random 
import threading 
import psutil
from fastapi import FastAPI

app = FastAPI()

SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")

_chaos_active = False
_chaos_lock = threading.Lock()  

CHAOS_DURATION = int(os.getenv("CHAOS_DURATION", 30))

def _reset_chaos():
    global _chaos_active
    time.sleep(CHAOS_DURATION)
    _chaos_active = False


@app.get("/health")
def health():
    return {"service": SERVICE_NAME, "status": "ok"}

@app.get("/metrics")
def metrics():
    with _chaos_lock:
        chaos = _chaos_active

    if chaos:
        cpu        = round(random.gauss(88, 6), 2)
        memory     = round(random.gauss(85, 5), 2)
        latency    = round(random.gauss(520, 80), 2)
        error_rate = round(random.gauss(0.13, 0.03), 4)
    else:
        cpu        = round(random.gauss(35, 8), 2)
        memory     = round(random.gauss(50, 7), 2)
        latency    = round(random.gauss(120, 25), 2)
        error_rate = round(random.gauss(0.01, 0.005), 4)

    cpu        = max(0, min(100, cpu))
    memory     = max(0, min(100, memory))
    latency    = max(5, latency)
    error_rate = max(0, min(1.0, error_rate))

    return {
        "service":        SERVICE_NAME,
        "cpu_percent":    cpu,
        "memory_percent": memory,
        "latency_ms":     latency,
        "error_rate":     error_rate,
        "restart_count":  0,
        "chaos_active":   chaos
    }


@app.post("/chaos")
def trigger_chaos():
    global _chaos_active
    with _chaos_lock:
        _chaos_active = True
    t = threading.Thread(target=_reset_chaos, daemon=True)
    t.start()
    return {"service": SERVICE_NAME, "chaos": "triggered", "duration_seconds": CHAOS_DURATION} 