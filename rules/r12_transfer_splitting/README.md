# r12_transfer_splitting

**Owner:** Abdul · **Ticket:** TRA-37 · **Process:** Funds movement

Transfer splitting: (a) pair-keyed, >=3 transfers originator→beneficiary each <$10,000 totalling >$10,000 in 7 days; (b) funnel variant with a new-sender condition. SAML-D's 'Structuring' label is variant (b).

Version 1 is implemented against the six-column TRA-6 contract. Both variants remain **shadow**.

- Variant **a** groups booked debit legs by customer, originator account and beneficiary
  account. At least three payments of at most $9,999.99 must total at least $10,000.01 within
  the run date and previous six calendar dates. `group_key = 'a:' + sender + '>' + receiver`.
- Variant **b** groups booked credit legs by the receiver's customer and account. At least
  five distinct sender accounts, including three new relationships, must pay the receiver;
  each entry must meet the same amount cap and their total the same minimum as variant a.
  `group_key = 'b:' + receiver`.
- A new relationship has no eligible non-cash payment from that sender to that receiver in
  the 90 calendar dates immediately **before the seven-date window**. Repeated payments
  within the current window do not make a newly observed sender old. Prior payments over
  $10,000 still establish an existing relationship. Measurement needs 96 prior dates.
- Both variants require a qualifying entry on the run date, so a quiet day does not repeat
  an unchanged window's hit. They use booked, unreversed USD payments only; exclude cash,
  fees, interest, missing endpoints, self-payments and transfers between the customer's own
  accounts. Each variant reads only its own booked direction, avoiding double counting when
  both legs exist. Receiver credit legs are required for the funnel; a sender-only export
  needs enrichment before that variant can operate.

`inject(df, rng, n=10)` appends ten seeded, isolated positive **pair** cases and an answer key.
It never reads the typology labels. Funnel behavior and new-sender history are tested with
explicit canonical boundary fixtures in `test_rule.py`.

```bash
uv run pytest rules/r12_transfer_splitting tests/test_contracts.py -q
uv run python scripts/measure_r12.py data/raw/saml_d/SAML-D.csv
```

The measurement script projects both booked directions directly from SAML-D and runs the actual
rule SQL for each date after a complete history warm-up. It prints aggregate hit volume,
consolidated customer-day volume scaled to 100k accounts, and native Structuring receiver
coverage. It does not import the unmerged TRA-24 implementation or export third-party rows.
It uses one account per customer and original decimal amounts; remeasure after US grouping or
cent normalization. Full results and the shadow decision are recorded in `docs/09-evaluation.md`.

RF-007 and RF-012 provide the red-flag citations. The pattern is an investigation indicator,
not a conclusion about intent. Full evidence panels and agent integration remain in TRA-38;
this folder includes only the summary template and explanation placeholder required by the
shared folder contract.
