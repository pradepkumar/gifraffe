# Live Search Filter — Design Spec

**Date:** 2026-03-24
**Feature:** Filter Browse page results as the user types

## Overview

Add live (as-you-type) filtering to the Browse page. Currently, the user must press the Search button or hit Enter to trigger a search. After this change, results will update automatically 300ms after the user stops typing.

## Approach

Use a debounced `useEffect` in `Browse.jsx` that watches `query` and `category`. On each change, a 300ms timer fires `load(query, category)`. The effect becomes the **single source of truth** for calling `load` — existing handlers that previously called `load()` directly (alongside `setQuery`/`setCategory`) are simplified to only update state.

**Deliberate tradeoff:** Category tab clicks and tag chip clicks will now fire the search after a 300ms debounce instead of immediately. This is intentional — it simplifies the code significantly and 300ms is imperceptible for explicit click actions.

**Initial load:** The initial page load fires without a debounce delay by using a `useRef` mount flag. On the first effect run, the ref is unset, so `load` is called immediately (on the first effect execution after paint) and the ref is set. On all subsequent runs, the 300ms debounce applies. Each new component mount creates a fresh `useRef` instance, so navigating away and back triggers a fresh immediate load.

`load` is wrapped in `useCallback` in the existing code, so it is stable across renders and safe in the dependency array.

`query` and `category` are both initialized to `''` via `useState('')` — static, not derived asynchronously — so the first effect run always fires with the correct initial values.

## Changes

### `frontend/src/pages/Browse.jsx`

**1. Replace the existing mount-only `useEffect`:**

```js
// Before (remove this)
useEffect(() => { load('', '') }, [load])

// After (add this, along with the ref above it)
const mounted = useRef(false)

useEffect(() => {
  if (!mounted.current) {
    mounted.current = true
    load(query, category)
    return
  }
  const timer = setTimeout(() => load(query, category), 300)
  return () => clearTimeout(timer)
}, [query, category, load])
```

Add `useRef` to the existing React import.

**2. Simplify `handleTagClick` — remove the direct `load()` call:**

```js
// Before
const handleTagClick = (tag) => {
  setQuery(tag)
  load(tag, category)
}

// After
const handleTagClick = (tag) => {
  setQuery(tag)
}
```

**3. Simplify category tab `onClick` — remove the direct `load()` call:**

```js
// Before
onClick={() => { setCategory(val); load(query, val) }}

// After
onClick={() => setCategory(val)}
```

**4. `handleSearch` is unchanged:**

```js
const handleSearch = (e) => {
  e.preventDefault()
  load(query, category)
}
```

`handleSearch` reads `query` and `category` but does not call `setQuery` or `setCategory`. This means pressing Search or Enter fires `load` exactly once immediately and does not trigger the debounced effect. **Required invariant:** `handleSearch` must never call `setQuery` or `setCategory`, or it will cause a double-fire.

No other files change.

## Behaviour

| Action | Result |
|--------|--------|
| Page load | Fires `load('', '')` on first effect run (no debounce delay) |
| Typing in search box | Fires `load` 300ms after last keystroke |
| Press Search / Enter | Fires `load` immediately via `handleSearch`; effect not re-triggered |
| Click category tab | Updates `category` state → effect fires 300ms later (intentional) |
| Click a tag chip | Updates `query` state → effect fires 300ms later (intentional) |

## Race conditions / stale results

Multiple in-flight requests may return out-of-order. Accepted as out-of-scope — the library is small and latency is low. AbortController cancellation can be added later.

## What doesn't change

- The Search button and Enter-to-submit remain
- The backend `/api/gifs` endpoint is unchanged
- No new dependencies or files

## Out of scope

- Request cancellation / AbortController (acceptable tradeoff for current scale)
- Minimum character threshold before triggering search (empty query correctly returns all GIFs)
- Debounce delay configurability (300ms is standard and sufficient)
