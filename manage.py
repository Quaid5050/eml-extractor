#!/usr/bin/env python3
"""Django CLI at repo root (Vercel discovers manage.py here)."""
import os
import sys
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent / "web"
sys.path.insert(0, str(WEB_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.management import execute_from_command_line  # noqa: E402

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
