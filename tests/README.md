# tests/

- `test_contracts.py` runs from day 0 and in the CI `rules` job: every rule folder validates against the schema, red-flag ids resolve, params are used, hostile memos exist, every tran-code map triplet is in the ISO codification, the fixture Parquet is reproducible, current and under 1 MB, quarantine rejects exactly its planted bad rows, every `rule.sql` returns the six hit columns on it with one row per (customer, business day, group_key), and two accounts of one customer keep separate hits through repeated hourly upserts.
- `tests/conftest.py` and `rules/conftest.py` provide `fixture_run` (runs every rule on the fixture Parquet once per session via `run_fixtures()`).
- `integration/` (TRA-11, TRA-35): Postgres-marked tests (`-m integration`), run by the CI `integration` job.
