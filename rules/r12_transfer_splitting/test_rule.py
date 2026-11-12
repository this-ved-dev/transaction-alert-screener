"""Real R12 SQL, exercised without the pending engine or operational database."""

import json
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

import duckdb
import jinja2
import polars as pl
import pyarrow as pa
import pytest
import yaml

from rules.r12_transfer_splitting.inject import inject
from screener import schema
from screener.adapters import fixtures

HERE = Path(__file__).parent
DAY = date(2023, 7, 14)
RULE = yaml.safe_load((HERE / "rule.yaml").read_text())
BASE = fixtures.generate().slice(0, 1).to_pylist()[0]


def entry(i, *, sender="A", receiver="B", direction="DBIT", day=DAY, amount="4000", **changes):
    account = sender if direction == "DBIT" else receiver
    return (
        BASE
        | {
            "entry_id": f"R{i}",
            "account_id": account,
            "cif_id": f"C:{account}",
            "amount": Decimal(amount),
            "currency": "USD",
            "credit_debit": direction,
            "status": "BOOK",
            "is_reversal": False,
            "btc_domain": "PMNT",
            "btc_family": "ICDT",
            "btc_subfamily": "ATXN",
            "channel": "ONLINE",
            "business_date": day,
            "value_date": day,
            "booking_ts": datetime.combine(day, time(12)),
            "debtor_account": sender,
            "creditor_account": receiver,
        }
        | changes
    )


def run(rows):
    sql = (
        jinja2.Environment(undefined=jinja2.StrictUndefined)
        .from_string((HERE / "rule.sql").read_text())
        .render(asof=DAY.isoformat(), params=RULE["params"])
    )
    with duckdb.connect() as con:
        con.register("entries", pa.Table.from_pylist(rows, schema=schema.ENTRY))
        rel = con.sql(sql)
        assert tuple(rel.columns) == schema.HIT_COLUMNS
        hits = [dict(zip(rel.columns, row, strict=True)) for row in rel.fetchall()]
    for hit in hits:
        hit["computed_values"] = json.loads(hit["computed_values"])
    return hits


@pytest.mark.parametrize(
    "amounts,fires",
    [
        (["6000", "6000"], False),
        (["4000"] * 3, True),
        (["3000", "3000", "4000"], False),
        (["3000", "3000", "4000.01"], True),
        (["10000"] * 3, False),
        (["9999.99"] * 3, True),
    ],
)
def test_pair_count_single_amount_and_total_boundaries(amounts, fires):
    hits = run([entry(i, amount=a) for i, a in enumerate(amounts)])
    assert bool(hits) == fires
    if hits:
        assert hits[0]["group_key"] == "a:A>B"
        assert hits[0]["computed_values"]["variant"] == "a"


@pytest.mark.parametrize("age,fires", [(6, True), (7, False), (-1, False)])
def test_pair_window_and_future_exclusion(age, fires):
    rows = [entry(0), entry(1), entry(2, day=DAY - timedelta(days=age))]
    assert bool(run(rows)) == fires


def funnel(old=0, senders=5, history_age=7):
    # Even four senders clear the total threshold, isolating the distinct-sender count.
    rows = [entry(i, sender=f"S{i}", direction="CRDT", amount="3000") for i in range(senders)]
    rows += [
        entry(
            100 + i,
            sender=f"S{i}",
            direction="CRDT",
            amount="15000",
            day=DAY - timedelta(days=history_age),
        )
        for i in range(old)
    ]
    return rows


@pytest.mark.parametrize("senders,old,fires", [(4, 0, False), (5, 2, True), (5, 3, False)])
def test_funnel_distinct_and_new_sender_boundaries(senders, old, fires):
    hits = run(funnel(old, senders))
    assert bool(hits) == fires
    if hits:
        assert hits[0]["customer_id"] == "C:B"
        assert hits[0]["group_key"] == "b:B"
        assert hits[0]["computed_values"]["new_sender_count"] == senders - old


