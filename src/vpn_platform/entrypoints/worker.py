import asyncio
import logging

from vpn_platform.application.services.order_expiry import ExpireOrdersService
from vpn_platform.config import get_settings
from vpn_platform.infrastructure.db.order_queries import SqlAlchemyOrderExpiryUoW
from vpn_platform.infrastructure.db.outbox import relay_outbox
from vpn_platform.infrastructure.db.session import create_engine, create_session_factory

logger = logging.getLogger(__name__)

_MAX_BACKOFF_SECONDS = 30.0


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    sessions = create_session_factory(engine)
    expiry_service = ExpireOrdersService(SqlAlchemyOrderExpiryUoW(sessions))
    backoff = settings.job_poll_seconds
    try:
        while True:
            try:
                async with sessions.begin() as session:
                    count = await relay_outbox(session)
                if count:
                    logger.info("relayed %d outbox events", count)
                sweep = await expiry_service.sweep()
                if sweep.expired_count:
                    logger.info("expired %d orders", sweep.expired_count)
            except Exception:
                logger.exception("worker iteration failed; retrying in %.1fs", backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)
                continue
            backoff = settings.job_poll_seconds
            await asyncio.sleep(settings.job_poll_seconds)
    finally:
        await engine.dispose()


def run() -> None:
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(main())
