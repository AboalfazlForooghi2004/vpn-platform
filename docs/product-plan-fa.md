# برنامه جامع پیاده‌سازی پروژه VPN مبتنی بر AmneziaWG

**وضعیت:** سند مرجع جاری  
**تاریخ:** ۱۷ اوت ۲۰۲۶  
**نسخه معماری:** AWG2-first / بدون eBPF / بدون Xray در MVP

> نسخه قبلی Reality-first این سند منسوخ شده و فقط با نام `vpn-project-reality-plan-obsolete-fa.md` آرشیو شده است. برنامه اجرایی VPS در `vpn-single-vps-pilot-plan-fa.md` قرار دارد.

---

# ۱. هدف محصول

ساخت MVP فروش و مدیریت اشتراک VPN از طریق Telegram Bot با تجربه‌ای ساده شبیه محصولات تجاری موجود، بدون clone کامل یک کسب‌وکار یا ادعای دسترسی به زیرساخت خصوصی آن:

- نمایش پلن و مبلغ
- پرداخت کارت‌به‌کارت
- دریافت رسید و بررسی انسانی
- فعال‌سازی خودکار بعد از تأیید
- تحویل کانفیگ AmneziaWG
- مشاهده حجم و انقضا
- تمدید، تعلیق و revoke
- اعلان و پشتیبانی
- مدیریت فروش و ظرفیت توسط ادمین

معیار اصلی Stage 0، اثبات فروش و تمدید واقعی روی یک VPS است؛ نه ساخت زیرساخت بزرگ از روز اول.

---

# ۲. تصمیم معماری قطعی

```text
Telegram Bot — long polling
          │
          ▼
Backend Application
  ├─ Orders / Payments / Receipts
  ├─ Subscriptions / Devices
  ├─ Wallet Ledger
  ├─ Config Delivery
  └─ Admin Operations
          │
          ▼
PostgreSQL + Postgres-backed Jobs/Outbox
          │
          ▼
AmneziaWG Provisioner
          │
          ▼
Local AWG Agent ──► AmneziaWG 2.0 Interface
```

اصول:

1. Backend منبع حقیقت مالی و lifecycle است.
2. Bot مستقیماً به data plane وصل نمی‌شود.
3. هر دستگاه peer، key و IP مستقل دارد.
4. Provisioning باید idempotent و بعد از restart قابل بازیابی باشد.
5. فایل `.conf` حاوی private key است و مانند secret محافظت می‌شود.
6. profile فعال AWG درجا تغییر نمی‌کند؛ نسخه جدید ساخته می‌شود.
7. تک‌سروره‌بودن implementation فعلی است، نه coupling معماری.

---

# ۳. انتخاب پروتکل

## Production Stage 0

- **AmneziaWG 2.0 Self-hosted**
- UDP
- فایل per-device `.conf`
- QR مکمل
- نسخه به‌روز AmneziaVPN؛ حداقل پشتیبانی اعلام‌شده رسمی AWG2 برابر 4.8.12.9 است.

## چرا AWG 3.0 فعلاً نه؟

تا تاریخ این سند، راه رسمی Self-hosted برای AWG 3.0 هنوز در مستندات Amnezia آماده اعلام نشده است. بنابراین:

- AWG3 را production-ready فرض نمی‌کنیم.
- AWG2 و AWG3 را compatible فرض نمی‌کنیم.
- ارتقا در آینده با profile/interface جدید و migration تدریجی است.

منابع رسمی:

- https://docs.amnezia.org/documentation/amnezia-wg/
- https://docs.amnezia.org/documentation/instructions/new-amneziawg-selfhosted/
- https://docs.amnezia.org/documentation/instructions/connect-via-config/
- https://docs.amnezia.org/faq/
- https://docs.amnezia.org/troubleshooting/self-hosted-amneziawg-not-working/

## خارج از MVP

- Xray/Reality
- Remnawave
- چندپروتکلی
- eBPF/XDP/TC سفارشی
- AWG3 self-hosted آزمایشی

Reality بعداً فقط اگر نیاز واقعی به fallback TCP اثبات شد از طریق Provisioner جدا اضافه می‌شود.

