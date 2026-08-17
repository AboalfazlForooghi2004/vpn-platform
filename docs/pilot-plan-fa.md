# برنامه پایلوت تک‌سروره فروش AmneziaWG

**وضعیت:** معماری جاری و مبنای پیاده‌سازی  
**تاریخ:** ۱۷ اوت ۲۰۲۶  
**جایگزین:** نسخه قبلی Reality/Xray این فایل  

---

## ۱. تصمیم نهایی MVP

هدف MVP فروش خودکار دسترسی **AmneziaWG** است، نه VLESS Reality.

```text
Telegram Bot
   │
   ▼
Backend + PostgreSQL + Job Runner
   │
   ▼
Local AWG Agent
   │
   ▼
AmneziaWG 2.0 Server
   │
   ▼
فایل اختصاصی .conf برای هر دستگاه
```

تصمیم‌ها:

- پروتکل MVP: **AmneziaWG 2.0 Self-hosted**
- کلاینت اصلی: AmneziaVPN و در صورت تست، اپ مستقل AmneziaWG
- تحویل اصلی: فایل `.conf` اختصاصی
- تحویل کمکی: QR همان کانفیگ
- روش پرداخت: کارت‌به‌کارت، ارسال رسید و تأیید دستی ادمین
- زیرساخت: همان VPS موجود
- مدیریت peerها: Backend و AWG Agent خودمان
- Remnawave و Xray در MVP نصب نمی‌شوند.
- AWG 3.0 تا زمان انتشار و مستندسازی رسمی Self-hosted وارد Production نمی‌شود.
- Mini App، referral، cashback، reseller و multi-region بعد از اثبات فروش‌اند.

---

## ۲. نسخه پروتکل

در حال حاضر برای Self-hosted از **AWG 2.0** استفاده می‌کنیم.

- AWG 2.0 برای Self-hosted مستند رسمی دارد.
- AmneziaVPN نسخه 4.8.12.9 و بالاتر طبق مستندات رسمی AWG 2.0 را پشتیبانی می‌کند؛ برای کاربران نسخه به‌روز توصیه و در تست پذیرش ثبت می‌شود.
- AWG 3.0 در کلاینت‌های جدید ارائه شده، اما مستندات رسمی هنوز نصب Self-hosted آن را آماده اعلام نکرده‌اند.
- AWG 2.0 و AWG 3.0 را backward-compatible فرض نمی‌کنیم.

منابع رسمی:

- https://docs.amnezia.org/documentation/amnezia-wg/
- https://docs.amnezia.org/documentation/instructions/new-amneziawg-selfhosted/
- https://docs.amnezia.org/faq/

### سیاست ارتقا

پارامترهای AWG server-wide هستند. تغییر S/H/port درجا می‌تواند کانفیگ‌های موجود را از کار بیندازد. بنابراین:

- هر مجموعه پارامتر یک `awg_profile` نسخه‌دار است.
- profile فعال بعد از فروش بدون migration plan و تست تغییر نمی‌کند.
- برای ارتقا، interface/profile جدید روی پورت دیگر بالا می‌آید.
- کاربران به‌تدریج کانفیگ جدید دریافت می‌کنند.
- profile قبلی تا پایان migration روشن می‌ماند.

---

## ۳. مشخصات VPS و امکان‌پذیری

مشخصات اعلام‌شده، با فرض اینکه RAM واقعاً ۲GB است:

- 2 vCPU
- 2 GB RAM
- 20 GB NVMe
- 1 TB ترافیک ماهانه
- پورت 1 Gbit/s

برای AWG 2.0، Bot و Backend سبک مناسب است، ولی این موارد حذف می‌شوند:

- Remnawave
- Xray
- Redis/Celery
- Grafana/Loki/Prometheus
- MinIO
- Mini App

اگر RAM واقعی ۱GB باشد، قبل از Production حداقل به ۲GB ارتقا می‌دهیم.

---

## ۴. توپولوژی تک‌سروره

