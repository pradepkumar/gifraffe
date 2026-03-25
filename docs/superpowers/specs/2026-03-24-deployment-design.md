# Deployment Design Spec

**Date:** 2026-03-24
**Feature:** Production deployment of Gifraffe on Google Cloud Platform

## Overview

Deploy the Gifraffe app (FastAPI backend + React frontend) to a single GCP Compute Engine VM. The app runs as a systemd service behind Nginx, accessible over HTTP via a static public IP. No domain or HTTPS for now — can be added later with minimal changes.

## Infrastructure

| Property | Value |
|----------|-------|
| Provider | Google Cloud Platform |
| Service | Compute Engine |
| Machine type | `e2-medium` (2 vCPU, 4GB RAM) |
| OS | Ubuntu 24.04 LTS |
| Disk | 30GB SSD (boot disk) |
| Region | `us-central1` |
| External IP | Static (reserved, so it doesn't change on restart) |
| Firewall | Ports 22 (SSH) and 80 (HTTP) open. Port 443 closed (no domain/SSL yet) |

No HTTPS for now. The admin password will be sent in plaintext over HTTP — acceptable for an initial deployment without a domain. When a domain is added, Let's Encrypt provides free SSL in ~10 minutes.

## Directory Layout on VM

```
/opt/gifraffe/               — app root (git clone of GitHub repo)
/opt/gifraffe/backend/       — FastAPI app
/opt/gifraffe/backend/.env   — secrets (created manually on server, never committed)
/opt/gifraffe/backend/storage/
  gifs/                      — approved GIFs (permanent)
  pending/                   — submitted, awaiting approval
  temp/                      — in-progress generation (cleaned up hourly)
/opt/gifraffe/frontend/      — React source
/opt/gifraffe/backend/static_frontend/  — built frontend (served by FastAPI via Nginx)
```

## Application Setup

### Nginx (reverse proxy)

Nginx listens on port 80 and:
- Serves `/static/gifs/` and `/static/temp/` directly from disk (bypasses Python for GIF file serving)
- Forwards all other requests to uvicorn on `localhost:8000`

FastAPI's catch-all route serves the built frontend from `backend/static_frontend/`. Vite is already configured with `outDir: '../backend/static_frontend'` so `npm run build` outputs there automatically — no extra config needed. Nginx does not need a separate block for the frontend assets; uvicorn handles them.

### uvicorn (systemd service)

A systemd unit file (`/etc/systemd/system/gifraffe.service`) runs uvicorn:
- Starts automatically on boot
- Restarts automatically on crash
- Runs as a dedicated non-root `gifraffe` system user
- Loads environment from `/opt/gifraffe/backend/.env`

### Environment

The `.env` file is created once manually on the server:

```env
ADMIN_PASSWORD_HASH=<bcrypt hash>
SESSION_SECRET=<64-char hex secret>
DB_PATH=/opt/gifraffe/backend/gifraffe.db
STORAGE_DIR=/opt/gifraffe/backend/storage
```

### System Dependencies

Installed via apt on the VM:
- `python3`, `python3-venv`, `python3-pip`
- `ffmpeg`
- `nodejs`, `npm`
- `nginx`
- `fail2ban`

yt-dlp is installed as a Python package in the virtualenv (already in `requirements.txt`).

## Deployment Flow

Manual deploy process (no CI/CD pipeline for now):

```bash
cd /opt/gifraffe
git pull origin main
cd frontend && npm run build
sudo systemctl restart gifraffe
```

## Production Hardening

### Rate Limiting

IP-based rate limit on `POST /api/generate`: maximum 5 requests per IP per hour. Implemented in FastAPI middleware using an in-memory dict (no Redis required at this scale). Excess requests receive HTTP 429.

This prevents a single user from queueing many CPU-heavy GIF generation jobs.

### Fail2ban

Configured to ban IPs after 5 failed SSH login attempts within 10 minutes (ban duration: 1 hour). This uses fail2ban's built-in `sshd` jail and requires no custom log parsing.

The admin login endpoint (`/api/admin/login`) is protected by the FastAPI rate limiter instead (same in-memory dict used for `/api/generate`): maximum 10 attempts per IP per hour, returning HTTP 429 on excess. This avoids the need for fail2ban to parse application logs.

### UFW Firewall

Ubuntu's UFW configured as a second layer on top of GCP firewall rules:
- Allow port 22 (SSH)
- Allow port 80 (HTTP)
- Deny everything else

### Automatic Security Updates

`unattended-upgrades` enabled to automatically apply Ubuntu security patches.

### Backups

Daily cron job (runs at 2am UTC) copies stateful data to a GCP Cloud Storage bucket:
- `gifraffe.db` (SQLite database)
- `storage/gifs/` directory (approved GIFs)

Retention: 7 daily backups kept in the bucket. Storage cost is negligible (~$0.02/GB/month).

## Migration Path

When GCP credits are depleted, migrating to another provider (e.g. Hetzner €4.51/mo) involves:
1. Spin up a new VM on the new provider
2. Run the same setup steps
3. Restore the database and GIF files from the GCS backup bucket
4. Update DNS (or just use the new IP)

No GCP-specific dependencies in the app itself.

## What's Not Included (Future)

- HTTPS / SSL (requires a domain)
- CI/CD pipeline (manual `git pull` + restart for now)
- Horizontal scaling (single VM is sufficient for initial traffic)
- CDN for GIF delivery