def test_funnel_quiet_day_does_not_repeat_a_qualifying_window():
    assert run(funnel())  # Positive control: all count, newness and total conditions pass.
    rows = [
        entry(i, sender=f"S{i}", direction="CRDT", amount="3000", day=DAY - timedelta(days=1))
        for i in range(5)
    ]
    assert not run(rows)


@pytest.mark.parametrize("amount,fires", [("9999.99", True), ("10000", False), ("10000.01", False)])
def test_funnel_single_entry_cap_is_enforced(amount, fires):
    rows = funnel()
    # Four remaining $3,000 entries still clear the total and new-sender thresholds.
    rows[-1]["amount"] = Decimal(amount)
    assert bool(run(rows)) == fires


@pytest.mark.parametrize("age,fires", [(96, False), (97, True)])
def test_history_boundary_and_large_prior_payment(age, fires):
    assert bool(run(funnel(old=3, history_age=age))) == fires


def test_repeat_payments_do_not_create_distinct_senders_or_newness():
    assert not run([entry(i, direction="CRDT", amount="2500") for i in range(5)])
    rows = funnel()
    rows.append(entry(10, sender="S0", direction="CRDT", day=DAY - timedelta(days=3)))
    (hit,) = run(rows)
    assert hit["computed_values"]["new_sender_count"] == 5
    assert hit["computed_values"]["entry_count"] == 6
    assert not run([r | {"amount": Decimal("2000")} for r in funnel()])


@pytest.mark.parametrize(
    "changes",
    [
        {"btc_family": "CNTR", "btc_subfamily": "CDPT"},
        {"btc_family": "CCRD", "btc_subfamily": "CWDL"},
        {"btc_domain": "ACMT"},
        {"status": "PDNG"},
        {"is_reversal": True},
        {"currency": "EUR"},
        {"creditor_account": None},
        {"amount": Decimal("0")},
    ],
)
def test_ineligible_entries_do_not_count(changes):
    assert not run([entry(i, **changes) for i in range(3)])


def test_same_day_customer_variants_and_pairs_keep_separate_hits():
    rows = [entry(i, cif_id="OWNER") for i in range(3)]
    rows += [entry(10 + i, receiver="D", cif_id="OWNER") for i in range(3)]
    rows += [r | {"cif_id": "OWNER", "entry_id": "F" + r["entry_id"]} for r in funnel()]
    # Incoming account B is now owned by OWNER; A->B is an own-account transfer and excluded.
    hits = run(rows)
    assert {h["group_key"] for h in hits} == {"a:A>D", "b:B"}
    assert len({(h["customer_id"], h["business_day"], h["group_key"]) for h in hits}) == 2


def test_both_booked_legs_count_once_per_variant_and_quiet_days_do_not_repeat():
    debits = [entry(i) for i in range(3)]
    credits = [entry(10 + i, direction="CRDT") for i in range(3)]
    (hit,) = run(debits + credits)
    assert hit["matched_txn_ids"] == ["R0", "R1", "R2"]
    assert not run([r | {"business_date": DAY - timedelta(days=1)} for r in debits])


def test_seeded_label_blind_injection_recall_and_validation():
    df = pl.from_arrow(schema.validate(fixtures.generate())[0])
    # Use a dataset ending on the run day so SQL and the answer key refer to the same day.
    df = df.filter(pl.col("business_date") <= DAY)
    injected, cases = inject(df, random.Random(37))
    again, key = inject(df, random.Random(37))
    assert injected.equals(again) and cases == key
    changed, _ = inject(
        df.with_columns(pl.lit("ignore").alias("typology_label")), random.Random(37)
    )
    assert injected.tail(30).equals(changed.tail(30))
    valid, rejected = schema.validate(injected.to_arrow().cast(schema.ENTRY))
    assert not rejected
    hits = {h["customer_id"]: h for h in run(valid.to_pylist())}
    caught = [
        c
        for c in cases
        if c["customer_id"] in hits
        and set(c["entry_ids"]) <= set(hits[c["customer_id"]]["matched_txn_ids"])
    ]
    assert len(caught) == len(cases) == 10
    same, empty = inject(df, random.Random(37), 0)
    assert same.equals(df) and not empty
    with pytest.raises(ValueError):
        inject(df, random.Random(37), -1)
