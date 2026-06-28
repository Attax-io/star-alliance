---
type: Document
timestamp: 2026-06-28T00:00:00Z
---

# ADR Template (Obsidian Flavor)

An Architecture Decision Record captures one significant decision: its status,
the context that forced it, the decision itself, and the consequences. In an
Obsidian vault, each ADR is a single note. Use frontmatter properties for the
machine-readable fields (status, date, tags) and wikilinks for Related Decisions
so the vault graph wires the decisions together automatically.

Adapted from the Safe Agentic Workflow `confluence-docs` ADR template, ported to
Obsidian Flavored Markdown (frontmatter properties + wikilinks).

## Why Obsidian flavor

- **Properties over prose status.** `status:` and `date:` live in frontmatter, so
  Dataview/search can list every Accepted ADR or every decision touching one area.
- **Wikilinks for Related Decisions.** `[[ADR-014 Caching Layer]]` makes each
  related decision a real graph edge — backlinks surface every ADR that
  references this one, with no manual index to maintain.
- **Tags for grouping.** `#adr` plus a domain tag (`#adr/security`) lets the vault
  collect decisions by area.

## The template

    ---
    title: ADR-XXX Short Decision Title
    date: 2026-06-28
    status: proposed
    tags:
      - adr
      - adr/<domain>
    deciders:
      - Name or Role
    aliases:
      - ADR-XXX
    ---

    # ADR-XXX: Short Decision Title

    > [!info] Status
    > **proposed** | accepted | deprecated | superseded by [[ADR-YYY Title]]

    ## Context

    What is the issue that motivates this decision? Capture the forces at play:
    technical constraints, business drivers, the problem we keep hitting. State
    the facts neutrally — the decision should read as inevitable given the context.

    ## Decision

    What is the change we are proposing and/or doing? State it in one clear,
    active sentence, then expand. "We will ___."

    ## Consequences

    ### Positive

    - [Benefit that this decision unlocks]
    - [Benefit]

    ### Negative

    - [Tradeoff or cost we accept]
    - [Tradeoff]

    ### Neutral

    - [Observation that is neither good nor bad — a fact that follows]

    ## Implementation Notes

    How should this decision be implemented? Migration steps, affected modules,
    rollout order, anything a future reader needs to act on it. Link supporting
    notes with `[[wikilinks]]`.

    ## Related Decisions

    - [[ADR-YYY Related Decision]] — how it relates (supersedes, depends on, refines)
    - [[ADR-ZZZ Related Decision]]

    ## References

    - [External documentation](https://example.com)
    - [[Supporting Note]]

## Status values

| Status         | Meaning                                                        |
| -------------- | -------------------------------------------------------------- |
| `proposed`     | Drafted, not yet agreed. Open for discussion.                  |
| `accepted`     | Agreed and in force. The current answer.                       |
| `deprecated`   | No longer recommended, but not replaced by a specific ADR.     |
| `superseded`   | Replaced — link the replacement: `superseded by [[ADR-YYY]]`.  |

When an ADR is superseded, set this note's `status: superseded`, add the
`superseded by [[ADR-YYY Title]]` wikilink in the Status callout, and add a
`[[ADR-XXX Title]]` backlink under the new ADR's **Related Decisions**.

## Output location & naming convention

| Item        | Convention                                                          |
| ----------- | ------------------------------------------------------------------- |
| Folder      | `ADRs/` (or `docs/adr/`) at the vault root                          |
| Filename    | `ADR-XXX Short Decision Title.md` — zero-padded number, space-cased |
| Number      | Sequential, never reused. `ADR-001`, `ADR-002`, …                   |
| `title`     | `ADR-XXX Short Decision Title` (matches the filename, no extension) |
| `aliases`   | Include the bare `ADR-XXX` so `[[ADR-014]]` resolves                |

Obsidian filenames can contain spaces, so `ADR-014 Caching Layer.md` is preferred
over hyphenated slugs — wikilinks read naturally (`[[ADR-014 Caching Layer]]`).
Add the bare number to `aliases` so a shorthand `[[ADR-014]]` link still resolves.

## Worked example

    ---
    title: ADR-014 Adopt Wikilinks for Cross-Doc References
    date: 2026-06-28
    status: accepted
    tags:
      - adr
      - adr/docs
    deciders:
      - The Architect
    aliases:
      - ADR-014
    ---

    # ADR-014: Adopt Wikilinks for Cross-Doc References

    > [!info] Status
    > **accepted**

    ## Context

    Decision records reference each other constantly, but Markdown-path links
    break the moment a file is renamed, and there is no backlink view to see what
    points at a given decision.

    ## Decision

    We will use Obsidian `[[wikilinks]]` for all intra-vault references between
    ADRs and supporting notes; plain Markdown links are reserved for external URLs.

    ## Consequences

    ### Positive

    - Renames update every reference automatically.
    - Backlinks reveal every ADR that depends on this one, for free.

    ### Negative

    - Links only resolve inside Obsidian; raw-GitHub rendering shows `[[…]]` literally.

    ### Neutral

    - Existing path-style links must be migrated once.

    ## Implementation Notes

    Sweep `ADRs/` and convert `[text](./ADR-…md)` links to `[[ADR-… Title]]`.

    ## Related Decisions

    - [[ADR-002 Documentation Home in Obsidian]] — this refines its linking rule.

    ## References

    - [[Obsidian Flavored Markdown Skill]]