---

# ۴. خروجی کاربر

برای هر دستگاه:

```text
1 device = 1 AWG peer = 1 tunnel IP = 1 private/public key pair
```

Backend این خروجی‌ها را فراهم می‌کند:

1. فایل `.conf` سازگار با AWG2
2. QR همان config
3. آموزش import در AmneziaVPN
4. دریافت مجدد config
5. rotation/revoke در صورت compromise

`vpn://` یک بهبود UX بعدی است و فقط پس از round-trip test روی کلاینت‌های هدف فعال می‌شود. generic subscription URL مدل Xray به AWG تعمیم داده نمی‌شود؛ اگر profile تغییر ناسازگار داشته باشد، کاربر باید کانفیگ جدید را import کند.

---

# ۵. محدوده Stage 0

## کاربر

- `/start` و ثبت کاربر
- فهرست پلن‌ها
- سفارش و نمایش مبلغ snapshotشده
- نمایش کارت مقصد و نام دارنده
- ارسال تصویر رسید
- مشاهده `در انتظار بررسی / تأیید / رد / نیازمند رسید جدید`
- دریافت `.conf` و QR پس از provisioning
- «اشتراک‌های من»
- مشاهده status، حجم و انقضا
- تمدید
- دریافت مجدد config
- revoke و ساخت config جدید
- پشتیبانی

## ادمین

- لیست سفارش‌ها و رسیدهای معطل
- مشاهده خصوصی receipt
- تأیید با confirmation دوم
- رد با reason کنترل‌شده
- درخواست رسید جدید
- تمدید، تعلیق و جبران قطعی
- revoke peer
- اعلان فردی/جمعی
- stop-sale برای plan یا node
- audit اقدامات

## feature-flag خاموش در لانچ

- Mini App
- کیف پول عمومی و top-up
- cashback
- referral
- reseller
- خرید عمده
- هدیه
- تمدید خودکار
- چند منطقه
- چند پروتکل

Wallet Ledger داخلی با وجود خاموش‌بودن UI عمومی از روز اول پیاده می‌شود.

---

# ۶. Stack سبک

- Python 3.13
- FastAPI
- aiogram 3
- SQLAlchemy 2
- Alembic
- PostgreSQL
- PostgreSQL job queue با `FOR UPDATE SKIP LOCKED`
- Docker Compose یا systemd برای استقرار اولیه
- `awg`/`amneziawg-go` یا kernel module نسخه pinشده پس از بررسی OS
- nftables
- backup رمزگذاری‌شده خارج از VPS

در Stage 0 Redis، Celery، Kafka، Kubernetes و monitoring سنگین نداریم.

---

# ۷. ساختار repository

```text
apps/
  bot/
  api/
  worker/
  scheduler/

modules/
  identity/
  catalog/
  ordering/
  payments/
  receipt_review/
  subscriptions/
  devices/
  wallet/
  provisioning/
  awg_profiles/
  usage/
  notifications/
  support/
  admin/
  audit/

integrations/
  telegram/
  manual_card_transfer/
  awg_agent/
  encrypted_storage/

infra/
  compose/
  systemd/
  nftables/
  backup/

migrations/
tests/
```

Domain serviceها نباید aiogram handler، SQL خام یا command سیستم را با منطق تجاری مخلوط کنند.

---

# ۸. مدل داده

## هویت و کاتالوگ

### `users`

- `id`
- `telegram_id` unique
- `status`
- `locale`
- `created_at`

### `devices`

- `id`
- `user_id`
- `alias`
- `platform`
- `status`
- `revoked_at`

### `plans`

- `id`
- `name`
- `duration_days`
- `traffic_limit_bytes`
- `device_limit`
- `price`
- `currency`
- `active`
- `sales_paused`

## سفارش و پرداخت

### `orders`

- `id`
- `user_id`
- `plan_id`
- `plan_snapshot_json`
- `amount_snapshot`
- `currency`
- `type` — `NEW / RENEWAL`
- `target_subscription_id` nullable
- `status`
- `expires_at`

### `payments`

