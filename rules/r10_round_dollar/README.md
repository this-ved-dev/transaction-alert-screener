# r10_round_dollar

**Owner:** Abdul · **Ticket:** TRA-36 · **Process:** Funds movement

Round-dollar pattern: >=5 non-cash entries in 30 days that are exact multiples of $1,000, each >=$2,000. SAML-D has 79 natural rows and none laundering; proven on injected cases.

Implemented against the TRA-6 schema, independently of TRA-24 and the rules engine.
`rule.sql` returns the six-column hit contract with `group_key = cif_id`, grouping across accounts.
The window includes the run date and the previous 29 calendar dates. Only booked, unreversed USD
entries count. Teller cash (`CNTR`) and ATM cash (`CCRD/CWDL`) are excluded; non-cash card
entries remain eligible. Decimal modulo is exact: $2,000 qualifies and $2,000.01 does not.

`inject(df, rng, n=10)` adds five entries for each of ten isolated synthetic customers, preserving
the input schema and returning an answer key. It never reads labels. Tests run the real SQL
through DuckDB directly, so they do not skip while TRA-21 is pending:

```bash
uv run pytest rules/r10_round_dollar tests/test_contracts.py -q
uv run python scripts/measure_r10.py data/raw/saml_d/SAML-D.csv
```

Measured on 2026-11-11: all ten injected cases detected (100% recall); full SAML-D has 79
qualifying individual entries, zero laundering-labelled entries among them, and zero customer-day
hits over 2022-10-07–2023-08-23. This is a disclosed one-sender-account/one-customer measurement,
not the future synthetic multi-account grouping. It does not establish performance on a real
bank export. Source rows are read locally and never committed.

RF-010 supplies the regulatory red-flag citation. The pattern alone does not establish that a
commercial purpose is absent. `evidence.html` is a basic summary; the full analyst panel and
`explain.py` agent integration remain in TRA-38.
