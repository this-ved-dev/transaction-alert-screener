"""Shared fixtures.

`fixture_run` runs every rule over the fixture Parquet once per session (rules engine ticket).
"""

import pytest


@pytest.fixture(scope="session")
def fixture_run():
    pytest.importorskip("screener.engine", reason="rules engine not built yet (TRA-21)")
    from screener.engine import run_fixtures  # noqa: PLC0415  (import inside fixture on purpose)

    return run_fixtures()
