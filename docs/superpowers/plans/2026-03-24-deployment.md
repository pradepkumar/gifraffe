# Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Gifraffe to a GCP e2-medium VM accessible via a public static IP over HTTP.

**Architecture:** A single Ubuntu 24.04 VM runs uvicorn (FastAPI) as a systemd service behind Nginx. The frontend is pre-built and served by FastAPI's catch-all route. GIF files are served directly by Nginx. Rate limiting is enforced in FastAPI using an in-memory store. Daily backups of the SQLite DB and approved GIFs are written to a GCS bucket.

**Tech Stack:** GCP Compute Engine, Ubuntu 24.04, Python 3.12, uvicorn, Nginx, systemd, fail2ban, UFW, gsutil

---

## Part A — Code Changes (local, committed to GitHub before server setup)

---

### Task 1: Add rate limiting to generate and admin login endpoints

**Files:**
- Create: `backend/rate_limiter.py`
- Create: `backend/tests/test_rate_limiter.py`
- Modify: `backend/routes/generate.py`
- Modify: `backend/routes/admin.py`

---

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_rate_limiter.py`:

```python
import datetime
import pytest
from fastapi import HTTPException
from rate_limiter import RateLimiter


def test_allows_requests_under_limit():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)


def test_blocks_on_limit_exceeded():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    assert exc_info.value.status_code == 429


def test_different_keys_are_independent():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    # Different IP should not be blocked
    limiter.check("key:5.6.7.8", max_requests=5, window_seconds=3600)


def test_expired_requests_do_not_count():
    limiter = RateLimiter()
    old_ts = datetime.datetime.now(datetime.timezone.utc).timestamp() - 3601
    limiter._requests["key:1.2.3.4"] = [old_ts] * 5
    # Should not be blocked — all 5 requests are outside the window
    limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)


def test_error_message_is_user_friendly():
    limiter = RateLimiter()
    for _ in range(5):
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("key:1.2.3.4", max_requests=5, window_seconds=3600)
    assert "try again" in exc_info.value.detail.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend
.venv/bin/pytest tests/test_rate_limiter.py -v
```

Expected: `ERROR` — `ModuleNotFoundError: No module named 'rate_limiter'`

- [ ] **Step 3: Create `backend/rate_limiter.py`**

```python
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= max_requests:
            raise HTTPException(429, detail="Too many requests — please try again later")
        self._requests[key].append(now)


def _get_ip(request: Request) -> str:
    """Return the real client IP, using X-Real-IP set by Nginx if present."""
    return request.headers.get("X-Real-IP") or request.client.host


rate_limiter = RateLimiter()


def limit_generate(request: Request) -> None:
    """5 GIF generation requests per IP per hour."""
    rate_limiter.check(f"generate:{_get_ip(request)}", max_requests=5, window_seconds=3600)


def limit_admin_login(request: Request) -> None:
    """10 admin login attempts per IP per hour."""
    rate_limiter.check(f"admin_login:{_get_ip(request)}", max_requests=10, window_seconds=3600)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend
.venv/bin/pytest tests/test_rate_limiter.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 5: Add rate limit to `/api/generate`**

In `backend/routes/generate.py`, update the import line and route decorator:

```python
# Change this import (add Depends):
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends

# Add this import after the existing imports:
from rate_limiter import limit_generate
```

Change the route decorator from:
```python
@router.post("/api/generate", status_code=202)
```
To:
```python
@router.post("/api/generate", status_code=202, dependencies=[Depends(limit_generate)])
```

- [ ] **Step 6: Add rate limit to `/api/admin/login`**

In `backend/routes/admin.py`, update the import line and route decorator:

```python
# Change this import (add Depends):
from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Request, Response

# Add this import after the existing imports:
from rate_limiter import limit_admin_login
```

Change the route decorator from:
```python
@router.post("/api/admin/login")
```
To:
```python
@router.post("/api/admin/login", dependencies=[Depends(limit_admin_login)])
```

- [ ] **Step 7: Run the full test suite to verify nothing is broken**

```bash
cd backend
.venv/bin/pytest tests/ -v
```

Expected: All tests pass (the previously failing `test_build_ffmpeg_command` test is a pre-existing issue unrelated to this change — it should still fail as before and is not a blocker)

- [ ] **Step 8: Commit and push**

```bash
git add backend/rate_limiter.py backend/tests/test_rate_limiter.py \
        backend/routes/generate.py backend/routes/admin.py
git commit -m "feat: add IP-based rate limiting to generate and admin login endpoints"
git push origin main
```

---

## Part B — Server Setup (run on local machine via gcloud CLI and SSH)

> **Prerequisites:** Install and authenticate the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install): `gcloud auth login && gcloud config set project YOUR_PROJECT_ID`

---

### Task 2: Provision the GCP VM

**Files:** None (GCP infrastructure only)

---

- [ ] **Step 1: Reserve a static external IP**

```bash
gcloud compute addresses create gifraffe-ip \
  --region=us-central1
```

Note the reserved IP address shown in the output — you'll need it throughout this plan. Call it `$VM_IP`.

