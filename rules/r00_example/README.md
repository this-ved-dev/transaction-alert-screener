# r00 — example rule folder

Copy to `rules/rNN_<slug>/`, then fill in the six files. Nothing outside your folder needs to change
for the engine, the alert page, the injector framework or the agent to pick your rule up.

| File | Contract |
|---|---|
| `rule.yaml` | validated against `rules/_schema/rule.schema.json`; bump `version` on any change |
| `rule.sql` | DuckDB; returns `customer_id, account_id, business_day, group_key, matched_txn_ids, computed_values`, one row per (customer_id, business_day, group_key); `group_key` is the value of `key` (cif_id, account_id, country, beneficiary account …), never NULL |
| `inject.py` | `inject(df, rng, n) -> (df, cases)`; label-blind; cases go to `data/answer_key.json` |
| `explain.py` | `evidence(hit, entries) -> list[EvidenceItem]`; no LLM calls here |
| `evidence.html` | Django partial; receives `hit` and `txns`; autoescaped |
| `test_rule.py` | boundary fixtures + answer-key recall ≥ 0.9 |

Measured numbers (volume per month at 100k accounts, precision, recall, lift) go in `docs/09-evaluation.md`.
