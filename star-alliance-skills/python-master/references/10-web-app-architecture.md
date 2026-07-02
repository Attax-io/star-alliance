---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Building Python Web Apps

An opinionated, batteries-included blueprint for shipping a small-to-mid SaaS app
solo or with a small team. It favors **boring, well-understood pieces wired the same
way every time** so a new app reaches "auth + billing + deploy" in hours, not weeks.

## The Default Stack

| Concern        | Default                                                        |
|----------------|---------------------------------------------------------------|
| Framework      | **FastAPI** (async), `uvicorn[standard]`                      |
| Packaging      | **uv** + `pyproject.toml` + `uv.lock`, hatchling, `src/` layout |
| Database       | **Postgres 16** + `asyncpg`, **SQLAlchemy 2.0** async, **Alembic** |
| Config         | **pydantic-settings** `BaseSettings`, env-prefixed, `@lru_cache` |
| Payments       | **Stripe ≥15**, one signed webhook, idempotency table         |
| Auth           | dependency guards + **bcrypt**; token scheme per app (see AUTH.md) |
| Frontend       | **Jinja2 + Tailwind (CDN) + Alpine.js**, *or* a decoupled SPA |
| Background work | **cron-as-worker** (same image, different command) — no Celery |
| Observability  | **Sentry + PostHog**, both no-op until keyed                  |
| Deploy         | **Docker** → managed platform (Render-style) via **Terraform** |
| Lint/test      | **ruff** + **pytest** + `pytest-asyncio`, Makefile entrypoint |

If you have no reason to deviate, use every row. The rest of this skill is the
"how", and the reference files hold copy-pasteable templates.

## Package Layout

One layered package, routers split by domain. Business logic never lives in a route.

```
src/myapp/
  main.py            # app + middleware + include_router() in a loop
  config.py          # pydantic-settings Settings + get_settings()
  db.py              # lazy async engine/sessionmaker + get_session() dep
  models.py          # SQLAlchemy 2.0 DeclarativeBase, Mapped[]
  schemas.py         # Pydantic request/response models
  security.py        # hashing, tokens, auth dependencies
  observability.py   # Sentry/PostHog init (guarded)
  api/               # one APIRouter module per domain (+ deps.py, webhooks.py)
  services/          # business logic; external SDKs isolated here
migrations/versions/ # Alembic
tests/               # pytest, mirrors api/ + services/
terraform/           # render.tf, stripe.tf, posthog.tf, variables.tf
Dockerfile  docker-compose.yml  pyproject.toml  uv.lock  alembic.ini  Makefile
```

**Routes → Services → Models.** Routes parse/validate and call services. Services
hold the logic and own all external SDK calls (Stripe, email, LLM) so they're
mockable. Models are persistence only.

## App Wiring

A module-level `app` (a factory is fine but unnecessary), routers registered in a
loop, cross-cutting concerns as middleware, and a health check that proves the DB
is reachable. Full template in **[STACK.md](STACK.md)**.

```python
# main.py (shape)
app = FastAPI(docs_url=None if settings.is_prod else "/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, ...)
# request-id + security-headers middleware, slowapi rate limiter
for router in (auth.router, billing.router, webhooks.router, ...):
    app.include_router(router)

@app.get("/health")
async def health(db: SessionDep):
    await db.execute(text("SELECT 1"))   # 503 if the DB is down
    return {"status": "ok"}
```

Share dependencies as `Annotated` type aliases — they read cleanly in signatures:

```python
# api/deps.py
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep    = Annotated[User, Depends(require_user)]
```

## Database

Lazy singleton async engine, `pool_pre_ping=True`, `expire_on_commit=False`, a
`get_session()` async-generator dependency, and a URL normalizer so platform-issued
`postgres://` URLs become `postgresql+asyncpg://`. **Postgres in prod, SQLite
(`aiosqlite`) for fast local/CI tests.** Migrations via Alembic, applied in the
deploy's pre-deploy step. See **[STACK.md](STACK.md)**.

## Config & Secrets

One `Settings(BaseSettings)` with an env prefix, `@lru_cache get_settings()`, and
**validators that refuse to boot in production with a default/missing secret**.
Commit a `.env.example`; never commit `.env`. Computed `@property` helpers
(`is_prod`, `cors_origins`, `billing_enabled`) keep routes clean.