```bash
# Verify
gcloud compute addresses describe gifraffe-ip --region=us-central1
```

Expected: `status: RESERVED` with an IP address listed.

- [ ] **Step 2: Create the VM**

```bash
gcloud compute instances create gifraffe \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2404-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-ssd \
  --address=gifraffe-ip \
  --tags=gifraffe-server
```

Expected: VM listed with status `RUNNING`.

- [ ] **Step 3: Create firewall rules**

```bash
# Allow HTTP
gcloud compute firewall-rules create gifraffe-allow-http \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:80 \
  --target-tags=gifraffe-server

# Allow SSH (if not already allowed by a default rule)
gcloud compute firewall-rules create gifraffe-allow-ssh \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --target-tags=gifraffe-server
```

- [ ] **Step 4: Verify SSH access**

```bash
gcloud compute ssh gifraffe --zone=us-central1-a
```

Expected: You land at an Ubuntu shell prompt. Type `exit` to leave.

---

### Task 3: Install system dependencies

> All commands in Tasks 3–8 run **inside the VM** via SSH:
> `gcloud compute ssh gifraffe --zone=us-central1-a`

---

- [ ] **Step 1: Update apt and install dependencies**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip ffmpeg nginx fail2ban ufw unattended-upgrades
```

- [ ] **Step 2: Install Node.js 20**

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

- [ ] **Step 3: Verify key dependencies**

```bash
ffmpeg -version | head -1
node --version
python3 --version
nginx -v
```

Expected: version strings printed for all four. No errors.

- [ ] **Step 4: Create the gifraffe system user**

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin gifraffe
```

---

### Task 4: Deploy the application

---

- [ ] **Step 1: Clone the repository**

```bash
sudo mkdir -p /opt/gifraffe
sudo chown $USER:$USER /opt/gifraffe
git clone https://github.com/pradepkumar/gifraffe.git /opt/gifraffe
```

- [ ] **Step 2: Set up Python virtualenv and install requirements**

```bash
cd /opt/gifraffe/backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 3: Build the frontend**

```bash
cd /opt/gifraffe/frontend
npm install
npm run build
```

Expected: Build completes, output in `/opt/gifraffe/backend/static_frontend/`.

- [ ] **Step 4: Create storage directories**

```bash
mkdir -p /opt/gifraffe/backend/storage/{gifs,pending,temp}
```

- [ ] **Step 5: Create the `.env` file**

```bash
# Generate a bcrypt hash for your admin password:
/opt/gifraffe/backend/.venv/bin/python3 -c \
  "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD_HERE', bcrypt.gensalt()).decode())"

# Generate a session secret:
python3 -c "import secrets; print(secrets.token_hex(32))"

# Write the .env file (replace the values):
cat > /opt/gifraffe/backend/.env << 'EOF'
ADMIN_PASSWORD_HASH=<paste bcrypt hash here>
SESSION_SECRET=<paste 64-char hex secret here>
DB_PATH=/opt/gifraffe/backend/gifraffe.db
STORAGE_DIR=/opt/gifraffe/backend/storage
EOF

chmod 600 /opt/gifraffe/backend/.env
```

- [ ] **Step 6: Set correct ownership**

```bash
sudo chown -R gifraffe:gifraffe /opt/gifraffe/backend/storage
sudo chown gifraffe:gifraffe /opt/gifraffe/backend/gifraffe.db 2>/dev/null || true
sudo chown gifraffe:gifraffe /opt/gifraffe/backend/.env
```

---

### Task 5: Configure the systemd service

**Files (created on VM):**
- Create: `/etc/systemd/system/gifraffe.service`

---

- [ ] **Step 1: Create the systemd unit file**

```bash
sudo tee /etc/systemd/system/gifraffe.service > /dev/null << 'EOF'
[Unit]
Description=Gifraffe FastAPI app
After=network.target

[Service]
Type=simple
User=gifraffe
WorkingDirectory=/opt/gifraffe/backend
EnvironmentFile=/opt/gifraffe/backend/.env
ExecStart=/opt/gifraffe/backend/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

- [ ] **Step 2: Enable and start the service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable gifraffe
sudo systemctl start gifraffe
```

- [ ] **Step 3: Verify it is running**

```bash
sudo systemctl status gifraffe
```

Expected: `Active: active (running)`. If it shows `failed`, check logs:

```bash
sudo journalctl -u gifraffe -n 50
```

- [ ] **Step 4: Verify the API responds locally**

```bash
curl http://127.0.0.1:8000/api/gifs
```

Expected: JSON response like `{"results": [], "total": 0}`.

---

### Task 6: Configure Nginx

**Files (created on VM):**
- Create: `/etc/nginx/sites-available/gifraffe`

---

- [ ] **Step 1: Write the Nginx config**

```bash
sudo tee /etc/nginx/sites-available/gifraffe > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    # Serve approved GIFs directly from disk
    location /static/gifs/ {
        alias /opt/gifraffe/backend/storage/gifs/;
    }

    # Serve temp GIFs directly from disk
    location /static/temp/ {
        alias /opt/gifraffe/backend/storage/temp/;
    }

    # Forward everything else to uvicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
