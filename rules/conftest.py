"""Per-rule tests need ``fixture_run`` when CI runs ``pytest rules`` alone."""

import pytest


@pytest.fixture(scope="session")
def fixture_run():
    pytest.importorskip("screener.engine", reason="rules engine not built yet (TRA-21)")
    from screener.engine import run_fixtures  # noqa: PLC0415

    return run_fixtures()
