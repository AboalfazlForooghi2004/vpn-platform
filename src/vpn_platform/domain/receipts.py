"""Receipt fraud assessment for the manual card-to-card review flow.

Every receipt is stored and reviewed; this module never blocks a submission.
It flags suspicious uploads so the admin review UI can render a warning before
an operator trusts the evidence.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

MAX_RECEIPT_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "application/pdf"})

class ReceiptFlag(StrEnum):
    DUPLICATE_HASH = "DUPLICATE_HASH"
    DUPLICATE_TELEGRAM_FILE = "DUPLICATE_TELEGRAM_FILE"
    OVERSIZED = "OVERSIZED"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"

@dataclass(frozen=True, slots=True)
class ReceiptFingerprint:
    """Persisted receipt identity used to catch reused evidence."""

    payment_id: UUID
    sha256: str
    telegram_file_unique_id: str

@dataclass(frozen=True, slots=True)
class ReceiptAssessment:
    flags: frozenset[ReceiptFlag]
    duplicate_payment_ids: tuple[UUID, ...]

    @property
    def is_clean(self) -> bool:
        return not self.flags

    @property
    def needs_admin_attention(self) -> bool:
        return bool(self.flags)

def assess_receipt(
    *,
    sha256: str,
    telegram_file_unique_id: str,
    mime_type: str,
    size_bytes: int,
    existing: Iterable[ReceiptFingerprint],
) -> ReceiptAssessment:
    """Flag risky receipts before an admin sees them.

    ``existing`` holds fingerprints of previously stored receipts (the caller
    excludes the receipt being assessed). A receipt identical in content hash
    or Telegram file id to an earlier submission is a fraud signal: the same
    card-to-card receipt must never back two different payments.
    """
    flags: set[ReceiptFlag] = set()
    duplicate_ids: list[UUID] = []
    for receipt in existing:
        content_match = receipt.sha256 == sha256
        file_match = receipt.telegram_file_unique_id == telegram_file_unique_id
        if not (content_match or file_match):
            continue
        if content_match:
            flags.add(ReceiptFlag.DUPLICATE_HASH)
        if file_match:
            flags.add(ReceiptFlag.DUPLICATE_TELEGRAM_FILE)
        if receipt.payment_id not in duplicate_ids:
            duplicate_ids.append(receipt.payment_id)

    if size_bytes > MAX_RECEIPT_BYTES:
        flags.add(ReceiptFlag.OVERSIZED)
    if mime_type.strip().lower() not in ALLOWED_MIME_TYPES:
        flags.add(ReceiptFlag.UNSUPPORTED_MEDIA_TYPE)

    return ReceiptAssessment(flags=frozenset(flags), duplicate_payment_ids=tuple(duplicate_ids))
