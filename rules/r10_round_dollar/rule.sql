-- Thirty calendar dates, including asof. Decimal modulo avoids floating-point tolerance.
SELECT
    cif_id AS customer_id,
    NULL::VARCHAR AS account_id,
    DATE '{{ asof }}' AS business_day,
    cif_id AS group_key,
    list(entry_id ORDER BY entry_id) AS matched_txn_ids,
    to_json({
        'entry_count': count(*),
        'total_amount': sum(amount),
        'required_count': {{ params.min_count }},
        'window_days': {{ params.window_days }},
        'multiple_of': {{ params.multiple_of }},
        'min_amount': {{ params.min_amount }}
    }) AS computed_values
FROM entries
WHERE business_date BETWEEN DATE '{{ asof }}' - ({{ params.window_days }} - 1)::INTEGER
                        AND DATE '{{ asof }}'
  AND status = 'BOOK' AND NOT is_reversal AND currency = 'USD'
  AND btc_family <> 'CNTR'
  AND NOT (btc_family = 'CCRD' AND btc_subfamily = 'CWDL')
  AND amount >= {{ params.min_amount }}
  AND amount % {{ params.multiple_of }} = 0
GROUP BY cif_id
HAVING count(*) >= {{ params.min_count }};
