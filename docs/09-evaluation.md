<!-- Generated from docs/PLAN.md on 2026-11-11. Edit PLAN.md for research changes; edit this file for working detail. -->

## B3. Evaluation protocol
Unit: customer × rule × window. Metrics: precision, recall, lift per rule on SAML-D labels where one exists and on `answer_key.json` for injected cases. Chronological split: warm-up Oct 7–Dec 31 2022; tune Jan–Apr 2023; validate May–Aug 2023. Demo "today" 2023-07-14. Injection is label-blind and disclosed; branch-dependent logic is proven on fixtures only, and the client is told so.

---

## Results (filled by `screener evaluate`, TRA-40)

| Rule | Mode | Alerts/month @100k | Precision | Recall | Lift | Labels used | Window | Command |
|---|---|---|---|---|---|---|---|---|
| R01 | live (CTR list) | ~2 (195 cash-in customer-days natural) | TRA-20 | 100% injected (5/5) | TRA-20 | Synthetic R01 answer key; statutory rule, labels not needed to fire | Natural: 2022-10-07–2023-08-23 | See R01 commands below |
| R02 | | | | | | | | |
| R03 | | | | | | | | |
| R04 | | | | | | | | |
| R05 | | | | | | | | |
| R06 | | | | | | | | |
| R07 | | | | | | | | |
| R08 | | | | | | | | |
| R09 | | | | | | | | |
| R10 | live | 0 natural | N/A (no natural hits) | 100% injected (10/10) | N/A | Synthetic R10 answer key; native labels reported separately | Natural: 2022-10-07–2023-08-23 | See R10 commands below |
| R11 | | | | | | | | |
| R12 | | | | | | | | |

### R01 measured baseline (TRA-15, 2026-11-11)

Commands: `uv run pytest rules/r01_ctr tests/test_contracts.py -q` and
`uv run python scripts/measure_r01.py data/raw/saml_d/SAML-D.csv`.

- Same full source and SHA-256 as R10 below; 525,683 cash rows (Cash Deposit and Cash Withdrawal).
- The actual rule SQL, run for every business day in the range: **195 cash-in customer-days** (195
  customers), which reproduces the profiling figure in docs/03. **0 cash-out customer-days**:
  SAML-D's largest single cash withdrawal is $350 and no account withdraws more than about $1,045 in a day,
  so the cash-out side is proven on fixtures only.
- Five injected CTR days (one teller deposit, two accounts, two branches, teller plus ATM cash out,
  night drop the evening before): all five caught, 100% recall.
- One account = one customer (depositor = sender, withdrawer = receiver), amounts read 1:1 as USD,
  weekend and `holidays_us.csv` roll-forward. Precision and lift against labels are TRA-20.

### R10 measured baseline (TRA-36, 2026-11-11)

Commands: `uv run pytest rules/r10_round_dollar tests/test_contracts.py -q` and
`uv run python scripts/measure_r10.py data/raw/saml_d/SAML-D.csv`.

- Full source: 9,504,852 rows; SHA-256
  `5b71ce2ea7b47fe6f19da1aa151776b04ec74560a852c2c077df91d20b8b4ef9`.
- 79 non-cash entries meet the amount condition; zero carry `Is_laundering = 1`.
  Running the actual rule SQL for every date in the source range yields zero customer-day hits:
  no account, as sender or receiver, has five qualifying entries in a 30-calendar-day window. Scaled natural volume
  remains zero against the budget of 10/month per 100k accounts.
- Ten injected positive customer cases, five entries each: all ten detected, 100% recall.
  Natural precision and lift are undefined with no alerts; injected recall is not native-label
  recall and does not measure performance on real bank data.
- Measurement reads the original CSV directly, uses one account as one customer, and counts both
  the sender-debit and receiver-credit legs, with USD interpreted 1:1. Exact source decimals are filtered before conversion to cents;
  no extra round-dollar rows are created by rounding. This baseline does not use TRA-24,
  synthetic US grouping, the pending engine, or the TRA-40 evaluation harness.
- Retain live mode for this implementation under the recorded budget. Re-measure after customer
  grouping or input-normalization changes; a real bank's exact-thousand frequency may differ.
