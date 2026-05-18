import time
import uuid
from datetime import datetime, timedelta

from services.observability.logger import logger
from app.v1.log_routes import add_log_from_middleware


# =========================
# 🚫 IGNORE SYSTEM ROUTES
# =========================
IGNORE_PATHS = {
    "/api/logs",
    "/docs",
    "/openapi.json",
    "/favicon.ico"
}


# =========================
# 📊 HELPERS
# =========================

def get_route_group(path: str):
    if "/tickets" in path:
        return "tickets"
    if "/runbook" in path:
        return "runbook"
    if "/logs" in path:
        return "observability"
    return "general"


def get_severity(status_code: int, latency: float):
    if status_code >= 500:
        return "critical"
    if status_code >= 400:
        return "warning"
    if latency > 2000:
        return "slow"
    return "info"


# =========================
# ⏰ UTC → IST CONVERTER
# =========================
def get_ist_timestamp():
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)

    # readable format with AM/PM + date
    return ist_now.strftime("%Y-%m-%d %I:%M:%S %p")


# =========================
# 🚀 MIDDLEWARE
# =========================

async def observability_middleware(request, call_next):

    start = time.time()

    if request.url.path in IGNORE_PATHS:
        return await call_next(request)

    request_id = str(uuid.uuid4())

    try:
        response = await call_next(request)

        latency = (time.time() - start) * 1000
        status = "success" if response.status_code < 400 else "failed"

        log_data = {
            "type": "api_request",

            # TRACE
            "request_id": request_id,

            # REQUEST
            "method": request.method,
            "path": request.url.path,
            "endpoint": request.url.path,
            "query_params": str(request.query_params),

            # RESPONSE
            "status": status,
            "status_code": response.status_code,

            # PERFORMANCE
            "latency_ms": round(latency, 2),

            # CLASSIFICATION
            "service": "ams-backend",
            "service_group": get_route_group(request.url.path),
            "severity": get_severity(response.status_code, latency),

            # SYSTEM
            "timestamp": get_ist_timestamp(),
            "client_ip": request.client.host if request.client else None,
        }

        logger.info(log_data)
        add_log_from_middleware(log_data)

        return response

    except Exception as e:

        latency = (time.time() - start) * 1000

        error_log = {
            "type": "api_error",

            "request_id": request_id,

            "method": request.method,
            "path": request.url.path,
            "endpoint": request.url.path,

            "status": "error",
            "status_code": 500,
            "error": str(e),

            "latency_ms": round(latency, 2),

            "service": "ams-backend",
            "service_group": get_route_group(request.url.path),
            "severity": "critical",

            "timestamp": get_ist_timestamp(),
            "client_ip": request.client.host if request.client else None,
        }

        logger.error(error_log)
        add_log_from_middleware(error_log)

        raise