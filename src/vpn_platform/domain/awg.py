from dataclasses import dataclass
from ipaddress import IPv4Address, ip_address

from vpn_platform.domain.errors import InvalidAwgConfiguration


@dataclass(frozen=True, slots=True)
class AwgProfile:
    server_public_key: str
    endpoint: str
    dns: tuple[str, ...]
    mtu: int
    jc: int
    jmin: int
    jmax: int
    s1: int
    s2: int
    s3: int
    s4: int
    h1: int
    h2: int
    h3: int
    h4: int
    i1: str | None = None
    i2: str | None = None
    i3: str | None = None
    i4: str | None = None
    i5: str | None = None
    persistent_keepalive: int = 25

    def __post_init__(self) -> None:
        if not self.server_public_key.strip():
            raise InvalidAwgConfiguration("server public key is required")
        if not self.endpoint.strip() or ":" not in self.endpoint:
            raise InvalidAwgConfiguration("endpoint must include host and port")
        if not 576 <= self.mtu <= 1500:
            raise InvalidAwgConfiguration("MTU must be between 576 and 1500")
        if self.jmin > self.jmax:
            raise InvalidAwgConfiguration("Jmin cannot exceed Jmax")
        if not self.dns:
            raise InvalidAwgConfiguration("at least one DNS server is required")


@dataclass(frozen=True, slots=True)
class ClientPeerConfig:
    private_key: str
    tunnel_ip: str
    preshared_key: str | None = None

    def __post_init__(self) -> None:
        if not self.private_key.strip():
            raise InvalidAwgConfiguration("client private key is required")
        address = ip_address(self.tunnel_ip)
        if not isinstance(address, IPv4Address):
            raise InvalidAwgConfiguration("Stage 0 client address must be IPv4")


def render_client_config(profile: AwgProfile, peer: ClientPeerConfig) -> str:
    """Render an AWG2 config. The returned text is secret and must never be logged."""
    interface_lines = [
        "[Interface]",
        f"PrivateKey = {peer.private_key}",
        f"Address = {peer.tunnel_ip}/32",
        f"DNS = {', '.join(profile.dns)}",
        f"MTU = {profile.mtu}",
        f"Jc = {profile.jc}",
        f"Jmin = {profile.jmin}",
        f"Jmax = {profile.jmax}",
        f"S1 = {profile.s1}",
        f"S2 = {profile.s2}",
        f"S3 = {profile.s3}",
        f"S4 = {profile.s4}",
        f"H1 = {profile.h1}",
        f"H2 = {profile.h2}",
        f"H3 = {profile.h3}",
        f"H4 = {profile.h4}",
    ]
    for index, value in enumerate((profile.i1, profile.i2, profile.i3, profile.i4, profile.i5), 1):
        if value:
            interface_lines.append(f"I{index} = {value}")

    peer_lines = [
        "[Peer]",
        f"PublicKey = {profile.server_public_key}",
    ]
    if peer.preshared_key:
        peer_lines.append(f"PresharedKey = {peer.preshared_key}")
    peer_lines.extend(
        [
            f"Endpoint = {profile.endpoint}",
            "AllowedIPs = 0.0.0.0/0",
            f"PersistentKeepalive = {profile.persistent_keepalive}",
        ]
    )
    return "\n".join((*interface_lines, "", *peer_lines, ""))
