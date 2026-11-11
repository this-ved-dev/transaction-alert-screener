<!-- Generated from docs/PLAN.md on 2026-11-11 (client reply applied). Edit PLAN.md for research changes; edit this file for working detail. -->

# PART B — THE 12 MVP RULES, MAPPED TO DATA AND OWNERS

## B1. Capacity budget
Client reply 2026-11-11: rule priority is wires and cash first (R01, R02, R03, R04, R06 outbound, R09), ACH next (R05, R07, R08, R10, R12), P2P last and possibly absent (R11 in shadow). Version 1 of every rule is the client's own definition where he gave one; our variants are version 2, switched on only after a backtest delta and, for time-based windows, a client walkthrough. Tier multipliers default to 1.0 because his thresholds are flat.

Scale to a bank with **100,000 accounts** (SAML-D: 855,460 accounts over 10.5 months, so divide its counts by 8.55 and by 10.5 for per-month). Capacity ~250 alerts/month for two analysts; every rule has a budget; a rule over budget ships in **shadow mode** until tuned under budget.

## B2. The rules, grouped into four processes

Defaults are industry convention. Tier multipliers default 1.0 (configurable in the admin console). Every hit stores rule version, parameters, matched transaction IDs and tier at fire time.

| Process (owner) | # | Rule | Definition (defaults) | Key / window | Drives volume on | Graded against | Measured / expected | Status |
|---|---|---|---|---|---|---|---|---|
| **Cash & CTR** (Vedant) | R1 | CTR candidate | Cash-in > $10,000 or cash-out > $10,000 per business day, totalled separately; weekend/holiday roll-forward | customer / 1 day | SAML-D Cash Deposit 225,206 and Cash Withdrawal 300,477 rows | Fixtures: $10,000.00 vs .01, two accounts one customer, two branches, Friday→Monday, holiday | 195 customer-days [measured] → ~2/month | Live, separate list |
| | R2 | Near-limit deposits (client) / multi-day structuring (ours) | **v1 (client):** any single cash deposit in [$9,000, $10,000]. **v2 (ours, after backtest and walkthrough):** (a) ≥3 cash deposits $2,000–$9,999 in 5 business days totalling ≥$15,000; (b) 30-day cash-in ≥$25,000, none > $9,999 | customer / 5 and 30 days | SAML-D cash deposits | **Smurfing** label: 932 deposits, 63 accounts [measured] | (a) 40 accounts, 90% precision, 57% recall; (b) 15, 100% / 24% [measured] → ~1.5/month | Live |
| | R3 | Same-day splitting (client) / cross-branch (ours) | **v1 (client):** one customer, ≥2 cash deposits each ≤ $10,000 across all accounts, day total > $10,000; one hit per customer per business day. **v2:** ≥2 branches/channels with day total $8,000–$10,000 | customer / 1 day | 0 natural days in SAML-D [measured]; branch is synthetic | ~10 injected cases + fixtures | ~0 natural | Live |
| **Account behaviour** (Vedanshu) | R4 | Dormant reactivation | **v1 (client):** no customer-initiated entry for ≥180 days (interest and fees do not reset; any deposit does), then **outbound ≥ $2,000** within 7 days. **v2:** ≥$5,000 in or out, or ≥10× prior 12-month average | account / 180 + 7 days | 10,420 accounts reactivate after 180+ days; 3,730 with ≥$5k in 7 days [measured]; fires from Apr 2023 | No native label; ~15 injected cases + 179-vs-180 fixture | ~42/month [measured, scaled]; the backtest demo | Live |
| | R7 | New-account burst (mule) | Account age < 90 days; ≥5 distinct inbound senders in 7 days; ≥80% out within 48h | account / 7 days + 48h | "Open date" = first-seen after 90-day warm-up; ~45k new accounts/month [measured] | Fan_In 364, Layered_Fan_In 656, Deposit-Send on new accounts; ~10 injected | Measure in C1; budget ≤30/month | Live if under budget and after a client walkthrough of the 48h window (P2) |
| | R8 | ATM anomaly | ≥5 ATM withdrawals in 24h; or daily ATM ≥$2,000 and ≥3× 90-day average; or ≥2 states in 24h | account / 24h + 90 days | Cash Withdrawal ≤$1,000 → ATM p=0.7, label-blind, seeded | Cash_Withdrawal typology 1,334 partially; ~8 injected multi-state | Measure in C1; budget ≤30/month | Live if under budget |
| **Funds movement** (Abdul) | R5 | Rapid pass-through | Inbound ≥$5,000 from A; ≥80% leaves within 72h to ≠A; and trailing-90-day median daily volume < 20% of inbound, or outbound is cross-border or to a first-time beneficiary | account / 72h + 90 days | SAML-D all rails | Deposit-Send 945, Layered_Fan_Out 529, Gather-Scatter 354; Tide benchmark 22.5% precision, 66% recall [measured] | As written floods: 861k hits, 0.4% precision, ~9,600/month [measured]; budget ≤50 | Shadow until under budget **and** the client has walked through the 72h window. Kickoff pain point #1; priority P2 per the Nov 11 reply |
| | R10 | Round-dollar pattern | ≥5 non-cash transactions in 30 days, exact multiples of $1,000, each ≥$2,000 | customer / 30 days | 79 natural rows, 0 laundering [measured] | ~10 injected | ~0 natural | Live |
| | R12 | Transfer splitting | (a) ≥3 transfers originator→same beneficiary, each < $10,000, total > $10,000 in 7 days; (b) funnel: ≥5 distinct senders → one receiver in 7 days, each < $10,000, total > $10,000, ≥3 senders new to the receiver | pair / receiver / 7 days | SAML-D non-cash rails | "Structuring" label = variant (b): 1,870 rows onto 75 receivers [measured]; receiver-only query fired on 161,853, so the new-sender condition is mandatory | Measure in C1; budget ≤40 | (a) live; (b) live if under budget |
| **Counterparty & rails** (Natalie) | R6 | High-risk jurisdiction transfer | **Outbound wires abroad first** (`PMNT/ICDT/XBCT`; inbound at lower weight). Any cross-border ≥$3,000 with a black-list country; cumulative ≥$10,000 in 30 days with grey-list or internal high-risk; **point-in-time lists** | customer × country / 1 and 30 days | SAML-D Cross-border 933,931 rows, 18 locations incl. Turkey, UAE, Nigeria, Albania, Morocco, Pakistan [measured] | Behavioural_Change_2 345, Structuring cross-border 723, Single_large cross-border | Measure in C1; budget ≤40 | Live if under budget |
| | R9 | Wire to new beneficiary | First outbound wire ≥$10,000 (≥$3,000 High) to a beneficiary unseen in 90 days; weight up if ≥3 new beneficiaries in 7 days | customer × beneficiary / 90 days | Cross-border = international wire; domestic wires from fixtures | Behavioural_Change_1 394, Fan_Out and Single_large cross-border | Measure in C1; budget ≤40 | Live if under budget. Debasish's #2 pain point |
| | R11 | P2P anomaly | P2P ≥$2,500/day; or ≥10 distinct P2P counterparties in 7 days; or ≥5× 90-day baseline; tighter on small accounts | customer / 1, 7, 90 days | Debit-card rows < $1,000 between personal accounts → P2P p=0.3, label-blind, seeded | Fan_Out / Scatter-Gather debit (weak); ~10 injected | Measure in C1; budget ≤30 | **Shadow (P3)**: client says P2P is last and may be absent from the export; demo rail is synthetic |

