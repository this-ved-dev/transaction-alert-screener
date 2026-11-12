<!-- Generated from docs/PLAN.md on 2026-11-11 (client reply applied). Edit PLAN.md for research changes; edit this file for working detail. -->

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

## Canonical entry schema (day-0 contract, TRA-6)

Source of truth: `screener/schema.py` (`ENTRY`, a pyarrow schema). One row per booked entry, stored as Parquet. The 32 columns implement the 26 rows of the D6 table; row 21 (risk tier, KYC status, PEP flag) lives on `customer`, never on the entry. `TxDtls` below is `Ntry/NtryDtls/TxDtls`; paths are relative to `Ntfctn` in camt.054.001.13. Req = `validate()` rejects the row when it is null.

| # | Column | Type | Req | camt.054 origin | Note |
|---|---|---|---|---|---|
| 1 | `entry_id` | string | ✓ | `Ntry/NtryRef` or `Ntry/AcctSvcrRef` | |
| 2 | `account_id` | string | ✓ | `Acct/Id/Othr/Id` | our customer's account |
| 3 | `amount` | decimal(18,2) | ✓ | `Ntry/Amt` | always > 0; direction is `credit_debit` |
| 4 | `currency` | string | ✓ | `Ntry/Amt/@Ccy` | ISO 4217 |
| 5 | `credit_debit` | string | ✓ | `Ntry/CdtDbtInd` | `CRDT` / `DBIT` |
| 6 | `is_reversal` | bool | ✓ | `Ntry/RvslInd` | |
| 7 | `status` | string | ✓ | `Ntry/Sts/Cd` | `BOOK` / `PDNG` |
| 8 | `booking_ts` | timestamp[us] | ✓ | `Ntry/BookgDt/DtTm` | bank local time without offset, so DuckDB gives the same answer on every host |
| 9 | `value_date` | date | ✓ | `Ntry/ValDt/Dt` | |
| 10 | `business_date` | date | ✓ | none; `TxDtls/RltdDts/Prtry{Tp=BUSD}` on export | weekend/holiday roll-forward; CTR aggregation key |
| 11–13 | `btc_domain`, `btc_family`, `btc_subfamily` | string | ✓ | `Ntry/BkTxCd/Domn/Cd`, `…/Domn/Fmly/Cd`, `…/Domn/Fmly/SubFmlyCd` | must be in the ISO codification (`screener/btc.py`) |
| 14 | `btc_proprietary` | string | | `Ntry/BkTxCd/Prtry/Cd` | `ZELLE`, ACH SEC code, BAI type code, ISO 8583 processing code |
| 15 | `channel` | string | ✓ | `Ntry/TechInptChanl` | `TELLER` `BRANCH` `NIGHT_DROP` `ATM` `POS` `ONLINE` `MOBILE` `WIRE_ROOM` `SYSTEM` (bank-originated fees, interest) |
| 16 | `instrument_refs` | struct{end_to_end_id, uetr, trace_no, cheque_no} | | `TxDtls/Refs/{EndToEndId, UETR, ClrSysRef, ChqNb}` | |
| 17–18 | `debtor`, `creditor` | struct{name, cif_id, country} | | `TxDtls/RltdPties/Dbtr\|Cdtr/Pty/{Nm, Id/…/Othr/Id (SchmeNm/Cd=CUST), CtryOfRes}` | counterparty country for R06 |
| 19–20 | `debtor_account`, `creditor_account` | string | | `TxDtls/RltdPties/DbtrAcct\|CdtrAcct/Id/Othr/Id` | |
| 21–22 | `debtor_agent`, `creditor_agent` | struct{routing, bic, country} | | `TxDtls/RltdAgts/DbtrAgt\|CdtrAgt/FinInstnId/{ClrSysMmbId/MmbId (USABA), BICFI, PstlAdr/Ctry}` | |
| 23 | `branch_id` | string | | `TxDtls/RltdAgts/…/BrnchId/Id` | CTR party type 34 |
| 24 | `conductor` | struct{name, cif_id, country} | | nearest `TxDtls/RltdPties/UltmtDbtr\|UltmtCdtr` or `InitgPty` | person at the counter, may differ from the owner |
| 25 | `cif_id` | string | ✓ | `Acct/Ownr/Id/…/Othr/Id` with `SchmeNm/Cd=CUST` | account owner; denormalised so rules group by customer without a join |
| 26 | `purpose` | string | | `TxDtls/Purp/Cd` | |
| 27 | `memo` | string | | `TxDtls/RmtInf/Ustrd`, `Ntry/AddtlNtryInf` | stored verbatim, rendered escaped, never parsed |
| 28 | `cash_detail` | list<struct{denomination, count}> | | `TxDtls/CshDpst/{NoteDnmtn, NbOfNotes}` | |
| 29 | `card_detail` | struct{masked_pan, mcc, terminal_id} | | `Ntry/CardTx` | |
| 30 | `source_message` | string | ✓ | none; `SplmtryData` on export | `fixture`, `saml_d`, `tide`, `pacs.008`, `nacha`, `iso8583`, `x937`, `zelle`, `teller` |
| 31 | `raw_ref` | string | | none; `SplmtryData` on export | pointer to the stored raw record |
| 32 | `typology_label` | string | | none | hidden: rules and injectors never read it |

