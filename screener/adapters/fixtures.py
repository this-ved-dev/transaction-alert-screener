"""Synthetic fixture: 2,000 canonical entries from a fixed seed (``screener fixtures``).

Covers every combination in data/reference/tran_code_map.csv, plants one r00 positive on DEMO_DAY
(one customer, two accounts) and ends with rows ``schema.validate`` must reject, so quarantine is
exercised. Every name and number is invented; nothing comes from SAML-D or a real customer.
"""

from __future__ import annotations

import csv
import hashlib
import random
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from screener import btc
from screener.schema import ENTRY

DATA = Path(__file__).resolve().parents[2] / "data"
OUT = DATA / "fixtures" / "fixture.parquet"
SEED = 20261111
ROWS = 2000
START, END = date(2023, 1, 3), date(2023, 7, 31)  # longer than R04's 180 idle days
DEMO_DAY = date(2023, 7, 14)  # CI and the demo run `screener run --day 2023-07-14`
CUSTOMERS, SECOND_ACCOUNTS = 200, 40  # the first 40 customers hold two accounts
BRANCHES = ("BR001", "BR002", "BR003", "BR004", "BR005")
OUR_AGENT = {"routing": "999999999", "bic": None, "country": "US"}
XB_COUNTRIES = ("CA", "GB", "IN", "MX", "AE", "NG", "TR", "IR")  # includes country_risk.csv rows
AMOUNTS = {"WIRE_ROOM": (1_000, 50_000), "POS": (5, 500), "MOBILE": (10, 1_000), "SYSTEM": (1, 35)}
MCCS = ("5411", "5541", "5812", "5999")
HOLIDAYS = {
    date.fromisoformat(r["date"])
    for r in csv.DictReader((DATA / "reference" / "holidays_us.csv").open())
}
MEMOS = ["rent", "invoice 2231", "payroll", "gift", "car repair"] + [
    r["memo"] for r in csv.DictReader((DATA / "fixtures" / "hostile_memos.csv").open())
]
BREAKS = (  # one field each that schema.validate must reject
    ("account_id", None),
    ("amount", Decimal("0.00")),
    ("credit_debit", "CR"),
    ("currency", "US"),
    ("channel", "FAX"),
    ("btc_subfamily", "ZZZZ"),
)


def business_date(d: date) -> date:
    # shortcut: local weekend/holiday roll-forward; use screener.calendar once TRA-21 lands
    while d.weekday() >= 5 or d in HOLIDAYS:
        d += timedelta(days=1)
    return d


def _notes(dollars: int) -> list[dict]:
    notes = []
    for d in (100, 50, 20, 10, 5, 1):
        count, dollars = divmod(dollars, d)
        if count:
            notes.append({"denomination": Decimal(d), "count": count})
    return notes


