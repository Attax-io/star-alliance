---
type: Document
title: Server vs Client Components, Data Fetching, Caching & Forms
description: The App Router / RSC mental model — where the client boundary belongs, how to fetch and cache deliberately, stream with Suspense, and handle mutations and forms with Server Actions.
timestamp: 2026-06-28T00:00:00Z
---

# Server vs client, data fetching, streaming & forms (App Router / RSC)

The single most consequential decision in a Next.js App Router app is **where code runs**. Get it wrong and you ship a megabyte of JS for a static page, or leak a secret, or block the whole page on the slowest query.

## The default-server mental model

**Rule.** In the App Router, *every component is a Server Component until proven otherwise*. `"use client"` opts a component — and its entire import subtree — into the browser bundle. Treat the directive as a cost, and push it as far down the tree as possible.

A Server Component can: `await` data directly, read secrets/env, import heavy libraries without shipping them, and render to HTML with zero client JS. It **cannot** use state, effects, browser APIs, or event handlers.

A Client Component can do interactivity (`useState`, `onClick`, `useEffect`, browser APIs) but ships JS and cannot be `async` at the top level.

**The boundary rule.** Mark the smallest interactive *leaf* as client; keep the data-fetching shell on the server. A client component may *render* server components only by receiving them as `children`/props (the "donut" pattern) — it cannot import them.

```tsx
// layout/shell: Server Component, fetches + composes
export default async function Page() {
  const posts = await getPosts();                 // server-only data access
  return (
    <Feed>                                         {/* server */}
      {posts.map(p => <Post key={p.id} post={p} />)} {/* server */}
      <Composer />                                  {/* the only client island */}
    </Feed>
  );
}

// composer.tsx
"use client";                                       // boundary at the interactive leaf
export function Composer() { const [draft, setDraft] = useState(''); /* ... */ }
```

**Anti-pattern.** `"use client"` at the top of `page.tsx` because one widget needs `onClick`. That drags the whole subtree — and its data fetching — into the client, re-introducing `useEffect` fetching and shipping JS you didn't need.

## Data fetching: on the server, in parallel

**Rule.** Fetch where the data is rendered, on the server, and fan out independent requests **in parallel** — never `await` independent calls in series.

```tsx
// ANTI: serial — page latency = sum of all three
const a = await getA(); const b = await getB(); const c = await getC();

// RIGHT: parallel — page latency = the slowest one
const [a, b, c] = await Promise.all([getA(), getB(), getC()]);
```

When you genuinely need client-side fetching (polling, infinite scroll, data tied to client interaction), use a query library (TanStack Query / SWR) — not a hand-rolled `useEffect` + `useState`. It gives you caching, dedup, revalidation, and request cancellation for free, and keeps server state out of component state.

## Caching deliberately

**Rule.** Caching is a decision, not a default — name the freshness requirement per fetch.

- **Static / build-time** for data that rarely changes.
- **Revalidated (ISR)** — `revalidate: N` seconds, or `revalidateTag` / `revalidatePath` after a mutation — for data that changes occasionally.
- **Dynamic / no-store** for per-request or user-specific data.

```tsx
const data = await fetch(url, { next: { revalidate: 60, tags: ['posts'] } }); // ISR + tag
// after a mutation:
revalidateTag('posts');                                                       // surgical bust
```

Tag your fetches so a mutation can invalidate exactly what changed instead of nuking the whole route.

## Streaming with Suspense

**Rule.** Don't block the shell on the slowest region. Wrap genuinely slow subtrees in `<Suspense>` with a *designed* skeleton so the shell paints instantly and slow content streams in.

```tsx
export default function Page() {
  return (
    <>
      <Header />                                  {/* paints immediately */}
      <Suspense fallback={<FeedSkeleton />}>
        <Feed />                                  {/* async RSC; streams when resolved */}
      </Suspense>
      <Suspense fallback={<SidebarSkeleton />}>
        <Recommendations />                       {/* independent — streams separately */}
      </Suspense>
    </>
  );
}
```

Use a real skeleton matching the final layout (no layout shift), and an `error.tsx` boundary so a failed region degrades gracefully instead of blanking the page.

## Mutations & forms — Server Actions

**Rule.** Mutate through Server Actions (or route handlers), keep the form usable without JS, validate on the server, and revalidate the affected cache after the write.

```tsx
// actions.ts
"use server";
export async function createPost(formData: FormData) {
  const parsed = PostSchema.parse(Object.fromEntries(formData)); // validate on the server
  await db.post.create({ data: parsed });
  revalidateTag('posts');                                        // refresh what changed
}

// form.tsx — works without client JS; progressively enhanced
<form action={createPost}>
  <input name="title" required />
  <SubmitButton />                {/* useFormStatus() for pending state when JS is on */}
</form>
```

For perceived speed, layer **optimistic UI** (`useOptimistic`) on top — but the server result remains the source of truth, and the error path is designed, not an afterthought.

## Quick decision table

| Need | Where it runs |
|---|---|
| Read DB/secret, render data | Server Component |
| `onClick`/`useState`/browser API | Client Component (leaf) |
| Independent fetches | `Promise.all` on the server |
| Per-interaction/polling fetch | Client query lib |
| Slow region | `<Suspense>` + skeleton |
| Write / form submit | Server Action + `revalidateTag` |
| Tab / filter / page | URL `searchParams` |
