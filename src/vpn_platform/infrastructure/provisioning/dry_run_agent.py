import asyncio
import contextlib
import json
import os
import stat
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from vpn_platform.infrastructure.provisioning.agent_protocol import (
    AgentOperation,
    AgentRequest,
    AgentResponse,
)


class DryRunPeerRegistry:
    """Development-only state. It never calls awg or changes networking."""

    def __init__(self) -> None:
        self.peers: dict[str, dict[str, Any]] = {}
        self.idempotent_results: dict[str, dict[str, Any]] = {}

    def execute(self, request: AgentRequest) -> dict[str, Any]:
        if request.operation is AgentOperation.HEALTH:
            return {"status": "ok", "driver": "dry-run"}
        if request.operation is AgentOperation.READ_COUNTERS:
            return {
                "counters": [
                    {
                        "peer_id": peer_id,
                        "received_bytes": 0,
                        "transmitted_bytes": 0,
                        "last_handshake_unix": None,
                    }
                    for peer_id in request.payload.get("peer_ids", [])
                    if peer_id in self.peers
                ]
            }
        if request.idempotency_key in self.idempotent_results:
            return self.idempotent_results[request.idempotency_key]

        peer_id = str(UUID(request.payload["peer_id"]))
        if request.operation is AgentOperation.CREATE_PEER:
            required = {"profile_id", "public_key", "tunnel_ip"}
            if not required.issubset(request.payload):
                raise ValueError("create peer payload is incomplete")
            existing = self.peers.get(peer_id)
            if existing and existing != request.payload:
                raise ValueError("peer already exists with a different specification")
            self.peers[peer_id] = {**request.payload, "enabled": True}
            result = {"peer_id": peer_id, "status": "ENABLED"}
        elif request.operation is AgentOperation.ENABLE_PEER:
            self.peers[peer_id]["enabled"] = True
            result = {"peer_id": peer_id, "status": "ENABLED"}
        elif request.operation is AgentOperation.DISABLE_PEER:
            self.peers[peer_id]["enabled"] = False
            result = {"peer_id": peer_id, "status": "DISABLED"}
        elif request.operation is AgentOperation.DELETE_PEER:
            self.peers.pop(peer_id, None)
            result = {"peer_id": peer_id, "status": "DELETED"}
        else:
            raise ValueError(f"unsupported operation: {request.operation}")

        self.idempotent_results[request.idempotency_key] = result
        return result


class DryRunAgentServer:
    def __init__(self, socket_path: Path) -> None:
        self.socket_path = socket_path
        self.registry = DryRunPeerRegistry()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request_id = UUID(int=0)
        try:
            raw = await reader.readline()
            request = AgentRequest.model_validate_json(raw)
            request_id = request.request_id
            result = self.registry.execute(request)
            response = AgentResponse(request_id=request_id, ok=True, result=result)
        except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
            response = AgentResponse(
                request_id=request_id,
                ok=False,
                error_code="INVALID_REQUEST",
                error_message=str(exc),
            )
        writer.write(response.model_dump_json().encode() + b"\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def serve(self) -> None:
        self.socket_path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        if self.socket_path.exists():
            mode = self.socket_path.stat().st_mode
            if not stat.S_ISSOCK(mode):
                raise RuntimeError(f"refusing to replace non-socket path: {self.socket_path}")
            self.socket_path.unlink()

        server = await asyncio.start_unix_server(self._handle, path=self.socket_path)
        os.chmod(self.socket_path, 0o660)
        try:
            async with server:
                await server.serve_forever()
        finally:
            with contextlib.suppress(FileNotFoundError):
                self.socket_path.unlink()
