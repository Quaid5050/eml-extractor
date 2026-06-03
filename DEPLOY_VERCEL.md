# Deploy eml-extractor web UI on Vercel

## Vercel project settings

| Setting | Value |
|---------|--------|
| **Framework Preset** | Other (auto-detects Django) |
| **Root Directory** | **`./`** (repo root — default) |
| **Build Command** | *(leave empty — uses `pyproject.toml`)* |
| **Install Command** | *(leave empty — uses `pyproject.toml`)* |

> You can also set Root Directory to **`web`**, but repo root (`./`) is now fully supported via root `pyproject.toml` + `wsgi.py`.

## Environment variables

**Project → Settings → Environment Variables:**

| Name | Value |
|------|--------|
| `DJANGO_SECRET_KEY` | Long random string (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DJANGO_DEBUG` | `0` |

## Deploy

1. **Push** latest code (must include root `pyproject.toml`, `requirements.txt`, `wsgi.py`)
2. **Redeploy** on Vercel

## What fixes the “No module named django” build error

Vercel installs Python deps from the **repo root** `pyproject.toml` / `requirements.txt`.  
The app runs through root `wsgi.py`, which loads Django from `web/`.

## Limits on Vercel

- ~**4.5 MB** request body on Hobby — small `.eml` batches only
- ZIP files are **temporary** (`/tmp`) — download right after extract
- Large mail dumps → use CLI: `make extract`

## Custom domain

Add `CSRF_TRUSTED_ORIGINS=https://yourdomain.com` if needed (Vercel sets `VERCEL_URL` automatically for `*.vercel.app`).
