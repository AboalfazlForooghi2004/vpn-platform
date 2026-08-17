from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from vpn_platform.domain.orders import Order
from vpn_platform.domain.payments import Payment, approve_payment


class PaymentApprovalUnitOfWork(Protocol):
    async def __aenter__(self) -> "PaymentApprovalUnitOfWork": ...

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    async def get_payment_for_update(self, payment_id: UUID) -> Payment: ...

    async def get_order_for_update(self, order_id: UUID) -> Order: ...

    async def save_payment(self, payment: Payment) -> None: ...

    async def save_order(self, order: Order) -> None: ...

    async def add_outbox(
        self, *, topic: str, idempotency_key: str, payload: dict[str, object]
    ) -> None: ...

    async def add_audit(self, *, actor_id: str, action: str, target_id: str) -> None: ...

    async def commit(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ApprovalResult:
    approved: bool
    already_approved: bool


class ApprovePaymentService:
    def __init__(self, uow: PaymentApprovalUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, *, payment_id: UUID, order_id: UUID, admin_telegram_id: int
    ) -> ApprovalResult:
        async with self._uow:
            payment = await self._uow.get_payment_for_update(payment_id)
            order = await self._uow.get_order_for_update(order_id)
            message = approve_payment(
                payment=payment,
                order=order,
                admin_telegram_id=admin_telegram_id,
                approved_at=datetime.now(UTC),
            )
            if message is None:
                return ApprovalResult(approved=True, already_approved=True)

            await self._uow.save_payment(payment)
            await self._uow.save_order(order)
            await self._uow.add_outbox(
                topic=message.topic,
                idempotency_key=message.idempotency_key,
                payload=message.payload,
            )
            await self._uow.add_audit(
                actor_id=str(admin_telegram_id),
                action="PAYMENT_APPROVED",
                target_id=str(payment_id),
            )
            await self._uow.commit()
            return ApprovalResult(approved=True, already_approved=False)
