"""Find duplicate screenshot copies by content hash.

Safe by design: nothing is deleted or moved. You get a CSV report and
decide for yourself. Grouping is exact (same bytes), so a lightly
re-compressed copy is *not* flagged (see STATUS.md for known gaps).
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

CHUNK = 1 << 20


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def find_duplicates(files: list[Path]) -> list[list[Path]]:
    """Group files that are byte-for-byte identical (ordered like the input)."""
    by_hash: dict[str, list[Path]] = {}
    order: list[str] = []
    for path in files:
        digest = sha256_of(path)
        if digest not in by_hash:
            by_hash[digest] = []
            order.append(digest)
        by_hash[digest].append(path)
    return [group for digest in order for group in [by_hash[digest]] if len(group) > 1]


def collect_images(root: Path) -> list[Path]:
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts)


def write_report(path: Path, groups: list[list[Path]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["duplicate_group", "file_path", "size_bytes", "sha256"])
        for i, group in enumerate(groups, start=1):
            for p in group:
                writer.writerow([i, str(p), p.stat().st_size, sha256_of(p)])
