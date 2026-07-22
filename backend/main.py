"""FastAPI application entry point with CORS, middleware stack, and startup/shutdown events.

Middleware order (outermost → innermost):
  CORS → GZip → Security Headers → Rate Limiter → Auth → Request ID → Route Handler
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware

from backend.config import settings
from backend.middleware.auth import FirebaseAuthMiddleware
from backend.middleware.rate_limiter import RateLimiterMiddleware
from backend.middleware.security_headers import SecurityHeadersMiddleware
from backend.models.database import create_tables, dispose_engine, async_session
from backend.utils.response import error_response, validation_error_response

# --- Router imports ---
from backend.routers.ahorro import router as ahorro_router
from backend.routers.creditos import router as creditos_router
from backend.routers.gastos_ingresos import router as gastos_ingresos_router
from backend.routers.deudas import router as deudas_router
from backend.routers.aportaciones import router as aportaciones_router
from backend.routers.afore import router as afore_router
from backend.routers.gbm_portfolio import router as gbm_portfolio_router
from backend.routers.patrimonio import router as patrimonio_router
from backend.routers.update_tracker import router as update_tracker_router
from backend.routers.optimizer import router as optimizer_router
from backend.routers.instruments import router as instruments_router
from backend.routers.courses import router as courses_router
from backend.routers.advisor import router as advisor_router
from backend.routers.categories import router as categories_router
from backend.routers.chat import router as chat_router
from backend.routers.scrapers import router as scrapers_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup: validate encryption key (fail fast if invalid in production)
    from backend.services.encryption import encryption_service  # noqa: F401
    from backend.services.seed_data import seed_instruments
    from backend.services.rate_scheduler import scheduler, setup_scheduler, run_initial_sync

    if settings.is_sqlite:
        await create_tables()

    # Seed instruments if table is empty
    async with async_session() as db:
        await seed_instruments(db)

    # Setup and start the rate scheduler
    setup_scheduler()
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()
    await dispose_engine()


app = FastAPI(
    title="Finalat API",
    description="Financial advisory and personal finance management platform for Mexico.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware stack
# ---------------------------------------------------------------------------
# Starlette applies middleware in REVERSE order of add_middleware calls.
# First added = innermost (closest to route handler).
# Last added = outermost (first to see the request).
#
# Desired order (outermost → innermost):
#   CORS → GZip → Security Headers → Rate Limiter → Auth
#
# Therefore we register: Auth → Rate Limiter → Security Headers → GZip → CORS
# ---------------------------------------------------------------------------

# 1. Auth Middleware (innermost — needs request.state.user_id for downstream)
app.add_middleware(FirebaseAuthMiddleware)

# 2. Rate Limiter Middleware (uses user_id from auth or falls back to IP)
app.add_middleware(RateLimiterMiddleware)

# 3. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 4. GZip Compression Middleware (compress JSON responses > 1KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 5. CORS Middleware (outermost — must handle preflight before anything else)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Register all routers
# ---------------------------------------------------------------------------
# Financial modules
app.include_router(ahorro_router)
app.include_router(creditos_router)
app.include_router(gastos_ingresos_router)
app.include_router(deudas_router)
app.include_router(aportaciones_router)
app.include_router(afore_router)
app.include_router(gbm_portfolio_router)
app.include_router(patrimonio_router)

# Categories
app.include_router(categories_router)

# Instruments & Optimizer
app.include_router(instruments_router)
app.include_router(optimizer_router)

# Learning system
app.include_router(courses_router)

# AI Advisor
app.include_router(advisor_router)

# Chat (Fina agent)
app.include_router(chat_router)

# Scrapers (rate sync)
app.include_router(scrapers_router)

# Update tracker
app.include_router(update_tracker_router)


# --- Request ID Middleware ---
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a unique request ID to each request for correlation in logs."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# --- Exception Handlers ---

@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standard envelope."""
    fields = {}
    message_parts = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"] if part != "body")
        msg = error["msg"]
        if loc:
            fields[loc] = msg
            message_parts.append(f"{loc}: {msg}")
        else:
            message_parts.append(msg)
    message = "; ".join(message_parts) if message_parts else "Validation error."
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "Validation error [request_id=%s]: %s",
        request_id,
        message,
    )
    return JSONResponse(
        status_code=400,
        content=validation_error_response(message, fields if fields else None),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions (404, etc.) with standard envelope."""
    request_id = getattr(request.state, "request_id", "unknown")

    if exc.status_code == 404:
        logger.info(
            "Not found [request_id=%s]: %s %s",
            request_id,
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=404,
            content=error_response("NOT_FOUND", "Endpoint not found."),
        )

    # For other HTTP exceptions, map to the appropriate error code
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        405: "METHOD_NOT_ALLOWED",
        429: "RATE_LIMITED",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "An error occurred."

    logger.warning(
        "HTTP %d [request_id=%s]: %s",
        exc.status_code,
        request_id,
        message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code, message),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions. Never exposes stack traces."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "Unhandled exception [request_id=%s]: %s: %s",
        request_id,
        type(exc).__name__,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content=error_response("INTERNAL_ERROR", "An unexpected error occurred."),
        headers={"X-Request-ID": request_id},
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "environment": settings.APP_ENV}
