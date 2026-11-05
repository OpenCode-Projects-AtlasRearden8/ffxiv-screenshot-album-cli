from pathlib import Path

from ffxiv_album.album import build_album
from ffxiv_album.organizer import organize


def _make_library(tmp_path: Path, embed: bool = False) -> tuple[Path, Path]:
    src = tmp_path / "raw"
    src.mkdir()
    (src / "ffxiv_20210904_213254.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"imgdata" * 10)
    (src / "ffxiv_20220122_012259.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"moredata" * 10)
    tags = tmp_path / "tags.csv"
    tags.write_text(
        "start_date,end_date,place\n2021-09-04,2021-09-10,Ishgard\n*,Home\n",
        encoding="utf-8",
    )
    lib = tmp_path / "lib"
    organize(src, lib, rules=tags)
    (lib / "captions.csv").write_text(
        "filename,year,place,caption,favorite\n"
        "2021-09-04_213254.png,2021,Ishgard,Dawn over the Firmament,1\n"
        "2022-01-22_012259.png,2022,Home,cozy,1\n",
        encoding="utf-8",
    )
    out = lib / "album.html"
    build_album(lib, out, embed=embed)
    text = out.read_text(encoding="utf-8")
    return lib, text


class TestAlbum:
    def test_written_and_has_captions(self, tmp_path):
        lib, text = _make_library(tmp_path)
        assert "Dawn over the Firmament" in text
        assert "Ishgard" in text
        assert "2021" in text and "2022" in text

    def test_links_to_real_images(self, tmp_path):
        _, text = _make_library(tmp_path)
        assert "2021/Ishgard/2021-09-04_213254.png" in text

    def test_self_contained_and_no_cdn(self, tmp_path):
        _, text = _make_library(tmp_path)
        assert "cdn" not in text.lower()
        assert "http://" not in text and "https://" not in text
        assert "<script>" in text and "<style>" in text

    def test_embed_bakes_images_in(self, tmp_path):
        _, text = _make_library(tmp_path, embed=True)
        assert "data:image/png;base64," in text
        assert "Dawn over the Firmament" in text

    def test_lightbox_ready(self, tmp_path):
        _, text = _make_library(tmp_path)
        assert "lightbox" in text and "Escape" in text