## Payments

Stripe with **exactly one signature-verified webhook endpoint**, idempotency backed
by a persisted events table, and dispatch by event type that never 500s on an
unknown event. Isolate every SDK call in a `services/stripe/` module. Full patterns
(checkout, subscriptions, webhook handler, Terraform-provisioned signing secret) in
**[PAYMENTS.md](PAYMENTS.md)**.

## The Decisions You Actually Make

Everything above is fixed. These are the real per-app choices:

- **Frontend** — server-rendered Jinja + Tailwind/Alpine (zero JS build, ship fast)
  *or* a decoupled React/Vite SPA on its own origin (richer UI, more moving parts).
  → **[FRONTEND.md](FRONTEND.md)**
- **Auth scheme** — cookie-JWT (browser app), bearer-JWT/API-key (programmatic),
  magic-link (passwordless), or OAuth (delegated). bcrypt + dependency guards are
  constant; only the token differs. → **[AUTH.md](AUTH.md)**
- **Background work** — inline in the request (simplest), cron-as-worker (the
  default for periodic/queued work), or a Redis-backed job queue (long-poll jobs).
  Reach for Celery only when you've outgrown all three. → **[BACKGROUND_JOBS.md](BACKGROUND_JOBS.md)**
- **LLM features** — `pydantic-ai` with structured Pydantic outputs, key required
  at boot, model configurable via env. → **[FRONTEND.md](FRONTEND.md)** has the note.

## Deployment

Single Docker image (the `astral-sh/uv` base, two-stage `uv sync` for layer
caching, non-root, `uvicorn --proxy-headers`). The **same image** runs web, worker,
and migrations via different commands. Target a managed platform; provision it with
**Terraform** (app + Postgres + Stripe + PostHog as code), with a platform Blueprint
file as the documented fallback. Migrations run in the pre-deploy step. Secrets are
generated in Terraform or marked no-sync and set out of band. → **[DEPLOYMENT.md](DEPLOYMENT.md)**

## Review Checklist

```
Structure:
- [ ] Logic in services/, not in route handlers
- [ ] External SDKs (Stripe/email/LLM) isolated behind a service module
- [ ] /health (or /readyz) actually pings the database

Data:
- [ ] Async engine is a lazy singleton with pool_pre_ping
- [ ] postgres:// URLs normalized to postgresql+asyncpg://
- [ ] Every schema change has an Alembic migration

Config:
- [ ] Production refuses to boot on a default/missing secret
- [ ] CORS not "*" and HTTPS enforced in production
- [ ] .env.example committed; .env gitignored

Billing & security:
- [ ] Exactly one Stripe webhook, signature-verified, idempotent
- [ ] Passwords bcrypt-hashed; auth via reusable dependencies
- [ ] Sentry + PostHog init guarded (no-op when unkeyed, never break a request)

Ship:
- [ ] One Docker image; web/worker/migrate are just different commands
- [ ] Migrations run pre-deploy, not at app startup in prod
- [ ] Infra is in Terraform; secrets are not committed
```

## Reference Files

- **[STACK.md](STACK.md)** — pyproject, `main.py`, `db.py`, `config.py`, Makefile templates
- **[PAYMENTS.md](PAYMENTS.md)** — Stripe checkout + idempotent webhook patterns
- **[AUTH.md](AUTH.md)** — the four token schemes and shared dependency guards
- **[BACKGROUND_JOBS.md](BACKGROUND_JOBS.md)** — inline vs cron-worker vs Redis queue
- **[FRONTEND.md](FRONTEND.md)** — Jinja/Tailwind/Alpine vs decoupled SPA (+ LLM note)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Dockerfile, Terraform, migrations, secrets

---

## Reference: STACK

# Core Stack Templates

Copy-pasteable starting points for the framework, packaging, database, and config
layers. Names use `myapp`; the env prefix is `MYAPP_`.

## pyproject.toml

