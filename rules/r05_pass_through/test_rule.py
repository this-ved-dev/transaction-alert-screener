"""R05 boundaries against the actual SQL, independent of the engine and adapters."""

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

from rules.r05_pass_through.inject import inject
from screener import schema
from screener.adapters import fixtures

HERE = Path(__file__).parent
DAY = date(2023, 7, 14)
AT = datetime.combine(DAY, time(10))
RULE = yaml.safe_load((HERE / "rule.yaml").read_text())
BASE = fixtures.generate().slice(0, 1).to_pylist()[0]


def entry(i, *, at=AT, amount="5000", direction="CRDT", account="A", other="ORIGIN", **changes):
    return (
        BASE
        | {
            "entry_id": str(i),
            "account_id": account,
            "cif_id": "C:" + account,
            "amount": Decimal(amount),
            "currency": "USD",
            "credit_debit": direction,
            "is_reversal": False,
            "status": "BOOK",
            "booking_ts": at,
            "value_date": at.date(),
            "business_date": at.date(),
            "btc_domain": "PMNT",
            "btc_family": "RCDT" if direction == "CRDT" else "ICDT",
            "btc_subfamily": "ATXN",
            "channel": "ONLINE",
            "debtor": None,
            "creditor": None,
            "debtor_account": other if direction == "CRDT" else account,
            "creditor_account": account if direction == "CRDT" else other,
        }
        | changes
    )


def history():
    return [entry("OBSERVED", account="HISTORY", at=AT - timedelta(days=120), amount="1")]


def example(*, hours=1, amount="4000", other="BEN", **changes):
    return history() + [
        entry("IN"),
        entry(
            "OUT",
            at=AT + timedelta(hours=hours),
            amount=amount,
            direction="DBIT",
            other=other,
            **changes,
        ),
    ]


def busy(volume="1000"):
    return [
        entry(f"H{i}", at=AT - timedelta(days=i), amount=volume, direction="DBIT", other="BEN")
        for i in range(1, 91)
    ]


def run(rows, *, day=DAY, sql=None):
    sql = (
        jinja2.Environment(undefined=jinja2.StrictUndefined)
        .from_string(sql or (HERE / "rule.sql").read_text())
        .render(params=RULE["params"], asof=day.isoformat())
    )
    with duckdb.connect() as con:
        con.register("entries", pa.Table.from_pylist(rows, schema=schema.ENTRY))
        result = con.sql(sql)
        assert tuple(result.columns) == schema.HIT_COLUMNS
        hits = [dict(zip(result.columns, r, strict=True)) for r in result.fetchall()]
    for hit in hits:
        hit["computed_values"] = json.loads(hit["computed_values"])
    return hits


@pytest.mark.parametrize("hours,fires", [(71, True), (72, True), (73, False), (0, False)])
def test_elapsed_hour_window(hours, fires):
    assert bool(run(example(hours=hours), day=(AT + timedelta(hours=hours)).date())) == fires


@pytest.mark.parametrize("amount,fires", [("3950", False), ("3999.99", False), ("4000", True)])
def test_outflow_ratio_is_exact_at_eighty_percent(amount, fires):
    assert bool(run(example(amount=amount))) == fires


def test_minimum_inbound_and_return_to_originator():
    rows = example()
    rows[1]["amount"] = Decimal("4999.99")
    assert not run(rows)
    assert not run(example(other="ORIGIN", btc_subfamily="XBCT"))


@pytest.mark.parametrize("volume,fires", [("1000", False), ("999.99", True), ("3000", False)])
def test_quiet_baseline_boundary_with_known_domestic_beneficiary(volume, fires):
    assert bool(run(example() + busy(volume))) == fires


def test_baseline_includes_inactive_days_as_zero():
    rows = example() + [
        entry("OLD", direction="DBIT", other="BEN", amount="100000", at=AT - timedelta(days=45))
    ]
    (hit,) = run(rows)
    (anchor,) = hit["computed_values"]["anchors"]
    assert anchor["quiet"] is True and anchor["median_daily_volume"] == 0


@pytest.mark.parametrize("cross_border,new_beneficiary", [(True, False), (False, True)])
def test_busy_account_can_use_risky_outflows(cross_border, new_beneficiary):
    rows = example(
        other="NEW" if new_beneficiary else "BEN", btc_subfamily="XBCT" if cross_border else "ATXN"
    ) + busy("3000")
    (hit,) = run(rows)
    (anchor,) = hit["computed_values"]["anchors"]
    assert anchor["quiet"] is False
    assert anchor["cross_border"] == cross_border
    assert anchor["new_beneficiary"] == new_beneficiary


def test_small_risky_payment_does_not_unlock_other_busy_account_outflows():
    rows = example(amount="3999") + busy("3000")
    rows.append(
        entry(
            "SMALL",
            at=AT + timedelta(hours=2),
            direction="DBIT",
            other="NEW",
            amount="1",
            btc_subfamily="XBCT",
        )
    )
    assert not run(rows)


@pytest.mark.parametrize("extra_microseconds,fires", [(0, False), (1, True)])
def test_new_beneficiary_history_boundary(extra_microseconds, fires):
    rows = example(other="NEW") + busy("3000")
    rows.append(
        entry(
            "PRIOR_NEW",
            at=AT - timedelta(days=90, microseconds=extra_microseconds),
            amount="1",
            direction="DBIT",
            other="NEW",
        )
    )
    assert bool(run(rows)) == fires


