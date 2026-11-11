# SAML-D and IBM AMLworld: can either be the primary input for a US bank rule-based transaction-monitoring MVP (R1–R6)?

Research date: 2026-11-04. "Verified" means read directly from the paper, thesis, Kaggle metadata (Kaggle public API JSON), the IBM repo code, or printed notebook output / file headers. "Own analysis" means I computed it from a public 100,000-row, CDLA-licensed subset of AMLworld HI-Small that is committed to GitHub (`hugomagee/aml-transaction-monitoring-dbt/ci/sample`). That subset keeps every laundering row and hash-samples the rest, so ratios computed from it are biased toward laundering. I did not download either full dataset.

## Q1. SAML-D: exact schema, size, time span, accounts, label rate

### Takeaway
SAML-D is one 996 MB CSV (`SAML-D.csv`) with 9,504,852 rows and 12 columns. It runs from 2022-10-07 10:35:19 to 2023-08-23 10:57:12, about 320 calendar days, with 0.104% (9,873) of rows labelled suspicious. Rows are keyed only by 10-digit sender and receiver account numbers. There is no customer ID, no branch, no KYC field, and no transaction ID.

### Cited Findings
- **Exact columns, in order (verified from printed `df.columns` / dtypes):** `Time` (str, HH:MM:SS), `Date` (str, YYYY-MM-DD), `Sender_account` (int64), `Receiver_account` (int64), `Amount` (float64), `Payment_currency`, `Received_currency`, `Sender_bank_location`, `Receiver_bank_location`, `Payment_type` (str), `Is_laundering` (int64, 0/1), `Laundering_type` (str). No nulls and no duplicate rows. — [anjalirathod310 notebook output](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard); [Bhargav-Kulkarni84/aml_agent backend/data/format.txt](https://github.com/Bhargav-Kulkarni84/aml_agent); [MaxKots loader REQUIRED_COLUMNS](https://github.com/MaxKots/HSE_AML_MLOps_pipeline)
- Shape (9504852, 12). The first row is `10:35:19 2022-10-07`; the last is `10:57:12 2023-08-23`. A chronological 60/20/20 split gives train 2022-10-07 → 2023-04-16, validate → 2023-06-19, test → 2023-08-23. — [linhdanapril AML.ipynb output](https://github.com/linhdanapril/Anti-Money-Laundering-AML)
- Kaggle file: `SAML-D.csv`, 996,168,850 bytes. Version 1 ("Initial release") was 2023-12-20 and version 2 ("Update 2024-01-12") was 2024-01-12. v2 is current, with no later versions, and has about 10,261 downloads. — [Kaggle API metadata](https://www.kaggle.com/api/v1/datasets/view/berkanoztas/synthetic-transaction-monitoring-dataset-aml); [Kaggle API file list](https://www.kaggle.com/api/v1/datasets/list/berkanoztas/synthetic-transaction-monitoring-dataset-aml)
- The Kaggle description says: "9,504,852 transactions, of which 0.1039% are suspicious" and "The dataset is an updated version compared to the paper." — [Kaggle dataset page](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml)
- The ICEBE 2023 paper (Table I) reports different figures for the earlier generation: 9,411,384 transactions, 749,507 accounts and 11,658 SAR transactions (0.124%). — [Oztas et al. 2023, Bournemouth eprint](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf); [IEEE Xplore 10356193](https://ieeexplore.ieee.org/document/10356193)
- The PhD thesis describes the released data as 9,504,852 transactions, "0.104% suspicious … precisely 9,873 entries", 676,912 unique sender and receiver accounts, 18 locations, 13 currencies and 7 payment types. — [Oztas PhD thesis, Bournemouth](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)
- `Is_laundering` value_counts are 0: 9,494,979 and 1: 9,873. There are 292,715 unique senders and 652,266 unique receivers. — [anjalirathod310 notebook output](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard)
- Accounts are "random 10-digit bank account numbers … unique identifiers for each account". Each account is assigned a set of normal typologies, and suspicious accounts also get normal typologies. — [Oztas thesis §4.3](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)
- The data is a multi-bank, UK-focused view, not a single bank's: "focusing on the United Kingdom, as opposed to creating a singular bank viewpoint… achieved by slightly modifying the generator." — [Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)

### Inferences
- About 320 days of history covers the R4 180-day dormancy window and the R6 90-day baseline. It does not cover a full 12-month prior average for R4's "10× prior 12-month average" branch, so that branch must fall back to the available history.
- Some printed account IDs have 9 digits (e.g. 287305149, 940337377). The likely cause is int64 dropping leading zeros. Read the account columns as strings.
- There is a single `Amount` column even when `Payment_currency` ≠ `Received_currency`. This suggests amounts are in one common unit, probably GBP given the UK focus, but nothing I read confirms it (see Gaps).

### Gaps
- The amount currency unit is not documented in the paper, thesis or Kaggle text.
- The calendar or weekend distribution is unverified: I did not confirm whether weekend or holiday volumes differ.
- The account-to-bank mapping is unclear. Thesis nodes have a "bank id", but no bank-ID column was released.

## Q2. SAML-D: payment types, locations, currencies

### Takeaway
SAML-D has explicit `Cash Deposit` and `Cash Withdrawal` payment types, which suits R1–R3. Its geography is a UK-domestic bank population plus 17 foreign locations, several of them high-risk. A US scenario needs the "UK" home market remapped to "US".

### Cited Findings
- **The 7 `Payment_type` values (verified):** `Cash Deposit`, `Cash Withdrawal`, `Cross-border`, `Cheque`, `ACH`, `Credit card`, `Debit card`. — [anjalirathod310 notebook unique() output](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard); [sid2002-N trained_columns.txt one-hot names](https://github.com/sid2002-N/Anti_Money_Laundering_Webapp)
- The paper names 6 types ("credit card, debit card, cash, ACH, cross-border, and cheque"). The released data splits cash into deposit and withdrawal. — [Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf); [Oztas thesis §5.3](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)
- **18 bank locations (from one-hot dummies):** Albania, Austria, France, Germany, India, Italy, Japan, Mexico, Morocco, Netherlands, Nigeria, Pakistan, Spain, Switzerland, Turkey, UAE, UK, USA. — [sid2002-N trained_columns.txt](https://github.com/sid2002-N/Anti_Money_Laundering_Webapp); the count of 18 is confirmed by the [Oztas thesis](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)
- **13 currencies:** Albanian lek, Dirham, Euro, Indian rupee, Mexican Peso, Moroccan dirham, Naira, Pakistani rupee, Swiss franc, Turkish lira, UK pounds, US dollar, Yen. — [sid2002-N trained_columns.txt](https://github.com/sid2002-N/Anti_Money_Laundering_Webapp); the count of 13 is confirmed by the [Oztas thesis](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)
- The paper names Mexico, Turkey, Morocco and the UAE as high-risk countries, sourced from the UK National Risk Assessment 2020 and FATF June 2023. Currencies "align with location features, with mismatched instances adding complexity." — [Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)
- Sample rows show `Cash Deposit` with distinct sender and receiver accounts (row 0: 8724731955 → 2769355426, UK→UK, GBP, `Normal_Cash_Deposits`). They also show `Cross-border` UK→UAE with Received_currency Dirham. — [anjalirathod310 notebook head()](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard)

### Inferences
- Even cash deposits are recorded as a sender-account → receiver-account edge. Before coding R1–R3, decide which side is the customer. For deposits it is probably the receiver; for withdrawals, probably the sender. Check with `df[df.Payment_type.str.startswith('Cash')].groupby('Payment_type')[['Sender_account','Receiver_account']].nunique()` and by testing whether either side is a small set of sentinel "cash" accounts.
- Counterparty country is available as `Receiver_bank_location` / `Sender_bank_location`. This is enough for the high-risk-jurisdiction stretch rule once the team maps UK to "domestic US".
- "Wire" does not exist. Map `Cross-border` to international wire and `ACH` to ACH. Domestic wires cannot be told apart from other transfers.

### Gaps
- I did not see a published frequency table for `Payment_type` or locations.
- Whether a "cash" sender is a real account or a placeholder is not documented.

## Q3. SAML-D: normal and suspicious typologies; how Structuring and Smurfing are generated

### Takeaway
SAML-D has 28 typologies, 11 normal and 17 suspicious, and every row carries its typology label. That is ideal for per-rule precision and recall. However, neither the paper nor the thesis gives the generation parameters for Structuring or Smurfing. The reporting threshold used (UK, GBP, or a $10k analogue) is not documented anywhere I could find.

### Cited Findings
- **The 17 suspicious `Laundering_type` labels, with counts among `Is_laundering==1` (total 9,873):** Structuring 1,870; Cash_Withdrawal 1,334; Deposit-Send 945; Smurfing 932; Layered_Fan_In 656; Layered_Fan_Out 529; Stacked Bipartite 506; Behavioural_Change_1 394; Bipartite 383; Cycle 382; Fan_In 364; Gather-Scatter 354; Behavioural_Change_2 345; Scatter-Gather 338; Single_large 250; Fan_Out 237; Over-Invoicing 54. — [anjalirathod310 notebook value_counts](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard); same counts reproduced in [Sentinel-AML knowledge_base/samld_typologies.md](https://github.com/Mayank2142/Sentinel-AML)
- **The 11 normal labels:** `Normal_Small_Fan_Out`, `Normal_Fan_Out`, `Normal_Fan_In`, `Normal_Group`, `Normal_Cash_Withdrawal`, `Normal_Cash_Deposits`, `Normal_Periodical`, `Normal_Plus_Mutual`, `Normal_Mutual`, `Normal_Foward` (misspelling in the source), `Normal_single_large`. — [Sentinel-AML samld_typologies.md](https://github.com/Mayank2142/Sentinel-AML); a partial list including `Normal_Foward` is in the [anjalirathod310 notebook unique() output](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard)
- **Paper definitions, suspicious typologies:**
  - From IBM/AMLSim: Fan-Out, Fan-In, Cycle, Bipartite, Stacked Bipartite, Scatter-Gather, Gather-Scatter, with randomised parameters.
  - Author-added: Layered Fan-In and Layered Fan-Out, where values change by 10–20% per layer. These represent layering.
  - Others: Structuring, Smurfing, Over-Invoicing, Deposit-Send, Cash Withdrawal, Single Large Transaction, Behaviour Change 1 and 2.
  - **Deposit-Send:** "an account first deposits cash into the bank and then within a short period of time sends it to another account. The transaction amount is generally below the reporting threshold limit, with the second transaction having an increased chance of being sent to a high-risk country."
  - **Suspicious Cash Withdrawal:** low-value withdrawals linked to forced sexual servitude.
  - **Behavioural Change 1:** the main account of a "Normal Group" structure starts transacting with new accounts.
  - **Behavioural Change 2:** the same, but with the new accounts in high-risk locations.
  - **Normal Group:** a main account that transacts with core accounts more often than with regular accounts.
  - The paper says it draws on 15 graph structures, shared across typologies with overlapping parameters to make detection harder.
  - — [Oztas et al. 2023 §IV.A](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)
- **Normal typologies from IBM:** Single Transaction, Fan-Out, Fan-In, Mutual, Forward, Periodical. New ones: Cash Withdrawal, Cash Deposit, Small Fan-out, Mutual Plus, Normal Group. — [Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)
- **Structuring and Smurfing:** the only description is that both were "frequently mentioned" in interviews with 8 AML experts and are considered the most prevalent placement-stage techniques. The text cites literature, not parameters. — [Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf); the thesis repeats the same wording ([Oztas thesis §4.4.1](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf))
- Parameters were "drawn from" AML specialist input (an industrial collaborator; co-author G. Aksu, Danske Bank London), the literature, and existing datasets. — [Oztas et al. 2023 §V](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)
- A third-party rule engine calibrated on SAML-D labels uses structuring = amount in [8,000, 10,000) with ≥3 near-threshold transactions in 7 days, and smurfing = ≥3 senders in 48 h totalling ≥10,000. These are that project's choices, not documented generator parameters. — [Sentinel-AML tools/rule_engine.py](https://github.com/Mayank2142/Sentinel-AML)

### Inferences
- The UK has no CTR-style cash reporting threshold, but the Deposit-Send text still refers to "the reporting threshold limit". The generator probably uses some round threshold near 10,000 in the Amount unit, but this is unverified. Before trusting R2 and R3 recall on SAML-D, profile the `Structuring` and `Smurfing` rows: their amounts, `Payment_type` mix (cash or not), transactions per account, and day spans. This takes about one pandas cell on the full CSV.
- Typology labels are per transaction. A suspicious account can also carry normal-labelled rows, so measure alert-level recall at the account × window level (for example, "alert covers ≥1 labelled row of type X").
- Rule-to-label mapping (inference):
  - R2 and R3: Structuring, Smurfing
  - R5: Deposit-Send, Layered_Fan_*, Gather-Scatter, Scatter-Gather
  - R6: Behavioural_Change_1/2
  - Stretch high-risk jurisdiction: Behavioural_Change_2, Deposit-Send
  - Funnel or mule: Fan_In, Layered_Fan_In, Smurfing
  - R1: Single_large (partial)
  - R4: no label

### Gaps
- No source gives the Structuring or Smurfing amount bands, window lengths, cash or non-cash mix, or currency.
- I found no journal version of the dataset paper. The thesis lists a later model paper (Tab-AML, IEEE CAI 2025) that uses SAML-D but does not re-document the generator.

## Q4. SAML-D: generator code, licence, versions, known data-quality issues

### Takeaway
The generator is not public. The data is CC BY-NC-SA 4.0, which permits non-commercial academic coursework. ShareAlike applies only if the team redistributes an adapted dataset. The main quality issues are the paper-versus-release mismatch, the absent customer, branch and KYC layer, and minor label and ID formatting quirks.

### Cited Findings
- The Kaggle licence is "CC BY-NC-SA 4.0", and the dataset asks users to cite Oztas et al., ICEBE 2023, pp. 47–54, doi 10.1109/ICEBE59045.2023.00028. — [Kaggle API metadata](https://www.kaggle.com/api/v1/datasets/view/berkanoztas/synthetic-transaction-monitoring-dataset-aml); [Kaggle page](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml)
- Under CC BY-NC-SA 4.0 you may share and adapt, subject to Attribution, NonCommercial ("A commercial use is one primarily intended for commercial advantage or monetary compensation") and ShareAlike (adaptations must be distributed under the same licence). — [CC BY-NC-SA 4.0 deed](https://creativecommons.org/licenses/by-nc-sa/4.0/)
- The paper is © 2023 IEEE and contains no separate data licence statement. The thesis lists that publication as "Licence: © 2023 IEEE". — [Oztas thesis publication list](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)
- Generator availability: neither the paper nor the thesis links any code. The thesis says only that the dataset "is publicly available on Kaggle". The GitHub API returned 404 for a `berkanoztas` user, and repo search for "SAML-D generator" returned nothing. — [Oztas thesis](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf); GitHub API search (no URL; negative result)
- Paper versus release: Kaggle has 9,504,852 rows, 9,873 suspicious and 7 payment types; the paper has 9,411,384 rows, 11,658 SAR transactions and 6 payment types. — [Kaggle](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml); [Oztas et al. 2023 Table I](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)
- The label `Normal_Foward` is misspelled in the source. — [Sentinel-AML samld_typologies.md](https://github.com/Mayank2142/Sentinel-AML)
- `Laundering_type` is widely treated as a leakage column for ML (dropped from features). — [MaxKots loader LEAKAGE_COLUMNS](https://github.com/MaxKots/HSE_AML_MLOps_pipeline); a 2026 arXiv paper says each SAML-D row carries `Is_laundering` and a 17-value `Laundering_type` that it excludes from inputs (seen in search snippet only) — [arXiv 2608.15447](https://arxiv.org/pdf/2608.15447)
- The authors' own limitations: synthetic data that "will not fully capture" real-world intricacy, parameters that may not embody all scenarios, and typologies that do not cover all strategies. — [Oztas et al. 2023 §VI](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)

### Inferences
- Licence for this team: a 4-student academic assignment with a role-played (fictional) bank is non-commercial, so using SAML-D is permitted. Obligations:
  - Credit the dataset, cite the paper, and link the licence.
  - If the team publishes the enriched dataset (with synthetic customers and branches), it must also be CC BY-NC-SA 4.0 with change notes.
  - The team's code can carry any licence.

  The licence objection in the current plan is therefore weak for this context. It would matter only if the MVP or the data were later used for commercial purposes. This is not legal advice.
- Without generator code, the team cannot regenerate SAML-D with US settings or a customer layer. All adaptation must be post-processing.

### Gaps
- I did not read Kaggle discussion threads for SAML-D, because the pages are JavaScript-rendered and the API exposes no discussions. User-reported issues there are unknown.

## Q5. IBM AMLworld: variants (rows, accounts, days, illicit ratio, files)

### Takeaway
AMLworld has six independent datasets, HI/LI × Small/Medium/Large. Small covers 10 primary days, Medium 16 and Large 97. The paper's laundering counts for the Small variants disagree with the Kaggle table and with actual file counts. Use the Kaggle and observed numbers.

### Cited Findings
- **Kaggle table, verbatim values:**

  | Variant | Date range (2022) | Days | Accounts | Transactions | Laundering | Laundering rate |
  |---|---|---|---|---|---|---|
  | HI-Small | Sep 1–10 | 10 | 515K | 5M | 5.1K | 1 in 981 |
  | LI-Small | Sep 1–10 | 10 | 705K | 7M | 4.0K | 1 in 1,942 |
  | HI-Medium | Sep 1–16 | 16 | 2,077K | 32M | 35K | 1 in 905 |
  | LI-Medium | Sep 1–16 | 16 | 2,028K | 31M | 16K | 1 in 1,948 |
  | HI-Large | Aug 1 – Nov 5 | 97 | 2,116K | 180M | 223K | 1 in 807 |
  | LI-Large | Aug 1 – Nov 5 | 97 | 2,064K | 176M | 100K | 1 in 1,750 |

  The variants are independent (Small is not a subset of Medium), and a 60/20/20 chronological split is recommended. — [Kaggle dataset page](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)
- The arXiv/NeurIPS paper's Table 4 gives the same figures except HI-Small laundering = **3.6K**. — [Altman et al., arXiv 2306.16424 (NeurIPS 2023 D&B)](https://arxiv.org/html/2306.16424)
- Actual counts:
  - HI-Small: 5,078,345 transactions, 5,177 laundering. This matches 1/981, so the paper's 3.6K is likely an error. — [hugomagee README / eda_notes](https://github.com/hugomagee/aml-transaction-monitoring-dbt); also 5,078,345 / 5,177 in [Oztas et al. 2023 Table I](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf)
  - LI-Small: 6,924,049 transactions and 3,565 laundering (not 4.0K). — [hugomagee README](https://github.com/hugomagee/aml-transaction-monitoring-dbt)
- Kaggle is at version 8 (2025-07-08), 41.6 GB in total, with about 57,788 downloads. It has 18 files: `{HI,LI}-{Small,Medium,Large}_Trans.csv`, `_Patterns.txt` and **`_accounts.csv`**.
  - `_Trans.csv` sizes: HI-Small 475.7 MB, LI-Small 650.4 MB, HI-Medium 3.03 GB, LI-Medium 2.98 GB, HI-Large 17.05 GB, LI-Large 16.74 GB.
  - `_accounts.csv` sizes: HI-Small 34 MB, LI-Small 47 MB, Medium and Large about 142–148 MB.

  The Kaggle description text still lists only 12 files (Trans and Patterns). — [Kaggle API metadata](https://www.kaggle.com/api/v1/datasets/view/ealtman2019/ibm-transactions-for-anti-money-laundering-aml); [Kaggle API file list](https://www.kaggle.com/api/v1/datasets/list/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)
- LI-Large transaction counts by format (paper Table 5): Cheque 69.7M, Credit Card 49.9M, ACH 21.7M, Cash 18.1M, Reinvestment 7.3M, Wire 6.3M, Bitcoin 3.6M. — [Altman et al.](https://arxiv.org/html/2306.16424)
- The README points to "NEW AND IMPROVED DATA ON KAGGLE" and to older Box data from an early generator version. — [IBM/AML-Data README](https://github.com/IBM/AML-Data)

### Inferences
- The only variant with enough history for any long-window rule is Large, at 97 days and about 17 GB per CSV. That is impractical on student laptops without DuckDB or Polars streaming, and still too short for 180-day dormancy.

### Gaps
- I did not establish exactly when the `_accounts.csv` files were first added. All current files show 2025-07-08 creation in v8.

## Q6. IBM AMLworld: Trans.csv schema, Payment Format values, currencies and conversion

### Takeaway
`Trans.csv` has 11 columns with minute-level timestamps. It contains bank and account IDs for both sides, separate paid and received amounts and currencies, 7 payment formats and a 0/1 label. There are 15 currencies with effectively fixed exchange rates, and no FX table is shipped.

### Cited Findings
- **Header, verbatim:** `Timestamp,From Bank,Account,To Bank,Account,Amount Received,Receiving Currency,Amount Paid,Payment Currency,Payment Format,Is Laundering`. Pandas renames the duplicate as `Account.1`. — own read of the [CDLA sample `HI-Small_Trans.csv.gz`](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample); [boutouile docs/data.md schema](https://github.com/boutouileabdelkrim-pixel/aml-network-intelligence)
- `Timestamp` format is `'%Y/%m/%d %H:%M'`. IBM's formatter builds the account key as `From Bank` + account string. — [IBM/Multi-GNN format_kaggle_files.py](https://github.com/IBM/Multi-GNN/blob/main/format_kaggle_files.py)
- **Payment Format values:** `ACH`, `Bitcoin`, `Cash`, `Cheque`, `Credit Card`, `Reinvestment`, `Wire`. — own analysis of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample); [Altman et al. Table 5](https://arxiv.org/html/2306.16424)
- **HI-Small full-file laundering by format:** ACH 4,483 of 600,797 rows; Cash 108 of 490,891; Bitcoin 56 of 146,091; Reinvestment 0 of 481,056; Wire 0 of 171,855. So about 87% of laundering rows are ACH. In LI-Small, laundering rows are ACH 2,611, Cash 124, Bitcoin 110 and Wire 0. — [hugomagee docs/eda_notes.md](https://github.com/hugomagee/aml-transaction-monitoring-dbt)
- **The 15 currencies:** Australian Dollar, Bitcoin, Brazil Real, Canadian Dollar, Euro, Mexican Peso, Ruble, Rupee, Saudi Riyal, Shekel, Swiss Franc, UK Pound, US Dollar, Yen, Yuan. — own analysis of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample); "15 currencies and no FX table" — [hugomagee README](https://github.com/hugomagee/aml-transaction-monitoring-dbt)
- Cross-currency rows occur only in ACH (1,064) and Wire (10) in the sample. In full HI-Small there are 72,170 cross-currency rows, and no same-currency rows where the two amounts differ. — own analysis of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample); [hugomagee eda_notes](https://github.com/hugomagee/aml-transaction-monitoring-dbt)
- **Implied units per USD**, from Amount Received / Amount Paid on USD cross-currency rows, are near-constant:

  | Currency | Units per USD | Currency | Units per USD |
  |---|---|---|---|
  | Euro | 0.8534 | Mexican Peso | 21.143 |
  | UK Pound | 0.7742 | Brazil Real | 5.6465 |
  | Yen | 105.40 | Ruble | 77.804 |
  | Yuan | 6.6976 | Rupee | 73.444 |
  | Swiss Franc | 0.9150 | Saudi Riyal | 3.7511 |
  | Canadian Dollar | 1.3193 | Shekel | 3.3770 |
  | Australian Dollar | 1.4128 | Bitcoin | about 0.0001 |

  — own analysis of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample)
- The paper says only that AMLworld generates transactions in "dollars, euros, yuan, yen, bitcoin, and more". It gives no FX method. — [Altman et al.](https://arxiv.org/html/2306.16424)

### Inferences
- **Conversion:** derive a fixed USD rate per currency from the data itself, as above, and convert `Amount Paid` with the payment-currency rate (debit side) and `Amount Received` with the receiving-currency rate (credit side). One rule-based project does this with a seed table named `fx_rates_approx`. — [hugomagee lineage](https://github.com/hugomagee/aml-transaction-monitoring-dbt)
- There is no counterparty-country column. Bank names embed countries (e.g. "Japan Bank #0", "France Bank #51", "Switzerland Bank #11", "Israel Bank #19", "India Bank #11"), alongside US-sounding names such as "National Bank of Laramie" and "Arbor Savings Bank". Parsing the bank name, or using currency as a proxy, could give a rough counterparty country. This is inferred from `accounts.csv` values in the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample), not documented.

### Gaps
- IBM's official FX table is not documented. The rates above are empirical.

## Q7. IBM AMLworld: accounts file (account → entity) and Patterns.txt format

### Takeaway
`*_accounts.csv` maps every account to a bank and to an **Entity ID**, which works as a customer ID. Entities can hold several accounts across banks. `Patterns.txt` holds `BEGIN/END LAUNDERING ATTEMPT - <TYPE>` blocks of Trans-format rows for 8 AMLSim-style patterns, but covers only part of the laundering.

### Cited Findings
- **`accounts.csv` header, verbatim:** `Bank Name,Bank ID,Account Number,Entity ID,Entity Name`. Example row: `Arbor Savings Bank,1,800042CB0,8000488C0,Partnership #37`. — own read of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample)
- **Sample statistics (own analysis):**
  - 102,174 accounts belong to 77,695 entities; 9,139 entities have more than one account, and 9,094 have accounts at more than one bank.
  - Entity Name prefixes: Partnership, Sole Proprietorship, Corporation, Country, Individual (86 only) and Direct.
  - One entity ("Country #1") holds 1,424 accounts across many banks.
  - The sample covers 4,329 banks.

  — [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample)
- Full HI-Small accounts table: 518,581 rows and 518,573 distinct account numbers. Every transaction account appears in it. Four account numbers occur at two banks, so the key is (bank, account). Bank IDs are zero-padded in Trans and Patterns (`010`) but not in accounts (`10`), and must be normalised before joining. — [hugomagee README / eda_notes](https://github.com/hugomagee/aml-transaction-monitoring-dbt)
- The paper says each person or company "owns one or more bank accounts directly and via subsidiaries", possibly at several banks, and that shell companies may bank elsewhere. — [Altman et al.](https://arxiv.org/html/2306.16424)
- **`Patterns.txt` format, verbatim:**

  ```
  BEGIN LAUNDERING ATTEMPT - FAN-OUT:  Max 16-degree Fan-Out
  2022/09/01 00:06,021174,800737690,012,80011F990,2848.96,Euro,2848.96,Euro,ACH,1
  …
  END LAUNDERING ATTEMPT - FAN-OUT
  ```

  The header variants are:
  - `FAN-IN: Max N-degree Fan-In`
  - `GATHER-SCATTER: Max N-degree Fan-In`
  - `CYCLE: Max N hops`
  - `RANDOM: Max N hops`
  - `BIPARTITE`, `SCATTER-GATHER` and `STACK`, with no suffix

  — own read of the [CDLA sample `HI-Small_Patterns.txt.gz`](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample)
- HI-Small has 370 pattern blocks. Counts: CYCLE 54, GATHER-SCATTER 51, BIPARTITE 49, FAN-OUT 48, SCATTER-GATHER 44, STACK 43, RANDOM 41, FAN-IN 40. — own analysis of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample), which keeps all pattern blocks
- Coverage: Patterns.txt rows cover 3,209 of 5,177 laundering rows (62.0%) in HI-Small and 1,023 of 3,565 (28.7%) in LI-Small. — [hugomagee eda_notes](https://github.com/hugomagee/aml-transaction-monitoring-dbt); "not all laundering in the data follows one of these 8 patterns" — [Kaggle page](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)
- **Pattern definitions:**
  - Fan-out: one vertex sends to ≥2 vertices. Fan-in: one vertex receives from ≥2.
  - Gather-scatter: a fan-in then a fan-out on the same vertex. Scatter-gather: a fan-out to intermediaries, then a fan-in to another vertex.
  - Cycle: funds return to the origin. Random: a cycle-like path that does not return.
  - Bipartite: from a set of input accounts to a set of output accounts. Stack: bipartite with an extra layer.
  - Placement comes from 9 crime sources: extortion, loan sharking, gambling, prostitution, kidnapping, robbery, embezzlement, drugs, smuggling.

  — [Altman et al. §3.2](https://arxiv.org/html/2306.16424)

### Inferences
- AMLworld already provides the customer↔account layer R1–R3 need. Entity names are mostly firms (Partnership, Sole Proprietorship, Corporation), so the population does not look like a retail-bank customer base, and there is no KYC tier, occupation or residency.
- There is no structuring, CTR or dormancy pattern in the typology set. AMLworld labels are graph-flow laundering, not cash-placement typologies.

### Gaps
- The meaning of the "Country #N" and "Direct #N" entity types is not documented.
- The entity-type distribution of the full file is unverified; my figures come from the laundering-heavy sample.

## Q8. IBM AMLworld: Cash semantics, tail days, licence, known issues

### Takeaway
"Cash" in AMLworld is a two-party payment edge between different accounts, usually at different banks. It is not a deposit or withdrawal at a branch. Each variant ends with a sparse tail of days that are mostly laundering. Data is CDLA-Sharing-1.0, which is permissive and has no non-commercial clause.

### Cited Findings
- In the sample, of 11,842 `Cash` rows only 20 are self-transfers (same bank and account) and 190 are same-bank. Examples include `0211/809DC13E0 → 0028690/80A879840, 74.97 AUD, Cash` and `070/100428660 → 0012803/8104709E0, 3,207,725.99 USD, Cash`. — own analysis of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample)
- Self-transfers are about 11.6% of HI-Small rows, mostly `Reinvestment` (591,212 self-transfers, 11 of them laundering). There are 9 exact duplicate rows. — [hugomagee README / eda_notes](https://github.com/hugomagee/aml-transaction-monitoring-dbt); in the sample, all 6,341 Reinvestment rows are self-transfers (own analysis)
- **Tail days:** Kaggle says the date range is the "primary" period and that "there are some transactions after the specified date period, and that those transactions are all laundering" (Kaggle discussion 427517). — [Kaggle page](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml); [discussion 427517, not read](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml/discussion/427517)
- Observed in HI-Small: days 11–18 (Sep 11–18) contain 1,108 transactions, of which 655 (59%) are laundering, against 0.10% before. The file actually spans 18 days. — [hugomagee README](https://github.com/hugomagee/aml-transaction-monitoring-dbt); in the sample, Sep 11 has 232 of 236 laundering and Sep 18 has 8 of 9 (own analysis)
- In the sample, weekend days have about half the volume of weekdays (Sat Sep 3: 4,249; Sun Sep 4: 4,549; Sat Sep 10: 4,322, against about 10k on weekdays). Monday Sep 5, 2022 (US Labor Day) shows normal weekday volume (9,914). — own analysis of the [CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample)
- **Licence:** the data is under CDLA-Sharing-1.0; the GitHub repository is Apache-2.0. — [IBM/AML-Data README](https://github.com/IBM/AML-Data); [Kaggle API metadata](https://www.kaggle.com/api/v1/datasets/view/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)
- CDLA-Sharing-1.0 terms:
  - You may use, modify and publish.
  - Published Data or Enhanced Data must stay under the same agreement, carry change notices and keep attribution.
  - Results (outputs of computational use) carry no restrictions.
  - No commercial-use restriction may be added.
  - Data is provided as-is.

  — [CDLA-Sharing-1.0 text](https://cdla.dev/sharing-1-0/)
- Labels are complete, which the paper presents as an advantage over real data. — [Altman et al.](https://arxiv.org/html/2306.16424)

### Inferences
- Cash-based rules R1–R3 can run if the team defines "cash-in" for the receiving entity and "cash-out" for the paying entity on `Cash` rows. The semantics are artificial: there is no teller channel, the amounts reach millions, and the counterparty is a named account.
- The tail days must be cut (keep Sep 1–10 for Small) or explicitly flagged. Otherwise any velocity or new-activity rule gets artificial precision.
- AMLworld volume shows a weekly cycle but no US holiday effect in this sample, so a US business-day calendar must be imposed anyway.

### Gaps
- I did not read Altman's full reply in discussion 427517, because the page is JavaScript-rendered.

## Q9. Fit to R1–R6 (verdicts) and what must be synthesised

### Takeaway
SAML-D is the better primary input. It has about 320 days of history, explicit cash deposit and withdrawal, counterparty country, and per-row typology labels that map to R2, R3, R5, R6 and the stretch rules. It lacks a customer, branch and KYC layer, so the team must synthesise that, along with a US calendar and USD framing. AMLworld has a real customer (entity) layer but only 10–18 days of history in Small. Its "cash" is a transfer and its laundering is about 87% ACH graph flows, so R4 and R6 cannot fire and R1–R3 have almost no matching labels. Keep AMLworld as a secondary benchmark, mainly for R5 and the funnel and fan-in stretch rules.

### Cited Findings
- **Basis for the SAML-D verdicts:** history 2022-10-07 → 2023-08-23 ([linhdanapril notebook](https://github.com/linhdanapril/Anti-Money-Laundering-AML)); Cash Deposit and Cash Withdrawal types ([anjalirathod310 notebook](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard)); labels Structuring 1,870, Smurfing 932, Deposit-Send 945, Behavioural_Change_1/2 394/345 ([same](https://github.com/anjalirathod310/aml-transaction-monitoring-dashboard)); accounts only, no customer ([Oztas thesis](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)).
- **Basis for the AMLworld verdicts:** 10/16/97 primary days ([Kaggle](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml)); Entity ID in accounts.csv ([CDLA sample](https://github.com/hugomagee/aml-transaction-monitoring-dbt/tree/main/ci/sample)); only 108 of 490,891 Cash rows labelled in HI-Small, with Wire laundering = 0 ([hugomagee eda_notes](https://github.com/hugomagee/aml-transaction-monitoring-dbt)).
- **Third-party rule results on AMLworld HI-Small**, at the account level, validate split days 8–18, base rate 0.73%:
  - Structuring rule: precision 1.31%, recall 4.4%
  - Pass-through: precision 2.85%, recall 1.6%
  - Fan-in/out: precision 7.15%, recall 4.9%
  - Cycles: precision 25%, recall 2.9%
  - A gradient-boosted model reached 24.5% precision at equal volume. The README calls the rules "a baseline, not a detector".

  — [hugomagee docs/rule_results.md](https://github.com/hugomagee/aml-transaction-monitoring-dbt)

### Inferences
**Verdict table.** These verdicts are my judgement from the cited schema facts.

| Rule | SAML-D | AMLworld (HI-Small; Large noted) |
|---|---|---|
| R1 CTR candidate, cash >$10k/business day per customer | **Fires weakly.** Cash Deposit and Withdrawal exist, but only per account: customer aggregation across accounts and branches needs synthetic grouping. No CTR label; use for volume only. | **Fires weakly.** Entity ID allows true cross-account and cross-bank aggregation, but "Cash" is a transfer with multi-million amounts, so CTR semantics are artificial. No label. |
| R2 multi-day structuring (5-day / 30-day) | **Fires meaningfully, pending verification.** Structuring (1,870) and Smurfing (932) labels exist, and the 30-day window fits in 320 days. Confirm that Structuring rows are cash and fall in the $2k–9,999 band. | **Fires weakly.** The 5-day window fits; the 30-day window cannot run in Small or Medium. No structuring typology, and only 108 labelled cash rows. |
| R3 same-day / cross-branch | **Fires weakly.** The same-day ≥2 cash in [$9k, $10k] branch can be tested per account. The cross-branch branch cannot without synthetic branches; `Payment_type` can stand in for "channel". | **Fires weakly.** Same-day can be tested; the bank in accounts.csv can stand in for branch (9k+ multi-bank entities). Labels are almost irrelevant. |
| R4 dormant reactivation (≥180 days) | **Fires weakly.** 180 days of dormancy fits only for reactivation in about the last 140 days. The 12-month average is unavailable, there is no dormancy label, and normal typologies are periodic, so few dormant accounts are likely. | **Cannot fire.** History is 10–18 days (Large: 97). |
| R5 rapid pass-through (≥80% out in 72h) | **Fires meaningfully.** Deposit-Send is exactly cash-in then quick send-out, often cross-border. Layered fan-in/out and gather-scatter are also labelled. | **Fires meaningfully, structurally.** Gather-scatter and fan patterns fit, but third-party precision is about 2–3% at about 1.6–2.6% recall. |
| R6 velocity spike (7d vs trailing 90d) | **Fires meaningfully.** A 90-day baseline is available after about Jan 2023; Behavioural_Change_1/2 are partial ground truth. | **Cannot fire** in Small or Medium (no 90-day baseline); at best marginal in Large (97 days). |
| Stretch: high-risk-jurisdiction wires | **Fires meaningfully.** Receiver location includes Mexico, Turkey, Morocco, UAE, Nigeria, Pakistan and Albania; labels Behavioural_Change_2 and Deposit-Send. | **Fires weakly.** No country column; parse it from bank names or currency. |
| Stretch: new beneficiary | **Fires meaningfully.** Behavioural_Change_1. | **Fires weakly.** Only 10 days to establish who is "new". |
| Stretch: funnel / mule burst | **Fires meaningfully.** Fan_In, Layered_Fan_In, Smurfing. | **Fires meaningfully.** FAN-IN, GATHER-SCATTER, SCATTER-GATHER. |
| Stretch: round-dollar | **Fires**, label-agnostic (amounts have cents). | **Fires**, label-agnostic. |

**What SAML-D needs synthesised.** My rough estimate is 1–2 person-days, with all logic seeded and deterministic:
1. **Customer↔account grouping.** Assign about 1–3 accounts per customer. Keep every account in a suspicious typology inside one customer, or one ring of linked customers, so labels stay coherent. Only accounts that appear as the "own bank" side need customers (see item 6).
2. **Branch per cash transaction.** Give each customer a home branch (for example 8–15 branches) and send a random share of cash transactions to other branches. Optionally bias Structuring and Smurfing rows toward multiple branches so R3's cross-branch branch has positives; disclose any label-aware injection.
3. **KYC tier.** Draw from typology membership with noise, or uniformly. Avoid leaking the label.
4. **US business-day calendar.** Map `Date` to US business days with a US federal holiday calendar (e.g. pandas `USFederalHolidayCalendar`). Roll weekend and holiday postings to the next business day.
5. **USD amounts.** Either relabel `Amount` as USD 1:1, which preserves the generator's threshold-relative structure (recommended), or convert from GBP. Conversion shifts all bands and can break the Structuring signal.
6. **Geography and own-bank view.** Remap location `UK` to "US/domestic" and the original `USA` to "foreign". Recast `Cross-border` as international wire. Pick which accounts belong to "our bank": either all UK-located accounts, or a sampled subset to mimic a $1–5B regional bank.

**What AMLworld would need.** It needs most of the same, minus customers, plus:
- FX conversion
- Cash re-semantics
- Tail-day trimming
- Country parsing from bank names
- Above all, more history

Generating more history is not feasible without IBM's generator. The IBM README points to the AMLworld generator only via the paper, and offers much larger datasets on request (ealtman@us.ibm.com) — [Kaggle page](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml). AMLworld therefore cannot be the primary input for R4 or R6.

### Gaps
- No one has published how SAML-D's Structuring and Smurfing rows distribute across amount and day. This single fact decides whether R2 and R3 "fire meaningfully"; verify it in the first hour of work.
- Whether dormant accounts exist at all in SAML-D is unverified.

## Q10. How published papers and GitHub projects adapt these datasets for rule-based monitoring (vs GNN/ML)

### Takeaway
Peer-reviewed work on both datasets is almost entirely ML or GNN. I found no paper that reports rule-baseline precision and recall for either dataset. A handful of GitHub portfolio projects do run rule engines: one on AMLworld with entity, FX and tail handling, and one that calibrates rules on SAML-D labels. Their approach is a useful template.

### Cited Findings
- **The original papers use ML only.** SAML-D: SVM, Naive Bayes, Decision Tree and Random Forest with a 70-15-15 stratified split on a subset. The paper notes that rules-based TM produces about 95% false positives. — [Oztas et al. 2023](https://eprints.bournemouth.ac.uk/40982/1/Full_IEEE_Dataset_Conference_Paper%20%284%29.pdf). AMLworld: GNN baselines (Multi-GNN), with code under Apache-2.0. — [Altman et al.](https://arxiv.org/html/2306.16424); [IBM/Multi-GNN](https://github.com/IBM/Multi-GNN)
- The follow-up SAML-D work is transformer-based (Tab-AML, IEEE CAI 2025). — [Oztas thesis publication list](https://eprints.bournemouth.ac.uk/41326/1/OZTAS%2C%20Berkan_Ph.D._2024.pdf)
- A web search found no published rule-baseline precision or recall for AMLworld or SAML-D. — [search result: AMLNet arXiv 2509.11595](https://ar5iv.arxiv.org/html/2509.11595) (unrelated generator); negative result
- **Rule-based adaptation of AMLworld** (dbt + DuckDB; written by an AI coding assistant under the owner's direction, per the README):
  - Five SQL rules: structuring, pass-through, fan-in/out, cycles and baseline anomaly.
  - Alert unit is account-day; labels are per split; a tune split (days 1–7) and a validate split (days 8–18).
  - Approximate FX seed table, normalised bank IDs, and the tail days handled explicitly.
  - Patterns.txt is used for diagnosis only, never as the label.
  - LI-Small serves as an untouched out-of-sample check.

  — [hugomagee/aml-transaction-monitoring-dbt](https://github.com/hugomagee/aml-transaction-monitoring-dbt)
- **Hybrid project:** SAML-D is used "only as a calibration and validation source" for a rule engine, with its labels mapped to rule families: Structuring, Smurfing, Cash_Withdrawal and Single_large → rule engine; layered and bipartite → graph tools; Behavioural_Change → statistical or ML. Detection runs on AMLworld HI-Small. — [Mayank2142/Sentinel-AML](https://github.com/Mayank2142/Sentinel-AML)

### Inferences
- **Recommended pattern for this team:**
  - Make SAML-D (post-processed with synthetic customers, branches, KYC tier and a US calendar) the primary input, scoring per-rule precision and recall against `Laundering_type`.
  - Report AMLworld HI-Small results for R5 and the funnel rule only, using Entity ID as the customer and trimming to Sep 1–10, as an "external benchmark" slide.
  - Borrow the hugomagee evaluation design: account-day alert unit, base-rate comparison, tune/validate split, and recall by typology.
- Expect low absolute precision on either dataset. Third-party AMLworld rules run at 1–7% precision, which is in line with real TM programmes and worth framing as such for the compliance-manager role-play.

### Gaps
- I found no academic paper evaluating rules (as opposed to ML) on SAML-D, so expected rule precision there is unknown.
- The GitHub projects cited are unreviewed portfolio work and should be treated as secondary evidence.
