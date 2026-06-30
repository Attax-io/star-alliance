# Push channels — six targets, one contract

Every push channel in this matrix is a *first-class output* of the pipeline.
Missing channels silently disable — you only see channels you actually
configured. Per-channel: env vars, signature / verification (where the
provider has it), and a test pattern. The dashboard shape is identical
across channels; the emoji + Chinese labels render natively on every
target listed here.

## Channel matrix

| Channel | Env vars (required) | Optional env vars | Signature | Rendering |
|---|---|---|---|---|
| **WeChat Work bot** | `WECHAT_WEBHOOK_URL` | — | optional | markdown, native emoji |
| **Feishu / Lark bot** | `FEISHU_WEBHOOK_URL` | `FEISHU_SECRET` (sign) | HMAC-SHA256 | rich text (post) or interactive card |
| **Telegram bot** | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | `TELEGRAM_BASE_URL` (custom bot API) | none | HTML, preserves emoji |
| **Discord webhook** | `DISCORD_WEBHOOK_URL` | `DISCORD_USERNAME`, `DISCORD_AVATAR_URL` | none | markdown, native emoji |
| **Slack bot** | `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID` | `SLACK_THREAD_TS` (thread a report) | none | mrkdwn / blocks |
| **Email** | `EMAIL_SENDER`, `EMAIL_PASSWORD` | `EMAIL_RECEIVERS` (comma-separated), `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_USE_TLS` | none | plain text + emoji, optional Markdown |

## Per-channel config

### WeChat Work (企业微信)

- Env: `WECHAT_WEBHOOK_URL`
- Setup: Group chat → Group bot → Add → copy webhook URL into the env.
- Format: Markdown in `markdown` type payload.
- Test:
  ```bash
  curl -H "Content-Type: application/json" \
    -d '{"msgtype":"markdown","markdown":{"content":"hello"}}' \
    "$WECHAT_WEBHOOK_URL"
  ```

### Feishu / Lark (飞书)

- Env: `FEISHU_WEBHOOK_URL`, optional `FEISHU_SECRET` (for sign verification).
- Setup: 飞书群 → 设置 → 群机器人 → 添加机器人 → 自定义机器人 → copy webhook
  URL and signing secret (if enabled).
- Sign: when `FEISHU_SECRET` is set, the pipeline computes `sign` =
  `HMAC-SHA256(secret, timestamp + "\n" + key)` per Feishu spec.
- Format: `interactive` card payload by default; falls back to `post` rich
  text when cards fail.
- Test:
  ```bash
  curl -H "Content-Type: application/json" \
    -d '{"msg_type":"text","content":{"text":"hello"}}' \
    "$FEISHU_WEBHOOK_URL"
  ```

### Telegram

- Env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- Setup: talk to @BotFather, create a bot, copy token; get your chat ID
  via @userinfobot or by sending a message to the bot and reading
  `getUpdates`.
- Optional: `TELEGRAM_BASE_URL` for self-hosted bot API; default is
  `https://api.telegram.org`.
- Format: HTML with `<pre>` block for the dashboard; preserves the emoji.
- Test:
  ```bash
  curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "parse_mode=HTML" \
    -d "text=hello"
  ```

### Discord

- Env: `DISCORD_WEBHOOK_URL`.
- Optional: `DISCORD_USERNAME`, `DISCORD_AVATAR_URL` to brand the bot.
- Setup: server → channel → Integrations → Webhooks → New webhook →
  copy URL.
- Format: `content` (markdown) + optional `embeds`. The pipeline ships
  the six-field card as an embed.
- Test:
  ```bash
  curl -H "Content-Type: application/json" \
    -d '{"content":"hello"}' \
    "$DISCORD_WEBHOOK_URL"
  ```

### Slack

- Env: `SLACK_BOT_TOKEN` (xoxb-…), `SLACK_CHANNEL_ID` (C…) or
  `SLACK_DM_USER_ID` (U…) for DMs.
- Optional: `SLACK_THREAD_TS` to thread reports under a parent message.
- Setup: api.slack.com → Create app → bot scope `chat:write` + `chat:write.public` →
  install to workspace → copy bot token → invite bot to channel.
- Format: Block Kit blocks; falls back to mrkdwn if blocks rejected.
- Test:
  ```bash
  curl -X POST "https://slack.com/api/chat.postMessage" \
    -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
    -H "Content-type: application/json" \
    -d "{\"channel\":\"${SLACK_CHANNEL_ID}\",\"text\":\"hello\"}"
  ```

### Email

- Env: `EMAIL_SENDER`, `EMAIL_PASSWORD`.
- Optional: `EMAIL_SMTP_HOST` (default derived from sender domain),
  `EMAIL_SMTP_PORT` (default 465 for SSL or 587 for STARTTLS),
  `EMAIL_USE_TLS` (default true), `EMAIL_RECEIVERS` (comma-separated
  recipients; default to sender).
- Setup: most providers expose an "app password" — Gmail requires it with
  2FA on; QQ Mail, 163 Mail, Outlook all support app passwords.
- Format: plain text with emoji preserved; Markdown rendered as plain
  text fallback; a `text/html` part is added when Markdown is detected.
- Test:
  ```bash
  python -c "from smtplib import SMTP_SSL; \
    s = SMTP_SSL('${EMAIL_SMTP_HOST}', ${EMAIL_SMTP_PORT}); \
    s.login('${EMAIL_SENDER}', '${EMAIL_PASSWORD}'); \
    s.sendmail('${EMAIL_SENDER}', ['${EMAIL_SENDER}'], 'Subject: test\\n\\nhello'); \
    s.quit()"
  ```

## Multi-channel routing

You can enable multiple channels at once; the pipeline fans out to each
configured channel independently. Channel failures (rate limit, bad
signature, network) are logged but never block the others.

Common configurations:

- **Personal trader (CN):** WeChat Work + Feishu (work + personal
  phones).
- **Power user (global):** Telegram + Discord + Email (the trio that
  works across platforms).
- **Team:** Slack + Email (the audit trail).

When in doubt, start with Telegram and Discord — both are quick to set
up, both render the dashboard well, and either alone gets you
end-to-end. Add Feishu / WeChat only after you confirm the dashboard
reads the way you want it to.

## Testing and re-runs

| Situation | What to do |
|---|---|
| new channel, untested | run `python main.py --dry-run --stocks AAPL` after the channel env is set; watch the log for the per-channel POST result |
| channel went down | pipeline logs the failure; rerun with `--debug` to see the exact HTTP status / error |
| scheduled run missed | check the Actions log (mode 1) / container log (mode 2); `--debug` is your friend |
| report didn't push but analysis ran | the per-channel push phase failed; the report is still in `reports/` or the web workbench history |

A failed push is never silently dropped — it's in the log, every time. If
a channel didn't deliver and the log says "200 OK", the issue is at the
receiver (e.g. you muted the group, you muted the bot, the email went to
spam).
