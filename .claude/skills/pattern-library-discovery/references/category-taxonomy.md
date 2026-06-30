---
type: Document
title: Category Taxonomy
description: The seven-category pattern taxonomy, folder layout, the README-index contract, and when to add a category.
timestamp: 2026-06-28T00:00:00Z
---

# Category Taxonomy

A pattern library is only as queryable as its filing. A **small, stable
taxonomy** lets a consumer know which folder to open before they search — the
opposite of a flat snippet pile that grows un-navigable.

## The seven categories

The library files patterns under a flat, fixed set of domains. Each is a folder
with its own README index.

| Category   | Holds                                   | Example patterns                                      |
| ---------- | --------------------------------------- | ---------------------------------------------------- |
| `api`      | Server routes / endpoints               | user-context API, admin-context API, webhook handler, Zod-validation API |
| `ui`       | Frontend components / pages             | authenticated page, form with validation, data table |
| `database` | Schema, migrations, data access         | RLS migration, transaction wrapper                    |
| `security` | Cross-cutting safety controls           | input sanitization, rate limiting, secrets management |
| `testing`  | Test shapes                             | API integration test, e2e user flow                   |
| `ci`       | Pipeline / delivery automation          | CI workflow, deployment pipeline                      |
| `config`   | App configuration / observability       | typed environment config, structured logging          |

## Folder layout

```
patterns_library/
├── README.md            # master index (use-case → pattern file)
├── api/
│   ├── user-context-api.md
│   ├── admin-context-api.md
│   ├── webhook-handler.md
│   └── zod-validation-api.md
├── ui/
│   ├── authenticated-page.md
│   ├── form-with-validation.md
│   └── data-table.md
├── database/
│   ├── rls-migration.md
│   └── prisma-transaction.md
├── security/   …
├── testing/    …
├── ci/         …
└── config/     …
```

One pattern = one file. The filename is the slug of the pattern name
(`user-context-api.md`), so a path is self-describing.

## The README-index contract

The master README is the **front door**, not an afterthought. It carries, per
category, a table mapping **use case → pattern file**:

```markdown
### API Routes
| Pattern              | File                          | Use Case                      |
| -------------------- | ----------------------------- | ----------------------------- |
| User Context API     | ./api/user-context-api.md     | User-specific CRUD operations |
| Webhook Handler      | ./api/webhook-handler.md      | Stripe, Clerk, 3rd-party events |
```

Plus a flat **"if you need to… → use this pattern"** matrix for fast matching:

```markdown
| If you need to...                 | Use this pattern            |
| --------------------------------- | --------------------------- |
| Create authenticated API endpoint | api/user-context-api.md     |
| Add new table with RLS            | database/rls-migration.md   |
| Validate API input with a schema  | api/zod-validation-api.md   |
```

**Contract:** every admitted pattern is added to both the category table and the
matrix **in the same commit** as the pattern file. An un-indexed pattern is
invisible to discovery and therefore dead weight.

## When to add a category

Rarely. A small taxonomy is a feature — it keeps "which folder?" a one-second
decision. Add a category only when a genuinely **new domain** of patterns emerges
(e.g. a first batch of `messaging` or `auth` patterns that fits none of the
seven), not per individual pattern. Resist the urge to subdivide: depth in
folders trades scannability for nothing.

## Maintenance roles

- **Owner:** the architect role — admits patterns, keeps the index authoritative.
- **Contributors:** discover gaps, extract and document patterns.
- **Consumers:** all execution agents — use patterns, report gaps.
- **Update cadence:** as new patterns emerge from production code (frequency-driven,
  per [capturing-patterns.md](capturing-patterns.md)), not on a fixed schedule.
