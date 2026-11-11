# Unlabelled bank-ledger datasets for realistic background activity, and US calibration sources (as of 2026-11-04)

Scope: public transaction datasets without AML labels that could serve as "normal" background for a rule-based TM MVP (R1 CTR >$10k cash per business day per customer; R2 multi-day structuring $2k–$9,999; R3 same-day cross-branch structuring; R4 dormant ≥180 days then ≥$5k; R5 pass-through within 72h; R6 velocity vs trailing 90-day baseline), plus public US sources for calibrating a synthetic generator. Requirements checked for each dataset: customer ID distinct from account ID (1 customer : N accounts), cash flag or channel, branch or location, posting date, ≥180–365 days of history per customer, KYC attributes.

Method note: Kaggle metadata (title, licence, description, file list and sizes) was read from Kaggle's public API (`https://www.kaggle.com/api/v1/datasets/view/<owner>/<slug>` and `/datasets/list/<owner>/<slug>`), which answered without login. No dataset files were downloaded. Column headers were confirmed from Hugging Face mirrors' dataset viewer, university course pages, or third-party write-ups, as noted against each.

## 1. Berka / PKDD'99 Czech Financial dataset

### Takeaway
This is the only candidate that is a real, anonymised retail-bank ledger. It has about 6 years of account-level postings, a cash-deposit code (`VKLAD`), a cash-withdrawal code (`VYBER`), balances, and a branch district per account. It does not fit the MVP's data model natively: there is no channel (teller/ATM/night drop) and no branch on each transaction, amounts are in 1990s CZK, and the client↔account relation runs the wrong way. Each client has exactly one account, and some accounts have two clients (owner + disponent). For R1 and R3 the team would have to synthesise the multi-account customers, the channel and the per-transaction branch.