Why this grouping: each process shares a data shape (cash rows; per-account history; inbound-outbound flows; counterparty attributes), so each owner writes one set of helper views and one evidence panel style. Debasish's three pain points land one each on Abdul (R5), Natalie (R9, R11), which spreads the demo weight.

### R10 implementation and evidence (TRA-36)

Version 1: `min_count=5`, `window_days=30`, `multiple_of=1000`, `min_amount=2000`;
weight 1, live mode, budget 10/month per 100k accounts, flat tier multipliers. These are pattern
thresholds from the project definition, not a statutory round-dollar threshold. RF-010 links
to the FFIEC red-flag source in `rules/red_flags.yaml`.

Count booked, unreversed USD non-cash payment (`PMNT`) entries in either direction across a
customer's accounts over the run date and prior 29 calendar dates. Exclude `CNTR` and
`CCRD/CWDL` cash while allowing non-cash card entries; exclude fees and interest (`ACMT`) and
both legs of transfers between the customer's own accounts. Each amount must be at least $2,000
and have zero decimal remainder modulo $1,000. Fire only on a run date that adds a qualifying
entry, so one pattern raises one alert, not one per day it stays in the window.
Return one customer hit (`group_key=cif_id`) with sorted entry IDs, count, total and thresholds.
The analyst must still establish the commercial context; the rule does not infer intent.

