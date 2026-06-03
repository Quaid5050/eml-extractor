from __future__ import annotations

import shutil
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from .services import cleanup_old_jobs, create_job_dir, run_extraction, save_zip

VERIFICATION_DIR = Path(__file__).resolve().parent.parent / "verification"
GOOGLE_VERIFICATION_FILE = VERIFICATION_DIR / "google2aaa255fde4003d7.html"


def google_site_verification(_request: HttpRequest) -> HttpResponse:
    """Serve Google Search Console HTML verification at site root."""
    if not GOOGLE_VERIFICATION_FILE.is_file():
        return HttpResponse("Verification file not found.", status=404)
    return FileResponse(GOOGLE_VERIFICATION_FILE.open("rb"), content_type="text/html; charset=utf-8")


class HomeView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        cleanup_old_jobs()
        return render(request, "portal/home.html")


class ExtractView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        uploads = request.FILES.getlist("eml_files")
        if not uploads:
            return render(
                request,
                "portal/home.html",
                {"error": "Choose at least one .eml file."},
                status=400,
            )

        if len(uploads) > settings.EML_MAX_FILES_PER_REQUEST:
            return render(
                request,
                "portal/home.html",
                {
                    "error": f"Too many files. Maximum is {settings.EML_MAX_FILES_PER_REQUEST} per upload.",
                },
                status=400,
            )

        files: list[tuple[str, bytes]] = []
        for upload in uploads:
            name = upload.name or "message.eml"
            if not name.lower().endswith(".eml"):
                continue
            data = upload.read()
            if len(data) > settings.EML_MAX_FILE_BYTES:
                return render(
                    request,
                    "portal/home.html",
                    {
                        "error": f"“{name}” exceeds {settings.EML_MAX_FILE_BYTES // (1024 * 1024)} MB limit.",
                    },
                    status=400,
                )
            files.append((name, data))

        if not files:
            return render(
                request,
                "portal/home.html",
                {"error": "No valid .eml files in upload."},
                status=400,
            )

        job_dir = create_job_dir()
        batch = run_extraction(files, job_dir)
        output_root = job_dir / "output"

        if batch.stats.success + batch.stats.updated == 0:
            shutil.rmtree(job_dir, ignore_errors=True)
            return render(
                request,
                "portal/home.html",
                {
                    "error": "Nothing was extracted. Check file format and try again.",
                    "batch": batch,
                },
                status=400,
            )

        zip_path = save_zip(job_dir, output_root)
        job_id = job_dir.name

        extracted_count = batch.stats.success + batch.stats.updated
        return render(
            request,
            "portal/result.html",
            {
                "job_id": job_id,
                "batch": batch,
                "extracted_count": extracted_count,
                "zip_size": zip_path.stat().st_size,
            },
        )


class DownloadZipView(View):
    def get(self, request: HttpRequest, job_id: str) -> HttpResponse:
        zip_path = settings.MEDIA_ROOT / "jobs" / job_id / "extracted.zip"
        if not zip_path.is_file():
            return HttpResponse("Download expired or not found.", status=404)

        response = FileResponse(zip_path.open("rb"), as_attachment=True, filename="eml-extracted.zip")
        return response
