"""Execute R12 over local SAML-D without importing the unmerged TRA-24 adapter.

Both booked perspectives are projected; one account is one customer. Only aggregate JSON
is printed. Native Structuring receiver coverage is reported separately from hit volume.
"""

import argparse
import hashlib
import json
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import duckdb
import jinja2
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--from-date", type=date.fromisoformat)
    parser.add_argument("--to-date", type=date.fromisoformat)
    args = parser.parse_args()
    rule = yaml.safe_load((ROOT / "rules/r12_transfer_splitting/rule.yaml").read_text())
    template = jinja2.Environment(undefined=jinja2.StrictUndefined).from_string(
        (ROOT / "rules/r12_transfer_splitting/rule.sql").read_text()
    )
    counts, hit_customers, caught = Counter(), {"a": set(), "b": set()}, set()
    alerts = set()
    receiver_hit_coverage = set()
    with duckdb.connect() as con:
        con.execute(
            "CREATE TABLE source AS SELECT * FROM read_csv(?, all_varchar=true)", [str(args.csv)]
        )
        first, last, rows = con.sql(
            "SELECT min(Date::DATE), max(Date::DATE), count(*) FROM source"
        ).fetchall()[0]
        history = rule["params"]["b_window_days"] - 1 + rule["params"]["b_new_sender_lookback_days"]
        args.from_date = args.from_date or first + timedelta(days=history)
        end = args.to_date or last
        if end < args.from_date:
            raise ValueError("to-date must not precede from-date")
        if end > last or args.from_date < first:
            raise ValueError("Measurement dates must be inside the observed source period")
        labelled = {
            r[0]
            for r in con.sql(
                "SELECT DISTINCT Receiver_account FROM source WHERE Laundering_type='Structuring'"
            ).fetchall()
        }
        period_labelled = {
            r[0]
            for r in con.execute(
                "SELECT DISTINCT Receiver_account FROM source WHERE Laundering_type='Structuring' "
                "AND Date::DATE BETWEEN ? AND ?",
                [args.from_date, end],
            ).fetchall()
        }
        accounts = con.sql(
            "SELECT count(*) FROM (SELECT Sender_account FROM source UNION "
            "SELECT Receiver_account FROM source)"
        ).fetchall()[0][0]
        # Keep both legs and unique IDs. Labels remain outside the rule's entries view.
        con.execute("""
            CREATE TABLE edges AS SELECT row_number() OVER () AS row_id, Sender_account,
                Receiver_account, Date::DATE AS business_date, Amount::DECIMAL(38,18) AS amount,
                Laundering_type AS typology_label
            FROM source WHERE Payment_type NOT IN ('Cash Deposit', 'Cash Withdrawal')
        """)
        positive_ids = {
            str(r[0]) + ":CRDT"
            for r in con.sql(
                "SELECT row_id FROM edges WHERE typology_label='Structuring'"
            ).fetchall()
        }
        con.execute("""
            CREATE VIEW entries AS SELECT
                row_id::VARCHAR || ':' || credit_debit AS entry_id,
                account_id, 'saml_d:' || account_id AS cif_id, credit_debit,
                Sender_account AS debtor_account, Receiver_account AS creditor_account,
                amount, business_date, 'USD' AS currency, 'BOOK' AS status,
                false AS is_reversal, 'PMNT' AS btc_domain, 'ICDT' AS btc_family,
                'ATXN' AS btc_subfamily
            FROM (SELECT *, Sender_account AS account_id, 'DBIT' AS credit_debit FROM edges
                  UNION ALL SELECT *, Receiver_account, 'CRDT' FROM edges)
        """)
        for i in range((end - args.from_date).days + 1):
            day = args.from_date + timedelta(days=i)
            hits = con.sql(template.render(params=rule["params"], asof=day.isoformat())).fetchall()
            for hit in hits:
                alerts.add((hit[0], day))
                variant = json.loads(hit[5])["variant"]
                counts[variant] += 1
                hit_customers[variant].add(hit[0])
                if variant == "b" and hit[1] in labelled:
                    receiver_hit_coverage.add(hit[1])
                    if any(entry_id in positive_ids for entry_id in hit[4]):
                        caught.add(hit[1])
    months = ((end - args.from_date).days + 1) / (365.25 / 12)
    with args.csv.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    print(
        json.dumps(
            {
                "rule": "r12",
                "mode": rule["mode"],
                "input_sha256": digest,
                "source_rows": rows,
                "from": str(args.from_date),
                "to": str(end),
                "source_accounts": accounts,
                "hits_by_variant": dict(counts),
                "customers_by_variant": {k: len(v) for k, v in hit_customers.items()},
                "consolidated_customer_day_alerts": len(alerts),
                "alerts_per_month_at_100k": len(alerts) / months * 100000 / accounts,
                "full_history_available": args.from_date >= first + timedelta(days=history),
                "all_structuring_receivers": len(labelled),
                "period_structuring_receivers": len(period_labelled),
                "caught_structuring_receivers": len(caught),
                "caught_period_structuring_receivers": len(caught & period_labelled),
                "labelled_receivers_with_any_hit": len(receiver_hit_coverage),
                "hits_per_month_at_100k": {
                    k: counts[k] / months * 100000 / accounts for k in ("a", "b")
                },
                "customer_proxy": "one account = one customer; both legs; no US grouping",
                "amounts": "exact original source decimals; remeasure after cent normalization",
                "duration_seconds": round(time.monotonic() - started, 3),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
