# Deployment — three modes, one dashboard

The pipeline runs in three deployment modes. Pick by your operational profile;
the dashboard shape is identical across all three.

| Mode | Cost | Who it's for | Trade-off |
|---|---|---|---|
| **GitHub Actions** | $0 (free tier) | Single user, personal schedule, no server | Public log; secrets live in repo secrets |
| **Docker** | whatever your host costs | Private cloud, shared team, custom schedule | You run the host; you patch the image |
| **Local Python** | free, your machine | Development, one-off runs, web UI dev | No automatic schedule; manual triggers only |

## Mode 1 — GitHub Actions (zero-cost, recommended)

Five-minute deploy; no server required. Suitable for a personal watchlist with
daily rhythm. Default non-trading days skip automatically; force-run with
`force_run=true` on the workflow dispatch.

### Steps

1. Fork the upstream repo (or copy this skill's source if you've forked).
2. Settings → Secrets and variables → Actions → New repository secret.
3. Add the secrets from the table below — at minimum `STOCK_LIST` plus one
   AI key, one push channel.
4. Actions tab → `I understand my workflows, go ahead and enable them`.
5. Actions → `每日股票分析` → `Run workflow` → `Run workflow` to test once.
6. Wait for 18:00 Beijing time on the next trading weekday, or use the
   manual dispatch.

### Secrets — full table

Secrets are case-sensitive. Required (`✅`), recommended (`⭐`), optional
(`○`).

#### AI models — at least one required

| Secret | Required | Purpose |
|---|---|---|
| `ANSPIRE_API_KEYS` | ⭐ recommended | Anspire — one key unlocks models + CN-friendly search |
| `AIHUBMIX_KEY` | ⭐ recommended | AIHubMix — OpenAI-compatible aggregator, no VPN needed |
| `GEMINI_API_KEY` | ○ | Google Gemini |
| `ANTHROPIC_API_KEY` | ○ | Anthropic Claude |
| `OPENAI_API_KEY` | ○ | OpenAI (or DeepSeek, 通义千问 via base URL) |
| `OPENAI_BASE_URL` | ○ | Custom endpoint for OpenAI-compatible services |
| `OPENAI_MODEL` | ○ | Model name when using OpenAI-compatible endpoint |

Local Ollama belongs in Docker or local mode, not Actions.

#### Push channels — at least one required

| Secret | Channel |
|---|---|
| `WECHAT_WEBHOOK_URL` | WeChat Work bot |
| `FEISHU_WEBHOOK_URL` | Feishu / Lark bot |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Telegram |
| `DISCORD_WEBHOOK_URL` | Discord webhook |
| `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_ID` | Slack bot |
| `EMAIL_SENDER` + `EMAIL_PASSWORD` (+ `EMAIL_RECEIVERS`) | email |

See `references/push-channels.md` for the per-channel signature / test pattern.

#### Watchlist — required

| Secret | Required | Format |
|---|---|---|
| `STOCK_LIST` | ✅ | comma-separated: `600519,hk00700,AAPL,7203.T,005930.KS` |

#### News sources — recommended

| Secret | Strong at |
|---|---|
| `ANSPIRE_API_KEYS` (same key) | CN web + AI ranking |
| `SERPAPI_API_KEYS` | Baidu / Google scrape |
| `TAVILY_API_KEYS` | general English news |
| `BOCHA_API_KEYS` | CN search with summaries |
| `BRAVE_API_KEYS` | privacy-first, English |
| `MINIMAX_API_KEYS` | structured search |
| `SEARXNG_BASE_URLS` | self-hosted no-quota fallback |

A multi-source setup improves the catalyst + sentiment fields; one source is
the floor, two is the recommended baseline.

### Local CLI on a runner — flags

When you run from a checkout (recommended for local dev, useful for debugging
GitHub Actions failures), the entry point is `python main.py` with these
flags:

