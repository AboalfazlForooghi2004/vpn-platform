from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from vpn_platform.infrastructure.db.models import PaymentReceiptModel

async def find_receipt_fingerprint_matches(
    session: AsyncSession,
    *,
    sha256: str,
    telegram_file_unique_id: str,
    limit: int = 50,
) -> Sequence[PaymentReceiptModel]:
    """Return earlier receipts sharing a content hash or Telegram file id."""
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