### Cited Findings
**Provenance and counts**
- Prepared by Petr Berka and Marta Sochorova from a Czech bank. It covers "over 5,300 bank clients with approximately 1,000,000 transactions", plus close to 700 loans and nearly 900 credit cards. — [UNC Charlotte ITCS6265 Berka domain page](https://webpages.uncc.edu/mirsad/itcs6265/group1/domain.html)
- Rows per table: account 4,500; client 5,369; disp 5,369; order (permanent orders, debits only) 6,471; trans 1,056,320; loan 682; card 892; district 77. — [UNC Charlotte domain page](https://webpages.uncc.edu/mirsad/itcs6265/group1/domain.html)
- Relationships: "One client can have more accounts, more clients can manipulate with single account; clients and accounts are related together in relation 'disposition'". At most one loan per account; more than one card can be issued per account. — [UNC Charlotte domain page](https://webpages.uncc.edu/mirsad/itcs6265/group1/domain.html)
- Time span: transactions run January 1993 to December 1998 (a secondary catalogue; no primary statement was retrieved). — [AI4FCF workshop open-datasets list, via search](https://sites.google.com/view/ai4fcf/open-datasets)

**`trans` columns** — [UNC Charlotte transaction schema](https://webpages.uncc.edu/mirsad/itcs6265/group1/transaction_domain.html)
- `trans_id`, `account_id`, `date` (YYMMDD), `type`, `operation`, `amount`, `balance` (balance after the transaction), `k_symbol`, `bank` (partner bank, a unique two-letter code), `account` (partner account).
- `type`: `PRIJEM` = credit; `VYDAJ` = debit (withdrawal).
- `operation`: `VYBER KARTOU` = credit card withdrawal; `VKLAD` = credit in cash; `PREVOD Z UCTU` = collection from another bank; `VYBER` = withdrawal in cash; `PREVOD NA UCET` = remittance to another bank.
- `k_symbol`: `POJISTNE` insurance payment; `SLUZBY` payment of statement; `UROK` interest credited; `SANKC. UROK` sanction interest if negative balance; `SIPO` household payment; `DUCHOD` old-age pension; `UVER` loan payment.

**Other tables**
- `account`: `account_id`, `district_id` (location of the branch), `date` (creation, YYMMDD), `frequency` (`POPLATEK MESICNE` monthly, `POPLATEK TYDNE` weekly, `POPLATEK PO OBRATU` statement after each transaction). — [UNC Charlotte account schema](https://webpages.uncc.edu/mirsad/itcs6265/group1/account_domain.html)
- `client`: `client_id`, `birth_number` (YYMMDD for men; YYMM+50DD for women, so it encodes both date of birth and sex), `district_id` (client address). — [UNC Charlotte client schema](https://webpages.uncc.edu/mirsad/itcs6265/group1/client_domain.html)
- `district` (demographics): A1 district_id, A2 name, A3 region, A4 inhabitants, A5–A8 municipality counts by size, A9 number of cities, A10 urban ratio, A11 average salary, A12/A13 unemployment 1995/1996, A14 entrepreneurs per 1,000, A15/A16 crimes 1995/1996. — [UNC Charlotte demographic schema](https://webpages.uncc.edu/mirsad/itcs6265/group1/demographic_domain.html)

**Hosting and access**
- CTU Prague Relational Learning Repository: "Financial" database, 8 tables, 1,090,086 rows, 55 columns, 78.8 MB. It is served from a public MariaDB at `relational.fel.cvut.cz:3306` (user `guest`, password `ctu-relational`, published on the page) and can be exported to CSV or SQL. Three versions exist: Financial (Jan Motl; adds foreign keys and splits birth date and gender), Financial_ijs and Financial_std. The page states no licence or terms. — [CTU relational repository, Financial](https://relational.fel.cvut.cz/dataset/Financial)
- Kaggle mirror `marceloventura/the-berka-dataset`, labelled "CC0: Public Domain" by the uploader. Files: account.csv, card.csv, client.csv, disp.csv, district.csv, loan.csv, order.csv, trans.csv (69.4 MB). It credits the UNC Charlotte page as its source. — [Kaggle API metadata for marceloventura/the-berka-dataset](https://www.kaggle.com/datasets/marceloventura/the-berka-dataset)
- Other mirror: data.world `lpetrocelli/czech-financial-dataset-real-anonymized-transactions`, cited in a 2024 paper (contents not verified). — [arXiv 2402.11066](https://arxiv.org/pdf/2402.11066)
- The original PKDD'99 page (lisp.vse.cz/pkdd99, later sorry.vse.cz/~berka) is effectively dead. A 2016 forum post says the page no longer worked and points to `http://lisp.vse.cz/pkdd99/DATA/data_berka.zip` (unverified). My fetch of sorry.vse.cz failed with a DNS error. — [SAP community thread, via search](https://archive.sap.com/discussions/thread/3882406)
- Documentation reference: P. Berka, "Guide to the Financial Data Set", PKDD 2000 Discovery Challenge, Lyon, pp. 87–92. — [VŠFS publication record](https://is.vsfs.cz/publication/1423/en/Guide-to-the-Financial-Data-Set/Berka)
- English translation of code values: none of the mirrors ships an officially translated file. Translations of the codes (as above) appear in course pages and community notebooks. One preprocessing write-up notes that k_symbol values were "translated for ease of use". — [UNC Charlotte transaction preprocessing](https://webpages.uncc.edu/mirsad/itcs6265/group1/transaction_preprocessing.html)
- A Hugging Face text-to-SQL set built on Berka (`yifanmai/czech_bank_qa`) uses lowercase table names `client`, `disp`, `account`, `district`, which matches the CTU schema. — [HF yifanmai/czech_bank_qa](https://huggingface.co/datasets/yifanmai/czech_bank_qa)

### Inferences
- **Customer↔account mapping is effectively 1:1 from the client side.** disp has 5,369 rows, the same as client. Every client is by definition someone who can operate an account, so each client appears in exactly one disposition and has one account. The 5,369 − 4,500 = 869 extra rows are second clients (disponents) on shared accounts. The MVP's "one customer, many accounts" aggregation (R1 across accounts) is therefore never exercised by Berka natively. The team would have to merge or link accounts into synthetic customers.
- **Cash flag: yes, but coarse.** `operation = VKLAD` gives cash-in and `VYBER` gives cash-out. `VYBER KARTOU` (card withdrawal) is ambiguous (ATM or POS) and should not count as teller cash without an assumption. Teller, ATM, night drop, wire and ACH cannot be distinguished. `PREVOD Z UCTU` / `PREVOD NA UCET` are interbank credit transfers (a wire/ACH proxy) with a partner `bank` code and `account`.
- **Branch: account-level only.** `account.district_id` is the "location of the branch" (77 districts). There is no per-transaction branch, so R3 (same-day cross-branch) needs a synthetic branch per cash transaction.
- **History is ample for R4 and R6.** Accounts opened 1993–1997 with postings to 1998 give most accounts more than 1 year of history. The bank-initiated `k_symbol` values `UROK` (interest) and `SLUZBY` (statement fee) are useful for R4: they let the team test "no customer-initiated activity" while bank-generated postings continue.
- **KYC: thin.** Sex and date of birth (decoded from `birth_number`), home district and district socioeconomics. No occupation, business type or risk rating, and no business customers are flagged.
- **Currency and era rescaling.** Amounts are 1993–1998 Czech koruna (CZK). A raw FX conversion would not give US-plausible amounts, because 1990s Czech wage levels were far below US levels; district A11 average salary gives the local wage scale. A defensible approach is distribution or quantile mapping: rescale each customer's amounts by the ratio of a US income or flow benchmark to the Berka district's A11 average salary, or map Berka's cash-deposit amount quantiles onto quantiles calibrated from US sources (Section 9). Then shift dates by a constant offset, e.g. +30 years to 2023–2028, keeping weekday alignment by shifting a multiple of 7 days. State the method explicitly in the deliverable.
- **Licence is unclear.** It is widely used in academia for 25+ years and the CTU repository serves it publicly. The Kaggle "CC0" label is the uploader's assertion, not the data owner's. For a classroom MVP this is low risk; cite Berka (2000) and the CTU repository.

### Gaps
- Primary confirmation of the exact date range (min and max of `trans.date`) and of per-table date ranges: the original PKDD'99 page was unreachable.
- The distribution of `VKLAD` amounts, how many cash postings exceed any rescaled $10k-equivalent threshold, and how many accounts have ≥180-day gaps in customer-initiated activity. These would need a download and a profile.
- No official licence or terms of use found.
- The data.world mirror's contents and translation status were not verified.

## 2. IBM TabFormer / Altman synthetic credit-card transactions (Kaggle `ealtman2019/credit-card-transactions`)

### Takeaway
This is a large, US-located, multi-decade synthetic card ledger with a rich users (KYC-like) file. It is a card-purchase stream, not a deposit-account ledger: it has no cash deposits, no branches and no account-vs-customer split beyond cards per user. It is only usable as background spend noise for R6. It cannot drive R1–R5.

### Cited Findings
- Kaggle: "more than 20 million transactions generated from a multi-agent virtual world simulation performed by IBM". It covers "2000 (synthetic) consumers resident in the United States, but who travel the world" and "decades of purchases", with multiple cards per consumer. Licence: Apache 2.0, quoted in the description. — [Kaggle API metadata, ealtman2019/credit-card-transactions](https://www.kaggle.com/datasets/ealtman2019/credit-card-transactions)
- Kaggle files: `credit_card_transactions-ibm_v2.csv` (2.35 GB), `sd254_cards.csv` (487 KB), `sd254_users.csv` (224 KB), `User0_credit_card_transactions.csv` (1.9 MB). — [Kaggle API file list](https://www.kaggle.com/datasets/ealtman2019/credit-card-transactions)
- GitHub IBM/TabFormer: about 24M records with 12 fields in `./data/credit_card/transactions.tgz` (git-lfs), also at `https://ibm.box.com/v/tabformer-data`. The repo licence is Apache-2.0. — [GitHub IBM/TabFormer](https://github.com/IBM/TabFormer); [data/credit_card dir](https://github.com/IBM/TabFormer/tree/main/data/credit_card)
- The TabFormer paper says "24 million transactions from 20,000 users", with label column `isFraud?`. This contradicts Kaggle's 2,000 users. — [Padhi et al., arXiv 2011.01843 (PDF text)](https://arxiv.org/pdf/2011.01843)
- Schema (third-party loaded copy):
  - transactions: `User, Card, Year, Month, Day, Time, Amount, Use Chip, Merchant Name, Merchant City, Merchant State, Zip, MCC, Errors?, Is Fraud?`
  - users: `Person, Current Age, Retirement Age, Birth Year, Birth Month, Gender, Address, Apartment, City, State, Zipcode, Latitude, Longitude, Per Capita Income - Zipcode, Yearly Income - Person, Total Debt, FICO Score, Num Credit Cards`
  - cards: `CARD INDEX, Card Brand, Card Type, Card Number, Expires, CVV, Has Chip, Cards Issued, Credit Limit, Acct Open Date, Year PIN last Changed, Card on Dark Web`
  - Reported totals: 24,386,900 transactions and 6,146 cards.
  — [yawetse data-protection-exploration write-up](https://yawetse.github.io/data-protection-exploration/docs/examples/understanding-sample-datasets/credit-card-transactions)
- Generator background: Altman, "Synthesizing Credit Card Transactions" (2019), describes a "virtual world" combining domain knowledge and technical approaches. — [arXiv 1910.03033](https://arxiv.org/abs/1910.03033)

### Inferences
- Customer↔card (1:N) exists (User → Card), which is a loose analogue of customer → accounts. There is no deposit account, no balance and no cash-in.
- I did not confirm the `Use Chip` values in fetched text. Community usage suggests swipe/chip/online card-present indicators; this is a card channel, not teller/ATM/wire.
- Merchant City/State/Zip are merchant locations, not the bank's branches.
- Currency: USD (US consumers), per the Kaggle description. Era: decades ending around 2020 (exact years not verified).
- Fit: good for an R6 velocity baseline on spend. Poor for R1–R5 (no cash, no branch, no credits or pass-through).

### Gaps
- The exact year range and the `Use Chip` / `Errors?` value sets were not verified.
- The 2,000 vs 20,000 user discrepancy between Kaggle and the paper is unresolved. It may reflect different releases.

## 3. Sparkov-generated "Credit Card Transactions Fraud Detection" (Kaggle `kartik2112/fraud-detection`)

### Takeaway
This is a 2-year (2019–2020) synthetic US card-purchase set: 1,000 customers, 800 merchants, CC0. It has customer address and DOB but no cash, no branches and no deposit accounts. It does not fit R1–R5. The Sparkov generator itself (MIT) is a reusable, profile-driven template for a custom generator.

### Cited Findings
- Simulated legitimate and fraud transactions, 1 Jan 2019 – 31 Dec 2020, "credit cards of 1000 customers doing transactions with a pool of 800 merchants", generated with Brandon Harris's Sparkov. Licence CC0: Public Domain. Files `fraudTrain.csv` (351 MB) and `fraudTest.csv` (150 MB). — [Kaggle API metadata, kartik2112/fraud-detection](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
- Columns (Hugging Face mirror viewer): `Unnamed: 0, trans_date_trans_time, cc_num, merchant, category, amt, first, last, gender, street, city, state, zip, lat, long, city_pop, job, dob, trans_num, unix_time, merch_lat, merch_long, is_fraud`. The mirror reports 1,852,394 rows (train + test combined). In the sample row, `trans_date_trans_time` is 2020-06-21 while `unix_time` is 1371816865, i.e. 2013, so `unix_time` is offset and not usable. — [HF SlimG/transactions viewer](https://huggingface.co/datasets/SlimG/transactions)
- A secondary write-up reports 1,306,675 rows, 23 columns and about 0.58% fraud for one file. — [RPubs analysis](https://rstudio-pubs-static.s3.amazonaws.com/1192717_fad8abc99a6c416fb617cb6c40f276ac.html)
- Sparkov generator: MIT licence. `python datagen.py -n <customers> -o <out> <start> <end>`. Profile JSONs set transactions per day, day-of-week weights and amount mean/SD per category. It uses Faker for customers, merchants and card numbers. — [GitHub namebrandon/Sparkov_Data_Generation](https://github.com/namebrandon/Sparkov_Data_Generation); [Kaggle description of profiles](https://www.kaggle.com/datasets/kartik2112/fraud-detection)

### Inferences
- The commonly cited split of 1,296,675 train + 555,719 test sums exactly to the mirror's 1,852,394. The RPubs 1,306,675 figure is probably a typo.
- `cc_num` is the only key; customer = card (1:1). There is no customer ID distinct from the card.
- Fit: background card spend only. KYC-ish fields (job, dob, address, city_pop) are a useful template for synthetic KYC.

### Gaps
- None material. The fit is clearly poor for cash rules.

## 4. PaySim and BankSim (Lopez-Rojas)

### Takeaway
Both are agent-based simulators calibrated on real private logs: PaySim on African mobile money, BankSim on Spanish card payments. Both are too short (30 days and about 6 months), have no branches and no customer↔account split, and are fraud- rather than AML-oriented. PaySim's `CASH-IN` / `CASH-OUT` types are mobile-money agent cash, not bank teller cash. Neither suits R1–R6 background.

### Cited Findings
- PaySim (Kaggle `ealaxi/paysim1`, CC BY-SA 4.0). One file, `PS_20174392719_1491204439457_log.csv` (493.5 MB). The simulation is based on one month of real logs from a mobile money service in an African country, scaled to 1/4 for Kaggle. `step` = 1 hour, 744 steps (30 days). Types `CASH-IN, CASH-OUT, DEBIT, PAYMENT, TRANSFER`. Columns `step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud`. The amount is "in local currency". `isFlaggedFraud` fires on attempts to transfer more than 200,000. Full runs produce about 24M records. — [Kaggle API metadata, ealaxi/paysim1](https://www.kaggle.com/datasets/ealaxi/paysim1)
- BankSim (Kaggle `ealaxi/banksim1`, CC BY-NC-SA 4.0). Agent-based, based on aggregated data from a bank in Spain. 180 steps (about 6 months), 594,643 records (587,443 normal, 7,200 fraud). Files `bs140513_032310.csv` (49 MB) and `bsNET140513_032310.csv` (33 MB). Cite Lopez-Rojas & Axelsson, EMSS 2014. — [Kaggle API metadata, ealaxi/banksim1](https://www.kaggle.com/datasets/ealaxi/banksim1)

### Inferences
- Both have customer = account (single `nameOrig` / `customer` key) and no location or branch beyond BankSim zip codes (BankSim column names not verified here).
- BankSim's NC (non-commercial) licence is fine for an academic assignment. PaySim's share-alike licence would apply to redistributed derivatives.
- Fit: poor. Too short for R4 (≥180 days dormancy) and for R6 baselines; no teller cash.

### Gaps
- BankSim's exact column list was not verified from a fetched source. Recalled as `step, customer, age, gender, zipcodeOri, merchant, zipMerchant, category, amount, fraud`; treat as unverified.

## 5. Kaggle "Bank Customer Segmentation (1M+ Transactions)" (`shivamb/bank-customer-segmentation`, Indian bank)

### Takeaway
It is described as real-ish Indian bank data, but it has about 1.3 transactions per customer, no account ID, no transaction type or cash flag, and a short window. It is unusable as background for any of R1–R6.

### Cited Findings
- "1 Million+ transaction by over 800K customers for a bank in India", with customer DOB, location, gender, account balance at the time of the transaction, and transaction amount. One file, `bank_transactions.csv` (67.6 MB). Licence: "Data files © Original Authors". — [Kaggle API metadata, shivamb/bank-customer-segmentation](https://www.kaggle.com/datasets/shivamb/bank-customer-segmentation)
- Columns used in analyses: `CustomerID, CustGender, CustLocation, CustomerDOB, CustAccountBalance, TransactionAmount (INR), TransactionDate`. There is no separate account ID and no type or channel field. `CustLocation` is the customer's location (8,157 unique). — [cyfangus write-up](https://cyfangus.github.io/posts/2025/01/bank-customer-segmentation)
- Missing-value counts imply 1,048,567 rows (CustLocation 1,048,416 non-null + 151 missing). — [Deepnote analysis, via search](https://deepnote.com/app/sama-ec6c/Customer-Segmentation-for-an-Indian-Bank-7020afc7-d10f-4d2d-808d-711aa9677b3b)

### Inferences
- 1,048,567 rows across more than 800K customers means most customers have a single transaction. There is no history for R4 or R6, and no direction or cash flag for R1–R3.
- Currency INR. The "© Original Authors" licence restricts redistribution.
- Provenance is undocumented: there is no statement of how it was anonymised or whether it is real.

### Gaps
- The `TransactionDate` range was not verified (community notebooks suggest a few months in 2016, unconfirmed). Whether a `TransactionTime` / `TransactionID` column exists was also not confirmed from a primary source.

## 6. "Financial Transactions Dataset: Analytics" (Kaggle `computingvictor/transactions-fraud-datasets`, CaixaBank Tech 2024 AI Hackathon)

### Takeaway
This is a 2010s US-flavoured card-transaction set with users (KYC-like) and cards tables, Apache 2.0. It appears to be derived from the IBM/Altman generator lineage. It shares TabFormer's limits: card spend, no deposits, no teller cash, no branches. It is only marginally better than TabFormer because it uses snake_case IDs (`client_id`, `card_id`) and a single decade.

### Cited Findings
- It combines "transaction records, customer information, and card data from a banking institution, spanning across the 2010s decade". Files: `transactions_data.csv` (1.26 GB), `cards_data.csv` (510 KB), `users_data.csv` (165 KB), `mcc_codes.json` (4.7 KB), `train_fraud_labels.json` (159 MB). Licence Apache 2.0, last updated 2024-10-31. — [Kaggle API metadata, computingvictor/transactions-fraud-datasets](https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets)
- Credited as "Dataset created by Caixabank Tech for the 2024 AI Hackathon". — [GitHub mayankcodezzz/Financial-Transactions-Dataset-Analytics README](https://github.com/mayankcodezzz/Financial-Transactions-Dataset-Analytics)
- A Hugging Face QA set over this data references the columns `client_id`, `card_id`, `use_chip`, `merchant_city` and `errors`. Its sample reports 1,218 unique clients and 3,838 unique cards; the sample's provenance is unclear. — [HF STARXQ/FinTransEvalQA, via search](https://huggingface.co/datasets/STARXQ/FinTransEvalQA/blob/main/qa_evaluation_dataset.csv)

### Inferences
- The users file is a similar size to `sd254_users.csv` (165 KB vs 224 KB), and the column names mirror TabFormer's (`use_chip`, `merchant_city`, `errors`, MCC). That strongly suggests a snake_case re-cut of the IBM/Altman data restricted to the 2010s, with roughly 2,000 users. This is an inference, not verified.
- Fit: same as TabFormer. R6 background spend only. `train_fraud_labels.json` holds fraud labels, not AML labels.

### Gaps
- The exact column lists, row counts and year bounds were not verified (Kaggle's API returned no column schema, and no full mirror was readable).

## 7. Other public real anonymised retail-bank ledgers

### Takeaway
I found no public dataset that combines real US retail-bank deposits, a teller/ATM cash channel, branch IDs and multi-account customers. The closest real candidates are Berka (Czech, 1990s) and Russian bank-card competition datasets (e.g. Sberbank gender prediction), which have transaction-type codes but no branches or accounts.

### Cited Findings
- Sberbank Gender Prediction (Kaggle `nenriki/sberbank-gender-prediction`), licence ODbL / Database Contents. `transactions.csv` has `client_id`, `datetime` (ordered day number + hh:mm:ss, e.g. "421 06:33:15"), `code` (MCC), `type` (transaction type, described in `types.csv`) and `sum` (signed: + incoming, − outgoing). Other files: `codes.csv`, `types.csv`, `train_set.csv`, `test_set.csv`. — [Kaggle API metadata, nenriki/sberbank-gender-prediction](https://www.kaggle.com/datasets/nenriki/sberbank-gender-prediction)

### Inferences
- The Sberbank set has real anonymised flows with a type dictionary that may include cash deposit and withdrawal codes. It has no account ID, no branch, no calendar dates (only day offsets) and is in RUB. It is weaker than Berka for this MVP.
- Other Russian bank competition sets (e.g. Rosbank churn, Alfa-Bank, VTB Data Fusion) are known in the sequence-modelling literature. They were not verified here and are likely card or MCC streams without branches.

### Gaps
- I could not verify the Sberbank `types.csv` contents (whether cash-deposit types exist), row counts or day span. The Kaggle file size (transactions.csv about 5.5 MB) suggests a small subset, not the full competition data.
- No public US real-bank deposit ledger with cash and branch fields was found. This matches the widely stated privacy barrier (see the PaySim Kaggle text on the "intrinsically private nature of financial transactions").

## 8. Plaid Sandbox custom users

### Takeaway
Plaid Sandbox custom users cannot provide the needed background. They are capped at about 250 transactions and 10 accounts per user, have no settable branch, location or payment channel, and are aimed at API integration testing, not bulk dataset generation.

### Cited Findings
- Custom users are configured via Sandbox Studio, Link (username `user_custom`, JSON as password) or `/sandbox/public_token/create` with `override_username` / `override_password`. — [Plaid docs: Sandbox custom users](https://plaid.com/docs/sandbox/user-custom/)
- Per-account settings: `type`, `subtype`, `starting_balance`, `available_balance`, `iso_currency_code`, `metadata`, plus `numbers`, `transactions`, `identity`, `liability`, `inflow_model`, `income`, and so on. Transaction fields are limited to `date_transacted`, `date_posted` (a future date makes it pending), `amount`, `description` and `currency`. — [Plaid docs](https://plaid.com/docs/sandbox/user-custom/)
- Limits: configs over about 55 KB or about 250 transactions are unsupported; more than 10 accounts per custom user is unsupported. Dates are fixed unless `roll_dates_forward` is set; transactions added via `/sandbox/transactions/create` keep their given dates. — [Plaid docs](https://plaid.com/docs/sandbox/user-custom/)
- The docs do not list `payment_channel`, location or branch, or a cash-deposit type as settable transaction fields for custom users. — [Plaid docs](https://plaid.com/docs/sandbox/user-custom/)

### Inferences
- A "cash deposit" could only be faked through `description` text (e.g. "BRANCH DEPOSIT CASH #12"), which Plaid enrichment may or may not classify. 180+ days of history is possible in principle by choosing dates, but at 250 transactions per user it means very few customers. Getting background data out would also require Plaid API keys and Item creation. Not worth it for a 1-week MVP.

### Gaps
- No maximum lookback date for custom transactions is documented on the page.

## 9. Calibration: Diary and Survey of Consumer Payment Choice (Atlanta Fed / Boston Fed / FedCash)

### Takeaway
This is the best public US source for consumer cash payment shares and sizes (cash about 14% of payments; 70% of cash payments are under $25). It describes consumer spending, not deposits into bank accounts, so it calibrates ATM withdrawal and cash-spend behaviour more than teller cash deposits.

### Cited Findings
From the 2025 Findings report (October 2024 Diary data) — [FRB Services, 2025 Diary of Consumer Payment Choice (PDF)](https://www.frbservices.org/wp-content/uploads/2025-diary-of-consumer-payment-choice.pdf):
- Payments per month: 48 per consumer in 2024, up 2 from 2023.
- Cash use: 7 cash payments per month for four years; cash was 14% of payments by number; 70% of cash payments were under $25. Credit cards were 35% of payments.
- Cash use by demographic group: households earning under $25k used cash for 24% of payments, versus 9% for households earning over $150k. Adults 55+ used cash for 19% of payments, ages 25–54 for 14%, ages 18–24 for 10%.
- Cash holdings: average on-person cash $67; store-of-value cash $306.
- Sample: the Diary is managed by the Atlanta Fed Research Department, with responses weighted to national benchmarks from the USC Understanding America Study panel (about 14,700 respondents).
- Data report: Foster, Greene and Stavins, Atlanta Fed Research Data Report no. 25-1.

Later and secondary figures:
- For 2025 (the 2026 release), Pew reports cash at 14% of payments, an average cash purchase of $58 (debit $74, credit $80), and credit cards at 34% of payments. — [Pew Research, 2026-09-30](https://www.pewresearch.org/short-reads/2026/09/30/from-cash-to-credit-how-americans-payment-methods-have-changed-in-the-past-decade/)
- A secondary analysis of the public October 2025 Diary microdata gives cash at 13.9% of in-person payments and provides a size-band table (figures not captured). — [Eco3min](https://eco3min.fr/en/cash-use-in-america-by-age-and-purchase-size/)

### Inferences
- Use the Diary to set ATM withdrawal sizes and frequencies, and the share of retail customers who use cash at all (about 80% hold cash). Do not use it for teller deposit amounts.
- For R1/R2 false-positive realism, the Diary implies retail consumers rarely transact in cash amounts near $2k–$10k. Large cash-in at a regional bank comes mainly from small-business customers, for which no public distribution was found (Section 13).

### Gaps
- The atlantafed.org Diary landing URL I tried returned a 404 (site restructured). The current microdata download URL was not captured. Per the reports, the public data are distributed by the Atlanta Fed (Survey and Diary of Consumer Payment Choice data pages).
- Exact 2024/2025 cash shares by size band were not extracted.

## 10. Calibration: Federal Reserve Payments Study (FRPS)

### Takeaway
The FRPS gives national aggregates (counts and values by instrument, including ATM cash withdrawals). Use it for channel mix (card vs ACH vs check vs wire vs ATM) at the population level, not for per-customer distributions.

### Cited Findings
- The 2025 triennial study's initial findings (released 2026-07-01, covering 2024): 236.6 billion noncash payments in 2024, more than triple the 2000 level. Cards were over three quarters of payments by number. Credit grew faster than debit for the first time in almost a decade. ACH was almost three quarters of noncash value. Check payments and ATM cash withdrawals continued to decline by number and value. Estimates come from surveys of depository institutions, networks and processors. — [Federal Reserve press release 2026-07-01](https://www.federalreserve.gov/newsevents/pressreleases/other20260701a.htm); [Glenbrook summary](https://glenbrook.com/payments_news/federal-reserve-issues-initial-findings-from-its-2025-triennial-payments-study/)
- FRPS landing page and data are hosted by the Atlanta Fed and Fed Board; there is also a data.gov listing. — [Atlanta Fed FRPS](https://www.atlantafed.org/what-we-study/payments/federal-reserve-payments-study); [data.gov FRPS](https://catalog.data.gov/dataset/federal-reserve-payments-study-frps)

### Gaps
- Exact 2024 ATM withdrawal counts and values, and average ACH/check/wire values, were not captured from the detailed tables.

## 11. Calibration: FDIC Summary of Deposits (SOD) / BankFind

### Takeaway
SOD gives real branch locations and branch deposit totals for any real $1–5B bank through a free, keyless JSON API. Use it to build a realistic branch table (IDs, cities, lat/long, deposit weights) for synthetic customers and for R3.

### Cited Findings
- A live API call returned 219 branch records for Vermont in 2025. The first rows were Bar Harbor Bank & Trust branches (e.g. Brandon Park St, Pittsford, Woodstock) with `ASSET` = 4,106,441 and `DEPSUMBR` of 92,169, 26,412 and 51,311, plus `BRNUM`, `UNINUMBR`, `SIMS_LATITUDE` and `SIMS_LONGITUDE`. The index is dated 2026-09-18. — [FDIC BankFind API: /banks/sod](https://api.fdic.gov/banks/sod?filters=YEAR:2025%20AND%20STALPBR:VT&fields=NAMEFULL,NAMEBR,CITYBR,STALPBR,DEPSUMBR,ASSET,BRNUM,UNINUMBR,SIMS_LATITUDE,SIMS_LONGITUDE&limit=3)
- Field definitions CSV: `ADDRESBR` branch location; `ASSET` institution total assets as of June 30, repeated for every location; `BKMO` main office (1) or branch (0); `BRNUM` branch number within the institution; `BRSERTYP` service type (11–13 full service, including 12 retail; 21–30 limited service, including 23 drive-through and 28 limited retail); `CITYBR`; `CERT`; plus BKCLASS and charter fields. — [FDIC SOD variable definitions CSV](https://api.fdic.gov/banks/docs/sod_variables_definitions.csv)
- API documentation lives at api.fdic.gov/banks/docs; the SOD explorer is in BankFind Suite. — [BankFind Suite API docs](https://api.fdic.gov/banks/docs/); [data.gov SOD definitions](https://catalog.data.gov/dataset/summary-of-deposits-sod-definitions)

### Inferences
- FDIC reports dollar fields in thousands, so `ASSET` = 4,106,441 means about $4.1B. That puts Bar Harbor Bank & Trust inside the $1–5B persona range, and its branch `DEPSUMBR` values are about $26–92M. (Units inferred from standard FDIC convention; confirm in the YAML definitions.)
- A practical recipe: filter `ASSET` between 1,000,000 and 5,000,000 for a chosen state, pick one CERT, and pull all its branches. Use `DEPSUMBR` shares as branch weights for assigning home branches, and `BRSERTYP` to mark which branches take teller cash. The data is US government public data, so no licence issue.

### Gaps
- The full SOD YAML field list (e.g. `DEPSUM` vs `DEPSUMBR`, `STCNTYBR`) was not exhaustively read.

## 12. Calibration: FinCEN CTR and SAR volumes

### Takeaway
About 20.9M CTRs were filed in FY2023, 84% by depository institutions, and a $20k threshold would have cut filings by about 65%. That implies roughly two-thirds of CTR events involve $10k–$20k of cash, which is directly useful for calibrating the right tail of synthetic cash deposits and the expected R1 hit mix. Structuring is a top SAR category (more than 500k structuring SARs in 2023).

### Cited Findings
From GAO-25-106500 — [GAO-25-106500](https://files.gao.gov/reports/GAO-25-106500/index.html):
- CTR volumes: about 20.9M CTRs in FY2023, up from 12.9M in FY2002 (+62%); 90,403,652 CTRs over FY2019–2023.
- Filers: about 84% filed by depository institutions in FY2023 (about 86% over FY2019–2023). The top three filers (large banks) filed nearly 30% of CTRs in FY2022–2023.
- Threshold: a $20,000 threshold would have reduced FY2023 CTR filings by about 65%. $10,000 in 1972 equals about $72,880 in 2023 dollars.
- Structuring: more than 900,000 structuring-related SAR activities per fiscal year from FY2019 to FY2023, and more than 500,000 structuring SARs in 2023 for transactions below the threshold.

Other sources:
- More than half of FY2023 SARs (about 2.5M) came from depository institutions. — [ABA Banking Journal, via search](https://bankingjournal.aba.com/?p=51769)
- FY2023 totals of about 4.6M SARs and 20.8M CTRs, a secondary summary of FinCEN's Year in Review that differs slightly from GAO's 20.9M. — [AML Watcher](https://amlwatcher.com/news_article/fincen-released-year-in-review-for-fiscal-year-2023)
- FinCEN's Interactive SAR Stats tool gives aggregated counts by suspicious-activity category, industry and geography from FinCEN Form 111 data. — [data.gov SAR Stats listing](https://catalog-old.data.gov/dataset/suspicious-activity-report-statistics-sar-stats); historical editions: [SAR Stats 2](https://www.fincen.gov/sites/default/files/shared/SAR_Stats_2_FINAL.pdf)

### Inferences
- To scale to the persona bank, apportion the about 17.5M depository-institution CTRs (84% of 20.9M) by deposits. A $1–5B bank is roughly 0.005–0.03% of US domestic deposits (about $18T, an outside-knowledge figure, not sourced here). That suggests on the order of hundreds to a few thousand CTRs per year, but large banks are over-represented (the top 3 file about 30%). Treat this as a sanity band for R1 alert volume, not a target.
- The 65% figure supports a heavy-tailed cash-deposit distribution: most over-$10k cash days sit between $10k and $20k.

### Gaps
- The CTR amount distribution beyond the $20k counterfactual, and current structuring SAR counts for depository institutions by state or asset size, were not retrieved (they need Interactive SAR Stats queries).

## 13. Published distributions of small-business cash deposits

### Takeaway
I found no public, citable distribution of small-business cash deposit amounts or frequencies for US banks. The team will need to parameterise these and state the assumptions.

### Cited Findings
- None found in this research pass.

### Inferences
- Reasonable proxies: the GAO 65% counterfactual for the over-$10k tail (Section 12); Diary data for consumer cash; FDIC SOD branch deposits for branch weights. Other options are cash-intensive-business sales scaled by a cash-share assumption (e.g. restaurants, convenience stores, laundromats) from Census Annual Business Survey or County Business Patterns receipts. Those are not researched here.

### Gaps
- No Fed, FDIC or industry dataset with per-deposit small-business cash amounts was located. The Fed's cash product office (FedCash) publishes depository-level currency flows only in aggregate (not verified).

## 14. Overall: does "real unlabelled background + injected typologies" beat a pure generator for this MVP?

### Takeaway
For this MVP (due 2026-11-11, with rules keyed on customer↔multi-account, cash channel, branch and ≥180 days of history), a calibrated pure generator beats real-background injection. No public real ledger supplies the needed fields. The only real one, Berka, needs synthetic customers, channels, branches, currency and dates layered on, which removes most of its realism advantage. A good compromise is a calibrated generator as the primary dataset, plus an optional "Berka realism slice": Berka accounts remapped to USD, with synthetic channel and branch, used only to measure false-positive rates on real cadence.

### Cited Findings
Per-candidate fit summary (facts as cited in Sections 1–8):

| Candidate | Real? | Customer≠account (1:N) | Cash flag / channel | Branch / location | History | Currency / era | Licence | R1–R6 fit |
|---|---|---|---|---|---|---|---|---|
| Berka PKDD'99 | Real, anonymised | Inverted: N clients : 1 account (disp OWNER/DISPONENT) | `VKLAD` cash-in, `VYBER` cash-out; no teller/ATM split | Account-level `district_id` (77) | 1993–1998 | CZK, 1990s | Unstated (CTU public; Kaggle mirror says CC0) | Partial: R2, R4, R5, R6 possible; R1/R3 need synthetic layers |
| IBM TabFormer / Altman | Synthetic | User→cards | Card `Use Chip` only | Merchant city/state; user address | Decades | USD | Apache 2.0 | R6 spend only |
| Sparkov (kartik2112) | Synthetic | Card only | None | Customer + merchant lat/long | 2019–2020 | USD | CC0 (generator MIT) | R6 spend only |
| PaySim | Synthetic (calibrated) | No | CASH-IN/CASH-OUT (mobile-money agents) | None | 30 days | Local (African) | CC BY-SA 4.0 | Poor |
| BankSim | Synthetic (calibrated) | No | None | Zip codes | ~6 months | EUR (inferred) | CC BY-NC-SA 4.0 | Poor |
| Indian bank segmentation | Claimed real | No account ID | None | Customer location | ~1.3 txns/customer | INR | © Original Authors | Unusable |
| CaixaBank / computingvictor | Synthetic (IBM lineage, inferred) | client→cards | `use_chip` | Merchant city/state | 2010s | USD | Apache 2.0 | R6 spend only |
| Plaid Sandbox custom | Synthetic test | ≤10 accounts/user | Description text only | None | Any dates, ≤250 txns | Configurable | Plaid ToS | Unsuitable |

### Inferences
**Why the pure, calibrated generator wins here**
- Every rule depends on fields that no public ledger provides together. Injecting into Berka would still mean generating customer↔account links, teller/ATM/night-drop/wire/ACH channels, per-transaction branches, a USD rescale and a date shift. Most columns relevant to R1 and R3 would be synthetic anyway.
- A generator gives exact ground truth for both injected typologies and background, and controls the edge cases rules need (business-day boundaries, $9,999 vs $10,000, 179 vs 180 days, 71 vs 73 hours). Real background can contain unlabelled true positives, e.g. natural structuring-like patterns in Berka, which muddy precision and recall reporting.
- Licence and redistribution are clean (own code). Berka's licence is unstated.

**Where real background still adds value**
- Berka gives authentic temporal cadence: monthly salary and pension credits (`DUCHOD`), household payments (`SIPO`), interest and fees (`UROK`, `SLUZBY`), and cash withdrawals. This is a credible test that the R6 velocity baseline and R4 "customer-initiated" logic do not over-fire on normal behaviour. Bank-initiated `UROK` and `SLUZBY` postings make R4's customer-initiated filter testable.

**Recommended build (inference)**
1. Generator parameters:
   - Branch table: FDIC SOD branches of one real $1–5B bank (e.g. CERT for Bar Harbor Bank & Trust, about $4.1B), weighted by `DEPSUMBR`.
   - Consumer cash behaviour: Diary values (cash about 14% of payments, 70% under $25, about 7 cash payments a month, cash use higher for low-income and 55+ customers).
   - Channel mix: FRPS for card, ACH and check.
   - Cash-deposit tail: GAO (about 65% of CTR events $10k–$20k).
   - Business-customer cash: stated assumptions (no public source).
2. Typology injector applied on top of the generated background. Optionally apply the same injector to the Berka-derived slice.
3. Berka slice (optional, if time allows):
   - Rescale amounts with a district A11-salary-to-US-income factor or quantile mapping.
   - Shift dates by a multiple of 7 days.
   - Treat `VKLAD` as teller cash-in. Randomly assign about 70/30 teller vs ATM to `VYBER`, as an assumption.
   - Group 1–3 Berka accounts in the same district into synthetic multi-account customers.
   - Assign per-transaction branches from the SOD branch table, biased to the home branch.
   - Report alert rates on this slice as an "unlabelled realism check", not as accuracy.

### Gaps
- No one has published how many Berka accounts would trip R1/R2 after any particular CZK→USD rescale. This would have to be measured.
- I found no quantitative comparison (paper or benchmark) of hybrid real+injected versus fully synthetic data for rule-based AML testing. The recommendation above is reasoned, not evidenced.
