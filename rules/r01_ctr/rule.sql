-- One row per direction per customer-day; group_key CRDT:<cif> / DBIT:<cif> keeps them apart.
-- business_date already carries the weekend and holiday roll-forward (set by the adapter).
SELECT
    e.cif_id AS customer_id,
    NULL::VARCHAR AS account_id,
    e.business_date AS business_day,
    e.credit_debit || ':' || e.cif_id AS group_key,
    list(e.entry_id ORDER BY e.entry_id) AS matched_txn_ids,
    to_json({
        'direction': e.credit_debit,
        'total': sum(e.amount),
        'threshold': {{ params.threshold_usd }}
    }) AS computed_values
FROM entries e
WHERE e.business_date = DATE '{{ asof }}'
  AND e.status = 'BOOK' AND NOT e.is_reversal
  -- shortcut: USD only; foreign-currency cash (FCDP/FCWD) also counts once an FX table exists
  AND e.currency = 'USD'
  AND e.btc_domain = 'PMNT'
  AND e.btc_family IN ('CNTR', 'CCRD')  -- teller/night drop, and ATM
  AND e.btc_subfamily IN ('CDPT', 'CWDL')
GROUP BY e.cif_id, e.business_date, e.credit_debit
HAVING sum(e.amount) > {{ params.threshold_usd }};
