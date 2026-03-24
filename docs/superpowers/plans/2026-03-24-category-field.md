# Category Field Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a required `category` field (Tamil / English / Other) to GIFs, with a category filter on the Browse page and category editing in the admin queue.

**Architecture:** Single source of truth per layer: `CATEGORIES` constant in `models.py` (backend) and `frontend/src/constants.js` (frontend). DB migration via `ALTER TABLE` on startup. Category flows through submission, storage, retrieval, and approval.

**Tech Stack:** Python/FastAPI/Pydantic/SQLite (backend), React/Vite (frontend), pytest (tests)

**Prerequisite:** The admin-edit-before-approve plan must be fully implemented before this plan. This plan extends `ApproveRequest` and `Admin.jsx` from that plan.

---

## File Map

| File | Change |
|------|--------|
| `backend/database.py` | Add `category` column to schema + migration |
| `backend/models.py` | Add `CATEGORIES`, update `SubmitRequest`, `GifSummary`, `AdminGifItem`, `ApproveRequest` |
| `backend/routes/submit.py` | Add `category` to INSERT |
| `backend/routes/gifs.py` | Add `category` to `row_to_summary`, `GifDetail` constructor, `list_gifs` filter |
| `backend/routes/admin.py` | Add `category` to partial-update block |
| `backend/tests/test_routes_submit.py` | Add `category` to all existing payloads + 2 new tests |
| `backend/tests/test_routes_gifs.py` | Update `insert_gif` helper + 1 new test |
| `backend/tests/test_routes_admin.py` | 1 new test |
| `frontend/src/constants.js` | New file — `CATEGORIES` constant |
| `frontend/src/api.js` | Update `searchGifs` to accept `category` param |
| `frontend/src/components/MetadataForm.jsx` | Extract styles, add `categories` prop and `<select>` |
| `frontend/src/pages/Make.jsx` | Import `CATEGORIES`, pass to `MetadataForm` |
| `frontend/src/pages/Browse.jsx` | Import `CATEGORIES`, add filter tabs, pass category to `load` |
| `frontend/src/pages/Admin.jsx` | Import `CATEGORIES`, add category to `toEdits` and card select |

---

## Task 1: Database schema + migration

**Files:**
- Modify: `backend/database.py`

- [ ] **Step 1: Add `category` column to `CREATE_GIFS_TABLE`**

In `database.py`, add `category TEXT NOT NULL DEFAULT 'Other'` to the `CREATE_GIFS_TABLE` string, after `source_end REAL NOT NULL`:

```python
CREATE_GIFS_TABLE = """
CREATE TABLE IF NOT EXISTS gifs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT NOT NULL,
    submitter_name TEXT NOT NULL,
    submitter_email TEXT,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_start REAL NOT NULL,
    source_end REAL NOT NULL,
    category TEXT NOT NULL DEFAULT 'Other'
)
"""
```

- [ ] **Step 2: Add migration to `init_db`**

Update `init_db` to migrate existing databases. Add the `ALTER TABLE` block between `conn.commit()` and `conn.close()`:

```python
def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_GIFS_TABLE)
    conn.commit()
    try:
        conn.execute("ALTER TABLE gifs ADD COLUMN category TEXT NOT NULL DEFAULT 'Other'")
        conn.commit()
    except Exception:
        pass  # Column already exists
    conn.close()
```

- [ ] **Step 3: Run existing tests to confirm nothing is broken**

```bash
cd backend && .venv/bin/pytest tests/ -v
```

Expected: all tests pass (migration is a no-op on test DBs since they are freshly created each test).

- [ ] **Step 4: Commit**

```bash
git add backend/database.py
git commit -m "feat: add category column to gifs table with migration"
```

---

## Task 2: Backend models + submit route

**Files:**
- Modify: `backend/models.py`
- Modify: `backend/routes/submit.py`
- Test: `backend/tests/test_routes_submit.py`

- [ ] **Step 1: Write failing tests**

In `test_routes_submit.py`, add the two new tests:

```python
def test_submit_rejects_invalid_category(client, done_job):
    resp = client.post("/api/submit", json={
        "job_id": done_job,
        "title": "T", "tags": ["t"], "submitter_name": "R",
        "category": "Invalid",
    })
    assert resp.status_code == 422

def test_submit_accepts_valid_category(client, done_job):
    resp = client.post("/api/submit", json={
        "job_id": done_job,
        "title": "T", "tags": ["t"], "submitter_name": "R",
        "category": "Tamil",
    })
    assert resp.status_code == 201
```

Also add `"category": "Tamil"` to every existing submit payload in the file. The four affected tests are `test_submit_returns_gif_id`, `test_submit_moves_file_to_pending`, `test_submit_returns_409_on_double_submit`, and `test_submit_returns_400_if_job_not_done` (the last one can omit category since it fails before validation).

