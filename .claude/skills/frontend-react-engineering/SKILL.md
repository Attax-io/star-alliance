---
name: frontend-react-engineering
description: "Production React / Next.js engineering craft for the-developer: component architecture, hooks discipline, server vs client components (App Router / RSC), state placement (local/URL/server/global), data fetching plus caching, Suspense streaming, forms and Server Actions, performance (re-render control, memoization that earns it, code-splitting, list virtualization), TypeScript prop contracts, and accessibility-aware components. Triggers: 'build this React component', 'fix this re-render', 'server or client component', 'wire this Next.js page', 'where should this state live', 'this page is slow'. Differs from image-to-code (screenshot to markup, one-shot), motion-design (the animation only), and design skills like design-tokens/design-unity (visual decisions, not engineering). Owns hardening the Designer to production-React handoff."
metadata:
  version: 1.1.0
type: Skill
changelog:
  - version: 1.1.0
    date: 2026-06-28
    note: "Added analytics & instrumentation surface (references/analytics-instrumentation.md + Principle 8): provider-neutral product-event taxonomy (snake_case, category-prefixed), capture-at-the-leaf, SPA $pageview tracking, and feature-flag-gated components. PostHog as the concrete example."
  - version: 1.0.0
    date: 2026-06-28
    note: "Initial release: production React/Next.js engineering craft (architecture, hooks, RSC boundary, data/caching, state placement, performance, TypeScript contracts, accessibility)."
---

# Frontend React Engineering

The craft of building React / Next.js (App Router, RSC) that survives production: code a real reviewer would merge, not a demo that renders once and rots. You are a senior product engineer who reasons about the render tree, the network waterfall, and the type contract before touching JSX — and who knows that the hardest React bugs are never syntax, they are *where state lives* and *when code runs*.

This skill owns the seam from a finished design to shipped, typed, accessible, fast React. It is the guild's production-React authority because the flagship product is a Next.js app.

## What it is

- Component architecture: composition over configuration, where to draw the boundary, props as a contract.
- Hooks discipline: dependency arrays, effect honesty, derived-not-stored state, custom-hook extraction.
- Server vs client components (App Router / RSC): the default-server mental model and where the `"use client"` line belongs.
- Data fetching + caching: fetch on the server, cache deliberately, stream with Suspense, mutate with actions.
- State management: local vs server vs URL vs global — choosing the smallest correct scope.
- Performance: re-render control, memoization that earns its keep, code-splitting, list virtualization.
- TypeScript hygiene: prop contracts, discriminated unions for variant components, no `any` at a boundary.
- Accessibility-aware components: semantics, focus, and keyboard wired in at build time, not bolted on.
- Analytics & instrumentation: a stable product-event taxonomy, capture at the interactive leaf, SPA pageview tracking, and feature-flag-gated branches — wired in as the component ships, not later.

## What it is NOT

- **Not image-to-code** — that turns a screenshot into markup in one shot. This takes an already-built or designed component and makes it *engineered*: typed, performant, correctly client/server-split, stateful.
- **Not motion-design** — that owns the animation curve and choreography. This wires the component the animation rides on.
- **Not a design skill** (design-tokens, design-unity, design-taste) — those make the visual decisions. This consumes their tokens and renders them faithfully in React; it never invents spacing or color.
- **Not backend / data-model work** — it calls the API and shapes the response into props; it does not design the schema.

## Principles

### 1. Decide where code runs before you write a line of it.

In the App Router every component is a Server Component until you write `"use client"`. That directive is not decoration — it ships JavaScript to the browser, forfeits direct data access, and taints every child as client too. So push the boundary *down*: keep data-fetching, secrets, and heavy deps on the server; mark only the interactive leaf as client.

```tsx
// page.tsx — Server Component: fetches, no JS shipped for this part
export default async function Page() {
  const user = await getUser();            // runs on the server
  return <Profile user={user}><EditButton /></Profile>; // EditButton is the only client island
}
// edit-button.tsx
"use client";                              // the boundary lives HERE, at the leaf
export function EditButton() { const [open, setOpen] = useState(false); /* ... */ }
```

Wrong instinct: stamping `"use client"` at the top of the page because one button needs `onClick`. That makes the whole subtree client. Right instinct: a server shell with small client islands. See `references/server-vs-client-and-data.md`.

### 2. State has a home; put it in the smallest correct scope.

Most "state management" problems are a value stored in the wrong place. Ask in order: can this be **derived** from props/existing state (then don't store it)? Is it **URL** state — a tab, a filter, a page (then `searchParams`, so it's shareable and back-button-correct)? Is it **server** state — data you fetched (then it belongs to a cache/query layer, not `useState`)? Only truly local, ephemeral UI state (a dropdown's open flag) earns `useState`; only genuinely cross-tree state earns context or a store.

```tsx
// ANTI: server data mirrored into local state — now you have two sources of truth that drift
const [items, setItems] = useState([]);
useEffect(() => { fetch('/api/items').then(r => r.json()).then(setItems); }, []);

// BETTER: server state stays server state (RSC fetch, or a query lib on the client)
const { data: items } = useQuery({ queryKey: ['items'], queryFn: getItems });
```

Reach for global state last, not first. See `references/component-architecture.md`.

### 3. Effects are for synchronizing with the outside world — nothing else.

`useEffect` is an escape hatch to systems React doesn't control (the DOM, a socket, a subscription, the document title). It is **not** for transforming props into render output (do that during render), not for "running code when a prop changes" (that's usually derived state or an event handler), and not for fetching in a Server-Component world unless you genuinely need a client. An effect that sets state from other state is a re-render loop waiting to happen. When you do write one, the dependency array must be *honest* — list every reactive value it reads — and you must handle cleanup.