- `id`
- `order_id` unique
- `method = CARD_TO_CARD`
- `status`
- `destination_card_id`
- `payer_card_last4` nullable
- `transfer_reference` nullable
- `approved_by`
- `approved_at`
- `rejection_reason`

### `payment_receipts`

- `id`
- `payment_id`
- `telegram_file_unique_id`
- `storage_key`
- `sha256`
- `mime_type`
- `size_bytes`
- `review_status`
- `reviewed_by`
- `reviewed_at`
- `review_note`

`file_unique_id` و SHA-256 فقط duplicate flag هستند؛ رد خودکار نمی‌کنند.

### `destination_cards`

- `id`
- `card_number_encrypted`
- `card_number_masked`
- `holder_name`
- `active`
- `priority`

## اشتراک و AWG

### `subscriptions`

- `id`
- `user_id`
- `plan_id`
- `status`
- `starts_at`
- `expires_at`
- `traffic_limit_bytes`
- `used_bytes_projection`
- `suspension_reason`

### `awg_profiles`

- `id`
- `version`
- `node_id`
- `interface_name`
- `listen_port`
- `tunnel_cidr`
- `server_public_key`
- secret reference برای private key
- `dns_servers`
- `mtu`
- `jc/jmin/jmax`
- `s1..s4`
- `h1..h4`
- `i1..i5`
- `status = STAGING/ACTIVE/DRAINING/RETIRED`

### `awg_peers`

- `id`
- `subscription_id`
- `device_id`
- `profile_id`
- `tunnel_ip`
- `public_key`
- `private_key_encrypted`
- `preshared_key_encrypted` nullable
- `status`
- `remote_revision`
- `last_handshake_at`
- `rx_bytes_total`
- `tx_bytes_total`
- `counter_epoch`

Constraintها:

- `(profile_id, tunnel_ip)` unique
- `public_key` unique
- یک peer فعال برای هر device/profile
- quarantine برای IP آزادشده

### `usage_snapshots`

- `peer_id`
- `runtime_rx`
- `runtime_tx`
- `delta_rx`
- `delta_tx`
- `counter_epoch`
- `captured_at`

## عملیات

- `jobs`
- `outbox_events`
- `telegram_updates`
- `audit_logs`
- `notifications`
- `support_tickets`

---

# ۹. Wallet Ledger داخلی

Wallet یک Ledger حسابداری است، نه ستون mutable به نام balance.

### جدول‌ها

- `wallet_accounts`
- `wallet_transactions`
- `wallet_entries`
- `payment_applications`

### accountها

- `USER_AVAILABLE`
- `USER_RESERVED`
- `PLATFORM_CLEARING`
- `PLATFORM_SALES`
- `PROMO_EXPENSE`

### invariants

- هر transaction یک `idempotency_key` یکتا دارد.
- currency در تمام entryهای transaction یکی است.
- مجموع debit/credit transaction صفر است.
- موجودی منفی کاربر مجاز نیست.
- balance از entryها یا projection تراکنشی به‌دست می‌آید.
- هر grant/refund/adjustment دارای actor، reason و audit است.
- order و payment با `payment_applications` به منبع پرداخت متصل می‌شوند.

### رفتار Stage 0

- خرید عادی کارت‌به‌کارت مستقیماً به order اعمال می‌شود.
- refund یا اعتبار جبرانی می‌تواند به `USER_AVAILABLE` وارد شود.
- UI کیف پول و top-up عمومی خاموش است.
- در آینده پرداخت wallet ابتدا reserve، سپس در موفقیت provisioning finalize و در failure release می‌شود.

---

# ۱۰. State Machine

## سفارش

```text
CREATED
  → AWAITING_RECEIPT
  → UNDER_REVIEW
  → PAID
  → PROVISIONING
  → COMPLETED
```

مسیرهای جانبی:

```text
AWAITING_RECEIPT → EXPIRED
UNDER_REVIEW → NEEDS_NEW_RECEIPT → UNDER_REVIEW
UNDER_REVIEW → REJECTED
PAID/PROVISIONING → PROVISIONING_ERROR → RETRY / MANUAL_REVIEW
```

## اشتراک

