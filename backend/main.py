"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import articles, auth, categories, feed, health, profile
from backend.config import settings
from backend.database.base import Base, engine
from backend.database.session import session_scope
from backend.logging_config import configure_logging, get_logger
from backend.services.user_service import ensure_niches

configure_logging(settings.log_level)
logger = get_logger("api")


def _init_db() -> None:
    """Create tables (for dev/first run) and seed niches.

    In production, Alembic migrations own the schema; ``create_all`` is a no-op
    when the tables already exist.
    """
    import backend.models  # noqa: F401  ensure models are registered

    Base.metadata.create_all(bind=engine)
    with session_scope() as db:
        ensure_niches(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application", extra={"ctx_env": settings.environment})
    _init_db()

    scheduler = None
    if settings.enable_scheduler:
        # Imported lazily so the API can start even if scheduler deps are absent.
        from scheduler.scheduler import shutdown_scheduler, start_scheduler

        scheduler = start_scheduler()

    yield

    if scheduler is not None:
        from scheduler.scheduler import shutdown_scheduler

        shutdown_scheduler(scheduler)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="AI-Powered Personalized News Aggregator API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(feed.router)
    app.include_router(articles.router)
    app.include_router(categories.router)

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {"name": settings.app_name, "docs": "/docs", "health": "/health"}

    return app


app = create_app()
