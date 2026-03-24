# Live Search Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `Browse.jsx` so results filter as the user types, without requiring a button press.

**Architecture:** Replace the mount-only `useEffect` with a single debounced effect (300ms) that watches `query` and `category`. A `useRef` mount flag ensures the initial load fires immediately on first render. Existing handlers that previously called `load()` directly are simplified to only update state — the effect becomes the single source of truth for triggering `load`.

**Tech Stack:** React 18 (hooks: `useState`, `useEffect`, `useCallback`, `useRef`), Vite dev server (for manual testing)

---

### Task 1: Implement live search in Browse.jsx

**Files:**
- Modify: `frontend/src/pages/Browse.jsx`

**Spec:** `docs/superpowers/specs/2026-03-24-live-search-filter-design.md`

---

- [ ] **Step 1: Add `useRef` to the React import**

Open `frontend/src/pages/Browse.jsx`. Line 1 currently reads:

```js
import { useState, useEffect, useCallback } from 'react'
```

Change it to:

```js
import { useState, useEffect, useCallback, useRef } from 'react'
```

---

- [ ] **Step 2: Add the mount ref and replace the existing `useEffect`**

Remove this existing `useEffect` (currently around line 30):

```js
useEffect(() => { load('', '') }, [load])
```

Replace it with the following two blocks, placed in the same location (after the `load` definition, before `handleSearch`):

```js
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

---

- [ ] **Step 3: Simplify `handleTagClick`**

Find `handleTagClick` (around line 37):

```js
const handleTagClick = (tag) => {
  setQuery(tag)
  load(tag, category)
}
```

Remove the `load(tag, category)` call:

```js
const handleTagClick = (tag) => {
  setQuery(tag)
}
```

---

- [ ] **Step 4: Simplify category tab onClick**

Find the category tab `onClick` handler (inside the `{['All', ...CATEGORIES].map(...)}` block, around line 58):

```js
onClick={() => { setCategory(val); load(query, val) }}
```

Remove the `load(query, val)` call:

```js
onClick={() => setCategory(val)}
```

---

- [ ] **Step 5: Manual verification — start the dev server**

Start the backend and frontend:

```bash
# Terminal 1 — backend
cd backend && uvicorn main:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open `http://localhost:5173` and navigate to Browse.

---

- [ ] **Step 6: Verify each behaviour from the spec**

Check each of the following:

| Test | Expected |
|------|----------|
| Page loads | GIFs appear immediately (no button press needed) |
| Type a character in the search box | Results update ~300ms after you stop typing |
| Type quickly (multiple characters fast) | Only ONE request fires after you stop, not one per character (check Network tab in browser DevTools) |
| Press the Search button | Results update immediately |
| Press Enter in the search box | Results update immediately |
| Click a category tab | Results update ~300ms later, filtered by category |
| Click a tag chip on any GIF card | Search box updates and results refresh ~300ms later |
| Clear the search box | All GIFs load ~300ms after clearing |

---

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/Browse.jsx
git commit -m "feat: live search filter with 300ms debounce on Browse page"
```
