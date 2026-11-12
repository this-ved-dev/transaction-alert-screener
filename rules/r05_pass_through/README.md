# r05_pass_through

**Owner:** Abdul · **Ticket:** TRA-33 · **Process:** Funds movement

Rapid pass-through with baseline condition. Prior as-written research estimated 9,600/month;
the current implementation's native tuning is pending. Stays shadow until measured under
50/month and the client has reviewed the tuning table. Debasish's first pain point.

Version 1 is implemented against the six-column TRA-6 contract, with one hit per account and
run day (`group_key=account_id`). Params: `min_inbound=5000`, `outflow_ratio=0.8`,
`outflow_window_hours=72`, `baseline_days=90`, `quiet_ratio=0.2`; weight 4, budget 50/month
per 100k accounts, mode **shadow**, flat tier multipliers. RF-006 is the red-flag citation.

- An anchor is a booked, unreversed USD payment credit of at least $5,000. Debit outflows must
  be strictly after it, no later than 72 elapsed hours, and paid to a different counterparty.
  A cash deposit may lack an originator account; other credits must identify that account.
  Outflows need a destination account. Own-account transfers, fees, interest, pending items,
  reversals, non-USD entries and future data do not count.
- The baseline is median daily incoming plus outgoing eligible payment volume over the 90
  calendar dates before the anchor date, including zero-volume dates. Quiet means strictly
  less than 20% of the anchor amount. No prior-90-day observation horizon means unknown
  baseline/newness, not assumed quietness. The observation horizon is the available ledger's
  earliest timestamp; per-account onboarding/coverage metadata remain a later integration.
- Quiet accounts count all otherwise eligible outflows. Busy accounts count only cross-border
  outflows (`XBCT`) or outflows to beneficiaries absent from the prior 90 elapsed days before
  the anchor. The boundary at exactly 90 days counts as prior history. The qualifying amounts
  themselves must sum to at least 80%: a tiny new-beneficiary transfer does not unlock a large
  established domestic outflow. This is the conservative interpretation of the OR condition;
  it must be included in the client's walkthrough before any live use.
- A hit requires a contributing anchor or outflow posted on the run date; quiet days do not
  repeat unchanged windows. All qualifying anchors retain their own amounts, baseline and
  outbound IDs. Shared outflows are deduplicated in `matched_txn_ids`; do not add the per-anchor
  outflow totals together as unique funds. This is a timing heuristic, not attribution of funds.

The seeded injector creates ten positive cases, each with $5,000 in and $4,000 out one hour
later, plus an isolated synthetic history marker. Original rows and schema are preserved;
labels are never read. Tests execute the real SQL without the pending engine:

```bash
uv run pytest rules/r05_pass_through tests/test_contracts.py -q
uv run pytest rules/r05_pass_through -k fixture_operating_points -s -q
```

The three-point comparison uses four constructed cases only: quiet/known-beneficiary,
busy/known-beneficiary, busy/cross-border, and busy/new-beneficiary. It is not SAML-D precision
or evidence of being under the natural volume budget. Native tuning against Deposit-Send,
Layered_Fan_Out and Gather-Scatter remains pending TRA-24/TRA-30 data with both booked legs,
customer mapping and timestamp assumptions resolved. The unified evaluation command belongs to
TRA-40. Keep shadow until native volume is under budget **and** the client has seen the table.
The full evidence timeline and explanation tool remain in TRA-38; this folder contains the
required basic summary and explanation placeholder.