**Validation and quarantine.** `schema.validate(table) -> (valid, rejected)` rejects a row when a required column is null, `amount <= 0`, the currency is not three capital letters, `credit_debit`/`status`/`channel` is outside its list, the BTC triplet is not in the codification, or `business_date` is before the booking date. The first failing check is the reason. The adapter writes each rejected item (`reason`, `raw_row` JSON) to `rejected_entry` with its `load_batch_id`, `source` and `created_at`; rules only ever see valid rows.

**Rule SQL inputs.** The engine provides the view `entries` (validated canonical rows) and `customers` (`cif_id`, `risk_tier`, …), and renders `rule.sql` with Jinja (`StrictUndefined`) using `asof` (the business day, ISO string) and `params.<key>` (from `rule.yaml`, after tier multipliers). Jinja braces inside SQL comments are rendered too, so comments must not contain them.

**Hit → alert contract.** `rule.sql` returns exactly these six columns, in this order, with these DuckDB types (`schema.HIT_COLUMNS`, enforced by `tests/test_contracts.py` on the fixture Parquet):

| Column | Type | Meaning |
|---|---|---|
| `customer_id` | VARCHAR | the `cif_id` the hit is reported on |
| `account_id` | VARCHAR | the account for account-keyed rules; `NULL::VARCHAR` otherwise |
| `business_day` | DATE | the business day the hit belongs to |
| `group_key` | VARCHAR, never NULL | the value of the rule's `key` in `rule.yaml`: `cif_id` for `customer`, `account_id` for `account`, the country code for `customer_country`, the beneficiary account for `customer_beneficiary`, and so on |
| `matched_txn_ids` | VARCHAR[] | `entry_id`s the analyst sees as evidence |
| `computed_values` | JSON | the numbers the evidence panel and `explain.py` quote (totals, counts, thresholds) |

A rule returns at most one row per (`customer_id`, `business_day`, `group_key`). When one `rule.sql` can produce several rows for the same key value (two directions, two variants, several conditions), pick one of two patterns:

- **Prefix** `group_key` to keep them as separate hits when each needs its own statistics: `CRDT:CIF00001` / `DBIT:CIF00001` for R01's directions, `a:CIF00001` / `b:CIF00001` for R02 v2's variants, `a:<sender>><receiver>` / `b:<receiver>` for R12.
- **Merge** them into one row and list what fired in `computed_values` (for example `conditions: ["count", "multi_state"]`) when they are facets of one finding: R08's and R11's conditions.

