from collections.abc import Iterator
from ipaddress import IPv4Address, IPv4Network, ip_address, ip_network


def candidate_tunnel_ips(
    cidr: str,
    *,
    server_ip: str,
    allocated: set[str] | None = None,
    quarantined: set[str] | None = None,
) -> Iterator[IPv4Address]:
    """Yield usable client addresses; the database unique constraint is the final lock."""
    network = ip_network(cidr, strict=True)
    if not isinstance(network, IPv4Network):
        raise ValueError("Stage 0 IPAM is IPv4-only")

    parsed_server = ip_address(server_ip)
    if not isinstance(parsed_server, IPv4Address) or parsed_server not in network:
        raise ValueError("server_ip must be an IPv4 host inside the tunnel network")

    excluded: set[IPv4Address] = {parsed_server}
    for value in (allocated or set()) | (quarantined or set()):
        parsed = ip_address(value)
        if not isinstance(parsed, IPv4Address):
            raise ValueError("allocated and quarantined addresses must be IPv4")
        excluded.add(parsed)

    for address in network.hosts():
        if address not in excluded:
            yield address
