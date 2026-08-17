from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from vpn_platform.domain.errors import InvalidTransition
from vpn_platform.domain.orders import Order, OrderStatus


class PaymentStatus(StrEnum):
    AWAITING_RECEIPT = "AWAITING_RECEIPT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(slots=True)
class Payment:
    id: UUID
    order_id: UUID
    status: PaymentStatus
    approved_by: int | None = None
    approved_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    topic: str
    idempotency_key: str
    payload: dict[str, Any]


def approve_payment(
    *, payment: Payment, order: Order, admin_telegram_id: int, approved_at: datetime
) -> OutboxMessage | None:
    """Approve once and emit one deterministic provisioning command.

    Persistence must save the payment, order, audit record and returned message in one
    database transaction. Calling this function after a successful approval is a no-op.
    """
    if payment.status is PaymentStatus.APPROVED and order.status is OrderStatus.PAID:
        return None
    if payment.status is not PaymentStatus.PENDING_REVIEW:
        raise InvalidTransition(f"payment in {payment.status} cannot be approved")
    if order.status is not OrderStatus.UNDER_REVIEW:
        raise InvalidTransition(f"order in {order.status} cannot be paid")

    payment.status = PaymentStatus.APPROVED
    payment.approved_by = admin_telegram_id
    payment.approved_at = approved_at
    order.transition_to(OrderStatus.PAID)

    return OutboxMessage(
        topic="PROVISION_PEER",
        idempotency_key=f"provision-order:{order.id}",
        payload={"order_id": str(order.id), "payment_id": str(payment.id)},
    )
