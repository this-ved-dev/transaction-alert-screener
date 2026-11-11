"""Contract tests that run from day 0.

Rule folders validate, red flags resolve, params are used, hostile memos are present, every
BankTransactionCode we map is in the ISO codification, the fixture Parquet is reproducible and
quarantines its planted bad rows, every rule.sql returns the hit columns on it, hits keep one
row per account (group_key) through repeated hourly upserts, and the bank-feed skeletons and the
field sheet (docs/14) name only canonical columns.
"""

from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

import duckdb
import jinja2
import pyarrow.parquet as pq
import pytest
import yaml
from jsonschema import Draft202012Validator

from screener import btc, schema
from screener.adapters import core_csv, fixtures, wire_feed

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"
SCHEMA = json.loads((RULES / "_schema" / "rule.schema.json").read_text())
RED_FLAGS = {rf["id"]: rf for rf in yaml.safe_load((RULES / "red_flags.yaml").read_text())}
FIXTURE = ROOT / "data" / "fixtures" / "fixture.parquet"
RULE_DIRS = sorted(
    p for p in RULES.iterdir() if p.is_dir() and p.name[:1] == "r" and p.name[1:3].isdigit()
)


def test_schema_is_valid_jsonschema():
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("rule_dir", RULE_DIRS, ids=lambda p: p.name)
def test_rule_folder(rule_dir: Path):
    yaml_path = rule_dir / "rule.yaml"
    if not yaml_path.exists():
        pytest.skip(f"{rule_dir.name}: rule.yaml not written yet")
    rule = yaml.safe_load(yaml_path.read_text())
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(rule), key=str)
    assert not errors, "\n".join(e.message for e in errors)
    assert rule["id"] == rule_dir.name[:3], "folder prefix must match rule id"
    for rf in rule["red_flag_ids"]:
        assert rf in RED_FLAGS, f"{rf} missing from rules/red_flags.yaml"
    sql = (rule_dir / "rule.sql").read_text()
    for key in rule["params"]:
        assert f"params.{key}" in sql, f"param {key} is never used in rule.sql"
    for required in ("inject.py", "explain.py", "evidence.html", "test_rule.py"):
        assert (rule_dir / required).exists(), f"{rule_dir.name}/{required} missing"
    if rule["mode"] == "live":
        assert rule["budget_per_month"] > 0


def test_every_red_flag_has_source_and_rule():
    for rf in RED_FLAGS.values():
        assert rf["url"].startswith("https://"), rf["id"]
        assert rf["rule_ids"], rf["id"]


def test_hostile_memos_fixture_present():
    rows = list(csv.DictReader((ROOT / "data" / "fixtures" / "hostile_memos.csv").open()))
    assert any("<script>" in r["memo"] for r in rows)
    assert any("ignore previous instructions" in r["memo"] for r in rows)


def test_example_rule_defaults_are_flat():
    rule = yaml.safe_load((RULES / "r00_example" / "rule.yaml").read_text())
    assert rule["tier_multipliers"] == {"low": 1.0, "medium": 1.0, "high": 1.0}
    assert "client_definition" in rule


def test_every_mapped_triplet_and_channel_is_valid():
    combos = btc.tran_code_combos()
    bad = [c for c in combos if not btc.is_valid(c["domain"], c["family"], c["subfamily"])]
    assert not bad, f"not in the ISO codification: {bad}"
    assert {c["channel"] for c in combos} <= set(schema.CHANNELS)
    assert not btc.is_valid("PMNT", "CNTR", "ZZZZ")


@pytest.mark.parametrize("feed", [core_csv, wire_feed], ids=["core_csv", "wire_feed"])
def test_feed_skeleton_names_canonical_columns_and_waits_for_layout(feed):
    lists = feed.REQUIRED + feed.DERIVABLE + feed.NICE_TO_HAVE
    assert len(lists) == len(set(lists)), "a column has two marks"
    assert set(lists) <= set(schema.ENTRY.names), set(lists) - set(schema.ENTRY.names)
    assert set(schema.REQUIRED) <= set(feed.REQUIRED + feed.DERIVABLE), "validate() would reject"
    with pytest.raises(NotImplementedError, match="layout not received yet"):
        feed.load("any.csv")


def test_field_sheet_lists_every_canonical_column():
    sheet = (ROOT / "docs" / "14-field-requirements.md").read_text()
    assert [c for c in schema.ENTRY.names if f"`{c}`" not in sheet] == []


def test_fixture_is_reproducible_small_and_current(tmp_path):
    first, second = tmp_path / "a.parquet", tmp_path / "b.parquet"
    assert fixtures.write(first) == fixtures.write(second), "same seed must give the same bytes"
    assert pq.read_table(first).equals(pq.read_table(FIXTURE)), "stale: run `screener fixtures`"
    assert FIXTURE.stat().st_size < 1_000_000
    assert pq.read_schema(FIXTURE).remove_metadata().equals(schema.ENTRY)


def test_fixture_covers_every_mapped_combo():
    t = pq.read_table(FIXTURE).to_pydict()
    cols = ("credit_debit", "btc_domain", "btc_family", "btc_subfamily", "btc_proprietary")
    seen = set(zip(*(t[c] for c in (*cols, "channel")), strict=True))
    for c in btc.tran_code_combos():
        key = (c["direction"], c["domain"], c["family"], c["subfamily"], c["proprietary"])
        assert (*key, c["channel"]) in seen, c


