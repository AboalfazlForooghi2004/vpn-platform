from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from vpn_platform.domain.errors import InvalidTransition


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    AWAITING_RECEIPT = "AWAITING_RECEIPT"
    UNDER_REVIEW = "UNDER_REVIEW"
    NEEDS_NEW_RECEIPT = "NEEDS_NEW_RECEIPT"
    PAID = "PAID"
    PROVISIONING = "PROVISIONING"
    COMPLETED = "COMPLETED"
    PROVISIONING_ERROR = "PROVISIONING_ERROR"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


_ALLOWED: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset({OrderStatus.AWAITING_RECEIPT}),
    OrderStatus.AWAITING_RECEIPT: frozenset({OrderStatus.UNDER_REVIEW, OrderStatus.EXPIRED}),
    OrderStatus.UNDER_REVIEW: frozenset(
        {OrderStatus.NEEDS_NEW_RECEIPT, OrderStatus.PAID, OrderStatus.REJECTED}
    ),
    OrderStatus.NEEDS_NEW_RECEIPT: frozenset({OrderStatus.UNDER_REVIEW, OrderStatus.EXPIRED}),
    OrderStatus.PAID: frozenset({OrderStatus.PROVISIONING}),
    OrderStatus.PROVISIONING: frozenset({OrderStatus.COMPLETED, OrderStatus.PROVISIONING_ERROR}),
    OrderStatus.PROVISIONING_ERROR: frozenset({OrderStatus.PROVISIONING}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.REJECTED: frozenset(),
    OrderStatus.EXPIRED: frozenset(),
}


@dataclass(slots=True)
class Order:
    id: UUID
    user_id: UUID
    status: OrderStatus
    amount: int
    currency: str

    def transition_to(self, target: OrderStatus) -> None:
        if target not in _ALLOWED[self.status]:
            raise InvalidTransition(f"order transition {self.status} -> {target} is not allowed")
        self.status = target
