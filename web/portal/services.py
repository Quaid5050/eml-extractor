from __future__ import annotations

import io
import shutil
import uuid
import zipfile
from pathlib import Path

from django.conf import settings

from eml_core import BatchResult, process_uploads

JOBS_DIR = settings.MEDIA_ROOT / "jobs"


def create_job_dir() -> Path:
    job_id = uuid.uuid4().hex
    job_dir = JOBS_DIR / job_id
    output_dir = job_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def run_extraction(files: list[tuple[str, bytes]], job_dir: Path) -> BatchResult:
    output_root = job_dir / "output"
    return process_uploads(files, output_root)


def build_zip_bytes(output_root: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(output_root.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(output_root).as_posix()
                zf.write(path, arcname)
    buffer.seek(0)
    return buffer.getvalue()


def save_zip(job_dir: Path, output_root: Path) -> Path:
    zip_path = job_dir / "extracted.zip"
    zip_path.write_bytes(build_zip_bytes(output_root))
    return zip_path


def cleanup_old_jobs() -> None:
    if not JOBS_DIR.exists():
        return
    # Best-effort; production would use cron/celery
    import time

    max_age = settings.EML_JOB_RETENTION_MINUTES * 60
    now = time.time()
    for job_dir in JOBS_DIR.iterdir():
        if not job_dir.is_dir():
            continue
        if now - job_dir.stat().st_mtime > max_age:
            shutil.rmtree(job_dir, ignore_errors=True)