Updated payloads:
- `test_submit_returns_gif_id`: add `"category": "Tamil"`
- `test_submit_moves_file_to_pending`: add `"category": "Tamil"`
- `test_submit_returns_409_on_double_submit`: add `"category": "Tamil"` to `payload`
- `test_submit_returns_400_if_job_not_done`: add `"category": "Tamil"` (will still get 400 — job not done check runs before model validation)

- [ ] **Step 2: Run new tests to confirm they fail**

```bash
cd backend && .venv/bin/pytest tests/test_routes_submit.py::test_submit_rejects_invalid_category tests/test_routes_submit.py::test_submit_accepts_valid_category -v
```

Expected: both FAIL (category field not yet in model)

- [ ] **Step 3: Update `models.py`**

Add `CATEGORIES` constant and update `SubmitRequest`. Also add `field_validator` to the pydantic import:

```python
from pydantic import BaseModel, field_validator

CATEGORIES = ["Tamil", "English", "Other"]
```

Add to `SubmitRequest` (after `submitter_email`):

```python
category: str

@field_validator("category")
@classmethod
def category_must_be_valid(cls, v):
    if v not in CATEGORIES:
        raise ValueError(f"category must be one of {CATEGORIES}")
    return v
```

Add `category: str` to `GifSummary` (after `created_at`).

Add `category: str` to `AdminGifItem` (after `created_at`).

Add `category: str | None = None` to `ApproveRequest` (after `description`).

- [ ] **Step 4: Update `routes/submit.py` INSERT**

Replace the existing `conn.execute("""INSERT INTO gifs...""")` call with:

```python
conn.execute(
    """INSERT INTO gifs
       (id, title, description, tags, submitter_name, submitter_email,
        file_path, status, created_at, source_url, source_start, source_end, category)
       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (
        gif_id, req.title, req.description, tags_str,
        req.submitter_name, req.submitter_email,
        str(dst), "pending", now,
        job["source_url"], job["source_start"], job["source_end"],
        req.category,
    )
)
```

- [ ] **Step 5: Run full submit test suite**

```bash
cd backend && .venv/bin/pytest tests/test_routes_submit.py -v
```

Expected: all submit tests pass including the two new ones.

- [ ] **Step 6: Run full test suite**

```bash
cd backend && .venv/bin/pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/models.py backend/routes/submit.py backend/tests/test_routes_submit.py
git commit -m "feat: category field in SubmitRequest with validation"
```

---

## Task 3: GIF retrieval routes — return and filter by category

**Files:**
- Modify: `backend/routes/gifs.py`
- Modify: `backend/routes/admin.py`
- Test: `backend/tests/test_routes_gifs.py`
- Test: `backend/tests/test_routes_admin.py`

- [ ] **Step 1: Write failing tests**

In `test_routes_gifs.py`, update the `insert_gif` helper to accept `category` (default `"Tamil"` so existing calls are unaffected):

```python
def insert_gif(db_path, status="approved", title="Test GIF", tags="funny,test", category="Tamil"):
    gid = str(uuid.uuid4())
    conn = get_conn(db_path)
    conn.execute(
        """INSERT INTO gifs
           (id, title, description, tags, submitter_name, file_path, status,
            created_at, source_url, source_start, source_end, category)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (gid, title, "desc", tags, "Ravi",
         f"storage/gifs/{gid}.gif", status,
         datetime.now(timezone.utc).isoformat(),
         "https://youtube.com/watch?v=abc", 0.0, 5.0, category)
    )
    conn.commit()
    conn.close()
    return gid
```

Add the new test at the bottom:

```python
def test_search_filters_by_category(client):
    db_path = os.environ["DB_PATH"]
    insert_gif(db_path, title="Tamil GIF", category="Tamil")
    insert_gif(db_path, title="English GIF", category="English")
    resp = client.get("/api/gifs?category=Tamil")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["results"][0]["title"] == "Tamil GIF"
    assert data["results"][0]["category"] == "Tamil"
```

In `test_routes_admin.py`, add:

```python
def test_approve_updates_category(client):
    db_path = os.environ["DB_PATH"]
    storage_dir = os.environ["STORAGE_DIR"]
    gid = insert_pending_gif(db_path, storage_dir)
    cookies = login(client)
    resp = client.post(
        f"/api/admin/approve/{gid}",
        json={"category": "Tamil"},
        cookies=cookies,
    )
    assert resp.status_code == 200
    conn = get_conn(db_path)
    row = conn.execute("SELECT * FROM gifs WHERE id=?", (gid,)).fetchone()
    conn.close()
    assert row["category"] == "Tamil"
    assert row["status"] == "approved"
```

