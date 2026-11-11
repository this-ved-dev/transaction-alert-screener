"""Seeded label-blind pair cases for R12; all fields use the canonical schema."""

from datetime import datetime, time, timedelta
from decimal import Decimal

import polars as pl


def inject(df: pl.DataFrame, rng, n: int = 10) -> tuple[pl.DataFrame, list[dict]]:
    if n < 0:
        raise ValueError("n must be nonnegative")
    if n == 0:
        return df, []
    day = df["business_date"].drop_nulls().max()
    if day is None:
        raise ValueError("Injection requires a dated canonical frame")
    existing = set(df["entry_id"].to_list()) | set(df["cif_id"].to_list())
    rows, cases = [], []
    for _ in range(n):
        while True:
            token = f"R12-{rng.getrandbits(128):032x}"
            if token not in existing and not any(f"{token}-{i}" in existing for i in range(3)):
                break
        existing.add(token)
        ids = []
        for i in range(3):
            booked, entry_id = day - timedelta(days=2 - i), f"{token}-{i}"
            ids.append(entry_id)
            row = dict.fromkeys(df.columns)
            row.update(
                entry_id=entry_id,
                account_id=f"{token}-A",
                cif_id=token,
                amount=Decimal(rng.randint(4000, 4500)),
                currency="USD",
                credit_debit="DBIT",
                is_reversal=False,
                status="BOOK",
                booking_ts=datetime.combine(booked, time(12)),
                value_date=booked,
                business_date=booked,
                btc_domain="PMNT",
                btc_family="ICDT",
                btc_subfamily="ATXN",
                channel="ONLINE",
                source_message="injected",
                debtor_account=f"{token}-A",
                creditor_account=f"{token}-B",
                raw_ref=f"injected:r12:{entry_id}",
            )
            rows.append(row)
        cases.append(
            {
                "rule_id": "r12",
                "customer_id": token,
                "business_day": day.isoformat(),
                "entry_ids": ids,
                "note": "Three sub-$10k payments to one beneficiary, total >$10k",
            }
        )
    return pl.concat([df, pl.DataFrame(rows, schema=df.schema)]), cases
