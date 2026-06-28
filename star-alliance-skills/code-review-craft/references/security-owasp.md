---
type: Reference
title: Security — OWASP Top-10 Lens and Scan Recipes
skill: code-review-craft
---

# OWASP Top-10 lens + concrete scan recipes

The security dimension in `review-dimensions.md` says *what* to look for in principle.
This file makes it operational: an OWASP Top-10 mapping that turns each abstract risk
into a concrete check, plus copy-paste scan recipes to find the evidence. Adapted from
the SAW (safe-agentic-workflow) security-audit playbook.

Use it as a checklist pass over a security-sensitive diff, or as the deep sweep when a
"is this safe?" review touches auth, data access, secrets, or dependencies. Every row
ends in a grounded finding — a cited line and the concrete case it breaks — exactly as
the parent skill requires. The greps locate suspects; you still read each hit and judge
it. A grep hit is a lead, not a verdict.

## The OWASP Top-10 mapping

| Risk | What it means here | Concrete check |
| --- | --- | --- |
| **A01 Broken Access Control** | A user reaches data or an action they should not. | Auth checked before every protected action; RLS / row-owner enforced; cache key, query, and filter include the tenant / owner id. |
| **A02 Cryptographic Failures** | Secrets or sensitive data exposed or weakly protected. | Secrets only from env vars, never hardcoded or logged; TLS for data in transit; no home-rolled crypto / weak hashes (MD5, SHA1, plain bcrypt-less passwords). |
| **A03 Injection** | Untrusted input concatenated into SQL, shell, HTML, a path, or a template. | Parameterized queries only (no string-interpolated SQL); input validated at the boundary (e.g. a schema / Zod); output escaped; no `eval` on external data. |
| **A04 Insecure Design** | The auth-first / least-privilege pattern is skipped by design. | Protected route follows the auth-first shape (verify identity, then act); no "we'll add the check later" gaps. |
| **A05 Security Misconfiguration** | Prod settings leak or over-permit. | No debug/stack traces to clients; CORS not `*` on credentialed routes; security headers set; default creds removed; env files not committed. |
| **A06 Vulnerable / Outdated Components** | A dependency has a known CVE. | `npm audit --audit-level=high` (or the stack's equivalent) is clean; no pinned-to-vulnerable versions. |
| **A07 Identification & Auth Failures** | Login / session handling is weak. | Sessions invalidated on logout; no auth bypass branch; rate-limiting / lockout on credential endpoints; tokens not in URLs. |
| **A08 Software & Data Integrity Failures** | Untrusted data or code is trusted. | No unsafe deserialization; CI / dependency sources verified; RLS prevents row tampering. |
| **A09 Logging & Monitoring Failures** | Security events vanish or secrets land in logs. | Auth failures and access-control denials logged; errors logged loudly (never swallowed); no secrets / PII in log lines. |
| **A10 Server-Side Request Forgery (SSRF)** | External data chooses a URL the server fetches. | User-supplied URLs validated / allow-listed before fetch; no raw fetch of attacker-controlled hosts. |

When the diff touches a row above, name the OWASP id in the finding so the author can
triage by category — e.g. `L77 — Critical (A01): cache key omits tenant prefix...`.

## Scan recipes

These find the evidence behind the rows above. Adapt the file globs and the
context-wrapper / auth-helper names to the project under review. On macOS, prefer
`rg` or `LC_ALL=C grep` — plain `grep` silently misses matches in UTF-8 / multibyte
files.

### A02/A09 — Hardcoded credentials and secrets

```bash
# Live keys, passwords, secrets that are NOT pulled from env
grep -rEn "(sk_live|pk_live|password|secret|api[_-]?key)" \
  --include="*.ts" --include="*.tsx" --include="*.js" \
  | grep -v "process.env"
```

A hit that is not `process.env.SOMETHING` is a candidate hardcoded secret. Read the
line: a key literal is Critical (A02); a secret echoed into a log line is A09.

### A01 — Direct-DB calls vs context-wrapper count

A common access-control pattern wraps every DB call in a context helper
(`withUserContext` / `withTenantContext` / an RLS-scoped client). A raw client call in
a route handler bypasses that and is an A01 lead.

```bash
# Raw DB calls that skip the context wrappers (adapt the client + wrapper names)
grep -rEn "prisma\.|db\.query|supabase\.from" --include="*.ts" app/ lib/ \
  | grep -v "withUserContext\|withTenantContext\|withSystemContext"

# Count raw calls vs wrapped calls — a rising raw count is the signal
grep -rEc "prisma\." --include="*.ts" app/ lib/ | awk -F: '{s+=$2} END{print "raw:",s}'
```

Each surviving hit: confirm whether the call is scoped to the actor. An unscoped
`findMany` in a request path is the classic cross-tenant read.

### A03 — String-interpolated SQL (injection)

```bash
# Template-literal SQL with an interpolation inside — the injection smell
grep -rEn '(SELECT|INSERT|UPDATE|DELETE)[^\n]*\$\{' \
  --include="*.ts" --include="*.js"
```

A hit means user input may be concatenated into the query. The fix is a parameterized
query; cite the line and the input that reaches it.

### A04/A07 — Routes missing an auth check

```bash
# Every route handler — then read each for an auth/identity check before data access
grep -rln "export async function (GET|POST|PUT|PATCH|DELETE)" \
  --include="route.ts" app/
```

This lists handlers; open each and confirm an identity check precedes any data access.
A handler that reads user data with no preceding `auth()` / session check is A01/A04.

### A06 — Dependency vulnerabilities

```bash
# Fail the review on known high/critical CVEs in dependencies
npm audit --audit-level=high
# (pnpm: pnpm audit --audit-level=high · yarn: yarn npm audit --severity high)
```

Treat a high/critical advisory as a finding: name the package, the advisory, and the
fixed version. A clean audit closes A06.

### A10 — Server-side fetch of user-supplied URLs (SSRF)

```bash
# Outbound fetches whose URL may be attacker-controlled
grep -rEn "fetch\(|axios\.(get|post)\(|http\.request" \
  --include="*.ts" --include="*.js"
```

For each hit, trace the URL: if it comes from request input without an allow-list
check, that is an SSRF finding (A10).

## Turning a scan hit into a finding

A grep hit is a lead, not a finding. To promote it, do what the parent skill demands:
cite the line, name the concrete case it breaks, tag severity, and add the OWASP id.

> Weak: "grep found some `prisma.` calls without wrappers."
> Grounded: "`app/api/orders/route.ts:24` — Critical (A01): `prisma.order.findMany()`
> runs unscoped in the GET handler with no tenant filter — repro: call as tenant B,
> read tenant A's orders. Fix: wrap in `withTenantContext`."

Authoritative reference: OWASP Top 10 — https://owasp.org/Top10/
