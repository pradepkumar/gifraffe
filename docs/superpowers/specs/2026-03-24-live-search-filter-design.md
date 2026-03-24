# Live Search Filter — Design Spec

**Date:** 2026-03-24
**Feature:** Filter Browse page results as the user types

## Overview

Add live (as-you-type) filtering to the Browse page. Currently, the user must press the Search button or hit Enter to trigger a search. After this change, results will update automatically 300ms after the user stops typing.

## Approach

Use a debounced `useEffect` in `Browse.jsx` that watches `query` and `category`. On each change, a 300ms timer fires `load(query, category)`. If the user types again before the timer fires, the previous timer is cleared and a new one starts.

## Changes

### `frontend/src/pages/Browse.jsx`

Replace the existing mount-only `useEffect`:
```js
useEffect(() => { load('', '') }, [load])
```

With a debounced effect that covers both the initial load and live filtering:
```js
useEffect(() => {
  const timer = setTimeout(() => load(query, category), 300)
  return () => clearTimeout(timer)
}, [query, category, load])
```

No other files change.

## Behaviour

| Action | Result |
|--------|--------|
| Page load | Loads all GIFs immediately (query is `''`, fires after 300ms — imperceptible) |
| Typing in search box | Waits 300ms after last keystroke, then fires search |
| Press Search / Enter | Fires immediately (existing `handleSearch` unchanged) |
| Click category tab | Fires immediately (existing category handler unchanged) |
| Click a tag chip | Fires immediately (existing `handleTagClick` unchanged) |

## What doesn't change

- The Search button remains
- The category tabs behaviour is unchanged
- The backend `/api/gifs` endpoint is unchanged
- No new dependencies or files

## Out of scope

- Minimum character threshold before triggering search (not needed — empty query returns all GIFs, which is correct)
- Debounce delay configurability (300ms is standard and sufficient)