```text
PENDING
  → ACTIVE
  → SUSPENDING
  → SUSPENDED
  → ACTIVE     # renewal/enable
  → EXPIRED
  → REVOKED
```

## Peer

```text
REQUESTED
  → CREATING
  → ENABLED
  → DISABLING
  → DISABLED
  → DELETING
  → DELETED
```

`UNKNOWN` یا `ERROR` برای نتیجه نامشخص عملیات وجود دارد و فقط با reconciliation حل می‌شود؛ retry کورکورانه create ممنوع است.

---

# ۱۱. تراکنش تأیید پرداخت

اقدام ادمین `APPROVE` فقط زمانی موفق است که payment در `PENDING_REVIEW` باشد.

در یک DB transaction:

1. lock روی payment/order گرفته می‌شود.
2. payment به `APPROVED` می‌رود.
3. `approved_by` و `approved_at` ثبت می‌شوند.
4. order به `PAID` می‌رود.
5. audit ثبت می‌شود.
6. outbox/job با idempotency key یکتا ایجاد می‌شود.

ارسال receipt هرگز خودکار سرویس را فعال نمی‌کند. OCR در MVP تصمیم‌گیر نیست.

---

# ۱۲. Provisioning Contract

Backend فقط interface زیر را می‌شناسد:

```text
create_peer(allocation_id, profile_id, tunnel_ip, key_material_ref)
enable_peer(peer_id)
disable_peer(peer_id)
delete_peer(peer_id)
read_counters(peer_ids)
reconcile(profile_id, desired_state)
health_check()
```

پیاده‌سازی Stage 0:

```text
AmneziaWGProvisioner → LocalAwgAgent
```

در مقیاس بعدی:

```text
AmneziaWGProvisioner → RemoteAwgAgent over mTLS
```

هر operation دارای `idempotency_key` و timeout است. داده‌های user-controlled به command shell interpolate نمی‌شوند.

---

# ۱۳. AWG Agent

Agent تنها بخش privileged است.

## transport

- تک‌سروره: Unix socket
- چندسروره: HTTPS خصوصی با mTLS و allowlist
- هیچ public management endpoint

## عملیات

- validate profile
- allocate/apply peer
- enable/disable/delete
- read handshake/counter
- projection config از desired state
- apply اتمیک با ابزار pinned AWG
- reconcile runtime و DB

## safety

- lock per-interface
- temporary file و atomic rename
- `awg set` یا `awg syncconf` مطابق نسخه تست‌شده
- بدون restart interface برای هر خرید
- health/readiness مستقل
- audit بدون private key و config plaintext
- command allowlist و typed input
- حداقل privilege ممکن

## restart recovery

1. runtime خوانده می‌شود.
2. desired peers از PostgreSQL می‌آیند.
3. missing peerها اضافه می‌شوند.
4. unauthorized peerها حذف می‌شوند.
5. counter epoch اصلاح می‌شود.
6. فروش فقط پس از readiness فعال می‌شود.

---

# ۱۴. AWG Profile و تغییرات ناسازگار

پارامترهای `Jc/Jmin/Jmax/S1-S4/H1-H4/I1-I5` و پورت باید با config سرور و کلاینت سازگار باشند.

قوانین:

- profile `ACTIVE` immutable است.
- هر تغییر ناسازگار version جدید می‌سازد.
- profile جدید ابتدا `STAGING` است.
- تست Android/iOS/Windows/macOS و شبکه‌های هدف انجام می‌شود.
- سپس `ACTIVE` و profile قبلی `DRAINING` می‌شود.
- Bot به کاربران migration پیام می‌دهد.
- old profile تا مهلت اعلام‌شده فعال می‌ماند.

تمدید عادی profile یا peer را تغییر نمی‌دهد.

---

# ۱۵. Config Generation و Delivery

## تولید key

برای MVP، key pair در Agent/Backend trusted تولید و private key با envelope encryption ذخیره می‌شود تا «دریافت مجدد» ممکن باشد.

- plaintext در log، audit، exception و analytics ممنوع
- ادمین عادی private key را نمی‌بیند.
- decrypt فقط در مسیر مجاز config generation
- rotation با peer جدید و حذف peer قدیمی