```toml
[project]
name = "myapp"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic-settings>=2.6",
    "stripe>=15.2",
    "sentry-sdk[fastapi]>=2.18",
    "posthog>=7.18",
    "slowapi>=0.1.9",
    "bcrypt>=4.2",
    "pyjwt>=2.10",
    "jinja2>=3.1",            # if server-rendering
    "httpx>=0.27",
]

[project.scripts]
myapp-api    = "myapp.main:run"
myapp-worker = "myapp.worker:main"
myapp-seed   = "myapp.seed:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
package = true

[dependency-groups]
dev = ["pytest>=8.3", "pytest-asyncio>=0.24", "pytest-cov", "ruff", "playwright"]

[tool.ruff]
line-length = 100
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "C4", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["src"]
```

Manage with **uv** only: `uv sync`, `uv run pytest`, `uv add <pkg>`. Commit `uv.lock`.
`requires-python >=3.11`; the Docker image and CI can pin 3.12.

## config.py — pydantic-settings with prod guards

```python
from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYAPP_", env_file=".env", extra="ignore")

    environment: str = "development"
    secret_key: str = "dev-insecure-change-me"
    database_url: str = "sqlite+aiosqlite:///./local.db"
    cors_origins_raw: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    sentry_dsn: str = ""
    posthog_key: str = ""

    @property
    def is_prod(self) -> bool:
        return self.environment == "production"

    @property
    def db_url(self) -> str:
        # Platforms hand out postgres://; SQLAlchemy async needs the driver.
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def billing_enabled(self) -> bool:
        return bool(self.stripe_secret_key and self.stripe_webhook_secret)

    @model_validator(mode="after")
    def _guard_prod(self):
        if self.is_prod:
            if self.secret_key == "dev-insecure-change-me":
                raise ValueError("MYAPP_SECRET_KEY must be set in production")
            if "*" in self.cors_origins:
                raise ValueError("wildcard CORS not allowed in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Commit `.env.example` documenting every variable; gitignore `.env`.

## db.py — lazy async engine + session dependency

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from myapp.config import get_settings

_engine = None
_sessionmaker = None


def _init():
    global _engine, _sessionmaker
    if _engine is None:
        _engine = create_async_engine(
            get_settings().db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            future=True,
        )
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    _init()
    async with _sessionmaker() as session:
        yield session
```

Why each knob: `pool_pre_ping` survives platform connection drops;
`expire_on_commit=False` keeps ORM objects usable after commit (essential in async);
the lazy singleton avoids opening a pool at import time (breaks tests and CLI tools).

## models.py — SQLAlchemy 2.0 declarative

```python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)  # soft delete
```

Use typed `Mapped[]`/`mapped_column`. Prefer soft-delete (`deleted_at`) over hard
deletes. For capacity/race-prone rows, lock explicitly with `SELECT ... FOR UPDATE`.

## Alembic

`alembic init migrations`, point `sqlalchemy.url` at the runtime config, set
`target_metadata = Base.metadata`. Autogenerate then **read the diff** before
committing. Apply with `alembic upgrade head` in the deploy's pre-deploy step — never
auto-migrate at app startup in production. Use `render_as_batch=True` if you also run
SQLite locally.

## Makefile — the developer entrypoint

```makefile
run:        ; uv run uvicorn myapp.main:app --reload
test:       ; uv run pytest
lint:       ; uv run ruff check . && uv run ruff format --check .
fmt:        ; uv run ruff format . && uv run ruff check --fix .
migrate:    ; uv run alembic upgrade head
revision:   ; uv run alembic revision --autogenerate -m "$(m)"
```

## Testing shape

`pytest` + `pytest-asyncio` (`asyncio_mode=auto`). `conftest.py` sets env vars
*before* importing the app, builds the schema from `Base.metadata` on a fresh
SQLite engine per test, and drives the app through `httpx.ASGITransport` (no live
server). Run against SQLite locally for speed; run a Postgres service in CI. Add
Playwright for browser/e2e and a thin prod smoke suite.

---

## Reference: AUTH

# Authentication

What stays constant across every app, and the one real choice: **which token**.

## Constant: hashing + dependency guards

- **bcrypt** for passwords (`bcrypt>=4.2`). Never store or log plaintext.
- Auth is expressed as **FastAPI dependencies**, not middleware, so each route
  declares its own requirement and you get it for free in the OpenAPI schema.

```python
# security.py
import bcrypt

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())
```

