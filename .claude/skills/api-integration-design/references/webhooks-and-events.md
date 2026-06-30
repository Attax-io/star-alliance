---
title: Webhooks & Events
type: reference
---
# Webhooks & Events

Webhooks invert the contract: *you* call the receiver. They are delivered at-least-once over an
unreliable network (Principle 3) and must be authenticated inbound (Principle 5).

## Event design

- An event is an immutable fact in the past tense: `invoice.paid`, `subscription.canceled` — not a
  command. Name it `resource.action`.
- Envelope every event with stable metadata:
  ```json
  { "id": "evt_01H…", "type": "invoice.paid", "created_at": "2026-06-28T10:00:00Z",
    "api_version": "2026-06-01", "data": { … } }
  ```
- `id` is a unique, stable event id — the receiver's dedupe key. `api_version` pins the payload shape
  so receivers can evolve; version events like any other contract (Principle 2).
- Keep payloads **thin or thick deliberately**: thin (id only, receiver fetches) avoids stale/oversized
  bodies; thick (full snapshot) avoids a round-trip but can race. State which you send.

## Delivery & retries (sender side)

- Deliver **at-least-once**. Network failures mean you must retry, so duplicates are expected.
- Retry on connection failure or non-2xx response with **exponential backoff + jitter** over a bounded
  window (e.g. retries across minutes → hours, then dead-letter).
- Consider a 2xx the only success. Time out slow receivers (they should `202` fast and process async).
- Provide a **dead-letter / replay** path: failed events are stored and re-deliverable, plus a manual
  "resend event" affordance for receivers recovering from an outage.
- Optionally guarantee per-resource ordering, but most systems should not assume order — design events
  to be order-independent and let the receiver reconcile by `created_at`/state.

## Idempotent consumption (receiver side)

- Expect duplicates. Dedupe on the event `id`: record processed ids and short-circuit repeats.
- Make handlers idempotent at the effect level too (upsert by resource id, not blind insert) so a
  redelivery after partial work is safe.
- Acknowledge fast (`2xx`), then process asynchronously; never do slow work inside the request the
  sender is timing.

## Signature verification (authenticate inbound — Principle 5)

This is non-negotiable: an unverified webhook endpoint lets anyone forge your events.

1. The sender signs the **raw request body** with a shared secret:
   `signature = HMAC-SHA256(secret, timestamp + "." + raw_body)`, sent in a header
   (e.g. `X-Signature: t=…,v1=…`).
2. The receiver, **before parsing or trusting anything**:
   - reads the **raw** body (not the re-serialized JSON — re-serialization changes bytes and breaks
     the HMAC);
   - recomputes the HMAC with the shared secret;
   - **constant-time** compares it to the header value;
   - rejects if the `timestamp` is outside a tolerance window (replay defense);
   - only then parses and acts.
3. Support secret **rotation**: accept two valid secrets during a rollover window.

## Local example (receiver)

```python
import hmac, hashlib, time

def verify(raw_body: bytes, header_sig: str, header_ts: str, secret: bytes) -> bool:
    if abs(time.time() - int(header_ts)) > 300:          # replay window
        return False
    signed = f"{header_ts}.".encode() + raw_body
    expected = hmac.new(secret, signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header_sig)      # constant-time
```
