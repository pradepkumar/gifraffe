# Gifraffe — Design Spec
**Date:** 2026-03-24

## Overview

Gifraffe is a GIF finder and maker website. Users generate GIFs from any YouTube video by providing a URL and a start and end time, then optionally submit them to a curated, searchable library. The site is mobile-first, lightweight, and giraffe-themed (warm amber/golden savanna palette with giraffe spot accents).

Primary sharing targets: WhatsApp and Telegram.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                React Frontend (Vite)             │
│  / (search)  |  /make  |  /admin                │
└──────────────────────┬──────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼──────────────────────────┐
│              FastAPI Backend                     │
│  POST /api/generate           → create GIF job   │
│  GET  /api/jobs/{id}          → poll job status  │
│  POST /api/submit             → save pending GIF │
│  GET  /api/gifs               → search approved  │
│  GET  /api/gifs/{id}          → single GIF detail│
│  POST /api/admin/login        → set session      │
│  GET  /api/admin/queue        → list pending     │
│  GET  /api/admin/pending/{id} → serve pending GIF│
│  POST /api/admin/approve/{id}                    │
│  POST /api/admin/reject/{id}                     │
│  GET  /static/gifs/{id}.gif   → serve approved  │
│  GET  /static/temp/{id}.gif   → serve temp files │
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
    ┌─────▼──────┐          ┌───────▼──────┐
    │  SQLite DB │          │  Local Files │
    │ (metadata) │          │  (GIF files) │
    └────────────┘          └──────────────┘
```

**Tech stack:**
- Backend: Python + FastAPI
- Frontend: React + Vite
- Database: SQLite
- File storage: Local filesystem (approved GIFs served as FastAPI static files; pending GIFs served through an authenticated endpoint)
- Video processing: yt-dlp (YouTube download) + FFmpeg (GIF conversion)
- Session signing: `itsdangerous` (TimestampSigner)

---

## Pages

### `/` — Browse & Search
- Gifraffe logo/wordmark header with nav links (Browse | Make a GIF)
- Full-width search bar
- GIF grid — cards showing the GIF, title, and tags as chips
- Clicking a tag runs a tag-filtered search
- Clicking a GIF shows full-size preview with all metadata, download button, and Web Share button
- Empty search shows all approved GIFs (newest first, capped at 100 results)

### `/make` — GIF Maker
- YouTube URL input
- Start time / End time inputs (MM:SS or seconds format)
- "Generate GIF" button
- Progress indicator with steps: `Downloading → Extracting → Converting → Done`
- On success: GIF preview + actions:
  - **Download GIF** — downloads the file directly (reliable on all mobile browsers)
  - **Share** — uses the Web Share API (native share sheet on mobile) with fallback to download
  - **Submit to Gifraffe** — opens metadata form inline (disabled if temp file has expired, i.e. > 1 hour since generation)
- If the user tries to submit after the temp file has expired, show: "This GIF has expired — generate it again to submit."
- Metadata form fields:
  - Title* (required)
  - Tags* (required, comma-separated)
  - Your Name* (required)
  - Description (optional — dialogue, scene context, etc.)
  - Email (optional)

> **Note on sharing:** The Clipboard API for binary GIF data is unreliable on mobile browsers (not supported in Firefox, permission-gated elsewhere). We use a **Download** button as the primary action — users download the GIF and share it from their photo library. The Web Share API (`navigator.share` with a File object) is used as an enhanced option where supported (most modern Android/iOS browsers). No clipboard write is attempted.

### `/admin` — Admin Approval Queue
- Route: `/admin`
- Password prompt on first visit; session cookie valid 24 hours
- Shows pending GIFs with full preview and all metadata
- Approve / Reject buttons per GIF
- Pending GIF images are served via authenticated endpoint `/api/admin/pending/{id}` — not as static files
- Approving moves file from `storage/pending/` to `storage/gifs/`, updates status to `approved` in DB
- Rejecting deletes the file from `storage/pending/` and deletes the DB row entirely (hard delete, no audit record)

---

## Data Model

### SQLite — `gifs` table

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | TEXT (UUID) | yes | primary key |
| `title` | TEXT | yes | |
| `description` | TEXT | no | dialogue, scene context, etc. |
| `tags` | TEXT | yes | comma-separated |
| `submitter_name` | TEXT | yes | |
| `submitter_email` | TEXT | no | |
| `file_path` | TEXT | yes | relative path under `storage/` |
| `status` | TEXT | yes | `pending` or `approved` (rejected rows are hard-deleted) |
| `created_at` | DATETIME | yes | |
| `source_url` | TEXT | yes | original YouTube URL |
| `source_start` | REAL | yes | start time in seconds |
| `source_end` | REAL | yes | end time in seconds |

### In-Memory Jobs (Python dict)

Jobs track async GIF generation state. Stored in-memory — job state is lost on server restart, which is acceptable since jobs complete within 60 seconds.

| Field | Type | Notes |
|---|---|---|
| `id` | TEXT (UUID) | job ID |
| `status` | TEXT | `pending` / `processing` / `done` / `failed` |
| `step` | TEXT | current progress step label |
| `file_path` | TEXT | set on completion: `storage/temp/{job_id}.gif` |
| `error` | TEXT | set on failure |
| `source_url` | TEXT | original YouTube URL (used by submit endpoint) |
| `source_start` | REAL | start time in seconds (used by submit endpoint) |
| `source_end` | REAL | end time in seconds (used by submit endpoint) |
| `created_at` | DATETIME | used for cleanup |

### File Storage Layout

```
storage/
  temp/       ← generated GIFs awaiting submission or download
    {job_id}.gif
  pending/    ← submitted GIFs awaiting admin approval
    {gif_id}.gif
  gifs/       ← approved GIFs served publicly as static files
    {gif_id}.gif
