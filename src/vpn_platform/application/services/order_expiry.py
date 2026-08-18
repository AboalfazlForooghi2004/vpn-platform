"""Sweep orders whose receipt window has elapsed into the EXPIRED state."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from vpn_platform.domain.orders import OrderStatus, can_transition

EXPIRABLE_STATUSES: tuple[OrderStatus, ...] = (
    OrderStatus.AWAITING_RECEIPT,
    OrderStatus.NEEDS_NEW_RECEIPT,
)

@dataclass(frozen=True, slots=True)
class ExpirableOrder:
    """Minimal locked row view the sweeper needs to decide on expiry."""

    id: UUID
    status: OrderStatus
    expires_at: datetime

class OrderExpiryUnitOfWork(Protocol):
    async def __aenter__(self) -> "OrderExpiryUnitOfWork": ...

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    async def lock_due_orders(self, *, now: datetime, limit: int) -> Sequence[ExpirableOrder]: ...

    async def mark_expired(self, order_id: UUID) -> None: ...

    async def add_audit(self, *, action: str, target_id: str) -> None: ...

    async def commit(self) -> None: ...

@dataclass(frozen=True, slots=True)
class ExpirySweepResult:
    expired_order_ids: tuple[UUID, ...]

    @property
    def expired_count(self) -> int:
        return len(self.expired_order_ids)

class ExpireOrdersService:
    """Expire due orders in small locked batches; safe to run every worker tick."""

    def __init__(self, uow: OrderExpiryUnitOfWork, *, batch_size: int = 100) -> None:
        self._uow = uow
        self._batch_size = batch_size

    async def sweep(self, *, now: datetime | None = None) -> ExpirySweepResult:
        moment = now or datetime.now(UTC)
        async with self._uow:
            due = await self._uow.lock_due_orders(now=moment, limit=self._batch_size)
            expired: list[UUID] = []
            for order in due:
                if not can_transition(order.status, OrderStatus.EXPIRED):
                    continue  # defensive: the query already filters to expirable states
                await self._uow.mark_expired(order.id)
                await self._uow.add_audit(action="ORDER_EXPIRED", target_id=str(order.id))
                expired.append(order.id)
            await self._uow.commit()
        return ExpirySweepResult(expired_order_ids=tuple(expired))
