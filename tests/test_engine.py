"""Rules engine core (TRA-21): discover, validate, render, run, upsert, retract, manifest."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml

from screener import schema
from screener.adapters import fixtures as fx
from screener.engine import (
    RuleError,
    discover_rules,
    load_rule,
    render_sql,
    run,
    run_fixtures,
)

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"

ACCOUNT_KEYED_SQL = """
SELECT cif_id AS customer_id, account_id, business_date AS business_day, account_id AS group_key,
       list(entry_id ORDER BY entry_id) AS matched_txn_ids,
       to_json({'cash_in_total': sum(amount)}) AS computed_values
FROM entries
WHERE btc_subfamily = 'CDPT' AND credit_debit = 'CRDT' AND business_date = DATE '{{ asof }}'
GROUP BY ALL
HAVING sum(amount) > {{ params.threshold_usd }}
"""


def _live_rules_copy(tmp_path: Path, *names: str) -> Path:
    """Copy selected rule folders into a temp tree (with schema); force mode=live."""
    root = tmp_path / "rules"
    root.mkdir()
    shutil.copytree(RULES / "_schema", root / "_schema")
    for name in names:
        dest = root / name
        shutil.copytree(RULES / name, dest)
        spec = yaml.safe_load((dest / "rule.yaml").read_text())
        spec["mode"] = "live"
        (dest / "rule.yaml").write_text(yaml.safe_dump(spec))
    return root


def _write_probe_rule(rules_root: Path, *, folder: str, rule_id: str, mode: str = "live") -> Path:
    """Minimal valid rule folder (in-range id) for discovery/run AC tests."""
    rule_dir = rules_root / folder
    rule_dir.mkdir(parents=True)
    (rule_dir / "rule.yaml").write_text(
        yaml.safe_dump(
            {
                "id": rule_id,
                "name": "Engine probe rule for discovery AC",
                "owner": "example",
                "version": 1,
                "mode": mode,
                "key": "customer",
                "windows": {"lookback_days": 1},
                "params": {"threshold_usd": 10000.0},
                "weight": 1.0,
                "red_flag_ids": ["RF-004"],
                "budget_per_month": 10,
                "description": "Probe rule used only to prove folder discovery and execution.",
                "tier_multipliers": {"low": 1.0, "medium": 1.0, "high": 1.0},
            }
        )
    )
    (rule_dir / "rule.sql").write_text((RULES / "r00_example" / "rule.sql").read_text())
    return rule_dir


def test_discover_includes_every_folder_with_rule_yaml():
    names = {p.name for p in discover_rules()}
    assert "r00_example" in names
    assert "r10_round_dollar" in names


def test_new_rule_folder_picked_up_without_code_change(tmp_path):
    """AC: a new folder is discovered, loaded, and executed with no engine change.

    Uses an in-range id (r12) because the day-0 schema pattern is r00–r12; r99 cannot validate.
    """
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    shutil.copytree(RULES / "_schema", rules_root / "_schema")
    probe = _write_probe_rule(rules_root, folder="r12_tmp", rule_id="r12")
    assert probe in discover_rules(rules_root)
    loaded = load_rule(probe, rules_dir=rules_root)
    assert loaded.rule_id == "r12"
    db = tmp_path / "probe.sqlite"
    manifest = run(
        day=fx.DEMO_DAY,
        store="sqlite",
        sqlite_path=db,
        parquet=fx.OUT,
        rules_dir=rules_root,
    )
    assert "r12" in manifest["rules_run"]
    assert manifest["hit_count"] >= 1


def test_invalid_rule_yaml_fails_fast(tmp_path):
    bad = tmp_path / "r00_bad"
    bad.mkdir()
    (bad / "rule.yaml").write_text("id: not-a-rule\nname: x\n")
    (bad / "rule.sql").write_text("SELECT 1")
    with pytest.raises(RuleError, match="invalid rule.yaml"):
        load_rule(bad)


def test_unknown_param_in_sql_fails_fast():
    with pytest.raises(RuleError, match="unknown param"):
        render_sql(
            "SELECT {{ params.does_not_exist }} AS x",
            params={"threshold_usd": 1},
            asof=date(2023, 7, 14),
        )


def test_run_day_writes_hits_manifest_and_rejected_count(tmp_path):
    db = tmp_path / "screener.sqlite"
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    # Shadow via mode on a different in-range id (ids must be unique across folders).
    _write_probe_rule(rules_root, folder="r11_shadow", rule_id="r11", mode="shadow")

    manifest = run(
        day=fx.DEMO_DAY,
        store="sqlite",
        sqlite_path=db,
        parquet=fx.OUT,
        rules_dir=rules_root,
    )
    assert manifest["mode"] == "day"
    assert manifest["hit_count"] >= 1
    assert "r00" in manifest["rules_run"]
    assert "r11" in manifest["rules_run"]
    assert manifest["rejected_count"] == len(fx.BREAKS)
    assert manifest["input_hashes"]["parquet"]
    assert manifest["input_hashes"]["country_risk"]
    assert manifest["input_hashes"]["holidays"]
    assert Path(db).exists()
    modes = {row["mode"] for row in manifest["rule_versions"]}
    assert modes == {"live", "shadow"}


def test_manifest_hashes_change_when_country_risk_changes(tmp_path):
    """Reference inputs must be in the manifest: changing country risk changes the hash."""
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "ref.sqlite"
    risk_a = tmp_path / "country_risk_a.csv"
    risk_b = tmp_path / "country_risk_b.csv"
    holidays = ROOT / "data" / "reference" / "holidays_us.csv"
    risk_a.write_text(
        "country_iso2,country_name,tier,source,effective_from,effective_to,verified_on,source_url,note\n"
        "MX,Mexico,grey,test,2022-01-01,,,https://example.test/,a\n"
    )
    risk_b.write_text(
        "country_iso2,country_name,tier,source,effective_from,effective_to,verified_on,source_url,note\n"
        "MX,Mexico,black,test,2022-01-01,,,https://example.test/,b\n"
    )
    first = run(
        day=fx.DEMO_DAY,
        store="sqlite",
        sqlite_path=db,
        parquet=fx.OUT,
        rules_dir=rules_root,
        country_risk=risk_a,
        holidays=holidays,
    )
    second = run(
        day=fx.DEMO_DAY,
        store="sqlite",
        sqlite_path=db,
        parquet=fx.OUT,
        rules_dir=rules_root,
        country_risk=risk_b,
        holidays=holidays,
    )
    assert first["input_hashes"]["parquet"] == second["input_hashes"]["parquet"]
    assert first["input_hashes"]["holidays"] == second["input_hashes"]["holidays"]
    assert first["input_hashes"]["country_risk"] != second["input_hashes"]["country_risk"]


def test_default_run_skips_off_but_still_loads_r00_example(tmp_path):
    """Production ``screener run`` skips mode=off; r00 is discovered and validated only."""
    db = tmp_path / "off.sqlite"
    loaded = [load_rule(p) for p in discover_rules()]
    assert any(r.rule_id == "r00" and r.mode == "off" for r in loaded)
    manifest = run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT)
    assert "r00" not in manifest["rules_run"]
    assert "r10" in manifest["rules_run"]


def test_run_fixtures_executes_r00_on_demo_day():
    """``run_fixtures`` / ``fixture_run`` includes off rules so r00 tests work."""
    result = run_fixtures()
    hits = result.hits("r00")
    assert hits, "r00 should fire on the fixture demo day"
    assert any(h["computed_values"]["cash_in_total"] > 10000 for h in hits)
    assert hits[0]["group_key"] == "CIF00001"
    assert result.manifest["mode"] == "day"


def test_two_accounts_survive_engine_hourly_upsert(tmp_path):
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    shutil.copytree(RULES / "_schema", rules_root / "_schema")
    rule_dir = rules_root / "r00_accounts"
    rule_dir.mkdir()
    (rule_dir / "rule.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "r00",
                "name": "Account-keyed cash-in for upsert test",
                "owner": "example",
                "version": 1,
                "mode": "live",
                "key": "account",
                "windows": {"lookback_days": 1},
                "params": {"threshold_usd": 4000.0},
                "weight": 1.0,
                "red_flag_ids": ["RF-004"],
                "budget_per_month": 10,
                "description": "Account-keyed example used only for engine upsert coverage.",
                "tier_multipliers": {"low": 1.0, "medium": 1.0, "high": 1.0},
            }
        )
    )
    (rule_dir / "rule.sql").write_text(ACCOUNT_KEYED_SQL)
    db = tmp_path / "upsert.sqlite"
    m1 = run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    m2 = run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    assert m1["hit_count"] == m2["hit_count"] == 2
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT group_key, matched_txn_ids, computed_values FROM hit "
        "WHERE customer_id = 'CIF00001' AND retracted_run_id IS NULL ORDER BY group_key"
    ).fetchall()
    assert len(rows) == 2
    totals = [Decimal(str(json.loads(r[2])["cash_in_total"])) for r in rows]
    assert totals == [Decimal("6000"), Decimal("4500")]


def test_reconcile_soft_retracts_hit_that_stops_firing(tmp_path):
    """Must-fix #1: append-only soft-retract when a re-eval no longer produces the hit."""
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "retract.sqlite"
    first = run(
        day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root
    )
    assert first["hit_count"] >= 1
    # Drop CIF00001 cash-in rows so r00 no longer fires.
    base = schema.validate(pq.read_table(fx.OUT))[0]
    kept = [
        r
        for r in base.to_pylist()
        if not (
            r["cif_id"] == "CIF00001"
            and r["btc_subfamily"] == "CDPT"
            and r["credit_debit"] == "CRDT"
            and r["business_date"] == fx.DEMO_DAY
        )
    ]
    slim = tmp_path / "slim.parquet"
    pq.write_table(pa.Table.from_pylist(kept, schema=schema.ENTRY), slim)
    second = run(
        day=fx.DEMO_DAY,
        reconcile=True,
        store="sqlite",
        sqlite_path=db,
        parquet=slim,
        rules_dir=rules_root,
    )
    assert second["hit_count"] == 0
    assert second["retracted_count"] >= 1
    con = sqlite3.connect(db)
    row = con.execute(
        "SELECT retracted_run_id FROM hit WHERE customer_id = 'CIF00001' AND group_key = 'CIF00001'"
    ).fetchone()
    assert row is not None
    assert row[0] == second["run_id"]


