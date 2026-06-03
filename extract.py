#!/usr/bin/env python3
"""
eml-extractor — batch-export .eml files to folders with headers, bodies, and attachments.

Usage:
  python extract.py
  python extract.py path/to/message.eml
"""

from __future__ import annotations

import email
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.header import decode_header
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"

INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_LEGACY_SUFFIX_DIR = re.compile(r"^(.+)_(\d+)$")


@dataclass
class ExtractResult:
    eml_name: str
    out_dir: Path
    status: str  # "success" | "updated"
    legacy_dirs_removed: list[str]


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


def remove_legacy_suffix_dirs(folder_name: str) -> list[str]:
    """Remove output/<name>_2, _3, … left from older runs."""
    removed: list[str] = []
    for child in OUTPUT_DIR.iterdir():
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
    return any(p.name != ".gitkeep" for p in out_dir.iterdir())


def prepare_output_dir(out_dir: Path) -> None:
    """Reuse one folder per .eml; clear previous extraction before writing."""
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


def write_email_txt(
    msg: email.message.Message,
    source_name: str,
    out_dir: Path,
    saved_files: list[str],
) -> None:
    plain, html = get_bodies(msg)

    header_fields = [
        ("Message-ID", "Message-ID"),
        ("Date", "Date"),
        ("From", "From"),
        ("To", "To"),
        ("Cc", "Cc"),
        ("Bcc", "Bcc"),
        ("Reply-To", "Reply-To"),
        ("Subject", "Subject"),
        ("Delivered-To", "Delivered-To"),
        ("Return-Path", "Return-Path"),
    ]

    lines = [
        "=" * 60,
        "EMAIL SUMMARY",
        "=" * 60,
        f"Source file: {source_name}",
        f"Output folder: {out_dir.name}",
        f"Extracted at: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    for label, header_key in header_fields:
        value = decode_mime_header(msg.get(header_key))
        lines.append(f"{label}: {value}")

    lines.extend(
        [
            "",
            "=" * 60,
            "PLAIN TEXT BODY",
            "=" * 60,
            (plain or "").strip() or "(none)",
            "",
            "=" * 60,
            "HTML BODY",
            "=" * 60,
            (html or "").strip() or "(none)",
            "",
            "=" * 60,
            "SAVED FILES",
            "=" * 60,
        ]
    )

    if saved_files:
        lines.extend(f"- {name}" for name in saved_files)
    else:
        lines.append("(no attachments)")

    lines.append("")
    (out_dir / "email.txt").write_text("\n".join(lines), encoding="utf-8")


def save_attachment(out_dir: Path, filename: str, data: bytes) -> str:
    dest = out_dir / filename
    dest.write_bytes(data)
    return dest.name


def process_eml(eml_path: Path) -> ExtractResult:
    with eml_path.open("rb") as fh:
        msg = email.message_from_binary_file(fh, policy=policy.default)

    folder_name = sanitize_name(eml_path.stem)
    out_dir = OUTPUT_DIR / folder_name
    was_existing = output_dir_has_content(out_dir)
    legacy_removed = remove_legacy_suffix_dirs(folder_name)
    prepare_output_dir(out_dir)

    saved_files: list[str] = []
    for filename, data, _ctype in collect_attachments(msg):
        saved_files.append(save_attachment(out_dir, filename, data))

    write_email_txt(msg, eml_path.name, out_dir, saved_files)
    status = "updated" if was_existing else "success"
    return ExtractResult(
        eml_name=eml_path.name,
        out_dir=out_dir,
        status=status,
        legacy_dirs_removed=legacy_removed,
    )


def print_summary(stats: RunStats) -> None:
    print("")
    print("─" * 40)
    print("Extract summary")
    print(f"  Total in batch:         {stats.total_input}")
    print(f"  Success (new):          {stats.success}")
    print(f"  Updated (re-extract):   {stats.updated}")
    print(f"  Skipped:                {stats.skipped}")
    print(f"  Skipped (dup input):    {stats.skipped_duplicate_input}")
    print(f"  Failed:                 {stats.failed}")
    print(f"  Duplicate dirs removed: {stats.legacy_dirs_removed}")
    print("─" * 40)


def main(argv: list[str]) -> int:
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    if len(argv) > 1:
        paths = [Path(p).resolve() for p in argv[1:]]
    else:
        paths = sorted(INPUT_DIR.glob("*.eml")) + sorted(INPUT_DIR.glob("*.EML"))

    if not paths:
        print(f"No .eml files found. Add files to:\n  {INPUT_DIR}")
        return 1

    stats = RunStats(total_input=len(paths))
    seen_folder_names: set[str] = set()

    for eml_path in paths:
        if not eml_path.is_file():
            stats.skipped += 1
            print(f"SKIP  [not a file]      {eml_path}")
            continue
        if eml_path.suffix.lower() != ".eml":
            stats.skipped += 1
            print(f"SKIP  [not .eml]        {eml_path}")
            continue

        folder_name = sanitize_name(eml_path.stem)
        if folder_name in seen_folder_names:
            stats.skipped_duplicate_input += 1
            stats.skipped += 1
            print(f"SKIP  [duplicate input] {eml_path.name} (same output folder as earlier file)")
            continue
        seen_folder_names.add(folder_name)

        try:
            result = process_eml(eml_path)
            rel = result.out_dir.relative_to(SCRIPT_DIR)
            if result.status == "updated":
                stats.updated += 1
            else:
                stats.success += 1
            stats.legacy_dirs_removed += len(result.legacy_dirs_removed)

            extra = ""
            if result.legacy_dirs_removed:
                extra = f" (removed duplicate folders: {', '.join(result.legacy_dirs_removed)})"
            label = "UPDATED" if result.status == "updated" else "SUCCESS"
            print(f"{label} {result.eml_name} -> {rel}/{extra}")
        except Exception as exc:
            stats.failed += 1
            print(f"FAIL  {eml_path.name}: {exc}")

    print_summary(stats)
    return 1 if stats.failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
