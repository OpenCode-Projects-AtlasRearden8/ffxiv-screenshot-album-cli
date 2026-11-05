import datetime as dt

from ffxiv_album.rename import friendly_stem, is_friendly, make_unique, plan_renames
from ffxiv_album.scanner import Shot, parse_stamp


def _shot(name: str, taken="auto"):
    """Build a Shot; taken='auto' parses the date from the name like scan() does."""
    when = parse_stamp(name) if taken == "auto" else taken
    if when == "mtime":
        when = None
    return Shot(path=__import__("pathlib").Path(name), taken=when,
                source="filename" if when else "unknown", size=0)


class TestParseStamp:
    def test_windows_ffxiv_name(self):
        got = parse_stamp("ffxiv_20210904_213254.png")
        assert got == dt.datetime(2021, 9, 4, 21, 32, 54)

    def test_ps5_name(self):
        got = parse_stamp("s2d_20210904_213254_001.png")
        assert got == dt.datetime(2021, 9, 4, 21, 32, 54)

    def test_mac_name(self):
        assert parse_stamp("ffxiv_20220122_012259.png") == dt.datetime(2022, 1, 22, 1, 22, 59)

    def test_dated_name_with_dashes(self):
        assert parse_stamp("2021-09-04_213254.png") == dt.datetime(2021, 9, 4, 21, 32, 54)

    def test_pretty_name(self):
        assert parse_stamp("2021-09-04 213254.jpg") == dt.datetime(2021, 9, 4, 21, 32, 54)

    def test_no_stamp_asks_for_mtime(self):
        assert parse_stamp("Screenshot_23.png") == "mtime"

    def test_bad_date_asks_for_mtime(self):
        assert parse_stamp("ffxiv_20211399_999999.png") == "mtime"


class TestFriendlyName:
    def test_friendly_from_filename_date(self):
        s = _shot("ffxiv_20210904_213254.png")
        assert friendly_stem(s) == "2021-09-04_213254"

    def test_friendly_from_midnight(self):
        s = _shot("s2d_20210101_000000_000.png", dt.datetime(2021, 1, 1))
        assert friendly_stem(s) == "2021-01-01_000000"

    def test_no_date_keeps_original_stem(self):
        s = _shot("gpose_bonus.png", taken=None)
        assert friendly_stem(s) == "gpose_bonus"

    def test_is_friendly(self):
        assert is_friendly("2021-09-04_213254.png")
        assert is_friendly("2021-09-04_213254-2.png")
        assert not is_friendly("ffxiv_20210904_213254.png")
        assert not is_friendly("holiday.png")

    def test_extension_preserved(self):
        s = _shot("ffxiv_20210904_213254.jpg")
        from ffxiv_album.rename import proposed_name

        assert proposed_name(s) == "2021-09-04_213254.jpg"


class TestMakeUnique:
    def test_no_collision(self):
        assert make_unique("2021-09-04_213254.png", set()) == "2021-09-04_213254.png"

    def test_second_collision_gets_dash2(self):
        taken = set()
        assert make_unique("2021-09-04_213254.png", taken) == "2021-09-04_213254.png"
        assert make_unique("2021-09-04_213254.png", taken) == "2021-09-04_213254-2.png"
        assert make_unique("2021-09-04_213254.png", taken) == "2021-09-04_213254-3.png"

    def test_caseinsensitive(self):
        taken = set()
        assert make_unique("Shot.PNG", taken) == "Shot.PNG"
        assert make_unique("shot.png", taken) == "shot-2.png"

    def test_taken_trackable(self):
        taken: set[str] = set()
        first = make_unique("a.png", taken)
        assert "a.png" in taken


class TestPlanRenames:
    def test_ffxiv_names_map_to_friendly(self):
        plan = plan_renames(
            [
                _shot("ffxiv_20210904_213254.png"),
                _shot("s2d_20210904_213254_001.png"),
                _shot("s2e_20210904_213254_002.png"),
            ]
        )
        assert [n for _, n in plan] == [
            "2021-09-04_213254.png",
            "2021-09-04_213254-2.png",
            "2021-09-04_213254-3.png",
        ]

    def test_rerun_is_noop(self):
        shots = [_shot("2021-09-04_213254.png"), _shot("2021-09-04_213254-2.png")]
        plan = plan_renames(shots)
        assert [n for _, n in plan] == ["2021-09-04_213254.png", "2021-09-04_213254-2.png"]

    def test_distinct_dates_not_suffixed(self):
        plan = plan_renames(
            [
                _shot("ffxiv_20210904_213254.png"),
                _shot("ffxiv_20210904_213255.png"),
            ]
        )
        assert [n for _, n in plan] == [
            "2021-09-04_213254.png",
            "2021-09-04_213255.png",
        ]
