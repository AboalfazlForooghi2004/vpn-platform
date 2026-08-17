from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from vpn_platform.infrastructure.db.models import JobModel


async def claim_due_jobs(
    session: AsyncSession,
    *,
    worker_id: str,
    limit: int = 10,
    lease_seconds: int = 30,
) -> Sequence[JobModel]:
    """Claim due work inside the caller's transaction using row-level locks."""
    now = datetime.now(UTC)
    statement = (
        select(JobModel)
        .where(
            JobModel.run_at <= now,
            or_(
                JobModel.status == "PENDING",
                (JobModel.status == "RUNNING") & (JobModel.lease_until < now),
            ),
        )
        .order_by(JobModel.run_at, JobModel.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    jobs = list((await session.scalars(statement)).all())
    for job in jobs:
        job.status = "RUNNING"
        job.worker_id = worker_id
        job.lease_until = now + timedelta(seconds=lease_seconds)
        job.attempts += 1
    return jobs
