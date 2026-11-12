"""Rules engine: discover rule folders, validate, render, execute, upsert hits.

Design: rules are SQL templates in ``rules/r??_*/``; the engine globs the folders,
renders Jinja params (StrictUndefined), runs DuckDB over canonical Parquet, and
upserts hits on ``schema.HIT_IDENTITY``. Adding a rule never requires touching
shared code. Consolidation/alerts are TRA-22; backtest is TRA-23.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import duckdb
import jinja2
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
import yaml
from jsonschema import Draft202012Validator

from screener import schema
from screener.adapters import fixtures as fx

ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "rules"
SCHEMA_PATH = RULES_DIR / "_schema" / "rule.schema.json"
FIXTURE_PATH = ROOT / "data" / "fixtures" / "fixture.parquet"
COUNTRY_RISK_PATH = ROOT / "data" / "reference" / "country_risk.csv"
HOLIDAYS_PATH = ROOT / "data" / "reference" / "holidays_us.csv"
DEFAULT_SQLITE = ROOT / "data" / "screener.sqlite"

RULE_DIR_RE = re.compile(r"^r\d{2}_.+$")
RunMode = Literal["day", "since", "reconcile"]

_JINJA = jinja2.Environment(undefined=jinja2.StrictUndefined)  # noqa: S701  (SQL, not HTML)


class RuleError(Exception):
    """Invalid rule.yaml, missing files, or unknown Jinja param."""


@dataclass
class LoadedRule:
    path: Path
    spec: dict[str, Any]
    sql_template: str

    @property
    def rule_id(self) -> str:
        return self.spec["id"]

    @property
    def version(self) -> int:
        return self.spec["version"]

    @property
    def mode(self) -> str:
        return self.spec["mode"]


@dataclass
class FixtureRun:
    """Result of ``run_fixtures()`` for per-rule tests (``fixture_run.hits("r00")``)."""

    run_id: str
    asof: date
    manifest: dict[str, Any]
    _hits: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def hits(self, rule_id: str) -> list[dict[str, Any]]:
        return list(self._hits.get(rule_id, []))


def _rule_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def discover_rules(rules_dir: Path = RULES_DIR) -> list[Path]:
    """Return ``rules/r??_*/`` folders that contain a ``rule.yaml``, sorted by name."""
    if not rules_dir.is_dir():
        return []
    found = [
        p
        for p in sorted(rules_dir.iterdir())
        if p.is_dir() and RULE_DIR_RE.match(p.name) and (p / "rule.yaml").exists()
    ]
    return found


def load_rule(rule_dir: Path) -> LoadedRule:
    """Validate ``rule.yaml`` against the JSON schema and load ``rule.sql``."""
    yaml_path = rule_dir / "rule.yaml"
    sql_path = rule_dir / "rule.sql"
    if not yaml_path.exists():
        raise RuleError(f"{rule_dir.name}: rule.yaml missing")
    if not sql_path.exists():
        raise RuleError(f"{rule_dir.name}: rule.sql missing")
    try:
        spec = yaml.safe_load(yaml_path.read_text())
    except yaml.YAMLError as e:
        raise RuleError(f"{rule_dir.name}: invalid YAML: {e}") from e
    errors = sorted(Draft202012Validator(_rule_schema()).iter_errors(spec), key=str)
    if errors:
        messages = "; ".join(e.message for e in errors)
        raise RuleError(f"{rule_dir.name}: invalid rule.yaml: {messages}")
    if spec["id"] != rule_dir.name[:3]:
        raise RuleError(
            f"{rule_dir.name}: folder prefix {rule_dir.name[:3]!r} != id {spec['id']!r}"
        )
    return LoadedRule(path=rule_dir, spec=spec, sql_template=sql_path.read_text())


def apply_tier_multipliers(params: dict[str, Any], tier_multipliers: dict[str, float]) -> dict:
    """Apply the default (medium) tier multiplier to monetary params.

    Client thresholds are flat (1.0/1.0/1.0), so this is a no-op until the admin
    console sets non-unit multipliers. Counts/windows stay intact.
    """
    factor = float(tier_multipliers.get("medium", 1.0))
    if factor == 1.0:
        return dict(params)
    out: dict[str, Any] = {}
    for key, value in params.items():
        scale = (
            isinstance(value, int | float)
            and not isinstance(value, bool)
            and ("threshold" in key or key.endswith("_usd") or "amount" in key)
        )
        out[key] = value * factor if scale else value
    return out


def _max_window_days(rules: list[LoadedRule]) -> int:
    """Largest look-back among active rules (windows.* and params.*_days)."""
    widest = 1
    for rule in rules:
        for value in (rule.spec.get("windows") or {}).values():
            if isinstance(value, int) and value > widest:
                widest = value
        for key, value in (rule.spec.get("params") or {}).items():
            if isinstance(value, int) and "day" in key and value > widest:
                widest = value
    return widest


def render_sql(sql_template: str, *, params: dict[str, Any], asof: date) -> str:
    """Render ``rule.sql`` with Jinja StrictUndefined (unknown params fail fast)."""
    try:
        return _JINJA.from_string(sql_template).render(params=params, asof=asof.isoformat())
    except jinja2.UndefinedError as e:
        raise RuleError(f"unknown param in SQL: {e}") from e


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _open_duckdb(
    entries_table,
    *,
    country_risk: Path = COUNTRY_RISK_PATH,
    holidays: Path = HOLIDAYS_PATH,
) -> duckdb.DuckDBPyConnection:
    """DuckDB with views rules may read: entries (no typology_label), customers, refs."""
    con = duckdb.connect()
    cols = [c for c in entries_table.column_names if c != "typology_label"]
    con.register("_entries_arrow", entries_table.select(cols))
    con.execute("CREATE VIEW entries AS SELECT * FROM _entries_arrow")
    con.execute(
        "CREATE VIEW customers AS SELECT DISTINCT cif_id, 'low'::VARCHAR AS risk_tier FROM entries"
    )
    con.register("_country_risk", pacsv.read_csv(country_risk))
    con.register("_holidays", pacsv.read_csv(holidays))
    con.execute("CREATE VIEW country_risk AS SELECT * FROM _country_risk")
    con.execute("CREATE VIEW holidays AS SELECT * FROM _holidays")
    return con


# --- persistence (SQLite; Postgres wired later via DATABASE_URL) -----------------


def _connect_store(store: Literal["sqlite", "postgres"], sqlite_path: Path) -> Any:
    if store == "postgres":
        import os

        import psycopg

        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuleError("DATABASE_URL required for --store postgres")
        conn = psycopg.connect(url)
        _ensure_schema_postgres(conn)
        return conn
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    _ensure_schema_sqlite(conn)
    return conn


def _ensure_schema_sqlite(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rule_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            mode TEXT NOT NULL,
            params TEXT NOT NULL,
            weight REAL NOT NULL,
            red_flag_ids TEXT NOT NULL,
            UNIQUE (rule_id, version)
        );
        CREATE TABLE IF NOT EXISTS run (
            id TEXT PRIMARY KEY,
            asof_day TEXT,
            mode TEXT NOT NULL,
            watermark TEXT,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            input_hashes TEXT NOT NULL,
            rule_versions TEXT NOT NULL,
            hit_count INTEGER NOT NULL,
            entry_count INTEGER NOT NULL,
            manifest TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS hit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            rule_version_id INTEGER NOT NULL,
            customer_id TEXT NOT NULL,
            account_id TEXT,
            business_day TEXT NOT NULL,
            group_key TEXT NOT NULL,
            matched_txn_ids TEXT NOT NULL,
            computed_values TEXT NOT NULL,
            UNIQUE (rule_version_id, customer_id, business_day, group_key)
        );
        CREATE TABLE IF NOT EXISTS engine_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    conn.commit()


def _ensure_schema_postgres(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rule_version (
                id SERIAL PRIMARY KEY,
                rule_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                mode TEXT NOT NULL,
                params JSONB NOT NULL,
                weight DOUBLE PRECISION NOT NULL,
                red_flag_ids JSONB NOT NULL,
                UNIQUE (rule_id, version)
            );
            CREATE TABLE IF NOT EXISTS run (
                id TEXT PRIMARY KEY,
                asof_day DATE,
                mode TEXT NOT NULL,
                watermark TIMESTAMPTZ,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ NOT NULL,
                duration_ms INTEGER NOT NULL,
                input_hashes JSONB NOT NULL,
                rule_versions JSONB NOT NULL,
                hit_count INTEGER NOT NULL,
                entry_count INTEGER NOT NULL,
                manifest JSONB NOT NULL
            );
            CREATE TABLE IF NOT EXISTS hit (
                id SERIAL PRIMARY KEY,
                run_id TEXT NOT NULL,
                rule_version_id INTEGER NOT NULL,
                customer_id TEXT NOT NULL,
                account_id TEXT,
                business_day DATE NOT NULL,
                group_key TEXT NOT NULL,
                matched_txn_ids JSONB NOT NULL,
                computed_values JSONB NOT NULL,
                UNIQUE (rule_version_id, customer_id, business_day, group_key)
            );
            CREATE TABLE IF NOT EXISTS engine_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
    conn.commit()


def _upsert_rule_version(conn, rule: LoadedRule, store: str) -> int:
    params_json = json.dumps(rule.spec["params"], sort_keys=True)
    flags_json = json.dumps(rule.spec["red_flag_ids"])
    if store == "sqlite":
        conn.execute(
            """
            INSERT INTO rule_version (rule_id, version, mode, params, weight, red_flag_ids)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (rule_id, version) DO UPDATE SET
                mode = excluded.mode,
                params = excluded.params,
                weight = excluded.weight,
                red_flag_ids = excluded.red_flag_ids
            """,
            (
                rule.rule_id,
                rule.version,
                rule.mode,
                params_json,
                float(rule.spec["weight"]),
                flags_json,
            ),
        )
        row = conn.execute(
            "SELECT id FROM rule_version WHERE rule_id = ? AND version = ?",
            (rule.rule_id, rule.version),
        ).fetchone()
        return int(row["id"])
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO rule_version (rule_id, version, mode, params, weight, red_flag_ids)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s::jsonb)
            ON CONFLICT (rule_id, version) DO UPDATE SET
                mode = EXCLUDED.mode,
                params = EXCLUDED.params,
                weight = EXCLUDED.weight,
                red_flag_ids = EXCLUDED.red_flag_ids
            RETURNING id
            """,
            (
                rule.rule_id,
                rule.version,
                rule.mode,
                params_json,
                float(rule.spec["weight"]),
                flags_json,
            ),
        )
        return int(cur.fetchone()[0])