EOF
```

- [ ] **Step 2: Enable the site and remove the default**

```bash
sudo ln -s /etc/nginx/sites-available/gifraffe /etc/nginx/sites-enabled/gifraffe
sudo rm -f /etc/nginx/sites-enabled/default
```

- [ ] **Step 3: Test the Nginx config**

```bash
sudo nginx -t
```

Expected: `syntax is ok` and `test is successful`.

- [ ] **Step 4: Reload Nginx**

```bash
sudo systemctl reload nginx
```

- [ ] **Step 5: Verify the app is accessible via the public IP**

From your **local machine** (not the VM):

```bash
curl http://$VM_IP/api/gifs
```

Expected: `{"results": [], "total": 0}`

Also open `http://$VM_IP` in a browser — the Gifraffe browse page should load.

---

### Task 7: Security hardening

---

- [ ] **Step 1: Configure UFW**

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw --force enable
```

Verify:

```bash
sudo ufw status
```

Expected:
```
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
```

- [ ] **Step 2: Configure fail2ban for SSH**

The default `sshd` jail is enabled by creating a local override:

```bash
sudo tee /etc/fail2ban/jail.d/sshd.local > /dev/null << 'EOF'
[sshd]
enabled = true
maxretry = 5
findtime = 600
bantime = 3600
EOF

sudo systemctl restart fail2ban
```

Verify:

```bash
sudo fail2ban-client status sshd
```

Expected: `Status for the jail: sshd` with `Currently banned: 0`.

- [ ] **Step 3: Enable automatic security updates**

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

When prompted, select **Yes**.

Verify the config:

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
```

Expected:
```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

---

### Task 8: Set up GCS backups

---

- [ ] **Step 1: Create a GCS bucket (from your local machine)**

```bash
gsutil mb -l us-central1 gs://gifraffe-backups-$(gcloud config get-value project)
```

Note the full bucket name (e.g. `gs://gifraffe-backups-my-project`). Use it below.

- [ ] **Step 2: Grant the VM's service account access to the bucket**

```bash
# Get the VM's service account email
SA=$(gcloud compute instances describe gifraffe \
  --zone=us-central1-a \
  --format='value(serviceAccounts[0].email)')

# Grant storage write access
gsutil iam ch serviceAccount:$SA:objectAdmin gs://gifraffe-backups-$(gcloud config get-value project)
```

- [ ] **Step 3: Write the backup script (inside the VM)**

```bash
sudo tee /opt/gifraffe/backup.sh > /dev/null << 'EOF'
#!/bin/bash
set -e

BUCKET="gs://gifraffe-backups-YOUR_PROJECT_ID"
DATE=$(date +%Y-%m-%d)
DB_PATH="/opt/gifraffe/backend/gifraffe.db"
GIFS_DIR="/opt/gifraffe/backend/storage/gifs"

# Back up database
gsutil cp "$DB_PATH" "$BUCKET/db/$DATE/gifraffe.db"

# Back up approved GIFs
gsutil -m rsync -r "$GIFS_DIR" "$BUCKET/gifs/$DATE/"

# Delete backups older than 7 days
gsutil ls "$BUCKET/db/" | sort | head -n -7 | xargs -r gsutil -m rm -r
gsutil ls "$BUCKET/gifs/" | sort | head -n -7 | xargs -r gsutil -m rm -r

echo "Backup complete: $DATE"
EOF

# Replace YOUR_PROJECT_ID with your actual GCP project ID
sudo sed -i "s/YOUR_PROJECT_ID/$(gcloud config get-value project 2>/dev/null || echo 'YOUR_PROJECT_ID')/" /opt/gifraffe/backup.sh
sudo chmod +x /opt/gifraffe/backup.sh
```

- [ ] **Step 4: Test the backup script manually**

```bash
sudo /opt/gifraffe/backup.sh
```

Expected: `Backup complete: 2026-03-24` (or today's date). No errors.

Verify in GCS:

```bash
gsutil ls gs://gifraffe-backups-$(gcloud config get-value project)/db/
```

- [ ] **Step 5: Add cron job to run daily at 2am UTC**

Run as root (so it can read the DB file owned by the `gifraffe` user):

```bash
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /opt/gifraffe/backup.sh >> /var/log/gifraffe-backup.log 2>&1") | sudo crontab -
```

Verify:

```bash
sudo crontab -l
```

Expected: `0 2 * * * /opt/gifraffe/backup.sh >> /var/log/gifraffe-backup.log 2>&1`

---

## Deployment Update Procedure

When you push new code to GitHub and want to deploy it to the server:

```bash
# SSH into the VM
gcloud compute ssh gifraffe --zone=us-central1-a

# Pull and redeploy
cd /opt/gifraffe
git pull origin main
cd backend && .venv/bin/pip install -r requirements.txt
cd ../frontend && npm run build
sudo systemctl restart gifraffe
```
