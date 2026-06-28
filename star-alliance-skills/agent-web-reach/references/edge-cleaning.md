---
type: Document
title: Edge Cleaning
description: Concrete struct-stripping and HTML-in-JSON cleaning of verbose platform API responses before they reach the model, for agent-web-reach.
timestamp: 2026-06-28T00:00:00Z
---

# Edge Cleaning — strip the API blob before the model sees it

Principle 5 ("clean at the edge — return signal, not structure") is abstract on its
own. This is the concrete version: a reached API response is a 40-field nested blob,
mostly structural redundancy that burns tokens. Clean it **at the reach boundary**,
in the channel, before it ever reaches the model — cleaning is part of "reach," not
a later analysis step.

Two recurring shapes need cleaning: **nested note/feed structs** (extract the
load-bearing fields, drop the rest) and **HTML-in-JSON** (API returns post bodies
with embedded HTML tags). Both are handled by a small per-channel formatter.

## Pattern A — strip a nested struct to load-bearing fields (Xiaohongshu)

`channels/xiaohongshu.py: format_xhs_result` / `_clean_note` is the reference
implementation. The raw XHS response nests the real note under `note_card` or
`note`, scatters engagement across `interact_info` / `note_interact_info` /
top-level, and carries image objects with five URL variants each. The cleaner:

- **Unwraps the envelope** once — handles a single note, a `{"items": [...]}`
  search wrapper, and a `{"data": {"items"|"notes": [...]}}` wrapper, mapping a list
  of items through the same `_clean_note`.
- **Whitelists fields** rather than blacklisting: keep `id`/`note_id`/`title`/
  `desc`/`type`/`time`, fall back to `content` only if `desc` is absent.
- **Collapses author** to `{nickname, user_id}` (tolerating `nick_name` and
  `author` aliases) instead of the full user object.
- **Normalizes engagement** by reading the same four counts
  (`liked_count`/`collected_count`/`comment_count`/`share_count`) from whichever of
  the three locations carries them.
- **Reduces images to bare URLs** — picks `url` / `url_default` / `original` from
  each image object, dropping width/height/trace/format metadata.
- **Flattens tags** to a name list, and recurses comments through a `_clean_comment`
  that keeps only `content` + author nickname + reply counts.

```python
def format_xhs_result(data):
    if isinstance(data, list):
        return [_clean_note(i) for i in data]
    if isinstance(data, dict):
        items = data.get("items")
        if items is None and isinstance(data.get("data"), dict):
            items = data["data"].get("items") or data["data"].get("notes")
        if isinstance(items, list):
            return [_clean_note(i) for i in items]   # search-feeds wrapper
        return _clean_note(data)                     # single note
    return data

def _clean_note(note):
    inner = note.get("note_card") or note.get("note") or note   # unwrap envelope
    result = {k: inner[k] for k in
              ("id","note_id","xsec_token","title","desc","type","time") if k in inner}
    # author → {nickname, user_id}; engagement from interact_info OR top-level;
    # images → bare URL list; tags → name list; comments recursed. (full code in source)
    return result
```

The rule of thumb: **whitelist the id/title/body/author/engagement/images-as-URLs/
tags/comments and discard everything else**; tolerate key aliases (`nick_name` vs
`nickname`, `note` vs `note_card`) rather than assuming one schema.

## Pattern B — strip HTML out of a JSON field (Xueqiu)

Xueqiu's hot-posts endpoint is doubly wrapped: each timeline item carries a
**JSON-encoded string** in its `data` field, and *inside* that the post `text` /
`description` is **HTML**. So the cleaner does two strips — `json.loads` the inner
string, then run a tag/entity stripper over the body — before truncating to a
preview length (`channels/xueqiu.py: get_hot_posts` + `_strip_html`):

```python
def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)                  # drop tags
    for ent, ch in (("&nbsp;"," "),("&amp;","&"),("&lt;","<"),("&gt;",">")):
        text = text.replace(ent, ch)                     # decode common entities
    return text.strip()

# per timeline item:
post = json.loads(item["data"]) if isinstance(item.get("data"), str) else {}
text = _strip_html(post.get("text") or post.get("description") or "")
results.append({
    "id": post.get("id", 0), "title": post.get("title") or "",
    "text": text[:200],                                   # truncate list previews
    "author": (post.get("user") or {}).get("screen_name", ""),
    "likes": post.get("like_count", 0),
    "url": f"https://xueqiu.com{post.get('target','')}" if post.get("target") else "",
})
```

## Doctrine

- Clean **in the channel**, at the reach boundary — never hand the raw blob to the
  model "to be cleaned later."
- **Whitelist** fields; the raw response grows new noise fields over time, a
  blacklist rots.
- **Tolerate aliases and envelope variants** — the same datum appears under several
  keys across API versions; read them all, emit one.
- **Decode HTML-in-JSON** and double-encoded JSON strings before extracting text.
- **Truncate list previews** (e.g. 200 chars) so a list response doesn't carry full
  bodies; the model asks for detail on the items it actually wants.
