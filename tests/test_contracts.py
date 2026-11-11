"""Contract tests that run from day 0.

Rule folders validate, red flags resolve, params are used, hostile memos are present.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"
SCHEMA = json.loads((RULES / "_schema" / "rule.schema.json").read_text())
RED_FLAGS = {rf["id"]: rf for rf in yaml.safe_load((RULES / "red_flags.yaml").read_text())}
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
