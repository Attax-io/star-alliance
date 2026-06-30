---
type: Document
title: Analytics & Instrumentation — Product-Event Taxonomy, Capture-at-the-Leaf, SPA Pageviews & Feature Flags
description: Provider-neutral instrumentation craft for production React — a snake_case category-prefixed event taxonomy, capturing events at the interactive leaf, manual $pageview tracking for client-side route changes, and feature-flag-gated component branches. PostHog shown as the concrete example.
timestamp: 2026-06-28T00:00:00Z
---

# Analytics & instrumentation

A production frontend that fires no product events ships half-blind: nobody can tell whether the feature is used, where the funnel leaks, or whether the experiment won. Instrumentation is part of *shipping*, not a later add-on — the same shape as accessibility and types. Wire it in at the leaf as you build the component, with names that read like an event log a year from now.

This is **provider-neutral**. The examples use PostHog (`posthog-js/react`) because it is concrete, but the patterns — a stable taxonomy, capture at the interactive boundary, explicit SPA pageviews, flag-gated branches — hold for any analytics provider (Segment, Amplitude, GA4, a thin in-house wrapper). Swap `posthog?.capture(...)` for `analytics.track(...)` and the discipline is identical.

## 1. Event taxonomy: snake_case, category-prefixed, past-tense

An event name is a permanent key in someone's dashboard. Treat it like a typed contract: pick a convention and never drift from it. The house rule is **`category_object_action`**, snake_case, the action in past tense (it already happened).

```
// User lifecycle
user_signed_up
user_signed_in
user_profile_updated

// Feature usage
feature_dark_mode_toggled
feature_export_clicked

// Payments / commerce
payment_checkout_started
payment_completed
subscription_upgraded

// Content
content_video_watched
content_pdf_downloaded

// Navigation / CTAs
cta_clicked
page_viewed
```

Rules that keep the taxonomy clean:

- **Prefix by category** (`payment_`, `feature_`, `content_`, `cta_`, `user_`) so events group in the dashboard and a glance tells you the domain.
- **One canonical name per concept** — `payment_checkout_started`, never also `started_checkout` or `checkoutStart`. Decide once; reuse.
- **Properties, not name explosions.** Don't mint `cta_clicked_pricing` and `cta_clicked_home`; fire `cta_clicked` with `{ page: '/pricing' }`. Names stay finite; the dimensions live in properties.
- **Centralize the names.** Export them from one module (`const EVENTS = { CTA_CLICKED: 'cta_clicked', ... } as const`) and reference the constant, so a typo can't silently fork an event into two.

## 2. Capture at the leaf, in the event handler

An analytics call lives in the **same client leaf that owns the interaction** — the `onClick`/`onSubmit` handler — not bubbled up through a prop chain and not in an effect. This is the exact mirror of the skill's client-boundary rule: the interactive island is already `"use client"`, so the capture belongs there and ships no extra surface.

```tsx
"use client";
import { usePostHog } from "posthog-js/react";

export function CtaButton({ page }: { page: string }) {
  const posthog = usePostHog();

  function handleClick() {
    // fire at the leaf, in the handler, with descriptive properties
    posthog?.capture("cta_clicked", {
      button_text: "Get Started",
      page,
      variant: "primary",
    });
    // ...then do the actual work
  }

  return <Button onClick={handleClick}>Get Started</Button>;
}
```

Why the leaf, not a parent: the parent doesn't know the click happened without an extra callback prop, and a parent-level capture drifts out of sync the moment the button's behavior changes. The optional-chain (`posthog?.`) means a missing/uninitialized provider degrades to a no-op instead of throwing — instrumentation must never crash the feature it measures.

**Don't capture in an effect** to "track when X mounted/changed." A render-driven `useEffect(() => capture(...))` double-fires under StrictMode and decouples the event from the user action that caused it. Events are user-caused → they belong in handlers (the same reasoning the effects principle applies to state).

## 3. SPA `$pageview`: track route changes yourself

Auto-capture libraries fire one pageview on the initial hard load and then go quiet, because a client-side route change in the App Router never reloads the document. In a single-page app **you** must emit the pageview on navigation, or your funnel shows one visit per session.

```tsx
"use client";
import { usePathname, useSearchParams } from "next/navigation";
import { usePostHog } from "posthog-js/react";
import { useEffect } from "react";

// Mount once high in the tree (e.g. in the root layout's client provider).
export function PageViewTracker() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const posthog = usePostHog();

  useEffect(() => {
    if (!pathname || !posthog) return;
    let url = pathname;
    const qs = searchParams?.toString();
    if (qs) url += `?${qs}`;
    posthog.capture("$pageview", { $current_url: url });
  }, [pathname, searchParams, posthog]);

  return null;
}
```

This is the *legitimate* use of an effect for analytics: a route change is a synchronization with an outside system (the URL/history), exactly what effects are for. Depend on `pathname` **and** `searchParams` so filter/tab changes count as views. Mount it once near the root, not per page.

## 4. Feature-flag-gated components

Flags let you ship a branch dark, ramp it to a cohort, and run an experiment without a redeploy. Read the flag at the leaf that branches on it and render one path or the other; keep the gate shallow so the dead branch is easy to delete once the flag graduates.

```tsx
"use client";
import { useFeatureFlagEnabled } from "posthog-js/react";

export function Checkout() {
  const newFlow = useFeatureFlagEnabled("new-checkout-flow");
  return newFlow ? <NewCheckoutFlow /> : <LegacyCheckoutFlow />;
}
```

Discipline:

- **Default to the safe path** while the flag resolves. `useFeatureFlagEnabled` can return `undefined` before the flags load — treat falsy/undefined as "old behavior" so a flag-service hiccup never blanks the page.
- **Gate the smallest unit** that differs, not a whole page, so the flag boundary is also the future delete boundary.
- **Flags are temporary.** A flag that has been at 100% for a release cycle is debt — remove the gate and the dead branch. Long-lived configuration is config, not a flag.
- The same `posthog?` no-op rule applies: a flag read must degrade gracefully when the provider is absent (SSR, tests, an env without the key).

## Where this sits in the skill

Instrumentation rides the **client leaf** the skill already isolates: the `"use client"` island that owns the click is also where the `capture` and the flag read live. It obeys the same laws as the rest of the craft — events are user-caused so they live in handlers (effects principle), the gate is a small client boundary (server/client principle), and the event names are a typed contract you don't let drift (prop-contract principle). Build it in with the component; don't bolt it on after ship.
