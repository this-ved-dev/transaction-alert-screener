# Public AML-labelled transaction datasets and generators other than SAML-D and IBM AMLworld (current to 2026-11-04)

Scope: I checked every candidate named in the brief plus anything I found on Hugging Face, Zenodo, figshare, Mendeley and GitHub. SAML-D and IBM AMLworld are left out because another researcher covers them. Unless a line says "Inference", it is something I checked against the primary page, the dataset API, or the file headers themselves. For TransXion, Tide and SA-SAML-D I read the CSV headers and the first rows directly.

Legend for the rule-fit columns: **Y** = the data supports the rule as written, **P** = partial (it needs a proxy, a unit conversion, or the semantics are weak), **N** = not supported. R1 = CTR > $10k cash per business day per customer. R2 = multi-day structuring. R3 = same-day / cross-branch structuring. R4 = dormant reactivation (≥180 days idle). R5 = pass-through (≥80% of inbound out within 72h). R6 = velocity against a 90-day baseline.

## Q0. Which credible candidates exist, and what does each contain? (comparison table + per-dataset notes)

### Takeaway
Seven candidates are credible and obtainable now: SynthAML, Tide, SA-SAML-D, TransXion, AMLNet v2, AMLGentex and IBM AMLSim. The JP Morgan AML set needs an email request. The FCA dataset is not public. None of them supports R1–R6 as written: none has transaction-level branch, none is in USD with US rails, and only SynthAML carries real alert dispositions. **Tide** (12 months, explicit cash DEPOSIT/WITHDRAWAL, entity→account ownership edges, country codes, CC BY 4.0) and **SA-SAML-D** (27 months, Cash Deposit/Withdrawal, counterparty country, KYC/risk fields, 22 typologies) fit the rules best. **SynthAML** is the only source of Report/Dismiss outcomes.

### Cited Findings

#### Comparison table

