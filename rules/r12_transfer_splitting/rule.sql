-- Use each customer's own booked leg: DBIT for the pair, CRDT for the receiver funnel.
-- New means no relationship in the 90-date history BEFORE the current seven-date window.
WITH payments AS (
    SELECT e.* FROM entries e
    WHERE e.business_date <= DATE '{{ asof }}'
      AND e.status = 'BOOK' AND NOT e.is_reversal AND e.currency = 'USD'
      AND e.btc_domain = 'PMNT' AND e.btc_family <> 'CNTR'
      AND NOT (e.btc_family = 'CCRD' AND e.btc_subfamily = 'CWDL')
      AND e.amount > 0
      AND e.debtor_account IS NOT NULL AND e.creditor_account IS NOT NULL
      AND e.debtor_account <> '' AND e.creditor_account <> ''
      AND e.debtor_account <> e.creditor_account
      AND NOT EXISTS (
          SELECT 1 FROM entries own
          WHERE own.cif_id = e.cif_id
            AND own.account_id = CASE e.credit_debit WHEN 'DBIT' THEN e.creditor_account
                                                     ELSE e.debtor_account END
      )
), small AS (
    SELECT * FROM payments WHERE amount <= {{ params.a_max_single }}
), pairs AS (
    SELECT cif_id AS customer_id, debtor_account AS account_id,
        DATE '{{ asof }}' AS business_day,
        'a:' || debtor_account || '>' || creditor_account AS group_key,
        list(entry_id ORDER BY entry_id) AS matched_txn_ids,
        to_json({'variant': 'a', 'entry_count': count(*), 'total_amount': sum(amount),
                 'required_count': {{ params.a_min_count }},
                 'min_total': {{ params.a_min_total }},
                 'max_single': {{ params.a_max_single }},
                 'window_days': {{ params.a_window_days }}}) AS computed_values
    FROM small
    WHERE credit_debit = 'DBIT' AND account_id = debtor_account
      AND business_date >= DATE '{{ asof }}' - ({{ params.a_window_days }} - 1)::INTEGER
    GROUP BY cif_id, debtor_account, creditor_account
    HAVING count(*) >= {{ params.a_min_count }} AND sum(amount) >= {{ params.a_min_total }}
       AND max(business_date) = DATE '{{ asof }}'
), inbound AS (
    SELECT s.*,
        NOT EXISTS (
            SELECT 1 FROM payments history
            WHERE history.debtor_account = s.debtor_account
              AND history.creditor_account = s.creditor_account
              AND history.business_date >= DATE '{{ asof }}'
                  - ({{ params.b_window_days }} - 1)::INTEGER
                  - {{ params.b_new_sender_lookback_days }}::INTEGER
              AND history.business_date < DATE '{{ asof }}'
                  - ({{ params.b_window_days }} - 1)::INTEGER
        ) AS new_sender
    FROM small s
    WHERE s.credit_debit = 'CRDT' AND s.account_id = s.creditor_account
      AND s.business_date >= DATE '{{ asof }}' - ({{ params.b_window_days }} - 1)::INTEGER
)
SELECT * FROM pairs
UNION ALL
SELECT cif_id AS customer_id, creditor_account AS account_id,
    DATE '{{ asof }}' AS business_day, 'b:' || creditor_account AS group_key,
    list(entry_id ORDER BY entry_id) AS matched_txn_ids,
    to_json({'variant': 'b', 'sender_count': count(DISTINCT debtor_account),
             'new_sender_count': count(DISTINCT debtor_account) FILTER (WHERE new_sender),
             'entry_count': count(*), 'total_amount': sum(amount),
             'min_senders': {{ params.b_min_senders }},
             'min_new_senders': {{ params.b_min_new_senders }},
             'min_total': {{ params.a_min_total }},
             'max_single': {{ params.a_max_single }},
             'window_days': {{ params.b_window_days }},
             'history_days': {{ params.b_new_sender_lookback_days }}}) AS computed_values
FROM inbound
GROUP BY cif_id, creditor_account
HAVING count(DISTINCT debtor_account) >= {{ params.b_min_senders }}
   AND count(DISTINCT debtor_account) FILTER (WHERE new_sender) >= {{ params.b_min_new_senders }}
   AND sum(amount) >= {{ params.a_min_total }} AND max(business_date) = DATE '{{ asof }}';
