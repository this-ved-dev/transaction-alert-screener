# Adapters

One adapter per source layout. Every adapter fills the canonical fields, sets the BankTransactionCode triplet from
`data/reference/tran_code_map.csv`, writes a `load_batch` row with the reconciliation totals, and writes every row it
cannot map to `rejected_entry` with a reason (client rule: set aside, never drop).

| Adapter | Source | Ticket | Status |
|---|---|---|---|
| `saml_d.py` | SAML-D CSV (primary demo data) | TRA-24 | to build |
| `tide.py` | Tide HI edges + nodes (optional R05 benchmark) | TRA-31 | to build |
| `fixtures.py` | the synthetic 2,000-row fixture (`screener fixtures`; see `data/fixtures/README.md`) | TRA-6 | built |
| `core_csv.py` | the bank's nightly core export (layout unknown; see `docs/14-field-requirements.md`) | TRA-58 | skeleton |
| `wire_feed.py` | the bank's wire feed (layout unknown; see `docs/14-field-requirements.md`) | TRA-58 | skeleton |
