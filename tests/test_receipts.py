from uuid import UUID, uuid4

from vpn_platform.domain.receipts import (
    MAX_RECEIPT_BYTES,
    ReceiptFingerprint,
    ReceiptFlag,
    assess_receipt,
)


def _existing(
    payment_id: UUID | None = None,
    sha256: str = "a" * 64,
    file_id: str = "tg-1",
) -> ReceiptFingerprint:
    return ReceiptFingerprint(
        payment_id=payment_id or uuid4(),
        sha256=sha256,
        telegram_file_unique_id=file_id,
    )


def test_clean_receipt_has_no_flags() -> None:
    assessment = assess_receipt(
        sha256="b" * 64,
        telegram_file_unique_id="tg-2",
        mime_type="image/jpeg",
        size_bytes=1024,
        existing=[_existing()],
    )
    assert assessment.is_clean
    assert not assessment.needs_admin_attention
    assert assessment.duplicate_payment_ids == ()


def test_same_hash_is_flagged_with_originating_payments() -> None:
    first, second = uuid4(), uuid4()
    assessment = assess_receipt(
        sha256="a" * 64,
        telegram_file_unique_id="tg-new",
        mime_type="image/png",
        size_bytes=2048,
        existing=[
            _existing(payment_id=first, sha256="a" * 64, file_id="tg-1"),
            _existing(payment_id=second, sha256="a" * 64, file_id="tg-2"),
        ],
    )
    assert ReceiptFlag.DUPLICATE_HASH in assessment.flags
    assert assessment.duplicate_payment_ids == (first, second)
    assert assessment.needs_admin_attention


def test_same_telegram_file_is_flagged_even_with_new_hash() -> None:
    original = uuid4()
    assessment = assess_receipt(
        sha256="c" * 64,
        telegram_file_unique_id="tg-1",
        mime_type="application/pdf",
        size_bytes=2048,
        existing=[_existing(payment_id=original)],
    )
    assert ReceiptFlag.DUPLICATE_TELEGRAM_FILE in assessment.flags
    assert ReceiptFlag.DUPLICATE_HASH not in assessment.flags
    assert assessment.duplicate_payment_ids == (original,)


def test_oversized_and_unknown_media_are_flagged() -> None:
    assessment = assess_receipt(
        sha256="d" * 64,
        telegram_file_unique_id="tg-9",
        mime_type="application/octet-stream",
        size_bytes=MAX_RECEIPT_BYTES + 1,
        existing=[],
    )
    assert ReceiptFlag.OVERSIZED in assessment.flags
    assert ReceiptFlag.UNSUPPORTED_MEDIA_TYPE in assessment.flags


def test_mime_check_is_case_and_whitespace_insensitive() -> None:
    assessment = assess_receipt(
        sha256="e" * 64,
        telegram_file_unique_id="tg-10",
        mime_type=" Image/PNG ",
        size_bytes=100,
        existing=[],
    )
    assert assessment.is_clean
