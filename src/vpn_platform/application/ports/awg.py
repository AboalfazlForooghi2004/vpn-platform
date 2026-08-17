from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PeerSpec:
    peer_id: UUID
    profile_id: UUID
    public_key: str
    tunnel_ip: str
    preshared_key: str | None = None


@dataclass(frozen=True, slots=True)
class PeerCounters:
    peer_id: UUID
    received_bytes: int
    transmitted_bytes: int
    last_handshake_unix: int | None


class AwgProvisioner(Protocol):
    async def create_peer(self, spec: PeerSpec, *, idempotency_key: str) -> None: ...

    async def enable_peer(self, peer_id: UUID, *, idempotency_key: str) -> None: ...

    async def disable_peer(self, peer_id: UUID, *, idempotency_key: str) -> None: ...

    async def delete_peer(self, peer_id: UUID, *, idempotency_key: str) -> None: ...

    async def read_counters(self, peer_ids: tuple[UUID, ...]) -> tuple[PeerCounters, ...]: ...

    async def health_check(self) -> bool: ...
