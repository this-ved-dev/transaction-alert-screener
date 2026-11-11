"""Injector contract: add labelled cases for this rule to the canonical entries frame.

The US layer calls ``inject(df, rng, n)`` for every rule folder that defines it and writes the
returned cases to ``data/answer_key.json``. Assignments must use ``rng`` only and must never read
``typology_label``; the answer key is the only ground truth for injected cases.
"""

from __future__ import annotations

import polars as pl


def inject(df: pl.DataFrame, rng, n: int = 10) -> tuple[pl.DataFrame, list[dict]]:
    """Return (df_with_injected_rows, cases).

    Each case: {"rule_id": "r00", "customer_id": ..., "business_day": "YYYY-MM-DD",
                "entry_ids": [...], "note": "what makes it positive"}.
    """
    raise NotImplementedError("example only; see rules/r01_ctr once TRA-15 lands")