## تحویل

اولویت:

1. ارسال فایل `.conf` به همان Telegram user
2. QR به‌صورت پیام محافظت‌شده در همان chat
3. `vpn://` فقط پس از تست

نام فایل شامل Telegram ID، شماره تلفن یا نام واقعی نیست.

اگر بعدها download endpoint اضافه شد:

- HTTPS
- token تصادفی یک‌بارمصرف یا کوتاه‌عمر
- hash token در DB
- `Cache-Control: no-store`
- عدم ثبت token/config در access log
- ownership check
- rate limit و revoke

---

# ۱۶. Usage Accounting و Quota

Worker در فاصله کوتاه counterهای هر peer را می‌خواند:

```text
billable_usage = rx_delta + tx_delta
```

ملاحظات:

- counter runtime ممکن است با restart reset شود.
- `counter_epoch` reset را تشخیص می‌دهد.
- delta منفی نباید به مصرف رایگان تبدیل شود.
- polling lag یک overshoot کوچک ایجاد می‌کند و در AUP لحاظ می‌شود.
- زمان/حجم در Backend enforce می‌شود، سپس peer در Agent disable می‌شود.
- reconciliation تأیید می‌کند peer واقعاً غیرفعال است.

در MVP rate limit per-user نداریم.

---

# ۱۷. تمدید، revoke و جبران

## تمدید

```text
new_expiry = max(now, current_expiry) + purchased_duration
```

- همان subscription حفظ می‌شود.
- همان peer/config حفظ می‌شود.
- peer غیرفعال در صورت اعتبار مجدد enable می‌شود.
- افزایش حجم طبق policy plan انجام می‌شود؛ reset یا add باید snapshot سفارش داشته باشد.

## revoke

- peer فعلی disable/delete می‌شود.
- key و tunnel IP جدید ساخته می‌شود.
- config قبلی دیگر کار نمی‌کند.
- دلیل و actor ثبت می‌شوند.

## جبران قطعی

- admin operation idempotent است.
- روز/حجم جبرانی به subscription یا wallet ledger افزوده می‌شود.
- مخاطبان، reason و مقدار snapshot می‌شوند.
- اجرای job قابل resume و audit است.

---

# ۱۸. Bot UX

## منوی اصلی

- خرید اشتراک
- اشتراک‌های من
- دریافت کانفیگ Amnezia
- تمدید
- آموزش اتصال
- پشتیبانی

## خرید

```text
پلن → خلاصه سفارش → مبلغ/کارت → ارسال رسید
→ انتظار بررسی → تأیید → ساخت peer → فایل/QR
```

## صفحه اشتراک

- نام پلن
- `AmneziaWG 2.0`
- وضعیت
- دستگاه
- حجم مصرفی/کل
- زمان باقی‌مانده
- آخرین handshake، اگر موجود
- دانلود config
- QR
- تمدید
- revoke

پیام‌ها باید تفاوت «رسید دریافت شد» با «پرداخت تأیید شد» را واضح بیان کنند.

---

# ۱۹. Admin UX

## صف رسید

هر کارت:

- order code
- user internal reference
- پلن و مبلغ snapshot
- کارت مقصد
- زمان سفارش/رسید
- تصویر خصوصی
- last4/reference در صورت موجودبودن
- duplicate warning

اقدامات:

- تأیید + confirmation دوم
- درخواست رسید جدید
- رد با reason
- escalate بررسی

## عملیات سرویس

- pause/unpause plan sales
- node stop-sale
- suspend/enable subscription
- revoke peer
- compensate
- resend config
- user notification
- audit lookup

---

# ۲۰. امنیت و حریم خصوصی

- SSH فقط key-based و allowlist در صورت امکان
- Bot admin ID allowlist + Telegram 2FA
- DB و Agent غیرعمومی
- nftables با default deny
- secret خارج از repository
- encryption at rest برای receipt و private key
- backup رمزگذاری‌شده خارج از VPS
- log redaction برای token، key، config، card و receipt
- dependency/image pinning
- upload size و MIME validation
- receipt بدون URL عمومی
- retention policy برای receipt/config artifact
- restore test واقعی
- admin action با actor/reason/timestamp

