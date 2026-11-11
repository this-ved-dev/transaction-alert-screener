# Build on SAML-D, cross-check pass-through on Tide

> **Final recommendation, 2026-11-04, after downloading and profiling both datasets.** This replaces the original recommendation further down, which is kept for the record. Details are in the two "Profiling" sections.
>
> **SAML-D is the primary dataset.** It is the only one with real cash deposits *and* labelled cash structuring:
> - Its "Smurfing" type is 932 cash deposits from 63 accounts, clustered within days.
> - The 5-day structuring rule (R2a) flags 40 accounts. 36 are Smurfing accounts (90% precision), which is 57% of the 63.
> - 10,420 accounts reactivate after 180+ days idle, so the dormancy rule (R4) fires on native data.
> - Caveat: SAML-D's label named "Structuring" is not cash. It is many senders paying one receiver under $10k over ACH, cheque, card or cross-border. It belongs to the transfer-splitting and funnel stretch rules.
>
> **Tide is an optional cross-check:**
> - It is strong for pass-through (R5): 66% recall at 22.5% precision against a 2.2% base rate.
> - It has native customers who own several accounts.
> - Its "DEPOSIT" and "WITHDRAWAL" rows are transfers between different owners' accounts, and no account is ever idle 180 days, so it cannot grade the cash or dormancy rules.
>
> **Hand-built test cases are needed for everything no dataset carries:**
> - R3 same-day pairs just under $10k: SAML-D has none, and Tide's carry no labels.
> - Cross-branch activity: no dataset has branches.
> - Cross-account aggregation on SAML-D.
> - Threshold edges.
>
> **OpenSanctions** covers name and jurisdiction screening, not transactions. See its own section.

The team should build its MVP on **Tide's HI reference dataset** (CC BY 4.0, 12 months, about 7.6M edges) and score its rules against **SAML-D** (9.5M rows with a typology label on every row). IBM AMLworld HI-Small should come out of the benchmark slot. Tide is the only openly licensed candidate that has all of the following: explicit cash DEPOSIT and WITHDRAWAL transactions, entity-to-account ownership edges for customer-level aggregation, KYC-style customer attributes, country-risk flags, a full year of history and an MIT-licensed generator the team can re-run. Its first fraudulent rows are already sub-€10,000 structured deposits. SAML-D has no customers or branches, but its labels (1,870 Structuring, 932 Smurfing and 945 Deposit-Send rows among 17 suspicious types) make it the best public yardstick for per-rule recall. Its non-commercial licence does not bar an unpaid course project with a fictional client. AMLworld HI-Small covers only 10 primary days, so R4 and R6 cannot run on it. Its "Cash" is a transfer between two accounts, and about 87% of its laundering is ACH. SA-SAML-D has the richest KYC fields and the longest window (27 months), but it has an unlicensed download, ZAR amounts and an 11% suspicious-account rate, so it is a fallback. No public dataset has transaction-level branches or US payment rails. The team still has to build a thin US layer: USD relabel, US business-day calendar, branch table, tran-code map and customer file. That is about 3–4 person-days including the benchmark adapter. Two checks in the first hour after download decide whether this choice holds. First, does Tide produce customer-days with more than $10k in cash, and customers who own several accounts? Second, are SAML-D's Structuring rows cash in the $2k–$9,999 band? With seven days left before the Nov 11 deadline, the team's Faker generator should shrink to a set of boundary-case test fixtures.

## Every candidate lacks branches and US rails, so customers and cash decide the choice

