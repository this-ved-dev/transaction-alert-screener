-- Rule SQL contract (DuckDB). The engine provides:
--   view  entries         canonical entries (camt.054-shaped; see docs/05-architecture.md)
--   view  customers       cif_id, risk_tier, ...
--   Jinja asof            the business day being run (DATE)
--   Jinja params.<key>    from rule.yaml, after tier multipliers are applied by the engine
--   (no Jinja braces in comments: they are rendered too)
-- It must return exactly these six columns (screener.schema.HIT_COLUMNS):
--   customer_id, account_id, business_day,
--   group_key (VARCHAR, never NULL: the value of rule.yaml key, e.g. cif_id, account_id, country),
--   matched_txn_ids (LIST<VARCHAR>), computed_values (JSON)
-- and at most one row per (customer_id, business_day, group_key): hits upsert on that key.
SELECT
    e.cif_id                                   AS customer_id,
    NULL::VARCHAR                              AS account_id,
    e.business_date                            AS business_day,
    e.cif_id                                   AS group_key,  -- key: customer
    list(e.entry_id)                           AS matched_txn_ids,
    to_json({'cash_in_total': sum(e.amount), 'threshold': {{ params.threshold_usd }}}) AS computed_values
FROM entries e
WHERE e.btc_family = 'CNTR' AND e.btc_subfamily = 'CDPT' AND e.credit_debit = 'CRDT'
  AND e.business_date = DATE '{{ asof }}'
GROUP BY e.cif_id, e.business_date
HAVING sum(e.amount) > {{ params.threshold_usd }};
