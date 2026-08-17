from uuid import uuid4

import pytest

from vpn_platform.domain.errors import LedgerInvariantError
from vpn_platform.domain.wallet import LedgerEntry, LedgerTransaction


def test_balanced_wallet_transaction() -> None:
    transaction = LedgerTransaction(
        idempotency_key="refund:order-1",
        reason="service outage compensation",
        entries=(
            LedgerEntry(uuid4(), 100_000, "IRR"),
            LedgerEntry(uuid4(), -100_000, "IRR"),
        ),
    )
    assert sum(entry.amount for entry in transaction.entries) == 0


def test_unbalanced_wallet_transaction_is_rejected() -> None:
    with pytest.raises(LedgerInvariantError, match="sum to zero"):
        LedgerTransaction(
            idempotency_key="broken",
            reason="must fail",
            entries=(
                LedgerEntry(uuid4(), 100_000, "IRR"),
                LedgerEntry(uuid4(), -90_000, "IRR"),
            ),
        )
