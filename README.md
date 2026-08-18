# VPN Platform

MVP خصوصی فروش اشتراک **AmneziaWG 2.0** از طریق Telegram Bot.

## معماری

```text
Telegram Bot (long polling)
        ↓
Backend + PostgreSQL + Postgres Jobs/Outbox
        ↓
AmneziaWG Provisioner
        ↓
Local AWG Agent
        ↓
AmneziaWG 2.0 interface
```

هر خرید MVP یک دستگاه، یک peer، یک IP تونل و یک فایل `.conf` مستقل دارد.

## وضعیت فعلی

پیاده‌سازی‌شده در اولین milestone:

- مدل دامنه سفارش، پرداخت و state transitionها
- approval idempotent و outbox event قطعی
- Wallet Ledger دوبل با invariant مجموع صفر
- AWG profile، config generation و IPAM پایه
- قرارداد typed میان Backend و Local AWG Agent
- Agent توسعه‌ای `--dry-run` روی Unix socket
- مدل‌های PostgreSQL و migration اولیه
- health API و Bot `/start`
- job claimer مبتنی بر `FOR UPDATE SKIP LOCKED`
- احراز هویت admin: توکن Bearer با مقایسه constant-time برای API (fail-closed) و فیلتر `AdminOnlyFilter` در Bot
- ارزیابی تقلب رسید (hash/فایل تکراری، حجم و نوع رسانه) قبل از review ادمین
- سوییپر انقضای سفارش در worker با قفل ردیفی `FOR UPDATE SKIP LOCKED`
- تست‌های دامنه و CI

هنوز Production-ready نیست:

- driver واقعی AWG بعد از مشخص‌شدن OS/kernel VPS
- ذخیره‌سازی رمزگذاری‌شده receipt/config
- handler کامل سفارش و review رسید (فعلاً فقط لیست pending در admin API)
- usage poller و reconciliation واقعی
- deploy/hardening نهایی VPS

## شروع توسعه

نیازمندی: Python 3.13

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

برای PostgreSQL محلی:

```bash
docker compose up -d postgres
alembic upgrade head
```

اجرای API:

```bash
vpn-api
```

اجرای Agent بی‌خطر توسعه‌ای:

```bash
vpn-awg-agent --dry-run --socket ./runtime/awg-agent.sock
```

Agent بدون `--dry-run` عمداً اجرا نمی‌شود تا driver واقعی متناسب با VPS پیاده و audit شود.

## قواعد امنیتی

- هیچ token یا private key در Git قرار نمی‌گیرد.
- فایل `.conf` یک secret است.
- Agent management port عمومی ندارد.
- پرداخت فقط پس از تأیید صریح ادمین به `PAID` می‌رود.
- بدون `ADMIN_API_TOKEN` همه endpointهای `/admin/*` بسته می‌مانند (fail-closed).
- Bot مستقیماً data plane را فراخوانی نمی‌کند.
- profile فعال AWG immutable و migration نسخه‌دار است.

## اسناد

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/adr/0001-awg2-first.md`](docs/adr/0001-awg2-first.md)
- [`docs/adr/0002-postgres-outbox.md`](docs/adr/0002-postgres-outbox.md)
- [`SECURITY.md`](SECURITY.md)
