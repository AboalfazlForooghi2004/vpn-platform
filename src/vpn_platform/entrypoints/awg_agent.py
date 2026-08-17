import argparse
import asyncio
from pathlib import Path

from vpn_platform.config import get_settings
from vpn_platform.infrastructure.provisioning.dry_run_agent import DryRunAgentServer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local AmneziaWG Agent")
    parser.add_argument("--dry-run", action="store_true", help="never change network state")
    parser.add_argument("--socket", type=Path, help="Unix socket path")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if not args.dry_run:
        raise RuntimeError(
            "production AWG driver is intentionally unavailable until VPS OS/kernel validation"
        )
    socket_path = args.socket or get_settings().awg_agent_socket
    await DryRunAgentServer(socket_path).serve()


def run() -> None:
    asyncio.run(main())
