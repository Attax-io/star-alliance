---
type: Document
title: Component Architecture, State Placement & Hooks Discipline
description: How to draw component boundaries, place state in the smallest correct scope, keep hooks honest, and type prop contracts so illegal states are unrepresentable.
timestamp: 2026-06-28T00:00:00Z
---

# Component architecture, state & hooks

The structural decisions that decide whether a React codebase stays workable. Syntax is easy; *boundaries* and *state placement* are where production React lives or dies.

## Drawing component boundaries

**Rule.** Split a component when a *responsibility* changes, not when a file gets long. A boundary should isolate one of: a unit of layout, a unit of state, or a unit of reuse. Composition (passing children / slots) beats configuration (adding a 12th boolean prop).

**Why.** A component that owns layout + data + interaction + variants becomes untestable and re-renders for unrelated reasons. Slot-based composition lets the parent stay dumb and the pieces stay swappable.

**Example — configuration soup vs composition:**
```tsx
// ANTI: every variation is a new prop; the component knows about every caller
<Card hasIcon icon={Bell} hasBadge badgeCount={3} footerVariant="split" dense />

// BETTER: the card is a layout shell; callers compose what they need
<Card>
  <Card.Header><Bell /><Badge count={3} /></Card.Header>
  <Card.Body dense>{children}</Card.Body>
  <Card.Footer split>...</Card.Footer>
</Card>
```

## State placement — the decision order

Run this checklist *before* typing `useState`:

1. **Derivable?** If the value is computable from props or existing state, compute it during render. Don't store it.
2. **URL state?** Tab, filter, page number, selected id, search query — anything a user would expect to survive a refresh or be shareable — belongs in `searchParams` / the route, not component state.
3. **Server state?** Data you fetched lives in a cache layer (RSC fetch + revalidation, or TanStack Query / SWR on the client). Mirroring it into `useState` creates a second source of truth that drifts.
4. **Truly local + ephemeral?** Only now: `useState` (a dropdown's open flag, an input's draft value, a hover state).
5. **Genuinely cross-tree?** Only then: context (low-frequency, e.g. theme/auth) or an external store (high-frequency or large). Reach here last.

**Why URL state matters.** Storing a filter in `useState` breaks the back button, breaks deep links, and loses the state on refresh. `?status=open` is free, shareable, and correct.

```tsx
// next/navigation — filter as URL state
const params = useSearchParams();
const status = params.get('status') ?? 'all';
// changing it: router.push(`?status=${next}`) — back button now works
```

## Context: split it, keep it low-frequency

**Rule.** A context value change re-renders *every* consumer. Put slow-changing data (theme, current user, locale) in context; keep fast-changing data out, or split context into a state context and a dispatch context so setters don't re-render readers.

```tsx
// Split so components that only dispatch don't re-render when the value changes
const StateCtx = createContext<State | null>(null);
const DispatchCtx = createContext<Dispatch | null>(null);
```

## Hooks discipline

**Effects are for external synchronization only.** The dependency array must list every reactive value the effect reads — lying to it causes stale closures; omitting cleanup causes leaks. Before writing an effect, ask:

- Is this **derived state**? → compute during render, no effect.
- Is this **user-caused**? → event handler, no effect.
- Is this **data fetching** in an App-Router app? → fetch in a Server Component, no client effect.
- Is this genuinely syncing to a non-React system (DOM node, socket, `localStorage`, subscription, `document.title`)? → *now* an effect, with cleanup.

```tsx
// RIGHT: effect synchronizing with a real external system, with cleanup
useEffect(() => {
  const sock = openSocket(roomId);
  sock.onMessage(setMsg);
  return () => sock.close();            // cleanup is mandatory
}, [roomId]);                           // honest deps: every reactive value read
```

**Extract a custom hook** when the same stateful logic appears twice, or when a component's hook soup obscures its render. A custom hook is named `useThing`, returns a stable shape, and hides the wiring — not a place to dump unrelated effects.

**Stable keys, not array index.** A list `key` must be a stable identity (`item.id`), never the array index — index keys corrupt state and inputs when the list reorders or filters.

## Prop contracts (TypeScript)

**Rule.** Props are the component's public API. Type them so illegal combinations don't compile.

- Prefer **discriminated unions** over multiple optional booleans/fields — make exactly one valid state representable.
- **Derive** prop types from the source of truth (`type Props = { user: User }`, `Pick`, `ComponentProps<typeof X>`) instead of re-declaring shapes that drift.
- Never let **`any`** cross a boundary; use `unknown` + a narrow, or a real type.
- Type `children` as `React.ReactNode`; type event handlers with React's event types, not `any`.

```tsx
// Derive instead of re-declaring — props can't drift from the model
type Props = Pick<User, 'name' | 'avatarUrl'> & { onEdit: () => void };

// Extend a native element so you don't re-type every DOM prop
type ButtonProps = React.ComponentProps<'button'> & { variant: 'primary' | 'ghost' };
```

## Smells checklist

- `useEffect` that only calls `setState` from other state → derived state.
- `useState` holding fetched data → server-state layer.
- A filter/tab in `useState` → URL state.
- Index as list `key` → stable id.
- Optional-boolean prop soup → discriminated union.
- A component over ~200 lines doing layout + data + variants → split by responsibility.
