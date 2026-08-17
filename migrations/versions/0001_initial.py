"""Initial Stage 0 schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-17
"""

from collections.abc import Sequence

from alembic import op

from vpn_platform.infrastructure.db import models as _models  # noqa: F401
from vpn_platform.infrastructure.db.base import Base

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # This repository is still pre-production. The first migration mirrors the pinned
    # metadata; later migrations must use explicit Alembic operations.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
