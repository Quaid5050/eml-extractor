#!/usr/bin/env python3
"""
eml-extractor CLI — batch-export .eml files to folders with email.md, email.html, attachments.

Usage:
  python extract.py
  python extract.py path/to/message.eml
"""

from __future__ import annotations

import sys
from pathlib import Path

from eml_core import RunStats, process_batch

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / "input"
OUTPUT_DIR = SCRIPT_DIR / "output"


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

    batch = process_batch(paths, OUTPUT_DIR)

    for result in batch.results:
        if result.status == "skipped":
            reason = result.error or "skipped"
            print(f"SKIP  [{reason}] {result.eml_name}")
            continue
        if result.status == "failed":
            print(f"FAIL  {result.eml_name}: {result.error}")
            continue
        rel = result.out_dir.relative_to(SCRIPT_DIR)
        extra = ""
        if result.legacy_dirs_removed:
            extra = f" (removed duplicate folders: {', '.join(result.legacy_dirs_removed)})"
        label = "UPDATED" if result.status == "updated" else "SUCCESS"
        print(f"{label} {result.eml_name} -> {rel}/{extra}")

    print_summary(batch.stats)
    return 1 if batch.stats.failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