- [ ] **Step 2: Run new tests to confirm they fail**

```bash
cd backend && .venv/bin/pytest tests/test_routes_gifs.py::test_search_filters_by_category tests/test_routes_admin.py::test_approve_updates_category -v
```

Expected: both FAIL

- [ ] **Step 3: Update `routes/gifs.py`**

Update `row_to_summary` to include `category`:

```python
def row_to_summary(row, storage_dir: str) -> GifSummary:
    return GifSummary(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        tags=[t.strip() for t in row["tags"].split(",") if t.strip()],
        gif_url=f"/static/gifs/{row['id']}.gif",
        created_at=row["created_at"],
        category=row["category"],
    )
```

Update `get_gif` to add `category=row["category"]` to the `GifDetail(...)` constructor call.

Replace `list_gifs` with the version that supports `category` filtering:

```python
@router.get("/api/gifs", response_model=GifListResponse)
async def list_gifs(request: Request, q: str = "", category: str = Query(default=""), limit: int = 100, offset: int = 0):
    limit = min(limit, 100)
    settings = request.app.state.settings
    conn = get_conn(settings.db_path)
    try:
        cat_clause = " AND category=?" if category else ""
        cat_param = (category,) if category else ()
        if q:
            pattern = f"%{q}%"
            rows = conn.execute(
                f"""SELECT * FROM gifs
                    WHERE status='approved'
                    AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                    {cat_clause}
                    ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (pattern, pattern, pattern, *cat_param, limit, offset)
            ).fetchall()
            total = conn.execute(
                f"""SELECT COUNT(*) FROM gifs
                    WHERE status='approved'
                    AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                    {cat_clause}""",
                (pattern, pattern, pattern, *cat_param)
            ).fetchone()[0]
        else:
            rows = conn.execute(
                f"SELECT * FROM gifs WHERE status='approved'{cat_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (*cat_param, limit, offset)
            ).fetchall()
            total = conn.execute(
                f"SELECT COUNT(*) FROM gifs WHERE status='approved'{cat_clause}",
                cat_param
            ).fetchone()[0]
    finally:
        conn.close()

    return GifListResponse(
        results=[row_to_summary(r, settings.storage_dir) for r in rows],
        total=total,
        offset=offset,
    )
```

Also add `Query` to the fastapi import: `from fastapi import APIRouter, HTTPException, Query, Request`

- [ ] **Step 4: Update `routes/admin.py` partial-update block**

In the `approve_gif` function, inside the `updates = {}` block (added in the previous plan), add after the `description` check:

```python
if req.category is not None:
    updates["category"] = req.category
```

- [ ] **Step 5: Run all new tests**

```bash
cd backend && .venv/bin/pytest tests/test_routes_gifs.py tests/test_routes_admin.py -v
```

Expected: all pass.

- [ ] **Step 6: Run full test suite**

```bash
cd backend && .venv/bin/pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/routes/gifs.py backend/routes/admin.py backend/tests/test_routes_gifs.py backend/tests/test_routes_admin.py
git commit -m "feat: category filter in GET /api/gifs, category in admin approve"
```

---

## Task 4: Frontend — constants, api.js, MetadataForm

**Files:**
- Create: `frontend/src/constants.js`
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/components/MetadataForm.jsx`

- [ ] **Step 1: Create `frontend/src/constants.js`**

```js
export const CATEGORIES = ["Tamil", "English", "Other"]
```

- [ ] **Step 2: Update `searchGifs` in `api.js`**

Replace the existing `searchGifs` function:

```js
export async function searchGifs(q = '', offset = 0, category = '') {
  const params = new URLSearchParams({ offset })
  if (q) params.set('q', q)
  if (category) params.set('category', category)
  const res = await fetch(`${BASE}/api/gifs?${params}`)
  if (!res.ok) throw new Error('Search failed')
  return res.json()
}
```

- [ ] **Step 3: Extract styles to module level in `MetadataForm.jsx`**

Add two module-level constants before the `MetadataForm` component:

```js
const fieldStyle = {
  width: '100%', padding: '10px 12px', borderRadius: 8,
  border: '2px solid #e8c97a', fontSize: '0.95rem',
  outline: 'none', background: '#fffdf5', resize: 'vertical',
  boxSizing: 'border-box',
}

