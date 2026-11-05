"""Copy screenshots into a tidy, human-navigable library.

    DEST/
      2023/
        Coerthas Western Highlands/
          2023-09-04_213254.png
      captions.csv          <- editable: filename,place,caption,favorite

Source files are only ever *copied* (shutil.copy2), never moved, edited,
or deleted. Re-running keeps captions you have already written.
"""

from __future__ import annotations

import csv
from pathlib import Path

from .rename import plan_renames
from .scanner import Shot, scan
from .tags import TagRule, load_tags, place_for

CAPTION_COLUMNS = ["filename", "year", "place", "caption", "favorite"]


def _load_existing_captions(captions_csv: Path) -> dict[str, dict[str, str]]:
    if not captions_csv.exists():
        return {}
    with open(captions_csv, newline="", encoding="utf-8") as fh:
        return {
            (row.get("filename") or "").strip(): {
                "caption": (row.get("caption") or "").strip(),
                "favorite": (row.get("favorite") or "").strip(),
            }
            for row in csv.DictReader(fh)
        }


def organize(
    src: Path,
    dest: Path,
    rules: "list[TagRule] | Path | None" = None,
    dry_run: bool = False,
) -> list[dict[str, str]]:
    """Copy/plan copies of every shot from *src* into *dest*, return caption rows."""
    shots: list[Shot] = scan(src)
    if rules is None:
        rules = []
    elif isinstance(rules, Path):
        rules = load_tags(rules)
    old_new = plan_renames(shots)
    captions_csv = dest / "captions.csv"
    existing = _load_existing_captions(captions_csv)

    rows: list[dict[str, str]] = []
    for shot, (old, new) in zip(shots, old_new):
        year = shot.taken.strftime("%Y") if shot.taken else "unknown-year"
        place = place_for(rules, shot.taken)
        prev = existing.get(new, {})
        rows.append(
            {
                "filename": new,
                "year": year,
                "place": place,
                "caption": prev.get("caption", ""),
                "favorite": prev.get("favorite", ""),
            }
        )
        if not dry_run:
            folder = dest / year / place
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / new
            if not target.exists():
                import shutil

                shutil.copy2(shot.path, target)

    rows.sort(key=lambda r: (r["year"], r["place"], r["filename"]))
    if not dry_run:
        dest.mkdir(parents=True, exist_ok=True)
        write_captions(captions_csv, rows)
    return rows


def write_captions(path: Path, rows: list[dict[str, str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CAPTION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def read_captions(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [
            {
                "filename": (row.get("filename") or "").strip(),
                "year": (row.get("year") or "").strip(),
                "place": (row.get("place") or "").strip(),
                "caption": (row.get("caption") or "").strip(),
                "favorite": (row.get("favorite") or "").strip(),
            }
            for row in csv.DictReader(fh)
            if (row.get("filename") or "").strip()
        ]
