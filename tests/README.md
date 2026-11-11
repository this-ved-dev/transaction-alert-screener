# tests/

- `test_contracts.py` runs from day 0 and in the CI `rules` job: every rule folder validates against the schema, red-flag ids resolve, params are used, hostile memos exist, every tran-code map triplet is in the ISO codification, the fixture Parquet is reproducible, current and under 1 MB, quarantine rejects exactly its planted bad rows, and every `rule.sql` returns the five hit columns on it.
- `conftest.py` provides `fixture_run` once TRA-21 exists; until then rule tests are skipped (not failed).
- `integration/` (TRA-11, TRA-35): Postgres-marked tests (`-m integration`), run by the CI `integration` job.
