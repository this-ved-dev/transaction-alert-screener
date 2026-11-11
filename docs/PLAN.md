# Transaction Alert Screener — Research, Rules, Data, Architecture, Ownership, Linear and CI Plan

Team: Vedant (lead), Abdul, Vedanshu, Natalie. Client side (from the Nov 5 kickoff): **Debasish Chanda** plays bank leadership, **Anurag Gupta** is the Coforge partner, **Stacy** is a banking SME on request; calls need 48 hours' notice; a Coforge BFSI leadership presentation is due around early January 2027. Revised 2026-11-11.

What changed in this revision: (1) the kickoff facts replace the "compliance manager" persona and the "sell process, not AI" framing with a **hybrid** (deterministic rules + an in-bank AI investigator agent + a human deciding every case); (2) ownership is now **four end-to-end process slices**, three rules each, every owner building business logic, tests, evaluation and UI; (3) a complete **Linear workspace** design with every ticket written out; (4) a **per-rule folder** scaffold that lets four people work without merge conflicts; (5) **git/CI hygiene** with GitHub Actions that lint, test, build the Docker image and smoke-test the containers on every pull request.

Tags: [verified] primary source · [measured] we ran it on the file · [estimated] derived · [anecdotal] vendor or forum. Sources are numbered [S#] and listed at the end.

**Scope of this document and of the session that produced it.** This is the team's reference document and is committed to the repository as `docs/PLAN.md`. The session that wrote it does three things and then stops: (1) commits this document, (2) creates the Linear workspace structure and every ticket in F3, (3) creates the repository scaffold in F4 with configuration, CI, Docker, contract documents and folder templates but **no application or rule code**. All build work, starting with TRA-2, is done by the ticket owners in their own sessions.

---

## 0. Glossary

| Term | Plain meaning |
|---|---|
| **BSA / AML / CFT** | Bank Secrecy Act (1970) and the anti-money-laundering and counter-terrorist-financing program every US bank must run under it. |
| **FinCEN** | Treasury bureau that writes the BSA rules and receives CTRs and SARs. |
| **OCC / Fed / FDIC** | The federal bank examiners. They publish consent orders when a bank's program fails. |
| **FFIEC manual** | The exam manual. Appendix F is its red-flag list. |
| **CTR** | Currency Transaction Report: mandatory when one person moves more than $10,000 of physical cash in one business day. Mechanical. |
| **SAR** | Suspicious Activity Report: confidential report to FinCEN when the bank suspects something. A judgment call by the BSA officer. Nobody outside need-to-know may learn one exists. |
| **Structuring / smurfing** | Splitting cash into pieces under $10,000 to dodge a CTR. A federal crime. |
| **Dormant reactivation** | An account idle for months suddenly moves money. |
| **Pass-through** | Money comes in and leaves almost immediately. A layering sign. Debasish's first named pain point. |
| **Mule** | An account, often a duped person's, that receives and forwards illicit funds. |
| **Funnel account** | Many people pay into one account; it is then emptied. |
| **Typology / red flag / rule** | A named laundering pattern / a regulator-listed indicator / our parameterised test for it. |
| **Hit / alert / case** | One rule firing once on one customer / what the analyst sees, one per customer per day with all hits attached / an escalated alert. |
| **Disposition** | The decision on an alert plus its reason. |
| **Four-eyes** | A second person must approve every SAR recommendation. |
| **Audit trail** | Immutable who/what/when/why. |
| **CIF** | Customer Information File: the customer-level ID. One customer, many accounts. |
| **KYC / CDD / risk tier** | Know Your Customer. Low/Medium/High at onboarding; High gets tighter thresholds. |
| **Core** | The bank's ledger system (Fiserv, Jack Henry, FIS). We read its nightly export. |
| **Tran code** | The core's transaction type code. Mapping these to cash/wire/ACH/ATM is the dirtiest part of any monitoring project. |
| **Business day** | Posting day. Saturday cash counts on Monday. **Night drop**: after-hours deposit box, posts next business day. |
| **ACH / wire / P2P** | Electronic rails: slow batch, same-day and expensive, and Zelle-style person-to-person. |
| **OFAC / SDN** | Treasury sanctions office and its Specially Designated Nationals list. Free CSV. |
| **FATF black / grey list** | Countries with weak AML controls, updated three times a year. |
| **314(a) / 314(b)** | FinCEN's secret name-search list (not public) and bank-to-bank information sharing. |
| **False positive / lift** | An alert that is nothing (90–95% of rule alerts by common claim) / precision divided by the base rate, the honest metric at 0.1% base rates. |
| **ATL/BTL / shadow mode / backtest** | Sampling above and below a threshold / running a rule over past data without producing live alerts. |
| **MRM** | Model risk management. SR 11-7 was replaced by SR 26-2 in April 2026; SR 26-2 excludes generative and agentic AI from its scope. |
| **Consent order / NPRM / GLBA / SOC 2** | Public enforcement action / proposed regulation / customer-data protection law / the security audit report vendors give banks. |
| **Investigator agent** | An LLM-driven assistant that gathers evidence for an alert and drafts a recommendation and narrative. In this design it never decides and never closes. |
| **SAML-D / Tide** | The two synthetic datasets on disk (D1). |
| **DuckDB / Parquet** | In-process analytical SQL engine / columnar file format. Our rules compute layer. |
| **ISO 20022** | The international XML/JSON standard for financial messages. Wires (Fedwire, CHIPS, Swift) and instant rails (FedNow, RTP) use it on the wire; ACH, cards, cheques, Zelle and teller cash do not. |
| **camt.054 / entry** | The ISO 20022 "bank-to-customer debit/credit notification". One `Ntry` (entry) per booked debit or credit on an account, whatever rail produced it. The shape of our canonical record. |
| **BankTransactionCode (BkTxCd)** | ISO 20022's open taxonomy of what an entry *is*: Domain / Family / SubFamily, e.g. `PMNT/CNTR/CDPT` = cash deposit at the counter. About 1,500 permitted triplets, free to download. Our category column. |
| **Nacha / SEC code** | The US ACH file standard (fixed-width 94-character records) and its Standard Entry Class codes (PPD, CCD, WEB, TEL, IAT). Not ISO. |
| **ISO 8583 / X9.100-187** | The card and ATM message standard / the cheque image-exchange standard. Neither is ISO 20022. |
| **CIF in ISO 20022** | The customer number travels as a party identifier with scheme code `CUST`. Risk tier has no ISO slot and lives in our own party extension. |
| **Cycle / project / milestone** | Linear's sprint / a body of work with an owner / a checkpoint inside a project. |

---

# PART A — DOMAIN RESEARCH

## A1. The problem in domain terms, updated by the kickoff
The brief said analysts filter core CSV exports by eye for two patterns and that nothing records what was flagged, why or when. The kickoff (Nov 5) added: fraud losses are about $30–40M a year, AML is roughly 20% of incidents and 40% of dollar impact; four offshore analysts cover all fraud; detection takes about 24h and resolution about 24h; Nov–Jan is peak season; there is no data warehouse, analysts work in Excel and VB scripts; data is scattered across ACH, wire, P2P/Zelle, cash and ATM; branches span NJ and Manhattan. Debasish's ranked pain points are **rapid pass-through, small transfers to new beneficiaries or jurisdictions, and high-count P2P on small accounts**. He rejected rules-only automation and wants an agentic, policy-driven harness with an admin console to change thresholds and add rules without recoding, running inside the bank on the bank's own LLM credentials. He claimed a "60-minute flag mandate"; research found no such US rule, and the brief asks him for the citation.

The missing audit trail remains the disease. The Blue Ridge Bank consent order (OCC, Jan 2024, ~$3B community bank) cites no written alert-disposition standards, undocumented decisions not to file, insufficient staffing and no board view of backlog [S30] [verified].

## A2. What the law requires

| Topic | Rule | Design consequence |
|---|---|---|
| CTR | Cash **> $10,000** per person per business day across all accounts and branches; cash-in and cash-out totalled separately; file in 15 days; keep 5 yrs (31 CFR 1010.311/.313/.306) [S1–S4] [verified] | Deterministic. Separate "CTR candidates" list. |
| Structuring | Splitting cash into ≤$10k pieces "on one or more days" to evade (31 CFR 1010.100(xx); 31 USC 5324) [S6][S7]. **Oct 9 2025 interagency FAQ:** near-$10k alone is not a SAR trigger; need a pattern [S8] [verified] | Rules surface patterns, not single deposits. |
| SAR | ≥$5k with suspect, ≥$25k regardless; 30 days from "initial detection" (+30 if no suspect, cap 60); retain 5 yrs; strict confidentiality; board notified (31 CFR 1020.320; 12 CFR 21.11) [S11][S12] [verified] | Deadline clock; SAR status gated to BSA role; access logged; nothing hard-deleted. |
| No-SAR decisions | Not legally required to document; "a short, concise statement" suffices; examiners expect it [S8][S30] | Reason code + rationale on every close. |
| Program | Five pillars incl. risk-based ongoing monitoring (31 CFR 1020.210) [S17] | Risk tier feeds thresholds. |
| Model risk | SR 11-7 and the 2021 BSA/AML statement **superseded Apr 17 2026 by SR 26-2 / OCC 2026-13**, which exclude GenAI and agentic AI [S20][S21]; FFIEC asks whether filtering criteria are "independently verified" and periodically reviewed [S18] | Rule inventory, versioned thresholds with approver, backtest evidence, plus a separate control set for the agent. |
| 2026 rulemaking | FinCEN AML/CFT Program **NPRM Apr 10 2026**: "does it work", risk assessment drives rules, technology counts as evidence; final rule expected late 2026/early 2027 [S24][S25]. STREAMLINE Act (CTR→$30k) not advanced [S26] | Thresholds are versioned config. |
| Retention | 5 yrs general; OFAC 10 yrs since Mar 2025 [S27][S28] | Soft-close only. |
| Free text | Project rule + XSS hygiene | Memos stored verbatim, rendered escaped, never parsed, never passed to the agent as instructions. |
| "60-minute mandate" | No US rule found. Nacha 2026 fraud-monitoring rules set no time window; SAR rule says 30 days and "immediately" call law enforcement for urgent cases; EO 14406 (May 2026) sets 60/90/180-*day* agency tasks | Framed as a clarifying question to the client; design supports a sub-hour lane later (streaming), not now. |

## A3. Enforcement that proves the pain (all [verified])
TD Bank ~$3.1B (2024): unmonitored volume, P2P gaps, backlogs, funnel accounts [S31]. Bank of America OCC $750M (Oct 2026): thresholds not appropriate, ~200k case backlog [S32][S33]. AmEx OCC $350M (Oct 2026). **Blue Ridge Bank** (2024) [S30]. Block $40M (2025): alerts 18k→169k after new tooling without staffing [S34]. USAA: new system without a pilot → 90k unreviewed alerts [S35]. Shinhan: migration without a parallel run missed 468 alerts [S36]. U.S. Bank $185M: capped alerts to staffing [S37]. OCC Apr 2026 order: triage system auto-closed most alerts [S38]. Lessons encoded in Parts B and C: shadow mode before go-live, no auto-close by rules or by the agent, documented thresholds, parallel-run export.

## A4. How a compliance team works
Alert → L1 triage → case → BSA officer → SAR decision → filing (outside our tool). 90–95% false positives [anecdotal] [S39][S40]; ~100–150 alerts per analyst per month [anecdotal] [S42]; 20–60 min per alert [S43]; BPI measures 21.4h per SAR vs FinCEN's 1.98h estimate [anecdotal]. FinCEN FY2024: 2.6M SARs from depository institutions [S44] [verified]. Vendor systems consolidate hits per entity [S45–S47]. No alert SLA in law; the SAR clock is the hard deadline.

## A5. Vendors, agents and cost
Verafin (Nasdaq) and Abrigo dominate US banks under $10B; a $1–5B bank likely pays **$75–200k/yr licence + $25–75k implementation** [estimated] [S71–S73]. Prices found elsewhere: Unit21 average $157k (Vendr), Lucinity from $54k, ComplyAdvantage $30k fintech package, Marble SaaS from about €2.5k/month [anecdotal]. **Agentic offerings the client asked us to study:** NICE Actimize X-Sight ActOne InvestigateAI (Apr 2025) builds investigation plans from the bank's own policy documents, the closest match to the "policy harness"; Hawk AML Investigative Agent (Mar 2026) is model-agnostic; Verafin Agentic AI Workforce (650+ institutions, Jun 2026); FIS + Anthropic Financial Crimes Agent (May 2026); FNBO runs Verafin agents on Bedrock with ~50% time saved and analysts keeping the decision [anecdotal]. SR 26-2 excludes GenAI and agentic AI, so the bank needs its own agent control set [verified]. Labor: a 4+1 BSA team ≈ **$506k/yr** loaded [estimated]; US+Canada compliance cost $61B/yr [S79]. Independent validation **$15–40k every 1–2 yrs** [estimated]. In-house infrastructure plus LLM ≈ $40–200k/yr at scale; LLM at ~$0.25 per alert ≈ $15k/yr at 5k alerts/month [estimated]; for the prototype, Sonnet at ~3k in / 500 out tokens per alert is ≈ $11/month at 1,000 alerts [S85].

| | Status quo | Buy | Build the harness in-bank (hybrid) |
|---|---|---|---|
| Year 1, ex-labor | ~$0 + exam exposure | **$115–315k** | **$20–60k + build labor**; $40–200k/yr at production scale |
| Steady state | ~$0 | **$90–240k/yr** | **$10–30k/yr** prototype; vendor bake-off optional |

Vendor-neutral recommendation from the discovery brief: build the data foundation, policy harness and audit layer in-bank because every option needs them; bake off our agent against one or two vendors in a 90-day shadow pilot.

## A6. Friction and our answers

| Friction | Evidence | Answer |
|---|---|---|
| Scattered data, no warehouse, Excel and VB scripts | kickoff | Canonical schema with one adapter per source; hourly incremental batch, no streaming (client: "not real-time") |
| Core data access; tran codes; account-only keys | [S86–S88] | Editable tran-code map; CIF keys; reconciliation report per load |
| Vendor risk (OCC 2023-17; SOC 2) | [S89] | Everything runs inside the bank, including the LLM on the bank's credentials |
| Alert flood; auto-close is a finding | Block, USAA, OCC 2026 | Encode current thresholds as v1; shadow mode; no auto-close by rules or agent |
| Undocumented tuning | FFIEC [S18] | Maker-checker threshold changes in the admin console; backtest attached |
| Switching needs a parallel run | Shinhan | Daily alert export |
| SAR confidentiality | [S12][S15][S16] | Role-gated status; access log |
| Black-box fear; SR 26-2 silent on agents | [S91][S20] | Deterministic rules decide what is flagged; the agent only gathers and drafts, with citations; autonomy grows in graduated steps against measured accuracy |
| Seasonal peak Nov–Jan with contract analysts | kickoff | Seasonal threshold profiles (versioned) and a queue that onboards a contractor in minutes |

## A7. What leadership wants to hear
Debasish asked for the "why" behind every decision and a regulator report on demand, business impact before technology, an ROI he can take to the CFO, and intelligence rather than workflow automation. The pitch is therefore: a defensible record and sub-day triage first; an agent that explains, cites and drafts second; a human deciding always.

---

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

## B3. Evaluation protocol
Unit: customer × rule × window. Metrics: precision, recall, lift per rule on SAML-D labels where one exists and on `answer_key.json` for injected cases. Chronological split: warm-up Oct 7–Dec 31 2022; tune Jan–Apr 2023; validate May–Aug 2023. Demo "today" 2023-07-14. Injection is label-blind and disclosed; branch-dependent logic is proven on fixtures only, and the client is told so.

---

# PART C — BUSINESS LOGIC

1. Store every hit; one alert per (customer, business day); disposition cascades to hits; per-rule statistics on hits.
2. CTR candidates are a separate list with a reconcile status.
3. Status machine `NEW → IN_REVIEW → PENDING_INFO → ESCALATED → CLOSED_NO_ACTION | SAR_RECOMMENDED → SAR_FILED`; reason codes on close (expected activity, documented business purpose, duplicate, false positive, other with text); `SAR_FILED` set only by BSA officer with the external filing ID; the tool never files, blocks, freezes or contacts.
4. Roles: Analyst, BSA Officer, Auditor (read-only, every view logged). Nobody else has access.
5. Four-eyes: `ESCALATED → SAR_RECOMMENDED` requires a BSA officer who is not the escalating analyst.
6. Thresholds: versioned rows edited in the **admin console** with maker-checker (an analyst or officer proposes with a reason; a different officer approves); applies to future runs; each hit stores its rule-version ID; `backtest` reports alert counts per rule per version. Rule modes: `live`, `shadow`, `off`. **Seasonal profiles**: a named parameter set with a date range (Nov–Jan) that overrides defaults, versioned the same way.
7. Suppression: one rule, one customer, ≤90 days, with reason; logged; no other auto-close.
8. Priority score = Σ rule weights (each rule once per alert, however many hits it has) × tier factor + 2 × prior alerts in 12 months; sorted by score then age; age badge at 20 days; SAR clock after escalation.
9. Audit log: append-only; actor, role, timestamp, entity, action, before/after JSON, reason; hash-chained; the app's Postgres role lacks UPDATE/DELETE on it.
10. Audit export: date range or customer → CSV + printable HTML, including rule versions in force and any agent drafts with their evidence.
11. Business day = posting date; weekend/holiday cash rolls forward.
12. Free text stored verbatim, rendered escaped, never parsed; fixtures include hostile memos.
13. **Investigator agent (thin slice):** for one alert, assemble an **evidence pack** (the alert's hits, parameters, matched transactions, the customer's 90-day summary, prior alerts, country-risk entries in force), redact names and account numbers to tokens, call the LLM configured by environment variables (the bank's credentials; Anthropic SDK by default, provider switchable), and return a four-sentence "why flagged" plus a who/what/when/where/why narrative starter with citations back to evidence-pack items. Output is a draft the analyst must edit; it is stored with the alert, logged, and never changes status. Memos inside the evidence pack are wrapped as quoted data, never as instructions.

## Data model

| Entity | Key fields |
|---|---|
| `customer` | id (CIF), name, type, dob, address, phone, email, occupation, expected_monthly_cash, risk_tier, onboarded_on, ctr_exempt_phase, pep_flag |
| `account` | id, customer_id, type, opened_on, status, home_branch_id |
| `branch` | id, name, city, state, lat, lon, full_service |
| `entry` (was `transaction`; camt.054-entry-shaped, see D6) | entry_id, account_id, amount, currency, credit_debit, is_reversal, status, booking_ts, value_date, **business_date**, btc_domain, btc_family, btc_subfamily, btc_proprietary, channel, instrument_refs (end_to_end_id, uetr, trace_no, cheque_no), debtor / creditor (name, cif_id, country), debtor_account / creditor_account, debtor_agent / creditor_agent (routing, country), branch_id, conductor, purpose, memo, cash_detail, card_detail, source_message, raw_ref, typology_label (hidden) |
| `rule_version` | id, rule_id, version, mode, params JSON, weight, red_flag_ids, profile (default/seasonal), effective_from, effective_to, proposed_by, approved_by, reason |
| `hit` | id, run_id, rule_version_id, customer_id, account_id, business_day, group_key, matched_txn_ids, computed_values JSON |
| `alert` | id, customer_id, business_day, score, status, assigned_to, risk_tier_at_fire, created_at |
| `alert_hit`, `alert_event`, `suppression`, `audit_log`, `user`, `ctr_candidate`, `load_batch`, `run` | as named; `hit` is unique on (rule_version_id, customer_id, business_day, group_key) so hourly reruns upsert and two accounts of one customer keep separate hits |
| `rejected_entry` | id, load_batch_id, source, raw_row JSON, reason, created_at (client: bad rows are set aside with a reason, never dropped) |
| `agent_draft` | id, alert_id, model, prompt_hash, evidence_pack JSON, output, created_by, created_at |
| `country_risk` | country, tier, source, effective_from, effective_to |

---

# PART D — DATA PLAN

## D1. On disk (verified 2026-11-04, unchanged 2026-11-11)

| Path | Size / rows | Role |
|---|---|---|
| `data/raw/saml_d/SAML-D.csv` | 996 MB, 9,504,852 rows, 2022-10-07 → 2023-08-23; 12 columns; 7 payment types; 28 typologies | **Primary** bank book and label set |
| `data/raw/tide/generated_edges_HI.csv` + `generated_nodes_HI.csv` | 905 MB + 3.8 MB; 7.59M transactions, 28,550 ownership edges, 36,629 nodes with KYC-style attributes | Optional: R5 benchmark, native multi-account customers |
| `reports/`, `research_notes/`, `scripts/profile_*.py` | the other chat's dataset research and DuckDB profiling | Its SQL becomes our rule templates |
| `docs/discovery-call.html` | the Nov 5 deck | keep |
| `docs/data-and-rules-scope.md` = `reports/data-and-rules-scope.md` | duplicate | keep `docs/`, delete the copy |

Not on disk: OFAC/OpenSanctions, FDIC branches, FATF JSON, holidays. Not a git repository yet. Toolchain: Python 3.14 system, uv 0.12, Node 26, Docker 29, 24 GB RAM; no pandas/duckdb/django installed.

## D2. Canonical schema and adapters
All sources map once into the **camt.054-entry-shaped canonical record** defined in D6 and are stored as Parquet. Adapters: `saml_d`, `tide` (optional), `fixtures`, `core_csv` (Jack Henry / Fiserv shape), and later one per rail message (`pacs008`, `nacha`, `iso8583`, `x937`). Every adapter's only job is to fill the canonical fields and set the BankTransactionCode triplet; rules never see rail-specific columns. A **committed 2,000-row fixture Parquet** (synthetic, generated by `screener fixtures`) is the day-0 contract every rule owner develops against before the SAML-D adapter lands.

SAML-D payment types map to triplets as: Cash Deposit → `PMNT/CNTR/CDPT`; Cash Withdrawal → `PMNT/CNTR/CWDL` (or `PMNT/CCRD/CWDL` when the US layer assigns ATM); ACH → `PMNT/ICDT|RCDT/ATXN` with `btc_proprietary` = a seeded SEC code; Cross-border → `PMNT/ICDT|RCDT/XBCT`; Cheque → `PMNT/ICHQ|RCHQ/CCHQ`; Credit/Debit card → `PMNT/CCRD/POSC|POSD`; the synthetic P2P share → `PMNT/ICDT|RCDT/DMCT` with `btc_proprietary` = `ZELLE` (there is no P2P sub-family in the standard, which is also how banks code it today).

## D3. The US layer on SAML-D (owner: Abdul, ~3–4 person-days)
Currency 1:1 USD · customers: one account = one customer, plus a disclosed label-blind 10% sample grouped into 2–3-account customers · KYC tier 80/15/5 seeded and shown next to every flag (KYC lives in the core; we do not re-verify or screen) · open date = first-seen after 90-day warm-up · US federal holidays 2022–2023 · branches from FDIC SOD renamed, home branch ~80%, label-blind · channels (ATM p=0.7 on withdrawals ≤$1,000; night-drop share on deposits) · P2P relabel p=0.3 on debit < $1,000 between personal accounts · demo subsample of about 300,000 accounts keeping all labelled accounts, so that daily rows land near the client's "tens of thousands, tops" (assumption, documented) · typology injection with `answer_key.json` (each rule owner writes the injector for their own rules against a shared injector interface).

## D4. Reference data
OFAC SDN + Consolidated CSV (public domain) [S58][S59]; OpenSanctions `us_sanctions`, `peps`, `us_fincen_special_measures` (CC BY-NC, class use only) [S64]; FATF point-in-time JSON (black: DPRK, Iran, Myanmar; grey with effective dates: Turkey Oct 2021–Jun 2024, UAE Mar 2022–Feb 2024, Nigeria Feb 2023–Oct 2025, Albania Feb 2020–Oct 2023, Morocco Feb 2021–Feb 2023, Pakistan Jun 2018–Oct 21 2022 — **verify each date in a browser**) [S61]; FDIC SOD; pandas holiday calendar.

## D5. Licence and repo rules
SAML-D CC BY-NC-SA: coursework qualifies; **no rows in the repo**. Tide CC BY 4.0: a small sample may be committed with attribution. `data/raw/`, `data/parquet/`, `kaggle.json`: gitignored, and pre-commit blocks any file over 1 MB.

## D6. Can our data live in one industry-standard format? (researched 2026-11-11)

**Short answer: yes, at the booked-entry level; no, at the wire level.** Each rail speaks its own standard and that will not change in our horizon:

| Rail | Standard on the wire today (US, Nov 2026) | Status of the spec | Evidence |
|---|---|---|---|
| Fedwire Funds | ISO 20022 since 14 Jul 2025 (pacs.008/009/004, camt.056/029, camt.110/111) | Specs on Swift MyStandards; free swift.com login required | frbservices FAQ [S95] [verified] |
| CHIPS | ISO 20022 since 8 Apr 2024 | TCH release | [S96] [verified] |
| FedNow, RTP | ISO 20022 (pacs.008 settles; pacs.002, pain.013/014, camt.026/028/056/029) | RTP PDFs public; FedNow specs need MyStandards | [S97] [verified] |
| Swift cross-border | ISO 20022 CBPR+; MT coexistence ended 22 Nov 2025; MT101 end date conflicting (Nov 2026 vs "delayed") | swift.com blocks fetch | [S98] [secondary] |
| ACH | **Nacha**, fixed-width 94-char records, SEC codes PPD/CCD/WEB/TEL/IAT; not ISO | Developer guide free; Operating Rules sold | [S99] [verified] |
| Cards, ATM | **ISO 8583**; ISO 20022 for cards exists but no network has a migration date | — | [S100] [secondary] |
| Cheques | **ANSI X9.100-187** image cash letter; paywalled; open parser moov-io | — | [S101] [verified] |
| Zelle | Proprietary participant files; no public schema; settlement over RTP uses ISO 20022 | portal participant-gated | [S102] [secondary] |
| Teller cash | No interbank message; core posting record. Nearest standards: X9.121 BTRS (ex-BAI2) type codes and ISO 20022 BkTxCd `PMNT/CNTR/CDPT|CWDL` | X9.121 free | [S103] [verified] |

**The unifying layer is ISO 20022 account reporting (camt.052/053/054).** Every rail ends as a debit or credit entry on a customer account, and that is exactly what a camt.054 `Ntry` models: amount, credit/debit indicator, booking and value dates, a **BankTransactionCode** triplet saying what kind of entry it is, and transaction details with references, related parties (debtor/creditor with identifiers), related agents (banks, with a branch element), remittance text, dates and even a cash-deposit detail block. The taxonomy is open: the ISO 20022 external code sets and the BankTransactionCode codification (about 1,500 permitted Domain/Family/SubFamily combinations) download without a login [S104–S106] [verified, files parsed]. Nacha publishes a free ACH-to-camt.053 mapping guide [S107] [verified]; HSBC and ING publish their BAI2/ISO code maps [S108]. The open-source monitors confirm the direction: Tazama ingests ISO 20022 pain.001, pain.013, pacs.008 and pacs.002 and stores the raw messages unaltered for audit; Mojaloop maps its API to pacs.008/002 [S109] [verified]. Nobody has published a cross-rail canonical that covers teller cash and cheques, so ours is a small, defensible extension of a standard rather than an invention.

**Verified BankTransactionCode triplets we use** (from the Nov 2025 BTC description v8.0 and the codification spreadsheet):

| Event | Triplet |
|---|---|
| Cash deposit / withdrawal at counter | `PMNT/CNTR/CDPT` · `PMNT/CNTR/CWDL` (branch variants `BCDP`/`BCWD`) |
| ATM withdrawal / deposit / withdrawal abroad | `PMNT/CCRD/CWDL` · `PMNT/CCRD/CDPT` · `PMNT/CCRD/XBCW` |
| Card POS debit / credit | `PMNT/CCRD/POSD` · `PMNT/CCRD/POSC` |
| Domestic credit transfer out / in (wire) | `PMNT/ICDT/DMCT` · `PMNT/RCDT/DMCT` |
| Cross-border transfer out / in | `PMNT/ICDT/XBCT` · `PMNT/RCDT/XBCT` |
| Instant transfer out / in (FedNow, RTP) | `PMNT/IRCT/DMCT` · `PMNT/RRCT/DMCT` |
| ACH credit / debit | `PMNT/ICDT|RCDT/ATXN` (Nacha guide), also `ACDT`, `ADBT` |
| Direct debit issued / received | `PMNT/IDDT/PMDD` · `PMNT/RDDT/PMDD` |
| Cheque issued / received | `PMNT/ICHQ/CCHQ` · `PMNT/RCHQ/CCHQ` |
| Fees / interest | `ACMT/MDOP|MCOP/FEES` · `ACMT/MCOP|MDOP/INTR` |
| Unknown | `PMNT/OTHR/OTHR` or `NTAV` |
| P2P (Zelle) | **no sub-family exists**; code as `ICDT|RCDT/DMCT` (or `IRCT|RRCT` over RTP) with `Prtry/Cd = ZELLE` |

**Customer identity.** ISO 20022 carries the bank's customer number as a party identifier with scheme code `CUST` ("CustomerIdentificationNumber"), verified in the 2Q2026 external code sets [S104]. Risk tier, KYC status and PEP flags have **no ISO element**; banks keep them in customer-master domains (BIAN "Party Reference Data Directory", FIBO ontology) [S110]. We keep them in `party_ext` joined on `cif_id`.

**Regulatory output.** FinCEN's CTR and SAR XML schema user guides are public PDFs [S111][S112] [verified, parsed]. The CTR aggregates per person per business day per direction over cash, distinguishes the conductor (party type 50/17) from the beneficiary (23), carries account numbers per side and a transaction location (34 = branch), with detail codes 55 Deposit and 56 Withdrawal. That dictates four canonical fields ISO lacks or only approximates: `business_date`, `conductor`, `branch_id` (ISO has `BrnchId` under the agent) and `cash_detail`.

**Our canonical record: a camt.054 entry profile plus three extensions**

| # | Field | ISO 20022 origin (camt.054.001.13, relative to `Ntfctn`) | Note |
|---|---|---|---|
| 1 | `entry_id` | `Ntry/NtryRef` or `AcctSvcrRef` | |
| 2 | `account_id` | `Acct/Id/Othr/Id` | our customer's account |
| 3–4 | `amount`, `currency` | `Ntry/Amt`, `@Ccy` | |
| 5 | `credit_debit` | `Ntry/CdtDbtInd` | CRDT / DBIT |
| 6 | `is_reversal` | `Ntry/RvslInd` | |
| 7 | `status` | `Ntry/Sts/Cd` | BOOK / PDNG |
| 8–9 | `booking_ts`, `value_date` | `Ntry/BookgDt`, `Ntry/ValDt` | |
| 10 | `business_date` | **none**; `TxDtls/RltdDts/Prtry{Tp=BUSD}` on export | CTR aggregation key; weekend/holiday roll-forward |
| 11 | `btc_domain`, `btc_family`, `btc_subfamily` | `Ntry/BkTxCd/Domn/Cd`, `Fmly/Cd`, `Fmly/SubFmlyCd` | replaces the ad-hoc `category` enum |
| 12 | `btc_proprietary` | `Ntry/BkTxCd/Prtry/Cd` + `Issr` | ZELLE, SEC code, BAI type code, ISO 8583 processing code |
| 13 | `channel` | `Ntry/TechInptChanl` | TELLER / ATM / ONLINE / MOBILE / NIGHT_DROP |
| 14 | `instrument_refs` | `TxDtls/Refs/{EndToEndId, UETR, ClrSysRef, ChqNb}` | UETR for wires, ACH trace, cheque serial |
| 15–16 | `debtor`, `creditor` (+ accounts) | `TxDtls/RltdPties/Dbtr|Cdtr/Pty/{Nm, PstlAdr, Id, CtryOfRes}`, `DbtrAcct|CdtrAcct` | counterparty country for R6 |
| 17 | `debtor_agent`, `creditor_agent` | `TxDtls/RltdAgts/DbtrAgt|CdtrAgt/FinInstnId/{ClrSysMmbId/MmbId (USABA), BICFI, Nm}` | |
| 18 | `branch_id` | `RltdAgts/…/BrnchId/Id` | CTR party type 34 |
| 19 | `conductor` | nearest `RltdPties/UltmtDbtr|UltmtCdtr` or `InitgPty` | person at the counter ≠ account owner |
| 20 | `cif_id` per party | `Pty/Id/PrvtId|OrgId/Othr/{Id, SchmeNm/Cd=CUST, Issr}` | verified code |
| 21 | `risk_tier`, `kyc_status`, `pep_flag` | **none**; `party_ext` table | |
| 22 | `purpose` | `TxDtls/Purp/Cd` | |
| 23 | `memo` | `TxDtls/RmtInf/Ustrd`, `Ntry/AddtlNtryInf` | always rendered escaped |
| 24 | `cash_detail` | `TxDtls/CshDpst` | denominations, for structuring |
| 25 | `card_detail` | `Ntry/CardTx` | masked PAN, MCC, terminal |
| 26 | `source_message`, `raw_ref` | **none**; `SplmtryData` on export | pacs.008 / nacha / iso8583 / x937 / zelle / teller / saml_d / fixture, plus pointer to the stored raw record |

Deviations from the standard are exactly four (`business_date`, `conductor`, `risk_tier` family, `source_message`), each with a documented landing zone, so a genuine camt.054 export of our entries is possible if an auditor or a vendor asks for one. This is the answer to "can this even be done": the per-rail schemas stay different at the edge, one adapter each; the rules, the UI, the audit trail and the agent see one standard-shaped record.

**Consequences for the build:** `category` becomes the BTC triplet everywhere (rules filter on `btc_family IN ('CNTR','CCRD')` for cash, on `btc_subfamily = 'XBCT'` for cross-border, on `btc_proprietary = 'ZELLE'` for P2P); the tran-code map in `data/reference/` maps core codes → triplets; `data/reference/iso20022/` holds the downloaded external code sets, BTC codification and the camt.054 XSD; `screener export --format camt054` is a stretch ticket (TRA-48). Nothing in the rules changes except column names.

## D7. Dataset and reference-data availability register (every item checked 2026-11-11)

| Asset | Where to get it | Checked how | Result | Licence | Where it lives for us |
|---|---|---|---|---|---|
| **SAML-D** (9,504,852 rows) | Kaggle `berkanoztas/synthetic-transaction-monitoring-dataset-aml` [S51] | page HTTP 200; download needs a free Kaggle account or API token; file already on disk, 996,168,850 bytes | **Available, on disk** | CC BY-NC-SA 4.0 (Kaggle page; coursework OK) | `data/raw/saml_d/SAML-D.csv` (gitignored); `~/Downloads/archive.zip` is the same file |
| **Tide HI** (edges + nodes) | Zenodo records 18804069 (paper/dataset) and 20591329 (reference HI/LI data), `access_right: open` [S52] | record pages HTTP 200; API JSON 200 with default agent; MD5s matched by the Nov 4 profiling | **Available, on disk** | CC BY 4.0 | `data/raw/tide/generated_edges_HI.csv`, `generated_nodes_HI.csv` (gitignored) |
| Tide generator | github.com/mntijn/Tide | HTTP 200 | Available | MIT | not vendored; cite |
| IBM AMLworld / AML-Data | github.com/IBM/AML-Data (Kaggle `ealtman2019/…`) | HTTP 200; README states data is CDLA-Sharing-1.0 | Available, **not used** (10 primary days; "cash" is a transfer) | CDLA-Sharing-1.0 | — |
| AMLNet v2 | Zenodo 21237971 | HTTP 200 | Available, **not used** (AUD, CASH_OUT only, CC BY-NC) | CC BY-NC 4.0 | — |
| SynthAML alerts | figshare collection 6504421 (article 22396057 `synthetic_transactions`) | API HTTP 200 | Available, optional disposition prior | CC0 | `data/reference/synthaml/` if used |
| **OFAC SDN** (+ADD, ALT) | `sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV` [S58] | HTTP 200, 5.83 MB, published 2026-11-09 | **Available, no key** | US public domain | `data/reference/ofac/` via `fetch_lists.sh` |
| **OFAC Consolidated** | same host, `CONS_PRIM.CSV` [S59] | HTTP 200, 269 KB | Available | public domain | same |
| **UN Security Council consolidated** | `scsanctions.un.org/resources/xml/en/consolidated.xml` [S60] | HTTP 200, 2.18 MB | Available | free | same |
| **OpenSanctions** `us_ofac_sdn`, `us_sanctions`, `us_fincen_special_measures`, `peps` | `data.opensanctions.org/datasets/latest/<name>/targets.simple.csv` [S64] | index.json HTTP 200 for all four; `us_sanctions` CSV 12.0 MB; `us_ofac_sdn` 72,987 entities exported 2026-11-11 | Available, bulk, no key | CC BY-NC 4.0 (class use OK; licence for a real bank) | `data/reference/opensanctions/` via `fetch_lists.sh` |
| **FDIC Summary of Deposits branches** | `api.fdic.gov/banks/sod?filters=YEAR:2025 AND STALPBR:NJ AND ASSET:[1000000 TO 5000000]&fields=NAMEFULL,NAMEBR,CITYBR,STALPBR,DEPSUMBR,ASSET,BRNUM,UNINUMBR,SIMS_LATITUDE,SIMS_LONGITUDE` | HTTP 200; 263 NJ branches of $1–5B banks returned with coordinates; variable definitions CSV HTTP 200 | **Available, no key** | US public data | `data/reference/branches_fdic.csv` |
| **FATF black/grey lists** | fatf-gafi.org black-and-grey-lists page [S61] | **HTTP 403 to scripts**; must be read in a browser | Available in a browser only | public | hand-coded `data/reference/country_risk.csv` with `verified_on` |
| US federal holidays | OPM federal-holidays page; pandas `USFederalHolidayCalendar` | HTTP 200 | Available | public | `data/reference/holidays_us.csv` |
| ISO 3166 country codes | `raw.githubusercontent.com/datasets/country-codes/main/data/country-codes.csv` | HTTP 200, 134 KB | Available | mixed open | `data/reference/country_codes.csv` |
| **ISO 20022 external code sets** (2Q2026 v3) | `iso20022.org/sites/default/files/media/file/ExternalCodeSets_XLSX.zip` [S104] | zip HTTP 200 and parsed (the HTML page is 403) | **Available, no login** | ISO 20022 free use | `data/reference/iso20022/` |
| **BankTransactionCode description v8.0 (Nov 2025) and codification (Mar 2024)** | `…/BTC_ExternalCodeListDescription_Nov2025.docx`, `…/BTC_Codification_21March2024.xlsx` [S105][S106] | HTTP 200, parsed, 1,567 combinations | Available | free | same |
| **camt.054.001.13 XSD** | `iso20022.org/sites/default/files/documents/messages/camt/schemas/camt.054.001.13.xsd` | HTTP 200, parsed | Available | free | same |
| Nacha ACH developer guide; Nacha ISO 20022 camt.053 mapping guide | achdevguide.nacha.org/ach-file-details; nacha.org PDF [S99][S107] | guide readable; PDF HTTP 200 | Available (Operating Rules are sold) | free | cite; `docs/05` |
| FinCEN CTR and SAR XML user guides | bsaefiling.fincen.gov/docs/XMLUserGuide_FinCENCTR.pdf (v1.8), …FinCENSAR.pdf (v1.6) [S111][S112] | HTTP 200, 2.5 MB and 3.7 MB, parsed | Available | public | `docs/` reference links |
| FinCEN SAR Stats | fincen.gov/reports/sar-stats | HTTP 200 | Available | public domain | sizing slide |
| FFIEC manual Appendix F | bsaaml.ffiec.gov/manual/Appendices/07 | **403 to scripts** | browser only | public | `rules/red_flags.yaml` hand-curated |
| Tazama docs | github.com/tazama-lf/docs | HTTP 200 | Available | Apache-2.0 | cite only |
| FinCEN 314(a) list | — | not public by design | **Not available**; mocked | — | synthetic list in fixtures |
| Zelle / Early Warning schema | developer.earlywarning.com | participant-gated, JS-only | **Not available**; P2P rail is synthetic and disclosed | — | — |
| Jack Henry / Fiserv / FIS export layouts | vendor portals | behind vendor logins | **Not available**; `core_csv` adapter follows the public jXchange field list | — | — |

---

# PART E — TECHNICAL ARCHITECTURE

## E1. Principles
Determinism (any day re-runnable from inputs + rule versions), compute separated from state, append-only evidence, role-based access, reproducible deployment inside the bank, observability, documented lineage, and a per-rule folder layout so four owners rarely touch the same file. One layered Python monolith with two stores. Not microservices.

## E2. Stack (decided)

| Layer | Choice | Why |
|---|---|---|
| Language / tooling | **Python 3.13 pinned with `uv`**; `ruff`, `pytest`, `pre-commit` | uv installed; reproducible |
| Rules compute | **DuckDB over Parquet**, rules as parameterised SQL templates (Jinja2 for parameters, read-only) | profiling SQL already exists; windowed aggregations native; 9.5M rows in seconds |
| Dataframes | Polars for adapters and injection | speed on 1 GB files |
| Operational store | **PostgreSQL 16** (Docker) for alerts, dispositions, users, audit, rule versions, agent drafts; SQLite for unit tests | revoke UPDATE/DELETE on `audit_log`; the enterprise story |
| Web | **Django 5 + HTMX + Tailwind (CDN)** — decided; the kickoff's "admin console to change thresholds and add rules without recoding" is Django admin plus maker-checker | auth, roles, ORM, migrations, admin, CSRF, autoescaping, `django-simple-history` built in |
| Agent | Anthropic Python SDK behind a small `LLMClient` interface; provider and credentials from environment; deterministic stub for tests and CI | bank's own credentials; no vendor lock |
| Background | `screener` CLI via `docker compose run` / cron | hourly incremental run (`--since`) plus nightly reconciliation (`--reconcile`), per the client's reply |
| Proxy / TLS | Caddy | two-line config |
| CI | GitHub Actions (E5) | |
| Observability | structured JSON logs; `run` manifest; `/healthz` | |
| Secrets | `.env` (gitignored) + Docker secrets; `.env.example` committed | |

## E3. Component architecture

```
 core CSV / SAML-D / Tide / fixtures
        │  adapters/*.py → canonical Parquet → us_layer → load_batch reconciliation
        ▼
 REFERENCE DATA  country_risk (point-in-time) · holidays · branches · tran_code_map
        ▼
 RULES ENGINE (DuckDB)   rules/rNN_*/rule.yaml + rule.sql (12 folders, one owner each)
        │  engine.run(day) → hits · engine.backtest(version, range) · consolidate → alerts · score
        ▼
 ALERT MANAGEMENT (Postgres)  alerts · hits · events · suppression · CTR candidates · rule_versions (maker-checker)
        │  AUDIT (append-only, hash-chained) · RBAC (Analyst / BSA Officer / Auditor)
        ▼
 WEB UI (Django + HTMX)  queue · alert detail with per-rule evidence panels · disposition · four-eyes
        │  admin console (thresholds, profiles, rules) · backtest · customer page · audit export
        ▼
 INVESTIGATOR AGENT (thin)  evidence pack → redact → LLM (bank credentials) → draft with citations → stored, never decides
 EVALUATION (CLI)  precision / recall / lift per rule on SAML-D labels + answer key
```

**Day-0 contracts** (written into `docs/05-architecture.md` and enforced by tests; these are what let four people work in parallel):
1. Canonical Parquet schema (column names, types) and the committed fixture Parquet.
2. **Rule contract:** `rules/<id>_<slug>/rule.yaml` (id, name, owner, version, mode, key, windows, params, weight, red_flag_ids, budget_per_month, description) and `rule.sql` returning `(customer_id, account_id, business_day, group_key, matched_txn_ids, computed_values)`; the engine globs the folders; a rule can be added without touching shared code.
3. **Evidence-panel contract:** `rules/<id>_<slug>/evidence.html`, a Django template partial receiving `hit` (with `computed_values`) and `txns`; the alert page includes one per hit. Owners build UI for their rules without editing the alert page.
4. **Injector contract:** `rules/<id>_<slug>/inject.py` exposing `inject(df, rng, n) -> (df, cases)`; the US layer calls each and writes `answer_key.json`.
5. **Hit → alert contract:** consolidation and scoring read only the six hit columns plus `rule.yaml` weight and mode.
6. **Agent tool contract:** `rules/<id>_<slug>/explain.py` exposing `evidence(hit) -> list[EvidenceItem]`; the agent harness concatenates them.

## E4. Interface decision record (ADR-001)
Django + HTMX + Tailwind. Reasons: the client asked for an admin console for thresholds and rules without recoding, which Django admin plus `django-simple-history` provides in a day; roles, audit and forms are the product; one language and one build system for four people. Alternatives considered: FastAPI + HTMX (1–2 days more plumbing), FastAPI + React (two build systems), Streamlit (no real roles). Revisit only if someone volunteers to own a React front end end-to-end.

## E5. Git and CI hygiene

**Repository.** GitHub repo `transaction-alert-screener` (public, per the assignment's "public repository URL"). Default branch `main`, protected: pull request required, one approval from a CODEOWNER of the touched paths, all required checks green, linear history (squash merge), no force-push, conversation resolution required. `CODEOWNERS` maps `rules/r01_*`, `rules/r02_*`, `rules/r03_*`, `screener/audit*`, `.github/`, `Dockerfile`, `docker-compose*.yml` → Vedant; `rules/r04_*`, `r07_*`, `r08_*`, `screener/engine*`, `screener/consolidate*`, `screener/scoring*` → Vedanshu; `rules/r05_*`, `r10_*`, `r12_*`, `screener/adapters/`, `screener/us_layer/`, `screener/evaluate*` → Abdul; `rules/r06_*`, `r09_*`, `r11_*`, `app/` → Natalie; `docs/` → anyone, one approval.

**Branches and commits.** Branch per Linear issue, named by Linear's suggested format `vedant/tra-12-ctr-candidate-rule`, so Linear auto-links and moves the issue to In Progress on first push and to Done on merge. Conventional Commits (`feat(r02): add 30-day structuring variant`), PR title prefixed with the issue key (`TRA-12: …`). PRs under ~400 lines; one issue per PR. PR template: What / Why / How tested / Screenshots for UI / Checklist (tests added, docs updated, no data committed, rule.yaml version bumped if params changed). Draft PRs early.

**Pre-commit** (runs locally and as a CI job): `ruff` lint + format, `check-added-large-files --maxkb=1024`, `check-yaml`, `end-of-file-fixer`, `gitleaks` for secrets, `hadolint` for the Dockerfile.

**GitHub Actions.**
- `ci.yml` on every PR and on push to `main`:
  1. `lint`: `uv sync --frozen`, `pre-commit run --all-files`.
  2. `test`: `pytest -m "not integration"` on SQLite with coverage; uploads the coverage report as an artifact.
  3. `integration`: Postgres 16 service container; `pytest -m integration` (state machine, four-eyes, append-only audit, migrations).
  4. `rules`: `screener fixtures && screener run --day <fixture day> --store sqlite` then `pytest tests/rules` (every rule on boundary fixtures, every injected typology ≥0.9 recall, `rule.yaml` schema and red-flag integrity, every live rule's fixture-corpus volume within budget).
  5. `docker`: `docker buildx build` with GitHub Actions cache; `docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --wait`; wait for `/healthz`; `docker compose run app screener fixtures && screener load && screener run`; assert alerts > 0 via a management command; `docker compose logs` on failure; `down -v`. This is the "Dockerfile runs through CI" requirement.
  6. `security`: `trivy image` on the built image (fails on critical CVEs) and `pip-audit`.
  Required checks for merge: lint, test, integration, rules, docker.
- `publish.yml` on push to `main`: builds and pushes `ghcr.io/<org>/transaction-alert-screener:{sha,main}`; on a `v*` tag also `:vX.Y.Z` and `:latest`, and creates a GitHub Release with auto-generated notes.
- `dependabot.yml`: weekly updates for GitHub Actions, Docker base images and Python (uv lockfile), grouped.
- Concurrency groups cancel superseded runs on the same PR; all jobs pinned to action SHAs.

**Docker.** Multi-stage `Dockerfile` (uv builder → slim runtime, non-root user, `HEALTHCHECK` on `/healthz`). `docker-compose.yml`: `app` (gunicorn), `scheduler` (runs `screener run --since last` hourly and `--reconcile` nightly via `supercronic`), `db` (Postgres 16 with a named volume and an init script that creates the restricted app role), `caddy` (TLS). `docker-compose.ci.yml` overrides: no caddy, app on `localhost:8000`, deterministic LLM stub, ephemeral volumes. `docker-compose.demo.yml`: preloads the demo subsample. `make up / make test / make demo` wrap the common commands.

**Environments.** `dev` (compose on a laptop, SQLite optional), `ci` (compose.ci), `demo` (compose.demo on one VM or a laptop for the client walkthrough), `bank` (compose behind the bank's proxy with their LLM credentials; documented, not provisioned by us).

---

# PART F — OWNERSHIP, LINEAR WORKSPACE, TICKETS, SCAFFOLD, CALENDAR

## F1. Ownership model: four processes, end to end
Each owner delivers, for their three rules: the SQL and `rule.yaml`, boundary fixtures and injector, unit and answer-key tests, the measured volume and precision/recall on SAML-D written into `docs/09-evaluation.md`, the evidence panel the analyst sees, the agent `explain()` tool, and the rules-catalogue section. Each owner also owns **one platform component** so platform work is spread equally and no single person is a bottleneck. Everyone integrates into the UI through the day-0 contracts rather than by editing shared pages.

| Owner | Process (rules) | Platform component | UI surfaces owned |
|---|---|---|---|
| **Vedant** | Cash & CTR (R1, R2, R3) | Repo, CI, Docker, audit log, audit export, reference data loader | CTR candidates page; audit export page; evidence panels r01–r03 |
| **Vedanshu** | Account behaviour (R4, R7, R8) | Rules engine core: loader, templating, run, backtest, consolidation, scoring | Customer page (account timeline, dormancy view); backtest page; evidence panels r04, r07, r08 |
| **Abdul** | Funds movement (R5, R10, R12) | Data: adapters, canonical Parquet, US layer, injection framework, evaluation harness, demo subsample | Funds-flow view on the alert page (in/out within window); evaluation dashboard page; evidence panels r05, r10, r12 |
| **Natalie** | Counterparty & rails (R6, R9, R11) | Django app skeleton, auth and roles, queue, alert detail shell, disposition state machine, four-eyes, admin console with maker-checker | Queue; alert detail shell; disposition forms; admin console; counterparty/country panel; evidence panels r06, r09, r11 |
| **Shared, lead-coordinated** | Investigator agent thin slice | Harness by Vedant; each owner's `explain.py` feeds it | Agent draft panel on the alert page |

## F2. Linear workspace design (workspace `Transaction-Monitoring`, team `TRA`, four members present, created Nov 11)

**Team settings to change by hand** (the API cannot): enable **Cycles**, weekly, starting Wednesday, auto-add started issues to the current cycle; enable **Estimates** (Fibonacci points 1, 2, 3, 5, 8); default issue template set to the one below; default status for new issues Backlog; triage off.

**Statuses:** keep Backlog, Todo, In Progress, Done, Canceled, Duplicate; **add `In Review`** (started type) so a PR awaiting review is visible.

**Labels** (groups): `type/` feature, chore, bug, docs, spike, test · `area/` data, rules, ui, platform, ci, agent, docs, client · `rule/` R01…R12 · `contract` (changes a day-0 contract; needs all four reviewers). The existing Bug and Feature labels are moved into `type/`; Improvement is deleted.

**Projects** (each with a lead, a description, milestones and a target date):

| Project | Lead | Milestones |
|---|---|---|
| P0 Platform & Delivery | Vedant | M0 Scaffold and contracts merged · M1 CI green with Docker smoke · M2 Demo environment · M3 Leadership-deck build |
| P1 Cash & CTR | Vedant | M1 Rules green on fixtures · M2 Measured on SAML-D · M3 UI integrated · M4 Agent explain |
| P2 Account Behaviour | Vedanshu | same four |
| P3 Funds Movement | Abdul | same four |
| P4 Counterparty & Rails | Natalie | same four |
| P5 Investigator Agent | Vedant | M1 Harness with stub · M2 Four explain tools · M3 Draft panel in UI |
| P6 Client & Docs | Vedant | M1 Research docs in repo · M2 Demo script · M3 Leadership presentation outline |

**Issue template** (`Default`): Context (one paragraph, why this exists and which client need it serves) · Scope (bullet list of what changes, files or modules) · Out of scope · Acceptance criteria (checkboxes, testable) · Dependencies (blocked-by issue keys, or "none") · Test evidence (what the PR must show) · Docs touched.

**Views:** "My cycle" per member; "Blocked" (has blocked-by relation unresolved); "Contract changes" (label `contract`); "Ready for review" (status In Review).

**Working agreement:** one issue per PR; move to In Review when the PR is opened; the reviewer is the CODEOWNER; anything that changes a contract gets the `contract` label and a 15-minute sync; daily 10-minute standup; Friday demo of each slice on the fixture corpus.

## F3. The tickets

Estimates in points. "Dep" = blocked by. Cycle C1 = this week, C2 = next, C3 = the week after. Every ticket below is written in the template shape (Context · Scope · AC · Dep · Evidence); descriptions are condensed here and expanded verbatim when created.

### P0 Platform & Delivery (Vedant)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-1 | Repo scaffold, uv project, pre-commit, PR template, CODEOWNERS | 3 | C1 day 0 | — | Context: nothing exists; four people start tomorrow. Scope: tree in F4; `pyproject.toml` with pinned 3.13; `.pre-commit-config.yaml` (ruff, large-file block 1 MB, gitleaks, hadolint); `.gitignore` for data; PR template; CODEOWNERS per F1; MIT licence; README skeleton with ownership table and meeting-notes section. AC: `uv sync` and `pre-commit run --all-files` pass on a clean clone; `git log` shows one initial commit; branch protection on `main` configured as in E5. Evidence: screenshot of branch-protection settings. |
| TRA-2 | Day-0 contracts: camt.054-shaped canonical entry schema, BankTransactionCode taxonomy, fixture Parquet, rule/evidence/injector/explain contracts | 5 | C1 day 0 | TRA-1 | Context: these contracts are what let four slices proceed in parallel, and the canonical record follows ISO 20022 camt.054 so the bank's real rails can be adapted later without touching rules (D6). Scope: `screener/schema.py` (pyarrow schema for the 26 fields in D6), `screener/btc.py` loading the ISO BankTransactionCode codification and validating triplets, `screener fixtures` generating a 2,000-row synthetic Parquet covering every triplet and channel we use, `docs/05-architecture.md` contract section with the field-to-XPath table, `tests/test_contracts.py` validating any `rules/*/rule.yaml` against a JSON schema, checking `rule.sql` returns the five hit columns on the fixture Parquet, and rejecting any entry whose triplet is not in the codification. AC: `rules/r00_example/` passes; fixture Parquet committed and under 1 MB; every fixture triplet validates. Label `contract`. |
| TRA-3 | GitHub Actions `ci.yml`: lint, unit, integration (Postgres service), rules | 3 | C1 | TRA-1 | Scope per E5 jobs 1–4, concurrency groups, SHA-pinned actions, coverage artifact. AC: a PR with a deliberate ruff error fails `lint`; a PR with a failing fixture test fails `rules`; green on `main`. |
| TRA-4 | Dockerfile, docker-compose (app, scheduler, db, caddy), compose.ci, compose.demo, Makefile | 5 | C1 | TRA-1 | Scope: multi-stage uv image, non-root, HEALTHCHECK; Postgres init script creating the restricted `app` role without UPDATE/DELETE on `audit_log`; supercronic scheduler; Caddyfile. AC: `make up` serves `/healthz` 200 locally; `docker compose run app screener --help` works; image under 400 MB. |
| TRA-5 | CI `docker` job: build with cache, compose up, healthz, fixture run, alert-count assertion, trivy | 3 | C1 | TRA-3, TRA-4 | Scope per E5 job 5–6. AC: the job fails if `/healthz` never returns 200 within 60s or if the fixture run yields zero alerts; trivy fails on critical CVEs; logs are uploaded on failure. |
| TRA-6 | `publish.yml`: push image to GHCR on main and tags; GitHub Release on `v*`; dependabot | 2 | C2 | TRA-5 | AC: `ghcr.io/<org>/transaction-alert-screener:main` exists after merge; `v0.1.0` tag creates a release with notes and `:latest`. |
| TRA-7 | Audit log module: append-only writer, hash chain, `audit.record()` helper, access logging middleware | 3 | C1 | TRA-2 | Context: C9 and the Blue Ridge checklist. Scope: `screener/audit.py`, Django model, middleware logging Auditor views and any SAR-status view. AC: integration test proves the app role cannot UPDATE/DELETE; chain verifies; every write path in the app calls `audit.record()` (grep test). |
| TRA-8 | Audit export: CSV + printable HTML for a date range or a customer, including rule versions in force and agent drafts | 3 | C2 | TRA-7, TRA-31 | AC: export for July 2023 on the demo subsample opens in Excel; printable view renders without JS; export action itself is audited. |
| TRA-9 | Reference data loader: holidays, FDIC branches (NJ, $1–5B banks, verified API), country_risk point-in-time table, tran-code → BankTransactionCode map; `fetch_lists.sh` for OFAC, UN, OpenSanctions and the ISO 20022 code sets, BTC codification and camt.054 XSD (all URLs in D7) | 3 | C1 | TRA-2 | AC: `screener refdata load` populates tables; `fetch_lists.sh` downloads every D7 asset with a checksum log; `country_risk` lookups by date return Turkey as grey on 2023-03-01 and normal on 2026-11-11; every FATF date row has a `verified_on` and a source URL; every tran-code map row resolves to a valid triplet. |
| TRA-48 | Stretch: `screener export --format camt054` producing a schema-valid camt.054.001.13 XML for a date range (business_date in `RltdDts/Prtry`, source in `SplmtryData`) | 3 | C3 or later | TRA-2 | Context: proves the "standard format" claim to the client and gives vendors a bake-off input. AC: output validates against the downloaded XSD; round-trip test reads it back into the canonical schema with no field loss. |
| TRA-10 | Demo environment: compose.demo preloads the 100k-account subsample, seeded users for three roles, demo day 2023-07-14 | 2 | C3 | TRA-4, TRA-20 | AC: `make demo` on a clean machine reaches a populated queue in under 10 minutes; passwords only in `.env.example` with a warning. |

### P1 Cash & CTR (Vedant)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-11 | R1 CTR candidate rule, fixtures, tests | 3 | C1 | TRA-2 | Scope: `rules/r01_ctr/` with `rule.yaml`, `rule.sql` (per-customer per-business-day cash-in and cash-out totals, separately, never netted), `inject.py` (5 CTR days), tests for $10,000.00 vs $10,000.01, two accounts one customer, two branches, Friday→Monday and holiday roll-forward. AC: all fixture tests pass; writes to `ctr_candidate`, not `hit`. |
| TRA-12 | R2 multi-day structuring rule (variants a and b), fixtures, injector | 3 | C1 | TRA-2 | AC: fixtures pass; on SAML-D reproduces 40 accounts / 90% precision / 57% recall for (a) and 15 / 100% / 24% for (b) (after TRA-20). |
| TRA-13 | R3 same-day / cross-branch structuring rule, fixtures, injector | 2 | C1 | TRA-2 | AC: ~10 injected cases recalled ≥0.9; natural volume reported as ~0 in docs/09. |
| TRA-14 | Evidence panels r01–r03 and the CTR candidates page | 3 | C2 | TRA-30 | Scope: `evidence.html` for each rule showing deposits by day and branch with the threshold line; CTR page with reconcile status. AC: renders from the fixture run; a hostile memo renders as text; screenshot in PR. |
| TRA-15 | `explain.py` for r01–r03 (agent evidence items) | 1 | C2 | TRA-40 | AC: returns cited items; unit test with the stub LLM. |
| TRA-16 | Measure R1–R3 on SAML-D; write volumes, precision, recall, lift to docs/09; set modes and budgets | 2 | C2 | TRA-20 | AC: numbers in docs/09 with the command that produced them; `rule.yaml` modes set. |

### P2 Account Behaviour (Vedanshu)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-17 | Rules engine core: folder loader, YAML schema, Jinja parameter rendering, DuckDB execution, `run --day`, run manifest | 5 | C1 | TRA-2 | Context: every slice depends on this; it ships against the fixture Parquet first. Scope: `screener/engine.py`, `screener/cli.py run`, `run` table. AC: `screener run --day` executes every `live` and `shadow` rule folder and writes hits with rule-version IDs; adding a new folder needs no code change (test adds `r99_tmp`). Label `contract`. |
| TRA-18 | Consolidation and scoring: hits → one alert per customer-day; priority score; CTR routing | 3 | C1 | TRA-17 | AC: two hits → one alert with both attached; cascade on close covered by a test; score formula in C8 with a unit test. |
| TRA-19 | Backtest: `screener backtest --rule --version --from --to` and the backtest page (counts per version, delta) | 3 | C2 | TRA-17, TRA-30 | AC: backtest of R4 at 180/120/365 days over May–Aug produces a table and a chart on the page; results stored with the proposed rule version so maker-checker can see them. |
| TRA-21 | R4 dormant reactivation rule, fixtures (179 vs 180 days), injector | 3 | C1 | TRA-2 | AC: fixtures pass; on SAML-D reproduces ~3,730 events; ~15 injected cases recalled ≥0.9. |
| TRA-22 | R7 new-account burst rule, fixtures, injector | 3 | C1 | TRA-2 | AC: fixtures pass; measured volume and budget decision in docs/09. |
| TRA-23 | R8 ATM anomaly rule (count, value vs baseline, multi-state), fixtures, injector | 3 | C1 | TRA-2 | AC: fixtures pass; relies on `channel` and ATM location from the US layer (TRA-26). |
| TRA-24 | Customer page (account timeline, dormancy gaps, prior alerts) and evidence panels r04, r07, r08 | 3 | C2 | TRA-30 | AC: renders from the fixture run; screenshot in PR. |
| TRA-25 | `explain.py` for r04, r07, r08; measure R4, R7, R8 on SAML-D into docs/09 | 2 | C2 | TRA-20, TRA-40 | AC: numbers and modes recorded; stub-LLM test passes. |

### P3 Funds Movement (Abdul)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-20 | SAML-D adapter → canonical Parquet (cash orientation: depositor = sender, withdrawer = receiver; string account IDs; 1:1 USD) with reconciliation report | 3 | C1 | TRA-2 | AC: 9,504,852 rows in, row count and Σ amounts reconcile; `load_batch` row written; runtime under 3 minutes on the laptop. |
| TRA-26 | US layer: customers (label-blind 10% grouping), KYC tiers, open dates, branches, channels, P2P relabel, holidays; injector framework calling each rule's `inject.py`; `answer_key.json` | 5 | C1 | TRA-20, TRA-9 | AC: every assignment uses the seeded RNG and never reads labels (test asserts no label column is referenced); answer key lists every injected case with rule id; docs/04 describes each proxy. Label `contract`. |
| TRA-27 | Demo subsample (100k accounts, all labelled accounts kept) and Tide adapter (optional, R5 benchmark) | 2 | C2 | TRA-26 | AC: subsample Parquet reproducible from seed; Tide adapter runs R5 and reports the 22.5% / 66% benchmark. |
| TRA-28 | Evaluation harness: `screener evaluate` (precision, recall, lift per rule on labels + answer key, chronological split) and the evaluation page | 3 | C2 | TRA-17, TRA-26 | AC: writes `docs/09-evaluation.md` tables from a command; page shows per-rule volume vs budget with live/shadow badge. |
| TRA-29 | R5 rapid pass-through rule with baseline condition, fixtures (71 vs 73 hours), injector; tuning record | 5 | C1–C2 | TRA-2 | Context: Debasish's first pain point and the flood example. AC: as-written and tightened volumes both recorded; ships in shadow unless ≤50/month; tuning steps documented as the demo narrative. |
| TRA-32 | R10 round-dollar rule, fixtures, injector | 2 | C1 | TRA-2 | AC: ~10 injected cases recalled; natural volume ~0 recorded. |
| TRA-33 | R12 transfer splitting rule (pair-keyed and funnel variant with new-sender condition), fixtures, injector | 3 | C1 | TRA-2 | AC: variant (b) catches the 75 "Structuring" receivers at a volume under budget, or ships in shadow with the measurement recorded. |
| TRA-34 | Funds-flow view and evidence panels r05, r10, r12; `explain.py` for the three | 3 | C2 | TRA-30, TRA-40 | AC: in/out within window drawn as a small table and timeline; renders from the fixture run. |

### P4 Counterparty & Rails (Natalie)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-30 | Django app skeleton: project, `accounts` (three roles, login), `alerts` models mirroring the data model, migrations, queue page, alert detail shell including evidence partials by rule id, `/healthz`, Tailwind | 5 | C1 | TRA-1 | Context: every UI ticket depends on this; ship the shell against the fixture run first. AC: login as each role; queue sorted by score then age with aging badges; alert page includes `rules/<id>/evidence.html` for each hit; autoescaping test with a hostile memo. Label `contract`. |
| TRA-31 | Disposition state machine, reason codes, notes, four-eyes, SAR clock, suppression | 5 | C1–C2 | TRA-30, TRA-7 | AC: every transition in C3 tested, illegal ones rejected; analyst cannot self-approve; SAR status hidden from Analyst role; every change calls `audit.record()`. |
| TRA-35 | Admin console: rule versions with maker-checker, seasonal profiles, mode switch, red-flag catalogue; `django-simple-history` | 5 | C2 | TRA-30, TRA-17 | Context: Debasish's "change thresholds and add rules without recoding". AC: a proposed change needs a different BSA officer to approve; the backtest result (TRA-19) is visible on the proposal; approved versions take effect on the next run only. |
| TRA-36 | R6 high-risk jurisdiction rule with point-in-time lists, fixtures, injector | 3 | C1 | TRA-2, TRA-9 | AC: fixture with a Turkey wire in 2023 fires and the same wire dated 2026 does not; measured volume and budget decision recorded. |
| TRA-37 | R9 wire to new beneficiary rule, fixtures (90-day lookback edge), injector | 3 | C1 | TRA-2 | AC: fixtures pass; domestic-wire fixtures included; measured volume recorded. |
| TRA-38 | R11 P2P anomaly rule (value, count, baseline, small-account tightening), fixtures, injector | 3 | C1 | TRA-2 | AC: fixtures pass; rail disclosed as synthetic in docs/04; measured volume recorded. |
| TRA-39 | Counterparty/country panel and evidence panels r06, r09, r11; `explain.py` for the three | 3 | C2 | TRA-30, TRA-40 | AC: panel shows country tier in force on the transaction date with its source. |

### P5 Investigator Agent (Vedant, with one ticket per owner)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-40 | Agent harness: `LLMClient` interface (Anthropic SDK + deterministic stub), evidence-pack builder, redaction, prompt with citation format, `agent_draft` model, CLI `screener draft --alert` | 5 | C2 | TRA-18, TRA-7 | Context: the kickoff asked for an agentic harness on the bank's credentials; the thin slice must never decide. AC: stub works offline and in CI; real provider enabled only by env; memos are wrapped as quoted data; the draft never changes status; every call is audited with prompt hash and model. Label `contract`. |
| TRA-41 | Agent draft panel on the alert page with "Draft" button, editable output, citations linking to evidence items | 3 | C2–C3 | TRA-40, TRA-30 | AC: Analyst and Officer can draft; Auditor can read; the draft is stored and exported with the alert (TRA-8). |
| TRA-42 | Agent control set document: scope, redaction, logging, graduated autonomy, accuracy measurement plan | 2 | C3 | TRA-40 | AC: `docs/10-agent-controls.md` reviewed by all four; ties to SR 26-2's exclusion of agentic AI. |

### P6 Client & Docs (Vedant, sections by owner)

| Key | Title | Pts | Cycle | Owner | Description |
|---|---|---|---|---|---|
| TRA-43 | Move research into `docs/` (glossary, client brief, regulations, rules catalogue skeleton, data plan, architecture with ADR-001, vendors and cost, friction, sources); delete duplicate scope file | 3 | C1 | Vedant | AC: every file in F4 `docs/` exists with content from this plan; README links them. |
| TRA-44 | Rules catalogue sections for own rules (parameters, red-flag citations, measured numbers, caveats) | 1 each | C2 | each owner | AC: `docs/02-rules-catalogue.md` section per rule with the numbers from docs/09. |
| TRA-45 | Demo script v2 (hybrid: rules, tuning, four-eyes, audit export, agent draft) and rehearsal checklist | 2 | C3 | Vedant | AC: runs end to end on `make demo` in under 12 minutes. |
| TRA-46 | Leadership presentation outline for Coforge BFSI (early Jan 2027): business impact, cost of doing nothing, ROI model, architecture, roadmap, KPIs | 3 | C3 | Vedant | AC: outline reviewed by the team; no timeline estimates in client-facing text; every number tagged. |
| TRA-47 | Written follow-up questions to the client (60-minute citation, ISO 20022 reference, asset size and regulator, LLM platform, fraud split by rail) | 1 | C1 | Vedant | AC: sent by email with Adam copied; answers logged in README meeting notes. |

**Dependency shape:** TRA-1 and TRA-2 (day 0) unblock every rule ticket; TRA-17 unblocks consolidation, backtest, evaluation and the admin console; TRA-30 unblocks every UI ticket; TRA-20/26 unblock the measurements; TRA-40 unblocks the explain tools. Everything else runs in parallel. The critical path is TRA-1 → TRA-2 → TRA-17 → TRA-18 → TRA-30 → TRA-31, all of C1, so Vedant does TRA-1/2 on day 0 while Vedanshu starts TRA-17 against the contract draft and Natalie starts TRA-30 against the fixture Parquet.

**Points per owner (approx.):** Vedant 37 (platform-heavy, fewer rule points), Vedanshu 28, Abdul 29, Natalie 30. Cycle load C1 ≈ 60, C2 ≈ 50, C3 ≈ 15 plus tuning and polish.

## F4. Repository scaffold (created on approval; per-rule folders are the point)

```
transaction-alert-screener/
├── README.md  LICENSE  .gitignore  .gitattributes  .env.example  Makefile
├── pyproject.toml  uv.lock  .pre-commit-config.yaml  .python-version (3.13)
├── CODEOWNERS  .github/PULL_REQUEST_TEMPLATE.md  .github/dependabot.yml
├── .github/workflows/ci.yml  publish.yml
├── Dockerfile  docker-compose.yml  docker-compose.ci.yml  docker-compose.demo.yml  Caddyfile
├── docs/
│   ├── 00-glossary.md  01-client-brief.md  02-regulations.md  03-rules-catalogue.md
│   ├── 04-data-plan.md  05-architecture.md (contracts + ADR-001)  06-vendors-and-cost.md
│   ├── 07-friction-and-risks.md  08-client-questions.md  09-evaluation.md (generated tables)
│   ├── 10-agent-controls.md  11-demo-script.md  12-linear-workflow.md  sources.md
│   └── discovery-call.html  data-and-rules-scope.md
├── reports/  research_notes/  scripts/              (kept as the research record)
├── rules/
│   ├── _schema/rule.schema.json  red_flags.yaml
│   ├── r00_example/   rule.yaml  rule.sql  inject.py  explain.py  evidence.html  test_rule.py  README.md
│   ├── r01_ctr/ … r03_structuring_same_day/          (Vedant)
│   ├── r04_dormant/  r07_new_account_burst/  r08_atm_anomaly/   (Vedanshu)
│   ├── r05_pass_through/  r10_round_dollar/  r12_transfer_splitting/   (Abdul)
│   └── r06_high_risk_jurisdiction/  r09_new_beneficiary/  r11_p2p_anomaly/   (Natalie)
├── data/
│   ├── raw/ (gitignored)  parquet/ (gitignored)
│   ├── fixtures/fixture.parquet  boundary_cases.csv  hostile_memos.csv
│   ├── reference/country_risk.csv  holidays_us.csv  tran_code_map.csv (core code → BTC triplet)  branches_fdic.csv  fetch_lists.sh
│   │   ├── iso20022/ (ExternalCodeSets_XLSX.zip, BTC_Codification.xlsx, BTC description docx, camt.054.001.13.xsd — downloaded, checksummed)
│   │   ├── ofac/  un/  opensanctions/ (downloaded, gitignored)
│   └── answer_key.json (generated, committed for the fixture corpus only)
├── screener/
│   ├── schema.py (camt.054 entry profile)  btc.py (BankTransactionCode validation)  calendar.py  reference.py
│   ├── ingest.py  engine.py  consolidate.py  scoring.py  audit.py  evaluate.py  export_camt054.py (stretch)  cli.py
│   ├── adapters/{core_csv,saml_d,tide,fixtures}.py   (later: pacs008, nacha, iso8583, x937 — one per rail)
│   ├── us_layer/{customers,tiers,branches,channels,p2p,inject}.py
│   └── agent/{client.py,stub.py,evidence.py,redact.py,draft.py}
├── app/                                   Django project
│   ├── manage.py  config/{settings,urls,wsgi}.py
│   ├── accounts/  alerts/  rules_admin/  audit/  exports/  agent/  customers/  evaluation/
│   └── templates/ (base, queue, alert_detail includes rules/<id>/evidence.html)
└── tests/  conftest.py  test_contracts.py  test_business_day.py  test_consolidation.py
           test_state_machine.py  test_four_eyes.py  test_audit_append_only.py  test_memo_escaping.py
           integration/ (Postgres-marked)
```

## F5. Calendar (three weekly cycles from Wed Nov 11; adjust to the class deadline)

| Cycle | Goal | Exit criteria |
|---|---|---|
| **C1 (Nov 11–17)** | Foundations and every rule green on fixtures | TRA-1/2 merged day 0; CI with Docker smoke green; all 12 rule folders pass fixture tests; SAML-D Parquet and US layer loaded; app shell with login, queue and alert detail renders the fixture run |
| **C2 (Nov 18–24)** | Real data, UI integration, admin console, agent slice | Every rule measured on SAML-D with mode set; evidence panels for all 12; disposition, four-eyes, audit log and export; admin console with maker-checker and backtest; agent draft with stub and real provider behind env |
| **C3 (Nov 25–Dec 1)** | Tuning, hardening, demo and leadership outline | Over-budget rules tuned or documented as shadow; evaluation page; demo environment; demo script rehearsed; `v0.1.0` released to GHCR; leadership presentation outline |
| Dec–early Jan | Leadership presentation prep | Business-impact and ROI deck for Coforge BFSI |

## F6. Demo script v2 (hybrid, 12 minutes, "today" 2023-07-14)
1. Problem in Debasish's words; regulatory frame; the audit-rebuild question.
2. `screener load`: reconciliation report and the Quarantine page (rows set aside with a reason). `screener run --since`: the hourly incremental run adds to the queue without duplicating; 12 rules with live/shadow badges and the risk rating beside each alert.
3. Open a pass-through alert (Debasish's pain point 1): funds-flow view, rule version, parameters, matched transactions, red-flag citation.
4. Press Draft: the agent's "why flagged" and narrative starter with citations; edit it; show it is stored and logged, not acted on.
5. Close a different alert with a reason; the audit log entry appears.
6. Escalate as Analyst; approve as a different BSA Officer; show the self-approval block and the SAR clock.
7. Admin console: propose dormant 180 → 120 days with a reason; backtest delta appears; a second officer approves; next run uses it.
8. R5 in shadow: as-written flood vs tuned volume; the decision rule.
9. Export the audit trail for July and the one-page summary for a single account (every flag it ever had: date, rule, amount, decision); open the CSV.
10. Evaluation page: volume vs budget, precision, recall, lift per rule. Close with cost, friction, roadmap (streaming lane, screening, full agentic triage in a 90-day shadow pilot).

## F7. Verification
- CI green on `main`: lint, unit, integration, rules, docker smoke, trivy.
- Every rule folder passes fixture tests; every injected typology recalled ≥0.9; R2 reproduces 90% / 57%.
- `make demo` on a clean machine reaches the populated queue; demo script runs end to end.
- Audit log proven append-only in an integration test; hostile memo renders escaped; agent stub never changes status.
- Linear: every ticket above exists with assignee, project, labels, estimate, cycle and blocked-by relations; the four "My cycle" views show roughly equal points; `In Review` status exists; template is default.
- Docs: every regulatory statement links to a primary source; every price tagged; FATF dates eyeballed; no timeline estimates in client-facing docs.

## F8. What happens on approval (in this order; this is the whole remaining scope of this session)
1. **Linear.** Through the connector: add the `In Review` status; create the label groups and labels; create the seven projects with descriptions and milestones; create the issue template as a team document; create the 48 tickets (TRA-1 … TRA-48, where TRA-44 is one ticket per owner) with full template bodies, assignees (Vedant = veddev404@gmail.com, Natalie = natalie.king@coforge.com, Vedanshu = vedanshu.patel@coforge.com, Abdul = abdul.2.shaik@coforge.com), labels, estimates and blocked-by relations; mark TRA-1 and TRA-43 Done once step 2 lands. Cycles and estimates must be switched on by hand in team settings first; I will say so and proceed with the rest, and cycle assignment is then a two-minute drag in Linear.
2. **Scaffold.** In the project folder: `git init`; the F4 tree with `pyproject.toml` (uv, Python 3.13 pin, dependency list), `.pre-commit-config.yaml`, `.gitignore`, `.gitattributes`, `.env.example`, `Makefile`, `CODEOWNERS`, PR template, `dependabot.yml`, `ci.yml` and `publish.yml`, `Dockerfile`, the three compose files and `Caddyfile`; `docs/` filled from this plan including `docs/PLAN.md` (this document), `docs/05-architecture.md` with the day-0 contract text and the field-to-XPath table, `docs/12-linear-workflow.md` with the working agreement and the exact `gh` commands for branch protection; `rules/_schema/rule.schema.json`, `rules/red_flags.yaml` seeded with the curated red flags, and `rules/r00_example/` with annotated placeholder `rule.yaml`, `rule.sql`, `inject.py`, `explain.py`, `evidence.html`, `test_rule.py`, `README.md`; the twelve empty rule folders each containing only a `README.md` naming the owner, the ticket and the contract; `data/reference/fetch_lists.sh` and `data/reference/README.md` with every D7 URL; `screener/` and `app/` as packages containing only `__init__.py` and a `README.md` pointing at TRA-2 and TRA-30; `tests/conftest.py` and an empty `tests/README.md`. No rule logic, no engine, no Django project. First commit; delete the duplicate `reports/data-and-rules-scope.md`. GitHub remote creation and branch protection run only if `gh auth status` succeeds; otherwise the commands are left in `docs/12-linear-workflow.md`.
3. **Hand-over.** The breakdown email draft for Adam with the ownership table and ticket keys, and a one-paragraph "start here" note per owner in `README.md`. Then this session ends; everything else happens in the owners' sessions.

## F9. Caveats
- The kickoff memory is two days old; if the Nov 11 walkthrough already happened, C1 shifts by the days used and the demo script is for the next client touchpoint.
- Linear cycles were not enabled when checked; the API cannot enable them, so cycle assignments in the tickets wait on that one setting.
- Branch, ATM, P2P and multi-account assignments are synthetic and label-blind; SAML-D is UK-centric data read as USD; rule parameters are conventions; vendor prices are estimates; FATF historical dates need a browser check.
- Standards research caveats: the Swift MT101 end date is reported both as Nov 2026 and as "delayed indefinitely" (swift.com blocks fetch); the exact FedNow message inventory rests on secondary sources; the newest BankTransactionCode codification spreadsheet found is March 2024, while the Nov 2025 narrative agrees with it; FFIEC Appendix F wording comes from secondary sources. Kaggle's download of SAML-D requires a free account, which the team already used.

# PART G — CLIENT REPLY OF NOV 11 (DEBASISH) RECONCILED WITH THE PLAN

Debasish answered our nine written questions on 2026-11-11. He asked us to document assumptions and reasoning where he could not be precise. This part records what his answers confirm, what they change, and the exact edits to make in the repo and in Linear. The scaffold session applies these edits; build work stays with the owners.

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

## G2. Coverage: already in the plan, no change
Flag-only and human decision (Part C, every rule ticket, agent controls A1); audit log and export as the core deliverable (TRA-11, TRA-12); admin console without a programmer (TRA-39); canonical schema plus one adapter per layout and the tran-code map (D6, TRA-6, TRA-24); risk rating displayed next to the flag; no crypto; 60-minute threshold treated as a question.

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

## G4. What this does not change
The canonical schema and contracts (the client's "plan a mapping step" is exactly D6); the per-rule folder layout; the Django choice; the four-slice ownership; the agent thin slice (he did not mention it; the kickoff asked for it; it stays, phase 0, draft only).

## G6. Every Linear ticket, what changes (applied through the connector; descriptions get a "Client reply 2026-11-11" block, priorities and modes as listed)

| Ticket | Owner | Change |
|---|---|---|
| TRA-5 scaffold | Vedant | Status note only: hourly cron and quarantine table added to the scaffold. |
| TRA-6 day-0 contracts | Vedant | Add `rejected_entry` table (load_batch_id, source, raw_row JSON, reason) to the schema; hit uniqueness key (rule_version_id, customer_id, business_day, group_key) so hourly reruns upsert (group_key added in the PR #7 review so two accounts of one customer keep separate hits); `tier_multipliers` default 1.0/1.0/1.0 in the rule schema; fixture Parquet gains a few rows that fail validation to exercise quarantine. |
| TRA-7 ci.yml | Vedant | No change. |
| TRA-8 Docker/compose | Vedant | `docker/crontab`: hourly `screener run --since last` plus nightly `screener run --day yesterday --reconcile`; AC adds "hourly run is idempotent on a second pass". |
| TRA-9 CI docker job | Vedant | Smoke sequence adds `screener run --since` after the day run and asserts no duplicate alerts. |
| TRA-10 publish | Vedant | No change. |
| TRA-11 audit log | Vedant | No change. |
| TRA-12 audit export | Vedant | Add `--account` filter; add printable **one-page account summary** (every flag the account ever had: date, rule, version, amount, decision, actor); AC: "for any account, every flag ever, CSV plus one page". |
| TRA-13 reference data | Vedant | No change (country risk still needed for outbound wires). |
| TRA-14 demo environment | Vedant | Demo subsample sized to ~10k rows/day (client: "tens of thousands, tops"); demo shows one hourly incremental run. |
| TRA-53 camt.054 export | Vedant | No change (stretch). |
| **TRA-58 (new)** field-requirements sheet and feed adapters | Vedant, P0, 2 pts, M0 | `docs/14-field-requirements.md`: minimum fields from the core export and the wire feed mapped to the canonical schema, with "required / derivable / nice-to-have"; `screener/adapters/core_csv.py` and `wire_feed.py` skeletons that raise with the field list; sent to Debasish for ops and the vendors. |
| TRA-15 R01 CTR | Vedant | Note: a same-day split that exceeds $10,000 is both a CTR candidate and an R03 hit by design; no logic change. Priority Urgent. |
| TRA-16 R02 | Vedant | **v1 = client rule: any single cash deposit in [$9,000, $10,000]** (`params.near_limit_low 9000, near_limit_high 10000`). Variants (a) and (b) become v2, enabled only after the backtest delta is shown to the client. Priority Urgent. |
| TRA-17 R03 | Vedant | **v1 = client rule: one customer, ≥2 cash deposits each ≤ $10,000 across all accounts, day total > $10,000, one hit per customer per business day.** Branch/channel condition becomes v2. Priority Urgent. |
| TRA-18 panels r01–r03 | Vedant | R03 panel lists every account of the customer that contributed. |
| TRA-19 explain r01–r03 | Vedant | No change. |
| TRA-20 measure R01–R03 | Vedant | Measure v1 and v2 for R02 and R03 and record the delta table. |
| TRA-21 rules engine | Vedanshu | Add `run --since <timestamp>` (incremental: new entries plus re-evaluation of every customer-day they touch) and `--reconcile` (full day); upsert hits by the uniqueness key; manifest records the mode. Nightly-only wording removed. |
| TRA-22 consolidation | Vedanshu | Upsert: a new hit on an existing open alert attaches to it; on a closed customer-day alert it creates an `alert_event` "new hit after close" and reopens to NEW (audited). Tier factor default 1.0. |
| TRA-23 backtest | Vedanshu | AC adds: compare two versions side by side (the v1 client definitions vs our v2 variants). |
| TRA-25 R04 | Vedanshu | **v1 = client rule: idle ≥180 days on customer-initiated entries (interest and fees excluded; any deposit resets), then outbound ≥ $2,000 within 7 days.** $5,000 in-or-out and 10× become v2. Priority Urgent. |
| TRA-26 R07 | Vedanshu | Priority High (ACH-dependent); AC adds "client walkthrough of the 48h window before live". |
| TRA-27 R08 | Vedanshu | Priority High; note cash withdrawals come from the core export (wires and cash first). |
| TRA-28 customer page | Vedanshu | Add an **account history tab**: every flag per account with date, rule, amount, decision (the auditor's view), reusing the export query. |
| TRA-29 explain + measure | Vedanshu | No change. |
| TRA-24 SAML-D adapter | Abdul | Write `rejected_entry` rows with reasons instead of counting rejects; AC: "no row is dropped silently". |
| TRA-30 US layer | Abdul | Remove sanctions/PEP-based tiering (KYC is the core's job); tier stays a seeded synthetic field shown next to the flag; P2P relabel kept and marked as an assumption pending a real export sample. |
| TRA-31 subsample + Tide | Abdul | Subsample target ≈ 300k accounts so daily rows ≈ 10k (documented assumption); alert budgets scale with it. |
| TRA-33 R05 | Abdul | Priority High (ACH next); shadow; AC adds "client walkthrough of the 72h window before live". |
| TRA-36 R10 | Abdul | Priority High. |
| TRA-37 R12 | Abdul | Priority High. |
| TRA-38 funds-flow panels | Abdul | No change. |
| TRA-40 evaluation | Abdul | Output a v1-vs-v2 comparison for rules that have both. |
| TRA-34 Django skeleton | Natalie | Queue and alert header show the risk rating; add a Quarantine page (rejected rows with reasons) and a Loads page (reconciliation report per batch). |
| TRA-35 state machine | Natalie | No change. |
| TRA-39 admin console | Natalie | Tier multipliers editable, default 1.0; otherwise no change. |
| TRA-41 R06 | Natalie | Scope v1 to **outbound** wires abroad (`PMNT/ICDT/XBCT`); inbound cross-border weight lowered; Priority Urgent. |
| TRA-42 R09 | Natalie | Priority Urgent (wires first); no logic change. |
| TRA-43 R11 | Natalie | Priority Medium; mode **shadow**; description notes the rail may be absent from the export and that the demo rail is synthetic. |
| TRA-44 counterparty panels | Natalie | No change. |
| TRA-45/46/47 agent | Vedant | No change. |
| TRA-48 docs | Vedant | Done; reopened only to add docs/14 and the meeting-notes entry (or folded into TRA-52). |
| TRA-49 and TRA-54–57 catalogue sections | all | Each section states the client's v1 definition verbatim, our v2 variant, and the measured delta. |
| TRA-50 demo script | Vedant | Steps added: hourly incremental run, quarantine page, per-account one-page export; R11 shown only as shadow. |
| TRA-51 leadership outline | Vedant | Lead with "90 analyst-minutes a day and an audit trail you can hand to an examiner"; fraud-loss figures as context; streaming lane and digital assets moved to "aspirational". |
| TRA-52 client follow-ups | Vedant | Log the nine answers; new follow-ups: confirm rule priority vs kickoff pain points; whether P2P appears in the export; sample layouts of the two feeds (or the field sheet filled in); screening vendor and KYC refresh cycle for the deck only. |

## G7. Every scaffold file that changes

| File | Edit |
|---|---|
| `docs/PLAN.md` | This Part G appended; B2 table rows for R02, R03, R04, R06, R11 updated with v1 client definitions, v2 variants, priorities and modes; D3 drops PEP tiering and states the subsample assumption; E3 data flow says "hourly incremental run plus nightly reconciliation"; F6 demo steps updated. |
| `docs/03-rules-catalogue.md` | Regenerated from the updated B2; a "Version 1 (client) vs version 2 (ours)" column. |
| `docs/04-data-plan.md` | D3 edits; quarantine described; subsample size assumption. |
| `docs/05-architecture.md` | Data model gains `rejected_entry`; hit uniqueness key and upsert semantics added to the hit → alert contract; run modes `--day`, `--since`, `--reconcile`. |
| `docs/08-client-questions.md` | Q1, Q7, Q10 marked answered with the reply text; new follow-ups F1–F4 with defaults. |
| `docs/11-demo-script.md` | Steps for hourly run, quarantine, per-account export; R11 as shadow. |
| `docs/12-linear-workflow.md` | Ticket table regenerated with new priorities, TRA-58 added. |
| `docs/14-field-requirements.md` | New: field sheet for core export and wire feed. |
| `README.md` | Meeting notes: "2026-11-11 written reply" entry with the nine answers condensed; ownership table unchanged; start-here notes point to v1 definitions. |
| `rules/r02_structuring_multi_day/README.md`, `rules/r03_structuring_same_day/README.md`, `rules/r04_dormant_reactivation/README.md` | v1 client definition quoted, v2 variant described, walkthrough gate where time-based. |
| `rules/r06_high_risk_jurisdiction/README.md`, `rules/r11_p2p_anomaly/README.md` | Outbound-only scope; shadow and rail-assumption note. |
| `rules/r00_example/rule.yaml` | `tier_multipliers: { low: 1.0, medium: 1.0, high: 1.0 }`. |
| `rules/_schema/rule.schema.json` | Description of `tier_multipliers` says default 1.0; optional `client_definition: string` field to quote the client's wording. |
| `docker/crontab` | Hourly incremental line plus nightly reconciliation line. |
| `data/reference/tran_code_map.csv` | Placeholder rows for `core_csv` and `wire_feed` sources marked "to be filled from the vendor layouts". |
| `screener/adapters/README.md` (new) | Lists saml_d, tide, fixtures, core_csv, wire_feed and the field sheet. |
| `tests/test_contracts.py` | Accepts the optional `client_definition` field; asserts default multipliers are 1.0 in `r00_example`. |

## G5. Verification for this part
- `rules/r02_*`, `r03_*`, `r04_*` READMEs and docs/03 show the client's version-1 definitions with the quoted thresholds and the version-2 variants marked "after backtest and client walkthrough".
- Linear: priorities and descriptions updated on the tickets named above; one new ticket for the field-requirements sheet and wire-feed adapter; TRA-43 marked shadow in its description.
- docs/08 and README record the reply and the four open follow-ups.
- Nothing in the repo contradicts the reply (grep for "nightly" in docs resolves to "hourly incremental plus nightly reconciliation").

---

## Sources
1. 31 CFR 1010.311 — https://www.law.cornell.edu/cfr/text/31/1010.311
2. 31 CFR 1010.313 — https://www.law.cornell.edu/cfr/text/31/1010.313
3. FinCEN CTR guidance — https://www.fincen.gov/resources/statutes-regulations/administrative-rulings/currency-transaction-reporting-completing-ctr
4. 31 CFR 1010.306 — https://www.law.cornell.edu/cfr/text/31/1010.306
6. 31 USC 5324 — https://www.govinfo.gov/content/pkg/USCODE-2022-title31/html/USCODE-2022-title31-subtitleIV-chap53-subchapII-sec5324.htm
7. 31 CFR 1010.100 — https://www.law.cornell.edu/cfr/text/31/1010.100
8. Davis Polk on Oct 2025 SAR FAQs — https://www.davispolk.com/insights/client-update/fincen-and-banking-agencies-release-updated-sar-guidance
11. 12 CFR 21.11 — https://www.law.cornell.edu/cfr/text/12/21.11
12. 31 CFR 1020.320 — https://www.law.cornell.edu/cfr/text/31/1020.320
15. FIN-2012-A002 — https://www.fincen.gov/sites/default/files/shared/FIN-2012-A002.pdf
16. 2026 Joint Statement on SAR Confidentiality — https://www.fincen.gov/system/files/2026-09/Joint-Statement-on-SAR-Confidentiality.pdf
17. 31 CFR 1020.210 — https://www.law.cornell.edu/cfr/text/31/1020.210
18. FFIEC exam procedures — https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/04_ep
20. Fed SR 26-2 — https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm
21. Orrick on 2026 MRM overhaul — https://www.orrick.com/en/Insights/2026/04/Agencies-Overhaul-Model-Risk-Management-Guidance-for-Banks-Heres-What-Changed
24. Federal Register AML/CFT Program NPRM Apr 2026 — https://www.federalregister.gov/documents/2026/04/10/2026-07033/anti-money-laundering-and-countering-the-financing-of-terrorism-programs
25. Unit21 NPRM FAQ — https://www.unit21.ai/blog/fincen-proposed-rule-2026-faqs-what-compliance-teams-need-to-know
26. McGuireWoods on STREAMLINE Act — https://blogs.mcguirewoods.com/2025/10/reducing-bsa-compliance-obligations-a-look-at-the-senates-streamline-act/
27. BDO 2026 AML/CFT tracker — https://www.bdo.com/insights/advisory/2026-u-s-aml-cft-regulatory-developments-tracker
28. 31 CFR 1010.430 — https://www.law.cornell.edu/cfr/text/31/1010.430
30. Blue Ridge Bank consent order — https://www.sec.gov/Archives/edgar/data/842717/000119312524015560/d870968dex101.htm
31. FinCEN TD Bank — https://www.fincen.gov/news/news-releases/fincen-assesses-record-13-billion-penalty-against-td-bank
32. OCC 2024-140 — https://occ.gov/news-issuances/news-releases/2024/nr-occ-2024-140.html
33. OCC 2026-89 — https://www.occ.gov/news-issuances/news-releases/2026/nr-occ-2026-89.html
34. NYDFS Block — https://www.dfs.ny.gov/system/files/documents/2025/04/ea20250410-block.pdf
35. USAA — https://jdsupra.com/legalnews/fincen-settles-with-usaa-federal-5373679
36. Shinhan — https://www.learnsignal.com/blog/shinhan-bank-america-fincen-15-million-penalty-transaction-monitoring-backlog-late-sars-guide/
37. Abrigo on U.S. Bank — https://www.abrigo.com/?p=3413
38. OCC Apr 2026 order commentary — https://www.financialservicesperspectives.com/2026/06/the-occs-recent-consent-order-is-a-warning-for-community-banks-in-the-fintech-partnership-space/
39. Flagright false positives — https://flagright.com/understanding-false-positives-in-transaction-monitoring
40. NICE Actimize report — https://www.niceactimize.com/Documents/aml_ai_in_aml_insights_report.pdf
42. Venturesathi — https://venturesathi.com/blogs/customer-experience/aml-alert-backlog-community-banks/
43. Facctum — https://facctum.com/blog/aml-false-positive-report
44. ABA on FinCEN FY2024 — https://bankingjournal.aba.com/2025/06/fincen-releases-figures-on-bsa-filings/
45. Oracle FCCM Alert Management — https://docs.oracle.com/cd/E91253_01/PDF/8.0.4.0.0/Alert%20Management%20User%20Guide_bd_8.0.4_1ed.pdf
46. NICE Actimize SAM — https://resources.niceactimize.com/wp-content/uploads/2022/04/nice_actimize_sam_brochure_2022.pdf
47. Unit21 entity-centred — https://www.unit21.ai/blog/solving-transaction-monitoring-challenges-with-entity-centered-investigations
51. SAML-D — https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml ; paper https://eprints.bournemouth.ac.uk/40982/
52. Tide — https://arxiv.org/html/2603.01863v1 ; https://zenodo.org/records/18804069 ; https://zenodo.org/records/20591329
58. OFAC SDN — https://sanctionslist.ofac.treas.gov/Home/static/sdn.html
59. OFAC Consolidated — https://sanctionslist.ofac.treas.gov/Home/static/consolidated.html
61. FATF lists — https://www.fatf-gafi.org/en/countries/black-and-grey-lists.html
64. OpenSanctions — https://www.opensanctions.org/docs/bulk/ ; https://www.opensanctions.org/docs/commercial/exemption/
71. Nasdaq–Verafin deck — https://nasdaq.com/docs/2020/11/19/Nasdaq_to_Acquire_Verafin_Investor_Presentation.pdf
72. Verafin release — https://verafin.com/news/nasdaq-to-acquire-verafin-creating-a-global-leader-in-the-fight-against-financial-crime
73. MANTL Verafin guide — https://mantl.zendesk.com/hc/en-us/articles/40281700714779-Verafin-Integration
79. LexisNexis 2024 — https://risk.lexisnexis.com/about-us/press-room/press-release/20240221-true-cost-of-compliance-us-ca
85. Anthropic pricing — https://platform.claude.com/docs/en/about-claude/pricing
86. JH Data Hub — https://knowledge.banno.com/data-reporting/data-hub/data-sets/
87. KC Fed core providers — https://www.kansascityfed.org/research/payments-system-research-briefings/market-structure-of-core-banking-services-providers/
88. qservicesit — https://www.qservicesit.com/guides/compliance-monitoring-in-community-banks
89. OCC 2023-17 — https://occ.treas.gov/news-issuances/bulletins/2023/bulletin-2023-17.html
91. Feedzai survey — https://www.feedzai.com/aml-compliance-competitive-advantage-ai/
95. Fedwire ISO 20022 MyStandards FAQ — https://www.frbservices.org/resources/financial-services/wires/faq/iso-20022/format-technical-documentation-mystandards ; implementation center https://www.frbservices.org/resources/financial-services/wires/fedwire-funds-service-iso-20022-implementation-center/
96. CHIPS ISO 20022 migration — https://theclearinghouse.org/payment-systems/Articles/2024/04/CHIPS_Network_Migrates_ISO_20022_04-10-2024
97. RTP technical documentation — https://www.theclearinghouse.org/payment-systems/rtp/technical-documentation ; FedNow ISO 20022 — https://www.frbservices.org/financial-services/fednow-service/iso-20022-why-does-it-matter
98. ISO 20022 coexistence end — https://www.aciworldwide.com/blog/the-end-of-coexistence-is-near-banks-take-an-existential-leap-towards-iso-20022 ; https://www.redcompasslabs.com/insights/what-now-iso-20022-deadlines-in-2026-onwards/
99. Nacha ACH developer guide — https://achdevguide.nacha.org/ach-file-details ; rules https://www.nacha.org/rules
100. ISO 20022 for cards — https://merchantadvisorygroup.org/news/mag-insights/article/2024/06/12/iso-20022-a-new-era-of-card-processing
101. X9.100-187 structure (moov-io) — https://moov-io.github.io/imagecashletter/file-structure ; X9 free standards https://x9.org/standards/free-standards/
102. Early Warning developer portal — https://developer.earlywarning.com/
103. HSBC BAI2 ↔ ISO transaction codes — https://develop.hsbc.com/sites/default/files/hsbc_pdf/HSBC%20SWIFT%20BAI2%20and%20ISO%20Transaction%20Codes.pdf
104. ISO 20022 external code sets (2Q2026) — https://www.iso20022.org/sites/default/files/media/file/ExternalCodeSets_XLSX.zip
105. BankTransactionCode description v8.0 Nov 2025 — https://www.iso20022.org/sites/default/files/media/file/BTC_ExternalCodeListDescription_Nov2025.docx
106. BankTransactionCode codification Mar 2024 — https://www.iso20022.org/sites/default/files/media/file/BTC_Codification_21March2024.xlsx ; camt.054.001.13 XSD https://www.iso20022.org/sites/default/files/documents/messages/camt/schemas/camt.054.001.13.xsd
107. Nacha ISO 20022 camt.053 mapping guide — https://www.nacha.org/system/files/2023-08/NACHA_ISO20022_Guide_camt.053_returns%2008-09-23.pdf
108. ING codification annex — https://assets.ing.com/m/3235595966a614f9/original/Codification-Annex-ING-update-2026-03-02.pdf
109. Tazama TMS API — https://raw.githubusercontent.com/tazama-lf/docs/dev/Product/transaction-monitoring-service-api.md ; Mojaloop ISO 20022 https://docs.mojaloop.io/product/features/iso20022.html
110. BIAN service landscape — https://bian.org/servicelandscape-10-0-0/views/view_51974.html ; FIBO https://edmcouncil.org/frameworks/fibo/
111. FinCEN CTR XML user guide v1.8 — https://bsaefiling.fincen.gov/docs/XMLUserGuide_FinCENCTR.pdf
112. FinCEN SAR XML user guide v1.6 — https://bsaefiling.fincen.gov/docs/XMLUserGuide_FinCENSAR.pdf ; base XSD index https://www.fincen.gov/base
113. FDIC Summary of Deposits API — https://api.fdic.gov/banks/sod ; variable definitions https://api.fdic.gov/banks/docs/sod_variables_definitions.csv
114. SynthAML (figshare) — https://api.figshare.com/v2/collections/6504421/articles
Discovery brief and backing research (Nov 5–6): https://claude.ai/artifact/MZHvnkQCg3GTBm2D5oju8h and https://claude.ai/artifact/6moN2xg54PbquShTB2D6A1. Full intermediate sources are in `reports/` and will be copied into `docs/sources.md`.
