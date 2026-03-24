# Admin Edit-Before-Approve Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow the admin to edit a GIF's title, tags, and description inline before approving it.

**Architecture:** The approve endpoint accepts an optional JSON body with field overrides. On the frontend, each queue card renders controlled inputs for the three fields; edited values are passed to `approveGif()` on approve. No new endpoints are needed.

**Tech Stack:** Python/FastAPI/Pydantic (backend), React (frontend), pytest (tests)

---

## File Map

| File | Change |
|------|--------|
| `backend/models.py` | Add `ApproveRequest` model |
| `backend/routes/admin.py` | Update `approve_gif` to accept body, apply field updates |
| `backend/tests/test_routes_admin.py` | Add 2 new tests |
| `frontend/src/api.js` | Update `approveGif` to accept and send fields |
| `frontend/src/pages/Admin.jsx` | Add edit state, inline inputs, pass fields on approve |

---

## Task 1: Backend — `ApproveRequest` model + updated `approve_gif` endpoint

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/routes/admin.py`
- Test: `backend/tests/test_routes_admin.py`

- [ ] **Step 1: Write two failing tests**

Add to `backend/tests/test_routes_admin.py`:

```python
def test_approve_updates_fields(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.post(
        f"/api/admin/approve/{gid}",
        json={"title": "Updated", "tags": ["new"], "description": "desc"},
        cookies=cookies,
    )
    assert resp.status_code == 200
    conn = get_conn(db_path)
    row = conn.execute("SELECT * FROM gifs WHERE id=?", (gid,)).fetchone()
    conn.close()
    assert row["title"] == "Updated"
    assert row["tags"] == "new"
    assert row["description"] == "desc"
    assert row["status"] == "approved"

def test_approve_empty_body_preserves_fields(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.post(f"/api/admin/approve/{gid}", json={}, cookies=cookies)
    assert resp.status_code == 200
    conn = get_conn(db_path)
    row = conn.execute("SELECT * FROM gifs WHERE id=?", (gid,)).fetchone()
    conn.close()
    assert row["title"] == "Test"
    assert row["tags"] == "tag1"
    assert row["description"] is None
    assert row["status"] == "approved"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && .venv/bin/pytest tests/test_routes_admin.py::test_approve_updates_fields tests/test_routes_admin.py::test_approve_empty_body_preserves_fields -v
```

Expected: both FAIL (422 or missing field behavior)

- [ ] **Step 3: Add `ApproveRequest` to `models.py`**

Add after the `AdminGifItem` class:

```python
class ApproveRequest(BaseModel):
    title: str | None = None
    tags: list[str] | None = None
    description: str | None = None
```

- [ ] **Step 4: Update `routes/admin.py` imports**

Change the existing import lines:

```python
from fastapi import APIRouter, Body, Cookie, HTTPException, Request, Response
from models import AdminLoginRequest, AdminGifItem, ApproveRequest
```

- [ ] **Step 5: Update `approve_gif` endpoint signature and body**

Replace the existing `approve_gif` function with:

```python
@router.post("/api/admin/approve/{gif_id}")
async def approve_gif(
    gif_id: str,
    request: Request,
    req: ApproveRequest = Body(default=ApproveRequest()),
    gifraffe_session: str | None = Cookie(default=None),
):
    _require_auth(request, gifraffe_session)
    settings = request.app.state.settings
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
    return {"ok": True}
```

- [ ] **Step 6: Run the new tests and full suite**

```bash
cd backend && .venv/bin/pytest tests/test_routes_admin.py -v
```

Expected: all admin tests pass including the two new ones.

```bash
cd backend && .venv/bin/pytest tests/ -v
```

Expected: all 43 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/models.py backend/routes/admin.py backend/tests/test_routes_admin.py
git commit -m "feat: approve endpoint accepts field overrides (title, tags, description)"
```

---

## Task 2: Frontend — `api.js` and `Admin.jsx`

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/pages/Admin.jsx`

- [ ] **Step 1: Update `approveGif` in `api.js`**

Replace the existing `approveGif` function:

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

- [ ] **Step 2: Add edit state and `toEdits` helper to `Admin.jsx`**

Add `edits` state and `toEdits` helper. At the top of the `Admin` component, after the existing `useState` declarations:

```js
const [edits, setEdits] = useState({})

const toEdits = (results) =>
  Object.fromEntries(results.map(g => [g.id, {
    title: g.title,
    tags: (g.tags ?? []).join(', '),
    description: g.description ?? '',
  }]))
```

- [ ] **Step 3: Call `setEdits` wherever `setQueue` is called**

In `loadQueue`, after `setQueue(data.results)`:
```js
setEdits(toEdits(data.results))
```

In the mount `useEffect` `.then` callback, update to:
```js
getAdminQueue()
  .then(data => { setAuthed(true); setQueue(data.results); setEdits(toEdits(data.results)) })
  .catch(() => {})
```

- [ ] **Step 4: Define `inlineInputStyle` constant**

Add at the bottom of `Admin.jsx` (alongside other style constants, or at module level before the component):

```js
const inlineInputStyle = {
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

- [ ] **Step 5: Replace static card content with editable inputs**

In the queue card rendering, replace the static `<h3>`, `<p>` (description), and `<TagChip>` tags section with controlled inputs. The card's info section (inside `<div style={{ padding: 16 }}>`) should become:

```jsx
<div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 12 }}>
  <input
    type="text"
    value={edits[gif.id]?.title ?? ''}
    onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], title: e.target.value } }))}
    style={inlineInputStyle}
    placeholder="Title"
  />
  <input
    type="text"
    value={edits[gif.id]?.tags ?? ''}
    onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], tags: e.target.value } }))}
    style={inlineInputStyle}
    placeholder="tag1, tag2"
  />
  <textarea
    value={edits[gif.id]?.description ?? ''}
    onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], description: e.target.value } }))}
    style={{ ...inlineInputStyle, resize: 'vertical', minHeight: 60 }}
    placeholder="Description (optional)"
  />
</div>
```

Keep the submitter info `<p>` and source `<a>` link unchanged below the inputs.

- [ ] **Step 6: Update `handleApprove` to pass edited fields**

Replace the existing `handleApprove`:

```js
const handleApprove = async (id) => {
  setActionInProgress(id)
  try {
    const { title, tags, description } = edits[id] ?? {}
    await approveGif(id, {
      title: title?.trim() || undefined,
      tags: tags ? tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
      description: description?.trim() || undefined,
    })
    setQueue(q => q.filter(g => g.id !== id))
  } catch (e) {
    alert('Failed to approve — ' + e.message)
  } finally {
    setActionInProgress(null)
  }
}
```

- [ ] **Step 7: Build to verify no errors**

```bash
cd frontend && npm run build
```

Expected: build completes with no errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/api.js frontend/src/pages/Admin.jsx
git commit -m "feat: admin inline edit of title, tags, description before approve"
```
