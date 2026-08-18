from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vpn_platform.config import get_settings
from vpn_platform.infrastructure.db.receipt_queries import list_pending_review_receipts
from vpn_platform.infrastructure.db.session import session_scope
from vpn_platform.infrastructure.security.tokens import token_matches

bearer_scheme = HTTPBearer(auto_error=False)

async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Guard every /admin/* endpoint; fails closed when no token is configured."""
    settings = get_settings()
    configured = settings.admin_api_token
    provided = credentials.credentials if credentials is not None else None
    expected = configured.get_secret_value() if configured is not None else None
    if not token_matches(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing admin credentials",
        )

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)

@admin_router.get("/receipts/pending-review")
async def pending_review_receipts(request: Request, limit: int = 100) -> dict[str, Any]:
    """Oldest-first receipt review queue for the admin console."""
    bounded_limit = min(max(limit, 1), 200)
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_scope(session_factory) as session:
        receipts = await list_pending_review_receipts(session, limit=bounded_limit)
    return {
        "receipts": [
            {
                "id": str(receipt.id),
                "payment_id": str(receipt.payment_id),
                "sha256": receipt.sha256,
                "mime_type": receipt.mime_type,
                "size_bytes": receipt.size_bytes,
                "submitted_at": receipt.submitted_at.isoformat(),
            }
            for receipt in receipts
        ]
    }
