# Category Field — Design Spec

**Date:** 2026-03-24
**Status:** Approved

## Overview

Add a required `category` field to GIFs. Users select a category when submitting on the Make page. The Browse page gets filter tabs (All | Tamil | English | Other). Admins can edit the category in the approval queue.

## Category List

Defined as a constant in `models.py`:

```python
CATEGORIES = ["Tamil", "English", "Other"]
```

This is the single source of truth. No API endpoint needed. To add categories in future, update this list and redeploy.

## Database

### Schema change

Add `category` column to the `gifs` table in `database.py`:

```sql
category TEXT NOT NULL DEFAULT 'Other'
```

### Migration

The DB may already exist with existing rows. On startup, `init_db` should run the following after `CREATE TABLE IF NOT EXISTS`:

```python
try:
    conn.execute("ALTER TABLE gifs ADD COLUMN category TEXT NOT NULL DEFAULT 'Other'")
    conn.commit()
except Exception:
    pass  # Column already exists
```

This is safe to run on both fresh and existing databases.

## Backend

### `models.py`

Add `CATEGORIES` constant. Update affected models:

**`SubmitRequest`** — add required field with validation:
```python
category: str

@field_validator("category")
@classmethod
def category_must_be_valid(cls, v):
    if v not in CATEGORIES:
        raise ValueError(f"category must be one of {CATEGORIES}")
    return v
```

**`GifItem`** — add `category: str`

**`AdminGifItem`** — add `category: str`

**`ApproveRequest`** (from admin-edit-before-approve spec) — add `category: str | None = None`. No validation needed here (admin-only endpoint; trust the admin).

### `routes/submit.py`

Add `category` to the `INSERT INTO gifs` statement. The column order and values tuple must include the new field.

### `routes/gifs.py` — `GET /api/gifs`

Add optional `category` query parameter:

```python
category: str | None = Query(default=None)
```

If `category` is provided and non-empty, append `AND category=?` to the WHERE clause and add `category` to the query params tuple.

Return `category` in each `GifItem`.

### `routes/admin.py` — `approve_gif`

In the partial-update block (from admin-edit-before-approve spec), add:

```python
if req.category is not None:
    updates["category"] = req.category
```

No strip/join needed — category is a plain string value from `CATEGORIES`.

## Frontend

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

Add a `categories` prop (array of strings). Add a `category` field to the initial form state (default `''` so the user must actively choose):

```js
const [form, setForm] = useState({
  title: '', tags: '', submitter_name: '', description: '',
  submitter_email: '', category: ''
})
```

Render a `<select>` for category, required:

```jsx
<div>
  <label style={labelStyle}>Category *</label>
  <select
    value={form.category}
    onChange={e => set('category', e.target.value)}
    required
    style={{ ...fieldStyle, cursor: 'pointer' }}
  >
    <option value="" disabled>Select a category</option>
    {categories.map(c => <option key={c} value={c}>{c}</option>)}
  </select>
</div>
```

Where `fieldStyle` is the same style object used by `Field` inputs (border `#e8c97a`, background `#fffdf5`, etc.), with `boxSizing: 'border-box'`.

### `pages/Make.jsx`

Pass `categories` to `MetadataForm`:

```jsx
<MetadataForm
  onSubmit={handleSubmit}
  loading={submitLoading}
  categories={CATEGORIES}
/>
```

`CATEGORIES` is imported or defined as `["Tamil", "English", "Other"]` in `Make.jsx`. The `submitGif` payload already spreads `formData`, so `category` is included automatically.

### `pages/Browse.jsx`

Add `category` state (default `''` = All):

```js
const [category, setCategory] = useState('')
```

Pass category to `load` and `searchGifs`:

```js
const load = useCallback(async (q, cat) => {
  ...
  const data = await searchGifs(q, 0, cat)
  ...
}, [])
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

Update `handleSearch` to pass current category:
```js
const handleSearch = (e) => {
  e.preventDefault()
  load(query, category)
}
```

Update `handleTagClick` to pass current category:
```js
const handleTagClick = (tag) => {
  setQuery(tag)
  load(tag, category)
}
```

`CATEGORIES` imported or defined as `["Tamil", "English", "Other"]` in `Browse.jsx`.

### `pages/Admin.jsx`

Add category `<select>` to the inline editable fields in each queue card. Category reads from `edits[gif.id].category` (initialized from `gif.category` in `toEdits`).

Update `toEdits`:
```js
const toEdits = (results) =>
  Object.fromEntries(results.map(g => [g.id, {
    title: g.title,
    tags: (g.tags ?? []).join(', '),
    description: g.description ?? '',
    category: g.category ?? 'Other',
  }]))
```

Render a `<select>` per card (same amber styling as other inline inputs):
```jsx
<select
  value={edits[gif.id]?.category ?? 'Other'}
  onChange={e => setEdits(ed => ({ ...ed, [gif.id]: { ...ed[gif.id], category: e.target.value } }))}
  style={inlineInputStyle}
>
  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
</select>
```

Update `handleApprove` to include category:
```js
category: (edits[id]?.category) || undefined,
```

`CATEGORIES` defined as `["Tamil", "English", "Other"]` at the top of `Admin.jsx`.

## Testing

Add to `backend/tests/test_routes_admin.py`:

**`test_approve_updates_category`** — insert pending GIF (default category `'Other'`), approve with body `{"category": "Tamil"}`, assert DB has `category="Tamil"`.

Add to `backend/tests/test_routes_submit.py` (or whichever file tests submit):

**`test_submit_rejects_invalid_category`** — POST to `/api/submit` with `category="Invalid"`, assert 422.

**`test_submit_accepts_valid_category`** — POST with `category="Tamil"`, assert 200/202 (note: submit requires a pre-existing job file in temp storage — follow the pattern of existing submit tests).

Add to `backend/tests/test_routes_gifs.py`:

**`test_search_filters_by_category`** — insert two approved GIFs with different categories, call `GET /api/gifs?category=Tamil`, assert only the Tamil GIF is returned.