```python
# api/deps.py
async def current_user(...) -> User | None: ...        # may be anonymous
async def require_user(user=Depends(current_user)) -> User:
    if user is None:
        raise HTTPException(401)
    return user
async def require_admin(user=Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403)
    return user

UserDep  = Annotated[User, Depends(require_user)]
AdminDep = Annotated[User, Depends(require_admin)]
```

### Timing-safe lookups

On login, if the email doesn't exist, still run a dummy bcrypt verify before
returning failure. Otherwise response time reveals which emails are registered.
Use `hmac.compare_digest` for comparing tokens/CSRF values.

## The choice: which token

Pick **one** scheme per app based on who calls the API. The guards above don't
change — only how `current_user` resolves a request to a user.

### 1. Cookie-JWT — browser apps (server-rendered)

JWT (HS256, `pyjwt`) stored in an **httponly, `samesite=lax`, `secure`-in-prod**
cookie. Best default for a Jinja-rendered app: no token handling in JS, and the
cookie can't be read by scripts. Add CSRF protection for state-changing POSTs.

### 2. Bearer-JWT / API key — programmatic or SPA clients

`HTTPBearer`; the SPA stores the access token and sends `Authorization: Bearer`.
Issue short-lived access + longer refresh tokens with a `type` claim. For
machine clients, issue API keys (`sk_live_...`): show once, store only a **SHA-256
hash**, look up by hash.

### 3. Magic link — passwordless

Email a single-use, signed, expiring link; clicking it mints a session token. No
passwords to store or leak. Good for low-friction consumer signups.

### 4. OAuth — delegated identity

Authorization-code flow against a provider (Google, GitHub, a domain-specific
provider). **Always validate the `state` parameter** to block login-CSRF. Encrypt
any third-party access/refresh tokens at rest (e.g. a SQLAlchemy `TypeDecorator`
that encrypts on the way in and decrypts on the way out).

## CSRF (cookie-based auth only)

If auth rides in a cookie, the browser attaches it automatically, so you need CSRF
protection on state-changing requests: a per-session token rendered into forms and
checked on POST with `hmac.compare_digest`. Token-in-header schemes (bearer) are not
CSRF-exposed and don't need this.

## Quick guide

| App type                         | Scheme            |
|----------------------------------|-------------------|
| Server-rendered Jinja dashboard  | Cookie-JWT (+CSRF) |
| Decoupled SPA / mobile           | Bearer-JWT (+refresh) |
| Public/programmatic API          | API key (hashed)  |
| Low-friction consumer signup     | Magic link        |
| "Sign in with <provider>"        | OAuth             |

---

## Reference: FRONTEND

# Frontend

Two supported approaches. Pick one per app; don't mix paradigms within a single UI.

## Approach A — Server-rendered Jinja (default, ship-fast)

Render HTML on the server with Jinja2, style with **Tailwind via CDN**, add
interactivity with **Alpine.js via CDN**. **No JS build step, no bundler, no
node_modules in the critical path.** This is the right default for dashboards,
marketing, and CRUD-heavy apps — you stay in one language and one deploy artifact.

```python
# templating.py
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["posthog_key"] = settings.posthog_key   # inject brand/analytics
templates.env.filters["markdown"] = render_markdown            # custom filters
```

```
app/templates/
  base.html              # <head>, Tailwind CDN, Alpine CDN, analytics snippet
  _chrome/{nav,footer}.html
  dashboard/index.html   # {% extends "base.html" %}
```

- **Design tokens in one CSS file.** Even with Tailwind-CDN for layout, keep a
  hand-authored `static/css/tokens.css` of CSS custom properties (colors, fonts,
  spacing) so the look is consistent and themeable. This is the only CSS you write.
- **Alpine for sprinkles**, not for an app. Dropdowns, modals, tabs, optimistic
  toggles — `x-data`/`x-show`/`@click`. If a page starts needing real client state,
  that page wants Approach B, not more Alpine.
- **Hand-written CSS** (no Tailwind at all) is also fine for small apps; the point
  is *no build step*.

Trade-off: cheapest to build and operate; weakest for highly interactive,
stateful UIs.

## Approach B — Decoupled SPA (rich, interactive)

A separate **React + TypeScript + Vite** app in `web/`, built (`tsc -b && vite
build`) and deployed as static files on **its own origin**. The FastAPI app becomes
a pure JSON API (`/api/v1/...`) with **CORS** allowing the SPA origin. Tailwind (the
real PostCSS build, not CDN), `react-router`, an `axios`/`fetch` client, `posthog-js`.