def test_quarantine_rejects_exactly_the_planted_rows():
    table = pq.read_table(FIXTURE)
    valid, rejected = schema.validate(table)
    planted = [r for r in table.column("raw_ref").to_pylist() if r.startswith("fixture:reject:")]
    assert sorted(json.loads(r["raw_row"])["raw_ref"] for r in rejected) == sorted(planted)
    assert len(planted) == len(fixtures.BREAKS)
    assert any(r["reason"].startswith("BankTransactionCode") for r in rejected)
    assert valid.num_rows == table.num_rows - len(planted)
    assert valid.schema.equals(schema.ENTRY)
    v = valid.to_pydict()
    triplets = zip(v["btc_domain"], v["btc_family"], v["btc_subfamily"], strict=True)
    assert all(btc.is_valid(*t) for t in triplets)


@pytest.fixture(scope="module")
def entries():
    """DuckDB with the views rule.sql may read; the engine (TRA-21) provides the real ones."""
    con = duckdb.connect()
    con.register("entries", schema.validate(pq.read_table(FIXTURE))[0])
    con.execute("CREATE VIEW customers AS SELECT DISTINCT cif_id, 'low' AS risk_tier FROM entries")
    return con


def render(sql: str, params: dict) -> str:
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    return env.from_string(sql).render(params=params, asof=fixtures.DEMO_DAY.isoformat())


def run_rule(con, rule_dir: Path) -> duckdb.DuckDBPyRelation:
    rule = yaml.safe_load((rule_dir / "rule.yaml").read_text())
    return con.sql(render((rule_dir / "rule.sql").read_text(), rule["params"]))


@pytest.mark.parametrize("rule_dir", RULE_DIRS, ids=lambda p: p.name)
def test_rule_sql_returns_the_hit_columns(rule_dir: Path, entries):
    if not (rule_dir / "rule.sql").exists():
        pytest.skip(f"{rule_dir.name}: rule.sql not written yet")
    rel = run_rule(entries, rule_dir)
    assert tuple(rel.columns) == schema.HIT_COLUMNS
    types = ["VARCHAR", "VARCHAR", "DATE", "VARCHAR", "VARCHAR[]", "JSON"]
    assert [str(t) for t in rel.types] == types
    rows = [dict(zip(rel.columns, r, strict=True)) for r in rel.fetchall()]
    assert all(r["group_key"] is not None for r in rows), "group_key must never be NULL"
    keys = [(r["customer_id"], r["business_day"], r["group_key"]) for r in rows]
    assert len(keys) == len(set(keys)), "one row per (customer_id, business_day, group_key)"


def test_r00_fires_on_the_fixture_demo_day(entries):
    rows = run_rule(entries, RULES / "r00_example").fetchall()
    assert [(r[0], r[3], sorted(r[4])) for r in rows] == [
        ("CIF00001", "CIF00001", ["FX000000", "FX000001"])
    ]


# Account-keyed rule (like R05): CIF00001's two accounts both pass $4,000 cash in on DEMO_DAY.
ACCOUNT_KEYED_SQL = """
SELECT cif_id AS customer_id, account_id, business_date AS business_day, account_id AS group_key,
       list(entry_id ORDER BY entry_id) AS matched_txn_ids,
       to_json({'cash_in_total': sum(amount)}) AS computed_values
FROM entries
WHERE btc_subfamily = 'CDPT' AND credit_debit = 'CRDT' AND business_date = DATE '{{ asof }}'
GROUP BY ALL
HAVING sum(amount) > {{ params.threshold_usd }}
"""


def test_two_accounts_of_one_customer_survive_repeated_hourly_upserts():
    con = duckdb.connect()
    con.register("base", schema.validate(pq.read_table(FIXTURE))[0])
    con.execute(
        "CREATE TABLE hit (rule_version_id INTEGER, customer_id VARCHAR, account_id VARCHAR, "
        "business_day DATE, group_key VARCHAR, matched_txn_ids VARCHAR[], computed_values JSON, "
        f"PRIMARY KEY ({', '.join(schema.HIT_IDENTITY)}))"
    )
    upsert = (
        f"INSERT INTO hit SELECT 1, * FROM ({render(ACCOUNT_KEYED_SQL, {'threshold_usd': 4000})}) "
        "ON CONFLICT DO UPDATE SET matched_txn_ids = excluded.matched_txn_ids, "
        "computed_values = excluded.computed_values"
    )
    con.execute("CREATE VIEW entries AS SELECT * FROM base")
    con.execute(upsert)
    con.execute(upsert)  # the same hour run again
    con.execute(  # next hour: a late $100 deposit lands on ACC00001
        "CREATE OR REPLACE VIEW entries AS SELECT * FROM base UNION ALL "
        "SELECT * REPLACE ('FXLATE' AS entry_id, 100::DECIMAL(18, 2) AS amount) "
        "FROM base WHERE entry_id = 'FX000000'"
    )
    con.execute(upsert)
    got = con.sql(
        "SELECT group_key, matched_txn_ids, (computed_values->>'cash_in_total')::DECIMAL(18, 2) "
        "FROM hit WHERE customer_id = 'CIF00001' ORDER BY group_key"
    ).fetchall()
    assert got == [
        ("ACC00001", ["FX000000", "FXLATE"], Decimal("6100.00")),
        ("ACC00201", ["FX000001"], Decimal("4500.00")),
    ]
