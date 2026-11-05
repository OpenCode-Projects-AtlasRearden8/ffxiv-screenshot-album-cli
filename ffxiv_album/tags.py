"""Place tags: a tiny editable CSV that maps date ranges to places.

Expected columns (header required):

    start_date,end_date,place

* ``end_date`` empty means "just that one day".
* ``*`` in start_date means "everything unmatched so far" (a catch-all row).
* first matching row wins; unmatched files go to ``Unknown``.
"""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass


@dataclass
class TagRule:
    start: dt.date | None
    end: dt.date | None
    place: str


def _parse_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value or value == "*":
        return None
    return dt.date.fromisoformat(value)


def load_tags(path) -> list[TagRule]:
    rules: list[TagRule] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            place = (row.get("place") or "").strip()
            if not place:
                continue
            rules.append(
                TagRule(
                    start=_parse_date(row.get("start_date", "")),
                    end=_parse_date(row.get("end_date", "")),
                    place=place,
                )
            )
    for rule in rules:
        if rule.start is not None and rule.end is None:
            rule.end = rule.start  # empty end_date = that one day
    return rules


def _covers(rule: TagRule, day: dt.date) -> bool:
    if rule.start is None:  # wildcard/catch-all row
        return True
    if day < rule.start:
        return False
    if rule.end is not None and day > rule.end:
        return False
    return True


def place_for(rules: list[TagRule], when: dt.datetime | None) -> str:
    """Best place name for a shot taken at *when* (None -> Unknown)."""
    if when is None:
        return "Unknown"
    day = when.date()
    for rule in rules:
        if _covers(rule, day):
            return rule.place
    return "Unknown"