The six rules read only a small set of fields. Start with what a real US core system would send. The public Jack Henry jXchange history mapping carries account ID, tran code and description, amount, posting and effective dates, teller, batch and running balance. It carries no customer (CIF) number on the transaction row and no cash flag ([jXchange AcctHistSrch](https://jackhenry.dev/jxchange-soap/api-reference/core-services/accthistsrch/providers/core-director/mapping/)). Apache Fineract's transaction table looks similar but adds a branch (`office_id`) ([Fineract](https://fineract.apache.org/docs/database/tables/m_savings_account_transaction.html)). So a realistic MVP input is two files. The first is a nightly transaction CSV of about 18 columns, with an unsigned amount plus a debit/credit flag and a bank-editable lookup from tran code to cash and channel. The second is a customer-to-account reference file. R1 adds one hard constraint. A CTR is filed per person per business day, with **cash-in and cash-out totalled separately and never netted**, and each account flagged as cash in or cash out ([FinCEN CTR XML guide](https://bsaefiling.fincen.gov/docs/XMLUserGuide_FinCENCTR.pdf)).

Against that target, **no public dataset has a branch ID on each transaction**. IBM's AMLSim puts `branch_id` on accounts only, and the FCA/Turing synthetic set has branch identifiers but is available only inside the FCA Digital Sandbox ([AMLSim schema](https://github.com/IBM/AMLSim/wiki/Data-Schema-for-Input-Parameters-and-Generated-Data-Set); [FCA report](https://www.fca.org.uk/publication/research-notes/synthetic-data-anti-money-laundering-project-report.pdf)). None is denominated in USD with US rails. Branch, calendar and currency will therefore be synthesised whichever dataset the team picks. Four things separate the candidates: a real customer-to-account mapping, true cash-in and cash-out semantics, enough history for 180-day dormancy and a 90-day baseline, and labels that map to the rules. Most of the field fails at least one of these outright.

| Candidate | Fatal gap for this MVP | Residual use |
|---|---|---|
| SynthAML (CC0) | Amounts are standardised log-DKK, and there is no customer or account ID, so dollar thresholds mean nothing ([Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)) | Only public source of bank-derived Report/Dismiss outcomes (about 17% reported) to set disposition rates |
| TransXion | Person and account are 1:1; "Cash" is a payment format on account-to-account edges; mostly CNY ([GitHub](https://github.com/chaos-max/TransXion)) | None |
| AMLNet v2 (CC BY-NC) | CASH_OUT only, no cash-in; 195 days; Australian rails; generator withheld ([Zenodo](https://zenodo.org/records/21237971)) | None |
| AMLGentex | Cash occurs only on SAR accounts, so any cash rule trivially finds the labels ([GitHub](https://github.com/aidotse/AMLGentex)) | None |
| IBM AMLSim | Generates no cash transaction type ([schema](https://github.com/IBM/AMLSim/wiki/Data-Schema-for-Input-Parameters-and-Generated-Data-Set)) | None |
| J.P. Morgan AML | Email request with unknown turnaround ([JPMC](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)) | None before Nov 11 |
| Berka PKDD'99 | Real data, but one client per account, 1990s CZK and no stated licence ([CTU](https://relational.fel.cvut.cz/dataset/Financial)) | Optional unlabelled realism check |
| TabFormer, Sparkov, PaySim, BankSim | Card spend or mobile money; no teller cash; short windows ([PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1)) | R6 background noise at most |

That leaves four finalists: SAML-D, Tide, SA-SAML-D and AMLworld. The core decision is among them.

## Tide has the structure a bank needs; SAML-D has the labels an evaluator needs

Tide and SAML-D have opposite strengths. Tide models individuals, businesses, accounts and institutions as nodes, and both transactions and ownership as edges. **Every individual and business has a dedicated cash account**, and a global cash node supplies deposits of unknown origin. The reference data spans January–December 2025 with a base of 8,000 individuals. The HI variant has 36,653 nodes, 7,618,299 edges and 0.19% illicit activity ([Tide paper](https://arxiv.org/html/2603.01863v1)). Node columns include `occupation`, `age_group`, `business_category`, `risk_score`, `country_code`, `is_high_risk_country` and `creation_date`. Transaction rows carry `edge_type`, `ownership_percentage`, `transaction_type`, `time_since_previous_transaction` and `is_fraudulent`. The first fraudulent rows are **individual-to-account DEPOSITs of €9,200, €9,300 and €9,700**, which look exactly like structured cash ([Zenodo 18804069](https://zenodo.org/records/18804069)). The fraud patterns are repeated overseas transfers, rapid fund movement, front-business activity, synchronised transactions and U-turns. The generator also adds **seven "counter-leakage" background patterns** so that legitimate customers do suspicious-looking things too ([Tide paper](https://arxiv.org/html/2603.01863v1)). For a triage tool, that is a feature: rules will raise false positives an analyst must dismiss. The generator is MIT-licensed, and `graph.yaml` sets scale and time span ([GitHub mntijn/Tide](https://github.com/mntijn/Tide)). Tide's weaknesses are real, though. Its label is a binary `is_fraudulent`, and no per-row pattern name has been confirmed. It was released in March 2026, and the notes found no third-party use of it. Amounts are in EUR. Nobody has yet checked whether individuals own more than one bank account beyond their cash account.

SAML-D is the more mature dataset. It has **9,504,852 rows over about 320 days** (2022-10-07 to 2023-08-23), 0.104% suspicious, and about 10,000 Kaggle downloads ([Kaggle](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml); [linhdanapril notebook](https://github.com/linhdanapril/Anti-Money-Laundering-AML)). Its seven payment types include **Cash Deposit and Cash Withdrawal**. Receiver locations include Mexico, Turkey, Morocco and the UAE, which the authors flag as high-risk ([Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)). Every row carries one of 28 typology labels ([anjalirathod310 notebook](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard)). The gaps are structural. Rows are keyed only by sender and receiver account, so there is no customer, branch, KYC field or transaction ID. The data is a multi-bank UK view rather than a single bank's book. The amount unit is undocumented, and the generator is not public ([Oztas thesis](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)). Most importantly, **neither the paper nor the thesis states the amount band, window or cash mix used to generate Structuring and Smurfing** ([Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)).

SA-SAML-D looks best on paper and worst in practice. It has 58 columns, including `Customer_type`, `PEP_category`, `Jurisdiction_risk_tier`, `Counterparty_country`, `Channel_preference` and `Account_open_date`. It covers 27 months and 22 typology families, with 200,065 cash deposits and 174,365 cash withdrawals ([data dictionary](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/simulated_data/SA_SAML_D_data_dictionary.csv); [payment-type metrics](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/insights/payment_type_metrics.csv)). But the median account has only **27 transactions in 27 months**, and **11.43% of accounts are suspicious** ([dataset overview](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/insights/dataset_overview.csv)). Its 7.15% suspicious-transaction rate is roughly 35–70 times the 0.10–0.19% in the other finalists, and it would inflate any precision figure. The Zenodo record says CC BY 4.0 but restricts its files, and the openly downloadable GitHub copy has no licence file ([Zenodo 22803333](https://zenodo.org/records/22803333); [GitHub](https://github.com/ColbertN/SA-AML-DATA-SIMULATION)). AMLworld HI-Small has a genuine customer layer: `accounts.csv` maps each account to an Entity ID, and some entities hold accounts at several banks. But it has only **10 primary days** plus a tail through day 18 in which 59% of rows are laundering. Only 108 of its 490,891 Cash rows are labelled, and none of its Wire rows ([hugomagee](https://github.com/hugomagee/aml-transaction-monitoring-dbt); [Kaggle](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)).

| | **Tide (HI)** | **SAML-D** | **SA-SAML-D** | **AMLworld HI-Small** |
|---|---|---|---|---|
| Released | arXiv Mar 2026; Zenodo v2 Jun 2026 | Kaggle v2 Jan 2024 | Zenodo 17 Sep 2026 | NeurIPS 2023; Kaggle v8 Jul 2025 |
| Size | 36,653 nodes; 7.6M edges; about 0.9 GB per file | 9,504,852 rows; 996 MB | 1,441,479 rows; 35,000 accounts; 908 MB | 5,078,345 rows; 476 MB |
| History | 12 months | about 320 days | 27 months (median 27 txns per account) | 10 primary days (+8 tail days) |
| Customer ↔ account | **Ownership edges** (profiled: individuals 1–3, businesses 1–5 accounts) | None; accounts only | Account = customer | Entity ID in `accounts.csv` |
| Cash semantics | DEPOSIT / WITHDRAWAL are transfers between different owners' accounts (profiled) | **Cash Deposit / Cash Withdrawal** payment types | **Cash Deposit / Cash Withdrawal** | "Cash" = transfer between two accounts |
| Branch | None | None | Profile-level channel preference only | Bank only |
| Country / risk | `country_code`, `is_high_risk_country` | 18 bank locations | Counterparty country, risk tier | None (parse from bank names) |
| KYC fields | Occupation, age, business type, risk score | None | Richest (PEP, income, sector…) | Entity-type prefix only |
| Labels | Binary only; 99% on TRANSFER (profiled) | **28 typologies per row** | 22 typology families | Binary + partial `Patterns.txt` |
| Illicit rate | 0.19% | 0.104% | 7.15% of rows; 11.43% of accounts | about 0.10% |
| Currency | 15 currencies, nominal amounts (profiled) | Undocumented (UK-focused) | ZAR | 15 currencies |
| Generator | **Public, MIT** | Not public | Script in an unlicensed repo | Not public |
| Licence | **CC BY 4.0** | CC BY-NC-SA 4.0 | Ambiguous | CDLA-Sharing-1.0 |
| Recommended role | **Primary** | **Benchmark** | Fallback, local only | Drop (optional R5 check) |

The best case for SAML-D as primary, which one research thread made, rests on maturity and labels. It is the more established dataset, and a typology on every row lets the team report recall per rule. That case is strong for evaluation and weak for the product. The layer SAML-D lacks (customers with several accounts and a KYC profile) is exactly what R1 tests and what a triage screen shows. If the team invents that grouping, **R1's cross-account aggregation becomes self-fulfilling**: the rule finds what the grouping script put there. Tide supplies the layer natively. Splitting the roles uses each dataset for what it does best.

## Rule by rule, Tide fires four rules natively and AMLworld fires none

The matrix below rates each rule as **Strong** (fires on native fields, with relevant positives), **Partial** (fires only after synthesis or a proxy), **Weak** (fires but with artificial semantics or almost no matching labels) or **Cannot**. The ratings are judgements from the cited schema facts, not measured results.

| Rule | Tide (HI) | SAML-D | SA-SAML-D | AMLworld HI-Small |
|---|---|---|---|---|
| **R1** CTR, cash >$10k per customer per business day | **Partial (profiled).** Multi-account rollup is native and fires on 24,469 customer-days, but "cash" rows are transfers and carry almost no labels; branch is synthetic | **Partial.** Cash types exist, but the customer grouping is synthetic, so the cross-account test is circular; Single_large (250) gives only partial positives | **Partial.** Account = customer; ZAR must be rescaled to the $10k threshold | **Weak.** Entity ID aggregates, but "Cash" is a transfer that reaches millions |
| **R2** multi-day structuring | **Weak (profiled).** 473 customers hit, but recall is 3 of 107 fraud cash-in customers, because injected "structuring" is one deposit per person | **Strong (profiled), via Smurfing.** R2a: 90% precision, 57% recall on 63 smurfing accounts; the "Structuring" label is non-cash | **Partial.** Structuring family labelled, but the ZAR band must be mapped and prevalence is inflated | **Weak.** No structuring typology; 30-day window does not fit |
| **R3** same-day / cross-branch | **Partial.** Same-day per customer is native; branch is synthetic | **Cannot (profiled).** No customer-day has two $9k–$10k cash deposits | **Partial.** Channel preference can guide branch assignment | **Weak.** Bank stands in for branch |
| **R4** dormant ≥180d, then ≥$5k in 7d | **Cannot (profiled).** No account has a gap of 180 days or more | **Partial (profiled).** 10,420 accounts reactivate after ≥180 days, 3,730 with ≥$5k in 7 days; no dormancy label | **Strong.** 27 months, open dates and sparse histories create natural gaps | **Cannot.** 10 days |
| **R5** ≥80% of inbound out within 72h | **Strong (profiled).** 65.8% recall, 22.5% precision vs a 2.23% base rate | **Strong.** Deposit-Send 945, Layered_Fan_*, Gather-Scatter | **Strong.** Mule / pass-through family | **Partial.** Fan patterns fit; third-party precision 2.85% |
| **R6** velocity vs 90-day baseline | **Strong.** Dense 12-month histories | **Strong.** Baseline available after Jan 2023; Behavioural_Change_1/2 (739 rows) | **Weak.** About 3 transactions per 90 days at the median | **Cannot.** No 90-day baseline |
| Stretch: high-risk wires | **Strong.** `is_high_risk_country`; overseas-transfer pattern | **Strong.** Mexico, Turkey, Morocco, UAE; Behavioural_Change_2 | **Strong.** Jurisdiction risk tier; International Wire | **Weak.** Country only from bank names |
| Stretch: funnel / mule burst | **Partial.** Synchronised-transactions pattern (inferred fit) | **Strong.** Fan_In, Layered_Fan_In, Smurfing | **Strong** | **Strong.** FAN-IN, GATHER-SCATTER |

Sources for the cells: Tide fields and patterns ([paper](https://arxiv.org/html/2603.01863v1); [Zenodo](https://zenodo.org/records/18804069)); SAML-D counts ([anjalirathod310](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard)); SA-SAML-D density ([overview](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/insights/dataset_overview.csv)); AMLworld rule results ([hugomagee rule_results](https://github.com/hugomagee/aml-transaction-monitoring-dbt)).

Before profiling, the tally was **Tide 4 Strong / 2 Partial, SAML-D 3 / 2 / 1 Weak, SA-SAML-D 2 / 3 / 1 Weak, AMLworld 0 Strong**. After profiling, Tide is **2 Strong (R5 measured; R6 not yet profiled) / 2 Partial (R1, R3) / 1 Weak (R2) / 1 Cannot (R4)**. Its edge over SAML-D is now customer structure and R5, not cash. After profiling, SAML-D is **3 Strong (R2 measured; R5, R6 not yet profiled) / 2 Partial (R1, R4) / 1 Cannot (R3)**, and it is the only finalist with native support for both of the client's pain points. Three cells deserve emphasis. First, R2 on SAML-D is the dataset's main selling point, yet it depends on a fact nobody has published: whether the Structuring rows are cash, sit in the $2k–$9,999 band and cluster within five days. Second, R4 is weak or partial everywhere except SA-SAML-D. The team should plan to prove R4 on hand-built fixtures whatever it chooses. Third, R3's cross-branch condition is circular on every dataset, because branch is always synthetic. Branch assignment should therefore be **label-blind**, with a handful of cross-branch cases injected and disclosed separately. Otherwise the R3 recall figure measures the team's own injection script.

Absolute precision will be low on any of these datasets, and the compliance-manager persona should hear that as normal rather than as failure. The SAML-D authors put rules-based monitoring at about 95% false positives ([Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)). A public rule engine on AMLworld HI-Small achieved **1.31% precision for structuring, 2.85% for pass-through and 7.15% for fan-in/out**, against a 0.73% base rate ([hugomagee rule_results](https://github.com/hugomagee/aml-transaction-monitoring-dbt)). Precision relative to the base rate (lift) is the honest metric to show.

## The non-commercial licences were never the real obstacle

The team ruled out SAML-D and AMLNet on licence grounds, but Creative Commons' own guidance points the other way. CC defines NonCommercial use as use "not primarily intended for or directed towards commercial advantage or monetary compensation" ([CC BY-NC-SA 4.0 legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)). CC's interpretation guidance says the test turns on the use, not the identity of the user ([CC NC interpretation](https://wiki.creativecommons.org/wiki/NonCommercial_interpretation)). An unpaid, graded student project for a role-played bank is not directed at commercial advantage, so **SAML-D is usable**. Its ShareAlike term binds only adapted data the team redistributes, not the Python code that reads it. The same guidance warns that not every educational use is automatically non-commercial. The conclusion would change if a sponsor paid the team, if a consultant reused the deliverable for real clients, or if the repo were used to market a product. Validating a real bank's rules against NC data would also count as commercial use. This is a reading of the licence text, not legal advice, and Kaggle's own site terms were not checked.

The cleaner pattern for the repo is to **commit code, fetch scripts and metrics, and almost no third-party rows**. Aggregate results such as alert counts and precision figures are facts. CDLA-Sharing explicitly frees "Results" ([CDLA-Sharing-1.0](https://cdla.dev/sharing-1-0/)). Tide's CC BY 4.0 licence is the easiest here: a small sample and the US-layer derived files can be committed with attribution, a licence link and a change note.

| Asset | Licence | Commit to GitHub? | Obligations |
|---|---|---|---|
| Team code | Team's choice (MIT) | Yes | None from the data licences; CC terms attach to data and its adaptations |
| Tide sample + US-layer derived files | CC BY 4.0 ([Zenodo](https://zenodo.org/records/18804069)) | Yes, a small sample | Credit van den Beukel et al. 2026 and the Zenodo record; link the licence; list changes in `CHANGES.md` |
| SAML-D | CC BY-NC-SA 4.0 ([Kaggle](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml)) | No rows; fetch script and metrics only | Any committed sample or derived file must be BY-NC-SA, in `data/saml_d/` with `LICENSE`, `ATTRIBUTION.md` (Oztas et al., ICEBE 2023, doi:10.1109/ICEBE59045.2023.00028) and `CHANGES.md`; credit it on slides that show rows |
| SA-SAML-D | Zenodo CC BY 4.0 with restricted files; GitHub copy unlicensed ([Zenodo](https://zenodo.org/records/22803333)) | No | Local use only; cite the DOI; ask the authors before relying on it |
| AMLworld (if kept) | CDLA-Sharing-1.0 ([IBM/AML-Data](https://github.com/IBM/AML-Data)) | Optional | Keep the CDLA text, a change notice and the attribution |
| SynthAML alerts | CC0 ([figshare](https://api.figshare.com/v2/collections/6504421/articles)) | Yes (505 KB) | None; cite as a courtesy |
| FDIC branch extract | US government public data ([FDIC API](https://api.fdic.gov/banks/docs/)) | Yes | Rename to the fictional bank |
| `kaggle.json`, `data/raw/` | — | Never | Add to `.gitignore` |

## Profiling Tide HI changed the cash-rule plan

*Run on 2026-11-04 against `generated_nodes_HI.csv` and `generated_edges_HI.csv` from Zenodo 20591329. Both files match the record's MD5 checksums. The script is `scripts/profile_tide.py`; raw output is in `research_notes/AML transaction dataset selection/tide_profile_output.txt`.*

**Shape.** The edges file holds 7,589,749 transactions and 28,550 ownership edges. Timestamps run from 2025-01-01 to 2026-01-06. 14,269 transactions (0.188%) are labelled fraudulent.

| Check | Result | What it means |
|---|---|---|
| 1 Multi-account owners | **Passes.** Excluding cash accounts, individuals own 1, 2 or 3 bank accounts in roughly equal thirds (2,653 / 2,700 / 2,639). Businesses own 1–5 (about 220–250 each). No account has more than one owner. 1,711 individuals hold accounts in 2–3 countries | R1's cross-account aggregation is tested on native data, which SAML-D cannot offer |
| 2 Cash bands | **Volume passes, meaning fails.** <br>• **Not teller cash:** 848,907 of 849,049 DEPOSIT rows and 639,283 of 639,324 WITHDRAWAL rows run between two accounts with *different* owners. That is the same "cash is really a transfer" flaw that ruled AMLworld out.<br>• **Labels sit on transfers:** only 112 deposits and 69 withdrawals are fraudulent, and 14,088 of the 14,269 fraud labels are TRANSFERs.<br>• **Leak:** the 78 deposits that come straight from an individual are all fraudulent, so any rule keyed on that edge shape trivially finds the labels.<br>• **Hit counts with amounts read 1:1:** R1 fires on 24,469 customer-days, R2a on 473 customers and R3 on 552 customer-days.<br>• **Recall:** R2a catches 3 of the 107 customers with a fraudulent cash-in (2.8%), because Tide's "structuring" is one sub-$10k deposit followed by weekly transfers out | Tide gives realistic *alert volume* for R1–R3 once the adapter reads DEPOSIT as cash-in to the receiving account. It cannot *grade* R1–R3 |
| 3 Label granularity | **Fails.** The only label is binary `is_fraudulent`, with no pattern name on edges or nodes. The node-level `is_fraudulent` is set on 10,668 accounts (39%), and 10,649 of them simply touch a fraud edge, so it is not a customer-level truth | Per-typology recall needs SAML-D or the team's own injected cases |
| 6 Dormancy | **Fails.** No bank account has a gap of 180 days or more between transactions, and none is idle in the last 180 days | R4 can only be graded on injected cases |
| Extra: R5 pass-through | **Strong.** Inbound ≥5,000 followed by ≥80% out within 72h: 14,697 hits on 6,254 accounts. 65.8% recall of fraud-related inbound events, and 22.5% precision against a 2.23% base rate (about 10× lift) | Tide is a genuine grading set for R5 |

**Two more quirks the adapter must handle:**
- **Currency.** Amounts are nominal in each account's own currency, across 15 currencies (EUR, GBP, USD, CHF, JPY, BMD, XCD, VUV, HKD, BSD, BZD, SGD, AED, BBD and SCR). The generator places structured deposits around 9,000–9,999 *nominal* whatever the currency. Converting at approximate 2025 FX rates pushes 33 of the 73 fraudulent $2k–$9,999 deposits above $10k: the fraudulent $10k–$20k band grows from 15 to 48. So **relabel every currency as USD 1:1**, not only EUR.
- **Geography.** Customers are spread almost evenly across 24 mostly offshore countries (KY, BM, VU, BS, BZ, SC, BB, AG, IM, LI, MC and others, about 4% each; USA is 351 of 8,000 individuals). 65% of businesses carry `is_high_risk_country`. Treat every Tide account as domestic to the fictional bank. Use the counterparty account's country only for the high-risk-wire rule, and expect that rule to over-fire.

Smaller data issues:
- 12% of `time_since_previous_transaction` values are negative, so recompute it from timestamps.
- 4,656 cash-typed rows land on accounts with no owner.

**Revised plan.**
- **Tide stays the bank book** (customers, accounts, KYC fields, 12 months) and **the grading set for R5 and high-risk wires**.
- **R1–R4 are graded on labelled typologies injected into Tide**, each recorded in an answer key. This is the typology half of the original generator, without its baseline:
  - CTR days;
  - multi-day and same-day/cross-branch structuring;
  - dormant accounts, made by blanking 180+ days of history and adding a reactivation.
- **SAML-D remains the external check for R2/R3** if check 4 passes. That check still needs a team member to download SAML-D with their own Kaggle login.

This is the report's "if both fail" branch, with check 4 still open. Check 4 was then run; see the next section.

## Profiling SAML-D made it the primary dataset

*Run on 2026-11-04 against `SAML-D.csv` (Kaggle v2, 996,168,850 bytes). The script is `scripts/profile_saml_d.py`; raw output is in `research_notes/AML transaction dataset selection/saml_d_profile_output.txt`. Amounts are read 1:1 as USD, and the customer is the account on the cash-depositor side.*

**Shape.** The file has 9,504,852 rows from 2022-10-07 to 2023-08-23, of which 9,873 (0.104%) are laundering. It holds 225,206 Cash Deposit rows (1,405 laundering: 932 Smurfing and 473 Deposit-Send) and 300,477 Cash Withdrawal rows (1,334 laundering).

| Check | Result | What it means |
|---|---|---|
| 4 Structuring / Smurfing profile | **Smurfing passes, "Structuring" fails.** <br>• **Smurfing:** all 932 rows are Cash Deposits of $1,008–$6,985 (median $2,629; 72% in $2k–$9,999). They come from 63 accounts, with a median of 15 deposits each spread over 121 days, and every one of those accounts has 3+ deposits within some 5-day window. <br>• **"Structuring":** 1,870 rows and **zero cash**. They run over ACH, cheque, card and cross-border, at $2,078–$12,454. Each comes from a different sender, and they land on just 75 receivers (median 24 payments over 191 days) | Grade R2 on Smurfing. "Structuring" is a non-cash fan-in to one beneficiary, which is the transfer-splitting and funnel typology |
| 5 Cash orientation | Cash Deposit rows have 24,328 distinct senders and 15,179 receivers. Cash Withdrawal rows have 15,009 senders and 23,517 receivers. No row is self-to-self | Treat the depositor as the sender and the withdrawer as the receiver. Each cash row links two accounts, so the adapter keeps only the customer side |
| R2a: 5-day, 3+ deposits of $2k–$9,999, total ≥$15k | 40 accounts hit; 36 are Smurfing accounts. That is **90% precision and 57% recall** of the 63 | A genuine, independently labelled test of the client's first pain point |
| R2b: 30-day total ≥$25k, none over $9,999 | 15 accounts hit, all Smurfing (100% precision, 24% recall) | Run both R2 variants and report their union |
| R3: 2+ deposits of $9k–$10k on one day | **0** customer-days | SAML-D's smurfing stays well under $9k. R3 needs hand-built test cases |
| R1: cash-in over $10k per day | 195 customer-days (150 involve laundering rows) | CTR candidates are rare and realistic in volume |
| 6 Dormancy | **Passes on volume.** 10,420 accounts restart after a gap of 180+ days, and 3,730 of those move $5k+ within 7 days. Only 2 involve laundering rows | R4 fires natively and shows realistic alert load. There is no dormancy label, so grade it on injected cases |
| R5 as written: inbound ≥$5k, then ≥80% out within 72h | 861,114 hits on 28,396 accounts. 36.8% recall, but **0.4% precision** against a 0.17% base rate | It floods: roughly 9,600 alerts a month per 100k accounts. On SAML-D, R5 needs a baseline condition before it can go live |
| Stretch 16 as written: 3+ non-cash payments under $10k to one receiver in 7 days, total over $10k | Catches all 75 "Structuring" receivers, but fires on **161,853** receivers | Too loose for SAML-D's normal fan-in. Add a distinct-new-senders condition before using it |

**Why this flips the primary choice.** The client's two stated pain points are cash structuring and dormant-account reactivation. SAML-D supports both on native data: labelled cash smurfing, and 10,420 natural dormancy gaps. Tide supports neither, because its cash rows are transfers and it has no idle accounts. Injecting typologies into Tide would have graded the rules against the team's own injection script, which is the circularity this report set out to avoid. The report's own decision rule ("if check 2 fails and check 4 passes, SAML-D becomes primary") lands here, with check 4 passing through Smurfing rather than "Structuring".

**What SAML-D still needs**, all inside the existing US-layer estimate:
- **Customers:** a customer file where one account equals one customer by default. To demo cross-account aggregation, group a disclosed, label-blind sample of accounts into multi-account customers.
- **Customer attributes:** a synthetic KYC tier.
- **Branches and dates:** label-blind branch assignment and the US business-day calendar.
- **Hand-built cases:** test cases for R3 and cross-branch R1.

Tide becomes optional. Use it for an R5 benchmark slide, and to show cross-account aggregation on data the team did not group itself.

## Recommendation: download Tide and SAML-D today, profile for an hour, then build

*Written before profiling. The roles below are superseded by the final recommendation at the top: SAML-D primary, Tide optional. The US-layer table and the licence rules still apply.*

**Primary dataset: Tide, HI variant** (Zenodo 18804069, plus 20591329 for `generated_edges`). **Benchmark: SAML-D**, used to measure per-rule recall against `Laundering_type`. Run it with `customer_id = account_id`, because it serves as a grading set, not the demo bank. **Disposition prior: SynthAML's alert table.** **Fallback: SA-SAML-D**, kept local. **Drop AMLworld HI-Small**, or keep it only as an optional external check on R5 and the funnel rule (trimmed to Sep 1–10, with Entity ID as the customer) if a student has spare time.

The US layer is thin because Tide already supplies customers, cash, KYC and country risk. Effort figures are estimates.

| Component | Method | Effort (person-days) |
|---|---|---|
| Adapter to the target schema | Map Tide edges to `txn_id` (hash), `account_id`, `customer_id` (from ownership edges), `post_date`, unsigned `amount`, `dr_cr`, `tran_code`, `channel`, `is_cash` and counterparty. Build the customer file with `customer_type`, `account_open_date` (from `creation_date`) and `last_customer_activity_date` | 0.5–1 |
| Currency | **Relabel all 15 currencies as USD 1:1** and document it. Amounts are nominal per account currency; FX conversion pushes 33 of the 73 fraudulent $2k–$9,999 deposits above $10k (profiled 2026-11-04) | <0.1 |
| Typology injector (added after profiling) | Inject labelled R1 CTR days, R2/R3 structuring and R4 dormant reactivations into Tide customers, and write an answer key. Tide's own cash rows are transfers and it has no dormancy | 0.5–1 |
| Calendar | Map timestamps to US business days with pandas `USFederalHolidayCalendar`; roll weekend and holiday postings to the next business day | 0.25 |
| Branches | Pull one $1–5B bank's branches from the keyless FDIC Summary of Deposits API ([FDIC SOD](https://api.fdic.gov/banks/sod?filters=YEAR:2025%20AND%20STALPBR:VT&fields=NAMEFULL,NAMEBR,CITYBR,STALPBR,DEPSUMBR,ASSET,BRNUM,UNINUMBR,SIMS_LATITUDE,SIMS_LONGITUDE&limit=3)) and rename them to the fictional bank. Weight home branches by `DEPSUMBR` and let only full-service branches take teller cash ([SOD variables](https://api.fdic.gov/banks/docs/sod_variables_definitions.csv)). Draw each cash transaction's branch label-blind (assumption: home branch about 80% of the time) | 0.5 |
| Channel / tran-code map | DEPOSIT → teller cash-in (with a stated ATM share), WITHDRAWAL → cash-out, cross-border TRANSFER/PAYMENT → international wire, domestic → ACH, all in an editable lookup table | 0.25 |
| Geography and bank scope | Treat every Tide account as domestic to the fictional bank. Countries are spread evenly over 24 mostly offshore jurisdictions, and USA is only about 4% (profiled). Use the counterparty account's country only for the high-risk-wire rule | 0.25 |
| KYC tier | Bucket `risk_score` and the high-risk flags into Low/Medium/High | <0.1 |
| Demo dispositions | Seed synthetic analyst outcomes at a report rate no higher than SynthAML's ~17%, which its authors call well above real-world rates ([Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)); label them synthetic | 0.25 |
| Boundary fixtures (the old Faker generator) | About 100 hand-built rows: $10,000.00 vs $10,000.01, $9,999, 179 vs 180 idle days, 71 vs 73 hours, Friday-to-Monday and holiday rollovers, one customer with two accounts, two branches on one day | 0.5 |
| SAML-D benchmark adapter | Same schema; read account columns as strings, since leading zeros are dropped; choose the customer side of cash rows after check 5; reuse the calendar and branch code | 0.5–1 |

The total is about **3–4 person-days, or roughly one calendar day across four students**. That leaves days 3–7 for the rules, the triage UI and evaluation.

These checks should run in the first hour after download, in DuckDB or Polars because both files are about 1 GB. Checks 2 and 4 are the ones that can flip the primary choice.

| # | Check | How | Result that keeps the plan | Result that changes it |
|---|---|---|---|---|
| 1 | Tide multi-account owners | Count ownership edges per individual or business to accounts whose `account_category` is not cash | A meaningful share of customers own ≥2 bank accounts, so R1 aggregation is tested on native data | Near zero: Tide's R1 advantage over SAML-D disappears. Synthesise grouping as SAML-D would need; decide on check 2 |
| 2 | Tide cash bands | Bin DEPOSIT/WITHDRAWAL amounts (<2k, 2k–8,999, 9,000–9,999, 10k and up) with the fraudulent share per bin. Count customer-business-days with cash-in or cash-out above 10,000, and customers with ≥3 deposits of 2k–9,999 in 5 days | Dozens or more R1 and R2 candidates. Most R1 hits fall at $10k–$20k, consistent with GAO's finding that a $20k threshold would remove about 65% of CTRs ([GAO-25-106500](https://files.gao.gov/reports/GAO-25-106500/index.html)) | Near zero: Tide cannot exercise the cash rules. **If check 4 passes, flip the primary to SAML-D** and add a synthetic customer layer (+1–2 person-days). Alternatively, regenerate Tide via `graph.yaml` |
| 3 | Tide label granularity | Does `generated_edges` or any field name the pattern for each fraudulent edge? | Yes: per-pattern recall can be computed on Tide itself | No: the SAML-D benchmark becomes mandatory, not optional |
| 4 | SAML-D Structuring/Smurfing profile | For those two `Laundering_type` values: `Payment_type` mix, `Amount` quantiles, rows per account within 5 days, day span | Mostly Cash Deposit, 2k–9,999 and clustered, so R2 recall is measurable | Non-cash or outside the band: SAML-D cannot grade R2 and stays only as the R5/R6/stretch benchmark |
| 5 | SAML-D cash orientation | For Cash Deposit and Cash Withdrawal rows, compare `nunique` of sender and receiver and look for sentinel "cash" accounts | Identifies the customer side; affects the adapter only | — |
| 6 | Dormancy in both datasets | Tide: `time_since_previous_transaction` ≥180 days followed by ≥$5k within 7 days. SAML-D: the same from account gaps | Some cases: R4 can be scored on data | None: prove R4 on fixtures. This does not flip the primary |

Taken together, the decision rule is simple. **Tide stays primary unless check 2 fails.** If check 2 fails and check 4 passes, SAML-D becomes primary. If both fail, keep Tide for R5, R6 and the stretch rules, and drive R1–R4 from fixtures. SA-SAML-D comes into play only if both fail and its authors confirm a licence.

| Existing plan | Change | Reason |
|---|---|---|
| Build an own Faker generator as the dataset | Use Tide plus the US layer; keep Faker only for about 100 boundary fixtures in unit tests | Public data is allowed. Tide already models customers, cash and KYC, and fixtures guarantee the threshold edges no dataset guarantees |
| Benchmark on AMLworld HI-Small | **Benchmark on SAML-D**; drop AMLworld or keep it as an optional R5 check | 10 primary days rule out R4 and R6; Cash is a transfer; ~87% of laundering is ACH ([hugomagee](https://github.com/hugomagee/aml-transaction-monitoring-dbt)) |
| Skip SAML-D over its NC licence | Use it, with no rows in the repo | Non-commercial status turns on the use; coursework with a fictional client qualifies |
| Skip AMLNet over its NC licence | Keep skipping it, but for fit, not licence | No cash-in type, 195 days, Australian rails ([Zenodo](https://zenodo.org/records/21237971)) |
| No disposition source | Add SynthAML outcomes as a prior | The only public bank-derived Report/Dismiss labels |
| No branch source | Add an FDIC SOD branch table | Real branch geography and deposit weights for R3 |
| Evaluation not specified | Alert unit = customer × rule × window; recall by typology on SAML-D; precision as lift over the base rate; tune and validate on a chronological split | Mirrors the most complete public rule evaluation ([hugomagee](https://github.com/hugomagee/aml-transaction-monitoring-dbt)) |
| — | Do not wait on the J.P. Morgan or FCA datasets | One needs an email request, the other is sandbox-only |

## OpenSanctions fits the screening side, not the transaction side

*Checked directly on 2026-11-04 against data.opensanctions.org/datasets/latest/index.json and opensanctions.org.*

OpenSanctions has no transactions, so it cannot be the primary dataset. It is, however, the best free source for everything the screener does with **names and jurisdictions**. It consolidates 501 source datasets into daily-updated collections. Each collection ships a flat `targets.simple.csv` with the columns `id, schema, name, aliases, birth_date, countries, addresses, identifiers, sanctions, phones, emails, program_ids, dataset, first_seen, last_seen, last_change`.

| Collection | Entities (2026-11-04) | `targets.simple.csv` | Use in the screener |
|---|---|---|---|
| `us_ofac_sdn` | 72,670 | 7.6 MB | Stretch rule 14 (OFAC screening), minimum legal list for a US bank |
| `us_sanctions` | 90,592 | 12 MB | All US lists (SDN, non-SDN and others) in one schema |
| `sanctions` | 309,889 | 79 MB | Adds UN, EU and UK lists, aliases and transliterations, de-duplicated |
| `peps` | 1,977,627 | 182 MB | PEP flag feeding the KYC risk tier (High tier → tighter thresholds) |
| `us_fincen_special_measures` | 858 | <0.1 MB | FinCEN 311/9714 "primary money laundering concern" banks and jurisdictions, alongside the FATF JSON for the high-risk-jurisdiction rule |
| `us_occ_enfact` | 11,304 | 1.4 MB | Research and pitch only (OCC enforcement history); not screening input |

Four concrete uses:

1. **Watchlist input for rule 14.** Read `us_sanctions` (or `sanctions`) instead of parsing OFAC's raw SDN/ADD/ALT CSVs. Aliases and transliterations come in one column, so a stdlib `difflib` or token-based matcher of a few dozen lines is enough for the MVP.
2. **PEP flag for risk tiering.** Mark a customer High tier when the matcher hits `peps`.
3. **An answer key for the matcher.** OpenSanctions publishes about 760,000 human match/no-match judgments on entity pairs (December 2025) as "matcher training data". That lets the team report screening precision and recall the same way SAML-D grades the transaction rules.
4. **Labelled screening hits in the demo data.** Give about 20 Tide or synthetic customers and wire counterparties a sanctioned name: some exact, some via an alias, some with a misspelling. Add near-miss decoys too. **Use sanctioned entities only.** Do not attach real PEPs' names to fabricated laundering in the repo or slides, because that pins invented suspicion on real, non-sanctioned people.

The self-hosted matching API, `yente`, is MIT-licensed. It needs an Elasticsearch/OpenSearch cluster, though, which is too heavy for a seven-day build; cite it as the production path.

**Licence.** The bulk data is CC BY-NC 4.0. OpenSanctions' free-use page names "a student project" as an example of non-commercial use that needs no permission, so the class project is covered. The same page says compliance screening counts as commercial use "even though it generates no revenue", and that any use inside a for-profit business requires a data licence. **For a real bank deployment, either buy a licence or switch rule 14 to the OFAC files, which are US-government public domain.** The prior plan's "skip OpenSanctions" should become "use it for the class, and swap to OFAC direct (or license it) for any real deployment". As with SAML-D, commit a fetch script rather than the bulk files.

## Conclusion

The question "which dataset?" was framed as a single choice, but it is really two jobs. The product needs a believable bank book, and the evaluation needs trustworthy labels. No public dataset does both, and the two strongest candidates fail in opposite directions. Pairing them avoids the trap the original plan was heading into: a self-built generator would have been both the bank book and the answer key, so every rule would have scored well against data designed to make it score well. The uncomfortable corollary applies even under this recommendation. **Branch-dependent logic (R3's cross-branch test and R1's "across branches") can only ever be proved on fixtures**, because every branch label is synthetic. The team should tell the role-played compliance manager this explicitly. It is exactly the kind of model-risk caveat a real BSA officer would expect to hear.

The biggest remaining uncertainty is Tide's youth. It is eight months old, has no third-party track record in these notes, and its account multiplicity and cash volume are unverified. Its MIT generator is the hedge: if the reference data is thin, the team can regenerate rather than abandon it, which is not possible with SAML-D or AMLworld. Download Tide HI and SAML-D today, run checks 1–6 before writing any rule code, and lock the choice by end of day.
