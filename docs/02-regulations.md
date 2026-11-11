<!-- Generated from docs/PLAN.md on 2026-11-11. Edit PLAN.md for research changes; edit this file for working detail. -->

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