```tsx
// ANTI: effect to compute derived value → extra render, stale risk
const [full, setFull] = useState('');
useEffect(() => { setFull(`${first} ${last}`); }, [first, last]);

// RIGHT: derive during render
const full = `${first} ${last}`;
```

If an effect feels necessary, first ask whether the work belongs in an event handler (user-caused) or at render (data-caused). See `references/component-architecture.md`.

### 4. Measure before you memoize; render structure beats `useMemo` spam.

`memo`, `useMemo`, and `useCallback` are not free — they cost comparison work and memory, and wrapping everything is cargo-culting. The biggest re-render wins come from *structure*: lift expensive subtrees out of frequently-changing parents, pass children as props so they don't re-render, and split context so a change in one slice doesn't wake every consumer. Profile with the React DevTools Profiler, find the component that actually re-renders hot, and fix *that* — memoize a genuinely expensive computation or stabilize a prop that breaks a `memo` boundary. Premature memoization hides the real cost and ages badly.

```tsx
// Cheap structural win: `children` passed in don't re-render when Counter's state changes
function Counter({ children }: { children: React.ReactNode }) {
  const [n, setN] = useState(0);
  return <button onClick={() => setN(n + 1)}>{n}{children}</button>;
}
```

See `references/react-performance.md`.

### 5. Props are a typed contract; make illegal states unrepresentable.

A component's props are its public API. Type them so a misuse fails at compile time, not in production. Prefer **discriminated unions** over a bag of optional booleans, derive prop types from a source of truth instead of re-declaring shapes, and never let `any` cross a component boundary. A good prop type tells the next engineer exactly which combinations are legal.

```tsx
// ANTI: optional-boolean soup allows nonsense (loading AND error AND data all set)
type Props = { loading?: boolean; error?: string; data?: Item[] };

// RIGHT: discriminated union — exactly one state is representable at a time
type Props =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; items: Item[] };
```

See `references/component-architecture.md`.

### 6. Stream the slow parts; never block the whole page on the slowest query.

With RSC + Suspense you fetch in parallel and reveal content as it resolves. Don't `await` three independent calls in series and ship a blank page for the sum of their latencies — fetch them concurrently, and wrap the genuinely slow region in `<Suspense>` with a real skeleton so the shell paints instantly. Mutations go through Server Actions / route handlers with optimistic UI where it helps, and the loading and error states are designed, not afterthoughts.

```tsx
export default function Page() {
  return (
    <>
      <Header />                                   {/* instant */}
      <Suspense fallback={<FeedSkeleton />}>
        <Feed />                                   {/* streams in when ready */}
      </Suspense>
    </>
  );
}
```

See `references/server-vs-client-and-data.md`.

### 7. Build accessibility and the design contract in, not on.

Use the semantic element (`button`, `a`, `nav`, `label`) before reaching for a `div` plus ARIA; ARIA patches missing semantics, it doesn't replace them. Wire focus management, keyboard handlers, and labels as you build the component, because retrofitting them after means re-deriving the interaction model. And render the design's **tokens** — never a hardcoded hex or magic px when a token exists. The component is correct only when it is typed, fast, keyboard-operable, and visually faithful to the design source.

### 8. Instrument as you ship; a feature with no events is half-blind.

Shipping a production frontend includes making it *measurable*. The same client leaf that owns a click owns its analytics call: fire the event in the handler, never in an effect and never bubbled up a prop chain. Names are a contract — snake_case, category-prefixed, past-tense (`payment_checkout_started`, `cta_clicked`) — kept finite by pushing variation into properties, not new names. In a single-page app you emit `$pageview` yourself on every route change (the one honest analytics use of an effect), and you gate dark or experimental branches behind a feature flag that defaults to the safe path while it resolves. This is provider-neutral; the example uses PostHog but the discipline holds for any analytics layer.

```tsx
"use client";
import { usePostHog } from "posthog-js/react";
export function CtaButton({ page }: { page: string }) {
  const posthog = usePostHog();                          // optional-chain → missing provider is a no-op
  return <Button onClick={() => posthog?.capture("cta_clicked", { page })}>Get Started</Button>;
}
```

See `references/analytics-instrumentation.md`.

## References

- `references/component-architecture.md` — composition, state placement, hooks discipline, prop-contract typing.
- `references/server-vs-client-and-data.md` — RSC boundary, data fetching/caching, Suspense streaming, Server Actions, forms.
- `references/react-performance.md` — re-render control, memoization that earns its keep, code-splitting, lists.
- `references/analytics-instrumentation.md` — product-event taxonomy, capture-at-the-leaf, SPA pageview tracking, feature-flag-gated components.
