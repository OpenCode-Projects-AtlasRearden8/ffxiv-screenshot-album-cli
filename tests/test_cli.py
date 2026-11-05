import io
import sys
from contextlib import redirect_stdout

from ffxiv_album.cli import main


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    return code, buf.getvalue()


class TestScan:
    def test_scan_counts(self, tmp_path):
        (tmp_path / "ffxiv_20210904_213254.png").write_bytes(b"a")
        (tmp_path / "weird.png").write_bytes(b"b")
        code, out = run(["scan", str(tmp_path)])
        assert code == 0
        assert "2 image(s)" in out

    def test_missing_folder(self, tmp_path):
        code, _ = run(["scan", str(tmp_path / "nope")])
        assert code == 2


class TestOrganizeCli:
    def test_dry_run_no_copies(self, tmp_path):
        src = tmp_path / "raw"
        src.mkdir()
        (src / "ffxiv_20210904_213254.png").write_bytes(b"a")
        code, out = run(["organize", str(src), str(tmp_path / "lib"), "--dry-run"])
        assert code == 0
        assert "Would copy" in out
        assert not (tmp_path / "lib").exists()

    def test_bad_tags_file_warns(self, tmp_path):
        src = tmp_path / "raw"
        src.mkdir()
        bad = tmp_path / "bad.csv"
        bad.write_text("no,columns,here\n1,2,3\n", encoding="utf-8")
        code, out = run([
            "organize", str(src), str(tmp_path / "lib"),
            "--tags", str(bad), "--dry-run",
        ])
        assert code == 0


class TestDedupeCli:
    def test_writes_report(self, tmp_path):
        (tmp_path / "a.png").write_bytes(b"dup")
        (tmp_path / "b.png").write_bytes(b"dup")
        (tmp_path / "c.png").write_bytes(b"orig")
        code, out = run(["dedupe", str(tmp_path)])
        assert code == 0
        assert "1 duplicate group(s)" in out
        assert (tmp_path / "duplicates.csv").exists()
        assert (tmp_path / "a.png").exists()

    def test_no_duplicates_no_report(self, tmp_path):
        (tmp_path / "a.png").write_bytes(b"only")
        code, out = run(["dedupe", str(tmp_path)])
        assert code == 0
        assert "no duplicates" in out
        assert not (tmp_path / "duplicates.csv").exists()


class TestAlbumCli:
    def test_requires_captions(self, tmp_path):
        code, _ = run(["album", str(tmp_path)])
        assert code == 2


class TestHelp:
    def test_help_works(self, capsys):
        try:
            main(["--help"])
        except SystemExit as e:
            assert e.code == 0
        out = capsys.readouterr().out
        assert "organize" in out and "dedupe" in out and "album" in out