def test_cash_anchor_can_have_no_originator_account_but_non_cash_requires_one():
    rows = example()
    rows[1].update(debtor_account=None, btc_family="CNTR", btc_subfamily="CDPT")
    assert run(rows)
    rows[1].update(btc_family="RCDT", btc_subfamily="ATXN")
    assert not run(rows)


def test_unknown_history_does_not_imply_quiet_or_new_relationship():
    assert not run(example()[1:])
    assert run(example(btc_subfamily="XBCT")[1:])


@pytest.mark.parametrize(
    "changes",
    [{"status": "PDNG"}, {"is_reversal": True}, {"currency": "EUR"}, {"btc_domain": "ACMT"}],
)
def test_ineligible_outflows_are_excluded(changes):
    assert not run(example(**changes))


def test_future_data_and_quiet_days_do_not_fire():
    assert not run(example(hours=25), day=DAY)
    assert not run(example(), day=DAY + timedelta(days=1))


def test_own_account_outflow_is_excluded():
    rows = example()
    rows.append(entry("OWN", account="BEN", cif_id="C:A", amount="1", btc_domain="ACMT"))
    assert not run(rows)


def test_overlapping_anchors_keep_evidence_in_one_account_day_hit():
    rows = example(amount="4800")
    rows.append(entry("IN2", at=AT - timedelta(minutes=1), amount="6000", other="ORIGIN2"))
    (hit,) = run(rows)
    assert hit["group_key"] == hit["account_id"] == "A"
    assert hit["computed_values"]["anchor_count"] == 2
    assert hit["matched_txn_ids"] == ["IN", "IN2", "OUT"]


def test_two_accounts_of_one_customer_preserve_separate_hits():
    rows = example()
    rows += [
        entry("IN2", account="A2", cif_id="C:A"),
        entry(
            "OUT2",
            account="A2",
            cif_id="C:A",
            at=AT + timedelta(hours=1),
            direction="DBIT",
            other="BEN2",
            amount="4000",
        ),
    ]
    assert {h["group_key"] for h in run(rows)} == {"A", "A2"}


def test_seeded_injection_is_label_blind_valid_and_recalled():
    df = pl.from_arrow(schema.validate(fixtures.generate())[0])
    injected, cases = inject(df, random.Random(33))
    same, key = inject(df, random.Random(33))
    assert injected.equals(same) and cases == key
    relabelled, _ = inject(
        df.with_columns(pl.lit("ignore").alias("typology_label")), random.Random(33)
    )
    assert injected.tail(30).equals(relabelled.tail(30))
    valid, rejected = schema.validate(injected.to_arrow().cast(schema.ENTRY))
    assert not rejected
    hits = {
        h["customer_id"]: h
        for h in run(valid.to_pylist(), day=date.fromisoformat(cases[0]["business_day"]))
    }
    caught = [
        c
        for c in cases
        if c["customer_id"] in hits
        and set(c["entry_ids"]) <= set(hits[c["customer_id"]]["matched_txn_ids"])
    ]
    assert len(caught) == len(cases) == 10
    same, empty = inject(df, random.Random(33), 0)
    assert same.equals(df) and empty == []
    with pytest.raises(ValueError):
        inject(df, random.Random(33), -1)


def test_fixture_operating_points():
    """Illustrate baseline effects; these constructed cases are not native AML metrics."""
    scenarios = {
        "QUIET": example()
        + [entry("KNOWN", at=AT - timedelta(days=45), direction="DBIT", other="BEN", amount="1")],
        "BUSY_KNOWN": example() + busy("3000"),
        "BUSY_XBCT": example(btc_subfamily="XBCT") + busy("3000"),
        "BUSY_NEW": example(other="NEW") + busy("3000"),
    }
    rows = []
    for name, case in scenarios.items():
        for original in case:
            row = original.copy()
            for field in ("entry_id", "cif_id", "account_id", "debtor_account", "creditor_account"):
                if row[field] is not None:
                    row[field] = name + ":" + row[field]
            rows.append(row)
    sql = (HERE / "rule.sql").read_text()
    guard = "WHERE quiet OR cross_border OR new_beneficiary"
    assert guard in sql
    configurations = {
        "no_baseline_gate": sql.replace(guard, "WHERE TRUE"),
        "quiet_only": sql.replace(guard, "WHERE quiet"),
        "quiet_or_XBCT_or_new": sql,
    }
    results = {}
    for name, query in configurations.items():
        caught = {hit["customer_id"].split(":")[0] for hit in run(rows, sql=query)}
        positives = set(scenarios) - {"BUSY_KNOWN"}
        results[name] = {
            "hits": len(caught),
            "true_cases": len(caught & positives),
            "false_cases": len(caught - positives),
            "positive_cases": len(positives),
        }
    assert results["no_baseline_gate"] == {
        "hits": 4,
        "true_cases": 3,
        "false_cases": 1,
        "positive_cases": 3,
    }
    assert results["quiet_only"] == {
        "hits": 1,
        "true_cases": 1,
        "false_cases": 0,
        "positive_cases": 3,
    }
    assert results["quiet_or_XBCT_or_new"] == {
        "hits": 3,
        "true_cases": 3,
        "false_cases": 0,
        "positive_cases": 3,
    }
    print(json.dumps(results, sort_keys=True))
