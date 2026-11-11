<!-- Generated from docs/PLAN.md on 2026-11-11 (client reply applied). Edit PLAN.md for research changes; edit this file for working detail. -->

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