def test_business_day_must_equal_asof(tmp_path):
    """Must-fix #2: reject rows whose business_day ≠ asof (every mode)."""
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    shutil.copytree(RULES / "_schema", rules_root / "_schema")
    rule_dir = rules_root / "r00_lookback"
    rule_dir.mkdir()
    (rule_dir / "rule.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "r00",
                "name": "Reports yesterday as business_day",
                "owner": "example",
                "version": 1,
                "mode": "live",
                "key": "customer",
                "windows": {"lookback_days": 2},
                "params": {"threshold_usd": 1.0},
                "weight": 1.0,
                "red_flag_ids": ["RF-004"],
                "budget_per_month": 10,
                "description": "Deliberately returns business_day of asof minus one day.",
                "tier_multipliers": {"low": 1.0, "medium": 1.0, "high": 1.0},
            }
        )
    )
    (rule_dir / "rule.sql").write_text(
        """
SELECT 'CIF00001' AS customer_id, NULL::VARCHAR AS account_id,
       DATE '{{ asof }}' - 1 AS business_day, 'CIF00001' AS group_key,
       ['X']::VARCHAR[] AS matched_txn_ids,
       to_json({'ok': true}) AS computed_values
"""
    )
    with pytest.raises(RuleError, match="business_day must equal asof"):
        run(
            day=fx.DEMO_DAY,
            store="sqlite",
            sqlite_path=tmp_path / "bad.sqlite",
            parquet=fx.OUT,
            rules_dir=rules_root,
        )


