"""
ML Microservice Entry Point.
FastAPI application for sentiment analysis, personality classification, and recommendations.
"""

import logging
import structlog
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram

from config import get_settings
from models.schemas import HealthResponse, ReadinessResponse, ErrorResponse

# Import routes
from routes.sentiment import router as sentiment_router
from routes.personality import router as personality_router
from routes.recommendations import router as recommendations_router

# Import database clients
from database.mongodb import get_mongodb, close_mongodb
from database.postgres import get_postgres, close_postgres
from database.weaviate_client import get_weaviate, close_weaviate
from database.interaction_client import get_interaction_client, close_interaction_client
from database.redis_client import get_redis, close_redis

# Import services for preloading
from services.sentiment_analyzer import preload_models
from services.recommendation_engine import preload_embedding_model

# Import Kafka consumer
from services.kafka_consumer import start_kafka_consumer, stop_kafka_consumer, get_kafka_consumer

# Configure standard library logging level
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "ml_service_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "ml_service_request_latency_seconds",
    "Request latency",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.
    """
    settings = get_settings()
    logger.info(
        "Starting ML microservice",
        version=settings.app_version,
        debug=settings.debug,
    )

    # Startup: Initialize database connections
    try:
        logger.info("Initializing database connections...")

        # Connect to all databases (with error handling for optional ones)
        try:
            await get_mongodb()
            logger.info("MongoDB connected")
        except Exception as e:
            logger.warning("MongoDB connection failed (non-fatal)", error=str(e))

        try:
            await get_postgres()
            logger.info("PostgreSQL connected")
        except Exception as e:
            logger.warning("PostgreSQL connection failed (non-fatal)", error=str(e))

        try:
            await get_redis()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning("Redis connection failed (non-fatal)", error=str(e))

        try:
            await get_weaviate()
            logger.info("Weaviate connected")
        except Exception as e:
            logger.warning("Weaviate connection failed (non-fatal)", error=str(e))

        try:
            await get_interaction_client()
            logger.info("Interaction logger connected")
        except Exception as e:
            logger.warning("Interaction logger connection failed (non-fatal)", error=str(e))

        # Preload ML models
        logger.info("Preloading ML models...")
        try:
            await preload_models()
        except Exception as e:
            logger.warning("Sentiment model preload failed (non-fatal)", error=str(e))

        try:
            await preload_embedding_model()
        except Exception as e:
            logger.warning("Embedding model preload failed (non-fatal)", error=str(e))

        # Start Kafka consumer
        try:
            await start_kafka_consumer()
            logger.info("Kafka consumer started")
        except Exception as e:
            logger.warning("Kafka consumer start failed (non-fatal)", error=str(e))

        logger.info("ML microservice started successfully")

    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise

    yield

    # Shutdown: Close all connections
    logger.info("Shutting down ML microservice...")

    # Stop Kafka consumer first
    try:
        await stop_kafka_consumer()
        logger.info("Kafka consumer stopped")
    except Exception as e:
        logger.warning("Error stopping Kafka consumer", error=str(e))

    await close_mongodb()
    await close_postgres()
    await close_redis()
    await close_weaviate()
    await close_interaction_client()

    logger.info("ML microservice shutdown complete")


# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ML Microservice for e-commerce: Sentiment Analysis, Personality Classification, and Recommendations",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Service-to-service authentication middleware.
    Validates X-Service-Auth header for protected endpoints.
    """
    # Paths excluded from authentication
    excluded_paths = ["/health", "/health/ready", "/metrics", "/docs", "/redoc", "/openapi.json"]

    if any(request.url.path.startswith(path) for path in excluded_paths):
        return await call_next(request)

    # Check authentication token
    auth_token = request.headers.get("X-Service-Auth")
    if not auth_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "error": "Missing X-Service-Auth header"},
        )

    if auth_token != settings.service_auth_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "error": "Invalid authentication token"},
        )

    return await call_next(request)


# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record request metrics."""
    import time

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Health endpoints
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Basic health check endpoint.",
)
async def health_check() -> HealthResponse:
    """Basic health check."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
    )


@app.get(
    "/health/ready",
    response_model=ReadinessResponse,
    tags=["Health"],
    summary="Readiness check",
    description="Check if all services are ready.",
)
async def readiness_check() -> ReadinessResponse:
    """Check readiness of all dependent services."""
    services = {}

    # Check MongoDB
    try:
        mongo = await get_mongodb()
        services["mongodb"] = await mongo.health_check()
    except Exception:
        services["mongodb"] = False

    # Check PostgreSQL
    try:
        postgres = await get_postgres()
        services["postgresql"] = await postgres.health_check()
    except Exception:
        services["postgresql"] = False

    # Check Redis
    try:
        redis = await get_redis()
        services["redis"] = await redis.health_check()
    except Exception:
        services["redis"] = False

    # Check Weaviate
    try:
        weaviate = await get_weaviate()
        services["weaviate"] = await weaviate.health_check()
    except Exception:
        services["weaviate"] = False

    # Check interaction logger
    try:
        interaction_client = await get_interaction_client()
        services["interaction_logger"] = await interaction_client.health_check()
    except Exception:
        services["interaction_logger"] = False

    # Check Kafka consumer
    try:
        kafka_consumer = get_kafka_consumer()
        services["kafka_consumer"] = await kafka_consumer.health_check()
    except Exception:
        services["kafka_consumer"] = False

    all_ready = all(services.values())

    return ReadinessResponse(
        ready=all_ready,
        services=services,
        message="All services ready" if all_ready else "Some services are not ready",
    )


@app.get(
    "/metrics",
    tags=["Monitoring"],
    summary="Prometheus metrics",
    description="Prometheus metrics endpoint.",
)
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Include API routers
app.include_router(sentiment_router, prefix="/api/v1")
app.include_router(personality_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
        "readiness": "/health/ready",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
