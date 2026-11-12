"""Seeded label-blind quiet-account pass-through cases for canonical fixtures."""

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
            token = f"R05-{rng.getrandbits(128):032x}"
            if token not in existing and not any(f"{token}-{i}" in existing for i in range(3)):
                break
        existing.add(token)
        # Establish the full observation horizon without giving this quiet account activity.
        for i, age in enumerate((100, 0, 0)):
            day_i = day - timedelta(days=age)
            row = dict.fromkeys(df.columns)
            inbound = i == 1
            account = f"{token}-history" if i == 0 else f"{token}-A"
            row.update(
                entry_id=f"{token}-{i}",
                account_id=account,
                cif_id=account,
                amount=Decimal(1 if i == 0 else 5000 if inbound else 4000),
                currency="USD",
                credit_debit="CRDT" if inbound else "DBIT",
                is_reversal=False,
                status="BOOK",
                booking_ts=datetime.combine(day_i, time(10 if inbound else 11)),
                value_date=day_i,
                business_date=day_i,
                btc_domain="PMNT",
                btc_family="ICDT",
                btc_subfamily="ATXN",
                channel="ONLINE",
                source_message="injected",
                debtor_account=f"{token}-origin" if inbound else account,
                creditor_account=account if inbound else f"{token}-beneficiary",
                raw_ref=f"injected:r05:{token}-{i}",
            )
            rows.append(row)
        cases.append(
            {
                "rule_id": "r05",
                "customer_id": f"{token}-A",
                "business_day": day.isoformat(),
                "entry_ids": [f"{token}-1", f"{token}-2"],
                "note": "Quiet account: $5,000 in, $4,000 to another party one hour later",
            }
        )
    return pl.concat([df, pl.DataFrame(rows, schema=df.schema)]), cases
