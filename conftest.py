"""Shared fixtures for ``tests/`` and ``rules/*/test_rule.py``."""

import pytest


@pytest.fixture(scope="session")
def fixture_run():
    """Run every rule over the fixture Parquet once per session (TRA-21)."""
    pytest.importorskip("screener.engine", reason="rules engine not built yet (TRA-21)")
    from screener.engine import run_fixtures  # noqa: PLC0415

    return run_fixtures()
