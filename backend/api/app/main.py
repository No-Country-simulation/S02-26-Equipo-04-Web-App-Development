import json
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.schemas.response import APIException, ErrorDetail, ErrorResponse
from app.utils.redis_client import redis_client

logger = setup_logging()


def redis_event_listener():
    """Background listener para eventos de Redis Pub/Sub"""
    logger.info("🎧 Starting Redis event listener...")

    try:
        pubsub = redis_client.subscribe("video_events")
        logger.info("✅ Redis listener ready")

        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    logger.info(f"📩 Event received: {data}")
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
    except Exception as e:
        logger.error(f"Redis listener error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 50)

    # Database migrations are handled by Alembic
    # Run: docker exec -it fastapi alembic upgrade head
    logger.info("⚠️ Remember to run Alembic migrations: alembic upgrade head")

    if redis_client.ping():
        logger.info("✅ Redis connected")
    else:
        logger.warning("⚠️ Redis not available")

    thread = threading.Thread(target=redis_event_listener, daemon=True)
    thread.start()
    logger.info("✅ Redis listener started in background")

    logger.info("🎉 Application startup complete")

    yield

    logger.info("👋 Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para procesamiento automático de videos (horizontal → vertical shorts)",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.DEBUG:

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug(f"{request.method} {request.url}")
        response = await call_next(request)
        logger.debug(f"Response: {response.status_code}")
        return response


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail, details=None).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        ErrorDetail(loc=list(err["loc"]), msg=err["msg"], type=err["type"]) for err in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Errores de validación en la solicitud", details=errors
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Error interno del servidor" if not settings.DEBUG else str(exc), details=None
        ).model_dump(),
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
