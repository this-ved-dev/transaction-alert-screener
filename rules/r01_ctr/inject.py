"""Seeded, label-blind CTR days: one isolated customer per case, over $10,000 in one direction."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from decimal import Decimal

import polars as pl

# note, legs: (direction, family, subfamily, channel, account, branch, min_usd, max_usd).
# Split legs stay at or under $10,000 each, so only the customer-day total catches them.
CASES = (
    ("one teller deposit", [("CRDT", "CNTR", "CDPT", "TELLER", "A", "BR001", 10_001, 25_000)]),
    (
        "deposits split across two accounts",
        [
            ("CRDT", "CNTR", "CDPT", "TELLER", "A", "BR001", 5_001, 9_999),
            ("CRDT", "CNTR", "CDPT", "TELLER", "B", "BR001", 5_001, 9_999),
        ],
    ),
    (
        "deposits split across two branches",
        [
            ("CRDT", "CNTR", "CDPT", "TELLER", "A", "BR001", 5_001, 9_999),
            ("CRDT", "CNTR", "CDPT", "TELLER", "A", "BR002", 5_001, 9_999),
        ],
    ),
    (
        "teller and ATM cash out",
        [
            ("DBIT", "CNTR", "CWDL", "TELLER", "A", "BR001", 9_401, 9_999),
            ("DBIT", "CCRD", "CWDL", "ATM", "A", None, 600, 1_000),
        ],
    ),
    (
        "night drop the evening before",
        [("CRDT", "CNTR", "CDPT", "NIGHT_DROP", "A", "BR003", 10_001, 25_000)],
    ),
)


def inject(df: pl.DataFrame, rng, n: int = 5) -> tuple[pl.DataFrame, list[dict]]:
    """Append n CTR customer-days on the frame's last business day, cycling through CASES."""
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n == 0:
        return df, []
    day = df["business_date"].drop_nulls().max() if not df.is_empty() else None
    if day is None:
        raise ValueError("Injection needs at least one dated canonical entry")
    existing = set(df["entry_id"].to_list()) | set(df["cif_id"].to_list())
    rows, cases = [], []
    for i in range(n):
        note, legs = CASES[i % len(CASES)]
        while (token := f"R01-{rng.getrandbits(128):032x}") in existing:
            pass
        existing.add(token)
        ids = []
        for j, (direction, family, sub, channel, acct, branch, lo, hi) in enumerate(legs):
            entry_id, account = f"{token}-{j}", f"{token}-{acct}"
            booked = day - timedelta(days=1) if channel == "NIGHT_DROP" else day
            ids.append(entry_id)
            row = dict.fromkeys(df.columns)
            row.update(
                entry_id=entry_id,
                account_id=account,
                cif_id=token,
                amount=Decimal(rng.randint(lo, hi)),
                currency="USD",
                credit_debit=direction,
                is_reversal=False,
                status="BOOK",
                booking_ts=datetime.combine(booked, time(21 if channel == "NIGHT_DROP" else 12)),
                value_date=day,
                business_date=day,
                btc_domain="PMNT",
                btc_family=family,
                btc_subfamily=sub,
                channel=channel,
                branch_id=branch,
                creditor_account=account if direction == "CRDT" else None,
                debtor_account=account if direction == "DBIT" else None,
                source_message="injected",
                raw_ref=f"injected:r01:{entry_id}",
            )
            rows.append(row)
        cases.append(
            {
                "rule_id": "r01",
                "customer_id": token,
                "business_day": day.isoformat(),
                "entry_ids": ids,
                "note": f"CTR candidate: {note}, over $10,000 in one direction",
            }
        )
    return pl.concat([df, pl.DataFrame(rows, schema=df.schema)]), cases
