# Target schema for a US core-banking transaction export, and licences of candidate AML datasets

Research date: 2026-11-04. Scope: (Part 1) what a US core nightly transaction/history extract carries, and what AML tools and FinCEN CTR require of it; (Part 2) what each candidate dataset's licence allows for a 4-student university course project with a role-played client, a public/class GitHub repo, and a demo. Not legal advice. "Verified" means read on the primary page in this session. Anything marked "via search summary" was read only through a search-engine summary because the page itself was blocked or login-gated.

## Q1. What fields does a US core nightly transaction / history extract carry, and are vendor layouts public?

### Takeaway
No US core vendor publishes its nightly flat-file layout openly. Two public sources come close and agree on the core fields: Jack Henry's jXchange Account History Search field mapping and Apache Fineract's transaction table. They carry account ID and type, tran code and description, amount, posting date and effective date, check number, teller and batch, source code, memo-post remarks, EFT/card details, running balance, and a record key. Neither carries the CIF/customer number on the transaction row. That has to come from a separate customer-to-account relationship extract. No public Fiserv (DNA/Premier/Precision/Signature), FIS (Horizon/IBS) or Symitar file layout was found.

### Cited Findings
- **Jack Henry jXchange AcctHistSrch, Core Director mapping (verified).** The response fields for each deposit history record are: `ACCTID.ACCOUNT_ID` / `ACCOUNT_TYPE`, `AMT`, `BATCHNUM`, `CHKNUM`, `EFFDT`, `POSTDT`, `SEQNUM`, `HISTFULLKEY` (→ `HistRecId`), `IMGNUM`, `TELLERNUM`, `TRNCODECODE`, `TRNCODEDESC`, `TRNTYPE`, `TRNRCPTID`, `SRCCODEDESC`, `TRNHISTBALAMT` (running balance), `MEMOPOST`, `MEMODTENTRY`, `MEMOTIMEENTRY`, `MEMOPOSTRMK`, `EFTDESC`. Card/EFT sub-records add `EFTCARDNUM`, `EFTTRNDT`, `EFTTRNTIME`, `EFTTRNAMT`, `EFTTRNCODE`, `EFTNTWKID`, `MERNAME`, `SURCHGAMT`, `EFTXFERTOACCTID`. Parallel record types exist for time deposits, loans and safe-deposit boxes. — [Jack Henry jXchange AcctHistSrch – Core Director mapping](https://jackhenry.dev/jxchange-soap/api-reference/core-services/accthistsrch/providers/core-director/mapping/)
- **Gaps in that mapping.** It has no explicit debit/credit code, branch code, or ACH counterparty fields (company name, SEC code, trace number). It has `SRCCODEDESC` but no raw source code. — [same page](https://jackhenry.dev/jxchange-soap/api-reference/core-services/accthistsrch/providers/core-director/mapping/)
- **SilverLake core table mappings (via search summary).** `PostDt` → `CDHIST.CHPSTD` (Date Posted), `EffDt` → `CDHIST.CHEFDT` (Effective Date), `TrnCodeCode` → `CDHIST.CHTRAN` with its description from `CDPAR3.C3DESC`, and `ChkNum` → `CDHIST.CHSERL`. Loans use the matching `LNHIST.LHPSTD` / `LHEFDT` / `LHTRAN` / `LHSERL`. — [jXchange AcctHistSrch](https://jackhenry.dev/jxchange-soap/api-reference/core-services/accthistsrch/); [SilverLake AcctHistSrch loans](https://jackhenry.dev/jxchange-soap/core-reference-resources/silverlake/accthistsrch/accthistsrch-loans/)
- **Running balance caveat (via search summary).** The running balance (`TrnHistBalAmt`) is not returned when check-number, amount-range, transaction-type, EFT-only, transfer-key or receipt-ID filters are used, or when sorting by anything other than posting or effective date. Memo-posted items are included in the running balance. — [jXchange AcctHistSrch](https://jackhenry.dev/jxchange-soap/api-reference/core-services/accthistsrch/)
- **Cores covered by jXchange.** The AcctHistSrch provider list includes CIF2020, Core Director, SilverLake, Corelation Keybridge and others. — [jXchange AcctHistSrch Core Director mapping page (navigation)](https://jackhenry.dev/jxchange-soap/api-reference/core-services/accthistsrch/providers/core-director/mapping/)
- **Apache Fineract `m_savings_account_transaction` (verified).** Columns include `id`, `savings_account_id`, `office_id` (branch), `payment_detail_id`, `transaction_type_enum`, `is_reversed`, `transaction_date`, `amount` DECIMAL(19,6), `running_balance_derived`, `cumulative_balance_derived`, `created_date` DATETIME, `appuser_id` (user/teller), `is_manual`, `ref_no`, `original_transaction_id`, `is_reversal`, `reason_for_block`, `is_lien_transaction`. Payment details live in a linked `m_payment_detail` table. — [Fineract DB docs](https://fineract.apache.org/docs/database/tables/m_savings_account_transaction.html)
- **Fineract payment-detail fields.** These are `paymentTypeId`, `accountNumber`, `checkNumber`, `routingCode`, `receiptNumber` and `bankNumber`. They appear as optional request fields in a generated Fineract SDK, which is a third-party package and not official documentation. — [fineract_sdk savings-account-api.d.ts](https://app.unpkg.com/fineract_sdk@0.0.5/files/dist/api/savings-account-api.d.ts)
- **SynthAML, from real Danish bank (Spar Nord) data.** Transactions carry a timestamp, an entry type (credit or debit), a transaction type (card, cash, international or wire) and a size. Size is log-DKK, standardised. — [SynthAML, Scientific Data 2023 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539331/), read via [Europe PMC full text](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)

### Inferences
- **Field-by-field evidence for the typical extract:**

  | Field | Public evidence |
  |---|---|
  | Account number | jXchange `ACCOUNT_ID`; Fineract `savings_account_id` |
  | CIF/customer number | Not on history rows in either source. Join it from a customer-account file (jXchange has separate customer services; their layouts were not checked). |
  | Tran code / description | `TRNCODECODE` / `TRNCODEDESC`; Fineract `transaction_type_enum` |
  | Amount | `AMT`; Fineract `amount` |
  | Debit/credit | Implied by tran code (`TRNTYPE` meaning not confirmed); SynthAML has an explicit entry type |
  | Posting / effective date | `POSTDT` / `EFFDT` |
  | Branch / teller | `TELLERNUM`, `BATCHNUM`; Fineract `office_id`, `appuser_id` |
  | Channel / source | `SRCCODEDESC`, EFT network ID |
  | Cash indicator | Not a native field. Derive it from the tran code. |
  | Check number | `CHKNUM`; Fineract `checkNumber` |
  | ACH/wire counterparty | `EFTDESC`, `EFTXFERTOACCTID`. True ACH addenda and wire fields were not found in public core docs. |
  | Memo | `MEMOPOSTRMK`; Fineract `ref_no` |
  | Running balance | `TRNHISTBALAMT`; Fineract `running_balance_derived` |
  | Reversal | Fineract `is_reversed`, `is_reversal`, `original_transaction_id` |

- **CIF table names.** `CDHIST`/`LNHIST`/`CDPAR3` look like SilverLake (IBM i) core tables. A real SilverLake nightly extract would likely be built from them, but Jack Henry does not publish an "export file" spec.
- **"Cash" depends on the bank's tran-code table.** A real nightly extract does not carry an `is_cash` flag. Whether an item is cash is decided by the bank's tran-code configuration (for example teller cash deposit vs. check deposit). So the MVP needs a bank-editable `tran_code → {cash_in, cash_out, channel}` lookup table. The CTR rule must not rely on the free-text description.

### Gaps
- No public Fiserv DNA/Premier/Precision/Signature, FIS Horizon/IBS, or Symitar extract layout was found. Fiserv's developer portal was not checked in this session.
- The meaning and values of jXchange `TRNTYPE` and `SRCCODEDESC` were not confirmed.
- No public ACH addenda or wire (Fedwire) fields in a core history API were found.
- How a CIF links to accounts in jXchange (for example a customer-relationship inquiry) was not researched.

## Q2. What do AML vendor import specs and APIs require as input fields?

### Takeaway
Bank-focused AML vendors (Verafin, Abrigo BAM+, Alessa) do not publish their transaction import specs. Their integrations are scoped batch files over SFTP. The fintech-oriented APIs (Flagright, Unit21, Marble, Tazama) are public, and they converge on a minimal core:

- a unique transaction ID
- a timestamp
- an amount and currency
- an origin party and account
- a destination party and account
- a type or method (including CASH, ACH, SWIFT and CHECK)
- a state or status (including reversed)

### Cited Findings
- **Flagright (verified).** The only required fields are `type`, `transactionId` and `timestamp`. Optional fields include `originUserId`, `destinationUserId`, `transactionState`, `originAmountDetails` / `destinationAmountDetails` (inside these, `transactionAmount` and `transactionCurrency` are required and `country` is optional), `originPaymentDetails` / `destinationPaymentDetails`, `reference`, `relatedTransactionIds`, `tags` and `metadata`.
  - `type` is free text, with examples DEPOSIT, WITHDRAWAL, TRANSFER, EXTERNAL_PAYMENT, REFUND, OTHER.
  - `transactionState` values: CREATED, PROCESSING, SENT, EXPIRED, DECLINED, SUSPENDED, REFUNDED, SUCCESSFUL, REVERSED.
  - Payment `method` values: CARD, IBAN, ACH, SWIFT, GENERIC_BANK_ACCOUNT, WALLET, UPI, MPESA, CHECK, CASH, NPP.
  - — [Flagright verify-transaction API reference](https://docs.flagright.com/api-reference/api-reference/transactions/verify)
- **Flagright state updates.** Transaction events must carry a `transactionState` and a timestamp, and they update the transaction's lifecycle. — [Flagright entities guide](https://docs.flagright.com/guides/overview/entities) (via search summary)
- **Unit21 (via search summary; the docs page now redirects to a login).** Event fields include `event_id`, `event_type` (must be "transaction" for monetary events), `event_subtype`, `status`, `sent_amount`, `sent_currency`, `sender_entity_id`, `sender_instrument_id`, `received_currency`, `receiver_entity_id`, `receiver_instrument_id`, and a normalised `amount`. A tutorial format also uses `event_time` (epoch seconds) and `received_amount`. — [Unit21 Events docs](https://docs.unit21.ai/docs/events)
- **Unit21 data hygiene.** Send entities first, then instruments, then transactions. Amounts should not be negative. — [Unit21 Best Practices](https://support.unit21.ai/hc/en-us/articles/6433426083732-Best-Practices-when-sending-Data-to-Unit21)
- **Marble (via search summary).** Marble "does not impose a specific data model". It suggests starting with individuals, businesses, accounts, events and transactions. Its Data Ingestion API has one endpoint per object and upserts each record. — [Marble: How Marble works](https://checkmarble.readme.io/docs/how-marble-works)
- **Tazama (verified).** The TMS API accepts ISO 20022 pain.001, pain.013 and pacs.008 messages and validates them against a Swagger spec. Its internal DataCache keeps `creDtTm`, `dbtrId`, `cdtrId`, `dbtrAcctId`, `cdtrAcctId`, `instdAmt` (`amt`, `ccy`), `intrBkSttlmAmt` and `xchgRate`. Non-ISO systems connect through a Payment Platform Adapter. The docs repo is Apache-2.0. — [Tazama TMS API doc](https://github.com/tazama-lf/docs/blob/dev/Product/transaction-monitoring-service-api.md); [tazama-lf/docs](https://github.com/tazama-lf/docs)
- **MANTL → Verafin (via search summary; the article returned HTTP 403).** This is a batch file sent over SFTP into Verafin's standard batch import. It follows the Verafin Account Opening Questionnaire 4.2.1 spec, which has 277 fields, plus a Beneficial Owner file. Which fields are sent is decided in a scoping exercise. Import testing takes 28–52 days. — [MANTL: Verafin Integration](https://mantl.zendesk.com/hc/en-us/articles/40281700714779-Verafin-Integration)

### Inferences
- **Verafin covers onboarding data, not transactions, here.** The public Verafin evidence is about account-opening (KYC) data, not the core transaction feed. The same pattern (a scoped batch file over SFTP, with a vendor-specific spec) plausibly applies to core feeds, but that is not confirmed.
- **CSV-over-SFTP is realistic.** The MVP's "nightly CSV export" assumption fits how bank-side AML tools ingest data.
- **Unsigned amounts.** Both Flagright (`type` + `transactionState`) and Unit21 (non-negative amounts with a sender/receiver direction) use unsigned amounts with a separate direction. The MVP schema should do the same: an unsigned amount plus a D/C indicator.

### Gaps
- No public Abrigo BAM+ data-file spec, Alessa import spec, or Verafin core transaction spec was found. These appear to be customer-only documents.
- Marble's field-level ingestion schema and Tazama's tms-service Swagger file were not read.

## Q3. Which FinCEN CTR (FinCEN Report 112) fields must the data support?

### Takeaway
A CTR is a per-person, per-business-day report. It needs the following (verified, FinCEN CTR XML User Guide v1.8, Aug 2021):

- the transaction date
- separate totals for cash in and cash out
- a breakdown by cash-in and cash-out type code
- the accounts affected, each flagged as cash in or cash out
- the role of each person (conducting on own behalf, for another, or on whose behalf)
- the transaction location (branch)
- indicators for ATM, armored car, mail/shipment, night deposit, shared branching and aggregated transactions

The transaction export can feed the date, amounts, accounts, direction, type and branch. Identity fields (name, TIN, DOB, ID document) come from the CIF and the teller capture, not from the transaction export.

### Cited Findings
All findings below are from the [FinCEN CTR XML Schema User Guide](https://bsaefiling.fincen.gov/docs/XMLUserGuide_FinCENCTR.pdf). The PDF pages show "Version 1.8 | August 2021"; the cover text also reads "Version 1.5 | January 2020".

- **Party types (`ActivityPartyTypeCode`):** 35 Transmitter; 37 Transmitter Contact; 30 Reporting financial institution; 8 Contact for assistance; 34 Transaction location; 50 Person conducting transaction on own behalf; 17 Person conducting transaction for another; 23 Person on whose behalf this transaction was conducted; 58 Common carrier.
- **Accounts:** `AccountNumberText` identifies "the account number for the account involved in the transaction(s)". Each account carries `PartyAccountAssociationTypeCode` 8 (activity affected account, cash in) or 9 (activity affected account, cash out).
- **Person-level elements** include `IndividualBirthDateText`, `BirthDateUnknownIndicator`, `IndividualEntityCashInAmountText`, `IndividualEntityCashOutAmountText`, `MultipleTransactionsPersonsIndividualsIndicator`, `PartyAsEntityOrganizationIndicator`, `PartyIdentificationTypeCode` / `PartyIdentificationNumberText`, and gender indicators.
- **`CurrencyTransactionActivity` elements:** `AggregateTransactionIndicator`, `ArmoredCarServiceIndicator`, `ATMIndicator`, `MailDepositShipmentIndicator`, `NightDepositIndicator`, `SharedBranchingIndicator`, `TotalCashInReceiveAmountText`, `TotalCashOutAmountText`, `TransactionDateText` (required, 8 numeric characters), and `CurrencyTransactionActivityDetail` / `CurrencyTransactionActivityDetailTypeCode`.
- **Cash-in type codes:** 55 Deposit(s); 46 Payment(s); 23 Currency received from funds transfer(s) out; 12 Purchase of negotiable instrument(s); 14 Currency exchange(s) in; 49 Currency to prepaid access; 18/21/25 gaming codes; 997 Other cash in; 53 Foreign currency in.
- **Cash-out type codes:** 56 Withdrawal(s); 30 Advance(s) on credit including markers; 32 Currency paid from funds transfer(s) in; 13 Negotiable instrument(s) cashed; 15 Currency exchange(s) out; 48 Currency from prepaid access; 28/31/33/34 gaming codes; 998 Other cash out; 54 Foreign currency out.
- **Aggregated-transactions indicator:** it means the institution did not identify any transactor because the CTR reports aggregated transactions that are each below the reporting threshold, with at least one transaction involving a teller.
- **Validation rules:**
  - Error D40: the same transaction type code may not appear more than once (foreign-currency codes excepted).
  - Warning: the sum of the subtotal cash-in amounts must equal the total cash-in amount. The same rule applies to cash out.

### Inferences
- **Minimum CTR rule inputs:** `customer_id`, `business_date`, `amount`, `is_cash` plus direction (cash in or cash out), a CTR type category (deposit, withdrawal, negotiable instrument, currency exchange, funds-transfer cash), `account_id`, and `branch_id`. Add `teller_id` or channel to set the ATM, night-deposit and aggregated indicators.
- **No netting.** Cash in and cash out are totalled and reported separately, so the rule should test each against the threshold separately and never net them. This follows from the separate `TotalCashIn` / `TotalCashOut` elements. The ">$10,000 per business day, aggregated per person" rule itself is in 31 CFR 1010.311/1010.313, which was not fetched this session.
- **Conductor vs. account owner.** The CTR distinguishes the person conducting the transaction (50/17) from the person on whose behalf it was conducted (23). A nightly transaction export rarely carries the conductor's identity. The MVP should aggregate by account-owner CIF and say clearly that conductor-level aggregation needs teller-capture data.
- **Keep PII out of the MVP.** Output a "CTR candidate" worklist, not a populated Form 112.

### Gaps
- It was not confirmed whether a CTR XML User Guide newer than v1.8 (Aug 2021) exists as of Nov 2026.
- The paper/PDF Form 112 instructions and 31 CFR 1010.311/313 were not fetched.

## Q4. Recommended minimal target schema for the MVP

### Takeaway
The MVP needs two inputs:

- **A nightly transaction CSV** with about 18 columns: about 10 required, the rest optional. Each column traces to jXchange, Fineract, a vendor API, or a CTR element.
- **A small customer-account reference file**, needed for CIF aggregation and dormancy.

Every candidate dataset should be mapped into these two files with an adapter. Datasets that lack a field (for example cash flags or customer IDs) should have it derived or generated, and that should be documented.

### Cited Findings
- The field-level evidence is cited in Q1–Q3. The key source anchors are the [jXchange Core Director mapping](https://jackhenry.dev/jxchange-soap/api-reference/core-services/accthistsrch/providers/core-director/mapping/), [Fineract](https://fineract.apache.org/docs/database/tables/m_savings_account_transaction.html), [Flagright](https://docs.flagright.com/api-reference/api-reference/transactions/verify), [Unit21](https://docs.unit21.ai/docs/events) and the [FinCEN CTR XML guide](https://bsaefiling.fincen.gov/docs/XMLUserGuide_FinCENCTR.pdf).
- **SynthAML amounts are anonymised.** They are "log DKK, standardised to zero mean and unit variance". Transactions link only to an `AlertID`. — [SynthAML (Europe PMC)](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML)
- **PaySim fields:** `step` (one hour each; 744 steps, i.e. 30 days), `type` (CASH-IN, CASH-OUT, DEBIT, PAYMENT, TRANSFER), `amount`, `nameOrig`, `oldbalanceOrg`, `newbalanceOrig`, `nameDest`, `oldbalanceDest`, `newbalanceDest`, `isFraud`, `isFlaggedFraud`. — [PaySim on Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1)
- **AMLNet fields:** `step`, `type`, `amount`, `category`, `nameOrig`, `nameDest`, `oldbalanceOrg`, `newbalanceOrig`, `isFraud`, `isMoneyLaundering`, `laundering_typology`, `fraud_probability`, `hour`, `day_of_week`, `day_of_month`, `month`, and a JSON `metadata` column. — [AMLNet v1.0 on Zenodo](https://zenodo.org/records/16736515)
- **SAML-D:** 12 features covering timestamps, sender and receiver accounts, amounts, payment types, bank locations, currencies and a suspicious flag; 28 typologies; about 9.5M rows. — [SAML-D on Kaggle](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml)

### Inferences

**Transaction file (one row per posted transaction)**

| Field | Type | Req? | Why a rule needs it | Public evidence |
|---|---|---|---|---|
| `txn_id` | string | Y | Dedupe across nightly files; link alerts back to rows | jXchange `HISTFULLKEY`/`TRNRCPTID`; Fineract `id`; Flagright `transactionId` (required); Unit21 `event_id` |
| `account_id` | string | Y | Pass-through and dormancy are account-level; CTR `AccountNumberText` | jXchange `ACCOUNT_ID`; Fineract `savings_account_id`; Tazama `dbtrAcctId`; CTR |
| `customer_id` (CIF) | string | Y* | CTR and structuring aggregate per person; velocity per customer | CTR party model; Unit21 `sender_entity_id`; Flagright `originUserId`; Tazama `dbtrId`. *Can be joined from the reference file. |
| `post_date` | date | Y | CTR business day (`TransactionDateText`); structuring windows; dormancy gap | jXchange `POSTDT`; Fineract `transaction_date`; CTR |
| `effective_date` | date | N | Back-dated items; use it if the bank defines the business day by effective date | jXchange `EFFDT` |
| `txn_time` | datetime | N | Intraday velocity and pass-through hours | Flagright `timestamp` (required); Unit21 `event_time`; Tazama `creDtTm`; jXchange `MEMOTIMEENTRY`/`EFTTRNTIME` |
| `amount` | decimal(18,2), >0 | Y | All thresholds | jXchange `AMT`; Fineract `amount`; Unit21 (non-negative) |
| `dr_cr` | enum D/C | Y | Direction for cash in/out, pass-through (in then out) | SynthAML entry type; Flagright origin/destination; Fineract type enum |
| `tran_code` | string | Y | Drives the cash/channel lookup; excludes system items (interest, fees) from dormancy | jXchange `TRNCODECODE`; Fineract `transaction_type_enum` |
| `tran_desc` | string | N | Analyst readability | jXchange `TRNCODEDESC` |
| `channel` | enum (BRANCH, ATM, ACH, WIRE, CHECK, CARD, ONLINE, INTERNAL, OTHER) | Y | Pass-through (wire/ACH out); CTR ATM/night indicators | jXchange `SRCCODEDESC`; Flagright `method` enum; CTR indicators |
| `is_cash` | bool (derived from `tran_code` lookup) | Y | CTR and structuring | CTR cash-in/out codes; Flagright CASH; SynthAML/PaySim cash types |
| `ctr_type` | enum (DEPOSIT, WITHDRAWAL, NEG_INSTR_PURCHASE, NEG_INSTR_CASHED, FX_IN, FX_OUT, FT_CASH, OTHER) | N | Fill in the CTR breakdown codes (55/56/12/13/14/15/23/32/997/998) | CTR XML guide |
| `branch_id` | string | N | CTR transaction location (party type 34); geographic dispersion | Fineract `office_id`; CTR Part III |
| `teller_id` | string | N | CTR aggregated-transactions logic (needs a teller); in-person vs. self-service | jXchange `TELLERNUM`; Fineract `appuser_id` |
| `check_number` | string | N | Check-cashing and negotiable-instrument context | jXchange `CHKNUM`; Fineract `checkNumber` (SDK) |
| `counterparty_name` / `counterparty_account` / `counterparty_routing` | string | N | Pass-through destination; repeat beneficiaries | Flagright destination payment details; Unit21 `receiver_*`; Tazama `cdtrId`/`cdtrAcctId`; jXchange `EFTXFERTOACCTID` |
| `memo` | string | N | Context for analysts | jXchange `MEMOPOSTRMK`/`EFTDESC`; Fineract `ref_no`; Flagright `reference` |
| `running_balance` | decimal | N | Pass-through ("balance returns to near zero") | jXchange `TRNHISTBALAMT`; Fineract `running_balance_derived`; PaySim old/new balance |
| `is_reversal` / `reversed_txn_id` | bool / string | N | Drop reversed items before thresholds, to avoid false CTRs | Fineract `is_reversed`/`is_reversal`/`original_transaction_id`; Flagright REVERSED |
| `currency` | ISO 4217, default USD | N | CTR foreign currency codes 53/54 | Flagright `transactionCurrency`; Unit21 `sent_currency` |

**Reference file (customer ↔ account)**

| Field | Type | Why |
|---|---|---|
| `customer_id` | string | Aggregation key |
| `account_id` | string | Join key |
| `customer_type` | enum (INDIVIDUAL, BUSINESS) | Exempt-person and threshold tuning |
| `account_open_date` | date | Velocity baselines for new accounts |
| `last_customer_activity_date` | date | Dormant-reactivation rule, so the tool does not need months of history in each nightly file |

**Dataset fit**
- **SynthAML cannot test the $10k CTR rule directly.** Its amounts are standardised log values with no customer ID. Use it only for alert-outcome experiments.
- **PaySim is too short for dormancy.** It covers 30 days in hourly steps, and it is mobile money, not a US core.
- **Generate a US-style demo file.** The most realistic option is a small, team-generated synthetic CSV in this schema, with planted CTR, structuring, dormancy, pass-through and velocity cases. It needs no licence obligations. Public datasets would then be used only for scale and benchmark runs through adapters.

### Gaps
- The exact SAML-D column names were not confirmed this session. From memory they are Time, Date, Sender_account, Receiver_account, Amount, Payment_currency, Received_currency, Sender_bank_location, Receiver_bank_location, Payment_type, Is_laundering, Laundering_type; check them against the CSV header.
- IBM AMLworld column names were not returned by the Kaggle API this session. From memory they are Timestamp, From Bank, Account, To Bank, Account, Amount Received, Receiving Currency, Amount Paid, Payment Currency, Payment Format, Is Laundering; unverified.
- The TabFormer column list was not checked (the README shows it only as an image).
- The Berka `trans` columns were not checked.

## Q5. Is a university course project with a role-played client "non-commercial"?

### Takeaway
Very likely yes under CC's NC definition. The test is the purpose of the use ("primarily intended for or directed towards commercial advantage or monetary compensation"), not who the user is. An unpaid student project graded by a university, with a fictional client, is not primarily directed at commercial advantage. CC itself warns that "not all educational uses are necessarily NonCommercial", so the conclusion changes if money or a real business use enters the picture.

### Cited Findings
- **NC definition:** "NonCommercial means not primarily intended for or directed towards commercial advantage or monetary compensation." — [CC BY-NC-SA 4.0 legal code §1](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en); [CC NC interpretation](https://wiki.creativecommons.org/wiki/NonCommercial_interpretation)
- **Use, not identity:** "NonCommercial turns on the use, not the identity of the reuser." No class of reuser is automatically included or excluded. — [CC NC interpretation](https://wiki.creativecommons.org/wiki/NonCommercial_interpretation)
- **Education is not automatically NC:** "not all educational uses are necessarily NonCommercial uses". — [CC NC interpretation](https://wiki.creativecommons.org/wiki/NonCommercial_interpretation)
- **Disputes are rare:** the NC interpretation page cites the "Defining Noncommercial" study for its statement that actual conflicts over NC "appear to be few". — [CC NC interpretation](https://wiki.creativecommons.org/wiki/NonCommercial_interpretation); [Defining Noncommercial](https://wiki.creativecommons.org/wiki/Defining_Noncommercial)
- **Commercial use needs permission:** commercial use of an NC work requires the licensor's permission. — [CC FAQ](https://creativecommons.org/faq/)

### Inferences
- **Factors that keep it NC:** no payment to students; the "client" is a role-play; the deliverable is for grading; the repo is public and free.
- **Factors that could make it commercial:**
  - a sponsoring company pays the course or the team
  - the real consultant's firm reuses the deliverable or data for client work
  - the repo or demo is used to market a startup or consulting service
  - the work is later folded into a paid product
- **The client role-play is fiction.** The licence looks at the actual use, so the role-played client does not by itself make the use commercial.

### Gaps
- The detailed findings of the 2009 "Defining Noncommercial" report were not read this session.
- The university's own IP policy, which could assign student IP, was not checked.

## Q6. Per licence: can the team commit a subsample or derived files to GitHub, and what obligations follow?

### Takeaway
- **CC BY-NC-SA (SAML-D):** committing is allowed for NC purposes, with attribution. Any adapted or derived data must itself be BY-NC-SA.
- **CC BY-NC (AMLNet):** committing is allowed for NC purposes, with attribution. There is no ShareAlike, but the NC limit still binds the underlying data.
- **CDLA-Sharing-1.0 (AMLworld):** committing is allowed for any purpose. Data you publish, including enhanced data, must stay under CDLA-Sharing, with change notices and the original attribution.
- **CC BY-SA (PaySim):** committing is allowed for any purpose. Derived data must be BY-SA.
- **Apache-2.0 (TabFormer):** committing is allowed, with the licence and notices kept.
- **Berka and JPM:** do not commit. No redistribution grant was found.

### Cited Findings
- **CC BY-NC-SA 4.0 grant (§2(a)(1)):** "reproduce and Share the Licensed Material, in whole or in part, for NonCommercial purposes only" and "produce, reproduce, and Share Adapted Material for NonCommercial purposes only." — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- **CC attribution (§3(a)):** if you share, you must keep the creator identification, the copyright notice and a URI or link to the material where reasonably practicable, and "indicate if You modified the Licensed Material". — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- **CC ShareAlike (§3(b)):** "The Adapter's License You apply must be a Creative Commons license with the same License Elements, this version or later, or a BY-NC-SA Compatible License." — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- **CC database rule (§4):** if you include "all or a substantial portion of the database contents" in a database in which you have sui generis database rights, that database (but not its individual contents) is Adapted Material, including for ShareAlike. — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- **CDLA-Sharing-1.0 publishing conditions:**
  - §3.1(a): data, including enhanced data, "must be Published under this Agreement".
  - §3.1(b): files containing enhanced data must "carry prominent notices that You have changed those files".
  - §3.1(c): "preserve all credit or attribution to the Data Provider(s)".
  - §3.3: publish "under an unmodified form of this Agreement", and you may not add any restriction on commercial or non-commercial use.
  - — [CDLA-Sharing-1.0](https://cdla.dev/sharing-1-0/)
- **CDLA definitions:** "Enhanced Data" is the published subset made of your additions or modifications; "Publish" means making all or a subset of data available. — [CDLA-Sharing-1.0](https://cdla.dev/sharing-1-0/)
- **CC licences need copyright to operate:** "CC licenses are operative only when applied to material in which a copyright exists". If an exception such as fair use applies, you need not rely on the licence. — [CC FAQ](https://creativecommons.org/faq/)

### Inferences
- **SAML-D (BY-NC-SA).** A verbatim 10k-row sample is "Licensed Material in part". A file remapped into the team's schema (renamed columns, derived `is_cash`, synthetic CIFs) is very likely Adapted Material, so it must be shared under BY-NC-SA 4.0 or later.
  - Put it in `data/samples/saml_d/` with a `LICENSE` (BY-NC-SA 4.0), an `ATTRIBUTION.md` (Oztas et al. 2023 citation and Kaggle URL) and a `CHANGES.md`.
  - The rest of the repo can keep its own code licence.
- **AMLNet (BY-NC).** The same attribution and NC rules apply. Without ShareAlike, the team may choose the licence for its own contributions to derived files, but downstream users still get the AMLNet portions only under NC. Simplest: mark the folder CC BY-NC 4.0.
- **AMLworld (CDLA-Sharing).** Any committed subset or remapped file must carry the CDLA-Sharing-1.0 text, a change notice, and IBM / Altman et al. attribution. Commercial use is not restricted.
- **PaySim (BY-SA).** The sample and any adaptations must be shared under BY-SA 4.0 (or a compatible licence), with attribution to Lopez-Rojas et al. 2016.
- **TabFormer (Apache-2.0).** Keep the Apache licence text and NOTICE, and mark modified files. The Apache §4 terms are from general knowledge and were not fetched this session.
- **Copyright in synthetic data is uncertain.** It is unclear whether purely synthetic, machine-generated data attracts US copyright at all; in the US, facts are not copyrightable. That uncertainty favours the user, but the safe course is to comply as if the licences bind.
- **Lowest-risk repo pattern:** commit no third-party data. Ship a `scripts/fetch_<dataset>.py` that downloads from the official source, plus a tiny team-generated demo CSV. If samples are committed, keep them small and in per-licence folders.

### Gaps
- Kaggle's site Terms of Use for downloaded datasets were not checked.
- The SynthAML figshare item's licence field was not read directly.

## Q7. Does each licence reach the code, or the outputs (alerts, metrics), built on the data?

### Takeaway
None of these data licences reach the team's rule engine code. CC licence conditions attach to the licensed data and to adaptations of it; code that reads a CSV is not an adaptation of the data. CDLA-Sharing explicitly frees "Results". Aggregate metrics (alert counts, precision/recall) are facts. Alert listings or slides that reproduce dataset rows are excerpts, so they carry attribution and NC/SA obligations.

### Cited Findings
- **CDLA Results are unrestricted (§3.5):** "This Agreement imposes no obligations or restrictions on Your Use or Publication of Results". Results are "the outcomes or outputs that You obtain from Your Computational Use of Data". — [CDLA-Sharing-1.0](https://cdla.dev/sharing-1-0/)
- **What counts as an adaptation:** CC Adapted Material is material "derived from or based upon the Licensed Material" and subject to copyright. — [CC BY-NC-SA 4.0 legal code §1](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- **Licences cover only rights-restricted parts:** a CC licence on a compiled work "does not affect parts of the work that are unrestricted by copyright or similar rights". — [CC FAQ](https://creativecommons.org/faq/)
- **No patent or trademark grant:** "Patent and trademark rights are not licensed under this Public License." — [legal code §2(b)(2)](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)

### Inferences
- **Code licence.** The Python code can be MIT or Apache-2.0 whatever dataset is used. ShareAlike does not "infect" code that merely processes data. This is the mainstream reading, but the CC FAQ text read here did not state it explicitly.
- **Slides and demo.** For NC datasets, an alert table showing real dataset rows (account IDs, amounts) is an excerpt of Licensed Material. Credit the dataset on the slide, keep the context NC, and for SAML-D note BY-NC-SA. Summary metrics need no licence, but citing the dataset is good academic practice and is requested by the SAML-D, AMLworld and PaySim pages.
- **Thresholds tuned on the data.** Thresholds are ideas or facts, not copyrightable expression. Using an NC dataset to tune them for a commercial product, though, is itself commercial use of the data (see Q8).

### Gaps
- No CC FAQ text was found in this session that explicitly addresses software or models built from CC-licensed data (the FAQ fetch was truncated).

## Q8. What changes if the tool were ever sold or used by a real bank?

### Takeaway
- **The code is unaffected.** A bank running the tool on its own core data owes nothing to any dataset licensor.
- **The NC datasets are the risk.** SAML-D (BY-NC-SA), AMLNet (BY-NC) and the J.P. Morgan data ("non-commercial purposes") may not be shipped with, demoed for sale with, or used to develop or validate a commercial product without permission.
- **The other licences allow commercial use.** CDLA-Sharing (AMLworld), CC BY-SA (PaySim) and Apache-2.0 (TabFormer) permit it, subject to their sharing and notice terms.

### Cited Findings
- **AMLNet:** "Commercial use is not permitted without prior permission"; enquiries go to s.huda@griffith.edu.au or hudasabin@gmail.com (v2.0). v1.0 says the same for "commercial AML system development and testing". — [AMLNet v2.0 Zenodo API](https://zenodo.org/api/records/16736515/versions/latest); [AMLNet v1.0](https://zenodo.org/records/16736515)
- **AMLNet production use:** the authors say production compliance use requires institution-specific validation, risk assessment and governance. — [AMLNet search summary of Zenodo/arXiv](https://arxiv.org/abs/2509.11595)
- **J.P. Morgan:** the datasets are "available for public use for non-commercial purposes subject to the terms of each dataset's original license". — [J.P. Morgan AI Research synthetic data](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)
- **CDLA-Sharing-1.0:** no commercial-use restriction; you may not add one (§3.3). — [CDLA-Sharing-1.0](https://cdla.dev/sharing-1-0/)

### Inferences
- **Sold as a product:**
  - Remove NC data from the repo, the test fixtures and the sales demos, or get written licences.
  - Shipping AMLworld samples is fine, but they stay CDLA-Sharing.
  - Shipping PaySim samples is fine, but they stay BY-SA.
  - Build the vendor demo dataset in-house.
- **Used by a real bank:** the bank's own data needs no licence. Validating the bank's rules against SAML-D or AMLNet is arguably commercial, because it is directed at the bank's compliance operations, so get permission or use CDLA/BY-SA/own synthetic data.
- **Model risk:** a real bank's model-risk and BSA validation would also expect tuning on its own historical data. Public synthetic sets are not a substitute.

### Gaps
- No licensor-specific statements were found for SAML-D or PaySim on commercial permissions beyond the licence itself.

## Q9. What exactly are the Berka/PKDD'99 terms and the J.P. Morgan synthetic AML data terms?

### Takeaway
- **Berka/PKDD'99:** no licence or terms of use was found on any current official page. The only documented condition, from 1999, limited participation in the discovery challenge to registered PKDD'99 attendees. The data is real (anonymised) Czech bank data.
- **J.P. Morgan:** access is by email request (data type, research purpose, name, affiliation, email). The program says the data is for "non-commercial purposes subject to the terms of each dataset's original license". Eligibility and redistribution are not stated publicly. The dataset-specific licence arrives with the data and was not reviewed. The old AML-specific page now returns 404.

### Cited Findings
- **Berka, current host:** the CTU Relational Learning Repository page has no licence, terms, citation or redistribution text. It describes "606 successful and 76 not successful loans along with their information and transactions" and cites a Web Archive copy of the original challenge page. — [CTU Relational: Financial](https://relational.fel.cvut.cz/dataset/Financial)
- **Berka, 1999 announcement:** "So only people registered for the PKDD'99 can participate in the discovery challenge". The contact is Petr Berka (berka@vse.cz), University of Economics, Prague. The data covers clients, accounts and transactions over several months, loans and credit cards. — [KDnuggets 99:09](https://www.kdnuggets.com/news/99/n09/i2.html)
- **Berka data origin:** described as real anonymised data from a Czech bank. — [search summary of TDS / Charlotte pages](https://webpages.charlotte.edu/mirsad/itcs6265/group1/index.html)
- **Berka documentation:** Berka, P. "Guide to the Financial Data Set", PKDD 2000 Discovery Challenge, Lyon, pp. 87–92. — [VSFS record](https://is.vsfs.cz/publication/1423/en?lang=en)
- **J.P. Morgan request process:** requests go to airdata.requests@jpmorgan.com, stating the type of data, the research purpose, and name, affiliation and email. The page also links the general JPMC terms and conditions. — [J.P. Morgan AI Research synthetic data](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)
- **J.P. Morgan old AML page:** returned HTTP 404 on 2026-11-04. — [old JPM AML page](https://jpmorgan.com/technology/artificial-intelligence/initiatives/synthetic-data/anti-money-laundering)
- **J.P. Morgan AML references:** Assefa et al. (ICAIF 2020) and Borrajo, Veloso & Shah (arXiv:2011.01826). — [J.P. Morgan synthetic data](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data)
- **J.P. Morgan data limitations:** a 2025 paper notes the dataset lacks transaction-level features such as channel and some customer attributes. — [arXiv 2509.18499](https://arxiv.org/pdf/2509.18499)

### Inferences
- **Berka.** With no licence, default copyright and EU/Czech database rights mean no explicit redistribution grant. Kaggle and GitHub mirrors carry licences chosen by uploaders, which do not bind or come from the originator.
  - For a public repo: do not commit Berka data; link to the CTU repository.
  - Berka is also Czech (CZK, 1993–1998 era) and a poor fit for a US core schema.
- **J.P. Morgan.** With 7 days to the deadline, the email-request route is a schedule risk, and the dataset licence (likely restricting redistribution) is unknown until approval. Do not plan the demo around it.

### Gaps
- The original PKDD'99 berka.htm page could not be fetched (web.archive.org is blocked for this tool).
- The actual J.P. Morgan AML dataset licence text, eligibility (for example student vs. faculty) and redistribution clauses were not found publicly.

## Q10. Licence shown on each dataset's official page, and conflicting statements

### Takeaway
The licences the team listed are confirmed for SAML-D, AMLworld, PaySim, TabFormer and AMLNet. SynthAML's article is CC BY 4.0, but the figshare data record's own licence field was not read. Three conflicts to note:

- AMLNet has a deprecated v1 record that listed CC BY 4.0.
- J.P. Morgan has a program-level NC statement but no dataset licence published.
- Berka has no licence at all.

### Cited Findings

| Dataset | Licence on official page | Source / notes |
|---|---|---|
| SAML-D | CC BY-NC-SA 4.0. Citation requested: Oztas et al., IEEE ICEBE 2023, doi:10.1109/ICEBE59045.2023.00028 | [Kaggle](https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml) (via Kaggle API) |
| IBM AMLworld | "Community Data License Agreement - Sharing - Version 1.0". Citation of arXiv 2306.16424 and 2306.11586 "appreciated" | [Kaggle](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml) |
| AMLNet | CC BY-NC 4.0, in both v1.0 (Aug 2025, doi:10.5281/zenodo.16736515) and v2.0 (published 2026-07-07, doi:10.5281/zenodo.21237971, "Commercial use is not permitted without prior permission"). **Conflict:** the earlier, superseded July 2025 record listed CC BY 4.0 and is marked deprecated. | [Zenodo v1.0](https://zenodo.org/records/16736515); [Zenodo v2.0 via API](https://zenodo.org/api/records/16736515/versions/latest); [deprecated record](https://zenodo.org/records/16482144) (via search summary) |
| SynthAML | The article is CC BY 4.0. Data is on figshare, DOI 10.6084/m9.figshare.c.6504421.v1 (files `synthetic_alerts.csv`, `synthetic_transactions.csv`). The figshare licence field was not verified. | [Europe PMC full text](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10539331/fullTextXML); [figshare DOI](https://doi.org/10.6084/m9.figshare.c.6504421.v1) |
| J.P. Morgan AML | Program statement: "non-commercial purposes subject to the terms of each dataset's original license"; request by email. | [JPMC synthetic data](https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data) |
| Berka PKDD'99 | No licence stated. | [CTU Relational](https://relational.fel.cvut.cz/dataset/Financial); [KDnuggets 1999](https://www.kdnuggets.com/news/99/n09/i2.html) |
| IBM TabFormer | The repo is Apache-2.0, with no separate data terms. Data is in `data/credit_card` via git-lfs, or at https://ibm.box.com/v/tabformer-data. "24M records with 12 fields". | [GitHub IBM/TabFormer](https://github.com/IBM/TabFormer) |
| PaySim | CC BY-SA 4.0. Citation requested: Lopez-Rojas, Elmir & Axelsson, EMSS 2016. | [Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1) |

### Inferences
- **PaySim:** the "?" in the brief can be removed; Kaggle shows CC BY-SA 4.0.
- **SynthAML:** "likely CC BY 4.0" is plausible. The article is CC BY 4.0, and Scientific Data usually requires open data licences. Confirm on the figshare page before committing any of it.
- **AMLNet:** cite v2.0 (2026) if using the newest data, and never use the deprecated CC BY record as a licence basis. AMLNet's columns resemble PaySim's (step, type, nameOrig, oldbalanceOrg…). If AMLNet were derived from PaySim's data, PaySim's BY-SA would conflict with AMLNet's NC. Its paper describes its own multi-agent generator, so this is probably only schema reuse, but that was not verified.
- **TabFormer:** the data sits in an Apache-2.0 repo without a separate data licence. The natural reading is that Apache-2.0 covers it. Since Apache-2.0 is a software licence, its fit to data is imperfect, but it is permissive either way.

### Gaps
- The figshare SynthAML licence field was not read (the figshare API search did not return the record; the PMC page was CAPTCHA-blocked).
- The IBM GitHub repos for AMLworld (for example the IBM/AMLworld or Multi-GNN code) were not checked for conflicting licence statements.
- The PaySim GitHub simulator code licence was not checked.
- SAML-D's paper or GitHub was not checked for a different licence from Kaggle's.
