# STATUS.md — ffxiv-screenshot-album-cli

**Date:** 2026-11-05
**Owner:** Asdale Dynamics, LLC (MIT license, see `LICENSE`)
**Status:** Working, tested, committed locally.

## What was built

A Python CLI that tames a Final Fantasy XIV screenshots folder (and works
for similar game screenshot folders). Standard library only — no runtime
dependencies beyond Python 3.10+. Source files are **never modified, moved,
or deleted**; all work happens on copies.

Four verbs (`python -m ffxiv_album <command>`):

| Command | What it does |
|---|---|
| `scan SRC` | Counts shots and reports where each date came from |
| `organize SRC DEST [--tags tags.csv] [--dry-run]` | Copies shots into `DEST/Year/Place/` with friendly names and writes/updates `captions.csv` |
| `dedupe FOLDER [--csv dupes.csv]` | Finds byte-identical duplicates by SHA-256; writes a read-only report |
| `album LIBRARY [--out album.html] [--embed]` | Builds a self-contained static HTML gallery from `captions.csv` |

Details:

- **Filename parsing** (`scanner.py`): understands `ffxiv_20210904_213254.png`
  (Windows/macOS client), `s2d_20210904_213254_001.png` (PS5), the tool's own
  friendly output, and generic `YYYYMMDD_HHMMSS` stamps. Falls back to the
  file's modified time when the name has no usable stamp; undatable files keep
  their original stem and land in `unknown-year/`.
- **Friendly rename** (`rename.py`): `ffxiv_20210904_213254.png` becomes
  `2021-09-04_213254.png`; same-second collisions become `-2`, `-3`, ...
  Re-runs are no-ops (idempotent).
- **Place tags** (`tags.py`): an editable CSV of `start_date,end_date,place`
  rows (single day via empty `end_date`, `*` catch-all row, first match wins);
  unmatched shots go to `Unknown`.
- **Captions** (`organizer.py`): `captions.csv`
  (`filename,year,place,caption,favorite`) is yours to edit; re-running
  `organize` preserves your captions and favorite stars.
- **Duplicates** (`dedupe.py`): groups identical bytes across a whole tree,
  writes a CSV report (group, path, size, sha256). Nothing is ever deleted.
  Works for any images, not just screenshots.
- **Album** (`album.py`): one dark-mode HTML file, grouped by year and place,
  click-to-enlarge lightbox (Esc to close), favorites marked, zero network
  dependencies (no CDN). `--embed` base64-encodes the images into one
  portable file. The HTML expects to live inside the library folder so
  relative image paths work; `--embed` output can go anywhere.
- **Examples**: `examples/tags.csv` (place tags) and `examples/captions.csv`
  (caption format).

## How to run it

```
python -m ffxiv_album --help
python -m ffxiv_album scan /path/to/screenshots
python -m ffxiv_album organize /path/to/screenshots /path/to/library --tags examples/tags.csv --dry-run
python -m ffxiv_album organize /path/to/screenshots /path/to/library --tags examples/tags.csv
# edit LIBRARY/captions.csv ...
python -m ffxiv_album dedupe /path/to/library
python -m ffxiv_album album /path/to/library
python -m ffxiv_album album /path/to/library --out album-portable.html --embed
```

Run the tests: `python -m pytest` (48 tests).

## Verification results

- `python -m compileall ffxiv_album tests` — clean (Python 3.13.5).
- `python -m pytest -q` — **48 passed, 0 failed** in ~0.1 s
  (rename logic, stamp parsing PS5/Windows/macOS, tag ranges/wildcards,
  organize + dry-run + caption preservation, dedupe grouping and CSV report,
  album HTML, all CLI verbs and error paths).
- Full end-to-end smoke run with 5 fake screenshots (Windows + PS5 names,
  a same-second collision, a copy-paste duplicate, one 2022 shot):
  - scan: 5 images, all dates from filenames — correct.
  - organize: copies landed in `2021/Adventures/` and `2022/Adventures/`
    with friendly names and collision suffixes; source folder verified
    untouched (same 5 files, same bytes).
  - Captions edited by hand survived a second `organize` run exactly.
  - dedupe: found the 1 duplicate pair (the copy), wrote `duplicates.csv`,
    deleted nothing.
  - album: `album.html` and `--embed` portable variant both built; captions,
    favorite stars, years, lightbox, and MIT footer present in the HTML.

## Known gaps

- **Duplicates are exact-byte only.** Re-compressed or resized "same shot"
  copies are not matched (no perceptual hashing in stdlib).
- **One level deep on scan.** The organizer reads shots from the top level of
  the source folder (typical for FFXIV); dedupe/album walk recursively.
- **No EXIF parsing** (stdlib can't read EXIF); dates come from filenames or
  mtime. Fine for FFXIV's naming, weaker for camera photos.
- **mtime timezone** is the local clock's, as files store it.
- **Album thumbnails** reuse the full image with CSS `object-fit`; there is
  no thumbnail generation (no PIL). `--embed` files get large with many
  screenshots.
- **Overwrite policy in organize:** if a friendlier-name target already
  exists in the library it is left in place (no clobbering), but re-organizing
  a changed *source* with identical friendly names will silently skip.
- Same filename with different case on a case-insensitive filesystem could
  confuse dedupe paths (Cosmetic; report uses real paths).