```

- `storage/gifs/` is mounted as a FastAPI `StaticFiles` route at `/static/gifs/`
- `storage/temp/` is mounted as a FastAPI `StaticFiles` route at `/static/temp/` (temp files are short-lived and non-sensitive)
- `storage/pending/` is **not** mounted as static files — served only through the authenticated `/api/admin/pending/{id}` endpoint

### Cleanup Policy

A background task runs on startup and every hour:
- Deletes `storage/temp/` files older than 1 hour and removes their in-memory job entries
- Deletes `storage/pending/` files and DB rows for pending GIFs older than 30 days (silent, no notification to submitter)

---

## API Contracts

### `POST /api/generate`
**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "start": 12.5,
  "end": 20.0
}
```
**Response (202 Accepted):**
```json
{ "job_id": "uuid" }
```
**Errors:** 400 if URL is not a YouTube URL, `end - start > 10`, or `start >= end`.

---

### `GET /api/jobs/{job_id}`
**Response while processing:**
```json
{ "status": "processing", "step": "Converting to GIF", "gif_url": null, "error": null }
```
**Response when done:**
```json
{ "status": "done", "step": "Done", "gif_url": "/static/temp/{job_id}.gif", "error": null }
```
**Response when failed:**
```json
{ "status": "failed", "step": null, "gif_url": null, "error": "Video unavailable or private" }
```
**Error:** 404 if job_id not found (server restarted or job expired).

---

### `POST /api/submit`
Submits a generated GIF by job ID. Backend resolves `source_url`, `source_start`, and `source_end` from the in-memory job entry. Moves file from `storage/temp/{job_id}.gif` → `storage/pending/{gif_id}.gif`. Creates a DB row with `status=pending`.

**Request:**
```json
{
  "job_id": "uuid",
  "title": "Vijay entry scene",
  "tags": "vijay,entry,comedy",
  "submitter_name": "Ravi",
  "description": "Naa poguren lyrics scene",
  "submitter_email": "ravi@example.com"
}
```
**Response (201 Created):**
```json
{ "gif_id": "uuid", "message": "Submitted for review" }
```
**Errors:**
- 404 if `job_id` not found in memory (server restarted or expired)
- 400 if job status is not `done`
- 410 if temp file no longer exists (expired/cleaned up)
- 409 if `job_id` already submitted (each job_id can only be submitted once)
- 400 if required fields missing

---

