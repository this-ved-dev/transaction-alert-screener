"""Execute the real SQL against canonical Arrow fixtures; no engine or database required."""

import json
import random
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import duckdb
import jinja2
import polars as pl
import pyarrow as pa
import pytest
import yaml

from rules.r01_ctr.inject import CASES, inject
from screener import schema
from screener.adapters import fixtures

HERE = Path(__file__).parent
RULE = yaml.safe_load((HERE / "rule.yaml").read_text())
DAY = date(2023, 7, 14)  # a Friday
CASH_IN = {"credit_debit": "CRDT", "btc_family": "CNTR", "btc_subfamily": "CDPT"}
CASH_OUT = {"credit_debit": "DBIT", "btc_family": "CNTR", "btc_subfamily": "CWDL"}


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


def entries(*amounts, **changes):
    """One teller cash deposit per amount for customer C1 on DAY; changes apply to every row."""
    base = fixtures.generate().slice(0, 1).to_pylist()[0]
    rows = [
        base
        | {
            "entry_id": f"E{i}",
            "cif_id": "C1",
            "account_id": "A0",
            "branch_id": "BR001",
            "business_date": DAY,
            "amount": Decimal(amount),
            "currency": "USD",
            "status": "BOOK",
            "is_reversal": False,
            "btc_domain": "PMNT",
            "channel": "TELLER",
        }
        | CASH_IN
        | changes
        for i, amount in enumerate(amounts)
    ]
    return pa.Table.from_pylist(rows, schema=schema.ENTRY)


def table(*parts):
    return pa.concat_tables(parts)


def total(hit):
    return Decimal(str(json.loads(hit["computed_values"])["total"]))


@pytest.mark.parametrize("amount,fires", [("10000.00", False), ("10000.01", True)])
def test_threshold_is_strictly_above_ten_thousand(amount, fires):
    assert bool(run(entries(amount))) == fires


def test_two_accounts_of_one_customer_add_up_to_one_row():
    t = table(entries("6000.00"), entries("4000.01", entry_id="E9", account_id="A1"))
    (hit,) = run(t)
    assert (hit["customer_id"], hit["account_id"], hit["group_key"]) == ("C1", None, "CRDT:C1")
    assert hit["matched_txn_ids"] == ["E0", "E9"]
    assert total(hit) == Decimal("10000.01")


def test_two_branches_add_up():
    t = table(entries("6000.00"), entries("4000.01", entry_id="E9", branch_id="BR002"))
    assert [h["group_key"] for h in run(t)] == ["CRDT:C1"]


def test_other_customers_do_not_add_up():
    assert not run(table(entries("6000.00"), entries("6000.00", entry_id="E9", cif_id="C2")))


def test_cash_in_and_cash_out_are_never_netted():
    # $12,000 in and $5,000 out: cash in still fires at $12,000, not a net $7,000
    (hit,) = run(table(entries("6000.00", "6000.00"), entries("5000.00", entry_id="X", **CASH_OUT)))
    assert (hit["group_key"], total(hit)) == ("CRDT:C1", Decimal("12000.00"))
    # $6,000 each way is $12,000 of cash handled, but neither direction exceeds the threshold
    assert not run(table(entries("6000.00"), entries("6000.00", entry_id="X", **CASH_OUT)))


def test_both_directions_over_threshold_give_two_rows():
    out = entries("10000.01", entry_id="X", **CASH_OUT)
    hits = run(table(entries("10000.01"), out))
    assert sorted(h["group_key"] for h in hits) == ["CRDT:C1", "DBIT:C1"]


def test_atm_and_night_drop_cash_count():
    atm = entries("800.00", entry_id="X", **CASH_OUT | {"btc_family": "CCRD", "channel": "ATM"})
    (hit,) = run(table(entries("9500.00", **CASH_OUT), atm))
    assert hit["group_key"] == "DBIT:C1"
    assert run(entries("10000.01", channel="NIGHT_DROP"))


@pytest.mark.parametrize(
    "booked,business_day",
    [
        (date(2023, 7, 15), date(2023, 7, 17)),  # Saturday -> Monday
        (date(2023, 7, 16), date(2023, 7, 17)),  # Sunday -> Monday
        (date(2023, 7, 4), date(2023, 7, 5)),  # Independence Day -> Wednesday
    ],
)
def test_weekend_and_holiday_cash_rolls_forward(booked, business_day):
    rolled = fixtures.business_date(booked)
    assert rolled == business_day
    booked_ts = datetime.combine(booked, time(12))
    off_day = entries("6000.00", booking_ts=booked_ts, business_date=rolled)
    t = table(off_day, entries("4000.01", entry_id="E9", business_date=rolled))
    (hit,) = run(t, rolled)
    assert hit["business_day"] == business_day and total(hit) == Decimal("10000.01")
    assert not run(t, DAY)


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "PDNG"},
        {"is_reversal": True},
        {"currency": "EUR"},
        {"btc_family": "RCDT", "btc_subfamily": "XBCT", "channel": "WIRE_ROOM"},
        CASH_OUT | {"btc_family": "CCRD", "btc_subfamily": "POSD", "channel": "POS"},
        {"btc_family": "CNTR", "btc_subfamily": "FEES"},
        {"btc_domain": "ACMT", "btc_family": "MCOP", "btc_subfamily": "INTR", "channel": "SYSTEM"},
    ],
)
def test_pending_reversed_foreign_non_cash_and_fee_entries_excluded(changes):
    assert not run(entries("10000.01", **changes))


def test_seeded_injection_is_valid_label_blind_and_recalls_every_case():
    df = pl.from_arrow(schema.validate(fixtures.generate())[0])
    injected, cases = inject(df, random.Random(15))
    again, key = inject(df, random.Random(15))
    assert injected.equals(again) and cases == key
    relabelled, _ = inject(
        df.with_columns(pl.lit("do not read").alias("typology_label")), random.Random(15)
    )
    assert injected.tail(8).equals(relabelled.tail(8))
    valid, rejected = schema.validate(injected.to_arrow().cast(schema.ENTRY))
    assert not rejected
    hits = run(valid, date.fromisoformat(cases[0]["business_day"]))
    found = {(h["customer_id"], frozenset(h["matched_txn_ids"])) for h in hits}
    caught = [c for c in cases if (c["customer_id"], frozenset(c["entry_ids"])) in found]
    assert len(caught) == len(cases) == len(CASES)  # one of each variant in CASES


def test_injector_zero_and_invalid_case_counts():
    df = pl.from_arrow(schema.validate(fixtures.generate())[0])
    same, cases = inject(df, random.Random(15), 0)
    assert same.equals(df) and cases == []
    with pytest.raises(ValueError):
        inject(df, random.Random(15), -1)
    with pytest.raises(ValueError):
        inject(df.head(0), random.Random(15))


def test_rule_writes_to_the_ctr_list_not_the_alert_queue():
    assert RULE["output"] == "ctr_candidate"
