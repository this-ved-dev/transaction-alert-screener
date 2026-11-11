<!-- Generated from docs/PLAN.md on 2026-11-11 (client reply applied). Edit PLAN.md for research changes; edit this file for working detail. -->

# PART C — BUSINESS LOGIC

1. Store every hit; one alert per (customer, business day); disposition cascades to hits; per-rule statistics on hits.
2. CTR candidates are a separate list with a reconcile status.
3. Status machine `NEW → IN_REVIEW → PENDING_INFO → ESCALATED → CLOSED_NO_ACTION | SAR_RECOMMENDED → SAR_FILED`; reason codes on close (expected activity, documented business purpose, duplicate, false positive, other with text); `SAR_FILED` set only by BSA officer with the external filing ID; the tool never files, blocks, freezes or contacts.
4. Roles: Analyst, BSA Officer, Auditor (read-only, every view logged). Nobody else has access.
5. Four-eyes: `ESCALATED → SAR_RECOMMENDED` requires a BSA officer who is not the escalating analyst.
6. Thresholds: versioned rows edited in the **admin console** with maker-checker (an analyst or officer proposes with a reason; a different officer approves); applies to future runs; each hit stores its rule-version ID; `backtest` reports alert counts per rule per version. Rule modes: `live`, `shadow`, `off`. **Seasonal profiles**: a named parameter set with a date range (Nov–Jan) that overrides defaults, versioned the same way.
7. Suppression: one rule, one customer, ≤90 days, with reason; logged; no other auto-close.
8. Priority score = Σ rule weights × tier factor + 2 × prior alerts in 12 months; sorted by score then age; age badge at 20 days; SAR clock after escalation.
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
| `hit` | id, run_id, rule_version_id, customer_id, account_id, business_day, matched_txn_ids, computed_values JSON |
| `alert` | id, customer_id, business_day, score, status, assigned_to, risk_tier_at_fire, created_at |
| `alert_hit`, `alert_event`, `suppression`, `audit_log`, `user`, `ctr_candidate`, `load_batch`, `run` | as named; `hit` is unique on (rule_version_id, customer_id, business_day) so hourly reruns upsert |
| `rejected_entry` | id, load_batch_id, source, raw_row JSON, reason, created_at (client: bad rows are set aside with a reason, never dropped) |
| `agent_draft` | id, alert_id, model, prompt_hash, evidence_pack JSON, output, created_by, created_at |
| `country_risk` | country, tier, source, effective_from, effective_to |

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
2. **Rule contract:** `rules/<id>_<slug>/rule.yaml` (id, name, owner, version, mode, key, windows, params, weight, red_flag_ids, budget_per_month, description) and `rule.sql` returning `(customer_id, account_id, business_day, matched_txn_ids, computed_values)`; the engine globs the folders; a rule can be added without touching shared code.
3. **Evidence-panel contract:** `rules/<id>_<slug>/evidence.html`, a Django template partial receiving `hit` (with `computed_values`) and `txns`; the alert page includes one per hit. Owners build UI for their rules without editing the alert page.
4. **Injector contract:** `rules/<id>_<slug>/inject.py` exposing `inject(df, rng, n) -> (df, cases)`; the US layer calls each and writes `answer_key.json`.
5. **Hit → alert contract:** consolidation and scoring read only the five hit columns plus `rule.yaml` weight.
6. **Agent tool contract:** `rules/<id>_<slug>/explain.py` exposing `evidence(hit) -> list[EvidenceItem]`; the agent harness concatenates them.

## E4. Interface decision record (ADR-001)
Django + HTMX + Tailwind. Reasons: the client asked for an admin console for thresholds and rules without recoding, which Django admin plus `django-simple-history` provides in a day; roles, audit and forms are the product; one language and one build system for four people. Alternatives considered: FastAPI + HTMX (1–2 days more plumbing), FastAPI + React (two build systems), Streamlit (no real roles). Revisit only if someone volunteers to own a React front end end-to-end.