```text
Telegram User
      │
      │ outbound long polling
      ▼
┌───────────────────────────────────────────┐
│ VPS                                       │
│                                           │
│  App                                      │
│  ├─ Telegram Bot                          │
│  ├─ Order/Payment/Receipt Review          │
│  ├─ Subscription Lifecycle                │
│  ├─ Config Delivery                       │
│  └─ Postgres-backed Job Runner            │
│                                           │
│  PostgreSQL                               │
│  Local AWG Agent                          │
│  AmneziaWG 2.0 interface                  │
│  Private encrypted receipt/config store   │
│  Backup + Health Jobs                     │
└───────────────────────────────────────────┘
```

### اجزای اصلی

1. `app`
   - FastAPI برای endpointهای داخلی و آینده
   - aiogram برای Bot long polling
   - state machine مالی
   - job runner مبتنی بر PostgreSQL
2. `postgres`
   - منبع حقیقت تجاری و فنی
3. `awg-agent`
   - سرویس privileged محلی
   - ساخت، حذف، suspend و restore peer
   - خواندن transfer counters
   - apply اتمیک تنظیمات
4. `amneziawg`
   - AWG 2.0 pinned
   - interface و UDP listener
5. `backup-job`
   - backup رمزگذاری‌شده خارج از VPS

---

## ۵. شبکه و پورت‌ها

AWG روی UDP اجرا می‌شود؛ Bot با long polling نیازی به public webhook ندارد.

| پورت | سرویس | دسترسی |
|---:|---|---|
| UDP/انتخابی | AmneziaWG 2.0 | عمومی |
| TCP/22 | SSH | key-only و محدود |
| PostgreSQL | Database | فقط local/private network |
| AWG Agent | Unix socket یا private network | هرگز عمومی |
| App internal API | Backend | فقط local/private network |

پورت AWG بعد از تست انتخاب می‌شود. گزینه‌های اولیه:

- UDP/443
- UDP/585
- UDP/1234

مستندات رسمی برای برخی شبکه‌های محدود، پورت زیر 9999 را پیشنهاد می‌کند. اگر UDP/443 استفاده شود، reverse proxy نباید HTTP/3/QUIC را روی همان UDP port bind کند. TCP/443 و UDP/443 می‌توانند هم‌زمان برای دو سرویس متفاوت استفاده شوند.

### Endpoint

برای پایلوت می‌توان از IP ثابت استفاده کرد:

```text
Endpoint = SERVER_IPV4:AWG_PORT
```

دامنه DNS-only بهتر است:

```text
Endpoint = edge.example.com:AWG_PORT
```

دامنه AWG نباید پشت CDN معمولی قرار گیرد، مگر آن CDN واقعاً UDP موردنیاز را proxy کند.

---

## ۶. آنچه کاربر دریافت می‌کند

بعد از تأیید پرداخت، Bot این گزینه‌ها را نمایش می‌دهد:

- `دانلود کانفیگ AmneziaWG`
- `نمایش QR`
- `آموزش اتصال در AmneziaVPN`
- `دریافت مجدد کانفیگ`
- `ابطال و ساخت کانفیگ جدید`
- `مشاهده حجم و تاریخ انقضا`
- `تمدید`

### خروجی اصلی

فایل per-device:

```text
customer-DEVICE_ALIAS.conf
```

ساختار مفهومی:

```ini
[Interface]
PrivateKey = CLIENT_PRIVATE_KEY
Address = CLIENT_TUNNEL_IP/32
DNS = SELECTED_DNS
MTU = TESTED_MTU
Jc = PROFILE_JC
Jmin = PROFILE_JMIN
Jmax = PROFILE_JMAX
S1 = PROFILE_S1
S2 = PROFILE_S2
S3 = PROFILE_S3
S4 = PROFILE_S4
H1 = PROFILE_H1_RANGE
H2 = PROFILE_H2_RANGE
H3 = PROFILE_H3_RANGE
H4 = PROFILE_H4_RANGE
I1 = PROFILE_I1

[Peer]
PublicKey = SERVER_PUBLIC_KEY
PresharedKey = OPTIONAL_PER_PEER_PSK
Endpoint = SERVER_ENDPOINT
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = TESTED_VALUE
```

مقادیر واقعی باید توسط ابزار pinned و profile معتبر تولید شوند؛ پارامترهای نمونه اینترنتی نباید کورکورانه در Production کپی شوند.

### فرمت تحویل

