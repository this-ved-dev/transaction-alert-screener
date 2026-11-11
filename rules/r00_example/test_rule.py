"""Per-rule tests.

Boundary fixtures live in data/fixtures; the engine fixture comes from tests/conftest.py.

Until TRA-6 and TRA-21 land there is no engine, so these tests are skipped, not failing.
"""

import pytest

engine = pytest.importorskip("screener.engine", reason="rules engine not built yet (TRA-21)")


def test_fires_above_threshold(fixture_run):
    hits = fixture_run.hits("r00")
    assert any(h["computed_values"]["cash_in_total"] > 10000 for h in hits)
