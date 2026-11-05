"""Friendly rename scheme.

Go from ``ffxiv_20210904_213254.png`` to ``2021-09-04_213254.png`` —
sortable by hand, readable by humans, and stable across re-runs.
Collisions get a numeric suffix: ``-2``, ``-3``, ...
"""

from __future__ import annotations

import re
from pathlib import Path

from .scanner import Shot


def friendly_stem(shot: Shot) -> str:
    """Build the friendly stem (date_time) for a shot."""
    if shot.taken is None:
        return shot.path.stem
    return shot.taken.strftime("%Y-%m-%d_%H%M%S")


def proposed_name(shot: Shot) -> str:
    return friendly_stem(shot) + shot.ext


def is_friendly(name: str) -> bool:
    """True if *name* already matches the friendly scheme, so re-runs are stable."""
    return bool(re.match(r"\d{4}-\d{2}-\d{2}_\d{6}(-\d+)?(\.\w+)?$", str(name)))


def make_unique(name: str, taken: set[str]) -> str:
    """Return *name*, or name-2/-3/..., avoiding anything in *taken* (case-insensitively)."""
    taken_ci = {t.lower() for t in taken}
    if str(name).lower() not in taken_ci:
        taken.add(name)
        return name
    p = Path(name)
    stem, ext = p.stem, p.suffix
    counter = 2
    while True:
        candidate = f"{stem}-{counter}{ext}"
        if candidate.lower() not in taken_ci:
            taken.add(candidate)
            return candidate
        counter += 1


def plan_renames(shots: list[Shot]) -> list[tuple[str, str]]:
    """Return (old, new) basename pairs: everything moves to the friendly scheme."""
    taken: set[str] = set()
    plan = []
    for shot in shots:
        old = shot.path.name
        new = make_unique(proposed_name(shot), taken)
        plan.append((old, new))
    return plan
