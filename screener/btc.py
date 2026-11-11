"""ISO 20022 BankTransactionCode taxonomy: the permitted triplets and our tran-code map.

``data/reference/iso20022/btc_codification.csv`` holds every permitted Domain/Family/SubFamily
combination. It is derived with ``refresh()`` from ISO's codification spreadsheet (downloaded by
``data/reference/fetch_lists.sh``) and committed, so tests and CI run without the download.
"""

from __future__ import annotations

import csv
from functools import cache
from itertools import product
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[1] / "data" / "reference"
CODIFICATION = REFERENCE / "iso20022" / "btc_codification.csv"
XLSX = REFERENCE / "iso20022" / "BTC_Codification_21March2024.xlsx"
TRAN_CODE_MAP = REFERENCE / "tran_code_map.csv"


@cache
def triplets() -> frozenset[tuple[str, str, str]]:
    with CODIFICATION.open(newline="") as f:
        return frozenset((r["domain"], r["family"], r["subfamily"]) for r in csv.DictReader(f))


def is_valid(domain: str, family: str, subfamily: str) -> bool:
    return (domain, family, subfamily) in triplets()


def tran_code_combos() -> list[dict]:
    """Expand ``tran_code_map.csv`` into concrete (direction, triplet, proprietary, channel) rows.

    ``A|B`` in direction and family pair up by position (CRDT↔RCDT, DBIT↔ICDT); ``A|B`` in
    subfamily or proprietary multiplies. Rows without a family (layout still TBD) are skipped.
    """
    lines = (line for line in TRAN_CODE_MAP.open(newline="") if not line.startswith("#"))
    combos: dict[tuple, dict] = {}
    for r in csv.DictReader(lines):
        if not r["btc_family"]:
            continue
        directions = r["direction"].split("|")
        families = r["btc_family"].split("|")
        if len(families) == 1:
            families *= len(directions)
        for (direction, family), sub, prop in product(
            zip(directions, families, strict=True),
            r["btc_subfamily"].split("|"),
            r["btc_proprietary"].split("|"),
        ):
            c = {
                "direction": direction,
                "domain": r["btc_domain"],
                "family": family,
                "subfamily": sub,
                "proprietary": prop or None,
                "channel": r["channel"],
                "cash": r["cash_flag"] == "true",
            }
            combos.setdefault(tuple(c.values()), c)
    return list(combos.values())


def refresh(xlsx: Path = XLSX, out: Path = CODIFICATION) -> int:
    """Rebuild the committed CSV from ISO's spreadsheet; returns the row count.

    Needs DuckDB's ``excel`` extension, which DuckDB downloads on first use.
    """
    import duckdb  # noqa: PLC0415  (only this maintenance path needs it)

    con = duckdb.connect()
    con.execute("INSTALL excel; LOAD excel")
    raw = con.execute(
        "SELECT D, E, F FROM read_xlsx(?, header = false, all_varchar = true, "
        "range = 'A4:F5000') WHERE D IS NOT NULL",
        [str(xlsx)],
    ).fetchall()
    # ISO pads some codes with non-breaking spaces ('POSC\xa0'); str.strip() removes them
    rows = sorted({tuple(v.strip() for v in r) for r in raw})
    with out.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["domain", "family", "subfamily"])
        w.writerows(rows)
    return len(rows)
