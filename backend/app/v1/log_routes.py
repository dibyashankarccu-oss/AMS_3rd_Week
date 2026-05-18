from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter()

logs_buffer: List[Dict[str, Any]] = []


# =========================
# 🕒 IST TIME FORMATTER (AM/PM)
# =========================
def get_ist_time():
    ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%Y-%m-%d %I:%M:%S %p")  # 👈 AM/PM format


# =========================
# ➕ ADD LOG
# =========================
def add_log(log: Dict[str, Any]):

    # ensure timestamp in IST + AM/PM
    if "timestamp" not in log:
        log["timestamp"] = get_ist_time()

    # default severity
    if "severity" not in log:
        log["severity"] = "info"

    logs_buffer.append(log)

    # keep last 100 logs only
    if len(logs_buffer) > 100:
        logs_buffer.pop(0)


# =========================
# 🔌 MIDDLEWARE ENTRY
# =========================
def add_log_from_middleware(log: dict):
    add_log(log)


# =========================
# 🌐 API ENDPOINT
# =========================
@router.get("/logs")
def get_logs():
    return {
        "logs": list(reversed(logs_buffer))
    }