def test_since_twice_over_same_data_yields_identical_hit_counts(tmp_path):
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "since.sqlite"
    since = "2000-01-01T00:00:00"
    first = run(since=since, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    second = run(since=since, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    assert first["hit_count"] >= 1
    assert first["hit_count"] == second["hit_count"]
    con = sqlite3.connect(db)
    assert (
        con.execute("SELECT count(*) FROM hit WHERE retracted_run_id IS NULL").fetchone()[0]
        == first["hit_count"]
    )


def test_day_run_does_not_rewind_ingestion_cursor(tmp_path):
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "wm.sqlite"
    incremental = run(
        since="last", store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root
    )
    assert incremental["hit_count"] >= 1
    run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    again = run(since="last", store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    assert again["hit_count"] == 0
    assert again["asof_days"] == []


def test_since_last_picks_up_late_arriving_earlier_booking(tmp_path):
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "late.sqlite"
    run(since="last", store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    base = schema.validate(pq.read_table(fx.OUT))[0]
    seed = base.slice(0, 1).to_pylist()[0]
    late = seed | {
        "entry_id": "FXLATE001",
        "cif_id": "CIF00999",
        "account_id": "ACC00999",
        "amount": Decimal("12000.00"),
        "credit_debit": "CRDT",
        "btc_family": "CNTR",
        "btc_subfamily": "CDPT",
        "channel": "TELLER",
        "business_date": fx.DEMO_DAY,
        "booking_ts": datetime(2023, 7, 14, 8, 0, 0),
        "raw_ref": "fixture:late",
        "typology_label": None,
    }
    late_path = tmp_path / "late.parquet"
    pq.write_table(pa.Table.from_pylist(base.to_pylist() + [late], schema=schema.ENTRY), late_path)
    second = run(
        since="last", store="sqlite", sqlite_path=db, parquet=late_path, rules_dir=rules_root
    )
    assert second["hit_count"] >= 1
    assert any(h["customer_id"] == "CIF00999" for h in second["_hits_by_rule"]["r00"])


def test_rule_version_rejects_param_change_without_bump(tmp_path):
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "ver.sqlite"
    run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    spec_path = rules_root / "r00_example" / "rule.yaml"
    spec = yaml.safe_load(spec_path.read_text())
    spec["params"]["threshold_usd"] = 20000.0
    spec_path.write_text(yaml.safe_dump(spec))
    with pytest.raises(RuleError, match="bump version"):
        run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    spec["version"] = int(spec["version"]) + 1
    spec_path.write_text(yaml.safe_dump(spec))
    ok = run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    assert ok["hit_count"] == 0


def test_rule_version_rejects_tier_multiplier_change_without_bump(tmp_path):
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "tier.sqlite"
    run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    spec_path = rules_root / "r00_example" / "rule.yaml"
    spec = yaml.safe_load(spec_path.read_text())
    spec["tier_multipliers"] = {"low": 1.0, "medium": 2.0, "high": 1.0}
    spec_path.write_text(yaml.safe_dump(spec))
    with pytest.raises(RuleError, match="bump version"):
        run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)


def test_duplicate_hit_identities_fail_before_write(tmp_path):
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    shutil.copytree(RULES / "_schema", rules_root / "_schema")
    rule_dir = rules_root / "r00_dup"
    rule_dir.mkdir()
    (rule_dir / "rule.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "r00",
                "name": "Duplicate identity repro",
                "owner": "example",
                "version": 1,
                "mode": "live",
                "key": "customer",
                "windows": {"lookback_days": 1},
                "params": {"threshold_usd": 1.0},
                "weight": 1.0,
                "red_flag_ids": ["RF-004"],
                "budget_per_month": 10,
                "description": "Deliberately returns two rows with the same hit identity.",
                "tier_multipliers": {"low": 1.0, "medium": 1.0, "high": 1.0},
            }
        )
    )
    (rule_dir / "rule.sql").write_text(
        """
SELECT 'CIF00001' AS customer_id, NULL::VARCHAR AS account_id,
       DATE '{{ asof }}' AS business_day, 'CIF00001' AS group_key,
       ['A']::VARCHAR[] AS matched_txn_ids,
       to_json({'which': 1}) AS computed_values
UNION ALL
SELECT 'CIF00001', NULL::VARCHAR, DATE '{{ asof }}', 'CIF00001',
       ['B']::VARCHAR[], to_json({'which': 2})
"""
    )
    with pytest.raises(RuleError, match="duplicate hit identities"):
        run(
            day=fx.DEMO_DAY,
            store="sqlite",
            sqlite_path=tmp_path / "dup.sqlite",
            parquet=fx.OUT,
            rules_dir=rules_root,
        )


def test_duplicate_rule_ids_across_folders_fail(tmp_path):
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    shutil.copytree(rules_root / "r00_example", rules_root / "r00_copy")
    with pytest.raises(RuleError, match="duplicate rule id"):
        run(
            day=fx.DEMO_DAY,
            store="sqlite",
            sqlite_path=tmp_path / "ids.sqlite",
            parquet=fx.OUT,
            rules_dir=rules_root,
        )


def test_day_and_since_rejected():
    with pytest.raises(RuleError, match="not both"):
        run(day=fx.DEMO_DAY, since="last", store="sqlite", sqlite_path=Path(":memory:"))


def test_load_rule_r00_example():
    rule = load_rule(RULES / "r00_example")
    assert rule.rule_id == "r00"
    assert rule.mode == "off"
    sql = render_sql(rule.sql_template, params=rule.spec["params"], asof=fx.DEMO_DAY)
    assert "10000" in sql
