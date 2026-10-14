from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.api import health, auth, skills, executions

settings = get_settings()

logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version} in {settings.environment} mode")
    await init_db()
    yield
    logger.info("Shutting down")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Beacon Console — AI Scientist Skills Platform",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.debug(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response


import time

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(executions.router, prefix="/api")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not found"})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception("Internal server error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if not settings.is_production else "disabled in production",
    }