-- Rule SQL contract (DuckDB). The engine provides:
--   view  entries         canonical entries (camt.054-shaped; see docs/05-architecture.md)
--   view  customers       cif_id, risk_tier, ...
--   param {{ asof }}      the business day being run (DATE)
--   param {{ params.* }}  from rule.yaml, after tier multipliers are applied by the engine
-- It must return exactly these five columns:
--   customer_id, account_id, business_day, matched_txn_ids (LIST<VARCHAR>), computed_values (JSON)
SELECT
    e.cif_id                                   AS customer_id,
    NULL                                       AS account_id,
    e.business_date                            AS business_day,
    list(e.entry_id)                           AS matched_txn_ids,
    to_json({'cash_in_total': sum(e.amount), 'threshold': {{ params.threshold_usd }}}) AS computed_values
FROM entries e
WHERE e.btc_family = 'CNTR' AND e.btc_subfamily = 'CDPT' AND e.credit_debit = 'CRDT'
  AND e.business_date = DATE '{{ asof }}'
GROUP BY e.cif_id, e.business_date
HAVING sum(e.amount) > {{ params.threshold_usd }};
