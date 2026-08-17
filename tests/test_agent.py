from uuid import uuid4

from vpn_platform.infrastructure.provisioning.agent_protocol import AgentOperation, AgentRequest
from vpn_platform.infrastructure.provisioning.dry_run_agent import DryRunPeerRegistry


def test_dry_run_agent_create_disable_delete_idempotently() -> None:
    registry = DryRunPeerRegistry()
    peer_id = uuid4()
    profile_id = uuid4()
    create = AgentRequest(
        operation=AgentOperation.CREATE_PEER,
        idempotency_key="create:1",
        payload={
            "peer_id": str(peer_id),
            "profile_id": str(profile_id),
            "public_key": "public-key",
            "tunnel_ip": "10.77.0.2",
            "preshared_key": None,
        },
    )
    assert registry.execute(create)["status"] == "ENABLED"
    assert registry.execute(create)["status"] == "ENABLED"

    disable = AgentRequest(
        operation=AgentOperation.DISABLE_PEER,
        idempotency_key="disable:1",
        payload={"peer_id": str(peer_id)},
    )
    assert registry.execute(disable)["status"] == "DISABLED"

    delete = AgentRequest(
        operation=AgentOperation.DELETE_PEER,
        idempotency_key="delete:1",
        payload={"peer_id": str(peer_id)},
    )
    assert registry.execute(delete)["status"] == "DELETED"
    assert str(peer_id) not in registry.peers