const labelStyle = {
  display: 'block', marginBottom: 4, fontSize: '0.85rem',
  fontWeight: 600, color: '#5a3a10',
}
```

In the `Field` function, replace the local `const style = {...}` with `fieldStyle`, and replace the inline label style object with `labelStyle`.

- [ ] **Step 4: Add `categories` prop and `category` field to `MetadataForm`**

Add `categories` to the `MetadataForm` function signature: `export default function MetadataForm({ onSubmit, loading, categories }) {`

Add `category: ''` to the initial form state:

```js
const [form, setForm] = useState({
  title: '', tags: '', submitter_name: '', description: '',
  submitter_email: '', category: ''
})
```

Add the category `<select>` after the tags `<Field>` and before the description `<Field>`:

```jsx
<div>
  <label style={labelStyle}>Category *</label>
  <select
    value={form.category}
    onChange={e => set('category', e.target.value)}
    required
    style={{ ...fieldStyle, cursor: 'pointer', resize: 'none' }}
  >
    <option value="" disabled>Select a category</option>
    {categories.map(c => <option key={c} value={c}>{c}</option>)}
  </select>
</div>
```

- [ ] **Step 5: Build to verify**

```bash
cd frontend && npm run build
```

Expected: build passes with no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/constants.js frontend/src/api.js frontend/src/components/MetadataForm.jsx
git commit -m "feat: CATEGORIES constant, searchGifs category param, category select in MetadataForm"
```

---

## Task 5: Frontend — Make, Browse, Admin pages

**Files:**
- Modify: `frontend/src/pages/Make.jsx`
- Modify: `frontend/src/pages/Browse.jsx`
- Modify: `frontend/src/pages/Admin.jsx`

- [ ] **Step 1: Update `Make.jsx`**

Add import at the top: `import { CATEGORIES } from '../constants.js'`

Pass `categories` to `MetadataForm`:

```jsx
<MetadataForm
  onSubmit={handleSubmit}
  loading={submitLoading}
  categories={CATEGORIES}
/>
```

`category` flows automatically through `formData` since `MetadataForm` already includes it in its state and `handleSubmit` spreads `formData`.

- [ ] **Step 2: Update `Browse.jsx`**

Add imports: `import { CATEGORIES } from '../constants.js'`

Add `category` state after existing state declarations:
```js
const [category, setCategory] = useState('')
```

Update `load` callback to accept `cat` parameter:
```js
const load = useCallback(async (q, cat = '') => {
  setLoading(true)
  setError(null)
  try {
    const data = await searchGifs(q, 0, cat)
    setGifs(data.results)
    setTotal(data.total)
  } catch (e) {
    setError('Failed to load GIFs')
  } finally {
    setLoading(false)
  }
}, [])
```

Update `useEffect`:
```js
useEffect(() => { load('', '') }, [load])
```

Update `handleSearch` and `handleTagClick`:
```js
const handleSearch = (e) => {
  e.preventDefault()
  load(query, category)
}

const handleTagClick = (tag) => {
  setQuery(tag)
  load(tag, category)
}
```

Add filter tabs just before the search `<form>`:
```jsx
<div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
  {['All', ...CATEGORIES].map(c => {
    const val = c === 'All' ? '' : c
    const active = category === val
    return (
      <button
        key={c}
        onClick={() => { setCategory(val); load(query, val) }}
        style={{
          background: active ? '#d4880a' : '#f5e6c0',
          color: active ? '#fff' : '#7a4f1a',
          border: 'none', borderRadius: 20,
          padding: '6px 16px', fontWeight: 600,
          cursor: 'pointer', fontSize: '0.9rem',
        }}
      >
        {c}
      </button>
    )
  })}
</div>
```

- [ ] **Step 3: Update `Admin.jsx`**

Add import: `import { CATEGORIES } from '../constants.js'`

Update `toEdits` to include category:
```js
const toEdits = (results) =>
  Object.fromEntries(results.map(g => [g.id, {
    title: g.title,
    tags: (g.tags ?? []).join(', '),
    description: g.description ?? '',
    category: g.category ?? 'Other',
  }]))
```

Add category `<select>` to each card's editable fields section (after the description textarea):
```jsx
<select
  value={edits[gif.id]?.category ?? 'Other'}
  onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], category: e.target.value } }))}
  style={inlineInputStyle}
>
  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
</select>
```

Update `handleApprove` to include category in the fields object:
```js
const handleApprove = async (id) => {
  setActionInProgress(id)
  try {
    const { title, tags, description, category } = edits[id] ?? {}
    await approveGif(id, {
      title: title?.trim() || undefined,
      tags: tags ? tags.split(',').map(t => t.trim()).filter(Boolean) : undefined,
      description: description?.trim() || undefined,
      category: category || undefined,
    })
    setQueue(q => q.filter(g => g.id !== id))
  } catch (e) {
    alert('Failed to approve — ' + e.message)
  } finally {
    setActionInProgress(null)
  }
}
```

- [ ] **Step 4: Build to verify**

```bash
cd frontend && npm run build
```

Expected: build passes with no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Make.jsx frontend/src/pages/Browse.jsx frontend/src/pages/Admin.jsx
git commit -m "feat: category filter tabs on Browse, category select on Make and Admin"
```
