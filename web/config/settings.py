import os
import sys
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent
EML_ROOT = WEB_DIR.parent
if str(EML_ROOT) not in sys.path:
    sys.path.insert(0, str(EML_ROOT))

BASE_DIR = WEB_DIR
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-eml-extractor-change-in-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")

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

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

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

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Upload limits
DATA_UPLOAD_MAX_NUMBER_FILES = 100
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
EML_MAX_FILE_BYTES = int(os.environ.get("EML_MAX_FILE_BYTES", str(25 * 1024 * 1024)))
EML_MAX_FILES_PER_REQUEST = int(os.environ.get("EML_MAX_FILES_PER_REQUEST", "50"))
EML_JOB_RETENTION_MINUTES = int(os.environ.get("EML_JOB_RETENTION_MINUTES", "60"))
