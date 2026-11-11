"""Measure R10 directly on local SAML-D, without TRA-24, TRA-21 or third-party row exports.

Run: .venv/bin/python scripts/measure_r10.py data/raw/saml_d/SAML-D.csv
One account = one customer; non-cash sender debit perspective. Amounts are checked exactly
before cent conversion; no sampled labels enter the rule SQL. Output is aggregate JSON only.
"""

import argparse
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import duckdb
import jinja2
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    rule = yaml.safe_load((ROOT / "rules/r10_round_dollar/rule.yaml").read_text())
    template = jinja2.Environment(undefined=jinja2.StrictUndefined).from_string(
        (ROOT / "rules/r10_round_dollar/rule.sql").read_text()
    )
    with duckdb.connect() as con:
        con.execute(
            "CREATE TABLE source AS SELECT * FROM read_csv(?, all_varchar=true)", [str(args.csv)]
        )
        start, end, rows = con.sql(
            "SELECT min(Date::DATE), max(Date::DATE), count(*) FROM source"
        ).fetchall()[0]
        # Filter source exact decimals before casting to cents, to avoid manufacturing multiples.
        con.execute(
            """
            CREATE TABLE candidates AS SELECT * FROM source
            WHERE Payment_type NOT IN ('Cash Deposit', 'Cash Withdrawal')
              AND Amount::DECIMAL(38,18) >= ? AND Amount::DECIMAL(38,18) % ? = 0
        """,
            [rule["params"]["min_amount"], rule["params"]["multiple_of"]],
        )
        candidate_count, positives = con.sql(
            "SELECT count(*), count(*) FILTER (WHERE Is_laundering='1') FROM candidates"
        ).fetchall()[0]
        con.execute("""
            CREATE VIEW entries AS SELECT 'S' || row_number() OVER () AS entry_id,
                Sender_account AS account_id, 'saml_d:' || Sender_account AS cif_id,
                Amount::DECIMAL(18,2) AS amount, Date::DATE AS business_date,
                'USD' AS currency, 'BOOK' AS status, false AS is_reversal,
                'ICDT' AS btc_family, 'ATXN' AS btc_subfamily FROM candidates
        """)
        count, customers = 0, set()
        for i in range((end - start).days + 1):
            sql = template.render(
                params=rule["params"], asof=(start + timedelta(days=i)).isoformat()
            )
            hits = con.sql(sql).fetchall()
            count += len(hits)
            customers.update(h[0] for h in hits)
    with args.csv.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    print(
        json.dumps(
            {
                "rule": "r10",
                "version": rule["version"],
                "input_sha256": digest,
                "source_rows": rows,
                "from": str(start),
                "to": str(end),
                "qualifying_source_entries": candidate_count,
                "qualifying_laundering_entries": positives,
                "natural_customer_day_hits": count,
                "natural_customers": len(customers),
                "customer_proxy": "one sender account = one customer; no US grouping",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