- `.conf` فرمت اصلی و قابل تست است.
- QR دقیقاً همان config را encode می‌کند.
- `vpn://` فقط پس از round-trip test روی Android، iOS، Windows و macOS اضافه می‌شود.
- لینک generic subscription مانند Xray را برای AWG تضمین نمی‌کنیم.
- Bot می‌تواند فایل جاری را دوباره ارسال کند، اما تغییر profile ممکن است نیازمند import مجدد باشد.

### قاعده دستگاه

هر فایل برابر یک peer و یک دستگاه است:

```text
1 config = 1 device = 1 peer = 1 tunnel IP
```

یک config نباید بین چند مشتری فروخته یا به‌صورت پیش‌فرض بین چند دستگاه share شود. پلن چنددستگاهی چند peer مستقل می‌سازد.

---

## ۷. AWG Profile

جدول `awg_profiles`:

- `id`
- `version`
- `interface_name`
- `listen_port`
- `tunnel_cidr`
- `server_public_key`
- reference امن به server private key
- `dns_servers`
- `mtu`
- `jc`
- `jmin`
- `jmax`
- `s1` تا `s4`
- `h1` تا `h4`
- `i1` تا `i5`
- `persistent_keepalive`
- `status` — `STAGING / ACTIVE / DRAINING / RETIRED`
- `created_at`

Constraintها:

- `(interface_name, listen_port)` معتبر و بدون conflict باشد.
- فقط profile تست‌شده `ACTIVE` شود.
- تغییر پارامترهای profile فعال ممنوع؛ نسخه جدید ساخته شود.
- private key و PSK در log یا audit metadata قرار نگیرند.

---

## ۸. Peer و IPAM

جدول `awg_peers` یا `allocations`:

- `id`
- `subscription_id`
- `device_id`
- `profile_id`
- `tunnel_ip`
- `public_key`
- `private_key_encrypted`
- `preshared_key_encrypted` در صورت استفاده
- `status`
- `created_at`
- `enabled_at`
- `disabled_at`
- `last_handshake_at`
- `rx_bytes_total`
- `tx_bytes_total`
- `counter_epoch`

Constraintهای ضروری:

- `(profile_id, tunnel_ip)` unique
- `public_key` unique
- هر subscription/device فقط یک peer فعال در هر profile
- IP آزادشده بلافاصله reuse نشود؛ quarantine داشته باشد.

### مدیریت private key

دو مدل ممکن است:

1. تولید روی دستگاه؛ امن‌تر ولی UX پیچیده‌تر.
2. تولید در Backend/Agent و نگهداری رمزگذاری‌شده؛ مناسب MVP و دریافت مجدد.

برای Bot MVP مدل دوم استفاده می‌شود:

- key در Agent تولید می‌شود.
- plaintext فقط برای ساخت config در حافظه ظاهر می‌شود.
- در DB با envelope encryption ذخیره می‌شود.
- ادمین عادی plaintext را نمی‌بیند.
- log، exception و audit آن را ثبت نمی‌کنند.
- با «ابطال و ساخت جدید»، peer قبلی حذف و key جدید ساخته می‌شود.

---

## ۹. AWG Agent

Bot و Backend نباید shell command خام اجرا کنند. Agent یک API محدود روی Unix socket دارد:

```text
create_peer(idempotency_key, profile_id, tunnel_ip, public_key)
enable_peer(peer_id)
disable_peer(peer_id)
delete_peer(peer_id)
get_peer_stats(peer_id)
reconcile(profile_id, desired_peers)
health_check()
```

### الزامات Agent

- privileged ولی بدون public port
- ورودی‌های strongly typed
- allowlist عملیات
- file lock هنگام تغییر config
- write به فایل temporary و atomic rename
- apply با `awg set` یا `awg syncconf` معتبر
- عدم restart کل interface برای هر خرید
- timeout و rollback
- idempotency key
- audit بدون key/config کامل
- version pin برای `amneziawg-go/tools` یا kernel module

### منبع حقیقت

PostgreSQL منبع حقیقت است. فایل server config یک projection از peerهای فعال است.

پس از restart:

1. interface بالا می‌آید.
2. Agent وضعیت runtime را می‌خواند.
3. Backend peerهای مطلوب را از DB می‌فرستد.
4. reconciliation peerهای جاافتاده را اضافه و peerهای غیرمجاز را حذف می‌کند.
5. تا پایان reconciliation فروش جدید می‌تواند موقتاً pause شود.

