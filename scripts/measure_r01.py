"""Measure R01 directly on local SAML-D, without TRA-24, TRA-21 or third-party row exports.

Run: uv run python scripts/measure_r01.py data/raw/saml_d/SAML-D.csv
One account = one customer: the depositor is the sender of a Cash Deposit and the withdrawer the
receiver of a Cash Withdrawal (data/reference/tran_code_map.csv). Cash rolls forward to the next
business day over weekends and holidays_us.csv. Output is aggregate JSON only.
"""

import argparse
import hashlib
import json
from datetime import timedelta
from pathlib import Path

import duckdb
import jinja2
import yaml

from screener.adapters.fixtures import business_date

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    args = parser.parse_args()
    rule = yaml.safe_load((ROOT / "rules/r01_ctr/rule.yaml").read_text())
    template = jinja2.Environment(undefined=jinja2.StrictUndefined).from_string(
        (ROOT / "rules/r01_ctr/rule.sql").read_text()
    )
    with duckdb.connect() as con:
        con.execute(
            "CREATE TABLE source AS SELECT * FROM read_csv(?, all_varchar=true) "
            "WHERE Payment_type IN ('Cash Deposit', 'Cash Withdrawal')",
            [str(args.csv)],
        )
        start, end, rows = con.sql(
            "SELECT min(Date::DATE), max(Date::DATE), count(*) FROM source"
        ).fetchall()[0]
        days = [start + timedelta(d) for d in range((end - start).days + 1)]
        con.execute("CREATE TABLE cal (dt DATE, bday DATE)")
        con.executemany("INSERT INTO cal VALUES (?, ?)", [(d, business_date(d)) for d in days])
        con.execute("""
            CREATE VIEW entries AS SELECT 'S' || row_number() OVER () AS entry_id,
                CASE WHEN cash_in THEN Sender_account ELSE Receiver_account END AS cif_id,
                CASE WHEN cash_in THEN 'CRDT' ELSE 'DBIT' END AS credit_debit,
                CASE WHEN cash_in THEN 'CDPT' ELSE 'CWDL' END AS btc_subfamily,
                Amount::DECIMAL(18,2) AS amount, cal.bday AS business_date,
                'USD' AS currency, 'BOOK' AS status, false AS is_reversal,
                'PMNT' AS btc_domain, 'CNTR' AS btc_family
            FROM (SELECT *, Payment_type = 'Cash Deposit' AS cash_in FROM source) s
            JOIN cal ON cal.dt = s.Date::DATE
        """)
        hits = {"CRDT": 0, "DBIT": 0}
        customers = set()
        for day in sorted({business_date(d) for d in days}):
            sql = template.render(params=rule["params"], asof=day.isoformat())
            for customer_id, _, _, group_key, _, _ in con.sql(sql).fetchall():
                hits[group_key.split(":")[0]] += 1
                customers.add(customer_id)
    with args.csv.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    print(
        json.dumps(
            {
                "rule": "r01",
                "version": rule["version"],
                "input_sha256": digest,
                "cash_source_rows": rows,
                "from": str(start),
                "to": str(end),
                "cash_in_customer_days": hits["CRDT"],
                "cash_out_customer_days": hits["DBIT"],
                "customers": len(customers),
                "customer_proxy": "one account = one customer; no US multi-account grouping",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
