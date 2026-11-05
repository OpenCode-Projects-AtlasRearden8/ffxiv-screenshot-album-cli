import csv
from pathlib import Path

from ffxiv_album.dedupe import collect_images, find_duplicates, write_report


def _mk(root: Path, name: str, blob: bytes):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(blob)
    return p


class TestFindDuplicates:
    def test_identical_files_grouped(self, tmp_path):
        a = _mk(tmp_path, "2021/ffxiv_20210904_213254.png", b"\x89PNG Bethlehem")
        b_ = _mk(tmp_path, "2021/copy of same.png", b"\x89PNG Bethlehem")
        c = _mk(tmp_path, "2021/different.png", b"\x89PNG Baroque")
        groups = find_duplicates([a, b_, c])
        assert len(groups) == 1
        assert {a, b_} <= set(groups[0])

    def test_unique_files_no_groups(self, tmp_path):
        a = _mk(tmp_path, "a.png", b"one")
        b_ = _mk(tmp_path, "b.png", b"two")
        assert find_duplicates([a, b_]) == []

    def test_empty_list(self):
        assert find_duplicates([]) == []


class TestReport:
    def test_csv_rows(self, tmp_path):
        a = _mk(tmp_path, "a.png", b"dup")
        b_ = _mk(tmp_path, "b.png", b"dup")
        c = _mk(tmp_path, "c.png", b"orig")
        groups = find_duplicates([a, b_, c])
        out = tmp_path / "dupes.csv"
        write_report(out, groups)
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        assert len(rows) == 2
        assert all(r["duplicate_group"] == "1" for r in rows)
        assert {Path(r["file_path"]).name for r in rows} == {"a.png", "b.png"}
        assert rows[0]["size_bytes"] == "3"
        assert len(rows[0]["sha256"]) == 64


class TestCollect:
    def test_collects_images_recursively(self, tmp_path):
        _mk(tmp_path, "2021/x.png", b"x")
        _mk(tmp_path, "2021/Ishgard/y.jpg", b"y")
        (tmp_path / "captions.csv").write_text("filename\n", encoding="utf-8")
        (tmp_path / "notes.txt").write_text("t", encoding="utf-8")
        names = {p.name for p in collect_images(tmp_path)}
        assert names == {"x.png", "y.jpg"}