---

# ۲۱. پورت و DNS

AWG به UDP نیاز دارد. پورت نهایی با تست شبکه تعیین می‌شود؛ کاندیدها:

- UDP/443
- UDP/585
- UDP/1234

اگر UDP/443 استفاده شود، HTTP/3/QUIC reverse proxy روی همان پورت نباید bind شود. TCP/443 جداست.

Bot با long polling public inbound نیاز ندارد. برای Stage 0، Endpoint می‌تواند IP ثابت باشد؛ دامنه DNS-only مهاجرت IP را ساده‌تر می‌کند و نباید پشت CDN فاقد UDP قرار گیرد.

---

# ۲۲. ظرفیت و Stop-sale

VPS پایلوت:

- 2 vCPU
- 2GB RAM مفروض
- 20GB NVMe
- 1TB traffic
- 1Gbit/s port اسمی

سقف محافظه‌کارانه entitlement اولیه:

```text
حدود 750GB از 1TB
```

مثال:

- 25 اشتراک 30GB
- 15 اشتراک 50GB

Stop-sale خودکار/دستی در این شرایط:

- مصرف یا entitlement نزدیک سقف
- disk بحرانی
- backup ناموفق طولانی
- Agent/AWG unhealthy
- provisioning error بالا
- receipt review backlog خارج از SLA

---

# ۲۳. Jobs و Outbox

Jobهای اصلی:

- `PROVISION_PEER`
- `DELIVER_CONFIG`
- `ENABLE_PEER`
- `DISABLE_EXPIRED_PEER`
- `REVOKE_PEER`
- `POLL_USAGE`
- `RECONCILE_PROFILE`
- `EXPIRE_ORDERS`
- `SEND_NOTIFICATION`
- `APPLY_COMPENSATION`
- `BACKUP_DATABASE`
- `VERIFY_BACKUP`

هر job:

- idempotency key
- attempt count
- lease/lock timeout
- exponential backoff
- terminal/dead-letter state
- minimal redacted error
- manual retry action

Outbox و تغییر domain state در یک transaction ثبت می‌شوند.

---

# ۲۴. تست

## مالی

- receipt تکراری
- approve هم‌زمان توسط دو admin
- approve تکراری
- reject و receipt جایگزین
- order expired
- price change بعد از order
- wallet double-entry invariant
- duplicate ledger idempotency

## Provisioning

- create retry
- timeout با نتیجه نامعلوم
- duplicate job
- restart app بعد از PAID
- peer ساخته‌شده و delivery شکست‌خورده
- Agent restart
- server reboot
- runtime drift و reconcile
- tunnel IP race

## AWG

- import `.conf`
- QR
- Android/iOS/Windows/macOS هدف
- Wi-Fi/mobile roaming
- DNS/MTU
- restart interface
- disable/enable
- counter reset
- quota suspension
- چند ISP و پورت UDP

## امنیت

- admin authorization
- IDOR روی config/receipt
- path traversal در upload
- oversized/malformed file
- secret redaction
- backup access/restore
- Agent public exposure test

---

# ۲۵. معیار پذیرش End-to-End

این سناریو باید کامل، idempotent و پس از restart قابل بازیابی باشد:

```text
سفارش
→ رسید
→ بررسی و تأیید دستی
→ outbox/job
→ تخصیص IP و key
→ ایجاد AWG peer
→ تولید .conf و QR
→ import در Amnezia
→ اتصال و ثبت مصرف
→ پایان حجم/زمان و suspend
→ تمدید
→ enable همان peer بدون تعویض config
```

پذیرش تکمیلی:

- تأیید دوباره peer دوم نسازد.
- delivery retry config/peer جدید نسازد.
- peer مشترک بین مشتریان وجود نداشته باشد.
- private key در log دیده نشود.
- restart VPS وضعیت را از DB reconcile کند.
- تغییر profile فعال بدون migration ممکن نباشد.
- wallet transaction نامتوازن commit نشود.

---

# ۲۶. برنامه اجرا

## Sprint 0 — کشف فنی VPS و AWG

