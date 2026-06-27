---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Lex Council Design Language

> **Mode of `design-language`.** The product voice of the Lex Council app — a legal-financial
> council. Load via the dispatcher when writing UI strings, changelogs, client-facing copy, or
> docs for the product. Triggers: "Lex Council tone", "write this in the council voice",
> "product copy for Lex Council". This is the *words* layer; the app's *look* is `design-taste`/`brandkit`.

---

## 1. The World

**Lex Council** is a council of record: a body that keeps the law, holds the books, and certifies
what is true. The product is a multi-portal app (admin, members, clients) where records live in the
**vault**, the law lives in the **codex**, money moves through the **ledger**, and authority is
exercised by **certifying** and **sealing**. The register is **institutional, exact, and trustworthy**
— the voice of a registrar, not a startup. Calm, precise, never breezy.

**Tone:** Formal but clear. A council speaks plainly and stands behind its words. Records are *kept*,
actions are *certified*, rules are *statutes*, and nothing important is informal. Confidence without flourish.

---

## 2. Core Vocabulary Mapping

| Plain English | Lex Council Voice |
|---|---|
| Record store / database | The **vault** |
| Knowledge base / law content | The **codex** |
| Public law page | The **Codex** (the public face of the codex) |
| Financial records / transactions log | The **ledger** |
| A transaction | A **transaction** (advance, deposit, withdrawal, expense, income) |
| Protected / locked transaction | A **safe** transaction |
| Approve / confirm an action | **Certify** it |
| Lock / finalize a record | **Seal** it |
| Approval / sign-off | **Certification** |
| Agree to / accept | **Agree** (an agreement) |
| Rule / policy | **Statute** |
| Permission / access flag | A **permission** (granted by the council) |
| Admin / member / client area | A **portal** |
| Audit / review | **Inspection** / review of the record |
| Log an action (mandatory) | Enter it in the **vault log** |
| Issue / bug | A **fault** in the record (raised in the report) |
| Fix | **Remedy** / correct the record |
| Notification | A **notice** from the council |
| Required user action | **Action required** (the matter is in question until resolved) |

---

## 3. Core Surfaces & Concepts

- **Portals.** The app is three portals — **admin**, **members**, **clients**. Address each in its
  register: admins *certify and seal*; members *submit and agree*; clients *view the record*.
- **The vault & vault log.** Records of consequence are kept in the vault, and every change of record
  is entered in the **vault log** — the council keeps a complete account of its own actions.
- **The codex.** The body of law. The public **Codex** page is the council's published face — copy
  there is canonical and must read as authoritative.
- **The ledger.** Transactions flow through tabs — Personal, Pending, Approval, Certification, Safe,
  History — and move forward only when **certified**. Safe transactions are sealed and protected.
- **Statutes & permissions.** Rules are **statutes**; access is granted as **permissions** the council
  confers on a portal or role.

---

## 4. Naming Conventions

- **Council register, not consumer-app slang.** "Certify", "seal", "statute", "vault", "ledger" —
  never "approve ✅", "lock 🔒", "rules", "storage", "money".
- **State plainly what changed.** Changelog entries read as council acts: "Sealed the certification
  flow for safe transactions." State the matter, the portal, and the outcome.
- **Matters in question.** When a record awaits the user, it is **in question** until the required
  action resolves it — never "pending your input lol". Formal, never flip.

---

## 5. Writing Style

- **Registrar's plainness.** Short, exact sentences. The council does not hedge or hype. Say what is
  true and what is required.
- **Certify / seal / keep / enter.** These are the council's verbs. Records are *kept*, actions
  *certified*, finals *sealed*, logs *entered*.
- **Authority without coldness.** Formal but human — a trusted clerk, not a robot. "Your transaction
  is certified and recorded in the ledger" — clear, final, reassuring.
- **Never bury the instruction.** If the user must act, the council says so directly: *Action required.*
- **No flavour over clarity.** Unlike the fantasy voices, lex-council leans *toward* plainness. The
  vocabulary is the formality; don't add ornament on top of it.

---

## 6. Example Reskins

**Before (plain):**
> "Your payment was approved and saved. We'll notify you if anything changes."

**After (Lex Council):**
> "Your transaction is certified and entered in the ledger. The council will issue a notice if the
> record changes."

**Before (plain):**
> "Only admins can edit this setting. This rule applies to all members."

**After (Lex Council):**
> "This permission is reserved to the admin portal. The statute applies to all members."

**Before (plain):**
> "We found a bug in the transactions page and fixed it. Logged the change."

**After (Lex Council):**
> "A fault was found in the ledger and remedied. The correction is entered in the vault log."
