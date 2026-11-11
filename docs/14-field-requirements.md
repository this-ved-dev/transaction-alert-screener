# Field requirements for the bank's two feeds

Debasish (2026-11-11): "Build assuming the fields don't match and plan a mapping step. Tell us which fields you need and we'll ask the vendors." This sheet is what we send. Please forward it to both vendors; each reads its own column.

**You do not need to rename or reformat anything.** We map your columns to our record ourselves (the canonical entry schema, `screener/schema.py`; ISO 20022 origin of each column in `docs/05-architecture.md`). Any row we cannot map is set aside with a reason, never dropped. We never need customer names, SSNs or addresses for the rules: the customer id is enough.

**Account numbers must be delivered and read as text.** Leading zeros are part of the number; Excel and most CSV readers drop them. Our adapters read every id column as text.

Marks: **required** = the rules cannot run without it · **derivable** = we compute it from other fields or the code list (send it anyway if you have it) · **nice-to-have** = improves the evidence an analyst sees or a later rule version; we run without it · — = does not apply to this feed.

| Our column | What we need from the feed | Core export | Wire feed | Why |
|---|---|---|---|---|
| `entry_id` | Unique id per row: transaction or sequence number (wires: the bank's wire reference) | **required** | **required** | De-duplicates rows across hourly incremental runs; the evidence link an analyst clicks |
| `account_id` | Our customer's account number, as text | **required** | **required** | Every rule and the per-account audit view key on it |
| `amount` | Transaction amount, dollars and cents | **required** | **required** | Every threshold compares against it |
| `currency` | Currency code | derivable | derivable | We assume USD; if any wire is booked in another currency, this becomes required |
| `credit_debit` | Debit/credit indicator, or a signed amount | **required** | **required** | Cash in and cash out are totalled separately; pass-through needs money in versus out |
| `is_reversal` | Reversal or correction flag | derivable | derivable | A reversed deposit must not count toward the day's cash total; the code list or wire type usually marks reversals and returns |
| `status` | Posted versus pending (memo-posted) | derivable | derivable | Rules count posted money only; we assume posted items only unless you tell us otherwise |
| `booking_ts` | Posting date, and the time if available | **required** | **required** | Daily rules need the date; hourly runs and the 24-, 48- and 72-hour windows need the time |
| `value_date` | Effective (value) date | derivable | **required** | Core: catches back-dated postings; we use the posting date if absent. Wires: when money actually moves, for dormancy and pass-through windows |
| `business_date` | Nothing; we compute it. Tell us the daily posting cut-off time | derivable | derivable | Cash totals are per business day; weekend, holiday and after-cut-off postings roll forward |
| `btc_domain`, `btc_family`, `btc_subfamily` | Transaction code and description on each row, plus the full code list marking cash, ATM, reversal, fee and interest codes (or a cash indicator on each row) | **required** | derivable | Core: one mapping from your codes to cash, ATM, ACH, cheque, card, fee or interest drives every rule. Wires: always a wire; domestic versus cross-border comes from the counterparty country |
| `btc_proprietary` | Nothing extra: your transaction code, kept as is (and the ACH SEC code if present) | derivable | derivable | An auditor sees your original code beside the ISO code |
| `channel` | Channel: teller, ATM, night drop, online, mobile | derivable | derivable | The ATM rule and night-drop roll-forward need it; derived from the code list or teller/terminal id if not a column. Wires: always the wire room |
| `instrument_refs` | Cheque number, ACH trace number; for wires the UETR or Fedwire IMAD/OMAD | nice-to-have | nice-to-have | Lets the analyst find the item in the core or the wire system |
| `debtor`, `creditor` (name) | Counterparty name: the sender for incoming, the beneficiary for outgoing (and their customer id if they bank with us) | nice-to-have | **required** | The new-beneficiary and pass-through rules need to know who sent or received the money |
| `debtor`, `creditor` (country) | Counterparty country | — | derivable | High-risk jurisdiction rule on outbound wires abroad; we take it from the BIC unless the feed gives it (the beneficiary's country can differ from the bank's) |
| `debtor_account`, `creditor_account` | Counterparty account number, as text | nice-to-have | **required** | A beneficiary is a bank plus an account; the new-beneficiary and transfer-splitting rules key on it |
| `debtor_agent`, `creditor_agent` | Counterparty bank: ABA routing number or BIC, and its country | nice-to-have | **required** | Completes the beneficiary identity; the BIC gives the country for the high-risk jurisdiction rule |
| `branch_id` | Branch, or a teller id we can map to a branch | nice-to-have | — | Cross-branch splitting (version 2) and the CTR's transaction location |
| `conductor` | Person who made the transaction at the counter, if not the account owner | nice-to-have | — | A CTR reports the person present separately from the owner; third-party cash deposits are a structuring sign |
| `cif_id` | Account owner's customer id (CIF), on each row or in a separate account-to-customer file | **required** | **required** | Your same-day splitting definition adds deposits across all of a customer's accounts; one alert per customer per day |
| `purpose` | Purpose or business function code | — | nice-to-have | Shown to the analyst next to the wire |
| `memo` | Free-text description, memo or remittance information | nice-to-have | nice-to-have | Shown to the analyst word for word (safely escaped); never used to decide a flag |
| `cash_detail` | Note denominations and counts | nice-to-have | — | Evidence for cash flags; rarely in exports, fine without |
| `card_detail` | ATM or card terminal id and its state (or a terminal list), merchant category, masked card number | nice-to-have | — | The "two states in 24 hours" leg of the ATM rule needs the terminal's state; without it that leg stays off |
| `source_message` | Nothing; we set it | derivable | derivable | Records which feed each row came from |
| `raw_ref` | Nothing; we set it (file name and line) | derivable | derivable | Points an auditor to the exact line in the file you sent |

`typology_label`, the last column of our record, is a test label that only our synthetic data carries; we never ask the bank for it.

## Please also send
1. The column layout of each feed (names, types, lengths), its delimiter and encoding, and whether it has a header row.
2. The transaction code list with descriptions.
3. A 50-row anonymised sample of each feed. Invented names and account numbers are fine; we need the real codes and formats.

## Questions for ops and the vendors
1. Is P2P (Zelle) activity present in either feed, and how is it coded? (Our P2P rule stays in shadow until this is answered.)
2. How often can each feed be produced: nightly only, or hourly incrementals?
3. Does the core export carry a customer id, or only account numbers?
4. What is the daily posting cut-off time, and do night-drop deposits post on the next business day?
5. Does the core export include pending (memo-posted) items, or posted items only?
6. Is any wire booked in a currency other than USD?