- تأیید OS، kernel، virt، RAM، disk، IPv4 و location
- تست UDP provider/firewall
- انتخاب implementation pinشده AWG2
- ساخت interface آزمایشی
- تولید config دستی
- تست سه پورت و کلاینت‌های هدف
- تثبیت MTU، DNS و profile

**Gate:** حداقل یک config AWG2 روی شبکه‌های هدف پایدار متصل شود.

## Sprint 1 — فروش و مالی

- schema و migration
- Bot long polling
- plans/orders/payments/receipts
- private admin review
- atomic approve/outbox
- Wallet Ledger و invariants
- audit و notification

**Gate:** پرداخت آزمایشی فقط با تأیید انسانی به job یکتا برسد.

## Sprint 2 — Provisioning

- IPAM
- Local AWG Agent
- create/disable/enable/revoke
- encrypted key storage
- `.conf` و QR
- delivery retry
- usage snapshots
- expiry/quota enforcement
- reconciliation

**Gate:** سناریوی End-to-End و restart test پاس شود.

## Sprint 3 — عرضه محدود

- backup/restore
- health/alert سبک
- stop-sale
- runbookها
- تست امنیتی
- پلن و قیمت نهایی
- عرضه محدود به گروه کوچک
- اندازه‌گیری conversion، support load و renewal

**Gate:** فقط پس از مشاهده رفتار واقعی، هزینه توسعه scale انجام شود.

---

# ۲۷. Runbookهای لازم

- AWG down
- Agent down
- PostgreSQL down
- disk full
- traffic cap نزدیک
- key compromise
- profile/port migration
- IP change
- receipt backlog
- mistaken payment approval
- duplicate receipt
- restore روی VPS تازه
- full node evacuation
- stop-sale و بازگشایی فروش

---

# ۲۸. مهاجرت بعد از اثبات فروش

1. تهیه control VPS
2. انتقال Bot، Backend و PostgreSQL
3. باقی‌ماندن VPS فعلی به‌عنوان AWG node
4. Remote Agent با mTLS
5. node دوم و scheduler ظرفیت
6. دامنه config gateway در صورت نیاز
7. Mini App
8. قابلیت‌های wallet/referral/reseller
9. AWG3 فقط پس از Self-hosted رسمی و migration test
10. Reality Provisioner فقط به‌عنوان fallback مبتنی بر نیاز واقعی

---

# ۲۹. اطلاعات لازم قبل از اجرا

خروجی VPS:

```bash
printf '\n=== OS ===\n'; cat /etc/os-release
printf '\n=== CPU ===\n'; nproc; lscpu | grep -E 'Model name|Architecture' | head
printf '\n=== RAM ===\n'; free -h
printf '\n=== DISK ===\n'; df -h /
printf '\n=== KERNEL ===\n'; uname -a
printf '\n=== VIRT ===\n'; systemd-detect-virt || true
printf '\n=== NETWORK ===\n'; ip -br addr
```

تصمیم‌های محصول:

تصمیم‌های ثبت‌شده:

- پلتفرم‌های لانچ: Android، iOS، Windows و macOS
- هر خرید/اشتراک در MVP: یک دستگاه، یک peer و یک فایل مستقل

موارد باقی‌مانده:

- حداقل نسخه AmneziaVPN پس از تست چهار پلتفرم
- حجم/مدت/قیمت
- currency و نمایش تومان/ریال
- DNS پیش‌فرض
- IPv4-only یا IPv6
- Telegram ID ادمین
- شماره کارت مقصد به‌صورت secret
- SLA بررسی receipt

---

# تصمیم نهایی

```text
Stage 0:
One VPS
+ Telegram Bot
+ Backend/PostgreSQL/Postgres Jobs
+ Card-to-Card Manual Review
+ Internal Wallet Ledger
+ Local AWG Agent
+ AmneziaWG 2.0
+ Per-device .conf/QR
```

این مسیر دقیقاً با انتخاب فعلی محصول هماهنگ است: سرویس فروخته‌شده **AmneziaWG** است و کاربر کانفیگ مخصوص Amnezia دریافت می‌کند. Reality، Remnawave و AWG3 جزو لانچ نیستند.