def _entry(rng, n, combo, cif, account, home, day, amount=None) -> dict:
    channel, sub, crdt = combo["channel"], combo["subfamily"], combo["direction"] == "CRDT"
    if amount is None and combo["cash"]:
        amount = Decimal(rng.randrange(20, 1_000 if channel == "ATM" else 9_800, 20))
    elif amount is None:
        lo, hi = AMOUNTS.get(channel, (50, 5_000))
        amount = Decimal(rng.randint(lo * 100, hi * 100)) / 100
    me = {"name": f"Customer {cif[3:]}", "cif_id": cif, "country": "US"}
    other = other_account = other_agent = None
    if not combo["cash"] and channel != "SYSTEM":
        k, xb = rng.randrange(1_000), sub == "XBCT"
        country = rng.choice(XB_COUNTRIES) if xb else "US"
        other = {"name": f"Counterparty {k:03d}", "cif_id": None, "country": country}
        other_account = f"EXT{k:06d}"
        other_agent = {
            "routing": None if xb else f"{rng.randrange(10**9):09d}",
            "bic": f"FXBK{country}XX" if xb else None,
            "country": country,
        }
    at_branch = channel in ("TELLER", "BRANCH", "NIGHT_DROP")
    third_party = {"name": f"Conductor {rng.randrange(100):02d}", "cif_id": None, "country": "US"}
    return {
        "entry_id": f"FX{n:06d}",
        "account_id": account,
        "amount": amount,
        "currency": "USD",
        "credit_debit": combo["direction"],
        "is_reversal": rng.random() < 0.01,
        "status": "BOOK",
        "booking_ts": datetime.combine(day, datetime.min.time())
        + timedelta(seconds=rng.randrange(6 * 3600, 22 * 3600)),
        "value_date": day,
        "business_date": business_date(day),
        "btc_domain": combo["domain"],
        "btc_family": combo["family"],
        "btc_subfamily": sub,
        "btc_proprietary": combo["proprietary"],
        "channel": channel,
        "instrument_refs": {
            "end_to_end_id": f"E2E{n:06d}" if sub == "DMCT" and channel != "WIRE_ROOM" else None,
            "uetr": str(uuid.UUID(int=rng.getrandbits(128), version=4))
            if channel == "WIRE_ROOM"
            else None,
            "trace_no": f"{rng.randrange(10**15):015d}" if sub == "ATXN" else None,
            "cheque_no": str(rng.randint(1000, 9999)) if sub == "CCHQ" else None,
        },
        "debtor": other if crdt else me,
        "creditor": me if crdt else other,
        "debtor_account": other_account if crdt else account,
        "creditor_account": account if crdt else other_account,
        "debtor_agent": other_agent if crdt else OUR_AGENT,
        "creditor_agent": OUR_AGENT if crdt else other_agent,
        "branch_id": (home if rng.random() < 0.8 else rng.choice(BRANCHES)) if at_branch else None,
        "conductor": (me if rng.random() < 0.95 else third_party)
        if combo["cash"] and at_branch
        else None,
        "cif_id": cif,
        "purpose": None,
        "memo": rng.choice(MEMOS) if rng.random() < 0.1 else None,
        "cash_detail": _notes(int(amount)) if sub == "CDPT" else None,
        "card_detail": {
            "masked_pan": f"************{rng.randrange(10_000):04d}",
            "mcc": "6011" if channel == "ATM" else rng.choice(MCCS),
            "terminal_id": f"T{rng.randrange(100_000):05d}",
        }
        if combo["family"] == "CCRD"
        else None,
        "source_message": "fixture",
        "raw_ref": f"fixture:{n}",
        "typology_label": None,
    }


def generate(seed: int = SEED, rows: int = ROWS) -> pa.Table:
    rng = random.Random(seed)  # noqa: S311  (reproducible synthetic data, not crypto)
    combos = btc.tran_code_combos()
    teller_cash_in = next(
        c for c in combos if c["subfamily"] == "CDPT" and c["channel"] == "TELLER"
    )
    accounts = [(f"CIF{i:05d}", f"ACC{i:05d}") for i in range(1, CUSTOMERS + 1)]
    accounts += [(f"CIF{i:05d}", f"ACC{CUSTOMERS + i:05d}") for i in range(1, SECOND_ACCOUNTS + 1)]
    home = {cif: rng.choice(BRANCHES) for cif, _ in accounts}
    days = [START + timedelta(d) for d in range((END - START).days + 1)]

    # r00 positive: one customer, two accounts, $10,500 teller cash in on DEMO_DAY
    records = [
        _entry(
            rng,
            0,
            teller_cash_in,
            "CIF00001",
            "ACC00001",
            home["CIF00001"],
            DEMO_DAY,
            Decimal(6000),
        ),
        _entry(
            rng,
            1,
            teller_cash_in,
            "CIF00001",
            "ACC00201",
            home["CIF00001"],
            DEMO_DAY,
            Decimal(4500),
        ),
    ]
    for i in range(rows - len(records) - len(BREAKS)):
        combo = combos[i] if i < len(combos) else rng.choice(combos)  # every combo at least once
        cif, account = rng.choice(accounts)
        records.append(_entry(rng, len(records), combo, cif, account, home[cif], rng.choice(days)))
    for field, value in BREAKS:
        n = len(records)
        cif, account = rng.choice(accounts)
        row = _entry(rng, n, rng.choice(combos), cif, account, home[cif], rng.choice(days))
        records.append(row | {field: value, "raw_ref": f"fixture:reject:{n}"})
    return pa.Table.from_pylist(records, schema=ENTRY)


def write(path: Path = OUT, seed: int = SEED) -> str:
    """Write the fixture Parquet and return its SHA-256 (the same on every run of one seed)."""
    pq.write_table(generate(seed), path, compression="zstd")
    return hashlib.sha256(path.read_bytes()).hexdigest()
