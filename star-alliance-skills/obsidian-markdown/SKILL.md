---
name: obsidian-markdown
description: Create and edit Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties, and other Obsidian-specific syntax. Includes an Architecture Decision Record (ADR) template in Obsidian flavor with frontmatter status and wikilinked related decisions. Use when working with .md files in Obsidian, when writing an ADR or architecture decision record, or when the user mentions wikilinks, callouts, frontmatter, tags, embeds, or Obsidian notes.
metadata:
  version: 1.1.0
type: Skill

---
# Obsidian Flavored Markdown Skill

Create and edit valid Obsidian Flavored Markdown. Obsidian extends CommonMark and GFM with wikilinks, embeds, callouts, properties, comments, and other syntax. This skill covers only Obsidian-specific extensions -- standard Markdown (headings, bold, italic, lists, quotes, code blocks, tables) is assumed knowledge.

## Workflow: Creating an Obsidian Note

1. **Add frontmatter** with properties (title, tags, aliases) at the top of the file. See [PROPERTIES.md](skills/obsidian-markdown/references/PROPERTIES.md) for all property types.
2. **Write content** using standard Markdown for structure, plus Obsidian-specific syntax below.
3. **Link related notes** using wikilinks (`[[Note]]`) for internal vault connections, or standard Markdown links for external URLs.
4. **Embed content** from other notes, images, or PDFs using the `![[embed]]` syntax. See [EMBEDS.md](skills/obsidian-markdown/references/EMBEDS.md) for all embed types.
5. **Add callouts** for highlighted information using `> [!type]` syntax. See [CALLOUTS.md](skills/obsidian-markdown/references/CALLOUTS.md) for all callout types.
6. **Verify** the note renders correctly in Obsidian's reading view.

> When choosing between wikilinks and Markdown links: use `[[wikilinks]]` for notes within the vault (Obsidian tracks renames automatically) and `[text](url)` for external URLs only.

