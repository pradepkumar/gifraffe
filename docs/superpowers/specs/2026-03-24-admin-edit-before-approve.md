# Admin Edit-Before-Approve — Design Spec

**Date:** 2026-03-24
**Status:** Approved

## Overview

Allow the admin to edit a pending GIF's metadata (title, tags, description) inline in the approval queue before approving it. Edits are submitted as part of the approve action — no separate save step.

## Scope

**In scope:**
- Editable fields: `title`, `tags`, `description`
- Editing happens inline in the queue card (always-editable inputs)
- Edited values are sent with the approve request and persisted to the DB

**Out of scope:**
- Submitter info (`submitter_name`, `submitter_email`) — read-only
- Source URL / timestamps — read-only
- Persisting edits across page refresh (not needed for admin workflow)
- Editing after approval

## Backend

### `POST /api/admin/approve/{gif_id}`

Add an optional request body:

```python
class ApproveRequest(BaseModel):
    title: str | None = None
    tags: list[str] | None = None
    description: str | None = None
```

Before moving the file and setting `status='approved'`, apply any provided non-None fields:

```sql
UPDATE gifs SET title=?, tags=?, description=? WHERE id=?
```

- `tags` stored as comma-joined string (existing convention: `",".join(tags)`)
- If a field is `None` in the request body, the existing DB value is unchanged
- The endpoint remains backward-compatible: an empty body behaves as before

### No new endpoints needed.

## Frontend

### `api.js`

Update `approveGif`:

```js
export async function approveGif(id, fields = {}) {
  const res = await fetch(`${BASE}/api/admin/approve/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Approve failed')
  return res.json()
}
```

### `Admin.jsx`

**Edit state:** Add `const [edits, setEdits] = useState({})`.

When the queue loads (both in `loadQueue` and the mount `useEffect`), initialise the edits map from the fetched data:

```js
const toEdits = (results) =>
  Object.fromEntries(results.map(g => [g.id, {
    title: g.title,
    tags: g.tags.join(', '),
    description: g.description ?? '',
  }]))
```

Call `setEdits(toEdits(data.results))` wherever `setQueue(data.results)` is called.

**Per-card rendering** — replace static display with controlled inputs:

| Field | Element | Notes |
|-------|---------|-------|
| title | `<input type="text">` | Full width |
| tags | `<input type="text">` | Comma-separated; placeholder "tag1, tag2" |
| description | `<textarea>` | Optional; show even when empty so admin can add one |

Each input calls `setEdits(e => ({ ...e, [gif.id]: { ...e[gif.id], field: value } }))`.

**On Approve** — pass current edits to `approveGif`:

```js
const handleApprove = async (id) => {
  const { title, tags, description } = edits[id] ?? {}
  await approveGif(id, {
    title: title?.trim() || undefined,
    tags: tags ? tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
    description: description?.trim() ?? undefined,
  })
  // remove from queue as before
}
```

Fields left as `undefined` are omitted from the JSON body and ignored by the backend.

## Styling

Inline inputs match the existing amber/savanna palette:
- Border: `2px solid #e8c97a`
- Background: `#fffdf5`
- Border-radius: `8px`
- Padding: `8px 10px`
- Width: `100%`, `box-sizing: border-box`

The visual layout of each card is unchanged — the inputs simply replace the static `<h3>`, `<p>`, and `<TagChip>` elements.

## Testing

**Backend:**
- `POST /api/admin/approve/{id}` with a body updates `title`, `tags`, `description` in the DB before approving
- `POST /api/admin/approve/{id}` with an empty body behaves identically to the current implementation
- After approval, `GET /api/gifs/{id}` reflects the updated fields

**Frontend:**
- No automated tests (existing project has no frontend tests)
- Manual smoke test: edit title + tags on a pending GIF, approve, verify updated values appear on the Browse page
