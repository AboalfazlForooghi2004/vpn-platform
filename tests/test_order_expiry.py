from datetime import UTC, datetime, timedelta
from types import TracebackType
from uuid import UUID, uuid4

from vpn_platform.application.services.order_expiry import ExpirableOrder, ExpireOrdersService
from vpn_platform.domain.orders import OrderStatus, can_transition
from vpn_platform.infrastructure.db.models import OrderModel


class FakeOrderExpiryUoW:
    def __init__(self, orders: list[ExpirableOrder]) -> None:
        self._orders = orders
        self.expired: list[UUID] = []
        self.audits: list[tuple[str, str]] = []
        self.committed = False

    async def __aenter__(self) -> "FakeOrderExpiryUoW":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def lock_due_orders(self, *, now: datetime, limit: int) -> list[ExpirableOrder]:
        return self._orders[:limit]

    async def mark_expired(self, order_id: UUID) -> None:
        self.expired.append(order_id)

    async def add_audit(self, *, action: str, target_id: str) -> None:
        self.audits.append((action, target_id))

    async def commit(self) -> None:
        self.committed = True


def test_state_machine_allows_expiry_only_from_receipt_states() -> None:
    assert can_transition(OrderStatus.AWAITING_RECEIPT, OrderStatus.EXPIRED)
    assert can_transition(OrderStatus.NEEDS_NEW_RECEIPT, OrderStatus.EXPIRED)
    assert not can_transition(OrderStatus.PAID, OrderStatus.EXPIRED)
    assert not can_transition(OrderStatus.UNDER_REVIEW, OrderStatus.EXPIRED)
    assert not can_transition(OrderStatus.COMPLETED, OrderStatus.EXPIRED)
    assert not can_transition(OrderStatus.EXPIRED, OrderStatus.EXPIRED)


def test_expiry_sweep_partial_index_is_defined() -> None:
    indexes = {index.name: index for index in OrderModel.__table__.indexes}
    index = indexes["ix_orders_expiry_sweep"]

    assert tuple(column.name for column in index.columns) == ("status", "expires_at")
    where = index.dialect_options["postgresql"]["where"]
    assert str(where) == "status IN ('AWAITING_RECEIPT', 'NEEDS_NEW_RECEIPT')"


async def test_sweep_expires_due_orders_and_writes_audit() -> None:
    now = datetime.now(UTC)
    due = ExpirableOrder(uuid4(), OrderStatus.AWAITING_RECEIPT, now - timedelta(minutes=1))
    also_due = ExpirableOrder(uuid4(), OrderStatus.NEEDS_NEW_RECEIPT, now - timedelta(days=1))
    uow = FakeOrderExpiryUoW([due, also_due])

    result = await ExpireOrdersService(uow).sweep(now=now)

    assert result.expired_order_ids == (due.id, also_due.id)
    assert result.expired_count == 2
    assert uow.expired == [due.id, also_due.id]
    assert uow.audits == [
        ("ORDER_EXPIRED", str(due.id)),
        ("ORDER_EXPIRED", str(also_due.id)),
    ]
    assert uow.committed


async def test_sweep_skips_orders_that_left_an_expirable_state() -> None:
    now = datetime.now(UTC)
    paid_in_time = ExpirableOrder(uuid4(), OrderStatus.PAID, now - timedelta(minutes=5))
    uow = FakeOrderExpiryUoW([paid_in_time])

    result = await ExpireOrdersService(uow).sweep(now=now)

    assert result.expired_count == 0
    assert uow.expired == []
    assert uow.audits == []
    assert uow.committed