```
web/
  src/{pages,components,context,lib}/
  package.json   vite.config.ts   tailwind.config.js
```

- The API serves no HTML; `docs` stays gated to admins.
- Auth is bearer-token (see **[AUTH.md](AUTH.md)** — Approach B pairs with Bearer-JWT).
- The static site gets the same security headers and an SPA rewrite (all routes →
  `index.html`).

Trade-off: best UX for app-like products; two build pipelines, two deploys, and
CORS to manage.

## Choosing

| Want…                                        | Use |
|----------------------------------------------|-----|
| Fastest path to a working product, one deploy | A — Jinja + Tailwind/Alpine |
| Marketing + dashboard CRUD                    | A   |
| Highly interactive, stateful, app-like UI     | B — React/Vite SPA |
| A public API that *also* has a web UI         | B (the UI is just another API client) |

## Marketing & blog

Keep marketing pages as plain templates (Approach A) or a static-site generator
(e.g. Hugo) built into the same Docker image and served under `/blog` via
`StaticFiles`. No need for a separate hosting story.

## LLM features

When the app calls an LLM, use **`pydantic-ai`** with **structured Pydantic
outputs** so model responses are validated, typed objects rather than free text:

```python
from pydantic_ai import Agent

agent = Agent(f"openai-chat:{settings.openai_model}", output_type=Analysis, retries=2)
result = await agent.run(prompt)        # result.output is a validated `Analysis`
```

- **Require the key at boot** (`Field(min_length=1)`) when the feature is core — fail
  fast rather than discovering a missing key mid-request. Gate the feature behind a
  config flag if it's optional.
- **Make the model configurable** via env (`MYAPP_OPENAI_MODEL`) so you can swap
  models without a deploy.
- Keep all LLM calls inside a service module, like any other external SDK.

---

## Reference: PAYMENTS

# Payments with Stripe

Stripe is the default. The rules that keep billing from becoming a support
nightmare: **isolate the SDK, verify every webhook, and make webhook handling
idempotent.** Use `stripe>=15`.

## Isolate the SDK

Every Stripe call lives in `services/stripe/` — nothing else imports `stripe`.
That keeps routes mockable and gives one place to swap API styles.

```python
# services/stripe/client.py
import stripe
from myapp.config import get_settings

_s = get_settings()
stripe.api_key = _s.stripe_secret_key          # legacy global, used by webhook verify
client = stripe.StripeClient(_s.stripe_secret_key)  # modern client for API calls
```

Blocking SDK calls inside an async handler should be offloaded
(`await anyio.to_thread.run_sync(...)`) or use the async API surface
(`*.create_async`) where available.

## Checkout

Hosted Checkout for both one-time and subscription billing — let Stripe own the
payment page. Drive behavior with `metadata` so the webhook can fulfill correctly.

```python
# services/stripe/checkout.py
def create_checkout(price_id: str, customer_id: str, *, mode: str, user_id: int):
    return client.checkout.sessions.create({
        "mode": mode,                       # "payment" | "subscription"
        "customer": customer_id,
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{base}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{base}/billing",
        "metadata": {"user_id": str(user_id)},
    })
```

Use Stripe's billing portal for self-serve plan changes/cancellation rather than
building your own.

## The Webhook — one endpoint, verified, idempotent

Exactly **one** unauthenticated route. Verify the signature with the raw body, then
dedupe on the event id before doing anything.

```python
# api/webhooks.py
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: SessionDep):
    payload = await request.body()                 # raw bytes — never the parsed JSON
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "invalid signature")

    if await already_processed(db, event["id"]):   # idempotency table
        return {"status": "duplicate"}
    await record_event(db, event["id"], event["type"])

    await dispatch(db, event)                       # by type; unknown types are a no-op
    return {"status": "ok"}
```

```python
async def dispatch(db, event):
    handlers = {
        "checkout.session.completed":      fulfill_checkout,
        "customer.subscription.updated":   sync_subscription,
        "customer.subscription.deleted":   cancel_subscription,
        "invoice.payment_failed":          flag_past_due,
    }
    handler = handlers.get(event["type"])
    if handler:                                     # never 500 on an event you don't handle
        await handler(db, event["data"]["object"])
```