| Flag | Purpose |
|---|---|
| `--debug` | verbose log (data fetches, AI calls, push attempts) |
| `--dry-run` | run the analysis without pushing to any channel |
| `--stocks 600519,hk00700,AAPL` | override `STOCK_LIST` for one run |
| `--market-review` | emit a market-wide review instead of a per-stock dashboard |
| `--schedule` | run as a long-lived scheduler (uses internal cron) |
| `--serve-only` | run the FastAPI server only, no analysis |
| `--webui` | run analysis + serve the FastAPI web workbench |
| `--webui-only` | serve the FastAPI web workbench only |

## Mode 2 — Docker

For private cloud, shared team, custom cron, or when you need to keep the
artefact on your own host.

```bash
docker pull zhulinsen/daily_stock_analysis
docker run -d \
  --name dsa \
  -p 8000:8000 \
  -e STOCK_LIST="600519,hk00700,AAPL,7203.T,005930.KS" \
  -e ANSPIRE_API_KEYS="..." \
  -e TELEGRAM_BOT_TOKEN="..." \
  -e TELEGRAM_CHAT_ID="..." \
  zhulinsen/daily_stock_analysis
```

Or with `docker-compose`:

```yaml
version: "3.9"
services:
  dsa:
    image: zhulinsen/daily_stock_analysis
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      STOCK_LIST: "600519,hk00700,AAPL,7203.T,005930.KS"
      ANSPIRE_API_KEYS: "${ANSPIRE_API_KEYS}"
      TELEGRAM_BOT_TOKEN: "${TELEGRAM_BOT_TOKEN}"
      TELEGRAM_CHAT_ID: "${TELEGRAM_CHAT_ID}"
```

Build from source:

```bash
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git
cd daily_stock_analysis
docker build -t dsa:local .
docker run -d --name dsa -p 8000:8000 dsa:local
```

### What's different from Actions

- All secrets set via `docker run -e` or `docker-compose env`, not repo
  secrets.
- The schedule is yours to set — `cron`, Kubernetes CronJob, or a sidecar
  loop. The image itself does not run on a timer unless you wire one up.
- You own the persistence (report history). Mount a volume if you want
  historical reports to survive container restart:
  `-v dsa-reports:/app/reports`.
- Web workbench is on `http://<host>:8000` by default; expose or proxy as
  needed.

## Mode 3 — Local Python (development)

For ad-hoc runs, development, and debugging without a Docker layer.

```bash
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git
cd daily_stock_analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
vim .env   # fill in keys + STOCK_LIST
python main.py --debug --dry-run   # test locally first
python main.py                     # real run + push
python main.py --webui             # analysis + web workbench
```

Cron-equivalent on Linux / macOS:

```cron
# m h dom mon dow command
0 18 * * 1-5 cd /path/to/daily_stock_analysis && .venv/bin/python main.py >> /var/log/dsa.log 2>&1
```

Same `.env` file works for all flags. `--debug` is your friend the first
time; if a field is degrading and you want to know why, `--debug` prints the
source-fallback chain inline.

## Configuration reference

A short tour of the most-used env vars (all three modes share these):

| Var | Type | Default | Purpose |
|---|---|---|---|
| `STOCK_LIST` | string | (required) | comma-separated tickers |
| `ANALYSIS_MARKETS` | csv | auto | restrict to subset of `cn, hk, us, jp, kr` |
| `REPORT_LANG` | string | `zh-CN` | output language (`en`, `zh-CN`, `zh-TW`) |
| `AGENT_MODE` | bool | `true` | enable the web Agent Q&A |
| `TRADING_DAY_CHECK` | bool | `true` | skip non-trading days |
| `FORCE_RUN` | bool | `false` | override the trading-day skip |
| `MAX_CONCURRENT_STOCKS` | int | `3` | parallel stock analysis workers |
| `LOG_LEVEL` | string | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `WEBUI_HOST` | string | `127.0.0.1` | FastAPI bind host |
| `WEBUI_PORT` | int | `8000` | FastAPI bind port |
| `WEBUI_AUTH_USER` | string | unset | web workbench username |
| `WEBUI_AUTH_PASS` | string | unset | web workbench password |
| `REPORT_FORMAT` | csv | `markdown,json` | additional export formats |

When in doubt, start with `STOCK_LIST`, one AI key, one push channel, one
news source. Add complexity only when the dashboard shape demands it.
