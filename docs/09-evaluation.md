<!-- Generated from docs/PLAN.md on 2026-11-11. Edit PLAN.md for research changes; edit this file for working detail. -->

## B3. Evaluation protocol
Unit: customer × rule × window. Metrics: precision, recall, lift per rule on SAML-D labels where one exists and on `answer_key.json` for injected cases. Chronological split: warm-up Oct 7–Dec 31 2022; tune Jan–Apr 2023; validate May–Aug 2023. Demo "today" 2023-07-14. Injection is label-blind and disclosed; branch-dependent logic is proven on fixtures only, and the client is told so.

---

## Results (filled by `screener evaluate`, TRA-40)

| Rule | Mode | Alerts/month @100k | Precision | Recall | Lift | Labels used | Window | Command |
|---|---|---|---|---|---|---|---|---|
| R01 | | | | | | | | |
| R02 | | | | | | | | |
| R03 | | | | | | | | |
| R04 | | | | | | | | |
| R05 | shadow | Pending native tuning | Not computed on native data | 100% injected (10/10) | Not computed | Synthetic answer key; native label evaluation pending | Fixtures only | See R05 commands below |
| R06 | | | | | | | | |
| R07 | | | | | | | | |
| R08 | | | | | | | | |
| R09 | | | | | | | | |
| R10 | live | 0 natural | N/A (no natural hits) | 100% injected (10/10) | N/A | Synthetic R10 answer key; native labels reported separately | Natural: 2022-10-07–2023-08-23 | See R10 commands below |
| R11 | | | | | | | | |
| R12 | shadow | 2,454.82 potential customer-day alerts | Not computed | 100% injected pair cases (10/10) | Not computed | Pair answer key; native Structuring receiver coverage below | 2023-01-11–2023-08-23 | See R12 commands below |

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

### R12 measured baseline and shadow decision (TRA-37, 2026-11-11)

Commands: `uv run pytest rules/r12_transfer_splitting tests/test_contracts.py -q` and
`uv run python scripts/measure_r12.py data/raw/saml_d/SAML-D.csv`.
The script runs the actual rule SQL for every day from 2023-01-11 through 2023-08-23 (225 days),
allowing 96 prior dates for the seven-date window and preceding 90-date relationship history.
It completed in 88.391 seconds on this laptop. Input: 9,504,852 rows, 855,460 accounts;
SHA-256 `5b71ce2ea7b47fe6f19da1aa151776b04ec74560a852c2c077df91d20b8b4ef9`.

| Measure | Result |
|---|---|
| Pair variant a | 216,977 hits; 90,945 customers |
| Funnel variant b | 9,531 hits; 8,221 receivers |
| Combined distinct customer-day groups | 155,236 |
| Potential alerts/month scaled to 100k accounts | 2,454.82; budget 40 |
| Variant-specific hits/month scaled to 100k | a: 3,431.16; b: 150.72 |
| Native Structuring receivers in full source / measured period | 75 / 74 |
| Receivers caught with labelled Structuring transactions in matched evidence | 73 of the 74 active in period (98.65% receiver coverage) |
| Injected pair cases detected | 10/10 (100% recall) |

**Decision: both variants stay shadow.** The combined potential alert volume is about 61 times
the budget. Variant b also exceeds the budget by itself; it does not catch every native receiver.
No operational alerts should be created from these shadow hits. Subsequent tuning should measure
count, amount and relationship-window changes with chronological validation before a mode change;
this ticket preserves the specified defaults and documents the over-budget result.

This is a direct-source baseline with one account per customer, both booked perspectives, and
exact original amounts interpreted 1:1 as USD. Labels never enter the rule's `entries` view.
Native receiver coverage counts only hits whose matched entries include an actual Structuring
transaction; it is not customer-window precision or recall. The pre-period receiver is not
claimed as detected. Month scaling uses 365.25/12 days and divides by 855,460/100,000 accounts.
Re-measure after US customer grouping and cent normalization. The sender-only TRA-24 prototype
cannot supply the funnel's receiver credit legs without further mapping; this script projects
both directions directly and does not imply that integration is complete. The unified
`screener evaluate` command remains owned by TRA-40.

Tests execute both variants without the engine and cover counts, amount caps and totals, seven-
date endpoints, 90-date history endpoints, old senders with prior large payments, repeated
senders, own-account exclusions, eligibility, both booked legs, variant hit identities, and
seeded label-blind injection. Pytest now uses importlib mode so multiple rule folders can each
contain `test_rule.py` without module-name collisions.

### R05 fixture comparison and native tuning still required (TRA-33)

Run `uv run pytest rules/r05_pass_through tests/test_contracts.py -q` for boundaries and
injection, and `uv run pytest rules/r05_pass_through -k fixture_operating_points -s -q` to
reproduce the comparison below. These are **four constructed synthetic cases**, not a SAML-D
backtest: quiet/established-beneficiary (positive), busy/established-beneficiary (negative),
busy/cross-border (positive), and busy/new-beneficiary (positive). All clear the same inbound,
80% ratio, 72-hour and different-counterparty conditions. Only the baseline gate varies.

| Fixture operating point | Hits | Positive cases detected (of 3) | Negative cases flagged (of 1) | Fixture precision | Fixture recall |
|---|---|---|---|---|---|
| No baseline/risk gate | 4 | 3 | 1 | 75% | 100% |
| Quiet-account gate only | 1 | 1 | 0 | 100% | 33.33% |
| Quiet OR XBCT OR new beneficiary (implemented) | 3 | 3 | 0 | 100% | 100% |

Separately, the seeded injector's ten positive quiet-account cases are all detected (10/10).
This proves fixture behavior and injected recall only. It does not replace the ticket's
required native three-operating-point tuning table or establish a production precision rate.

**Remaining gates:** TRA-24 and TRA-30 must supply canonical data with both booked legs,
customer mapping, consistent bank-local timestamps and disclosed observation coverage. Then
measure at least three native operating points against Deposit-Send, Layered_Fan_Out and
Gather-Scatter using chronological tuning/validation. Record account-day volume scaled to
100k accounts, precision/recall/lift under the agreed evaluation unit, the client walkthrough
of the 72-hour interpretation, and a live/shadow decision. The unified `screener evaluate`
command belongs to TRA-40. **R05 remains shadow**: no current native budget claim is made.

Implementation semantics: zero-filled median daily eligible payment volume over the 90 dates
before the inbound; quiet means strictly below 20% of its amount. Busy accounts count only
the XBCT/new-beneficiary outflow amounts toward the 80% threshold. Prior history includes
the exact 90-day timestamp boundary. Unknown observation history does not imply quietness or
beneficiary newness. Per-account-day evidence retains each qualifying inbound separately and
deduplicates matched IDs; overlapping anchor windows are not unique fund tracing. This
conservative interpretation and the baseline's ledger-wide observation proxy require the
client walkthrough and later coverage metadata before live use.
