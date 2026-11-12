# r01_ctr

**Owner:** Vedant · **Ticket:** TRA-15 · **Process:** Cash & CTR

CTR candidate (31 CFR 1010.311/.313, RF-004): cash in, or cash out, above $10,000 per customer per
business day across all accounts and branches. Writes to the CTR candidates list
(`output: ctr_candidate` in `rule.yaml`), not to hits.

- Cash is booked, unreversed USD `PMNT` with subfamily `CDPT` or `CWDL` in family `CNTR` (teller,
  night drop) or `CCRD` (ATM). Fees on the cash counter, card purchases and transfers do not count.
- Cash in and cash out are totalled separately and never netted: one row per direction,
  `group_key = CRDT:<cif_id>` or `DBIT:<cif_id>`. Exactly $10,000.00 does not fire; $10,000.01 does.
- The rule groups on `business_date`, which the adapter rolls forward over weekends and holidays,
  so Saturday and night-drop cash count on the next business day.
- A same-day split past $10,000 is both a CTR candidate here and an R03 hit, by design.
- A reversal entry is not cash and is skipped; the original deposit still counts. The list is
  reconciled against the core.
- Foreign-currency cash (`FCDP`/`FCWD`) is not counted yet; it needs an FX table.

```bash
uv run pytest rules/r01_ctr tests/test_contracts.py -q
uv run python scripts/measure_r01.py data/raw/saml_d/SAML-D.csv
```

Measured 2026-11-11 on full SAML-D: 195 cash-in customer-days, 0 cash-out (docs/09). Five
injected CTR days all caught. `explain.py` is TRA-19; the full evidence panel and CTR page are
TRA-18.
