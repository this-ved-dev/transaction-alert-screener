-- One account-day hit; retain all qualifying anchors without summing overlapping flows twice.
WITH payments AS (
    SELECT e.* FROM entries e
    WHERE e.status = 'BOOK' AND NOT e.is_reversal AND e.currency = 'USD'
      AND e.btc_domain = 'PMNT' AND e.amount > 0
      AND e.business_date <= DATE '{{ asof }}'
      AND e.booking_ts < DATE '{{ asof }}' + INTERVAL 1 DAY
      AND NOT EXISTS (
          SELECT 1 FROM entries own WHERE own.cif_id = e.cif_id
          AND own.account_id = CASE e.credit_debit WHEN 'CRDT' THEN e.debtor_account
                                                  ELSE e.creditor_account END
      )
), anchors AS (
    SELECT * FROM payments
    WHERE credit_debit = 'CRDT' AND account_id = creditor_account
      AND amount >= {{ params.min_inbound }}
      AND booking_ts >= DATE '{{ asof }}' - INTERVAL '{{ params.outflow_window_hours }} hours'
      AND (NULLIF(debtor_account, '') IS NOT NULL
           OR (btc_family = 'CNTR' AND btc_subfamily = 'CDPT'))
), daily AS (
    SELECT a.entry_id AS anchor_id, a.booking_ts AS anchor_ts, d.day,
           coalesce(sum(p.amount), 0) AS volume
    FROM anchors a
    CROSS JOIN LATERAL generate_series(
        date_trunc('day', a.booking_ts) - INTERVAL '{{ params.baseline_days }} days',
        date_trunc('day', a.booking_ts) - INTERVAL 1 DAY, INTERVAL 1 DAY
    ) d(day)
    LEFT JOIN payments p ON p.account_id = a.account_id
        AND p.booking_ts >= d.day AND p.booking_ts < d.day + INTERVAL 1 DAY
    GROUP BY a.entry_id, a.booking_ts, d.day
), baselines AS (
    SELECT anchor_id,
        CASE WHEN (SELECT min(booking_ts) FROM entries)
                  <= min(anchor_ts) - INTERVAL '{{ params.baseline_days }} days'
             THEN median(volume)::DECIMAL(24, 3) END AS median_daily_volume
    FROM daily GROUP BY anchor_id
), flows AS (
    SELECT a.entry_id AS anchor_id, a.cif_id, a.account_id,
        a.business_date AS inbound_day, a.amount AS inbound_amount, a.booking_ts AS inbound_ts,
        o.entry_id AS outbound_id, o.business_date AS outbound_day,
        o.amount AS outbound_amount, o.booking_ts AS outbound_ts,
        b.median_daily_volume,
        b.median_daily_volume < a.amount * {{ params.quiet_ratio }} AS quiet,
        o.btc_subfamily = 'XBCT' AS cross_border,
        ((SELECT min(booking_ts) FROM entries)
          <= a.booking_ts - INTERVAL '{{ params.baseline_days }} days'
         AND NOT EXISTS (
             SELECT 1 FROM payments prior
             WHERE prior.account_id = a.account_id AND prior.credit_debit = 'DBIT'
               AND prior.creditor_account = o.creditor_account
               AND prior.booking_ts >= a.booking_ts - INTERVAL '{{ params.baseline_days }} days'
               AND prior.booking_ts < a.booking_ts
         )) AS new_beneficiary
    FROM anchors a JOIN baselines b ON b.anchor_id = a.entry_id
    JOIN payments o ON o.account_id = a.account_id AND o.credit_debit = 'DBIT'
      AND o.debtor_account = a.account_id AND NULLIF(o.creditor_account, '') IS NOT NULL
      AND o.creditor_account <> a.account_id
      AND o.booking_ts > a.booking_ts
      AND o.booking_ts <= a.booking_ts + INTERVAL '{{ params.outflow_window_hours }} hours'
      AND (NULLIF(a.debtor_account, '') IS NULL OR o.creditor_account <> a.debtor_account)
), qualifying AS (
    SELECT * FROM flows WHERE quiet OR cross_border OR new_beneficiary
), matched AS (
    SELECT anchor_id, cif_id, account_id, inbound_amount, inbound_ts, median_daily_volume,
        sum(outbound_amount) AS qualifying_outbound,
        list(outbound_id ORDER BY outbound_id) AS outbound_ids,
        bool_or(quiet) AS quiet, bool_or(cross_border) AS cross_border,
        bool_or(new_beneficiary) AS new_beneficiary,
        max(outbound_ts) AS last_outbound_ts
    FROM qualifying
    GROUP BY anchor_id, cif_id, account_id, inbound_amount, inbound_ts, median_daily_volume
    HAVING sum(outbound_amount) >= inbound_amount * {{ params.outflow_ratio }}
       AND greatest(max(inbound_day), max(outbound_day)) = DATE '{{ asof }}'
)
SELECT cif_id AS customer_id, account_id, DATE '{{ asof }}' AS business_day,
    account_id AS group_key,
    list_sort(list_distinct(flatten(list(list_prepend(anchor_id, outbound_ids))))) AS matched_txn_ids,
    to_json({
        'anchor_count': count(*), 'min_inbound': {{ params.min_inbound }},
        'outflow_ratio': {{ params.outflow_ratio }},
        'outflow_window_hours': {{ params.outflow_window_hours }},
        'baseline_days': {{ params.baseline_days }}, 'quiet_ratio': {{ params.quiet_ratio }},
        'anchors': list({'entry_id': anchor_id, 'inbound_amount': inbound_amount,
            'booking_ts': inbound_ts, 'qualifying_outbound': qualifying_outbound,
            'outflow_ratio': qualifying_outbound / inbound_amount,
            'median_daily_volume': median_daily_volume, 'quiet': quiet,
            'cross_border': cross_border, 'new_beneficiary': new_beneficiary,
            'last_outbound_ts': last_outbound_ts, 'outbound_ids': outbound_ids}
            ORDER BY anchor_id)
    }) AS computed_values
FROM matched GROUP BY cif_id, account_id;
