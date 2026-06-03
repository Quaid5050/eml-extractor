import os
import sys
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

BASE_DIR = WEB_DIR
IS_VERCEL = os.environ.get("VERCEL") == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-eml-extractor-change-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "0" if IS_VERCEL else "1") == "1"

_default_hosts = "127.0.0.1,localhost,testserver,.vercel.app"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS: list[str] = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
if IS_VERCEL and not CSRF_TRUSTED_ORIGINS:
    vercel_url = os.environ.get("VERCEL_URL")
    if vercel_url:
        CSRF_TRUSTED_ORIGINS = [f"https://{vercel_url}"]
    production_url = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
    if production_url:
        origin = f"https://{production_url}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "portal",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

if IS_VERCEL:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "/tmp/eml-extractor.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "portal.context_processors.app_settings",
            ],
        },
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if IS_VERCEL:
    MEDIA_ROOT = Path("/tmp/eml-extractor-media")
else:
    MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

DATA_UPLOAD_MAX_NUMBER_FILES = 100
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024

_default_max_file = "4" if IS_VERCEL else "25"
EML_MAX_FILE_BYTES = int(os.environ.get("EML_MAX_FILE_BYTES", str(int(_default_max_file) * 1024 * 1024)))
EML_MAX_FILES_PER_REQUEST = int(os.environ.get("EML_MAX_FILES_PER_REQUEST", "20" if IS_VERCEL else "50"))
EML_JOB_RETENTION_MINUTES = int(os.environ.get("EML_JOB_RETENTION_MINUTES", "30" if IS_VERCEL else "60"))

if IS_VERCEL:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
