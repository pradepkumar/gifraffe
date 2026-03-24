# Category Field — Design Spec

**Date:** 2026-03-24
**Status:** Approved

## Overview

Add a required `category` field to GIFs. Users select a category when submitting on the Make page. The Browse page gets filter tabs (All | Tamil | English | Other). Admins can edit the category in the approval queue.

## Dependency

**This spec requires the admin-edit-before-approve spec to be implemented first.** The category changes to `ApproveRequest` and `Admin.jsx` build on top of that spec's changes. Do not implement this spec before that one is complete.

## Category List

Defined in `frontend/src/constants.js` (new file) as the single source of truth for the frontend:

```js
export const CATEGORIES = ["Tamil", "English", "Other"]
```

All three frontend files (`Make.jsx`, `Browse.jsx`, `Admin.jsx`) import from this file:

```js
import { CATEGORIES } from '../constants.js'
```

On the backend, defined as a constant in `models.py`:

```python
CATEGORIES = ["Tamil", "English", "Other"]
```

## Database

### Schema change

Add `category` column to the `gifs` table. Update `CREATE_GIFS_TABLE` in `database.py` to include:

```sql
category TEXT NOT NULL DEFAULT 'Other'
```

The full updated `CREATE_GIFS_TABLE` string should include this column.

### Migration for existing databases

The existing `init_db` function opens a `sqlite3.connect(db_path)` connection, executes `CREATE TABLE IF NOT EXISTS`, commits, and closes. Add the migration **between** the `conn.commit()` and `conn.close()` calls:

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

This is safe to run on both fresh and existing databases. On a fresh DB the column is already in `CREATE_GIFS_TABLE` so the `ALTER TABLE` raises and is swallowed.

## Backend

### `models.py`

Add `CATEGORIES` constant at the top. Update models:

**`SubmitRequest`** — add required `category` field with validation:
```python
category: str

@field_validator("category")
@classmethod
def category_must_be_valid(cls, v):
    if v not in CATEGORIES:
        raise ValueError(f"category must be one of {CATEGORIES}")
    return v
```

Also add the `field_validator` import: `from pydantic import BaseModel, field_validator`

**`GifSummary`** — add `category: str`

**`GifDetail`** inherits from `GifSummary` — gets `category` automatically. No change needed to the class definition, but the `get_gif` route manually constructs `GifDetail(...)` with explicit keyword arguments and must be updated (see routes section below).

**`AdminGifItem`** — add `category: str`

**`ApproveRequest`** (added by admin-edit-before-approve spec) — add `category: str | None = None`. No validation — admin-only endpoint.

### `routes/submit.py`

Add `category` to the INSERT statement. Updated INSERT:

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

### `routes/gifs.py`

**`row_to_summary`** — add `category=row["category"]`:
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

**`get_gif`** — add `category=row["category"]` to the `GifDetail(...)` constructor call.

**`list_gifs`** — add optional `category: str = Query(default="")` parameter. The `category` filter applies to both branches (with-`q` and without-`q`) and to both the data query and the count query — four places total. Add `AND category=?` and the category value to each:

```python
@router.get("/api/gifs", response_model=GifListResponse)
async def list_gifs(request: Request, q: str = "", category: str = Query(default=""), limit: int = 100, offset: int = 0):
    limit = min(limit, 100)
    settings = request.app.state.settings
    conn = get_conn(settings.db_path)
    try:
        if q:
            pattern = f"%{q}%"
            cat_clause = " AND category=?" if category else ""
            cat_param = (category,) if category else ()
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
            cat_clause = " AND category=?" if category else ""
            cat_param = (category,) if category else ()
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
    ...
```

### `routes/admin.py`

In the partial-update block (from admin-edit-before-approve spec), add:

```python
if req.category is not None:
    updates["category"] = req.category
```

No validation — admin-only. If an invalid value is sent manually it will simply be stored; the UI only offers valid options.

## Frontend

### `frontend/src/constants.js` (new file)

```js
export const CATEGORIES = ["Tamil", "English", "Other"]
```

### `api.js` — `searchGifs`

Add `category` parameter:

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

### `components/MetadataForm.jsx`

Extract both style objects from the `Field` function to module-level constants. The `Field` function currently has a local `const style = {...}` for inputs and an inline object literal for labels. Extract both:

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

Update `Field` to use `fieldStyle` instead of its local `const style`, and `labelStyle` instead of its inline label style object.

Add `categories` prop to `MetadataForm`. Add `category: ''` to the initial form state. Render a required `<select>` for category, placed after the tags field and before the description field:

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

Both `fieldStyle` and `labelStyle` are defined at module level as described above.

### `pages/Make.jsx`

Import `CATEGORIES` from `../constants.js`. Pass to `MetadataForm`:

```jsx
<MetadataForm
  onSubmit={handleSubmit}
  loading={submitLoading}
  categories={CATEGORIES}
/>
```

`category` is already in `formData` (via `MetadataForm`'s state) and is spread into `submitGif({job_id: jobId, ...formData, tags: ...})` automatically. No other change needed.

### `pages/Browse.jsx`

Import `CATEGORIES` from `../constants.js`.

Add `category` state:
```js
const [category, setCategory] = useState('')
```

Update `load` signature and `searchGifs` call:
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

Update `useEffect` to pass category:
```js
useEffect(() => { load('', '') }, [load])
```

Update `handleSearch` and `handleTagClick` to pass current category:
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

Render filter tabs above the search form:
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

### `pages/Admin.jsx`

Import `CATEGORIES` from `../constants.js`.

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

Add category `<select>` to each card's editable fields:
```jsx
<select
  value={edits[gif.id]?.category ?? 'Other'}
  onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], category: e.target.value } }))}
  style={inlineInputStyle}
>
  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
</select>
```

Where `inlineInputStyle` is the existing inline input style constant defined in `Admin.jsx` by the admin-edit-before-approve spec.

Update `handleApprove` to include category (consistent with the `|| undefined` pattern for other fields):
```js
category: edits[id]?.category || undefined,
```

## Testing

### Existing tests that need updating

**`backend/tests/test_routes_submit.py`** — all existing submit test payloads omit `category`. Since `category` is now required, all will return 422. Add `"category": "Tamil"` (or any valid value) to every `POST /api/submit` payload in that file.

**`backend/tests/test_routes_gifs.py`** — update `insert_gif` helper to accept and store a `category` parameter (default `"Tamil"` for backward compatibility with existing calls). Add `category` to the INSERT column list and values tuple. Existing test calls that don't pass `category` will use the default.

### New tests

**`test_routes_submit.py`** — add:
- `test_submit_rejects_invalid_category` — POST with `category="Invalid"`, assert 422
- `test_submit_accepts_valid_category` — POST with `category="Tamil"`, assert 201. Follow existing test pattern for building a valid submit payload (completed job in job_store, temp GIF file).

**`test_routes_gifs.py`** — add:
- `test_search_filters_by_category` — insert two approved GIFs with different categories (e.g. `"Tamil"` and `"English"`), call `GET /api/gifs?category=Tamil`, assert only the Tamil GIF is returned and `total=1`.

**`test_routes_admin.py`** — add:
- `test_approve_updates_category` — insert pending GIF (default category `'Other'`), approve with body `{"category": "Tamil"}`, assert DB has `category="Tamil"` and `status="approved"`.
