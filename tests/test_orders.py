from uuid import uuid4

import pytest

from vpn_platform.domain.errors import InvalidTransition
from vpn_platform.domain.orders import Order, OrderStatus


def make_order(status: OrderStatus) -> Order:
    return Order(
        id=uuid4(),
        user_id=uuid4(),
        status=status,
        amount=1_000_000,
        currency="IRR",
    )


def test_happy_path_transitions() -> None:
    order = make_order(OrderStatus.CREATED)
    for status in (
        OrderStatus.AWAITING_RECEIPT,
        OrderStatus.UNDER_REVIEW,
        OrderStatus.PAID,
        OrderStatus.PROVISIONING,
        OrderStatus.COMPLETED,
    ):
        order.transition_to(status)
    assert order.status is OrderStatus.COMPLETED


def test_receipt_does_not_skip_human_review() -> None:
    order = make_order(OrderStatus.AWAITING_RECEIPT)
    with pytest.raises(InvalidTransition):
        order.transition_to(OrderStatus.PAID)
