"""Review-time receipt fraud assessment for the admin review queue.

Assessment is recomputed from committed data at review time (not only at
upload time), so a duplicate submitted after an upload-time snapshot would
still be flagged when the admin opens the queue.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from vpn_platform.domain.receipts import ReceiptFingerprint, assess_receipt


@dataclass(frozen=True, slots=True)
class ReceiptSnapshot:
    """Persisted receipt data the review queue reasons about."""

    receipt_id: UUID
    payment_id: UUID
    sha256: str
    telegram_file_unique_id: str
    mime_type: str
    size_bytes: int
    submitted_at: datetime


@dataclass(frozen=True, slots=True)
class ReceiptReviewItem:
    """DTO-ready queue entry: receipt fields plus its fraud assessment."""

    receipt_id: UUID
    payment_id: UUID
    sha256: str
    mime_type: str
    size_bytes: int
    submitted_at: datetime
    flags: tuple[str, ...]
    needs_admin_attention: bool
    duplicate_payment_ids: tuple[str, ...]


def build_review_queue(
    *,
    pending: Sequence[ReceiptSnapshot],
    matches: Sequence[ReceiptSnapshot],
) -> list[ReceiptReviewItem]:
    """Attach a fresh fraud assessment to every pending receipt.

    ``matches`` are committed receipts sharing fingerprints with the queue,
    fetched with a single batch query. A receipt is compared only against
    *other payments'* receipts: it never matches itself, and a re-submission
    for the same payment is not fraud.
    """
    items: list[ReceiptReviewItem] = []
    for receipt in pending:
        existing = [
            ReceiptFingerprint(
                payment_id=match.payment_id,
                sha256=match.sha256,
                telegram_file_unique_id=match.telegram_file_unique_id,
            )
            for match in matches
            if match.receipt_id != receipt.receipt_id
            and match.payment_id != receipt.payment_id
            and (
                match.sha256 == receipt.sha256
                or match.telegram_file_unique_id == receipt.telegram_file_unique_id
            )
        ]
        assessment = assess_receipt(
            sha256=receipt.sha256,
            telegram_file_unique_id=receipt.telegram_file_unique_id,
            mime_type=receipt.mime_type,
            size_bytes=receipt.size_bytes,
            existing=existing,
        )
        items.append(
            ReceiptReviewItem(
                receipt_id=receipt.receipt_id,
                payment_id=receipt.payment_id,
                sha256=receipt.sha256,
                mime_type=receipt.mime_type,
                size_bytes=receipt.size_bytes,
                submitted_at=receipt.submitted_at,
                flags=tuple(flag.value for flag in sorted(assessment.flags)),
                needs_admin_attention=assessment.needs_admin_attention,
                duplicate_payment_ids=tuple(
                    str(payment_id) for payment_id in assessment.duplicate_payment_ids
                ),
            )
        )
    return items
