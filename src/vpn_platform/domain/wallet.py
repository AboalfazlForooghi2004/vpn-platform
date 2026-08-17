from dataclasses import dataclass
from uuid import UUID

from vpn_platform.domain.errors import LedgerInvariantError


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    account_id: UUID
    amount: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount == 0:
            raise LedgerInvariantError("a ledger entry cannot have a zero amount")
        if not self.currency or self.currency != self.currency.upper():
            raise LedgerInvariantError("currency must be a non-empty uppercase code")


@dataclass(frozen=True, slots=True)
class LedgerTransaction:
    idempotency_key: str
    entries: tuple[LedgerEntry, ...]
    reason: str

    def __post_init__(self) -> None:
        if not self.idempotency_key:
            raise LedgerInvariantError("idempotency key is required")
        if not self.reason.strip():
            raise LedgerInvariantError("reason is required")
        if len(self.entries) < 2:
            raise LedgerInvariantError("a transaction requires at least two entries")

        currencies = {entry.currency for entry in self.entries}
        if len(currencies) != 1:
            raise LedgerInvariantError("all entries must use the same currency")
        if sum(entry.amount for entry in self.entries) != 0:
            raise LedgerInvariantError("ledger transaction must sum to zero")
