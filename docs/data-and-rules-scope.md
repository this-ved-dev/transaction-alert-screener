# Data sources and rule scope (decision, 2026-11-04)

Client: a regional bank with a small BSA compliance team. Every rule that goes live in the MVP must produce a queue that one or two analysts can work. A typical analyst clears 100–150 alerts a month. Evidence for every number below is in `reports/AML transaction dataset selection.md` and `research_notes/AML transaction dataset selection/`.

## Data sources

| Role | Source | Why | Licence and repo rule |
|---|---|---|---|
| **Primary transactions** | **SAML-D** (Kaggle, 9.5M rows, Oct 2022 – Aug 2023) | Real Cash Deposit/Withdrawal rows. Labelled cash structuring ("Smurfing", 63 accounts). Natural dormancy (10,420 accounts restart after 180+ days idle). Typology label on every row | CC BY-NC-SA 4.0. Fine for coursework. **No rows in the repo**: commit only fetch steps and metrics |
| **Hand-built test cases** | About 100 rows we write (Faker for names) | What no dataset has: $10,000.00 vs $10,000.01, cross-account and cross-branch CTR totals, 179 vs 180 idle days, weekend and holiday roll-forward, planted dormant reactivations, hostile memo text | Ours (MIT) |
| **Branches** | FDIC Summary of Deposits (one $1–5B bank's branch list, renamed to our fictional bank) | Real branch geography. Assigned to transactions without looking at labels | US government public data |
| **Calendar** | US federal holidays | Business-day rule for CTR aggregation | — |

US layer on SAML-D:
- Amounts read 1:1 as USD.
- One account = one customer by default. Optionally, a disclosed, label-blind sample is grouped into multi-account customers.
- A synthetic KYC tier.

**Not used:**
- **Tide:** its "cash" rows are transfers between different people and no account is ever idle. Keep it only as an optional pass-through benchmark.
- **AMLworld:** only 10 days, and its "cash" is a transfer.
- **SynthAML, AMLNet, SA-SAML-D, J.P. Morgan, Berka, PaySim/TabFormer/Sparkov:** they fail on cash, history, licence or access.
- **Tazama:** no data. It is a design reference only.

## MVP rules (live in the analyst queue)

Measured on SAML-D. Alerts per month are scaled to a bank with 100k accounts (SAML-D has 855,460 accounts over 10.5 months); these are estimates.

| Rule | Client need | Evidence | Est. alerts/month per 100k accounts |
|---|---|---|---|
| **CTR candidate list.** Cash-in or cash-out above $10,000 per customer per business day, across accounts and branches. A separate list, not the suspicious-activity queue | Statutory (31 CFR 1010.311/313) | 195 customer-days. Cross-account and branch logic proven on hand-built cases | ~2 |
| **R2 Structuring, multi-day.** (a) 3+ cash deposits of $2,000–$9,999 within 5 business days totalling $15k or more; (b) a 30-day cash total of $25k or more with no single deposit above $9,999 | Pain point 1 | (a) 40 accounts flagged, 90% precision, 57% recall on labelled smurfing. (b) 15 accounts flagged, 100% precision, 24% recall. 138 alert customer-days across both | ~1.5 |
| **R4 Dormant reactivation.** No activity for 180+ days, then $5k or more within 7 days | Pain point 2 | 3,730 events on native data. No dormancy label, so recall is proven on planted cases. **Tuning this threshold is the backtest demo** | ~42 |

Total: about 45 alerts a month per 100k accounts, within one analyst's capacity.

## Stretch goals, in order

| # | Rule | Why it is not in the MVP | Data |
|---|---|---|---|
| 1 | **R5 Rapid pass-through** (80%+ of inbound $5k+ out within 72h) | As written it flags 28,396 SAML-D accounts at 0.4% precision, about 9,600 alerts a month per 100k accounts. It needs a baseline or known-pattern exclusion first. Show it in **shadow mode** (backtest counts only), which is the alert-flood lesson from the USAA and Block cases | SAML-D; Tide as a cross-check (22.5% precision there) |
| 2 | **R3 Same-day / cross-branch structuring** | SAML-D has 0 qualifying customer-days, and no dataset has branches | Hand-built cases only |
| 3 | **High-risk jurisdiction wires** | Cheap; needs only the list data | SAML-D receiver locations; FATF lists (hand-coded JSON); FinCEN 311 list (OpenSanctions `us_fincen_special_measures`) |
| 4 | **R6 Velocity spike** vs the 90-day baseline | Not yet measured; anomaly rules tend to flood | SAML-D Behavioural_Change labels |
| 5 | **Sanctions name screening** | Needs customer names and a fuzzy matcher | OFAC SDN (public domain) or OpenSanctions `us_sanctions`; OpenSanctions match/no-match pairs to grade the matcher |
| 6 | **Funnel / transfer splitting** | As written it flags 161,853 receivers. It needs a distinct-new-senders condition | SAML-D's "Structuring" label, which is actually non-cash fan-in |

**Roadmap only** (no supporting data in our sources): round-dollar, new beneficiary, mule burst, shared identifiers, ATM/P2P anomalies, cash-business deviation, and LLM-drafted alert narratives.

## What we tell the client

- Every live rule has a measured alert volume, a documented threshold and a versioned change history.
- Rules that would flood a small team run in shadow mode until they are tuned.
- Branch-dependent logic is proven on hand-built cases, because no available dataset records branches.
- Data is synthetic and licensed for non-commercial use. In a real deployment, the bank's own export replaces it.