Measurement: 79 qualifying natural SAML-D entries and zero natural customer-day hits; injected
recall 10/10. Commands, assumptions, source hash and caveats are in `docs/09-evaluation.md`.
This measurement uses one account per customer, both transfer legs, and original source amounts. Re-measure
after US-layer grouping or amount normalization changes. No third-party rows are committed.

## G1. Facts from the reply (verbatim meaning, our tag)
1. **Priority:** wires and cash deposits first ("those two feed our three core rules"), ACH next, P2P last and possibly absent from the export. [client]
2. **Geography:** US regional bank, domestic customers, no foreign branches; some outbound wires go abroad. The 60-minute threshold did not come from him; any time-based rule must be walked through with him before it goes live. [client]
3. **Thresholds today:** near-limit deposits $9,000–$10,000; same-day splitting = one customer, two or more deposits each at or under $10,000, adding past $10,000 across all their accounts, one flag per customer per day; dormancy = 180+ days idle, then $2,000+ going out; interest and fees do not reset the clock, a deposit does. Research = filter yesterday's export in Excel, then core-banking screens for history and ID; nothing recorded. [client]
4. **Formats:** core export and wire feed are two different layouts; probably not ISO 20022; plan a mapping step and tell them which fields we need. [client]
5. **Auditor:** for any **account**, every flag it ever had (date, rule, amount, decision), exportable as CSV or Excel, plus a printable one-page summary per account. [client]
6. **Operations:** manual review every morning, about 90 minutes a day, three patterns; tool flags only; bad rows are set aside with a reason, never dropped; limits changeable without a programmer. [client]
7. **Crypto:** none; do not build crypto handling. [client]
8. **KYC:** done at onboarding in the core under CIP; manual basic risk rating; do not re-verify; worst case show the rating next to a flag. [client]
9. **Throughput:** no number; "tens of thousands of rows a day, tops"; one batch run every hour on incrementals, not real time. [client]

Assumptions we must document because he could not answer: P2P exists in the export (we keep R11 in shadow and disclose that the rail is synthetic until a sample proves otherwise); daily volume 10k–50k rows (we size the demo subsample to 100k accounts, which produces that order of magnitude); the two feeds carry an account number and a cash indicator (if the cash indicator is missing, the tran-code map derives it).

## G3. Changes to make