def _upsert_hit(
    conn,
    *,
    store: str,
    run_id: str,
    rule_version_id: int,
    row: dict[str, Any],
) -> None:
    matched = row["matched_txn_ids"]
    if isinstance(matched, list):
        matched_json = json.dumps(list(matched))
    else:
        matched_json = json.dumps(list(matched) if matched is not None else [])
    computed = row["computed_values"]
    if isinstance(computed, dict | list):
        computed_json = json.dumps(computed)
    elif isinstance(computed, str):
        computed_json = computed
    else:
        computed_json = json.dumps(computed)
    business_day = row["business_day"]
    if hasattr(business_day, "isoformat"):
        business_day = business_day.isoformat()
    vals = (
        run_id,
        rule_version_id,
        row["customer_id"],
        row["account_id"],
        business_day,
        row["group_key"],
        matched_json,
        computed_json,
    )
    if store == "sqlite":
        conn.execute(
            """
            INSERT INTO hit (
                run_id, rule_version_id, customer_id, account_id, business_day,
                group_key, matched_txn_ids, computed_values
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (rule_version_id, customer_id, business_day, group_key) DO UPDATE SET
                run_id = excluded.run_id,
                account_id = excluded.account_id,
                matched_txn_ids = excluded.matched_txn_ids,
                computed_values = excluded.computed_values
            """,
            vals,
        )
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO hit (
                run_id, rule_version_id, customer_id, account_id, business_day,
                group_key, matched_txn_ids, computed_values
            ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
            ON CONFLICT (rule_version_id, customer_id, business_day, group_key) DO UPDATE SET
                run_id = EXCLUDED.run_id,
                account_id = EXCLUDED.account_id,
                matched_txn_ids = EXCLUDED.matched_txn_ids,
                computed_values = EXCLUDED.computed_values
            """,
            vals,
        )


def _get_watermark(conn, store: str) -> datetime | None:
    if store == "sqlite":
        row = conn.execute("SELECT value FROM engine_state WHERE key = 'watermark'").fetchone()
        return datetime.fromisoformat(row["value"]) if row else None
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM engine_state WHERE key = 'watermark'")
        row = cur.fetchone()
        return datetime.fromisoformat(row[0]) if row else None


def _set_watermark(conn, store: str, watermark: datetime) -> None:
    value = watermark.isoformat(sep="T", timespec="microseconds")
    if store == "sqlite":
        conn.execute(
            "INSERT INTO engine_state (key, value) VALUES ('watermark', ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (value,),
        )
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO engine_state (key, value) VALUES ('watermark', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (value,),
        )


def _save_run(conn, store: str, manifest: dict[str, Any]) -> None:
    payload = (
        manifest["run_id"],
        manifest.get("asof_day"),
        manifest["mode"],
        manifest.get("watermark"),
        manifest["started_at"],
        manifest["finished_at"],
        manifest["duration_ms"],
        json.dumps(manifest["input_hashes"]),
        json.dumps(manifest["rule_versions"]),
        manifest["hit_count"],
        manifest["entry_count"],
        json.dumps(manifest),
    )
    if store == "sqlite":
        conn.execute(
            """
            INSERT INTO run (
                id, asof_day, mode, watermark, started_at, finished_at, duration_ms,
                input_hashes, rule_versions, hit_count, entry_count, manifest
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO run (
                id, asof_day, mode, watermark, started_at, finished_at, duration_ms,
                input_hashes, rule_versions, hit_count, entry_count, manifest
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s::jsonb
            )
            """,
            payload,
        )


def _parse_hit_row(columns: list[str], raw: tuple) -> dict[str, Any]:
    row = dict(zip(columns, raw, strict=True))
    computed = row["computed_values"]
    if isinstance(computed, str):
        row["computed_values"] = json.loads(computed)
    elif computed is not None and not isinstance(computed, dict):
        row["computed_values"] = json.loads(str(computed))
    matched = row["matched_txn_ids"]
    if matched is not None and not isinstance(matched, list):
        row["matched_txn_ids"] = list(matched)
    return row


def _execute_rule(
    duck: duckdb.DuckDBPyConnection, rule: LoadedRule, asof: date
) -> list[dict[str, Any]]:
    multipliers = {
        "low": 1.0,
        "medium": 1.0,
        "high": 1.0,
        **(rule.spec.get("tier_multipliers") or {}),
    }
    params = apply_tier_multipliers(rule.spec["params"], multipliers)
    sql = render_sql(rule.sql_template, params=params, asof=asof)
    rel = duck.sql(sql)
    if tuple(rel.columns) != schema.HIT_COLUMNS:
        raise RuleError(
            f"{rule.rule_id}: SQL must return {schema.HIT_COLUMNS}, got {tuple(rel.columns)}"
        )
    return [_parse_hit_row(list(rel.columns), r) for r in rel.fetchall()]


def _load_entries(parquet: Path):
    table = pq.read_table(parquet)
    valid, _rejected = schema.validate(table)
    return valid


def run(
    *,
    day: date | None = None,
    since: str | None = None,
    reconcile: bool = False,
    store: Literal["sqlite", "postgres"] = "sqlite",
    sqlite_path: Path = DEFAULT_SQLITE,
    parquet: Path = FIXTURE_PATH,
    rules_dir: Path = RULES_DIR,
    include_off: bool = False,
) -> dict[str, Any]:
    """Run live/shadow rules (and optionally ``off``), upsert hits, write a run manifest.

    Modes
    -----
    * ``--day``: evaluate every rule for that business day (full entries look-back).
    * ``--since``: incremental; re-evaluate customer-days touched by new entries.
    * ``--reconcile``: nightly full-day pass (same compute as ``--day``, flagged in manifest).
    """
    if day is None and since is None:
        raise RuleError("pass --day and/or --since")
    if reconcile and day is None:
        raise RuleError("--reconcile requires --day")

    if reconcile:
        mode: RunMode = "reconcile"
    elif since is not None:
        mode = "since"
    else:
        mode = "day"

    started = time.perf_counter()
    started_at = datetime.now().isoformat(timespec="seconds")
    run_id = str(uuid.uuid4())

    entries = _load_entries(parquet)
    duck = _open_duckdb(entries)
    conn = _connect_store(store, sqlite_path)

    try:
        rules = [load_rule(p) for p in discover_rules(rules_dir)]
        active = [r for r in rules if include_off or r.mode in ("live", "shadow")]

        asof_days: list[date] = []
        watermark_out: datetime | None = None

        if since is not None:
            wm = _get_watermark(conn, store) if since == "last" else datetime.fromisoformat(since)
            if wm is None:
                touched = duck.execute("SELECT DISTINCT business_date FROM entries").fetchall()
                max_ts = duck.execute("SELECT max(booking_ts) FROM entries").fetchall()[0][0]
            else:
                touched = duck.execute(
                    "SELECT DISTINCT business_date FROM entries WHERE booking_ts > ?",
                    [wm],
                ).fetchall()
                max_ts = duck.execute(
                    "SELECT max(booking_ts) FROM entries WHERE booking_ts > ?",
                    [wm],
                ).fetchall()[0][0]
            # Entry on day D can change windowed hits on D .. D+(window-1); expand forward.
            base_days = {row[0] for row in touched if row[0] is not None}
            widest = _max_window_days(active)
            data_end = duck.execute("SELECT max(business_date) FROM entries").fetchall()[0][0]
            expanded: set[date] = set()
            for base in base_days:
                for offset in range(widest):
                    candidate = base + timedelta(days=offset)
                    if data_end is None or candidate <= data_end:
                        expanded.add(candidate)
            asof_days = sorted(expanded)
            if max_ts is not None:
                watermark_out = (
                    max_ts if isinstance(max_ts, datetime) else datetime.fromisoformat(str(max_ts))
                )
        elif day is not None:
            asof_days = [day]

        if not asof_days and day is not None:
            asof_days = [day]

        hits_by_rule: dict[str, list[dict[str, Any]]] = {r.rule_id: [] for r in active}
        version_ids: dict[tuple[str, int], int] = {}
        rule_version_manifest: list[dict[str, Any]] = []

        for rule in active:
            vid = _upsert_rule_version(conn, rule, store)
            version_ids[(rule.rule_id, rule.version)] = vid
            rule_version_manifest.append(
                {
                    "rule_id": rule.rule_id,
                    "version": rule.version,
                    "mode": rule.mode,
                    "rule_version_id": vid,
                    "path": rule.path.name,
                }
            )

        hit_count = 0
        for asof in asof_days:
            for rule in active:
                rows = _execute_rule(duck, rule, asof)
                for row in rows:
                    if row.get("group_key") is None:
                        raise RuleError(f"{rule.rule_id}: group_key must never be NULL")
                    _upsert_hit(
                        conn,
                        store=store,
                        run_id=run_id,
                        rule_version_id=version_ids[(rule.rule_id, rule.version)],
                        row=row,
                    )
                    hits_by_rule[rule.rule_id].append(row)
                    hit_count += 1

        # Watermark is the incremental cursor only; --day/--reconcile must not rewind it.
        if mode == "since" and watermark_out is not None:
            _set_watermark(conn, store, watermark_out)

        input_hashes = {
            "parquet": _file_sha256(parquet),
            "rules": {
                r.path.name: {
                    "rule.yaml": _file_sha256(r.path / "rule.yaml"),
                    "rule.sql": _file_sha256(r.path / "rule.sql"),
                }
                for r in active
            },
        }
        finished_at = datetime.now().isoformat(timespec="seconds")
        duration_ms = int((time.perf_counter() - started) * 1000)
        manifest: dict[str, Any] = {
            "run_id": run_id,
            "asof_day": day.isoformat()
            if day
            else (asof_days[0].isoformat() if asof_days else None),
            "asof_days": [d.isoformat() for d in asof_days],
            "mode": mode,
            "watermark": watermark_out.isoformat() if watermark_out else None,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_ms": duration_ms,
            "input_hashes": input_hashes,
            "rule_versions": rule_version_manifest,
            "hit_count": hit_count,
            "entry_count": entries.num_rows,
            "rules_run": [r.rule_id for r in active],
            "store": store,
        }
        _save_run(conn, store, manifest)
        conn.commit()
        manifest["_hits_by_rule"] = hits_by_rule
        return manifest
    finally:
        duck.close()
        conn.close()


def run_fixtures(
    *,
    day: date = fx.DEMO_DAY,
    parquet: Path = FIXTURE_PATH,
    rules_dir: Path = RULES_DIR,
    sqlite_path: Path | None = None,
) -> FixtureRun:
    """Session helper for tests: run every rule folder (including ``off``) on the fixture day."""
    import tempfile

    path = sqlite_path
    if path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)  # noqa: SIM115
        path = Path(tmp.name)
        tmp.close()
    manifest = run(
        day=day,
        store="sqlite",
        sqlite_path=path,
        parquet=parquet,
        rules_dir=rules_dir,
        include_off=True,
    )
    return FixtureRun(
        run_id=manifest["run_id"],
        asof=day,
        manifest={k: v for k, v in manifest.items() if k != "_hits_by_rule"},
        _hits=manifest["_hits_by_rule"],
    )