The engine adds `run_id` and `rule_version_id` and upserts into `hit` on `schema.HIT_IDENTITY` = (`rule_version_id`, `customer_id`, `business_day`, `group_key`); later hourly runs update `matched_txn_ids` and `computed_values` in place and never duplicate. `group_key` is in the identity because one rule can fire for two accounts, countries or beneficiaries of the same customer on the same day (R05, R06, R09): without it, a row-by-row upsert overwrites one account's evidence with the other's, and a bulk upsert (Postgres `ON CONFLICT`) fails on the repeated key. Both guarantees are tested (`test_rule_sql_returns_the_hit_columns`, `test_two_accounts_of_one_customer_survive_repeated_hourly_upserts`).

Consolidation and scoring read only these columns plus `weight` and `mode` from `rule.yaml`: `shadow` hits are stored and counted but never create alerts; all live hits for one customer and business day become one alert, each hit keeping its own evidence; the score counts each rule's weight once per alert however many hits it has.

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
1. Canonical Parquet schema (column names, types) and the committed fixture Parquet (§ Canonical entry schema above; `screener fixtures`).
2. **Rule contract:** `rules/<id>_<slug>/rule.yaml` (id, name, owner, version, mode, key, windows, params, weight, red_flag_ids, budget_per_month, description) and `rule.sql` returning `(customer_id, account_id, business_day, group_key, matched_txn_ids, computed_values)`; the engine globs the folders; a rule can be added without touching shared code.
3. **Evidence-panel contract:** `rules/<id>_<slug>/evidence.html`, a Django template partial receiving `hit` (with `computed_values`) and `txns`; the alert page includes one per hit. Owners build UI for their rules without editing the alert page.
4. **Injector contract:** `rules/<id>_<slug>/inject.py` exposing `inject(df, rng, n) -> (df, cases)`; the US layer calls each and writes `answer_key.json`.
5. **Hit → alert contract:** consolidation and scoring read only the six hit columns plus `rule.yaml` weight and mode.
6. **Agent tool contract:** `rules/<id>_<slug>/explain.py` exposing `evidence(hit, entries) -> list[EvidenceItem]`; the agent harness concatenates them.

## E3a. Rules engine (TRA-21)

`screener/engine.py` discovers `rules/r??_*/` folders that contain `rule.yaml`, validates each against `rules/_schema/rule.schema.json`, applies the medium-tier multiplier to monetary params (flat 1.0 by default), renders `rule.sql` with Jinja `StrictUndefined`, and executes in DuckDB over the canonical Parquet with views `entries` (no `typology_label`), `customers`, `country_risk` and `holidays`. Hits upsert on `schema.HIT_IDENTITY` = (`rule_version_id`, `customer_id`, `business_day`, `group_key`). Shadow rules record hits; consolidation (TRA-22) excludes them from alerts. `off` rules are validated but skipped by `screener run` (so `r00_example` stays off as the copy-me template); `run_fixtures()` / `fixture_run` includes `off` so per-rule tests still see r00 hits.

CLI: `screener run --day YYYY-MM-DD [--store sqlite|postgres]` for a full day; `screener run --since <timestamp|last>` for the hourly incremental (new entries → re-evaluate their business days expanded forward by the widest rule window so look-back rules stay correct; upserts are idempotent); `screener run --day … --reconcile` for the nightly full pass. Only `--since` advances the watermark; `--day` / `--reconcile` must not rewind it. The `run` manifest records mode, watermark, input file hashes, rule versions, hit/entry counts and duration. Business-day roll-forward lives in `screener/calendar.py` (weekend + `data/reference/holidays_us.csv`).

## E4. Interface decision record (ADR-001)
Django + HTMX + Tailwind. Reasons: the client asked for an admin console for thresholds and rules without recoding, which Django admin plus `django-simple-history` provides in a day; roles, audit and forms are the product; one language and one build system for four people. Alternatives considered: FastAPI + HTMX (1–2 days more plumbing), FastAPI + React (two build systems), Streamlit (no real roles). Revisit only if someone volunteers to own a React front end end-to-end.
