# FFXIV Screenshot Album CLI

A friendly Python command-line carer for your Final Fantasy XIV screenshots
folder (and honestly, any similarly-named game screenshot folder). It reads
the dates hidden in filenames, renames shots into something humans can read,
sorts copies into year/place folders *you* define, reports byte-identical
duplicates, and builds a browsable offline HTML album with captions you edit
in a simple CSV.

Built in plain-English tradition of
[Dylan Asdale's](https://dylanasdale.github.io) *The Massive AI Manual* —
no fuss, no cloud, no deletions.

- **Stdlib only.** No installs, no dependencies beyond Python 3.10+ and (for tests) pytest.
- **Copies only.** Your source screenshots are never renamed, edited, or deleted.
- **Local first.** The album is a single HTML file; your photos stay on your machine.

## Install

Just clone or copy the folder. You need Python 3.10 or newer:

```
python --version        # 3.10+ recommended
python -m ffxiv_album --help
```

Run the test suite once to see the "all green" glow:

```
python -m pytest
```

## The four verbs

### 1. `scan` — peek before you leap

```
python -m ffxiv_album scan "C:/Users/you/Documents/My Games/FINAL FANTASY XIV - A Realm Reborn/screenshots"
```

Counts your shots and reports where each date came from (parsed from the
filename like `ffxiv_20210904_213254.png`, or the file's modified time).

### 2. `organize` — copy into Year/Place folders + editable captions

```
python -m ffxiv_album organize RAW-FOLDER LIBRARY-FOLDER --tags where-we-roamed.csv
```

- Every shot is **copied** to `LIBRARY/2023/My Place/2023-09-21_183045.png`.
- Place names come from your tags CSV:

```csv
start_date,end_date,place
2023-09-20,2023-10-02,Ishgard
2024-03-30,,Spring Break RP
*,,Adventures
```

A date range (or a single day via empty `end_date`, or `*` for everywhere
unlisted). Unmatched shots land in `Unknown`/`unknown-year` folders, never lost.

- It writes `LIBRARY/captions.csv`:

```csv
filename,year,place,caption,favorite
2023-09-21_183045.png,2023,Ishgard,dim sum with the FC,1
```

**Edit that file freely** and re-run `organize` later: your captions and
favorite stars survive re-runs. Add `--dry-run` first to preview the plan.

### 3. `dedupe` — find byte-identical copies (read-only)

```
python -m ffxiv_album dedupe LIBRARY --csv dupes.csv
```

Groups files that are hash-for-hash identical and writes `dupes.csv`
(group, path, size, sha256). Nothing is ever removed; you decide.

### 4. `album` — build the browsable album

```
python -m ffxiv_album album LIBRARY
```

Writes `LIBRARY/album.html` — a dark, keyboard-friendly gallery grouped by
year and place, showing your captions (favorites marked with a star), with a
click-to-enlarge lightbox. Open it in any browser, works with zero network.
Prefer one portable file to email or post? Add `--embed` to base64-encode
the images straight into the HTML.

## Works for more than FFXIV

Any folder of image files with common dated names (`ffxiv_...`,
`s2d_...` from PS5, `2021-09-04_213254.png` styles) works, and anything
without a date in the name politely falls back to the file's modified time.

## Repository layout

```
ffxiv_album/          scanner, rename, tags, organizer, dedupe, album, cli
tests/                pytest suite (rename logic and friends)
README.md             you are here
LICENSE               MIT — Copyright (c) 2026 Asdale Dynamics, LLC
STATUS.md             build status, verification results, known gaps
```

## Like this? See the book

*The Massive AI Manual* by Dylan Asdale explains AI tools, agents, local AI
and free AI coding "like a friend would" — plain English, step by step.
More at [dylanasdale.github.io](https://dylanasdale.github.io).

## License

MIT. Copyright (c) 2026 Asdale Dynamics, LLC. All screenshots remain the
property of their players; Final Fantasy XIV is a trademark of Square Enix
and this tool is not affiliated with or endorsed by them.
