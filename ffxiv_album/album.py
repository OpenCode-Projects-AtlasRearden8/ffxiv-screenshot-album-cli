"""Build a browsable, offline-friendly static HTML album from captions.csv.

The album is a single self-contained ``album.html`` (one small stylesheet
and script inline, no CDN) that expects to sit *inside* the organized
library folder so it can show the real images by relative path. A
``--embed`` flag instead base64-encodes images into the HTML itself, so
you can email or ship the album as one file.
"""

from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path

from .dedupe import collect_images
from .organizer import read_captions

_CSS = """
:root{color-scheme:dark}
body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e8e6e3}
header{padding:24px 32px 8px}
h1{margin:0;font-size:1.5rem}
header p{margin:4px 0 0;color:#9aa0a6}
nav{padding:8px 32px 16px;display:flex;flex-wrap:wrap;gap:8px}
nav a{color:#7fb4ff;text-decoration:none;padding:2px 10px;border:1px solid #2a2f3a;border-radius:999px}
section{padding:0 32px}
h2{margin:24px 0 4px;font-size:1.15rem;color:#c9c5c1}
h3{margin:16px 0 4px;font-size:1rem;color:#9aa0a6;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
figure{margin:0;background:#171a21;border:1px solid #262b36;border-radius:10px;overflow:hidden;cursor:zoom-in}
figure img{display:block;width:100%;height:160px;object-fit:cover}
figcaption{padding:8px;font-size:.85rem;color:#c9c5c1}
figcaption .fav{color:#f5c518}
#lightbox{position:fixed;inset:0;background:rgba(0,0,0,.9);display:none;align-items:center;justify-content:center;flex-direction:column;padding:24px}
#lightbox.on{display:flex}
#lightbox img{max-width:92vw;max-height:78vh;border-radius:8px}
#lightbox figcaption{max-width:80vw;text-align:center;color:#d9d5d1;margin-top:10px;font-size:1rem}
footer{padding:32px;color:#6b7078;font-size:.8rem}
"""

_JS = """
function show(src,cap){var lb=document.getElementById('lightbox');
document.getElementById('lb_img').src=src;document.getElementById('lb_cap').textContent=cap;
lb.classList.add('on');}
function hide(){var lb=document.getElementById('lightbox');lb.classList.remove('on');
document.getElementById('lb_img').src='';}
document.addEventListener('keydown',function(e){if(e.key==='Escape')hide();});
"""


def _encode_image(path: Path) -> str | None:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    try:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        return None
    return f"data:{mime};base64,{data}"


def build_album(lib: Path, out: Path, embed: bool = False) -> Path:
    """Write *out* (album.html) describing the organized library at *lib*."""
    captions = read_captions(lib / "captions.csv")
    images = {p.name: p for p in collect_images(lib)}

    by_key: dict[tuple[str, str], list[dict]] = {}
    for row in captions:
        by_key.setdefault((row["year"], row["place"]), []).append(row)
    years = sorted({y for y, _ in by_key})

    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
             "<meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>FFXIV Album</title><style>", _CSS, "</style></head><body>",
             "<header><h1>FFXIV Album</h1>",
             f"<p>{sum(len(v) for v in by_key.values())} shots &middot; {len(years)} year(s) &middot; click any shot to enlarge &middot; Esc to close</p></header>",
             "<nav>", "".join(f"<a href='#{html.escape(y)}'>{html.escape(y)}</a>" for y in years), "</nav>"]

    for year in years:
        parts.append(f"<section id='{html.escape(year)}'><h2>{html.escape(year)}</h2>")
        places = sorted({pl for (y, pl) in by_key if y == year})
        for place in places:
            rows = sorted(by_key[(year, place)], key=lambda r: r["filename"])
            parts.append(f"<h3>{html.escape(place)}</h3><div class='grid'>")
            for row in rows:
                p = images.get(row["filename"])
                if p is None:
                    continue
                src = _encode_image(p) if embed else _rel_src(out, p)
                fav = "&#9733; " if row["favorite"] else ""
                cap = html.escape(f"{row['caption']}" or row["filename"])
                title = html.escape(row["filename"])
                parts.append(
                    "<figure onclick=\"show(" + _js_str(src) + "," + _js_str(row["caption"] or row["filename"]) + ")\" title='" + title + "'>"
                    f"<img src='{html.escape(src, quote=True)}' loading='lazy' alt='{cap}'>"
                    f"<figcaption>{fav}{cap}</figcaption></figure>"
                )
            parts.append("</div>")
        parts.append("</section>")

    parts.extend((
        "<div id='lightbox' onclick='hide()'><img id='lb_img' src='' alt=''>"
        "<figcaption id='lb_cap'></figcaption></div>"
        "<footer>Built with ffxiv-screenshot-album-cli &middot; "
        "Copyright (c) 2026 Asdale Dynamics, LLC &middot; MIT license. "
        "All screenshots remain the property of their players; FFXIV is &copy; Square Enix.</footer>"
        "<script>", _JS, "</script></body></html>",
    ))
    out.write_text("".join(parts), encoding="utf-8")
    return out


def _js_str(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _rel_src(out: Path, image: Path) -> str:
    try:
        return str(image.relative_to(out.parent)).replace("\\", "/")
    except ValueError:
        return _encode_image(image) or ""
