<!-- Generated from docs/PLAN.md on 2026-11-11. Edit PLAN.md for research changes; edit this file for working detail. -->

## E5. Git and CI hygiene

**Repository.** GitHub repo `transaction-alert-screener` (public, per the assignment's "public repository URL"). Default branch `main`, protected: pull request required, one approval from a CODEOWNER of the touched paths, all required checks green, linear history (squash merge), no force-push, conversation resolution required. `CODEOWNERS` maps `rules/r01_*`, `rules/r02_*`, `rules/r03_*`, `screener/audit*`, `.github/`, `Dockerfile`, `docker-compose*.yml` → Vedant; `rules/r04_*`, `r07_*`, `r08_*`, `screener/engine*`, `screener/consolidate*`, `screener/scoring*` → Vedanshu; `rules/r05_*`, `r10_*`, `r12_*`, `screener/adapters/`, `screener/us_layer/`, `screener/evaluate*` → Abdul; `rules/r06_*`, `r09_*`, `r11_*`, `app/` → Natalie; `docs/` → anyone, one approval.

**Branches and commits.** Branch per Linear issue, named by Linear's suggested format `vedant/tra-12-ctr-candidate-rule`, so Linear auto-links and moves the issue to In Progress on first push and to Done on merge. Conventional Commits (`feat(r02): add 30-day structuring variant`), PR title prefixed with the issue key (`TRA-16: …`). PRs under ~400 lines; one issue per PR. PR template: What / Why / How tested / Screenshots for UI / Checklist (tests added, docs updated, no data committed, rule.yaml version bumped if params changed). Draft PRs early.

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

**Docker.** Multi-stage `Dockerfile` (uv builder → slim runtime, non-root user, `HEALTHCHECK` on `/healthz`). `docker-compose.yml`: `app` (gunicorn), `scheduler` (runs `screener run` nightly via `supercronic`), `db` (Postgres 16 with a named volume and an init script that creates the restricted app role), `caddy` (TLS). `docker-compose.ci.yml` overrides: no caddy, app on `localhost:8000`, deterministic LLM stub, ephemeral volumes. `docker-compose.demo.yml`: preloads the demo subsample. `make up / make test / make demo` wrap the common commands.

**Environments.** `dev` (compose on a laptop, SQLite optional), `ci` (compose.ci), `demo` (compose.demo on one VM or a laptop for the client walkthrough), `bank` (compose behind the bank's proxy with their LLM credentials; documented, not provisioned by us).

---

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
| TRA-5 | Repo scaffold, uv project, pre-commit, PR template, CODEOWNERS | 3 | C1 day 0 | — | Context: nothing exists; four people start tomorrow. Scope: tree in F4; `pyproject.toml` with pinned 3.13; `.pre-commit-config.yaml` (ruff, large-file block 1 MB, gitleaks, hadolint); `.gitignore` for data; PR template; CODEOWNERS per F1; MIT licence; README skeleton with ownership table and meeting-notes section. AC: `uv sync` and `pre-commit run --all-files` pass on a clean clone; `git log` shows one initial commit; branch protection on `main` configured as in E5. Evidence: screenshot of branch-protection settings. |
| TRA-6 | Day-0 contracts: camt.054-shaped canonical entry schema, BankTransactionCode taxonomy, fixture Parquet, rule/evidence/injector/explain contracts | 5 | C1 day 0 | TRA-5 | Context: these contracts are what let four slices proceed in parallel, and the canonical record follows ISO 20022 camt.054 so the bank's real rails can be adapted later without touching rules (D6). Scope: `screener/schema.py` (pyarrow schema for the 26 fields in D6), `screener/btc.py` loading the ISO BankTransactionCode codification and validating triplets, `screener fixtures` generating a 2,000-row synthetic Parquet covering every triplet and channel we use, `docs/05-architecture.md` contract section with the field-to-XPath table, `tests/test_contracts.py` validating any `rules/*/rule.yaml` against a JSON schema, checking `rule.sql` returns the five hit columns on the fixture Parquet, and rejecting any entry whose triplet is not in the codification. AC: `rules/r00_example/` passes; fixture Parquet committed and under 1 MB; every fixture triplet validates. Label `contract`. |
| TRA-7 | GitHub Actions `ci.yml`: lint, unit, integration (Postgres service), rules | 3 | C1 | TRA-5 | Scope per E5 jobs 1–4, concurrency groups, SHA-pinned actions, coverage artifact. AC: a PR with a deliberate ruff error fails `lint`; a PR with a failing fixture test fails `rules`; green on `main`. |
| TRA-8 | Dockerfile, docker-compose (app, scheduler, db, caddy), compose.ci, compose.demo, Makefile | 5 | C1 | TRA-5 | Scope: multi-stage uv image, non-root, HEALTHCHECK; Postgres init script creating the restricted `app` role without UPDATE/DELETE on `audit_log`; supercronic scheduler; Caddyfile. AC: `make up` serves `/healthz` 200 locally; `docker compose run app screener --help` works; image under 400 MB. |
| TRA-9 | CI `docker` job: build with cache, compose up, healthz, fixture run, alert-count assertion, trivy | 3 | C1 | TRA-7, TRA-8 | Scope per E5 job 5–6. AC: the job fails if `/healthz` never returns 200 within 60s or if the fixture run yields zero alerts; trivy fails on critical CVEs; logs are uploaded on failure. |
| TRA-10 | `publish.yml`: push image to GHCR on main and tags; GitHub Release on `v*`; dependabot | 2 | C2 | TRA-9 | AC: `ghcr.io/<org>/transaction-alert-screener:main` exists after merge; `v0.1.0` tag creates a release with notes and `:latest`. |
| TRA-11 | Audit log module: append-only writer, hash chain, `audit.record()` helper, access logging middleware | 3 | C1 | TRA-6 | Context: C9 and the Blue Ridge checklist. Scope: `screener/audit.py`, Django model, middleware logging Auditor views and any SAR-status view. AC: integration test proves the app role cannot UPDATE/DELETE; chain verifies; every write path in the app calls `audit.record()` (grep test). |
| TRA-12 | Audit export: CSV + printable HTML for a date range or a customer, including rule versions in force and agent drafts | 3 | C2 | TRA-11, TRA-35 | AC: export for July 2023 on the demo subsample opens in Excel; printable view renders without JS; export action itself is audited. |
| TRA-13 | Reference data loader: holidays, FDIC branches (NJ, $1–5B banks, verified API), country_risk point-in-time table, tran-code → BankTransactionCode map; `fetch_lists.sh` for OFAC, UN, OpenSanctions and the ISO 20022 code sets, BTC codification and camt.054 XSD (all URLs in D7) | 3 | C1 | TRA-6 | AC: `screener refdata load` populates tables; `fetch_lists.sh` downloads every D7 asset with a checksum log; `country_risk` lookups by date return Turkey as grey on 2023-03-01 and normal on 2026-11-11; every FATF date row has a `verified_on` and a source URL; every tran-code map row resolves to a valid triplet. |
| TRA-53 | Stretch: `screener export --format camt054` producing a schema-valid camt.054.001.13 XML for a date range (business_date in `RltdDts/Prtry`, source in `SplmtryData`) | 3 | C3 or later | TRA-6 | Context: proves the "standard format" claim to the client and gives vendors a bake-off input. AC: output validates against the downloaded XSD; round-trip test reads it back into the canonical schema with no field loss. |
| TRA-14 | Demo environment: compose.demo preloads the 100k-account subsample, seeded users for three roles, demo day 2023-07-14 | 2 | C3 | TRA-8, TRA-24 | AC: `make demo` on a clean machine reaches a populated queue in under 10 minutes; passwords only in `.env.example` with a warning. |

### P1 Cash & CTR (Vedant)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-15 | R1 CTR candidate rule, fixtures, tests | 3 | C1 | TRA-6 | Scope: `rules/r01_ctr/` with `rule.yaml`, `rule.sql` (per-customer per-business-day cash-in and cash-out totals, separately, never netted), `inject.py` (5 CTR days), tests for $10,000.00 vs $10,000.01, two accounts one customer, two branches, Friday→Monday and holiday roll-forward. AC: all fixture tests pass; writes to `ctr_candidate`, not `hit`. |
| TRA-16 | R2 multi-day structuring rule (variants a and b), fixtures, injector | 3 | C1 | TRA-6 | AC: fixtures pass; on SAML-D reproduces 40 accounts / 90% precision / 57% recall for (a) and 15 / 100% / 24% for (b) (after TRA-24). |
| TRA-17 | R3 same-day / cross-branch structuring rule, fixtures, injector | 2 | C1 | TRA-6 | AC: ~10 injected cases recalled ≥0.9; natural volume reported as ~0 in docs/09. |
| TRA-18 | Evidence panels r01–r03 and the CTR candidates page | 3 | C2 | TRA-34 | Scope: `evidence.html` for each rule showing deposits by day and branch with the threshold line; CTR page with reconcile status. AC: renders from the fixture run; a hostile memo renders as text; screenshot in PR. |
| TRA-19 | `explain.py` for r01–r03 (agent evidence items) | 1 | C2 | TRA-45 | AC: returns cited items; unit test with the stub LLM. |
| TRA-20 | Measure R1–R3 on SAML-D; write volumes, precision, recall, lift to docs/09; set modes and budgets | 2 | C2 | TRA-24 | AC: numbers in docs/09 with the command that produced them; `rule.yaml` modes set. |

### P2 Account Behaviour (Vedanshu)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-21 | Rules engine core: folder loader, YAML schema, Jinja parameter rendering, DuckDB execution, `run --day`, run manifest | 5 | C1 | TRA-6 | Context: every slice depends on this; it ships against the fixture Parquet first. Scope: `screener/engine.py`, `screener/cli.py run`, `run` table. AC: `screener run --day` executes every `live` and `shadow` rule folder and writes hits with rule-version IDs; adding a new folder needs no code change (test adds `r99_tmp`). Label `contract`. |
| TRA-22 | Consolidation and scoring: hits → one alert per customer-day; priority score; CTR routing | 3 | C1 | TRA-21 | AC: two hits → one alert with both attached; cascade on close covered by a test; score formula in C8 with a unit test. |
| TRA-23 | Backtest: `screener backtest --rule --version --from --to` and the backtest page (counts per version, delta) | 3 | C2 | TRA-21, TRA-34 | AC: backtest of R4 at 180/120/365 days over May–Aug produces a table and a chart on the page; results stored with the proposed rule version so maker-checker can see them. |
| TRA-25 | R4 dormant reactivation rule, fixtures (179 vs 180 days), injector | 3 | C1 | TRA-6 | AC: fixtures pass; on SAML-D reproduces ~3,730 events; ~15 injected cases recalled ≥0.9. |
| TRA-26 | R7 new-account burst rule, fixtures, injector | 3 | C1 | TRA-6 | AC: fixtures pass; measured volume and budget decision in docs/09. |
| TRA-27 | R8 ATM anomaly rule (count, value vs baseline, multi-state), fixtures, injector | 3 | C1 | TRA-6 | AC: fixtures pass; relies on `channel` and ATM location from the US layer (TRA-30). |
| TRA-28 | Customer page (account timeline, dormancy gaps, prior alerts) and evidence panels r04, r07, r08 | 3 | C2 | TRA-34 | AC: renders from the fixture run; screenshot in PR. |
| TRA-29 | `explain.py` for r04, r07, r08; measure R4, R7, R8 on SAML-D into docs/09 | 2 | C2 | TRA-24, TRA-45 | AC: numbers and modes recorded; stub-LLM test passes. |

### P3 Funds Movement (Abdul)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-24 | SAML-D adapter → canonical Parquet (cash orientation: depositor = sender, withdrawer = receiver; string account IDs; 1:1 USD) with reconciliation report | 3 | C1 | TRA-6 | AC: 9,504,852 rows in, row count and Σ amounts reconcile; `load_batch` row written; runtime under 3 minutes on the laptop. |
| TRA-30 | US layer: customers (label-blind 10% grouping), KYC tiers, open dates, branches, channels, P2P relabel, holidays; injector framework calling each rule's `inject.py`; `answer_key.json` | 5 | C1 | TRA-24, TRA-13 | AC: every assignment uses the seeded RNG and never reads labels (test asserts no label column is referenced); answer key lists every injected case with rule id; docs/04 describes each proxy. Label `contract`. |
| TRA-31 | Demo subsample (100k accounts, all labelled accounts kept) and Tide adapter (optional, R5 benchmark) | 2 | C2 | TRA-30 | AC: subsample Parquet reproducible from seed; Tide adapter runs R5 and reports the 22.5% / 66% benchmark. |
| TRA-40 | Evaluation harness: `screener evaluate` (precision, recall, lift per rule on labels + answer key, chronological split) and the evaluation page | 3 | C2 | TRA-21, TRA-30 | AC: writes `docs/09-evaluation.md` tables from a command; page shows per-rule volume vs budget with live/shadow badge. |
| TRA-33 | R5 rapid pass-through rule with baseline condition, fixtures (71 vs 73 hours), injector; tuning record | 5 | C1–C2 | TRA-6 | Context: Debasish's first pain point and the flood example. AC: as-written and tightened volumes both recorded; ships in shadow unless ≤50/month; tuning steps documented as the demo narrative. |
| TRA-36 | R10 round-dollar rule, fixtures, injector | 2 | C1 | TRA-6 | AC: ~10 injected cases recalled; natural volume ~0 recorded. |
| TRA-37 | R12 transfer splitting rule (pair-keyed and funnel variant with new-sender condition), fixtures, injector | 3 | C1 | TRA-6 | AC: variant (b) catches the 75 "Structuring" receivers at a volume under budget, or ships in shadow with the measurement recorded. |
| TRA-38 | Funds-flow view and evidence panels r05, r10, r12; `explain.py` for the three | 3 | C2 | TRA-34, TRA-45 | AC: in/out within window drawn as a small table and timeline; renders from the fixture run. |

### P4 Counterparty & Rails (Natalie)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-34 | Django app skeleton: project, `accounts` (three roles, login), `alerts` models mirroring the data model, migrations, queue page, alert detail shell including evidence partials by rule id, `/healthz`, Tailwind | 5 | C1 | TRA-5 | Context: every UI ticket depends on this; ship the shell against the fixture run first. AC: login as each role; queue sorted by score then age with aging badges; alert page includes `rules/<id>/evidence.html` for each hit; autoescaping test with a hostile memo. Label `contract`. |
| TRA-35 | Disposition state machine, reason codes, notes, four-eyes, SAR clock, suppression | 5 | C1–C2 | TRA-34, TRA-11 | AC: every transition in C3 tested, illegal ones rejected; analyst cannot self-approve; SAR status hidden from Analyst role; every change calls `audit.record()`. |
| TRA-39 | Admin console: rule versions with maker-checker, seasonal profiles, mode switch, red-flag catalogue; `django-simple-history` | 5 | C2 | TRA-34, TRA-21 | Context: Debasish's "change thresholds and add rules without recoding". AC: a proposed change needs a different BSA officer to approve; the backtest result (TRA-23) is visible on the proposal; approved versions take effect on the next run only. |
| TRA-41 | R6 high-risk jurisdiction rule with point-in-time lists, fixtures, injector | 3 | C1 | TRA-6, TRA-13 | AC: fixture with a Turkey wire in 2023 fires and the same wire dated 2026 does not; measured volume and budget decision recorded. |
| TRA-42 | R9 wire to new beneficiary rule, fixtures (90-day lookback edge), injector | 3 | C1 | TRA-6 | AC: fixtures pass; domestic-wire fixtures included; measured volume recorded. |
| TRA-43 | R11 P2P anomaly rule (value, count, baseline, small-account tightening), fixtures, injector | 3 | C1 | TRA-6 | AC: fixtures pass; rail disclosed as synthetic in docs/04; measured volume recorded. |
| TRA-44 | Counterparty/country panel and evidence panels r06, r09, r11; `explain.py` for the three | 3 | C2 | TRA-34, TRA-45 | AC: panel shows country tier in force on the transaction date with its source. |

### P5 Investigator Agent (Vedant, with one ticket per owner)

| Key | Title | Pts | Cycle | Dep | Description |
|---|---|---|---|---|---|
| TRA-45 | Agent harness: `LLMClient` interface (Anthropic SDK + deterministic stub), evidence-pack builder, redaction, prompt with citation format, `agent_draft` model, CLI `screener draft --alert` | 5 | C2 | TRA-22, TRA-11 | Context: the kickoff asked for an agentic harness on the bank's credentials; the thin slice must never decide. AC: stub works offline and in CI; real provider enabled only by env; memos are wrapped as quoted data; the draft never changes status; every call is audited with prompt hash and model. Label `contract`. |
| TRA-46 | Agent draft panel on the alert page with "Draft" button, editable output, citations linking to evidence items | 3 | C2–C3 | TRA-45, TRA-34 | AC: Analyst and Officer can draft; Auditor can read; the draft is stored and exported with the alert (TRA-12). |
| TRA-47 | Agent control set document: scope, redaction, logging, graduated autonomy, accuracy measurement plan | 2 | C3 | TRA-45 | AC: `docs/10-agent-controls.md` reviewed by all four; ties to SR 26-2's exclusion of agentic AI. |

### P6 Client & Docs (Vedant, sections by owner)

| Key | Title | Pts | Cycle | Owner | Description |
|---|---|---|---|---|---|
| TRA-48 | Move research into `docs/` (glossary, client brief, regulations, rules catalogue skeleton, data plan, architecture with ADR-001, vendors and cost, friction, sources); delete duplicate scope file | 3 | C1 | Vedant | AC: every file in F4 `docs/` exists with content from this plan; README links them. |
| TRA-49 | Rules catalogue sections for own rules (parameters, red-flag citations, measured numbers, caveats) | 1 each | C2 | each owner | AC: `docs/02-rules-catalogue.md` section per rule with the numbers from docs/09. |
| TRA-50 | Demo script v2 (hybrid: rules, tuning, four-eyes, audit export, agent draft) and rehearsal checklist | 2 | C3 | Vedant | AC: runs end to end on `make demo` in under 12 minutes. |
| TRA-51 | Leadership presentation outline for Coforge BFSI (early Jan 2027): business impact, cost of doing nothing, ROI model, architecture, roadmap, KPIs | 3 | C3 | Vedant | AC: outline reviewed by the team; no timeline estimates in client-facing text; every number tagged. |
| TRA-52 | Written follow-up questions to the client (60-minute citation, ISO 20022 reference, asset size and regulator, LLM platform, fraud split by rail) | 1 | C1 | Vedant | AC: sent by email with Adam copied; answers logged in README meeting notes. |

**Dependency shape:** TRA-5 and TRA-6 (day 0) unblock every rule ticket; TRA-21 unblocks consolidation, backtest, evaluation and the admin console; TRA-34 unblocks every UI ticket; TRA-24/26 unblock the measurements; TRA-45 unblocks the explain tools. Everything else runs in parallel. The critical path is TRA-5 → TRA-6 → TRA-21 → TRA-22 → TRA-34 → TRA-35, all of C1, so Vedant does TRA-5/2 on day 0 while Vedanshu starts TRA-21 against the contract draft and Natalie starts TRA-34 against the fixture Parquet.

**Points per owner (approx.):** Vedant 37 (platform-heavy, fewer rule points), Vedanshu 28, Abdul 29, Natalie 30. Cycle load C1 ≈ 60, C2 ≈ 50, C3 ≈ 15 plus tuning and polish.

## GitHub setup commands (run once by the lead; the scaffold session could not create a public repository)

```bash
gh repo create transaction-alert-screener --public --source=. --remote=origin --push \
  --description "AML transaction alert screener for a regional bank: deterministic rules, append-only audit trail, human decision, thin investigator agent. Course project; synthetic data only."
```

```bash
gh api -X PATCH repos/this-ved-dev/transaction-alert-screener -f allow_squash_merge=true -f allow_merge_commit=false -f allow_rebase_merge=false -f delete_branch_on_merge=true -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY
```

```bash
gh api -X PUT repos/this-ved-dev/transaction-alert-screener/branches/main/protection --input - <<'JSON'
{"required_status_checks":{"strict":true,"contexts":["lint","test","integration","rules","docker"]},
 "enforce_admins":false,
 "required_pull_request_reviews":{"required_approving_review_count":1,"require_code_owner_reviews":true,"dismiss_stale_reviews":true},
 "restrictions":null,"required_linear_history":true,"allow_force_pushes":false,"allow_deletions":false,
 "required_conversation_resolution":true}
JSON
```

Then: invite the three collaborators (`gh api -X PUT repos/this-ved-dev/transaction-alert-screener/collaborators/<handle> -f permission=push`), replace the `@VEDANSHU_GITHUB`, `@ABDUL_GITHUB`, `@NATALIE_GITHUB` placeholders in `CODEOWNERS` with their handles, make the GHCR package public after the first `publish` run, and connect the Linear GitHub integration (Linear → Settings → Integrations → GitHub) so branches and PRs move issues automatically.
