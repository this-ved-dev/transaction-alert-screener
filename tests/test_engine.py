"""Rules engine core (TRA-21): discover, validate, render, run, upsert, manifest."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

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

# Same SQL as tests/test_contracts.py — two accounts of CIF00001 on DEMO_DAY.
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


def test_discover_includes_every_folder_with_rule_yaml():
    names = {p.name for p in discover_rules()}
    assert "r00_example" in names
    assert "r10_round_dollar" in names


def test_new_rule_folder_picked_up_without_code_change(tmp_path):
    """AC: adding rules/r99_tmp/ is discovered with no engine change (temp tree, no residue)."""
    rules_root = tmp_path / "rules"
    rules_root.mkdir()
    # Seed with the real example so the tree looks like production, then add r99_tmp.
    shutil.copytree(RULES / "r00_example", rules_root / "r00_example")
    dest = rules_root / "r99_tmp"
    shutil.copytree(RULES / "r00_example", dest)
    assert dest in discover_rules(rules_root)
    assert (dest / "rule.yaml").exists()


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


def test_run_day_loads_all_yaml_folders_runs_live_and_shadow_writes_manifest(tmp_path):
    """AC + scope: discover every rule.yaml; execute live/shadow (not off); write hits + manifest.

    r00 stays ``off`` in the repo (template default). Here we flip a copy to live so the
    CLI-equivalent path is proven to execute the example and persist hits.
    """
    db = tmp_path / "screener.sqlite"
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    # Also drop a shadow sibling to prove shadow hits are stored.
    shadow = rules_root / "r00_shadow"
    shutil.copytree(rules_root / "r00_example", shadow)
    spec = yaml.safe_load((shadow / "rule.yaml").read_text())
    spec["mode"] = "shadow"
    spec["version"] = 99
    (shadow / "rule.yaml").write_text(yaml.safe_dump(spec))

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
    assert manifest["input_hashes"]["parquet"]
    assert manifest["asof_day"] == fx.DEMO_DAY.isoformat()
    assert Path(db).exists()
    modes = {row["mode"] for row in manifest["rule_versions"]}
    assert modes == {"live", "shadow"}


def test_default_run_skips_off_but_still_loads_r00_example(tmp_path):
    """Production ``screener run`` skips mode=off; r00_example is discovered and validated."""
    db = tmp_path / "off.sqlite"
    # Real rules dir: r00 is off, r10 is live.
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
    """AC: mirror test_two_accounts_of_one_customer_survive_repeated_hourly_upserts via engine."""
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
        "WHERE customer_id = 'CIF00001' ORDER BY group_key"
    ).fetchall()
    assert len(rows) == 2
    assert rows[0][0] == "ACC00001"
    assert rows[1][0] == "ACC00201"
    # Rerun must update in place (still two rows), not overwrite one account with the other.
    totals = [Decimal(str(json.loads(r[2])["cash_in_total"])) for r in rows]
    assert totals == [Decimal("6000"), Decimal("4500")]
    assert con.execute("SELECT count(*) FROM hit").fetchone()[0] == 2


def test_since_twice_over_same_data_yields_identical_hit_counts(tmp_path):
    """Client AC: running --since twice over the same data yields identical hit counts."""
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "since.sqlite"
    since = "2000-01-01T00:00:00"
    first = run(since=since, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    second = run(since=since, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    assert first["hit_count"] >= 1
    assert first["hit_count"] == second["hit_count"]
    assert first["mode"] == second["mode"] == "since"
    assert first["watermark"] == second["watermark"]
    con = sqlite3.connect(db)
    # Upserts are idempotent: store has one row per HIT_IDENTITY, not doubled.
    assert con.execute("SELECT count(*) FROM hit").fetchone()[0] == first["hit_count"]


def test_day_run_does_not_rewind_ingestion_cursor(tmp_path):
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "wm.sqlite"
    incremental = run(
        since="last",
        store="sqlite",
        sqlite_path=db,
        parquet=fx.OUT,
        rules_dir=rules_root,
    )
    assert incremental["hit_count"] >= 1
    run(
        day=fx.DEMO_DAY,
        store="sqlite",
        sqlite_path=db,
        parquet=fx.OUT,
        rules_dir=rules_root,
    )
    again = run(since="last", store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    # --day must not clear processed_entry; --since last sees no new ids.
    assert again["hit_count"] == 0
    assert again["asof_days"] == []


def test_since_last_picks_up_late_arriving_earlier_booking(tmp_path):
    """P1: entry booked before the watermark but ingested later is still screened."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    from screener import schema

    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "late.sqlite"
    base = schema.validate(pq.read_table(fx.OUT))[0]
    # First incremental: process current fixture, advance cursor.
    run(since="last", store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    # Late arrival: new entry_id, booking_ts earlier than noon watermark on DEMO_DAY.
    seed = base.slice(0, 1).to_pylist()[0]
    late = seed | {
        "entry_id": "FXLATE001",
        "cif_id": "CIF00999",
        "account_id": "ACC00999",
        "amount": __import__("decimal").Decimal("12000.00"),
        "credit_debit": "CRDT",
        "btc_family": "CNTR",
        "btc_subfamily": "CDPT",
        "channel": "TELLER",
        "business_date": fx.DEMO_DAY,
        "booking_ts": __import__("datetime").datetime(2023, 7, 14, 8, 0, 0),
        "raw_ref": "fixture:late",
        "typology_label": None,
    }
    combined = pa.Table.from_pylist(base.to_pylist() + [late], schema=schema.ENTRY)
    late_path = tmp_path / "late.parquet"
    pq.write_table(combined, late_path)
    second = run(
        since="last", store="sqlite", sqlite_path=db, parquet=late_path, rules_dir=rules_root
    )
    assert second["hit_count"] >= 1
    assert any(h["customer_id"] == "CIF00999" for h in second["_hits_by_rule"]["r00"])


def test_rule_version_rejects_param_change_without_bump(tmp_path):
    """P1: mutating params under the same version must fail; hits keep their definition."""
    rules_root = _live_rules_copy(tmp_path, "r00_example")
    db = tmp_path / "ver.sqlite"
    run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    spec_path = rules_root / "r00_example" / "rule.yaml"
    spec = yaml.safe_load(spec_path.read_text())
    spec["params"]["threshold_usd"] = 20000.0  # same version
    spec_path.write_text(yaml.safe_dump(spec))
    with pytest.raises(RuleError, match="bump version"):
        run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    # Bumping version is accepted.
    spec["version"] = int(spec["version"]) + 1
    spec_path.write_text(yaml.safe_dump(spec))
    ok = run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    assert ok["hit_count"] == 0  # 10500 no longer exceeds 20000


def test_rule_version_rejects_tier_multiplier_change_without_bump(tmp_path):
    """P2: tier_multipliers are part of the immutable definition."""
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
    """P2: one execution returning the same HIT_IDENTITY twice must not silently overwrite."""
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
       to_json({'which': 1, 'threshold': {{ params.threshold_usd }}}) AS computed_values
UNION ALL
SELECT 'CIF00001', NULL::VARCHAR, DATE '{{ asof }}', 'CIF00001',
       ['B']::VARCHAR[], to_json({'which': 2, 'threshold': {{ params.threshold_usd }}})
"""
    )
    db = tmp_path / "dup.sqlite"
    with pytest.raises(RuleError, match="duplicate hit identities"):
        run(day=fx.DEMO_DAY, store="sqlite", sqlite_path=db, parquet=fx.OUT, rules_dir=rules_root)
    con = sqlite3.connect(db)
    assert con.execute("SELECT count(*) FROM hit").fetchone()[0] == 0


def test_load_rule_r00_example():
    rule = load_rule(RULES / "r00_example")
    assert rule.rule_id == "r00"
    assert rule.mode == "off"
    sql = render_sql(rule.sql_template, params=rule.spec["params"], asof=fx.DEMO_DAY)
    assert "10000" in sql