---

## ۱۰. جریان خرید و پرداخت

```text
انتخاب پلن
   ↓
Order = AWAITING_RECEIPT
   ↓
نمایش مبلغ + کارت مقصد + کد سفارش
   ↓
ارسال تصویر رسید
   ↓
Receipt = PENDING_REVIEW
   ↓
ارسال به چت خصوصی ادمین
   ↓
[تأیید] [رد] [درخواست رسید جدید]
   ↓
Confirmation دوم
   ↓
DB transaction:
Payment=APPROVED + Order=PAID + Outbox Job
   ↓
Create AWG Peer
   ↓
Generate encrypted config
   ↓
Subscription=ACTIVE
   ↓
ارسال فایل .conf و QR
```

### idempotency

- تأیید تکراری فقط یک peer می‌سازد.
- retry Agent از همان idempotency key استفاده می‌کند.
- قطع‌شدن app بعد از `PAID` با outbox جبران می‌شود.
- اگر peer ساخته شد ولی ارسال فایل شکست خورد، job delivery retry می‌شود و peer جدید ساخته نمی‌شود.

---

## ۱۱. تمدید، حجم و تعلیق

### تمدید

- رسید تمدید همان مسیر review را دارد.
- `expires_at` از بزرگ‌ترِ زمان فعلی یا انقضای فعلی محاسبه می‌شود.
- peer، tunnel IP و config بدون دلیل تغییر نمی‌کنند.
- peer منقضی پس از تمدید مجدداً enable می‌شود.

### مصرف

Agent counterهای peer را از AWG می‌خواند:

```text
usage = received_bytes + transmitted_bytes
```

Backend snapshot و delta را ثبت می‌کند. reset counter پس از restart با `counter_epoch` تشخیص داده می‌شود تا مصرف منفی یا رایگان ایجاد نشود.

### پایان زمان یا حجم

1. subscription به `SUSPENDING` می‌رود.
2. Agent peer را disable/remove می‌کند.
3. نتیجه در audit ثبت می‌شود.
4. subscription به `SUSPENDED` یا `EXPIRED` می‌رود.
5. Bot دلیل عمومی و دکمه تمدید را نمایش می‌دهد.

در MVP rate limit per-user نداریم؛ فقط حجم، مدت و lifecycle کنترل می‌شوند.

---

## ۱۲. مدل حداقلی دیتابیس

- `users`
- `devices`
- `plans`
- `orders`
- `payments`
- `payment_receipts`
- `destination_cards`
- `subscriptions`
- `awg_profiles`
- `awg_peers`
- `usage_snapshots`
- `wallet_accounts`
- `wallet_transactions`
- `wallet_entries`
- `payment_applications`
- `jobs`
- `outbox_events`
- `audit_logs`
- `telegram_updates`

Constraintهای کلیدی:

- `users.telegram_id` unique
- `payments.order_id` unique
- `jobs.idempotency_key` unique
- `telegram_updates.update_id` unique
- `(awg_profile_id, tunnel_ip)` unique
- `awg_peers.public_key` unique
- `wallet_transactions.idempotency_key` unique
- مجموع entryهای هر ledger transaction برابر صفر
- transaction اتمیک برای `APPROVED + PAID + OUTBOX`

### Wallet Ledger داخلی

Ledger از روز اول پیاده می‌شود، حتی اگر دکمه «کیف پول» هنوز در UI عمومی نمایش داده نشود.

- balance یک ستون قابل‌ویرایش نیست؛ از `wallet_entries` یا projection تراکنشی محاسبه می‌شود.
- هر کاربر accountهای `AVAILABLE` و در صورت نیاز `RESERVED` دارد.
- accountهای سیستمی مانند `PLATFORM_CLEARING`، `PROMO_EXPENSE` و `SALES` جدا هستند.
- هر transaction دارای `idempotency_key`، currency، reason، actor و reference به payment/order/refund است.
- debit و credit هر transaction باید در یک DB transaction و با مجموع صفر ثبت شوند.
- موجودی منفی مجاز نیست، مگر rule صریح آینده.
- پرداخت مستقیم کارت‌به‌کارت می‌تواند مستقیماً به order اعمال شود؛ فقط وقتی اعتبار، refund یا پرداخت از wallet داریم، balance کاربر تغییر می‌کند.
- admin grant/refund بدون reason و audit مجاز نیست.
- برای خرید با wallet در آینده ابتدا مبلغ `RESERVED` و پس از موفقیت provisioning نهایی می‌شود؛ در failure آزاد می‌گردد.