### `GET /api/gifs`
**Query params:**
- `q` — search string (optional)
- `limit` — max results (default: 100, max: 100)
- `offset` — for pagination (default: 0)

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "...",
      "description": "...",
      "tags": ["vijay", "comedy"],
      "gif_url": "/static/gifs/{id}.gif",
      "created_at": "2026-03-24T10:00:00Z"
    }
  ],
  "total": 42,
  "offset": 0
}
```
Search is case-insensitive `LIKE '%term%'` across `title`, `description`, and `tags`. Only `approved` rows returned.

---

### `GET /api/gifs/{gif_id}`
Returns a single approved GIF with full metadata.

**Response:**
```json
{
  "id": "uuid",
  "title": "...",
  "description": "...",
  "tags": ["vijay", "comedy"],
  "submitter_name": "Ravi",
  "gif_url": "/static/gifs/{id}.gif",
  "source_url": "https://www.youtube.com/watch?v=...",
  "source_start": 12.5,
  "source_end": 20.0,
  "created_at": "2026-03-24T10:00:00Z"
}
```
**Error:** 404 if not found or not approved.

---

### `POST /api/admin/login`
**Request:** `{ "password": "..." }`
**Response:** Sets a signed `session` cookie (HttpOnly, SameSite=Strict, signed with `itsdangerous` using `SESSION_SECRET`). Returns 200 on success, 401 on wrong password.

---

### `GET /api/admin/queue`
Returns all `pending` GIFs. Requires valid session cookie (401 otherwise).

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "...",
      "description": "...",
      "tags": ["vijay", "comedy"],
      "submitter_name": "Ravi",
      "submitter_email": "ravi@example.com",
      "gif_url": "/api/admin/pending/{id}",
      "source_url": "...",
      "source_start": 12.5,
      "source_end": 20.0,
      "created_at": "..."
    }
  ]
}
```

---

### `GET /api/admin/pending/{gif_id}`
Serves the pending GIF file. Requires valid session cookie (401 otherwise). Reads from `storage/pending/{gif_id}.gif` and streams with `Content-Type: image/gif`.

**Error:** 404 if file not found.

---

### `POST /api/admin/approve/{gif_id}`
Moves `storage/pending/{gif_id}.gif` → `storage/gifs/{gif_id}.gif`. Updates `status` to `approved`. Requires session cookie.

**Response:** `{ "ok": true }`

---

### `POST /api/admin/reject/{gif_id}`
Deletes `storage/pending/{gif_id}.gif`. Deletes DB row (hard delete). Requires session cookie.

**Response:** `{ "ok": true }`

---

## GIF Generation

### Constraints
- **YouTube only** — URL must match `youtube.com/watch` or `youtu.be/` patterns
- **Max duration: 10 seconds** — enforced on both frontend and backend (`end - start > 10` → 400 error)
- **Max file size: 5MB** — if output exceeds this, job marked failed with message "GIF is too large — try a shorter clip"
- **Job timeout: 60 seconds** — job marked failed if processing exceeds this

### FFmpeg Settings
Optimized for small file size and messaging app compatibility:
- Resolution: max 480px wide, height scaled proportionally (`scale=480:-1`)
- Frame rate: 12fps
- Single-pass palette optimization using FFmpeg's `split` + `palettegen` + `paletteuse` filters (no intermediate palette file)
- These settings keep most 10-second clips under 5MB

### Progress Steps
1. Downloading
2. Extracting clip
3. Converting to GIF
4. Done

---

## Admin Security

- Route: `/admin` (fixed path)
- `ADMIN_PASSWORD_HASH` env variable stores a **bcrypt hash** of the admin password (never store plaintext)
  - Setup: `python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"`
  - Set the output as `ADMIN_PASSWORD_HASH` in your `.env` file
- `SESSION_SECRET` env variable: a random string used by `itsdangerous` to sign session cookies; minimum 32 characters
- If either env variable is missing at startup, the server refuses to start with a clear error message
- Session cookie: HttpOnly, SameSite=Strict, expires 24 hours

---

## Rate Limiting

Out of scope for v1. If abuse becomes an issue, add `slowapi` and limit `/api/generate` to 5 requests per IP per minute.

---

## Search

- Single search box, case-insensitive `LIKE '%term%'` across `title`, `description`, `tags`
- Only `approved` rows returned
- Results paginated: default 100 per page
- Tags are clickable on GIF cards — triggers tag search
- Sufficient for expected scale (hundreds to low thousands of GIFs)

---

## Error States

| Scenario | User-facing message |
|---|---|
| Invalid YouTube URL | "Please enter a valid YouTube URL" |
| Clip exceeds 10 seconds | "Maximum clip length is 10 seconds" |
| Video unavailable/private | "This video is unavailable or private" |
| Output exceeds 5MB | "GIF is too large — try a shorter clip" |
| Generation timeout | "Generation timed out — please try again" |
| Temp file expired (submit) | "This GIF has expired — generate it again to submit" |
| Already submitted | "This GIF has already been submitted" |
| Generic failure | "Something went wrong — please try again" (with retry button) |

---

## UI Theme

- **Name:** Gifraffe
- **Palette:** Warm amber/golden yellows, earthy browns, off-white backgrounds
- **Accents:** Giraffe spot pattern used decoratively
- **Logo:** Giraffe-themed wordmark in header
- **Style:** Clean, minimal, mobile-first
- **Typography:** Friendly but readable — suits a fun, casual GIF site
