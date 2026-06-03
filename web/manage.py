#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def main() -> None:
    web_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(web_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Install dependencies: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