در لانچ عمومی، cashback، referral، top-up عمومی و خرید با wallet می‌توانند feature-flag خاموش باشند؛ اما schema، invariants و audit ledger حاضرند.

---

## ۱۳. امنیت

- SSH فقط key-based؛ password login و root مستقیم غیرفعال.
- Firewall فقط SSH و UDP مربوط به AWG را باز کند.
- PostgreSQL و Agent public bind نشوند.
- Telegram ID ادمین allowlist و حساب ادمین دارای 2FA باشد.
- server private key، client private key، PSK و Bot token secret هستند.
- فایل config در application log یا error tracker قرار نگیرد.
- نام فایل config شامل Telegram ID یا شماره تلفن نباشد.
- رسیدها و configها در storage خصوصی رمزگذاری شوند.
- فایل ارسال‌شده برای کاربر cache عمومی نداشته باشد.
- backup PostgreSQL و secret material خارج از VPS و رمزگذاری‌شده باشد.
- restore واقعاً تست شود.
- snapshot شرکت VPS جای backup مستقل را نمی‌گیرد.

---

## ۱۴. RAM، دیسک و ترافیک

### RAM

- یک app worker
- Postgres pool کوچک
- job runner سبک بدون Redis
- swap حدود 1 GB فقط برای جلوگیری از OOM
- بدون dashboardهای سنگین

### Disk

- log rotation حدود `10m × 3` برای هر سرویس
- receipt حداکثر حدود 5 MB
- retention مشخص برای رسید و config delivery artifact
- alert دیسک در 70٪ و وضعیت بحرانی در 85٪
- backup محلی پس از upload موفق خارج از VPS حذف شود.

### Traffic

پورت 1 Gbit/s تضمین throughput نیست. برای 1 TB سهمیه ماهانه:

```text
سقف فروش اولیه پیشنهادی ≈ 750 GB حجم اسمی
```

مثال:

- 25 دستگاه × 30GB
- 15 دستگاه × 50GB

حاشیه برای overhead پروتکل، تست، اختلاف counter و عملیات نگهداری است. اگر 1 TB اضافه واقعاً با هزینه اعلام‌شده فعال می‌شود، سقف فروش پس از تأیید AUP و روش billing قابل افزایش است.

---

## ۱۵. تست پذیرش

### کلاینت‌ها

حداقل روی این موارد تست شود:

- Android — نسخه به‌روز AmneziaVPN
- iOS — نسخه به‌روز AmneziaVPN/AmneziaWG طبق فرمت پشتیبانی‌شده
- Windows — نسخه به‌روز
- macOS — فقط پس از تست DNS، route و reconnect

### تست config

- import فایل `.conf`
- scan QR
- اتصال اولیه
- reconnect پس از تغییر شبکه Wi-Fi/mobile
- reboot دستگاه
- DNS leak test
- MTU و سایت‌های حجیم
- IPv4-only در MVP
- config اشتباه یا منقضی

### تست سرور

- create 20 peer آزمایشی
- add/remove بدون restart interface
- restart AWG و reconciliation
- restart VPS
- counter reset handling
- پایان حجم و suspend
- تمدید و enable مجدد
- backup/restore
- duplicate approve
- delivery retry

### تست شبکه هدف

- چند ISP ثابت
- اپراتورهای موبایل هدف
- UDP/443، UDP/585 و UDP/1234
- ساعات شلوغ
- packet loss و roaming

هیچ پورت یا profile بدون تست شبکه هدف به‌عنوان پیش‌فرض نهایی انتخاب نمی‌شود.

---

## ۱۶. تجربه کاربری Bot

منوی MVP:

- خرید اشتراک
- اشتراک‌های من
- دریافت کانفیگ Amnezia
- نمایش QR
- حجم و زمان باقی‌مانده
- تمدید
- ابطال دستگاه
- آموزش اتصال
- پشتیبانی

صفحه هر اشتراک:

