"""ProjeX Suite API — FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.api.v1 import router as api_v1_router
from app.middleware.tenant import TenantMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown events."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# --- Middleware stack (order matters: last added = first executed) ---

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

# Tenant resolution
app.add_middleware(TenantMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "version": settings.app_version}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler returning standard envelope."""
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "meta": {},
            "errors": [{"message": "Internal server error"}],
        },
    )