### Non-negotiables

- **Verify with the raw request body.** Re-serializing the parsed JSON changes bytes
  and the signature check fails.
- **Idempotency table.** Stripe retries and may deliver duplicates. Persist handled
  event ids and skip repeats — fulfillment must be exactly-once.
- **Never 500 on an unknown event.** Return 200; an exception makes Stripe retry
  forever. Map unknown subscription statuses to a safe default rather than crashing.
- **Gate on configuration.** `billing_enabled` (both secret + webhook secret present)
  lets the app run in a demo/free mode when Stripe isn't configured.

## Provision the webhook in Terraform

Create the endpoint and read its signing secret as code, then pipe it straight into
the app's environment — no copy-pasting secrets from the dashboard.

```hcl
resource "stripe_webhook_endpoint" "app" {
  url            = "https://${var.app_host}/api/v1/stripe/webhook"
  enabled_events = ["checkout.session.completed",
                    "customer.subscription.updated",
                    "customer.subscription.deleted",
                    "invoice.payment_failed"]
}
# stripe_webhook_endpoint.app.secret -> set as MYAPP_STRIPE_WEBHOOK_SECRET on the service
```

## Marketplace / split payments

If you take a fee on payments between users, use Stripe Connect (Express accounts)
with destination charges and an explicit `application_fee_amount` / platform-fee
percentage. Keep the platform-billed flow (you charge the user) and the
pass-through flow (user charges user, you skim) as separate, clearly named code
paths.

---

## Reference: BACKGROUND_JOBS

# Background Work

**Default to the simplest option that fits, and reach for Celery/RQ only when you
have genuinely outgrown all three below.** A full task-queue stack (broker + result
backend + worker fleet + monitoring) is real operational weight; most small apps
never need it.

## Option 1 — Inline in the request

Just `await` the work in the handler. No infrastructure, trivially correct, easy to
test. Use it whenever the work fits inside a reasonable request timeout.

```python
@router.post("/scan")
async def create_scan(payload: ScanIn, db: SessionDep, user: UserDep):
    result = await run_and_store_scan(db, user, payload)   # synchronous to the request
    return result
```

When it stops fitting (work takes too long, or you need it on a schedule), move to
option 2 — not straight to Celery.

## Option 2 — Cron-as-worker (the default for async/periodic work)

Run a plain `run_once()` coroutine on a schedule as a **separate process from the
same Docker image** (a platform cron job). No broker, no queue library — the
database *is* the queue. This covers polling, digests, retries, cleanup, and
draining a "send these" table.

```python
# worker.py
async def run_once() -> None:
    async with sessionmaker() as db:
        items = await claim_pending(db, limit=BATCH)   # SELECT ... FOR UPDATE SKIP LOCKED
        for item in items:
            try:
                await process(db, item)
            except Exception:
                await mark_failed(db, item)             # one bad item never stalls the batch
        await db.commit()

def main():
    import asyncio
    asyncio.run(run_once())
```

Schedule it (every 5 min, hourly, daily — whatever the work needs). Keep batches
bounded, make each item independently retryable, and add a heartbeat row so you can
alert if the worker stops running. Self-throttle with a small `app_state` table
holding budget/cooldown if the work calls rate-limited external APIs.

## Option 3 — Redis-backed job queue (interactive long-running work)

When a *user* kicks off work that's too slow for a request but they want to watch it
finish, enqueue a job, return a `job_id` immediately, and let the client poll. Back
it with Redis (`redis[hiredis]`, `redis.asyncio`) and drain it with a dedicated
worker service (again, same image, different command).

```python
@router.post("/jobs")
async def enqueue(payload: JobIn, user: UserDep) -> dict:
    job_id = await queue.enqueue(kind="report", args=payload.model_dump(), user_id=user.id)
    return {"job_id": job_id, "status": "pending"}      # client polls /jobs/{id}

@router.get("/jobs/{job_id}")
async def job_status(job_id: str, user: UserDep) -> dict:
    return await queue.get(job_id)                       # pending|processing|completed|failed
```

A `JobStatus` enum (`pending/processing/completed/failed`) and storing the result
(or error) on completion is enough — you don't need Celery's full feature set for
long-poll jobs.

## Choosing

