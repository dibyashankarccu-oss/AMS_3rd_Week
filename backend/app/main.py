from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.v1.ticket_routes import router as ticket_router
from app.v1.runbook_routes import router as runbook_router
from app.v1.rca_routes     import router as rca_router
from app.v1.log_routes import router as log_router   
from services.observability.logger import log_error
from services.observability.middleware import observability_middleware
from app.v1.timeline_routes import router as timeline_router

app = FastAPI()


# =========================
# ✅ BETTER STACK MIDDLEWARE
# =========================
app.middleware("http")(observability_middleware)


# =========================
# ✅ CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ✅ GLOBAL ERROR HANDLER
# =========================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    log_error("Unhandled exception occurred", {
        "path": request.url.path,
        "method": request.method,
        "error": str(exc)
    })

    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )


# =========================
# ✅ ROUTES
# =========================
app.include_router(ticket_router, prefix="/api")
app.include_router(runbook_router, prefix="/api")
app.include_router(rca_router,     prefix="/api")
app.include_router(log_router, prefix="/api")  
app.include_router(timeline_router, prefix="/api")