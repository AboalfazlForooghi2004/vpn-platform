import asyncio
from pathlib import Path
from typing import Any
from uuid import UUID

from vpn_platform.application.ports.awg import AwgProvisioner, PeerCounters, PeerSpec
from vpn_platform.infrastructure.provisioning.agent_protocol import (
    AgentOperation,
    AgentRequest,
    AgentResponse,
)


class AgentCallError(RuntimeError):
    pass


class LocalAwgAgentClient(AwgProvisioner):
    def __init__(self, socket_path: Path, *, timeout_seconds: float = 5.0) -> None:
        self._socket_path = socket_path
        self._timeout = timeout_seconds

    async def _call(
        self,
        operation: AgentOperation,
        *,
        idempotency_key: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = AgentRequest(
            operation=operation,
            idempotency_key=idempotency_key,
            payload=payload or {},
        )

        async def exchange() -> AgentResponse:
            reader, writer = await asyncio.open_unix_connection(self._socket_path)
            try:
                writer.write(request.model_dump_json().encode() + b"\n")
                await writer.drain()
                raw = await reader.readline()
                if not raw:
                    raise AgentCallError("agent closed the connection without a response")
                return AgentResponse.model_validate_json(raw)
            finally:
                writer.close()
                await writer.wait_closed()

        response = await asyncio.wait_for(exchange(), timeout=self._timeout)
        if response.request_id != request.request_id:
            raise AgentCallError("agent response request_id mismatch")
        if not response.ok:
            raise AgentCallError(f"agent operation failed: {response.error_code or 'UNKNOWN'}")
        return response.result

    async def create_peer(self, spec: PeerSpec, *, idempotency_key: str) -> None:
        await self._call(
            AgentOperation.CREATE_PEER,
            idempotency_key=idempotency_key,
            payload={
                "peer_id": str(spec.peer_id),
                "profile_id": str(spec.profile_id),
                "public_key": spec.public_key,
                "tunnel_ip": spec.tunnel_ip,
                "preshared_key": spec.preshared_key,
            },
        )

    async def enable_peer(self, peer_id: UUID, *, idempotency_key: str) -> None:
        await self._call(
            AgentOperation.ENABLE_PEER,
            idempotency_key=idempotency_key,
            payload={"peer_id": str(peer_id)},
        )

    async def disable_peer(self, peer_id: UUID, *, idempotency_key: str) -> None:
        await self._call(
            AgentOperation.DISABLE_PEER,
            idempotency_key=idempotency_key,
            payload={"peer_id": str(peer_id)},
        )

    async def delete_peer(self, peer_id: UUID, *, idempotency_key: str) -> None:
        await self._call(
            AgentOperation.DELETE_PEER,
            idempotency_key=idempotency_key,
            payload={"peer_id": str(peer_id)},
        )

    async def read_counters(self, peer_ids: tuple[UUID, ...]) -> tuple[PeerCounters, ...]:
        result = await self._call(
            AgentOperation.READ_COUNTERS,
            idempotency_key="read:" + ",".join(map(str, peer_ids)),
            payload={"peer_ids": [str(peer_id) for peer_id in peer_ids]},
        )
        return tuple(
            PeerCounters(
                peer_id=UUID(item["peer_id"]),
                received_bytes=int(item["received_bytes"]),
                transmitted_bytes=int(item["transmitted_bytes"]),
                last_handshake_unix=item.get("last_handshake_unix"),
            )
            for item in result.get("counters", [])
        )

    async def health_check(self) -> bool:
        result = await self._call(
            AgentOperation.HEALTH,
            idempotency_key="health",
        )
        return result.get("status") == "ok"
