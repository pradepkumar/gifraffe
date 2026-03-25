# Gifraffe

A GIF library app. Create GIFs from YouTube videos, browse and search the library, and manage submissions through an admin queue.

## Stack

- **Frontend:** React 18, Vite, React Router
- **Backend:** FastAPI, SQLite, yt-dlp, ffmpeg

## Features

- Create GIFs from YouTube clips (up to 10 seconds)
- Browse and search by title, tags, description, or category
- Submit GIFs for admin review
- Admin queue with approve/reject and inline metadata editing

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- ffmpeg (`brew install ffmpeg` / `apt install ffmpeg`)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
# Generate: python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
ADMIN_PASSWORD_HASH=

# Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
SESSION_SECRET=

DB_PATH=gifraffe.db
STORAGE_DIR=storage
```

```bash
uvicorn main:app --reload
```

### Frontend (dev)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Frontend (production build)

```bash
cd frontend
npm run build
```

The built files are served automatically by the FastAPI backend at `http://localhost:8000`.

## Admin

Navigate to `/admin` and log in with the password used to generate `ADMIN_PASSWORD_HASH`.
