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

### `models.py` — add `ApproveRequest`

Add alongside the existing models (`AdminLoginRequest`, `AdminGifItem`):

```python
class ApproveRequest(BaseModel):
    title: str | None = None
    tags: list[str] | None = None
    description: str | None = None
```

### `routes/admin.py` — update `approve_gif`

**Imports:** Add `Body` to the existing fastapi import line and `ApproveRequest` to the models import:

```python
from fastapi import APIRouter, Body, Cookie, HTTPException, Request, Response
from models import AdminLoginRequest, AdminGifItem, ApproveRequest
```

**Endpoint signature** — add the optional request body:

```python
@router.post("/api/admin/approve/{gif_id}")
async def approve_gif(
    gif_id: str,
    request: Request,
    req: ApproveRequest = Body(default=ApproveRequest()),
    gifraffe_session: str | None = Cookie(default=None),
):
```

**Partial-update logic:** only update columns that are explicitly provided (non-`None`). Add this block inside the existing `try` block, **before** the `move_file` call, using the same `get_conn` / `conn.commit()` / `try/finally conn.close()` pattern already used throughout `admin.py`:

```python
conn = get_conn(settings.db_path)
try:
    row = conn.execute("SELECT * FROM gifs WHERE id=? AND status='pending'", (gif_id,)).fetchone()
    if not row:
        raise HTTPException(404, detail="Pending GIF not found")

    # Apply field edits before approving
    updates = {}
    if req.title is not None:
        updates["title"] = req.title.strip()
    if req.tags is not None:
        updates["tags"] = ",".join(req.tags)
    if req.description is not None:
        updates["description"] = req.description.strip()
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        conn.execute(
            f"UPDATE gifs SET {set_clause} WHERE id=?",
            (*updates.values(), gif_id)
        )

    src = Path(settings.storage_dir) / "pending" / f"{gif_id}.gif"
    dst = Path(settings.storage_dir) / "gifs" / f"{gif_id}.gif"
    move_file(src, dst)
    conn.execute("UPDATE gifs SET status='approved', file_path=? WHERE id=?", (str(dst), gif_id))
    conn.commit()
finally:
    conn.close()
```

An empty body (all fields `None`) skips the field UPDATE entirely — backward-compatible with existing behaviour. The field update and status update share the same `conn.commit()`, so either both persist or neither does.

## Frontend

### `api.js`

Update `approveGif` to accept and send field overrides:

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

Define a helper to initialise edits from queue results (tags as comma-separated string for the input):

```js
const toEdits = (results) =>
  Object.fromEntries(results.map(g => [g.id, {
    title: g.title,
    tags: (g.tags ?? []).join(', '),
    description: g.description ?? '',
  }]))
```

Call `setEdits(toEdits(data.results))` **everywhere** `setQueue(data.results)` is called. There are two places:

1. Inside `loadQueue`:
```js
setQueue(data.results)
setEdits(toEdits(data.results))
```

2. Inside the mount `useEffect` `.then` callback:
```js
getAdminQueue()
  .then(data => { setAuthed(true); setQueue(data.results); setEdits(toEdits(data.results)) })
  .catch(() => {})
```

**Per-card rendering** — replace static display with controlled inputs:

| Field | Element | Notes |
|-------|---------|-------|
| title | `<input type="text">` | Full width |
| tags | `<input type="text">` | Comma-separated; placeholder "tag1, tag2" |
| description | `<textarea>` | Always shown (so admin can add a description even if empty) |

Each input reads from `edits[gif.id]` and updates via:
```js
setEdits(e => ({ ...e, [gif.id]: { ...e[gif.id], title: value } }))
```

**On Approve** — read edits and pass to `approveGif`. Use `||` for all three fields so an empty string is treated as "no change" (field omitted, existing DB value preserved):

```js
const handleApprove = async (id) => {
  const { title, tags, description } = edits[id] ?? {}
  await approveGif(id, {
    title: title?.trim() || undefined,
    tags: tags ? tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
    description: description?.trim() || undefined,
  })
  setQueue(q => q.filter(g => g.id !== id))
}
```

All three fields use `|| undefined` so an empty string is omitted from the JSON body (`JSON.stringify` drops `undefined` values). The backend receives only fields the admin filled in.

## Styling

Inline inputs match the existing amber/savanna palette, consistent with `MetadataForm.jsx`:

```js
{
  width: '100%',
  padding: '8px 10px',
  borderRadius: 8,
  border: '2px solid #e8c97a',
  background: '#fffdf5',
  fontSize: '0.9rem',
  outline: 'none',
  boxSizing: 'border-box',
}
```

Textarea gets the same style plus `resize: 'vertical'` and `minHeight: 60`.

## Testing

Add to `backend/tests/test_routes_admin.py`. The existing `insert_pending_gif` module-level helper and `login` helper are already defined in that file — reuse them directly (same pattern as all other tests in that file).

**`test_approve_updates_fields`** — insert a pending GIF with `insert_pending_gif`, login with `login(client)`, call `POST /api/admin/approve/{id}` with body `{"title": "Updated", "tags": ["new"], "description": "desc"}`. Assert 200, then query the DB directly and confirm `title="Updated"`, `tags="new"`, `description="desc"`, and `status="approved"`.

**`test_approve_empty_body_preserves_fields`** — same pattern with an empty body `{}`. Assert 200 and that `title`, `tags`, `description` in the DB are unchanged from the values set by `insert_pending_gif` (title=`"Test"`, tags=`"tag1"`, description=`None`).
