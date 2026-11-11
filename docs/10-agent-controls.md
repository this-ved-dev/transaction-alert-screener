<!-- Agent control set. Filled in by the agent-controls ticket (P5 M3). Reviewed by all four owners. -->
# Investigator agent: control set

**Why a separate control set.** SR 26-2 / OCC Bulletin 2026-13 (April 2026) exclude generative and agentic AI from model-risk scope, so the bank's model inventory will not govern the agent. The OCC's April 2026 consent order penalised a triage system that auto-closed alerts. The agent is therefore designed so that it cannot change an outcome, and these controls make that auditable.

## Scope (what the thin slice does)
For one alert: assemble an evidence pack from each rule's `explain.py`; redact names and account numbers to stable tokens; call the LLM configured by environment on the bank's credentials; return a four-sentence "why flagged" and a who/what/when/where/why narrative starter with citations to evidence items; store it as `agent_draft` with model, prompt hash and evidence pack; log the call. The analyst edits the draft. Nothing else.

## Controls
| # | Control | How it is enforced |
|---|---|---|
| A1 | The agent cannot change alert status, assignment, suppression or thresholds | No write path exists from `screener/agent/` to those tables; integration test asserts it |
| A2 | No customer identifiers reach the model | `redact.py` replaces names, account numbers, phone, email, addresses with tokens; unit test with fixture PII; US-only inference if the provider offers it |
| A3 | Free text is data | Memos are wrapped as quoted evidence, never placed in the instruction section; hostile-memo fixtures must not alter the output structure |
| A4 | Every call is audited | prompt hash, model, provider, token counts, evidence-pack hash, actor, timestamp |
| A5 | Deterministic in CI | `LLM_PROVIDER=stub` returns fixed text; CI never calls a real provider |
| A6 | Citations or nothing | Output sentences must cite evidence item ids; uncited sentences are shown greyed with a warning |
| A7 | Graduated autonomy | Phase 0: draft only (this build). Phase 1: suggested disposition shown, never applied, with measured agreement rate against analyst decisions. Phase 2 and beyond: only after the bank's own governance approves, with the measured accuracy in hand |
| A8 | Accuracy measurement | `screener evaluate --agent` compares drafts' suggested direction with final dispositions over the validation window; reported in `docs/09-evaluation.md` |
| A9 | Kill switch | `LLM_PROVIDER=off` hides the Draft button; no code change |
| A10 | Vendor independence | `LLMClient` interface; provider chosen by environment; no provider-specific prompt features |

## Open items for the bank
Which LLM platform and credentials (client question Q6); data-residency requirement; who approves moving from phase 0 to phase 1.
