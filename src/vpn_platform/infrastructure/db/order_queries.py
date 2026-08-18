from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vpn_platform.application.services.order_expiry import EXPIRABLE_STATUSES, ExpirableOrder
from vpn_platform.domain.orders import OrderStatus
from vpn_platform.infrastructure.db.models import AuditLogModel, OrderModel

async def lock_expired_orders(
    session: AsyncSession,
    *,
    now: datetime,
    limit: int,
) -> Sequence[OrderModel]:
    """Lock due orders so concurrent sweepers and web writes cannot race."""
    statement = (
        select(OrderModel)
        .where(
            OrderModel.expires_at <= now,
            OrderModel.status.in_([status.value for status in EXPIRABLE_STATUSES]),
        )
        .order_by(OrderModel.expires_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    return list((await session.scalars(statement)).all())

class SqlAlchemyOrderExpiryUoW:
    """Relational implementation of the order-expiry unit of work.

    One sweep batch runs in a single transaction: rows stay locked from read to
    commit, so an order paid while the sweep runs cannot flip to EXPIRED.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "SqlAlchemyOrderExpiryUoW":
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session, self._session = self._session, None
        if session is None:
            return
        try:
            if exc_type is not None:
                await session.rollback()
        finally:
            await session.close()

    def _require_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("unit of work is used outside its context manager")
        return self._session

    async def lock_due_orders(self, *, now: datetime, limit: int) -> Sequence[ExpirableOrder]:
        rows = await lock_expired_orders(self._require_session(), now=now, limit=limit)
        return [
            ExpirableOrder(id=row.id, status=OrderStatus(row.status), expires_at=row.expires_at)
            for row in rows
        ]

    async def mark_expired(self, order_id: UUID) -> None:
        session = self._require_session()
        order = await session.get(OrderModel, order_id)
        if order is None:
            raise LookupError(f"order {order_id} disappeared during the expiry sweep")
        order.status = OrderStatus.EXPIRED

    async def add_audit(self, *, action: str, target_id: str) -> None:
        self._require_session().add(
            AuditLogModel(
                actor_type="SYSTEM",
                actor_id="order-expiry-sweeper",
                action=action,
                target_type="ORDER",
                target_id=target_id,
                audit_metadata={},
            )
        )

    async def commit(self) -> None:
        await self._require_session().commit()
