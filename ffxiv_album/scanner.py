"""Scan a screenshots folder and figure out when each shot was taken.

Understands the common FFXIV naming styles:

    ffxiv_20210904_213254.png        (Windows / macOS client)
    s2d_20210904_213254_001.png      (PlayStation 5 screenshot)
    s2e_20210904_213254_001.jpg      (PlayStation 5 older pattern)

plus the tool's own friendly output (so re-runs are idempotent):

    2021-09-04_213254.png

Anything that doesn't match falls back to the file's modification time.
"""

from __future__ import annotations

import datetime as dt
import os
import re
from dataclasses import dataclass
from pathlib import Path

# 20210904_213254 or 2021-09-04 21-32-54 style stamps
STAMP_RE = re.compile(
    r"(?:(?P<ymd>(?<!\d)(?:19|20)\d{2})(?P<sep>[-_.]?)(?P<mo>\d{2})(?P=sep)(?P<da>\d{2}))"
    r"[_\- ]?"
    r"(?:(?P<hh>\d{2})(?P<tsep>[-_.]?)(?P<mm>\d{2})(?P=tsep)(?P<ss>\d{2}))?"
)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}

FRIENDLY_RE = re.compile(
    r"(?<!\d)(?P<ymd>\d{4}-\d{2}-\d{2})[_ ](?P<hms>\d{6})(?:-\d+)?"
)


@dataclass
class Shot:
    path: Path
    taken: dt.datetime | None  # naive local datetime, or None if undatable
    source: str  # "filename" or "mtime" or "unknown"
    size: int

    @property
    def ext(self) -> str:
        return self.path.suffix.lower()


def parse_stamp(name: str) -> dt.datetime | None | str:
    """Return a datetime parsed from *name*, "mtime" for fallback rule, or None."""
    base = Path(name).stem
    m = FRIENDLY_RE.search(base)
    if m:
        try:
            return dt.datetime.strptime(
                f"{m.group('ymd')}_{m.group('hms')}", "%Y-%m-%d_%H%M%S"
            )
        except ValueError:
            pass
    m = STAMP_RE.search(base)
    if not m:
        return "mtime"
    try:
        return dt.datetime(
            int(m.group("ymd")),
            int(m.group("mo")),
            int(m.group("da")),
            int(m.group("hh") or 0),
            int(m.group("mm") or 0),
            int(m.group("ss") or 0),
        )
    except ValueError:
        return "mtime"


def scan(src: str | os.PathLike) -> list[Shot]:
    """List image shots under *src* (one level) with their best-guess dates."""
    root = Path(src)
    shots: list[Shot] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_file() or entry.suffix.lower() not in IMAGE_EXTS:
            continue
        result = parse_stamp(entry.name)
        if result == "mtime":
            stamp = dt.datetime.fromtimestamp(entry.stat().st_mtime)
            shots.append(Shot(path=entry, taken=stamp, source="mtime", size=entry.stat().st_size))
        elif result is None:
            shots.append(Shot(path=entry, taken=None, source="unknown", size=entry.stat().st_size))
        else:
            shots.append(Shot(path=entry, taken=result, source="filename", size=entry.stat().st_size))
    return shots
