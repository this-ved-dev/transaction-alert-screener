<!-- Generated from docs/PLAN.md on 2026-11-11. Edit PLAN.md for research changes; edit this file for working detail. -->

## 0. Glossary

| Term | Plain meaning |
|---|---|
| **BSA / AML / CFT** | Bank Secrecy Act (1970) and the anti-money-laundering and counter-terrorist-financing program every US bank must run under it. |
| **FinCEN** | Treasury bureau that writes the BSA rules and receives CTRs and SARs. |
| **OCC / Fed / FDIC** | The federal bank examiners. They publish consent orders when a bank's program fails. |
| **FFIEC manual** | The exam manual. Appendix F is its red-flag list. |
| **CTR** | Currency Transaction Report: mandatory when one person moves more than $10,000 of physical cash in one business day. Mechanical. |
| **SAR** | Suspicious Activity Report: confidential report to FinCEN when the bank suspects something. A judgment call by the BSA officer. Nobody outside need-to-know may learn one exists. |
| **Structuring / smurfing** | Splitting cash into pieces under $10,000 to dodge a CTR. A federal crime. |
| **Dormant reactivation** | An account idle for months suddenly moves money. |
| **Pass-through** | Money comes in and leaves almost immediately. A layering sign. Debasish's first named pain point. |
| **Mule** | An account, often a duped person's, that receives and forwards illicit funds. |
| **Funnel account** | Many people pay into one account; it is then emptied. |
| **Typology / red flag / rule** | A named laundering pattern / a regulator-listed indicator / our parameterised test for it. |
| **Hit / alert / case** | One rule firing once on one customer / what the analyst sees, one per customer per day with all hits attached / an escalated alert. |
| **Disposition** | The decision on an alert plus its reason. |
| **Four-eyes** | A second person must approve every SAR recommendation. |
| **Audit trail** | Immutable who/what/when/why. |
| **CIF** | Customer Information File: the customer-level ID. One customer, many accounts. |
| **KYC / CDD / risk tier** | Know Your Customer. Low/Medium/High at onboarding; High gets tighter thresholds. |
| **Core** | The bank's ledger system (Fiserv, Jack Henry, FIS). We read its nightly export. |
| **Tran code** | The core's transaction type code. Mapping these to cash/wire/ACH/ATM is the dirtiest part of any monitoring project. |
| **Business day** | Posting day. Saturday cash counts on Monday. **Night drop**: after-hours deposit box, posts next business day. |
| **ACH / wire / P2P** | Electronic rails: slow batch, same-day and expensive, and Zelle-style person-to-person. |
| **OFAC / SDN** | Treasury sanctions office and its Specially Designated Nationals list. Free CSV. |
| **FATF black / grey list** | Countries with weak AML controls, updated three times a year. |
| **314(a) / 314(b)** | FinCEN's secret name-search list (not public) and bank-to-bank information sharing. |
| **False positive / lift** | An alert that is nothing (90–95% of rule alerts by common claim) / precision divided by the base rate, the honest metric at 0.1% base rates. |
| **ATL/BTL / shadow mode / backtest** | Sampling above and below a threshold / running a rule over past data without producing live alerts. |
| **MRM** | Model risk management. SR 11-7 was replaced by SR 26-2 in April 2026; SR 26-2 excludes generative and agentic AI from its scope. |
| **Consent order / NPRM / GLBA / SOC 2** | Public enforcement action / proposed regulation / customer-data protection law / the security audit report vendors give banks. |
| **Investigator agent** | An LLM-driven assistant that gathers evidence for an alert and drafts a recommendation and narrative. In this design it never decides and never closes. |
| **SAML-D / Tide** | The two synthetic datasets on disk (D1). |
| **DuckDB / Parquet** | In-process analytical SQL engine / columnar file format. Our rules compute layer. |
| **ISO 20022** | The international XML/JSON standard for financial messages. Wires (Fedwire, CHIPS, Swift) and instant rails (FedNow, RTP) use it on the wire; ACH, cards, cheques, Zelle and teller cash do not. |
| **camt.054 / entry** | The ISO 20022 "bank-to-customer debit/credit notification". One `Ntry` (entry) per booked debit or credit on an account, whatever rail produced it. The shape of our canonical record. |
| **BankTransactionCode (BkTxCd)** | ISO 20022's open taxonomy of what an entry *is*: Domain / Family / SubFamily, e.g. `PMNT/CNTR/CDPT` = cash deposit at the counter. About 1,500 permitted triplets, free to download. Our category column. |
| **Nacha / SEC code** | The US ACH file standard (fixed-width 94-character records) and its Standard Entry Class codes (PPD, CCD, WEB, TEL, IAT). Not ISO. |
| **ISO 8583 / X9.100-187** | The card and ATM message standard / the cheque image-exchange standard. Neither is ISO 20022. |
| **CIF in ISO 20022** | The customer number travels as a party identifier with scheme code `CUST`. Risk tier has no ISO slot and lives in our own party extension. |
| **Cycle / project / milestone** | Linear's sprint / a body of work with an owner / a checkpoint inside a project. |

---
