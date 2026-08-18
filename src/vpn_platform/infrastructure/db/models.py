from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from vpn_platform.infrastructure.db.base import Base


def uuid_pk() -> Mapped[UUID]:
    return mapped_column(primary_key=True, default=uuid4)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = uuid_pk()
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", nullable=False)
    locale: Mapped[str] = mapped_column(String(12), default="fa", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DeviceModel(Base):
    __tablename__ = "devices"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(80), nullable=False)
    platform: Mapped[str | None] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="ACTIVE", nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlanModel(Base):
    __tablename__ = "plans"

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    traffic_limit_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    device_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="IRR", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sales_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("duration_days > 0", name="duration_positive"),
        CheckConstraint("traffic_limit_bytes > 0", name="traffic_positive"),
        CheckConstraint("device_limit > 0", name="device_limit_positive"),
        CheckConstraint("price >= 0", name="price_nonnegative"),
    )


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("plans.id"), nullable=False)
    plan_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    amount_snapshot: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), default="NEW", nullable=False)
    target_subscription_id: Mapped[UUID | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    __table_args__ = (
        Index(
            "ix_orders_expiry_sweep",
            "status",
            "expires_at",
            postgresql_where=text("status IN ('AWAITING_RECEIPT', 'NEEDS_NEW_RECEIPT')"),
        ),
    )


class DestinationCardModel(Base):
    __tablename__ = "destination_cards"

    id: Mapped[UUID] = uuid_pk()
    card_number_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    card_number_masked: Mapped[str] = mapped_column(String(32), nullable=False)
    holder_name: Mapped[str] = mapped_column(String(160), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    method: Mapped[str] = mapped_column(String(24), default="CARD_TO_CARD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    destination_card_id: Mapped[UUID] = mapped_column(
        ForeignKey("destination_cards.id"), nullable=False
    )
    payer_card_last4: Mapped[str | None] = mapped_column(String(4))
    transfer_reference: Mapped[str | None] = mapped_column(String(80))
    approved_by: Mapped[int | None] = mapped_column(BigInteger)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(String(240))


class PaymentReceiptModel(Base):
    __tablename__ = "payment_receipts"

    id: Mapped[UUID] = uuid_pk()
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id"), nullable=False)
    telegram_file_unique_id: Mapped[str] = mapped_column(String(160), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(String(500))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    __table_args__ = (
        Index("ix_receipt_sha256", "sha256"),
        Index("ix_receipt_telegram_unique", "telegram_file_unique_id"),
        CheckConstraint("size_bytes > 0", name="receipt_size_positive"),
    )


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    traffic_limit_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    used_bytes_projection: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    suspension_reason: Mapped[str | None] = mapped_column(String(160))
    __table_args__ = (
        CheckConstraint("traffic_limit_bytes > 0", name="subscription_traffic_positive"),
        CheckConstraint("used_bytes_projection >= 0", name="usage_nonnegative"),
    )


class AwgProfileModel(Base):
    __tablename__ = "awg_profiles"

    id: Mapped[UUID] = uuid_pk()
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    node_id: Mapped[str] = mapped_column(String(80), nullable=False)
    interface_name: Mapped[str] = mapped_column(String(32), nullable=False)
    listen_port: Mapped[int] = mapped_column(Integer, nullable=False)
    tunnel_cidr: Mapped[str] = mapped_column(String(64), nullable=False)
    server_public_key: Mapped[str] = mapped_column(String(128), nullable=False)
    server_private_key_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    dns_servers: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    mtu: Mapped[int] = mapped_column(Integer, nullable=False)
    awg_parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    __table_args__ = (
        UniqueConstraint("node_id", "interface_name", name="uq_profile_node_interface"),
        UniqueConstraint("node_id", "listen_port", name="uq_profile_node_port"),
        CheckConstraint("listen_port > 0 AND listen_port <= 65535", name="port_range"),
    )


class AwgPeerModel(Base):
    __tablename__ = "awg_peers"

    id: Mapped[UUID] = uuid_pk()
    subscription_id: Mapped[UUID] = mapped_column(ForeignKey("subscriptions.id"), nullable=False)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id"), nullable=False)
    profile_id: Mapped[UUID] = mapped_column(ForeignKey("awg_profiles.id"), nullable=False)
    tunnel_ip: Mapped[str] = mapped_column(String(64), nullable=False)
    public_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    private_key_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    preshared_key_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    remote_revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_handshake_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rx_bytes_total: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    tx_bytes_total: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    counter_epoch: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    __table_args__ = (
        UniqueConstraint("profile_id", "tunnel_ip", name="uq_peer_profile_tunnel_ip"),
        UniqueConstraint("device_id", "profile_id", name="uq_peer_device_profile"),
        CheckConstraint("rx_bytes_total >= 0", name="rx_nonnegative"),
        CheckConstraint("tx_bytes_total >= 0", name="tx_nonnegative"),
    )


class WalletAccountModel(Base):
    __tablename__ = "wallet_accounts"

    id: Mapped[UUID] = uuid_pk()
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (
        UniqueConstraint(
            "user_id", "account_type", "currency", name="uq_wallet_owner_type_currency"
        ),
    )


class WalletTransactionModel(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[UUID] = uuid_pk()
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(40))
    reference_id: Mapped[UUID | None] = mapped_column()
    actor_telegram_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WalletEntryModel(Base):
    __tablename__ = "wallet_entries"

    id: Mapped[UUID] = uuid_pk()
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("wallet_transactions.id"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(ForeignKey("wallet_accounts.id"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    __table_args__ = (CheckConstraint("amount <> 0", name="wallet_entry_nonzero"),)


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[UUID] = uuid_pk()
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[str | None] = mapped_column(String(120))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    __table_args__ = (Index("ix_jobs_claim", "status", "run_at", "lease_until"),)


class OutboxEventModel(Base):
    __tablename__ = "outbox_events"

    id: Mapped[UUID] = uuid_pk()
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = uuid_pk()
    actor_type: Mapped[str] = mapped_column(String(24), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(60), nullable=False)
    target_id: Mapped[str] = mapped_column(String(120), nullable=False)
    audit_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
