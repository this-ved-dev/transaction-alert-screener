<!-- Client questions. Asked ones are ticked with the date; answers go into README.md § Meeting notes. Frame as options with our default in bold. -->
# Client questions

## Answered or asked on the 5 Nov discovery call
The 17 questions in [`discovery-call.html`](discovery-call.html) slide 6 (compliance, technology, business). Owners: Vedanshu (thresholds, one-alert-or-two), Abdul (dormant definition, core system, file fields, night-drop posting, sample export), Vedant (threshold approval, auditor requests, success in six months, analyst capacity), Natalie (SAR visibility, CTR list placement, where the tool runs, budget owner, noisy segments, customer friction).

## Written follow-ups after the kickoff (owner: Vedant; P1 answers shape the build, P2 shape the leadership deck)
| # | Question | Why we ask | Default if unknown | Priority | Addressee |
|---|---|---|---|---|---|
| Q1 | The "60-minute flag mandate": which rule, regulator or internal policy sets it? | We found no US rule; it decides whether a streaming lane is phase 1 or later | **Nightly batch first; sub-hour lane in a later phase** | P1 | Debasish |
| Q2 | "27,000 / 27,002": do you mean ISO 20022 (payments messaging) or ISO 27001/27002 (security)? | Decides whether the canonical schema or the security review is the ask | **ISO 20022 for data; 27001 controls documented** | P1 | Anurag |
| Q3 | Asset size and primary regulator (OCC, Fed, FDIC, state)? | Decides SR 26-2 applicability and exam expectations | **$1–5B, OCC-supervised** | P1 | Debasish |
| Q4 | Is the $30–40M fraud figure direct loss or fully loaded (labor, remediation)? | Avoids double counting in the ROI model | **Direct loss** | P1 | Debasish |
| Q5 | Fraud split by rail (ACH, wire, P2P, cash, ATM, card) over the last 12–18 months, and the rule ranking you offered | Sets rule budgets and demo emphasis | **Pass-through, new beneficiary, P2P first, per your ranking** | P1 | Debasish |
| Q6 | Which LLM platform does the bank already run (Bedrock, Azure OpenAI, other) and who owns its credentials? | The agent must run on your credentials | **Anthropic via the provider you name; stub until then** | P1 | Anurag |
| Q7 | Source systems and owners for each rail; is there any nightly export today, and in what layout? | Adapter order and the tran-code map | **One nightly CSV per rail; we map to ISO 20022 BankTransactionCode** | P1 | Anurag |
| Q8 | What is "detect in 24h" measured from: posting, alert creation, or analyst pickup? | Defines our time-to-flag KPI | **From posting** | P2 | Debasish |
| Q9 | Do the four analysts work AML and fraud alike, and what are peak-season volumes? | Capacity budget per rule | **250 alerts/month for two analysts** | P2 | Debasish |
| Q10 | Any crypto-kiosk operators, stablecoin exposure or tokenized-deposit plans? | Scope of the 24-month roadmap | **None today** | P2 | Debasish |
| Q11 | Which country-risk list do you follow: FATF only or an internal list? | R06 configuration | **FATF black/grey plus an internal tier** | P2 | Stacy |
| Q12 | When an auditor comes, what do they ask for first and in what format? | Audit export shape | **All alerts in a date range, CSV and printable** | P2 | Stacy |

Rule-ranking sheet for Debasish: the 12 rules with columns incidents (12–18 months), $ impact, rank, notes. Lives in the discovery brief appendix.

## Written reply received 2026-11-11 (Debasish)
| Q | Answer (condensed) | Consequence |
|---|---|---|
| Priority | Wires and cash deposits first (they feed the three core rules), ACH next, P2P last and possibly absent | Rule priorities P1/P2/P3 in docs/03; R11 in shadow |
| Geography / 60 minutes | US regional, domestic, some outbound wires abroad; the 60-minute threshold did not come from him; walk him through any time-based rule before it sticks | Q1 closed; R06 scoped to outbound; walkthrough gate on R05 and R07 |
| Thresholds | Near-limit $9,000–$10,000; same-day splitting ≥2 deposits ≤$10,000 adding past $10,000 across all accounts, one flag per customer per day; dormancy 180+ days then $2,000+ out; interest and fees do not reset, a deposit does | Version-1 definitions of R02, R03, R04 |
| Formats | Two layouts (core export, wire feed), probably not ISO 20022; plan a mapping step; tell us which fields | docs/14 field sheet; core_csv and wire_feed adapters (TRA-58) |
| Auditor | For any account, every flag ever (date, rule, amount, decision); CSV or Excel plus a printable one-page summary per account | TRA-12 account filter and one-page summary; TRA-28 account history tab |
| Operations | Manual, ~90 minutes a day, three patterns; flag only; bad rows set aside with a reason, never dropped; limits changeable without a programmer | `rejected_entry` quarantine; admin console; ROI anchor = 90 minutes a day |
| Crypto | None; do not build crypto handling | Q10 closed; roadmap item aspirational only |
| KYC | In the core under CIP; manual basic rating; do not re-verify; show the rating next to a flag | Tier multipliers default 1.0; sanctions/PEP tiering dropped; rating displayed |
| Throughput | Tens of thousands of rows a day, tops; one batch run every hour on incrementals | Hourly `--since` run, nightly `--reconcile`; demo subsample ~10k rows/day |

## Open follow-ups after the reply (owner Vedant, Adam copied)
| # | Question | Default if unknown |
|---|---|---|
| F1 | The kickoff named pass-through, new beneficiary and P2P as pain points; this reply names near-limit, same-day splitting and dormancy as the three core rules. Which order should the first release follow? | **This reply's order** |
| F2 | Does P2P (Zelle) activity appear in either feed, and how is it coded? | **Absent; R11 stays shadow** |
| F3 | Can you share the column layouts (or a 50-row anonymised sample) of the core export and the wire feed, or have ops fill `docs/14-field-requirements.md`? | **We build the adapters to the field sheet** |
| F4 | For the leadership deck only: screening vendor and KYC refresh cycle | **Left as "per bank policy"** |
