import csv
from pathlib import Path

from ffxiv_album.organizer import organize, read_captions, write_captions
from ffxiv_album.tags import load_tags, place_for


def _touch(path: Path, mtime=(2021, 9, 4, 21, 32, 54)):
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    import os

    stamp = __import__("datetime").datetime(*mtime).timestamp()
    os.utime(path, (stamp, stamp))


class TestTags:
    def test_range_row(self, tmp_path):
        tags = tmp_path / "tags.csv"
        tags.write_text("start_date,end_date,place\n2021-09-01,2021-09-30,Ishgard\n",
                        encoding="utf-8")
        rules = load_tags(tags)
        assert place_for(rules, _dt(2021, 9, 4)) == "Ishgard"
        assert place_for(rules, _dt(2021, 10, 1)) == "Unknown"

    def test_single_day_row(self, tmp_path):
        tags = tmp_path / "tags.csv"
        tags.write_text("start_date,end_date,place\n2021-09-01,,Home\n", encoding="utf-8")
        rules = load_tags(tags)
        assert place_for(rules, _dt(2021, 9, 1, 13, 0)) == "Home"
        assert place_for(rules, _dt(2021, 9, 2)) == "Unknown"

    def test_first_match_wins(self, tmp_path):
        tags = tmp_path / "tags.csv"
        tags.write_text(
            "start_date,end_date,place\n"
            "2021-09-01,2021-09-30,Ishgard\n"
            "2021-09-04,,Inn\n",
            encoding="utf-8",
        )
        assert place_for(load_tags(tags), _dt(2021, 9, 4)) == "Ishgard"

    def test_wildcard_catch_all(self, tmp_path):
        tags = tmp_path / "tags.csv"
        tags.write_text("start_date,end_date,place\n2021-01-01,2021-12-31,Ishgard\n*,,Adventures\n",
                        encoding="utf-8")
        assert place_for(load_tags(tags), _dt(2020, 1, 1)) == "Adventures"

    def test_none_datetime_is_unknown(self):
        assert place_for([], None) == "Unknown"


def _dt(*a):
    import datetime

    return datetime.datetime(*a)


class TestOrganize:
    def test_copies_into_year_place_folders(self, tmp_path):
        src = tmp_path / "raw"
        src.mkdir()
        (src / "ffxiv_20210904_213254.png").write_bytes(b"png-a")
        (src / "ffxiv_20210905_101010.png").write_bytes(b"png-b")
        tags = tmp_path / "tags.csv"
        tags.write_text("start_date,end_date,place\n2021-09-04,2021-09-10,Ishgard\n",
                        encoding="utf-8")
        lib = tmp_path / "lib"
        rows = organize(src, lib, rules=load_tags(tags))
        assert (lib / "2021" / "Ishgard" / "2021-09-04_213254.png").read_bytes() == b"png-a"
        assert (lib / "2021" / "Ishgard" / "2021-09-05_101010.png").exists()
        assert (lib / "captions.csv").exists()
        assert len(rows) == 2

    def test_source_untouched(self, tmp_path):
        src = tmp_path / "raw"
        src.mkdir()
        before = {p.name: p.read_bytes() for p in src.iterdir()}
        (src / "ffxiv_20210904_213254.png").write_bytes(b"keep me")
        before = (src / "ffxiv_20210904_213254.png").read_bytes()
        libs = organize(src, tmp_path / "lib")
        assert (src / "ffxiv_20210904_213254.png").read_bytes() == before
        assert sorted(p.name for p in src.iterdir()) == ["ffxiv_20210904_213254.png"]
        assert libs

    def test_dry_run_writes_nothing(self, tmp_path):
        src = tmp_path / "raw"
        src.mkdir()
        (src / "ffxiv_20210904_213254.png").write_bytes(b"png")
        lib = tmp_path / "lib"
        rows = organize(src, lib, dry_run=True)
        assert not lib.exists()
        assert len(rows) == 1

    def test_rerun_preserves_captions(self, tmp_path):
        src = tmp_path / "raw"
        src.mkdir()
        (src / "ffxiv_20210904_213254.png").write_bytes(b"png")
        lib = tmp_path / "lib"
        organize(src, lib)
        rows = read_captions(lib / "captions.csv")
        rows[0]["caption"] = "Gilded day"
        rows[0]["favorite"] = "1"
        write_captions(lib / "captions.csv", rows)

        (src / "ffxiv_20210905_101010.png").write_bytes(b"png2")
        organize(src, lib)
        rows = read_captions(lib / "captions.csv")
        assert rows[0]["caption"] == "Gilded day"
        assert rows[0]["favorite"] == "1"
        assert all(r["filename"] == "2021-09-04_213254.png" for r in rows[:1])
        assert len(rows) == 2

    def test_pages_new_file_gets_row(self, tmp_path):
        src = tmp_path / "raw"
        src.mkdir()
        (src / "s2d_20210904_213254_001.png").write_bytes(b"x")
        rows = organize(src, tmp_path / "lib")
        assert rows[0]["filename"] == "2021-09-04_213254.png"
        assert rows[0]["year"] == "2021"


class TestCaptionsCsv:
    def test_columns(self, tmp_path):
        lib = tmp_path / "lib"
        lib.mkdir()
        write_captions(lib / "captions.csv", [
            {"filename": "2021-09-04_213254.png", "year": "2021",
             "place": "Ishgard", "caption": "nice", "favorite": "1"},
        ])
        text = (lib / "captions.csv").read_text(encoding="utf-8")
        assert text.splitlines()[0] == "filename,year,place,caption,favorite"
        rows = read_captions(lib / "captions.csv")
        assert rows[0]["caption"] == "nice"
