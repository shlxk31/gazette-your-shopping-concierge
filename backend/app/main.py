"""
FastAPI application factory.
"""

import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.constants import API_V1_PREFIX
from app.api.v1 import api_router

settings = get_settings()


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["console"],
            },
        }
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logging.getLogger(__name__).info(
        "Agentic E-Commerce API starting — env=%s model=%s",
        settings.app_env,
        settings.groq_model,
    )
    yield
    logging.getLogger(__name__).info("Shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic E-Commerce API",
        description=(
            "Multi-agent backend that refines user intent, discovers products, "
            "and aggregates marketplace prices."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — adjust origins for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=API_V1_PREFIX)

    @app.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
