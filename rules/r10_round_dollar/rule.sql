-- Thirty calendar dates, including asof. Decimal modulo avoids floating-point tolerance.
SELECT
    e.cif_id AS customer_id,
    NULL::VARCHAR AS account_id,
    DATE '{{ asof }}' AS business_day,
    e.cif_id AS group_key,
    list(e.entry_id ORDER BY e.entry_id) AS matched_txn_ids,
    to_json({
        'entry_count': count(*),
        'total_amount': sum(e.amount),
        'required_count': {{ params.min_count }},
        'window_days': {{ params.window_days }},
        'multiple_of': {{ params.multiple_of }},
        'min_amount': {{ params.min_amount }}
    }) AS computed_values
FROM entries e
WHERE e.business_date BETWEEN DATE '{{ asof }}' - ({{ params.window_days }} - 1)::INTEGER
                          AND DATE '{{ asof }}'
  AND e.status = 'BOOK' AND NOT e.is_reversal AND e.currency = 'USD'
  AND e.btc_domain = 'PMNT'  -- payments only: fees and interest are not transfers
  AND e.btc_family <> 'CNTR'
  AND NOT (e.btc_family = 'CCRD' AND e.btc_subfamily = 'CWDL')
  AND e.amount >= {{ params.min_amount }}
  AND e.amount % {{ params.multiple_of }} = 0
  -- Both legs of a transfer between the customer's own accounts would otherwise count twice.
  AND NOT EXISTS (
      SELECT 1 FROM entries own
      WHERE own.cif_id = e.cif_id
        AND own.account_id = CASE e.credit_debit WHEN 'DBIT' THEN e.creditor_account
                                                 ELSE e.debtor_account END
  )
GROUP BY e.cif_id
-- Fire only on a day that adds a qualifying entry, not on every day the window stays full.
HAVING count(*) >= {{ params.min_count }} AND max(e.business_date) = DATE '{{ asof }}';
