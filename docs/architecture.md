# Architecture

## Source of truth

PostgreSQL owns financial state, subscription entitlement, device allocation, desired peer state, jobs, outbox events, and audit history. The AWG runtime is a projection and is reconciled from desired state.

## Trust boundaries

- Telegram users are untrusted.
- Receipt files are untrusted private uploads.
- Bot handlers call application services; they never execute AWG commands.
- Backend runs unprivileged.
- AWG Agent is privileged and reachable only through a permission-restricted Unix socket in Stage 0.
- Key/config plaintext must not enter logs, traces, analytics, or audit metadata.

## Main lifecycle

```text
Order.AWAITING_RECEIPT
  → Receipt.PENDING_REVIEW
  → admin approval transaction
  → Payment.APPROVED + Order.PAID + outbox(PROVISION_PEER)
  → worker claims the unique job
  → Agent creates the peer idempotently
  → Backend stores allocation/config secret
  → Subscription.ACTIVE
  → Bot delivers .conf and QR
```

## Failure handling

- Unknown provisioning outcomes are reconciled before retrying create.
- Delivery retries reuse the existing peer and config.
- Interface restart is not required per sale.
- On reboot, desired peers are compared with runtime peers.
- AWG profile parameters and port are immutable while active; migration creates another profile.

## Scaling path

Stage 0 uses a local Unix socket. After revenue proof, Bot/Backend/PostgreSQL move to a control VPS and the same typed Agent contract is exposed over private mTLS to one or more AWG nodes.
