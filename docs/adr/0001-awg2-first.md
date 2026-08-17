# ADR 0001: AmneziaWG 2.0 first

- Status: Accepted
- Date: 2026-08-17

## Context

The product must sell AmneziaWG access and deliver Amnezia-compatible configs. Stage 0 has one small VPS and must prove sales before infrastructure expansion. Official self-hosted documentation currently covers AWG 2.0; AWG 3.0 self-hosted is not yet the production default.

## Decision

Use AmneziaWG 2.0 as the only Stage 0 transport. Deliver one `.conf` per device and optionally a QR encoding the same config. Each device receives an independent peer, key pair, tunnel IP, lifecycle, and usage counters.

Active AWG profiles are immutable. A port or obfuscation-parameter change creates a new profile/interface and a controlled config reissue migration.

## Consequences

- No Xray or Remnawave dependency in Stage 0.
- UDP reachability must be tested on target networks.
- Renewal normally preserves the existing peer/config.
- Generic Xray subscription semantics are not promised.
- AWG 3.0 requires a later ADR after official self-hosted support and migration tests.
