import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from vpn_platform.api.admin import admin_router
from vpn_platform.config import Settings, get_settings
from vpn_platform.infrastructure.db.session import create_engine, create_session_factory

logger = logging.getLogger(__name__)

_MIN_ADMIN_TOKEN_LENGTH = 32


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    engine = create_engine(app_settings.database_url)

    admin_token = app_settings.admin_api_token
    if admin_token is not None and len(admin_token.get_secret_value()) < _MIN_ADMIN_TOKEN_LENGTH:
        logger.warning("ADMIN_API_TOKEN is shorter than %d characters", _MIN_ADMIN_TOKEN_LENGTH)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="VPN Platform API",
        version="0.1.0",
        docs_url="/docs" if app_settings.app_env == "development" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def ready() -> dict[str, str]:
        database: AsyncEngine = app.state.engine
        try:
            async with database.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="database is unavailable") from exc
        return {"status": "ok", "database": "ok"}

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, Any]:
        return {"service": "vpn-platform", "protocol": "AmneziaWG 2.0"}

    app.include_router(admin_router)

    return app
