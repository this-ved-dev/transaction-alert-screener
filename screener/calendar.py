"""Business-day mapping: weekend and US-holiday roll-forward (posting date).

Cash booked on Saturday, Sunday or a Federal Reserve holiday posts on the next
weekday that is not a holiday. Source: ``data/reference/holidays_us.csv``.
"""

from __future__ import annotations

import csv
from collections.abc import Set
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOLIDAYS = ROOT / "data" / "reference" / "holidays_us.csv"


@lru_cache(maxsize=4)
def load_holidays(path: str | Path = DEFAULT_HOLIDAYS) -> frozenset[date]:
    """Load holiday dates from a CSV with a ``date`` column (ISO)."""
    p = Path(path)
    with p.open(newline="") as f:
        return frozenset(date.fromisoformat(row["date"]) for row in csv.DictReader(f))


def business_day(d: date, holidays: Set[date] | None = None) -> date:
    """Roll ``d`` forward to the next business day (Mon–Fri, not a holiday)."""
    hol = load_holidays() if holidays is None else holidays
    while d.weekday() >= 5 or d in hol:
        d += timedelta(days=1)
    return d


def is_business_day(d: date, holidays: Set[date] | None = None) -> bool:
    hol = load_holidays() if holidays is None else holidays
    return d.weekday() < 5 and d not in hol
