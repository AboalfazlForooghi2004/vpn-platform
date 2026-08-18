from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from vpn_platform.application.services.receipt_review import ReceiptSnapshot
from vpn_platform.infrastructure.db.models import PaymentReceiptModel


def receipt_snapshot(row: PaymentReceiptModel) -> ReceiptSnapshot:
    """Map an ORM row to the application-layer snapshot used for assessment."""
    return ReceiptSnapshot(
        receipt_id=row.id,
        payment_id=row.payment_id,
        sha256=row.sha256,
        telegram_file_unique_id=row.telegram_file_unique_id,
        mime_type=row.mime_type,
        size_bytes=row.size_bytes,
        submitted_at=row.submitted_at,
    )


async def find_receipt_fingerprint_matches(
    session: AsyncSession,
    *,
    sha256: str,
    telegram_file_unique_id: str,
    exclude_receipt_id: UUID | None = None,
    exclude_payment_id: UUID | None = None,
    limit: int = 50,
) -> Sequence[PaymentReceiptModel]:
    """Return earlier receipts sharing a content hash or Telegram file id.

    ``exclude_receipt_id`` removes the receipt being assessed so it cannot
    match itself; ``exclude_payment_id`` removes re-submissions for the same
    payment, because a receipt only signals fraud when it backs a *different*
    payment.
    """
    statement = (
        select(PaymentReceiptModel)
        .where(
            or_(
                PaymentReceiptModel.sha256 == sha256,
                PaymentReceiptModel.telegram_file_unique_id == telegram_file_unique_id,
            )
        )
        .order_by(PaymentReceiptModel.submitted_at)
        .limit(limit)
    )
    if exclude_receipt_id is not None:
        statement = statement.where(PaymentReceiptModel.id != exclude_receipt_id)
    if exclude_payment_id is not None:
        statement = statement.where(PaymentReceiptModel.payment_id != exclude_payment_id)
    return list((await session.scalars(statement)).all())


async def find_fingerprint_matches_batch(
    session: AsyncSession,
    *,
    pending: Sequence[PaymentReceiptModel],
    limit: int = 500,
) -> Sequence[PaymentReceiptModel]:
    """Fetch every committed receipt sharing a fingerprint with the queue.

    One query for the whole page, so the review endpoint never issues one
    query per receipt (no N+1).
    """
    sha256s = [receipt.sha256 for receipt in pending]
    file_ids = [receipt.telegram_file_unique_id for receipt in pending]
    if not sha256s and not file_ids:
        return []
    statement = (
        select(PaymentReceiptModel)
        .where(
            or_(
                PaymentReceiptModel.sha256.in_(sha256s),
                PaymentReceiptModel.telegram_file_unique_id.in_(file_ids),
            )
        )
        .order_by(PaymentReceiptModel.submitted_at)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())


async def list_pending_review_receipts(
    session: AsyncSession,
    *,
    limit: int = 100,
) -> Sequence[PaymentReceiptModel]:
    """Oldest-first queue of receipts waiting for an admin decision."""
    statement = (
        select(PaymentReceiptModel)
        .where(PaymentReceiptModel.review_status == "PENDING_REVIEW")
        .order_by(PaymentReceiptModel.submitted_at)
        .limit(limit)
    )
    return list((await session.scalars(statement)).all())