```text
نام سرویس
وضعیت: فعال
پروتکل: AmneziaWG 2.0
دستگاه: Android-1
حجم مصرفی / کل
تاریخ انقضا
آخرین اتصال، در صورت موجود بودن
```

دکمه‌ها:

- `دانلود .conf`
- `نمایش QR`
- `تمدید`
- `تعویض کانفیگ`
- `حذف دستگاه`

---

## ۱۷. گسترش پس از اثبات فروش

ترتیب منطقی:

1. VPS کنترل جدا برای Bot، Backend و PostgreSQL
2. باقی‌ماندن VPS فعلی به‌عنوان AWG Node
3. تبدیل Local Agent به Remote Agent با mTLS
4. node دوم و profile/node scheduler
5. Config Delivery Gateway دامنه‌دار
6. Mini App
7. wallet/referral/reseller
8. بررسی AWG 3.0 فقط پس از Self-hosted رسمی و تست migration
9. افزودن Reality فقط در صورت نیاز به fallback TCP

معماری گسترش:

```text
Telegram Bot / Mini App
          │
          ▼
Backend + PostgreSQL + Worker
          │
          ├──► AWG Agent — Node 1
          ├──► AWG Agent — Node 2
          └──► Optional Reality Provisioner
```

---

## ۱۸. Sprint اول

- [ ] تأیید OS، RAM واقعی، IPv4، کشور و مجازی‌ساز VPS
- [ ] تأیید امکان UDP و انتخاب سه پورت آزمایشی
- [ ] انتخاب نسخه pinned AWG 2.0
- [ ] نصب interface آزمایشی و ساخت یک config دستی معتبر
- [ ] تست config روی AmneziaVPN Android/Windows و سپس iOS/macOS
- [ ] تثبیت profile، MTU، DNS و port
- [ ] ساخت PostgreSQL schema
- [ ] ساخت Bot long polling
- [ ] پیاده‌سازی کارت‌به‌کارت و receipt review
- [ ] ساخت AWG Agent محلی
- [ ] پیاده‌سازی IPAM و peer lifecycle
- [ ] تولید `.conf` و QR
- [ ] پیاده‌سازی counter polling و suspend
- [ ] تست idempotency و restart/reconciliation
- [ ] backup خارج از VPS
- [ ] عرضه محدود با stop-sale

---

## ۱۹. اطلاعات باقی‌مانده

برای بررسی VPS:

```bash
printf '\n=== OS ===\n'; cat /etc/os-release
printf '\n=== CPU ===\n'; nproc; lscpu | grep -E 'Model name|Architecture' | head
printf '\n=== RAM ===\n'; free -h
printf '\n=== DISK ===\n'; df -h /
printf '\n=== KERNEL ===\n'; uname -a
printf '\n=== VIRT ===\n'; systemd-detect-virt || true
printf '\n=== NETWORK ===\n'; ip -br addr
```

تصمیم‌های ثبت‌شده محصول:

- دستگاه‌های لانچ: Android، iOS، Windows و macOS
- هر خرید/اشتراک MVP: یک دستگاه، یک peer و یک فایل مستقل

اطلاعات محصول که باید تعیین شوند:

- حداقل نسخه قابل قبول AmneziaVPN پس از تست چهار پلتفرم
- حجم و مدت پلن‌ها
- DNS پیش‌فرض
- سیاست IPv6؛ پیشنهاد MVP: IPv4-only
- نگهداری یا rotate کردن config گم‌شده
- Telegram ID ادمین رسید
- شماره کارت و نام دارنده به‌صورت secret

---

# جمع‌بندی

معماری جاری پروژه:

```text
Bot فروش
+ کارت‌به‌کارت و تأیید دستی
+ PostgreSQL
+ AWG Agent
+ AmneziaWG 2.0
+ فایل .conf اختصاصی برای هر دستگاه
```

Reality/Xray و Remnawave از MVP حذف شدند. AWG 3.0 نیز تا زمان Self-hosted رسمی وارد Production نمی‌شود. مهم‌ترین دارایی نرم‌افزاری ما Backend مالی، state machine، IPAM، peer lifecycle، config delivery و audit است؛ خود AWG data plane پشت Agent قابل تعویض و توسعه باقی می‌ماند.
