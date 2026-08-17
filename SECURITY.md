# Security policy

## Secret handling

Never commit Telegram tokens, GitHub tokens, AWG private keys, client configs, card details, receipts, database dumps, or encryption keys. Use environment variables or the deployment secret store.

A generated AmneziaWG `.conf` contains a client private key and must be handled as a password. Application and agent logs must redact key material and config bodies.

## Reporting

Report vulnerabilities privately to the repository owner. Do not open a public issue containing credentials, receipts, personal data, or a working exploit.

## MVP boundaries

The dry-run AWG agent is a development adapter. It does not modify a real interface. A production driver must be implemented and audited only after the target VPS OS, kernel, and AWG runtime are confirmed.