| Dataset (release / last update) | What it is | Size | History span | Customer↔account | Cash semantics | Branch / channel | Counterparty country | Labels / typologies | Alert dispositions | Licence | Access | US realism | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **SynthAML** (Sci Data, Sep 2023; files 2023-09-25) | Synthetic (SDV HMA1) fit to Spar Nord (Denmark) alerts and transactions | 20,000 alerts; >16M txns (934.6 MB CSV) | Up to 365 days before each alert; alerts dated 2020–2021 | None. AlertID only, no customer or account ID | Type ∈ {Card, Cash, International, Wire} × Entry ∈ {Credit, Debit} | None | None ("International" type only) | No typologies | **Yes: Report / Dismiss (~17% reported)** | **CC0** | Open download (figshare) | Low (DKK; amounts standardised log values) | N | N | N | P | P | P |
| **Tide** (arXiv Mar 2026; Zenodo v2 2026-06-08) | Configurable graph generator plus reference LI/HI datasets | ~36.6k nodes; ~7.6M txn edges per variant (~0.9 GB each) | 12 months (Jan–Dec 2025) | **Yes**: individual/business → account ownership edges (ownership_percentage) | **Yes**: TransactionType.DEPOSIT / WITHDRAWAL / PAYMENT / TRANSFER; cash accounts plus a global cash node | None | **Yes**: country_code, is_high_risk_country per node | is_fraudulent; 5 fraud patterns | No | Data CC BY 4.0; code MIT | Open download (Zenodo) / generate | Medium-low (EUR; global countries) | P | Y | N | P | Y | Y |
| **SA-SAML-D** (Zenodo v1.0.0 2026-09-17; GitHub) | Simulated South African retail bank in an extended SAML-D-style schema | 35,000 monitored accounts; 1,441,479 txns; 58 columns (CSV ~908 MB) | 2024-01-01 → 2026-03-31 (27 months); median 27 txns per account | Account_id profile carries the customer fields; no separate customer ID | **Yes**: Payment_type "Cash Deposit" / "Cash Withdrawal" plus Direction | No branch ID; profile-level Channel_preference (e.g. branch/ATM cash) | **Yes**: Counterparty_country, Jurisdiction_risk_tier | Is_laundering; 22 typology families (structuring, mule/pass-through, cross-border layering…) | No | Zenodo record CC BY 4.0 but files restricted there; GitHub repo has no licence file | GitHub Git LFS (appears downloadable) or regenerate with code | Low-medium (ZAR; SA rails) | P | Y | N | P | Y | Y |
| **TransXion** (KDD '26; arXiv Apr 2026; repo active to 2026-11-03) | LLM-guided simulation of normal activity plus template-free illicit subgraphs | 47,526 accounts; 3,029,170 txns; 4,641 illicit (0.153%) | 365 days (from 2025-01-01) | 1:1 (person_id ↔ bank_account_number); persons and merchants tables | "Cash" is a Payment Format on account→account edges (AMLworld-style), not deposit/withdrawal | Payment Format ∈ {Mobile, Card, Cash, Transfer, …}; bank ID | No (currency only; mostly CNY) | Is Laundering only (no typology column) | No | Code MIT; no separate data licence stated | Open (git clone with Git LFS, tx.csv 245 MB) | Low (CNY-dominated) | P | P | N | P | Y | Y |
| **AMLNet v2** (Zenodo 2026-07-07, modified 2026-08-11) | Knowledge-guided multi-agent generator (Griffith Univ.), AUSTRAC-style | ~1.09M txns; 10,000 customer accounts; 1,411 suspicious (0.13%) | 195 days (13 Oct 2025 – 27 Apr 2026) | Account = customer (nameOrig/nameDest) | CASH_OUT only (no cash-in type) | Rails: BPAY, OSKO, NPP, EFTPOS, DEBIT…; device (Mobile/Web/ATM) in v1 metadata JSON | City/state/postcode in metadata (Australia) | laundering_typology ∈ {structuring, layering, integration, normal} | No | **CC BY-NC 4.0** | Open download (Zenodo, 765 MB) | Low (AUD; Australian rails) | P | P | N | N/P | Y | Y |
| **AMLGentex** (arXiv Jun/Sep 2025; repo to 2026-02; HF 2025-09-25) | Agent-based generator (AI Sweden + Handelsbanken/Swedbank) built on AMLSim/PaySim lineage; 12 preset datasets | e.g. us_100K_difficult = 8.6M rows (699 MB); Sweden 1M variants ~78M rows | Configurable (steps) | Accounts only | Cash only for SAR accounts (prob_spend_cash) | bankOrig/bankDest; no branch or channel | City; "country" config property | isSAR, alertID, modelType; alert patterns: cycle, bipartite, stack, random, gather-scatter, scatter-gather | No (alertID = injected pattern) | Code Apache-2.0; HF data MIT | Open (HF) / generate | Unclear ("us_" preset has no card) | N | P | N | P | Y | Y |
| **IBM AMLSim** (generator; repo pushed 2025-09) | Agent-based generator; produces CSVs, no shipped labelled dump | Configurable | Configurable (steps) | **Yes**: acct_id plus dsply_nm (customer ID) on accounts.csv | None generated (only WIRE/TRANSFER) | **branch_id on accounts.csv** (account-level) | Optional country (Alpha-2) on accounts | is_sar, alert_id; fan_in, fan_out, cycle, … | No | Apache-2.0 | Generate (Java + Python) | Medium (optional US-style state/zip/ssn fields) | N | N | P | P | Y | Y |
| **J.P. Morgan AML synthetic** (planner-based simulator, 2020–21) | Action-state traces from AI planning-execution simulator | 523,877 txns; 16 countries; 20% "BAD" (per 2025 user paper) | Not stated | **Yes** via SET-OWNERSHIP-ACCOUNT actions | **Yes**: QUICK-DEPOSIT / PLACEMENT-CASH-IN, CASH-OUT / INTEGRATION-CASH-OUT | None (no channel) | Account country | GOOD/BAD per action | No | Non-commercial, per dataset terms | **Email request** (airdata.requests@jpmorgan.com) | Medium (USD values) | P | P | N | ? | P | ? |
| **FCA / Turing synthetic AML** (research note 2026-04-15) | Fully synthetic data built from anonymised UK retail bank data, with typologies injected | Not disclosed | Not disclosed | Linked profiles → accounts → txns | Not disclosed | Branch identifiers exist ("inconsistent") | High-risk-jurisdiction typology | Structuring, layering, circular, high-risk jurisdiction | Not disclosed | n/a | **FCA Digital Sandbox only** (sprint firms) | UK | – | – | – | – | – | – |
| **Electric Sheep Africa Nigeria AML alerts** (HF, modified 2026-04-14) | Alert table only, no transactions | 2,000,000 alerts | 2023–2024 dates seen | customer_id on alerts | n/a | n/a | n/a | alert_type (structuring, rapid_movement, high_risk_country, …) | **true_positive (bool), investigation_days** | Conflicting ("other" in YAML; "apache-2.0" in card body) | Open (HF parquet) | Low (NGN) | – | – | – | – | – | – |
| **Mendeley "Synthetic Banking Transaction Dataset with Multi-Pattern Fraud Labels"** (v2 2025-11-03) | Fraud-oriented synthetic transactions | 1M txns; 100k customers; 20k merchants | 1 year | Customer profiles (schema not verified) | Not mentioned | Not mentioned | Randomised coordinates | Card testing, ATO, "money laundering rings", geo anomalies | No | CC BY 4.0 | Open (Mendeley) | USD, but fraud-centric | ? | ? | N | ? | ? | ? |
| **Elliptic / Elliptic2** | Bitcoin graphs | Elliptic2: ~49M nodes, 196M edges, ~122K labelled subgraphs | n/a | n/a | n/a | n/a | n/a | Licit/suspicious subgraphs | No | – | Open | Crypto, so out of scope | N | N | N | N | N | N |

Sources for every row are in the per-dataset notes below.

#### SynthAML (Jensen et al., Scientific Data 2023)
- Built from Spar Nord, a systemically important Danish bank with about 440,000 clients. It contains 20,000 AML alerts and over 16 million transactions in two tables, synthesised with the Synthetic Data Vault (SDV) HMA1 model, version 0.14.1 — [Jensen et al. 2023, full text via Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML); [PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539331/); DOI [10.1038/s41597-023-02569-2](https://doi.org/10.1038/s41597-023-02569-2)
- Exact schema. `synthetic_alerts.csv`: **AlertID, Date, Outcome** (Outcome ∈ {Report, Dismiss}). `synthetic_transactions.csv`: **AlertID, Timestamp, Entry** (Credit/Debit), **Type** (Card/Cash/International/Wire), **Size**. The relation is one-to-many, alert → transactions — [Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- Underlying alerts are private (non-business) clients, raised from 1 Jan 2020 to 31 Dec 2021. For each alert, all of the client's transactions in the 365 days before the alert were collected. About 300 real clients had more than 4 alerts — [Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- Amount transformation. Each transaction is multiplied by U(0.98, 1.02) noise and clipped per type/entry (a lower clip hides the minimum, about 0.01 DKK). Size is "measured in log Danske Kroner (DKK) and standardized to have zero mean and unit variance". Alert dates are replaced by a random date in the same quarter, and transaction times are noised — [Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- About 17% of alerts are reported. The authors say this is "considerably more than in real AML settings" because of stratification. Synthetic cash transactions are over-represented compared with the real data — [Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- figshare collection [10.6084/m9.figshare.c.6504421.v1](https://doi.org/10.6084/m9.figshare.c.6504421.v1). Files: `synthetic_transactions.csv` (934,561,137 bytes) and `synthetic_alerts.csv` (505,481 bytes), posted 2023-09-25. **Both carry licence CC0** — [figshare API, collection 6504421](https://api.figshare.com/v2/collections/6504421/articles); [synthetic_transactions](https://springernature.figshare.com/articles/dataset/synthetic_transactions/22396057); [synthetic_alerts](https://springernature.figshare.com/articles/dataset/synthetic_alerts/22396054). The paper itself is CC BY 4.0.
- A 2026 arXiv paper on explainable LLM triage uses "SynthAML10" as its main evaluation dataset — [arXiv 2604.19755](https://arxiv.org/pdf/2604.19755). "SynthAML10" is most likely a citation artefact: SynthAML is reference 10 in the original paper, so "SynthAML 10" appears in its text. It is not a variant.

#### Tide (van den Beukel, Rožanec, Varbanescu, arXiv 2603.01863, 2 Mar 2026)
- A customisable generator. Node types: individuals, businesses, accounts, financial institutions. Edges are transactions or ownership. Transaction types are payment, transfer, withdrawal and deposit. Each individual and business has a dedicated cash account, and a global cash node is the source of deposits of unknown origin. The reference data covers 12 months (Jan–Dec 2025) with a base population of 8,000 individuals — [Tide paper (arXiv HTML)](https://arxiv.org/html/2603.01863v1)
- Fraud patterns: repeated overseas transfers, rapid fund movement, front business activity, synchronised transactions, U-turn transactions. There are also 7 counter-leakage background patterns plus everyday, high-value and salary activity. LI variant: 36,629 nodes, 7,642,030 edges, 0.10% illicit. HI variant: 36,653 nodes, 7,618,299 edges, 0.19% illicit — [Tide paper](https://arxiv.org/html/2603.01863v1)
- Verified headers (reference data). Nodes: `account_category, age_group, business_category, country_code, creation_date, currency, gender, incorporation_year, institution_id, is_fraudulent, is_high_risk_category, is_high_risk_country, name, node_id, node_type, number_of_employees, occupation, risk_score`. Transactions: `src, dest, edge_type, amount, currency, is_fraudulent, ownership_percentage, ownership_start_date, time_since_previous_transaction, timestamp, transaction_type`. The first fraudulent rows I saw are individual → account `TransactionType.DEPOSIT` of 9,200 / 9,300 / 9,700 EUR, which looks like sub-10k structured deposits — [Zenodo 18804069 files](https://zenodo.org/records/18804069)
- Zenodo record 18804069 (2026-02-27) is CC BY 4.0 and holds the nodes and transactions CSVs for LI and HI (~0.9 GB per transactions file). A newer record, 20591329 (2026-06-08, CC BY 4.0), adds `generated_edges_{LI,HI}.csv` — [Zenodo 18804069](https://zenodo.org/records/18804069); [Zenodo 20591329](https://zenodo.org/records/20591329)
- The generator code is MIT-licensed. Output files are `generated_nodes.csv`, `generated_edges.csv` and `generated_transactions.csv`, and `graph.yaml` sets scale and time span — [github.com/mntijn/Tide](https://github.com/mntijn/Tide)

#### SA-SAML-D: "A Context-Aware Synthetic South African Retail AML Dataset" (Nekhumbe, Rimer, Gololo; Zenodo 2026-09-17)
- 35,000 monitored Account_id profiles, 1,441,479 transaction rows, 58 public fields and 22 AML typology families: structuring, mule and rapid pass-through, cross-border layering, procurement/invoice fraud, shell ownership, Ponzi collections, narcotics cash, crypto off-ramping and others. Normal behaviour covers salary, debit orders, social grants, cash-intensive activity and remittances. The record ships a JSON schema, a 58-row data dictionary and code to regenerate the data. The observation window is 2024-01-01 → 2026-03-31. Zenodo shows licence CC BY 4.0, but "the record is publicly accessible, but files are restricted" — [Zenodo 22803333](https://zenodo.org/records/22803333)
- Verified columns (data dictionary): Is_laundering, Transaction_id, Time, Date, Account_id, Sender_account, Receiver_account, Counterparty_account, Direction, Amount, Payment_currency, Received_currency, Sender_bank_location, Receiver_bank_location, **Counterparty_country**, **Payment_type**, Social_grant_indicator, Social_grant_type, Credit_card_indicator, Procurement_payment_indicator, Virtual_asset_transaction_indicator, Counterparty_type, Cross_border_transaction, SADC_corridor_transaction, **Jurisdiction_risk_tier**, **Customer_type**, Employment_status, Employment_sector, Monthly_income_estimate, Province, Grant_linked, Public_sector_exposure, Procurement_vendor, **PEP_category**, Intermediary_account_flag, Virtual_asset_exposure, Connected_party_count, Profile_jurisdiction_risk_tier, **Laundering_type**, Public_sector_counterparty, Scenario_reference_key, Scenario_detail, Gender, Age, Education_level, Nationality_country, Urban_rural, Township_or_informal_settlement_flag, Financial_inclusion_segment, **Channel_preference**, Informal_business_flag, Business_registration_status, High_risk_sector_category, High_risk_person_type, Targeted_financial_sanctions_match, Adverse_media_flag, Typical_foreign_counterparty_country, **Account_open_date** — [SA_SAML_D_data_dictionary.csv](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/simulated_data/SA_SAML_D_data_dictionary.csv)
- Payment_type mix: Electronic Transfer 397,739; Card Payment 282,432; PayShap 220,822; **Cash Deposit 200,065** (10.93% suspicious); **Cash Withdrawal 174,365**; International Wire 95,546; RTC 70,510 — [payment_type_metrics.csv](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/insights/payment_type_metrics.csv)
- History density: mean 41.19, median 27, p95 127, max 220 transactions per Account_id. Suspicious share is 7.15% of transactions and 11.43% of accounts (4,000 of 35,000) — [dataset_overview.csv](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/insights/dataset_overview.csv)
- Channel_preference values include card-first, mobile-app-first, mixed cash/digital, branch/ATM cash, agent/cash/mobile and remittance-app. The authors warn that Laundering_type, Scenario_reference_key and Scenario_detail leak the label — [GitHub README](https://github.com/ColbertN/SA-AML-DATA-SIMULATION); [Zenodo 22803333](https://zenodo.org/records/22803333)
- The full CSV is in the GitHub repo as a Git LFS object (907,631,927 bytes). A range request to GitHub's LFS media endpoint returned HTTP 206, so it appears openly downloadable. The repo has no LICENSE file (GitHub API shows licence = none). Regeneration: `python scripts/main.py` (seed via `AML_SIM_SEED`) — [github.com/ColbertN/SA-AML-DATA-SIMULATION](https://github.com/ColbertN/SA-AML-DATA-SIMULATION)

#### TransXion (KDD '26; arXiv 2604.17420; Fudan / Peking Univ.)
- About 3M transactions among about 50,000 entities with demographic and behavioural attributes. 4,641 (0.153%) are illicit. Normal activity is simulated from persistent entity profiles, and illicit subgraphs are synthesised without fixed templates. LightGBM AP falls to about 0.031, and the authors report it is harder than AMLSim, AMLworld and SAML-D — [TransXion paper](https://arxiv.org/pdf/2604.17420)
- README: 47,526 accounts, 3,029,170 transactions, 365 days. Files: `data/tx.csv` (Git LFS, 245 MB), `data/person.csv`, `data/merchant.csv`. Licence files `txsim/LICENSE` and `aml-terraformer/LICENSE` are both MIT — [github.com/chaos-max/TransXion](https://github.com/chaos-max/TransXion)
- Verified headers. tx.csv: `Timestamp, From Bank, From Account, To Bank, To Account, Amount Received, Receiving Currency, Amount Paid, Payment Currency, Payment Format, Is Laundering` (this is the IBM AMLworld schema). The first rows start 2025-01-01 and show Payment Format ∈ {Mobile, Cash, Card, Transfer}, currencies mostly CNY plus CHF/AUD/EUR. person.csv: `person_id, bank_account_number, bank, person_age, person_education, person_gender, person_marital_status, person_occupation`. merchant.csv: `merchant_id, bank_account_number, bank, description, type, registered_capital, industry, operating_status, establishment_date, legal_representative_id` — [TransXion data files](https://github.com/chaos-max/TransXion/tree/main/data)
- The normal-transaction backbone is generated by "hierarchical LLM-guided simulation" (DeepSeek API by default, or local vLLM) — [txsim README](https://raw.githubusercontent.com/chaos-max/TransXion/HEAD/txsim/README.md)

#### AMLNet v1 / v2 (Huda et al., Griffith University)
- v2.0 ("AMLNet – Synthetic AML Benchmark Dataset, Version 2.0") was published on Zenodo on **2026-07-07** and modified 2026-08-11. It has about 1.09M transactions, 1,411 suspicious (about 0.13%), 10,000 generated customer accounts and about 11,000 graph nodes, over 195 days (13 Oct 2025 – 27 Apr 2026). Types: BPAY, CASH_OUT, DEBIT, EFTPOS, NPP, OSKO, PAYMENT, TRANSFER. Licence **CC BY-NC 4.0**. File `AMLNet_v2_transactions.csv` is 764.6 MB. The generator source is withheld "for security reasons" — [Zenodo 21237971 (v2)](https://zenodo.org/records/21237971)
- The 17 columns (v1 and v2): step, type, amount, category, nameOrig, nameDest, oldbalanceOrg, newbalanceOrig, isFraud, isMoneyLaundering, laundering_typology, metadata (JSON: timestamp, location, device_info, merchant_info, risk_indicators, layering), fraud_probability, hour, day_of_week, day_of_month, month — [Zenodo 21237971](https://zenodo.org/records/21237971); [Zenodo 16736515 (v1)](https://zenodo.org/records/16736515)
- v1 (2025-08-04): 1,090,173 records, 1,745 laundering-labelled. laundering_typology ∈ {structuring, layering, integration, normal}. Metadata lists payment_method (BSB_Account, CardNumber, PayID) and device types Mobile/Web/ATM, plus Australian city/state/postcode. v1 supersedes the deprecated record 16482144 — [Zenodo 16736515](https://zenodo.org/records/16736515); [AMLNet paper arXiv 2509.11595](https://arxiv.org/pdf/2509.11595)

#### AMLGentex (Östman et al., AI Sweden; arXiv 2506.13989)
- An open-source suite for generating configurable transaction data and benchmarking detection. The authors argue that existing datasets neglect partial observability, temporal dynamics, uncertain labels and class imbalance. It is calibrated to real transactions, and country-specific datasets are released on Hugging Face — [arXiv 2506.13989v2](https://arxiv.org/abs/2506.13989v2)
- The repo is Apache-2.0 (built with Handelsbanken and Swedbank). Accounts file: ACCOUNT_ID, AGE, SALARY, CITY, INIT_BALANCE. Label is `is_sar`. Cash is limited to SAR accounts (`prob_spend_cash`). Normal patterns: fan-in, fan-out, mutual, forward, periodical, single. Alert patterns: cycle, bipartite, stack, random, gather-scatter, scatter-gather. It also models label noise — [github.com/aidotse/AMLGentex](https://github.com/aidotse/AMLGentex)
- The HF org has 12 datasets: Sweden 100K/1M easy/difficult with drift variants, `us_100K_difficult` and `spain_100K_difficult`, all updated 2025-09-25 — [huggingface.co/AMLGentex](https://huggingface.co/AMLGentex)
- `us_100K_difficult`: MIT licence, 8,599,468 rows, 699 MB, empty README. Columns: step, type, amount, nameOrig, bankOrig, daysInBankOrig, phoneChangesOrig, oldbalanceOrig, newbalanceOrig, nameDest, bankDest, daysInBankDest, phoneChangesDest, oldbalanceDest, newbalanceDest, isSAR, alertID, modelType — [HF us_100K_difficult](https://huggingface.co/datasets/AMLGentex/us_100K_difficult)

#### IBM AMLSim (generator)
- Output schema. accounts.csv: acct_id, **dsply_nm (customer identifier)**, type, acct_stat, acct_rptng_crncy, prior_sar_count, **branch_id**, open_dt, close_dt, initial_deposit, tx_behavior_id, bank_id, plus optional first_name, last_name, street_addr, city, state, country (Alpha-2), zip, gender, birth_date, ssn, lon, lat. transactions.csv: tran_id, orig_acct, bene_acct, tx_type, base_amt, tran_timestamp (simulation step), is_sar, alert_id. There are also alert_accounts.csv and alert_transactions.csv. Only WIRE is actually generated (TRANSFER is the default label), so there is no cash type. Typologies: fan_in, fan_out, cycle, and others — [AMLSim wiki: data schema](https://github.com/IBM/AMLSim/wiki/Data-Schema-for-Input-Parameters-and-Generated-Data-Set)
- Licence Apache-2.0; repo last pushed 2025-09-17 — [github.com/IBM/AMLSim](https://github.com/IBM/AMLSim)

#### J.P. Morgan AI Research, AML synthetic dataset
- Described as "high level interactions" between a financial institution and legitimate and laundering clients, generated by an AI planning-execution simulator. Record format: Time step, Label (GOOD/BAD), Action, Arg1–Arg3. Example: `1/26/21 14:33 | GOOD | CREATE-ACCOUNT | COMPANY-57251 | CHECKING-57245 | JAPAN`. No download: you "Contact us to request access" at **airdata.requests@jpmorgan.com** with the data type, research purpose, name, affiliation and email. The datasets are "for public use for non-commercial purposes subject to the terms of each dataset's original license" — [JPMorganChase AI Research – Synthetic Data](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)
- The simulator paper lists observable actions including create-account, set-ownership-account, payroll, **quick-deposit, placement-cash-in, digital-deposit, cash-out, integration-cash-out**, pay-bill and move-funds-internationally. Account-owner and account-country are observable predicates. The paper states the observer sees a post-laundering withdrawal "as a cash-out action" — [Borrajo, Veloso, Shah, arXiv 2011.01826](https://arxiv.org/abs/2011.01826)
- A 2025 user paper reports 523,877 transactions from 16 countries, 20% labelled BAD, with account features ID, institution and country, and transaction type plus dollar value (mean $148,339). It also says the dataset lacks channel (online/in-person/mobile) and node features such as age and business type — [Chung et al., arXiv 2509.18499](https://arxiv.org/pdf/2509.18499)
- The legacy URL jpmorgan.com/technology/artificial-intelligence/initiatives/synthetic-data/anti-money-laundering now returns HTTP 404. The live page is on jpmorganchase.com — [JPMorganChase synthetic data](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)

#### UK FCA synthetic AML data (with Alan Turing Institute, Plenitude, Napier AI)
- Research note published 15 Apr 2026. The dataset is fully synthetic, created from real UK retail-banking data that was anonymised at source, with synthetic typologies injected (structuring, rapid movement across accounts, circular patterns, high-risk-jurisdiction transfers, plus variations). It is "being made available through the FCA Digital Sandbox as part of the upcoming data sprint, to firms who are developing transaction monitoring solutions" — [FCA project report PDF](https://www.fca.org.uk/publication/research-notes/synthetic-data-anti-money-laundering-project-report.pdf); [FCA research note page](https://www.fca.org.uk/cy/node/166196)
- The data links profiles, accounts and transactions. Known issues: "unusually high numbers of accounts associated with individual customers, inconsistent branch identifiers, and currency-related anomalies". On wider release the FCA says only "We're also considering broadening access… For now, our sandbox is the right environment" — [FCA project report PDF](https://www.fca.org.uk/publication/research-notes/synthetic-data-anti-money-laundering-project-report.pdf)
- Sprint applications closed 26 Apr 2026 — [FCA research note page](https://www.fca.org.uk/cy/node/166196). Secondary sources say the sprint ran 13 May – 8 Jul 2026 — [Plenitude Consulting](https://www.plenitudeconsulting.com/news-insights/fca-launches-synthetic-data-aml-solution-sprint) (search snippet only; page not fetched).

#### Electric Sheep Africa: Nigeria AML alerts (Hugging Face)
- 2,000,000 rows (124.6 MB parquet). Columns: alert_id, alert_date, customer_id, alert_type, alert_amount_ngn, risk_score, investigation_days, true_positive. Sample alert_types are high_risk_country, rapid_movement and structuring; sample dates are 2023–2024 — [HF datasets-server first-rows](https://datasets-server.huggingface.co/first-rows?dataset=electricsheepafrica/africa-synth-banking-aml-alerts-nigeria&config=default&split=train)
- The card says the data is "Parameterized from published SSA literature, not real observations." The licence conflicts: YAML says `other`, while the card body says "License: apache-2.0" — [HF dataset card](https://huggingface.co/datasets/electricsheepafrica/africa-synth-banking-aml-alerts-nigeria)

#### Mendeley Data: Synthetic Banking Transaction Dataset with Multi-Pattern Fraud Labels
- 1,000,000 transactions, 100,000 customers, 20,000 merchants, one year, all in USD, fraud rate about 0.5%. Patterns: card testing, account takeover, money-laundering rings, geographic anomalies. CC BY 4.0, v2 published 2025-11-03 (Hasan & Rashid, Daffodil International Univ.) — [Mendeley ktbthg777x v2](https://data.mendeley.com/datasets/ktbthg777x/2)

#### Ruled out or not usable
- **Elliptic2** (crypto): background graph of about 49M nodes and 196M edges, about 122K labelled subgraphs of Bitcoin clusters. Out of scope for a bank cash/wire rule engine — [arXiv 2404.19109](https://arxiv.org/abs/2404.19109v2)
- **HuieL/Launder-Bench** (HF, Oct 2026) is about code-provenance "laundering" by coding agents, not AML — [HF Launder-Bench](https://huggingface.co/datasets/HuieL/Launder-Bench)
- **"datasynth-banking"** (a Rust crate that a search snippet claimed has `structuring` and `pouch_activity` multi-branch cash typologies). crates.io returns "crate `datasynth-banking` does not exist" and docs.rs returns 404, so I could not verify it — [crates.io API](https://crates.io/api/v1/crates/datasynth-banking)
- **Open-source platforms.** Marble ships no documented demo dataset; the README mentions only an online interactive demo, and the GitHub licence shows NOASSERTION — [github.com/checkmarble/marble](https://github.com/checkmarble/marble). Jube (AGPL-3.0) has no bundled sample data that I could find — [Jube AML page](https://jube-home.github.io/aml-transaction-monitoring). Tazama provides ISO 20022 pacs.008 / pain.001 example payloads and a demo UI, but no labelled dataset — [tazama-lf/docs](https://github.com/tazama-lf/docs); [Tazama demo-ui](https://hub.docker.com/r/tazamaorg/demo-ui)
- **Hugging Face mirrors.** Several are re-uploads of IBM AMLworld (e.g. `eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans`, `qubit420/ibm-aml-LI-smaller`, `mgarg12378/IBM_AML`), which belong to the other researcher's scope — [HF dataset search API](https://huggingface.co/api/datasets?search=aml&limit=80)

### Inferences
- **SynthAML cannot run threshold rules (R1–R3).** Amounts are standardised log-DKK, and the scaling parameters are undisclosed, so dollar thresholds have no meaning. You could rescale with an assumed mean and standard deviation, but those numbers would be invented. Its 365-day window works for R4 and R6 shape logic, and its Credit/Debit × Cash fields map to cash-in and cash-out. Its real value is the Report/Dismiss outcome, which is the only bank-derived disposition label among public datasets.
- **Tide fits R1/R2/R5/R6 best** among the openly licensed options. It has explicit DEPOSIT and WITHDRAWAL types from individuals into their accounts, ownership edges for customer-level aggregation across accounts, 12 months of history, and country and high-risk-country flags for the stretch wire rule. Amounts are EUR, so a $10k CTR would need a currency assumption or a relabel. R4 needs at least 180 idle days inside a 12-month window, which is possible but probably rare unless injected.
- **SA-SAML-D has the richest KYC and risk context** (customer type, PEP, jurisdiction risk tier, counterparty country, account open date) and labelled cash deposits and withdrawals over 27 months. But its median of 27 transactions per account is thin for a 90-day baseline (R6). Amounts are in ZAR, and the Zenodo files are restricted, so the team would depend on the GitHub LFS copy, which has no licence file. That combination is a licensing ambiguity the team should record.
- **TransXion's "Cash" is AMLworld-style.** It is a payment format on an account-to-account edge, so it does not separate cash-in from cash-out cleanly. The person-to-account mapping is 1:1, so cross-account aggregation can't be tested.
- **AMLNet v2's 195-day window is too short for R4 as specified.** It has CASH_OUT but no cash-in. Its structuring typology is probably keyed to AUSTRAC's AUD 10,000 threshold-transaction reporting. That threshold comes from my background knowledge; I did not confirm it in an AMLNet source.
- **AMLGentex confines cash to SAR accounts.** Any cash rule would trivially pick up the labels, which inflates apparent rule performance.
- **The JP Morgan set probably has the most "bank-like" semantics** (cash-in and cash-out actions, ownership, country, USD values). But an email request with an unknown turnaround is risky against the Nov 11 deadline, seven days away.

### Gaps
- The SynthAML paper does not state how many distinct synthetic clients exist, and the data has no client ID, so multi-alert clients can't be linked.
- TransXion's paper typology list and any data-specific licence (as opposed to the MIT code licence) were not confirmed. I did not read the paper's dataset section in full.
- The JP Morgan dataset's time span, number of clients and accounts, and exact licence text are unknown, and so is the request turnaround. Those are only available by request.
- The AMLGentex `us_100K` preset has no documentation, so its calibration source and step-to-day mapping are unknown.
- I did not open the Mendeley dataset's column schema; the landing page does not list it.
- Frappe/ERPNext AML apps were not checked.
- Kaggle-only AML datasets from 2024–2026 were not searchable by script. Some HF uploads (e.g. `Ajhesh7/AntiMoneyLaundering`, `Hazarath/aml_sam_1/2`, `SuodhanJ6/Money_laundering`) were not inspected. They are probably SAML-D or IBM re-uploads, but that is unverified.

## Q1. Which candidate has the longest per-customer history, real cash deposit/withdrawal semantics, and customer↔account mapping?

### Takeaway
No one dataset wins on all three. **SA-SAML-D** has the longest window (27 months) plus explicit Cash Deposit and Cash Withdrawal, but its histories are sparse and there is no customer ID separate from the account. **Tide** combines 12 months, explicit DEPOSIT and WITHDRAWAL, and real entity→account ownership edges, which makes it the best all-round fit for R1/R2/R5/R6.

### Cited Findings
- SA-SAML-D: window 2024-01-01 → 2026-03-31 — [Zenodo 22803333](https://zenodo.org/records/22803333). Median 27, p95 127, max 220 transactions per account — [dataset_overview.csv](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/insights/dataset_overview.csv). Cash Deposit and Cash Withdrawal are distinct Payment_type values — [payment_type_metrics.csv](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/insights/payment_type_metrics.csv)
- Tide: 12 months (2025); deposit and withdrawal transaction types; dedicated cash accounts and a global cash node; ownership edges between entities and accounts — [Tide paper](https://arxiv.org/html/2603.01863v1). Transaction rows carry `ownership_percentage` and `ownership_start_date`, and fraudulent rows are individual → account DEPOSITs — [Zenodo 18804069](https://zenodo.org/records/18804069)
- TransXion: 365 days, 1:1 person ↔ account — [GitHub README and person.csv](https://github.com/chaos-max/TransXion)
- SynthAML: up to 365 days of a client's transactions per alert, Cash × Credit/Debit, no customer or account ID — [Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- AMLSim: dsply_nm (customer ID) is distinct from acct_id, but no cash type is generated — [AMLSim schema](https://github.com/IBM/AMLSim/wiki/Data-Schema-for-Input-Parameters-and-Generated-Data-Set)
- JP Morgan: SET-OWNERSHIP-ACCOUNT, QUICK-DEPOSIT, PLACEMENT-CASH-IN and CASH-OUT actions — [JPMC page](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data); [Borrajo et al.](https://arxiv.org/abs/2011.01826)
- AMLNet v2: 195 days, CASH_OUT only — [Zenodo 21237971](https://zenodo.org/records/21237971)

### Inferences
- Tide's `generated_nodes.csv` plus its ownership edges is the cleanest way to build a customer_id → account_id map, which R1 aggregation across accounts needs.
- In SA-SAML-D, Account_id looks like both the customer and the account. Customer-level aggregation across several accounts isn't possible without synthesising extra accounts.
- AMLSim's dsply_nm gives a customer ID, but someone would have to add cash transaction types to the generator. That is feasible but would take more than the time left.

### Gaps
- I did not check whether Tide individuals actually own more than one account in the reference data, or whether there is always one cash account plus one bank account. Confirming it needs a scan of the 0.9 GB edges file.
- I did not confirm whether SA-SAML-D Account_id values ever share a customer.

## Q2. Does any dataset include branch or channel?

### Takeaway
No public dataset has a **transaction-level branch ID**. Branch exists only as an account-level attribute in the AMLSim generator and in the non-public FCA dataset. Several datasets carry channel or payment-rail fields, but none can drive R3's cross-branch test without synthesising branch.

### Cited Findings
- AMLSim accounts.csv has `branch_id` (account-level); transactions.csv has none — [AMLSim schema](https://github.com/IBM/AMLSim/wiki/Data-Schema-for-Input-Parameters-and-Generated-Data-Set)
- The FCA dataset has branch identifiers, noted as "inconsistent", but is sandbox-only — [FCA report](https://www.fca.org.uk/publication/research-notes/synthetic-data-anti-money-laundering-project-report.pdf)
- SA-SAML-D: transaction-level Payment_type (Cash Deposit, Cash Withdrawal, Electronic Transfer, Card Payment, PayShap, International Wire, RTC). Profile-level Channel_preference includes "branch/ATM cash" — [data dictionary](https://raw.githubusercontent.com/ColbertN/SA-AML-DATA-SIMULATION/HEAD/results/simulated_data/SA_SAML_D_data_dictionary.csv); [README](https://github.com/ColbertN/SA-AML-DATA-SIMULATION)
- TransXion: Payment Format (Mobile, Card, Cash, Transfer observed) plus From Bank / To Bank — [tx.csv header](https://github.com/chaos-max/TransXion)
- AMLNet: rail types (BPAY/OSKO/NPP/EFTPOS/…), and device_info (Mobile/Web/ATM) in the metadata JSON — [Zenodo 16736515](https://zenodo.org/records/16736515)
- SynthAML: Type (Card/Cash/International/Wire) only — [Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- JP Morgan: no channel — [Chung et al. 2025](https://arxiv.org/pdf/2509.18499)

### Inferences
- For R3, the team will need to assign branch_id to cash transactions synthetically, for example by sampling from a customer's "home" branch plus a few others. Whichever base dataset they pick, they should document this as a data-augmentation assumption.

### Gaps
- I could not see the FCA dataset's actual field list.

## Q3. Does any dataset carry alert dispositions?

### Takeaway
Only **SynthAML** has real-bank-derived alert outcomes (Report vs Dismiss, about 17% reported). The Electric Sheep Nigeria table has a synthetic `true_positive` flag and `investigation_days`, but no linked transactions. Every other "alert" field is an injected-typology ID or a SAR label, not an investigator decision.

### Cited Findings
- SynthAML: Outcome ∈ {Report, Dismiss}, about 17% reported (higher than real-world rates) — [Jensen et al. 2023](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- Nigeria alerts: true_positive (bool), investigation_days, risk_score, alert_type — [HF first-rows](https://datasets-server.huggingface.co/first-rows?dataset=electricsheepafrica/africa-synth-banking-aml-alerts-nigeria&config=default&split=train)
- AMLSim and AMLGentex: alert_id / alertID identify injected pattern instances; is_sar / isSAR is the ground-truth label — [AMLSim schema](https://github.com/IBM/AMLSim/wiki/Data-Schema-for-Input-Parameters-and-Generated-Data-Set); [HF us_100K_difficult](https://huggingface.co/datasets/AMLGentex/us_100K_difficult)
- JP Morgan: GOOD/BAD per action, with no alerts or dispositions — [JPMC page](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)

### Inferences
- For the triage and audit UI, SynthAML's alert table could supply a realistic dismiss/report mix and alert-date seasonality. Its transactions can't be joined to customers or accounts in another dataset, though. A common pattern would be to generate alerts by running R1–R6 on Tide or SA-SAML-D, then seed synthetic dispositions at a rate the team chooses and documents.
- No dataset includes SAR narratives, investigator notes or audit trails.

### Gaps
- The Nigeria dataset's generation method and true-positive rate were not examined beyond the sample rows.

## Q4. Which licences allow an academic project with a role-played commercial client, and which require a request or agreement?

### Takeaway
Open with no request needed: SynthAML (CC0), Tide data (CC BY 4.0) and code (MIT), AMLGentex (Apache-2.0 code, MIT HF data), AMLSim (Apache-2.0), TransXion (MIT code; no data-specific licence stated), and Mendeley (CC BY 4.0). AMLNet is CC BY-NC 4.0, which fits coursework. SA-SAML-D is ambiguous: CC BY 4.0 on Zenodo, restricted files, and a GitHub copy with no licence. J.P. Morgan needs an email request under non-commercial terms. The FCA data is unavailable outside the Digital Sandbox.

### Cited Findings
- SynthAML files are CC0 — [figshare API](https://api.figshare.com/v2/collections/6504421/articles)
- Tide data CC BY 4.0 — [Zenodo 18804069](https://zenodo.org/records/18804069). Tide code MIT — [GitHub](https://github.com/mntijn/Tide)
- AMLGentex code Apache-2.0 — [GitHub](https://github.com/aidotse/AMLGentex). HF data MIT — [HF us_100K_difficult](https://huggingface.co/datasets/AMLGentex/us_100K_difficult)
- AMLSim Apache-2.0 — [GitHub](https://github.com/IBM/AMLSim)
- TransXion: txsim/LICENSE and aml-terraformer/LICENSE are MIT — [GitHub](https://github.com/chaos-max/TransXion)
- AMLNet v2 is CC BY-NC 4.0; "commercial use requires separate permission" — [Zenodo 21237971](https://zenodo.org/records/21237971)
- SA-SAML-D: Zenodo shows CC BY 4.0 with restricted files — [Zenodo 22803333](https://zenodo.org/records/22803333); the GitHub repo has no licence — [GitHub](https://github.com/ColbertN/SA-AML-DATA-SIMULATION)
- J.P. Morgan: request by email; "non-commercial purposes subject to the terms of each dataset's original license" — [JPMC page](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)
- FCA: Digital Sandbox only, for sprint firms — [FCA report](https://www.fca.org.uk/publication/research-notes/synthetic-data-anti-money-laundering-project-report.pdf)
- Mendeley dataset CC BY 4.0 — [Mendeley](https://data.mendeley.com/datasets/ktbthg777x/2)
- Nigeria alerts: licence metadata conflicts ("other" vs "apache-2.0") — [HF card](https://huggingface.co/datasets/electricsheepafrica/africa-synth-banking-aml-alerts-nigeria)

### Inferences
- A role-played client is fictional, so the project stays non-commercial academic work, and CC BY-NC (AMLNet) and the JP Morgan terms should be acceptable. This is my reading, not legal advice. If the MVP were later shown to a real bank, CC0, CC BY, MIT and Apache sources would avoid re-licensing.
- For SA-SAML-D, the safest course is to cite the Zenodo DOI (CC BY 4.0), use the GitHub copy or regenerate it with the code, and record the ambiguity in the project's data-provenance notes.

### Gaps
- I did not read the exact text of the JP Morgan dataset licence or request agreement, which is only seen after a request.
- TransXion has no explicit data licence separate from the code's MIT licence.

## Q5. Is anything US-specific?

### Takeaway
None of these datasets models US rails or rules. None has a CTR $10k cash threshold, FinCEN SAR/CTR semantics, ACH/Fedwire channels, or US branches. The closest US touches are AMLGentex's undocumented `us_100K_difficult` preset, the USD amounts in the JP Morgan and Mendeley sets, and AMLSim's optional US-style demographic fields.

### Cited Findings
- AMLGentex `us_100K_difficult` exists with an empty README — [HF](https://huggingface.co/datasets/AMLGentex/us_100K_difficult)
- J.P. Morgan: transaction "dollar value" with a mean of $148,339 across 16 countries — [Chung et al. 2025](https://arxiv.org/pdf/2509.18499)
- Mendeley: all transactions in USD — [Mendeley](https://data.mendeley.com/datasets/ktbthg777x/2)
- AMLSim: optional state, zip, ssn and country fields on accounts — [AMLSim schema](https://github.com/IBM/AMLSim/wiki/Data-Schema-for-Input-Parameters-and-Generated-Data-Set)
- Non-US anchoring: SynthAML is Denmark/DKK; AMLNet is Australia/AUSTRAC; SA-SAML-D is South Africa/ZAR; TransXion is mostly CNY; Tide is EUR; FCA is the UK — sources as cited in Q0.

### Inferences
- With any base dataset, the team will need a "US localisation" layer: convert or relabel currency to USD, map channels to cash-in-branch, ATM, ACH, wire and Zelle, add branch_id, and apply a US business-day calendar. The data cannot honestly be called US-realistic without that layer, and it should be documented as a limitation in the compliance-manager deliverable.

### Gaps
- No US-centric, publicly downloadable, AML-labelled transaction dataset from 2024–2026 turned up on HF, Zenodo, figshare or Mendeley. Kaggle was not searchable by script, so a Kaggle-only US dataset can't be ruled out.
