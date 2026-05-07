import uiud
import numpy as np
from datetime import datetime, timezone
from src.config import THRESHOLDS, WINDOW_SIZE

def _zscore(values):
    if len(values) < 3:
        return 0.0
    arr = np.array(values)
    mean = np.mean(arr)
    std = np.std(arr)
    if std == 0:
        return 0.0
    return (arr[-1] - mean) / std


def _make_incident(service, incident_type, severity, signals, reason, recovery_action):
    return {
        "incident_id":       f"inc_{uuid.uuid4().hex[:8]}",
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "service":           service,
        "incident_type":     incident_type,
        "severity":          severity,
        "signals":           signals,
        "reason":            reason,
        "recovery_action":   recovery_action,
        "recovery_status":   "triggered"
    }

def detect(service: str, window: list ) -> list:
    if len(window) < 3: 
        return []
    
    incidents = []
    
    cpu_values = [s["cpu_percent"] for s in window]
    memory_values = [s["memory_percent"] for s in window]
    latency_values = [s["latency_ms"] for s in window]
    error_values = [s["error_rate"] for s in window]
    restart_values = [s["restart_count"] for s in window]

    latest = window[-1]




    cpu_z = _zscore(cpu_values)
    if latest["cpu_percent"] > THRESHOLDS["cpu_percent"]["critical"] or cpu_z > THRESHOLDS["cpu_percent"]["z_score"]:
        incidents.append(_make_incident(
            service=service,
            incident_type="high_cpu_anomaly",
            severity="critical",
            signals={"cpu_percent": latest["cpu_percent"], "z_score": round(cpu_z, 2)},
            reason=f"CPU at {latest['cpu_percent']}% (z-score: {round(cpu_z, 2)})",
            recovery_action="restart_container"
        ))


    mem_z = _zscore(memory_values)
    if latest["memory_percent"] > THRESHOLDS["memory_percent"]["critical"] or mem_z > THRESHOLDS["memory_percent"]["z_score"]:
        incidents.append(_make_incident(
            service=service,
            incident_type="high_memory_anomaly",
            severity="critical",
            signals={"memory_percent": latest["memory_percent"], "z_score": round(mem_z, 2)},
            reason=f"Memory at {latest['memory_percent']}% (z-score: {round(mem_z, 2)})",
            recovery_action="flag_possible_leak"
        ))

    
    lat_z = _zscore(latency_values)
    if latest["latency_ms"] > THRESHOLDS["latency_ms"]["critical"] or lat_z > THRESHOLDS["latency_ms"]["z_score"]:
        incidents.append(_make_incident(
            service=service,
            incident_type="latency_degradation",
            severity="critical",
            signals={"latency_ms": latest["latency_ms"], "z_score": round(lat_z, 2)},
            reason=f"Latency at {latest['latency_ms']}ms (z-score: {round(lat_z, 2)})",
            recovery_action="mark_service_degraded"
        ))

    
    err_z = _zscore(error_values)
    if latest["error_rate"] > THRESHOLDS["error_rate"]["critical"] or err_z > THRESHOLDS["error_rate"]["z_score"]:
        incidents.append(_make_incident(
            service=service,
            incident_type="error_burst",
            severity="critical",
            signals={"error_rate": latest["error_rate"], "z_score": round(err_z, 2)},
            reason=f"Error rate at {latest['error_rate']} (z-score: {round(err_z, 2)})",
            recovery_action="escalate_critical"
        ))

    
    if latest["restart_count"] >= THRESHOLDS["restart_count"]["critical"]:
        incidents.append(_make_incident(
            service=service,
            incident_type="restart_storm",
            severity="critical",
            signals={"restart_count": latest["restart_count"]},
            reason=f"Service restarted {latest['restart_count']} times",
            recovery_action="escalate_critical"
        ))

    return incidents

def detect_all(windows: dict) -> list:
    all_incidents = []
    for service, window in windows.items():
        found = detect(service, window)
        all_incidents.extend(found)
    return all_incidents