| Situation                                            | Use            |
|------------------------------------------------------|----------------|
| Fits in a request timeout                            | Inline         |
| Periodic, or fire-and-forget, or queue-drain         | Cron-as-worker |
| User-triggered, slow, they watch it finish           | Redis job queue |
| Fan-out across many workers, chains, retries-with-backoff at scale | Celery/RQ |

Whatever you pick, the worker is **the same Docker image as the web service**, run
with a different command — never a second codebase to keep in sync.

---

## Reference: DEPLOYMENT

# Deployment

**One Docker image, one managed platform, all infrastructure in Terraform.** The web
service, the worker, and migrations are the *same image* run with different commands
— never separate codebases.

## Dockerfile

Build on the `astral-sh/uv` image and use a two-stage `uv sync` so the dependency
layer caches independently of your source.

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# 1) deps only — cached unless the lockfile changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 2) project source
COPY . .
RUN uv sync --frozen --no-dev

RUN useradd -m appuser
USER appuser

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "myapp.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
```

`--proxy-headers --forwarded-allow-ips '*'` makes the app trust the platform's
load-balancer headers (correct scheme/host for secure cookies and redirects).

## One image, three roles

| Role    | Command                                            |
|---------|----------------------------------------------------|
| web     | `uvicorn myapp.main:app --proxy-headers ...`       |
| worker  | `python -m myapp.worker` (cron or always-on)       |
| migrate | `alembic upgrade head` (pre-deploy hook)           |

An `entrypoint.sh` that dispatches on `$1` (`web`/`worker`/`migrate`) keeps this in
one place.

## Migrations run pre-deploy

Run `alembic upgrade head` as the platform's **pre-deploy step**, so a new release's
schema is in place before traffic hits it. **Do not** run migrations at app startup
in production — concurrent instances race, and a bad migration takes down boot.

## Infrastructure as code — Terraform

Provision the platform with Terraform; keep a platform Blueprint file (a
`render.yaml`-style manifest) as the documented fallback. Organize by concern:

```
terraform/
  main.tf        # locals: shared env map, CSP, generated secrets
  variables.tf   # inputs (with sensible defaults)
  versions.tf    # provider pins
  render.tf      # project + Postgres + web service + worker/cron (+ static site)
  stripe.tf      # products, prices, webhook endpoint
  posthog.tf     # project + dashboards
  outputs.tf
```

```hcl
# render.tf (shape — applies to any managed platform with a TF provider)
resource "platform_postgres" "db"  { plan = "starter" }

resource "platform_web_service" "web" {
  image                = var.image
  pre_deploy_command   = "alembic upgrade head"
  health_check_path    = "/health"
  env_vars             = local.app_env       # shared map, see below
}

resource "platform_cron_job" "worker" {
  image    = var.image
  schedule = "*/5 * * * *"
  command  = "python -m myapp.worker"
  env_vars = local.app_env
}
```

Typical provider set: the platform provider, the **Stripe** provider, the
**PostHog** provider, and `random` for secret generation. One Terraform tree per
app — the app owns all of its own infrastructure; don't centralize it in a shared
infra repo.

## Secrets

Two clean patterns, no copy-pasting from dashboards:

- **Generate in Terraform** with `random_password` (e.g. `secret_key`) and inject the
  same value into both the web and worker services via the shared `local.app_env`.
- **Mark no-sync** (`sync = false` / equivalent) for values that must come from
  elsewhere, and set them out of band. The provisioned-by-TF Stripe webhook secret
  (see **[PAYMENTS.md](PAYMENTS.md)**) flows straight from the resource into the env.

The `secret_key` must be **identical** across web and worker (they verify the same
signed tokens). Never commit real secrets; `.env` is gitignored and `.env.example`
documents the variable names only.

## Health checks

Expose `/health` (and optionally `/readyz`) that runs `SELECT 1` and returns 503 if
the DB is unreachable. Point the platform's health check at it so a database-less
instance is pulled from rotation instead of serving errors.

## CI

GitHub Actions: `uv sync`, `ruff check` + `ruff format --check`, `alembic upgrade
head` against a Postgres service, then `pytest` (coverage-gated). For Approach B
frontends, a parallel job does `npm ci` + lint + build. Build/push the Docker image
on tag or main.
