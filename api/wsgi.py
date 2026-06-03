"""Vercel serverless entry (api/*.py → function)."""
import os
import sys
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
sys.path.insert(0, str(WEB_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
