"""Execute the real SQL against canonical Arrow fixtures; no engine or database required."""

import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import duckdb
import jinja2
import polars as pl
import pyarrow as pa
import pytest
import yaml

from rules.r10_round_dollar.inject import inject
from screener import schema
from screener.adapters import fixtures

HERE = Path(__file__).parent
RULE = yaml.safe_load((HERE / "rule.yaml").read_text())
DAY = date(2023, 7, 14)


def run(table, day=DAY):
    sql = (
        jinja2.Environment(undefined=jinja2.StrictUndefined)
        .from_string((HERE / "rule.sql").read_text())
        .render(params=RULE["params"], asof=day.isoformat())
    )
    with duckdb.connect() as con:
        con.register("entries", table)
        result = con.sql(sql)
        assert tuple(result.columns) == schema.HIT_COLUMNS
        return [dict(zip(result.columns, row, strict=True)) for row in result.fetchall()]


def entries(count=5, **changes):
    base = fixtures.generate().slice(0, 1).to_pylist()[0]
    rows = [
        base
        | {
            "entry_id": f"R{i}",
            "cif_id": "C1",
            "account_id": f"A{i % 2}",
            "business_date": DAY,
            "amount": Decimal("2000.00"),
            "currency": "USD",
            "credit_debit": "DBIT",
            "status": "BOOK",
            "is_reversal": False,
            "btc_family": "ICDT",
            "btc_subfamily": "ATXN",
            "channel": "ONLINE",
        }
        | changes
        for i in range(count)
    ]
    return pa.Table.from_pylist(rows, schema=schema.ENTRY)


def test_five_entries_across_accounts_consolidate_to_customer_hit():
    (hit,) = run(entries())
    assert (hit["customer_id"], hit["account_id"], hit["group_key"]) == ("C1", None, "C1")
    assert hit["matched_txn_ids"] == [f"R{i}" for i in range(5)]
    assert json.loads(hit["computed_values"])["entry_count"] == 5


@pytest.mark.parametrize(
    "count,amount,fires",
    [
        (4, "2000.00", False),
        (5, "2000.00", True),
        (5, "2000.01", False),
        (5, "1000.00", False),
        (5, "3000.00", True),
    ],
)
def test_count_amount_and_exact_multiple_boundaries(count, amount, fires):
    assert bool(run(entries(count, amount=Decimal(amount)))) == fires


@pytest.mark.parametrize(
    "family,subfamily,channel",
    [
        ("CNTR", "CDPT", "TELLER"),
        ("CNTR", "CWDL", "TELLER"),
        ("CCRD", "CWDL", "ATM"),
    ],
)
def test_teller_and_atm_cash_excluded(family, subfamily, channel):
    assert not run(entries(btc_family=family, btc_subfamily=subfamily, channel=channel))


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "PDNG"},
        {"is_reversal": True},
        {"currency": "EUR"},
    ],
)
def test_pending_reversed_or_foreign_currency_entries_excluded(changes):
    assert not run(entries(**changes))


@pytest.mark.parametrize("age,fires", [(0, True), (29, True), (30, False), (-1, False)])
def test_thirty_calendar_dates_include_both_endpoints(age, fires):
    assert bool(run(entries(business_date=DAY - timedelta(days=age)))) == fires


def test_customer_isolation_and_non_cash_card_entries():
    assert run(entries(btc_family="CCRD", btc_subfamily="POSD", channel="POS"))
    split = entries().to_pylist()
    split[-1]["cif_id"] = "C2"
    assert not run(pa.Table.from_pylist(split, schema=schema.ENTRY))


def test_seeded_injection_is_valid_label_blind_and_recalls_all_cases():
    baseline = schema.validate(fixtures.generate())[0]
    df = pl.from_arrow(baseline)
    injected, cases = inject(df, random.Random(36))
    again, key = inject(df, random.Random(36))
    assert injected.equals(again) and cases == key
    relabelled, _ = inject(
        df.with_columns(pl.lit("do not read").alias("typology_label")), random.Random(36)
    )
    assert injected.tail(50).equals(relabelled.tail(50))
    valid, rejected = schema.validate(injected.to_arrow().cast(schema.ENTRY))
    assert not rejected
    hits = {h["customer_id"]: h for h in run(valid, date.fromisoformat(cases[0]["business_day"]))}
    caught = [
        c
        for c in cases
        if c["customer_id"] in hits
        and set(c["entry_ids"]) <= set(hits[c["customer_id"]]["matched_txn_ids"])
    ]
    assert len(caught) / len(cases) >= 0.9
    assert len(caught) == len(cases) == 10


def test_injector_zero_and_invalid_case_counts():
    df = pl.from_arrow(schema.validate(fixtures.generate())[0])
    same, cases = inject(df, random.Random(36), 0)
    assert same.equals(df) and cases == []
    with pytest.raises(ValueError):
        inject(df, random.Random(36), -1)
    with pytest.raises(ValueError):
        inject(df.head(0), random.Random(36))
