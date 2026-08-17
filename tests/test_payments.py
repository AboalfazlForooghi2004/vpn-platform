from datetime import UTC, datetime
from uuid import uuid4

import pytest

from vpn_platform.domain.errors import InvalidTransition
from vpn_platform.domain.orders import Order, OrderStatus
from vpn_platform.domain.payments import Payment, PaymentStatus, approve_payment


def test_approval_is_idempotent_and_uses_deterministic_outbox_key() -> None:
    order = Order(uuid4(), uuid4(), OrderStatus.UNDER_REVIEW, 500_000, "IRR")
    payment = Payment(uuid4(), order.id, PaymentStatus.PENDING_REVIEW)
    now = datetime.now(UTC)

    message = approve_payment(
        payment=payment,
        order=order,
        admin_telegram_id=12345,
        approved_at=now,
    )

    assert message is not None
    assert message.idempotency_key == f"provision-order:{order.id}"
    assert payment.status is PaymentStatus.APPROVED
    assert payment.approved_by == 12345
    assert order.status is OrderStatus.PAID

    duplicate = approve_payment(
        payment=payment,
        order=order,
        admin_telegram_id=12345,
        approved_at=now,
    )
    assert duplicate is None


def test_unreviewed_payment_cannot_be_approved() -> None:
    order = Order(uuid4(), uuid4(), OrderStatus.AWAITING_RECEIPT, 500_000, "IRR")
    payment = Payment(uuid4(), order.id, PaymentStatus.AWAITING_RECEIPT)
    with pytest.raises(InvalidTransition):
        approve_payment(
            payment=payment,
            order=order,
            admin_telegram_id=12345,
            approved_at=datetime.now(UTC),
        )
