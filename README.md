# Transaction Alert Screener

An anti-money-laundering alert screener for a regional bank's small compliance team: deterministic detection rules over every
transaction, one queue of alerts with a reason on every decision, an append-only audit trail an examiner can read, and a thin
investigator agent that drafts, cites and never decides. **Flag and report only.** The tool never blocks a payment, freezes an
account, files a report or contacts a customer.

Team: **Vedant Misra** (lead), **Abdul Malik Shaik**, **Vedanshu Daxesh Patel**, **Natalie King**. Client: Debasish Chanda (bank
leadership), Anurag Gupta (Coforge partner), Stacy (banking SME). Course project; all data is synthetic or public.

## Ground rules
1. **Synthetic data only.** No real customer, account or transaction data, ever. Public datasets are read locally and never committed (`.gitignore`, pre-commit 1 MB block).
2. **Flag and report only.** Humans decide. No auto-close, by rules or by the agent.
3. **Free text is data.** Memos are stored verbatim, rendered escaped, never parsed as instructions.

## Start here
1. Read [`docs/PLAN.md`](docs/PLAN.md) once, end to end. Glossary first if banking is new to you.
2. Open your Linear project and your first ticket (table below). Branch names come from Linear (`<you>/tra-NN-...`).
3. `make setup` → `make test`. Copy `rules/r00_example/` to your rule folder. Contracts: [`docs/05-architecture.md`](docs/05-architecture.md).

| Owner | Process (rules) | Platform component | Linear project | First ticket |
|---|---|---|---|---|
| Vedant | Cash & CTR (R01, R02, R03) | repo, CI, Docker, audit log, exports, reference data, agent harness | P0 Platform & Delivery · P1 Cash & CTR · P5 · P6 | Day-0 contracts (schema, fixtures) |
| Vedanshu | Account behaviour (R04, R07, R08) | rules engine core: loader, run, backtest, consolidation, scoring | P2 Account Behaviour | Rules engine core |
| Abdul | Funds movement (R05, R10, R12) | data: adapters, canonical Parquet, US layer, injection, evaluation | P3 Funds Movement | SAML-D adapter |
| Natalie | Counterparty & rails (R06, R09, R11) | Django app: roles, queue, alert detail, disposition, four-eyes, admin console | P4 Counterparty & Rails | Django app skeleton |

Each owner delivers for their rules: SQL + `rule.yaml`, fixtures and injector, tests, measured volume and precision on SAML-D,
the evidence panel the analyst sees, the agent `explain()` tool, and the rules-catalogue section.

## Repository map
| Path | What |
|---|---|
| `docs/` | the plan and its sections: glossary, client brief, regulations, rules catalogue, data plan, architecture and contracts, vendors and cost, friction, client questions, evaluation, agent controls, demo script, Linear workflow, sources |
| `rules/<id>_<slug>/` | one folder per rule: `rule.yaml`, `rule.sql`, `inject.py`, `explain.py`, `evidence.html`, `test_rule.py`; `rules/r00_example/` is the template; `rules/red_flags.yaml` the regulator citations |
| `screener/` | framework-independent core (schema, engine, adapters, US layer, audit, agent) |
| `app/` | Django 5 + HTMX application |
| `data/reference/` | hand-maintained reference tables and `fetch_lists.sh` for public lists; `data/fixtures/` the committed fixture corpus; `data/raw/` local datasets (gitignored) |
| `reports/`, `research_notes/`, `scripts/` | the dataset-selection research and DuckDB profiling that the rules are measured against |
| `.github/workflows/` | `ci.yml` (lint, unit, integration, rules, Docker build + compose smoke + trivy) and `publish.yml` (GHCR, releases) |

## Running
```bash
make setup          # uv env + pre-commit hooks
make test           # unit tests
make up             # app + scheduler + Postgres + Caddy (needs .env from .env.example)
make ci-smoke       # what CI's docker job does
```
Datasets: SAML-D (Kaggle, CC BY-NC-SA, needs a free account) and Tide HI (Zenodo, CC BY 4.0) go under `data/raw/`; see
[`docs/04-data-plan.md`](docs/04-data-plan.md) § D7 for every URL and licence. Reference lists: `data/reference/fetch_lists.sh`.

## Meeting notes
### 2026-11-05 — kickoff / discovery call (45 min)
Attendees: Debasish Chanda (bank leadership), Anurag Gupta (Coforge partner, joined late), our team. Deck: [`docs/discovery-call.html`](docs/discovery-call.html).
- Fraud losses about $30–40M a year; AML roughly 20% of incidents and 40% of dollar impact. Four offshore analysts cover all fraud; detection ~24h, resolution ~24h; Nov–Jan is peak season with contract analysts.
- No data warehouse; analysts work in Excel and VB scripts; data scattered across ACH, wire, P2P/Zelle, cash and ATM; branches in NJ and Manhattan.
- Ranked pain points: rapid pass-through; small transfers to new beneficiaries or jurisdictions; high-count P2P on small accounts. Debasish will rank our 12 rules by impact over the last 12–18 months.
- "Workflow automation is not intelligence; this stop gap does not work for me." Wants an agentic, policy-driven harness, an admin console to change thresholds and add rules without recoding, all running inside the bank on the bank's own LLM credentials.
- Claimed a "60-minute flag mandate" (no such US rule found; citation requested). Mentioned "27,000/27,002" (clarification requested; ISO 20022 vs ISO 27001). Future: stablecoins, ISO 20022, crypto; study Actimize and Hawk.
- Logistics: questions in writing; calls need 48 hours' notice; SME Stacy available; Coforge BFSI leadership presentation in about two months.
- Decisions: hybrid advisory (deterministic rules as the regulatory floor, in-bank investigator agent for triage and drafting, human decides every case). Written summary and discovery brief sent Nov 6.

### Follow-up questions sent in writing
See [`docs/08-client-questions.md`](docs/08-client-questions.md). Answers are logged here as they arrive.

## Licence
MIT for our code. Third-party data keeps its own licence; see `docs/04-data-plan.md` § D5 and D7.
