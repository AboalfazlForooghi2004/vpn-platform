from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from vpn_platform.application.services.receipt_review import build_review_queue
from vpn_platform.config import Settings
from vpn_platform.infrastructure.db.receipt_queries import (
    find_fingerprint_matches_batch,
    list_pending_review_receipts,
    receipt_snapshot,
)
from vpn_platform.infrastructure.db.session import session_scope
from vpn_platform.infrastructure.security.tokens import token_matches

bearer_scheme = HTTPBearer(auto_error=False)


async def require_admin(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> None:
    """Guard every /admin/* endpoint; fails closed when no token is configured."""
    settings: Settings = request.app.state.settings
    configured = settings.admin_api_token
    provided = credentials.credentials if credentials is not None else None
    expected = configured.get_secret_value() if configured is not None else None
    if not token_matches(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("/whoami")
async def whoami() -> dict[str, bool]:
    """Cheap probe that proves admin credentials work; touches no data."""
    return {"admin": True}


@admin_router.get("/receipts/pending-review")
async def pending_review_receipts(
    request: Request, response: Response, limit: int = 100
) -> dict[str, Any]:
    """Oldest-first review queue with review-time fraud assessment on each row."""
    response.headers["Cache-Control"] = "no-store"
    bounded_limit = min(max(limit, 1), 200)
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_scope(session_factory) as session:
        pending_rows = await list_pending_review_receipts(session, limit=bounded_limit)
        match_rows = await find_fingerprint_matches_batch(session, pending=pending_rows)
    pending = [receipt_snapshot(row) for row in pending_rows]
    matches = [receipt_snapshot(row) for row in match_rows]
    items = build_review_queue(pending=pending, matches=matches)
    return {
        "receipts": [
            {
                "id": str(item.receipt_id),
                "payment_id": str(item.payment_id),
                "sha256": item.sha256,
                "mime_type": item.mime_type,
                "size_bytes": item.size_bytes,
                "submitted_at": item.submitted_at.isoformat(),
                "flags": list(item.flags),
                "needs_admin_attention": item.needs_admin_attention,
                "duplicate_payment_ids": list(item.duplicate_payment_ids),
            }
            for item in items
        ]
    }
