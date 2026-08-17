# ADR 0002: PostgreSQL jobs and transactional outbox

- Status: Accepted
- Date: 2026-08-17

## Context

The pilot VPS has 2 GB RAM and does not need Redis, Celery, or Kafka. Payment approval and provisioning must remain atomic and retryable.

## Decision

Store jobs and outbox events in PostgreSQL. Insert the payment approval, order transition, audit record, and unique provisioning outbox event in one transaction. Workers claim due jobs using `FOR UPDATE SKIP LOCKED` and a lease.

## Consequences

- Duplicate admin clicks cannot create duplicate provisioning jobs.
- Workers can restart without losing accepted work.
- Job handlers must be idempotent.
- Queue scale is intentionally limited but sufficient for Stage 0.
