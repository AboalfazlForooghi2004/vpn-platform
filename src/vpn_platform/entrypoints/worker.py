import asyncio
import logging

from vpn_platform.config import get_settings
from vpn_platform.infrastructure.db.outbox import relay_outbox
from vpn_platform.infrastructure.db.session import create_engine, create_session_factory

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    sessions = create_session_factory(engine)
    try:
        while True:
            async with sessions.begin() as session:
                count = await relay_outbox(session)
            if count:
                logger.info("relayed %d outbox events", count)
            await asyncio.sleep(settings.job_poll_seconds)
    finally:
        await engine.dispose()


def run() -> None:
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(main())
