"""PostgreSQL-backed sweeper tests.

Skipped unless VPN_TEST_DATABASE_URL points at a test database. CI provides a
postgres:17 service; locally run `make db-up` and export the variable.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vpn_platform.application.services.order_expiry import ExpireOrdersService
from vpn_platform.domain.orders import OrderStatus
from vpn_platform.infrastructure.db.base import Base
from vpn_platform.infrastructure.db.models import AuditLogModel, OrderModel, PlanModel, UserModel
from vpn_platform.infrastructure.db.order_queries import SqlAlchemyOrderExpiryUoW
from vpn_platform.infrastructure.db.session import create_engine, create_session_factory

pytestmark = pytest.mark.skipif(
    not os.environ.get("VPN_TEST_DATABASE_URL"),
    reason="requires PostgreSQL (set VPN_TEST_DATABASE_URL)",
)


@pytest.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_engine(os.environ["VPN_TEST_DATABASE_URL"])
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    factory = create_session_factory(engine)
    yield factory
    await engine.dispose()


async def _seed_user_and_plan(
    sessions: async_sessionmaker[AsyncSession],
) -> tuple[UUID, UUID]:
    async with sessions.begin() as session:
        user = UserModel(telegram_id=999000111)
        plan = PlanModel(
            name="integration-test",
            duration_days=30,
            traffic_limit_bytes=10_000_000_000,
            price=1000,
        )
        session.add_all([user, plan])
    return user.id, plan.id


def _order(
    user_id: UUID,
    plan_id: UUID,
    status: OrderStatus,
    expires_at: datetime,
) -> OrderModel:
    return OrderModel(
        user_id=user_id,
        plan_id=plan_id,
        plan_snapshot={"name": "integration-test"},
        amount_snapshot=1000,
        currency="IRR",
        status=status,
        expires_at=expires_at,
    )


async def _expired_audit_count(session: AsyncSession) -> int:
    rows = await session.scalars(
        select(AuditLogModel).where(AuditLogModel.action == "ORDER_EXPIRED")
    )
    return len(rows.all())


async def test_sweep_expires_only_due_expirable_orders(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    user_id, plan_id = await _seed_user_and_plan(sessions)
    now = datetime.now(UTC)
    due = _order(user_id, plan_id, OrderStatus.AWAITING_RECEIPT, now - timedelta(minutes=1))
    also_due = _order(user_id, plan_id, OrderStatus.NEEDS_NEW_RECEIPT, now - timedelta(days=1))
    in_review = _order(user_id, plan_id, OrderStatus.UNDER_REVIEW, now - timedelta(minutes=1))
    paid = _order(user_id, plan_id, OrderStatus.PAID, now - timedelta(minutes=1))
    future = _order(user_id, plan_id, OrderStatus.AWAITING_RECEIPT, now + timedelta(hours=1))
    async with sessions.begin() as session:
        session.add_all([due, also_due, in_review, paid, future])

    result = await ExpireOrdersService(SqlAlchemyOrderExpiryUoW(sessions)).sweep(now=now)

    assert set(result.expired_order_ids) == {due.id, also_due.id}
    async with sessions.begin() as session:
        rows = {row.id: row for row in (await session.scalars(select(OrderModel))).all()}
        assert rows[due.id].status == OrderStatus.EXPIRED
        assert rows[also_due.id].status == OrderStatus.EXPIRED
        assert rows[in_review.id].status == OrderStatus.UNDER_REVIEW
        assert rows[paid.id].status == OrderStatus.PAID
        assert rows[future.id].status == OrderStatus.AWAITING_RECEIPT
        assert await _expired_audit_count(session) == 2


async def test_two_concurrent_sweepers_never_process_the_same_order(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    user_id, plan_id = await _seed_user_and_plan(sessions)
    now = datetime.now(UTC)
    orders = [
        _order(user_id, plan_id, OrderStatus.AWAITING_RECEIPT, now - timedelta(minutes=index + 1))
        for index in range(20)
    ]
    async with sessions.begin() as session:
        session.add_all(orders)

    first = ExpireOrdersService(SqlAlchemyOrderExpiryUoW(sessions))
    second = ExpireOrdersService(SqlAlchemyOrderExpiryUoW(sessions))
    result_a, result_b = await asyncio.gather(first.sweep(now=now), second.sweep(now=now))

    expired_a = set(result_a.expired_order_ids)
    expired_b = set(result_b.expired_order_ids)
    assert not expired_a & expired_b
    assert expired_a | expired_b == {order.id for order in orders}
    async with sessions.begin() as session:
        assert await _expired_audit_count(session) == 20


async def test_order_locked_by_receipt_submission_is_skipped_and_not_expired(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    user_id, plan_id = await _seed_user_and_plan(sessions)
    now = datetime.now(UTC)
    order = _order(user_id, plan_id, OrderStatus.AWAITING_RECEIPT, now - timedelta(minutes=1))
    async with sessions.begin() as session:
        session.add(order)

    async with sessions() as locker:
        await locker.begin()
        locked = await locker.scalar(
            select(OrderModel).where(OrderModel.id == order.id).with_for_update()
        )
        assert locked is not None

        result = await ExpireOrdersService(SqlAlchemyOrderExpiryUoW(sessions)).sweep(now=now)
        assert result.expired_count == 0

        locked.status = OrderStatus.UNDER_REVIEW
        await locker.commit()

    async with sessions.begin() as session:
        row = await session.get(OrderModel, order.id)
        assert row is not None
        assert row.status == OrderStatus.UNDER_REVIEW
        assert await _expired_audit_count(session) == 0


class _FailingAuditUoW(SqlAlchemyOrderExpiryUoW):
    async def add_audit(self, *, action: str, target_id: str) -> None:
        raise RuntimeError("audit write failed")


async def test_mid_sweep_error_rolls_back_status_changes(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    user_id, plan_id = await _seed_user_and_plan(sessions)
    now = datetime.now(UTC)
    order = _order(user_id, plan_id, OrderStatus.AWAITING_RECEIPT, now - timedelta(minutes=1))
    async with sessions.begin() as session:
        session.add(order)

    with pytest.raises(RuntimeError, match="audit write failed"):
        await ExpireOrdersService(_FailingAuditUoW(sessions)).sweep(now=now)

    async with sessions.begin() as session:
        row = await session.get(OrderModel, order.id)
        assert row is not None
        assert row.status == OrderStatus.AWAITING_RECEIPT
        assert await _expired_audit_count(session) == 0
