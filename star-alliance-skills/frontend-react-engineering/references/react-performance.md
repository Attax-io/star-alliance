---
type: Document
title: React Performance — Re-render Control, Memoization, Code-Splitting & Lists
description: Profile-first performance craft — controlling re-renders through structure before memoization, memoizing only what earns it, code-splitting the right boundaries, and rendering large lists without jank.
timestamp: 2026-06-28T00:00:00Z
---

# React performance

Performance work that survives review is *measured*. The wrong instinct — wrapping everything in `useMemo`/`memo` "to be safe" — adds comparison cost and memory while hiding the real bottleneck. Profile first, fix the component that's actually hot, and prefer structural fixes over memo spam.

## Measure before you touch anything

**Rule.** Open the React DevTools **Profiler**, record the slow interaction, and find the component that *actually* re-renders or renders slowly. Optimize that one. Without a measurement you are guessing, and memoization-by-vibe ages badly.

Key signals: a component re-rendering when its visible output didn't change; a render that's individually expensive (big list, heavy compute); a `memo` boundary that never holds because an unstable prop (inline object/array/function) breaks it every render.

## Structure beats memoization

The largest re-render wins are structural and free — reach for them before `useMemo`.

**Pass slow subtrees as `children`.** Children passed in as props don't re-render when the parent's state changes, because their element identity is stable.

```tsx
// <ExpensiveTree /> does NOT re-render when Counter increments — it's a prop, created by the parent above
function Counter({ children }: { children: React.ReactNode }) {
  const [n, setN] = useState(0);
  return <div onClick={() => setN(n + 1)}>{n}{children}</div>;
}
<Counter><ExpensiveTree /></Counter>
```

**Lift expensive subtrees out of frequently-changing parents.** If only a small region changes often, isolate the changing state in a small child so the heavy siblings don't re-render.

**Split context.** A context change re-renders every consumer; separate fast-changing and slow-changing values into different providers so a tick in one doesn't wake the other's readers.

## Memoize only what earns it

`memo`, `useMemo`, `useCallback` have a cost (the comparison + retained memory). Apply them deliberately:

- **`useMemo`** — for a genuinely expensive computation (sorting/filtering a large array, building a heavy derived structure). Not for `a + b`.
- **`useCallback` / `useMemo` on props** — to keep a prop *referentially stable* so a downstream `memo` boundary actually holds. Pointless unless the child is memoized and the prop identity is what breaks it.
- **`memo`** — on a component that re-renders often with the same props and whose render is non-trivial. Pointless if its props change every render anyway (inline objects/arrays/callbacks defeat it).

```tsx
// Earns it: expensive derivation, memoized; callback stabilized for a memoized row
const sorted = useMemo(() => bigList.sort(cmp), [bigList]);
const onPick = useCallback((id: string) => select(id), [select]);
return sorted.map(r => <Row key={r.id} row={r} onPick={onPick} />); // Row is React.memo
```

**Anti-pattern.** `useMemo`/`useCallback` on everything "to be safe" — it adds dependency arrays to maintain, costs comparisons, and obscures which memo actually matters. (React's Compiler can automate much of this; until it's in play, memoize with intent.)

## Code-splitting at the right boundary

**Rule.** Split on boundaries the user doesn't need immediately — routes (automatic in the App Router), heavy below-the-fold components, modals/dialogs, and big optional dependencies (a chart lib, an editor).

```tsx
const Chart = dynamic(() => import('./Chart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,                       // skip SSR for a client-only heavy dep
});
```

Don't split tiny components (the request overhead outweighs the savings), and don't lazy-load anything above the fold that the user sees on first paint. Pair a split with a real skeleton to avoid layout shift.

## Large lists

**Rule.** Rendering thousands of DOM nodes janks scroll and inflates memory. **Virtualize** (e.g. TanStack Virtual / react-window) so only visible rows mount.

- Stable `key` per row (real id, never index) — index keys corrupt row state on reorder/filter.
- Memoize the row component and keep its props referentially stable so virtualization doesn't re-render every visible row each scroll tick.
- Paginate or infinite-scroll the data source; don't fetch 10k rows to render 20.

## Other production wins

- **Images:** use `next/image` for sizing, lazy-loading, and format negotiation; always set dimensions to prevent CLS.
- **Fonts:** `next/font` to self-host and avoid layout shift / render-blocking.
- **Bundle:** import named exports from large libs (or per-module paths) so tree-shaking works; watch the bundle analyzer for an accidental heavy dep pulled into a client component.
- **Keep heavy deps server-side:** a formatting/parsing lib imported only in a Server Component never reaches the browser bundle at all.

## Checklist

1. Profiled and found the actually-hot component.
2. Tried the structural fix (children-as-prop / lift state / split context) first.
3. Memoized only expensive compute or props that break a real `memo` boundary.
4. Code-split routes, modals, and heavy optional deps — not tiny or above-fold pieces.
5. Virtualized any list over a few hundred rows, with stable keys.
6. `next/image` + `next/font` to kill layout shift.
