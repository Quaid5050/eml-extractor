"""
Shared .eml extraction logic for CLI and web.
"""

from __future__ import annotations

import email
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from email import policy
from email.header import decode_header
from pathlib import Path

INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_LEGACY_SUFFIX_DIR = re.compile(r"^(.+)_(\d+)$")


@dataclass
class ExtractResult:
    eml_name: str
    out_dir: Path
    status: str  # "success" | "updated"
    legacy_dirs_removed: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class BatchResult:
    results: list[ExtractResult] = field(default_factory=list)
    stats: "RunStats" = field(default_factory=lambda: RunStats())

    @property
    def output_root(self) -> Path | None:
        if not self.results:
            return None
        return self.results[0].out_dir.parent


@dataclass
class RunStats:
    total_input: int = 0
    success: int = 0
    updated: int = 0
    skipped: int = 0
    skipped_duplicate_input: int = 0
    failed: int = 0
    legacy_dirs_removed: int = 0


def sanitize_name(name: str, max_len: int = 120) -> str:
    name = INVALID_PATH_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    return (name[:max_len] if name else "email")


def decode_mime_header(value: str | None) -> str:
    if not value:
        return ""
    parts: list[str] = []
    for fragment, charset in decode_header(value):
        if isinstance(fragment, bytes):
            parts.append(fragment.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(fragment)
    return "".join(parts)


def remove_legacy_suffix_dirs(output_root: Path, folder_name: str) -> list[str]:
    removed: list[str] = []
    if not output_root.exists():
        return removed
    for child in output_root.iterdir():
        if not child.is_dir() or child.name == folder_name:
            continue
        match = _LEGACY_SUFFIX_DIR.match(child.name)
        if match and match.group(1) == folder_name:
            shutil.rmtree(child)
            removed.append(child.name)
    return removed


def output_dir_has_content(out_dir: Path) -> bool:
    if not out_dir.exists():
        return False
    return any(p.is_file() and p.name != ".gitkeep" for p in out_dir.iterdir()) or any(
        p.is_dir() for p in out_dir.iterdir()
    )


def prepare_output_dir(out_dir: Path) -> None:
    if out_dir.exists():
        for item in out_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    out_dir.mkdir(parents=True, exist_ok=True)


def get_bodies(msg: email.message.Message) -> tuple[str | None, str | None]:
    plain: str | None = None
    html: str | None = None

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            disposition = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disposition:
                continue
            ctype = part.get_content_type()
            try:
                payload = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    charset = part.get_content_charset() or "utf-8"
                    payload = payload.decode(charset, errors="replace")
            if ctype == "text/plain" and plain is None:
                plain = payload if isinstance(payload, str) else None
            elif ctype == "text/html" and html is None:
                html = payload if isinstance(payload, str) else None
    else:
        try:
            payload = msg.get_content()
        except Exception:
            raw = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            payload = raw.decode(charset, errors="replace") if isinstance(raw, bytes) else raw
        if msg.get_content_type() == "text/plain":
            plain = payload if isinstance(payload, str) else None
        elif msg.get_content_type() == "text/html":
            html = payload if isinstance(payload, str) else None

    return plain, html


def collect_attachments(msg: email.message.Message) -> list[tuple[str, bytes, str]]:
    seen: set[tuple[str, int]] = set()
    results: list[tuple[str, bytes, str]] = []

    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue

        raw_name = part.get_filename()
        disposition = (part.get("Content-Disposition") or "").lower()
        is_attachment = "attachment" in disposition or bool(raw_name)

        if not is_attachment:
            continue

        if raw_name:
            filename = decode_mime_header(raw_name)
        else:
            content_id = (part.get("Content-ID") or "").strip("<>")
            filename = f"inline_{content_id}" if content_id else "attachment.bin"

        filename = sanitize_name(filename.replace("\n", " ").replace("\r", " "), max_len=200)
        data = part.get_payload(decode=True)
        if not data:
            continue

        key = (filename, len(data))
        if key in seen:
            continue
        seen.add(key)

        results.append((filename, data, part.get_content_type() or "application/octet-stream"))

    return results


def _md_escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def write_email_md(
    msg: email.message.Message,
    source_name: str,
    out_dir: Path,
    saved_files: list[str],
) -> None:
    plain, html = get_bodies(msg)
    subject = decode_mime_header(msg.get("Subject")) or "(no subject)"
    extracted_at = datetime.now().isoformat(timespec="seconds")

    header_fields = [
        ("Date", "Date"),
        ("From", "From"),
        ("To", "To"),
        ("Cc", "Cc"),
        ("Bcc", "Bcc"),
        ("Reply-To", "Reply-To"),
        ("Message-ID", "Message-ID"),
        ("Delivered-To", "Delivered-To"),
        ("Return-Path", "Return-Path"),
    ]

    lines = [
        f"# {subject}",
        "",
        f"- **Source file:** `{source_name}`",
        f"- **Output folder:** `{out_dir.name}`",
        f"- **Extracted at:** {extracted_at}",
        "",
        "## Headers",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]

    for label, header_key in header_fields:
        value = decode_mime_header(msg.get(header_key))
        if value:
            lines.append(f"| **{label}** | {_md_escape_cell(value)} |")

    lines.extend(["", "## Plain text body", ""])
    plain_stripped = (plain or "").strip()
    if plain_stripped:
        lines.extend(["```text", plain_stripped, "```"])
    else:
        lines.append("*(none)*")

    html_stripped = (html or "").strip()
    if html_stripped:
        (out_dir / "email.html").write_text(html_stripped, encoding="utf-8")
        lines.extend(
            [
                "",
                "## HTML body",
                "",
                "Open **[email.html](./email.html)** in a browser to preview the rendered email.",
            ]
        )
    else:
        lines.extend(["", "## HTML body", "", "*(none)*"])

    lines.extend(["", "## Attachments", ""])
    if saved_files:
        for name in saved_files:
            if name in ("email.md", "email.html"):
                continue
            lines.append(f"- [{name}](./{name})")
    else:
        lines.append("*(no attachments)*")

    lines.append("")
    (out_dir / "email.md").write_text("\n".join(lines), encoding="utf-8")


def save_attachment(out_dir: Path, filename: str, data: bytes) -> str:
    dest = out_dir / filename
    dest.write_bytes(data)
    return dest.name


def process_eml_file(eml_path: Path, output_root: Path) -> ExtractResult:
    with eml_path.open("rb") as fh:
        msg = email.message_from_binary_file(fh, policy=policy.default)

    folder_name = sanitize_name(eml_path.stem)
    out_dir = output_root / folder_name
    was_existing = output_dir_has_content(out_dir)
    legacy_removed = remove_legacy_suffix_dirs(output_root, folder_name)
    prepare_output_dir(out_dir)

    saved_files: list[str] = []
    for filename, data, _ctype in collect_attachments(msg):
        saved_files.append(save_attachment(out_dir, filename, data))

    write_email_md(msg, eml_path.name, out_dir, saved_files)
    status = "updated" if was_existing else "success"
    return ExtractResult(
        eml_name=eml_path.name,
        out_dir=out_dir,
        status=status,
        legacy_dirs_removed=legacy_removed,
    )


def process_eml_bytes(data: bytes, source_name: str, output_root: Path) -> ExtractResult:
    """Process uploaded bytes; source_name used for display and folder naming."""
    safe_stem = Path(source_name).stem or "email"
    tmp = output_root / "_uploads"
    tmp.mkdir(parents=True, exist_ok=True)
    eml_path = tmp / f"{sanitize_name(safe_stem, max_len=80)}.eml"
    eml_path.write_bytes(data)
    try:
        return process_eml_file(eml_path, output_root)
    finally:
        if eml_path.exists():
            eml_path.unlink()


def process_batch(paths: list[Path], output_root: Path) -> BatchResult:
    output_root.mkdir(parents=True, exist_ok=True)
    batch = BatchResult()
    batch.stats.total_input = len(paths)
    seen_folder_names: set[str] = set()

    for eml_path in paths:
        if not eml_path.is_file():
            batch.stats.skipped += 1
            batch.results.append(
                ExtractResult(eml_name=str(eml_path), out_dir=output_root, status="skipped", error="not a file")
            )
            continue
        if eml_path.suffix.lower() != ".eml":
            batch.stats.skipped += 1
            batch.results.append(
                ExtractResult(eml_name=eml_path.name, out_dir=output_root, status="skipped", error="not .eml")
            )
            continue

        folder_name = sanitize_name(eml_path.stem)
        if folder_name in seen_folder_names:
            batch.stats.skipped_duplicate_input += 1
            batch.stats.skipped += 1
            batch.results.append(
                ExtractResult(
                    eml_name=eml_path.name,
                    out_dir=output_root,
                    status="skipped",
                    error="duplicate name in batch",
                )
            )
            continue
        seen_folder_names.add(folder_name)

        try:
            result = process_eml_file(eml_path, output_root)
            batch.results.append(result)
            if result.status == "updated":
                batch.stats.updated += 1
            else:
                batch.stats.success += 1
            batch.stats.legacy_dirs_removed += len(result.legacy_dirs_removed)
        except Exception as exc:
            batch.stats.failed += 1
            batch.results.append(
                ExtractResult(
                    eml_name=eml_path.name,
                    out_dir=output_root,
                    status="failed",
                    error=str(exc),
                )
            )

    uploads_tmp = output_root / "_uploads"
    if uploads_tmp.exists():
        shutil.rmtree(uploads_tmp, ignore_errors=True)

    return batch


def process_uploads(files: list[tuple[str, bytes]], output_root: Path) -> BatchResult:
    """files: list of (filename, raw bytes)."""
    output_root.mkdir(parents=True, exist_ok=True)
    batch = BatchResult()
    batch.stats.total_input = len(files)
    seen_folder_names: set[str] = set()

    for filename, data in files:
        if not filename.lower().endswith(".eml"):
            batch.stats.skipped += 1
            batch.results.append(
                ExtractResult(eml_name=filename, out_dir=output_root, status="skipped", error="not .eml")
            )
            continue

        folder_name = sanitize_name(Path(filename).stem)
        if folder_name in seen_folder_names:
            batch.stats.skipped_duplicate_input += 1
            batch.stats.skipped += 1
            batch.results.append(
                ExtractResult(
                    eml_name=filename,
                    out_dir=output_root,
                    status="skipped",
                    error="duplicate name in batch",
                )
            )
            continue
        seen_folder_names.add(folder_name)

        try:
            result = process_eml_bytes(data, filename, output_root)
            batch.results.append(result)
            if result.status == "updated":
                batch.stats.updated += 1
            else:
                batch.stats.success += 1
            batch.stats.legacy_dirs_removed += len(result.legacy_dirs_removed)
        except Exception as exc:
            batch.stats.failed += 1
            batch.results.append(
                ExtractResult(
                    eml_name=filename,
                    out_dir=output_root,
                    status="failed",
                    error=str(exc),
                )
            )

    uploads_tmp = output_root / "_uploads"
    if uploads_tmp.exists():
        shutil.rmtree(uploads_tmp, ignore_errors=True)

    return batch