## Internal Links (Wikilinks)

    [[Note Name]]                          Link to note
    [[Note Name|Display Text]]             Custom display text
    [[Note Name#Heading]]                  Link to heading
    [[Note Name#^block-id]]                Link to block
    [[#Heading in same note]]              Same-note heading link

Define a block ID by appending `^block-id` to any paragraph:

    This paragraph can be linked to. ^my-block-id

For lists and quotes, place the block ID on a separate line after the block:

    > A quote block
    ^quote-id

## Embeds

Prefix any wikilink with `!` to embed its content inline:

    ![[Note Name]]                         Embed full note
    ![[Note Name#Heading]]                 Embed section
    ![[image.png]]                         Embed image
    ![[image.png|300]]                     Embed image with width
    ![[document.pdf#page=3]]               Embed PDF page

See [EMBEDS.md](skills/obsidian-markdown/references/EMBEDS.md) for audio, video, search embeds, and external images.

## Callouts

    > [!note]
    > Basic callout.
    > [!warning] Custom Title
    > Callout with a custom title.
    > [!faq]- Collapsed by default
    > Foldable callout (- collapsed, + expanded).

Common types: `note`, `tip`, `warning`, `info`, `example`, `quote`, `bug`, `danger`, `success`, `failure`, `question`, `abstract`, `todo`.

See [CALLOUTS.md](skills/obsidian-markdown/references/CALLOUTS.md) for the full list with aliases, nesting, and custom CSS callouts.

## Properties (Frontmatter)

    ---
    title: My Note
    date: 2024-01-15
    tags:
      - project
      - active
    aliases:
      - Alternative Name
    cssclasses:
      - custom-class
    ---

Default properties: `tags` (searchable labels), `aliases` (alternative note names for link suggestions), `cssclasses` (CSS classes for styling).

See [PROPERTIES.md](skills/obsidian-markdown/references/PROPERTIES.md) for all property types, tag syntax rules, and advanced usage.

## Tags

    #tag                    Inline tag
    #nested/tag             Nested tag with hierarchy

Tags can contain letters, numbers (not first character), underscores, hyphens, and forward slashes. Tags can also be defined in frontmatter under the `tags` property.

## Comments

    This is visible %%but this is hidden%% text.

    %%
    This entire block is hidden in reading view.
    %%

## Obsidian-Specific Formatting

    ==Highlighted text==                   Highlight syntax

## Math (LaTeX)

Inline: `$e^{i\pi} + 1 = 0$`

Block:

    $$
    \frac{a}{b} = c
    $$

## Diagrams (Mermaid)

    ```mermaid
    graph TD
        A[Start] --> B{Decision}
        B -->|Yes| C[Do this]
        B -->|No| D[Do that]
    ```

To link Mermaid nodes to Obsidian notes, add `class NodeName internal-link;`.

## Footnotes

    Text with a footnote[^1].
    [^1]: Footnote content.
    Inline footnote.^[This is inline.]

## Complete Example

    ---
    title: Project Alpha
    date: 2024-01-15
    tags:
      - project
      - active
    status: in-progress
    ---

    # Project Alpha

    This project aims to [[improve workflow]] using modern techniques.

    > [!important] Key Deadline
    > The first milestone is due on ==January 30th==.

    ## Tasks

    - [x] Initial planning
    - [ ] Development phase
      - [ ] Backend implementation
      - [ ] Frontend design

    ## Notes

    The algorithm uses $O(n \log n)$ sorting. See [[Algorithm Notes#Sorting]] for details.

    ![[Architecture Diagram.png|600]]

    Reviewed in [[Meeting Notes 2024-01-10#Decisions]].

## Templates: Architecture Decision Records (ADRs)

An Architecture Decision Record captures one significant decision so the *why*
survives the people who made it. In an Obsidian vault each ADR is a single note,
using frontmatter properties for the status and wikilinks for Related Decisions
so the graph wires the decisions together and backlinks need no manual index.

The structure is Status, Context, Decision, Consequences (positive / negative /
neutral), Implementation Notes, and Related Decisions:

    ---
    title: ADR-XXX Short Decision Title
    date: 2026-06-28
    status: proposed          # proposed | accepted | deprecated | superseded
    tags:
      - adr
      - adr/<domain>
    aliases:
      - ADR-XXX
    ---

    # ADR-XXX: Short Decision Title

    > [!info] Status
    > **proposed**

    ## Context
    What forces motivate this decision?

    ## Decision
    What we will do, in one active sentence, then expanded.

    ## Consequences
    ### Positive
    - Benefit
    ### Negative
    - Tradeoff we accept
    ### Neutral
    - A fact that follows

    ## Implementation Notes
    How to carry it out; link supporting notes with [[wikilinks]].

    ## Related Decisions
    - [[ADR-YYY Related Decision]] -- how it relates

**Convention:** store ADRs in an `ADRs/` folder, one note per decision, named
`ADR-XXX Short Decision Title.md` with a zero-padded sequential number that is
never reused. Put the bare `ADR-XXX` in `aliases` so `[[ADR-014]]` shorthand
resolves. When an ADR is superseded, set `status: superseded`, link the
replacement in the Status callout (`superseded by [[ADR-YYY Title]]`), and add a
backlink under the new ADR's Related Decisions.

See [adr-template.md](skills/obsidian-markdown/references/adr-template.md) for the
full template, status-value table, naming convention, and a worked example.

## References

- [Obsidian Flavored Markdown](https://help.obsidian.md/obsidian-flavored-markdown)
- [Internal links](https://help.obsidian.md/links)
- [Embed files](https://help.obsidian.md/embeds)
- [Callouts](https://help.obsidian.md/callouts)
- [Properties](https://help.obsidian.md/properties)

## Changelog

- **1.1.0** — Added an Architecture Decision Record (ADR) template in Obsidian
  flavor (frontmatter `status`, wikilinked Related Decisions) plus output-location
  and naming convention. New reference: `references/adr-template.md`. Adapted from
  the Safe Agentic Workflow `confluence-docs` ADR template.
- **1.0.0** — Initial Obsidian Flavored Markdown skill (wikilinks, embeds,
  callouts, properties, tags, comments, math, Mermaid, footnotes).
