# Deploy eml-extractor web UI on Vercel

The Django app lives in **`web/`**. Vercel must use that folder as the project root.

## 1. Import the repo

- GitHub repo: `Quaid5050/eml-extractor`
- Branch: `master`

## 2. Vercel project settings

| Setting | Value |
|---------|--------|
| **Project Name** | `eml-extractor` (or any name) |
| **Framework Preset** | **Other** (Vercel auto-detects Django from `manage.py`) |
| **Root Directory** | **`web`** ← important |

Click **Edit** next to Root Directory and set it to `web`, not `./`.

## 3. Environment variables

In **Project → Settings → Environment Variables**, add:

| Name | Value | Notes |
|------|--------|--------|
| `DJANGO_SECRET_KEY` | *(long random string)* | Required in production. Generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | `0` | Keep off on Vercel |

Optional:

| Name | Value |
|------|--------|
| `EML_MAX_FILES_PER_REQUEST` | `10` |
| `EML_MAX_FILE_BYTES` | `4194304` (4 MB) |

Vercel Hobby has a **~4.5 MB request body limit** — keep uploads small.

## 4. Deploy

Click **Deploy**. Vercel will:

1. Install `django` from `web/requirements.txt`
2. Run `python manage.py migrate --noinput` (from `pyproject.toml`)
3. Serve the Django WSGI app

Your site will be at `https://eml-extractor-*.vercel.app`.

## 5. Custom domain (optional)

**Project → Settings → Domains** → add your domain, then set:

```
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

## Limits on Vercel

- **No persistent disk** — ZIP jobs live in `/tmp` and expire (~30 min)
- **Download links** only work on the same deployment instance; use **Download ZIP** soon after extract
- **Large .eml + attachments** may hit body/size limits — use CLI locally for huge mail dumps
- **Cold starts** — first request after idle can be slower

## Local vs Vercel

| | Local `make web` | Vercel |
|--|------------------|--------|
| Root | `eml-extractor/` | `eml-extractor/web/` |
| Media | `web/media/` | `/tmp/eml-extractor-media/` |
| Max file | 25 MB default | 4 MB default |

## Troubleshooting

**DisallowedHost** — ensure `.vercel.app` is allowed (already in settings) or set `DJANGO_ALLOWED_HOSTS`.

**CSRF verification failed** — add your URL to `CSRF_TRUSTED_ORIGINS` or redeploy (Vercel sets `VERCEL_URL` automatically).

**Module not found `eml_core`** — Root Directory must be `web` (where `eml_core.py` and `manage.py` live).

**Build fails on migrate** — check build logs; Django 5 + Python 3.12 is supported on Vercel.

## CLI (unchanged)

From repo root on your machine:

```bash
make extract
make web
```