| # | Change | Where | Ticket |
|---|---|---|---|
| C1 | **R02 version-1 default = the client's rule:** variant (c) any single cash deposit in [$9,000, $10,000]. Our multi-day variants (a), (b) become version 2, enabled only after a backtest shows the alert-count delta to the client. | `rules/r02_structuring_multi_day/README.md`, docs/03 | TRA-16 description and AC |
| C2 | **R03 version-1 default = the client's same-day splitting:** one customer, ≥2 cash deposits each ≤$10,000 (across all accounts), day total > $10,000; one hit per customer per business day. Our branch/channel condition becomes version 2. R01 (CTR candidate, > $10,000 total regardless of count) stays a separate list; a split day is both a CTR candidate and an R03 hit by design. | `rules/r03_structuring_same_day/README.md`, docs/03 | TRA-17 |
| C3 | **R04 version-1 default = the client's dormancy:** idle ≥180 days counting customer-initiated entries only (interest and fees excluded, any deposit resets), then **outbound ≥ $2,000** within 7 days. Our $5,000 in-or-out and 10× rules become version 2. | `rules/r04_dormant_reactivation/README.md`, docs/03 | TRA-25 |
| C4 | **Rule priority and modes:** P1 live-candidates R01, R02, R03, R04, R09, R06 (R06 scoped to outbound wires abroad; inbound cross-border weight lowered); P2 R05, R12, R07, R08; P3 R11 stays **shadow** with the note "rail may be absent from the export". Linear priorities set accordingly. Note the conflict with the kickoff pain points (pass-through, new beneficiary, P2P) and ask Debasish to confirm the order in the next written exchange. | docs/03 B2 table, docs/08 | TRA-15/16/17/25/42/41 → Urgent; TRA-33/37/26/27 → High; TRA-43 → Medium, mode shadow |
| C5 | **Time-based rules need a client walkthrough before live:** R05 (72h) and R07 (48h) and any version-2 window change. Add a gate to the acceptance criteria. | docs/03, docs/08 | TRA-33, TRA-26 |
| C6 | **Hourly incremental batch:** `screener run --since <last_run>` processes new entries, re-evaluates affected customer-days, and upserts hits by (rule_version, customer, business_day, group_key) and alerts by (customer, business_day) so reruns are idempotent; scheduler cron becomes hourly; nightly remains a full reconciliation run. | `docker/crontab`, docs/05, E3 data flow | TRA-21 (engine), TRA-8 (compose) |
| C7 | **Quarantine, never drop:** `rejected_entry` table (load_batch_id, raw row, reason, source) written by every adapter; count shown on the load report; a Quarantine page lists rows with reasons. | docs/05 data model, docs/04 | TRA-6 (schema), TRA-24 (adapter), TRA-34 (page) |
| C8 | **Per-account audit view:** account-level filter on the export; printable one-page account summary (every flag: date, rule, version, amount, decision, actor); CSV opens in Excel, so CSV plus the printable page satisfies "CSV or Excel". | docs/11 demo step 9 | TRA-12, TRA-28 (customer page gets an account history tab) |
| C9 | **Risk tier:** multipliers default to 1.0 (client thresholds are flat); multipliers stay configurable in the admin console; drop sanctions/PEP-based tiering from the US layer (KYC is the core's job). Rating shown on every alert. | docs/03, docs/04 D3 | TRA-30 (remove PEP tiering), TRA-34 (show rating) |
| C10 | **Field-requirements sheet for the vendors:** the minimum fields we need from the core export and from the wire feed, mapped to the canonical schema (account id, customer id if any, posting and effective dates, amount, debit/credit, transaction code and description, cash indicator or derivable code, branch or teller id, channel, counterparty name, account, bank and country for wires, memo). Plus a `wire_feed` adapter skeleton beside `core_csv`. | new `docs/14-field-requirements.md`, `screener/adapters/` | **New ticket** (P0, Vedant, 2 pts) |
| C11 | **ROI anchor:** lead the leadership outline with "90 analyst-minutes a day and an audit trail", keep the fraud-loss framing as context, drop the streaming lane and digital-assets items from the roadmap (aspirational only). | docs/06, docs/13 outline | TRA-51 |
| C12 | **Record the answers:** docs/08 marks Q1 (60 minutes), Q7 (source systems), Q10 (crypto) answered with the text above; README meeting notes gain a "2026-11-11 written reply" entry; open follow-ups: confirm rule priority vs kickoff pain points; whether P2P appears in the export; which screening vendor and KYC refresh cycle (for the deck, not the build); sample layouts of the two feeds. | `docs/08-client-questions.md`, `README.md` | TRA-52 |
