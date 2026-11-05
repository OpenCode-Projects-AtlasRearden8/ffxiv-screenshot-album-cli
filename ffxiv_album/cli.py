"""Command-line interface.

    python -m ffxiv_album --help
    python -m ffxiv_album scan <src>
    python -m ffxiv_album organize <src> <dest> [--tags tags.csv] [--dry-run]
    python -m ffxiv_album dedupe <folder> [--csv dupes.csv]
    python -m ffxiv_album album <library> [--out album.html] [--embed]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .album import build_album
from .dedupe import collect_images, find_duplicates, write_report
from .organizer import organize
from .scanner import scan
from .tags import load_tags


def _cmd_scan(args: argparse.Namespace) -> int:
    src = Path(args.src)
    if not src.is_dir():
        print(f"error: {src} is not a folder", file=sys.stderr)
        return 2
    shots = scan(src)
    by_source: dict[str, int] = {}
    for s in shots:
        by_source[s.source] = by_source.get(s.source, 0) + 1
    print(f"{len(shots)} image(s) in {args.src}")
    for source in ("filename", "mtime", "unknown"):
        if source in by_source:
            label = {
                "filename": "date from filename",
                "mtime": "date from file modified time",
                "unknown": "no date found",
            }[source]
            print(f"  {by_source[source]:5d}  {label}")
    for shot in shots[:10]:
        print(f"  {shot.path.name} -> {shot.taken} ({shot.source})")
    if len(shots) > 10:
        print(f"  ... and {len(shots) - 10} more")
    return 0


def _cmd_organize(args: argparse.Namespace) -> int:
    src, dest = Path(args.src), Path(args.dest)
    if not src.is_dir():
        print(f"error: {src} is not a folder", file=sys.stderr)
        return 2
    rules = load_tags(args.tags) if args.tags else []
    if args.tags and not rules:
        print(f"warning: no usable place rows in {args.tags}", file=sys.stderr)
    rows = organize(src, dest, rules=rules, dry_run=args.dry_run)
    verb = "Would copy" if args.dry_run else "Copied"
    print(f"{verb} {len(rows)} shot(s) into {dest} (source untouched)")
    if not args.dry_run:
        print(f"edit captions at: {dest / 'captions.csv'}")
    return 0


def _cmd_dedupe(args: argparse.Namespace) -> int:
    root = Path(args.folder)
    files = collect_images(root)
    groups = find_duplicates(files)
    wasted = sum(sum(p.stat().st_size for p in g[1:]) for g in groups)
    print(f"{len(files)} image(s) scanned; {len(groups)} duplicate group(s); "
          f"{wasted} bytes of redundant copies")
    out = Path(args.csv) if args.csv else root / "duplicates.csv"
    if groups:
        write_report(out, groups)
        print(f"report written to {out} — nothing was deleted")
    else:
        print("no duplicates found; no report written")
    return 0


def _cmd_album(args: argparse.Namespace) -> int:
    lib = Path(args.library)
    if not (lib / "captions.csv").exists():
        print(f"error: no captions.csv in {lib} — run the organize step first",
              file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else lib / "album.html"
    path = build_album(lib, out, embed=args.embed)
    print(f"album written to {path} — open it in your browser")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ffxiv-album",
        description="Tame your FFXIV (or any game's) screenshots folder: "
                    "friendly renames, year/place sorting, duplicate reports, "
                    "and a static HTML album. Copies only — never touches sources.",
    )
    parser.add_argument("--version", action="version",
                        version=f"ffxiv-album {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scan", help="peek at a folder: how many shots, where dates came from")
    p.add_argument("src")
    p.set_defaults(func=_cmd_scan)

    p = sub.add_parser("organize", help="copy shots into DEST/Year/Place/ and (re)build captions.csv")
    p.add_argument("src", help="source folder with raw screenshots")
    p.add_argument("dest", help="destination library folder")
    p.add_argument("--tags", help="CSV of date-range -> place rows (start_date,end_date,place)")
    p.add_argument("--dry-run", action="store_true", help="show the plan, copy nothing")
    p.set_defaults(func=_cmd_organize)

    p = sub.add_parser("dedupe", help="report byte-identical duplicate screenshots (read-only)")
    p.add_argument("folder", help="folder to scan recursively")
    p.add_argument("--csv", help="where to write duplicates.csv (default: FOLDER/duplicates.csv)")
    p.set_defaults(func=_cmd_dedupe)

    p = sub.add_parser("album", help="build a static HTML album from a library's captions.csv")
    p.add_argument("library", help="organized library folder containing captions.csv")
    p.add_argument("--out", help="output HTML path (default: LIBRARY/album.html)")
    p.add_argument("--embed", action="store_true",
                   help="base64-embed images into one self-contained HTML file")
    p.set_defaults(func=_cmd_album)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
