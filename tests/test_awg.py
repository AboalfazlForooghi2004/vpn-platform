from vpn_platform.domain.awg import AwgProfile, ClientPeerConfig, render_client_config
from vpn_platform.domain.ipam import candidate_tunnel_ips


def profile() -> AwgProfile:
    return AwgProfile(
        server_public_key="server-public-key",
        endpoint="198.51.100.10:585",
        dns=("1.1.1.1", "9.9.9.9"),
        mtu=1280,
        jc=5,
        jmin=20,
        jmax=100,
        s1=64,
        s2=128,
        s3=32,
        s4=48,
        h1=1001,
        h2=1002,
        h3=1003,
        h4=1004,
        i1="<b 0x01>",
    )


def test_render_client_config_contains_awg2_fields() -> None:
    config = render_client_config(
        profile(),
        ClientPeerConfig(
            private_key="client-private-key",
            tunnel_ip="10.77.0.2",
            preshared_key="peer-psk",
        ),
    )
    assert "[Interface]" in config
    assert "PrivateKey = client-private-key" in config
    assert "Address = 10.77.0.2/32" in config
    assert "S3 = 32" in config
    assert "H4 = 1004" in config
    assert "I1 = <b 0x01>" in config
    assert "[Peer]" in config
    assert "Endpoint = 198.51.100.10:585" in config
    assert config.endswith("\n")


def test_ipam_skips_server_allocated_and_quarantined_addresses() -> None:
    addresses = candidate_tunnel_ips(
        "10.77.0.0/29",
        server_ip="10.77.0.1",
        allocated={"10.77.0.2"},
        quarantined={"10.77.0.3"},
    )
    assert str(next(addresses)) == "10.77.0.4"
