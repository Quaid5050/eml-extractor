# Deploy on Vercel (Django)

This project follows [Vercel’s Django guide](https://vercel.com/docs/frameworks/full-stack/django).

## How Vercel runs this repo

| Piece | Location | Role |
|--------|----------|------|
| `manage.py` | `web/manage.py` | Vercel finds Django and `DJANGO_SETTINGS_MODULE` |
| `WSGI_APPLICATION` | `config.wsgi.application` in `web/config/settings.py` | Default WSGI (see [docs](https://vercel.com/docs/frameworks/full-stack/django#configure-the-django-entrypoint)) |
| `tool.vercel.entrypoint` | `api/wsgi.py:application` in `pyproject.toml` |
| `vercel.json` | Rewrites all routes → `/api/wsgi` |
| Dependencies | Root `pyproject.toml` + `requirements.txt` | Installs Django before build |
| Build | `[tool.vercel.scripts] build` | `cd web && python manage.py migrate --noinput` |
| Static files | `STATIC_ROOT` in settings | Vercel runs `collectstatic` automatically ([docs](https://vercel.com/docs/frameworks/full-stack/django#serving-static-assets)) |

## Why you saw `404 NOT_FOUND`

If the build finishes in **~40ms** with no `pip install` / Django steps, Vercel did **not** create a Python function. You need:

1. Root **`vercel.json`** — routes all traffic to `wsgi.py` ([Python runtime](https://vercel.com/docs/functions/runtimes/python))
2. Root **`manage.py`** — so [Django detection](https://vercel.com/docs/frameworks/full-stack/django) works
3. Root **`requirements.txt`** + **`pyproject.toml`** — installs Django

After push, the build log should show `pip install` and `migrate` (several seconds, not 38ms).

## Vercel dashboard

| Setting | Value |
|---------|--------|
| **Root Directory** | `./` (repo root) |
| **Framework Preset** | Other (Django auto-detected via `web/manage.py`) |
| **Build / Install Command** | Leave empty — use `pyproject.toml` |

### Environment variables

| Name | Value |
|------|--------|
| `DJANGO_SECRET_KEY` | Random secret ([env vars](https://vercel.com/docs/environment-variables)) |
| `DJANGO_DEBUG` | `0` |

Generate a secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Deploy

1. Push to GitHub (`master`).
2. Import / connect the repo on Vercel.
3. Set env vars above.
4. Deploy (or **Redeploy** after fixes).

## Local dev with Vercel CLI (optional)

From the [Django on Vercel docs](https://vercel.com/docs/frameworks/full-stack/django#local-development) (CLI ≥ 50.38.0):

```bash
cd eml-extractor
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
vercel dev
```

Or without Vercel CLI:

```bash
make web-install && make web   # http://127.0.0.1:8765/
```

## Alternative: Root Directory = `web`

If you set **Root Directory** to `web` in the dashboard:

- Vercel uses `web/pyproject.toml` and `web/requirements.txt`
- Entrypoint can be `config.wsgi:application` (standard layout)
- Do **not** rely on repo-root `wsgi.py` for that mode

For most users, **Root Directory `./`** + root `pyproject.toml` is already configured.

## Build error: `No module named 'django'`

Cause: Vercel built from repo root but had no `pyproject.toml` / `requirements.txt` there.

Fix: ensure these exist at **repo root** and redeploy:

- `pyproject.toml` (with `django` in `dependencies`)
- `requirements.txt`
- `wsgi.py`
- `.python-version` (optional, pins 3.12)

## Limits

See [Vercel Functions limitations](https://vercel.com/docs/functions/limitations) and our app constraints:

- **~4.5 MB** request body (Hobby) — use small `.eml` batches
- **Ephemeral disk** — ZIP jobs in `/tmp`; download soon after extract
- **500 MB** function bundle limit ([Django on Vercel](https://vercel.com/docs/frameworks/full-stack/django#limitations))

For large mail archives, use the CLI: `make extract`.

## Custom domain

Add in Vercel env:

```
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

`*.vercel.app` hosts are handled via `VERCEL_URL` in settings when `VERCEL=1`.
