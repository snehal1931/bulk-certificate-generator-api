"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import main_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import DomainException, domain_exception_handler
from app.core.logging import setup_logging, logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan event handler for startup/shutdown tasks."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in environment: {settings.ENVIRONMENT}")
    
    # Ensure database tables exist (complements Alembic migrations)
    Base.metadata.create_all(bind=engine)
    
    # Ensure storage directory exists
    settings.get_absolute_storage_dir()

    yield

    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-ready backend API for asynchronous bulk PDF certificate generation. "
        "Built with Python, FastAPI, SQLAlchemy 2.x, PostgreSQL, Pydantic v2, and ReportLab."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(DomainException, domain_exception_handler)

# Include API Routers
app.include_router(main_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify server operational status."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
