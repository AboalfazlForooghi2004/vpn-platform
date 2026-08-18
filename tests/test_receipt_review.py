from datetime import UTC, datetime
from uuid import UUID, uuid4

from vpn_platform.application.services.receipt_review import (
    ReceiptSnapshot,
    build_review_queue,
)
from vpn_platform.domain.receipts import ReceiptFlag


def _snapshot(
    receipt_id: UUID | None = None,
    payment_id: UUID | None = None,
    sha256: str = "a" * 64,
    file_id: str = "tg-1",
    mime_type: str = "image/jpeg",
    size_bytes: int = 1024,
) -> ReceiptSnapshot:
    return ReceiptSnapshot(
        receipt_id=receipt_id or uuid4(),
        payment_id=payment_id or uuid4(),
        sha256=sha256,
        telegram_file_unique_id=file_id,
        mime_type=mime_type,
        size_bytes=size_bytes,
        submitted_at=datetime.now(UTC),
    )


def test_duplicate_from_another_payment_is_flagged() -> None:
    pending = _snapshot(sha256="b" * 64, file_id="tg-new")
    earlier = _snapshot(sha256="b" * 64, file_id="tg-old")

    (item,) = build_review_queue(pending=[pending], matches=[earlier])

    assert ReceiptFlag.DUPLICATE_HASH.value in item.flags
    assert item.needs_admin_attention
    assert item.duplicate_payment_ids == (str(earlier.payment_id),)


def test_resubmission_for_same_payment_is_not_flagged() -> None:
    payment_id = uuid4()
    pending = _snapshot(payment_id=payment_id, sha256="c" * 64, file_id="tg-2")
    previous = _snapshot(payment_id=payment_id, sha256="c" * 64, file_id="tg-1")

    (item,) = build_review_queue(pending=[pending], matches=[previous])

    assert item.flags == ()
    assert not item.needs_admin_attention


def test_receipt_never_matches_itself() -> None:
    pending = _snapshot()

    (item,) = build_review_queue(pending=[pending], matches=[pending])

    assert item.flags == ()
    assert not item.needs_admin_attention


def test_unrelated_matches_do_not_flag() -> None:
    pending = _snapshot(sha256="d" * 64, file_id="tg-10")
    unrelated = _snapshot(sha256="e" * 64, file_id="tg-99")

    (item,) = build_review_queue(pending=[pending], matches=[unrelated])

    assert item.flags == ()
    assert not item.needs_admin_attention


def test_queue_order_is_preserved() -> None:
    first = _snapshot(sha256="f" * 64, file_id="tg-20")
    second = _snapshot(sha256="0" * 64, file_id="tg-21")

    items = build_review_queue(pending=[first, second], matches=[])

    assert [item.receipt_id for item in items] == [first.receipt_id, second.receipt_id]
    assert items[0].flags == ()
    assert items[1].flags == ()


def test_flags_are_sorted_deterministically() -> None:
    huge_bad = _snapshot(mime_type="text/html", size_bytes=11 * 1024 * 1024)

    (item,) = build_review_queue(pending=[huge_bad], matches=[])

    assert item.flags == (
        ReceiptFlag.OVERSIZED.value,
        ReceiptFlag.UNSUPPORTED_MEDIA_TYPE.value,
    )
    assert item.needs_admin_attention
