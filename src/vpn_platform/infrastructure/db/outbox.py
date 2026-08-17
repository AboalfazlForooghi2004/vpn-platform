from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from vpn_platform.infrastructure.db.models import JobModel, OutboxEventModel


async def relay_outbox(session: AsyncSession, *, limit: int = 50) -> int:
    """Move unpublished domain messages into the durable jobs table exactly once."""
    statement = (
        select(OutboxEventModel)
        .where(OutboxEventModel.published_at.is_(None))
        .order_by(OutboxEventModel.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    events = list((await session.scalars(statement)).all())
    now = datetime.now(UTC)
    for event in events:
        await session.execute(
            insert(JobModel)
            .values(
                job_type=event.topic,
                idempotency_key=event.idempotency_key,
                payload=event.payload,
                status="PENDING",
                run_at=now,
            )
            .on_conflict_do_nothing(index_elements=[JobModel.idempotency_key])
        )
        event.published_at = now
    return len(events)
