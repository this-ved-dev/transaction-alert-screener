# Field requirements for the bank's two feeds

Debasish (2026-11-11): "Build assuming the fields don't match and plan a mapping step. Tell us which fields you need and we'll ask the vendors." This sheet is what we send. Every field maps to the canonical record in `docs/04-data-plan.md` § D6. Account identifiers must be delivered as text (leading zeros matter). We never need names or SSNs of customers for the rules; the customer id is enough.

## Feed 1: nightly core-banking export (cash, ACH, cheques, cards, fees, interest)

| Field we need | Why | Status |
|---|---|---|
| Account number | aggregation and the per-account audit view | **required** |
| Customer id (CIF) | same-day splitting "across ALL their accounts" and CTR aggregation per person | **required** if it exists on the row; otherwise a separate account→customer file |
| Posting date and effective date | business-day roll-forward for weekend and night-drop cash | **required** (posting); effective nice-to-have |
| Amount and debit/credit indicator | everything | **required** |
| Transaction code and its description | mapping to cash / ACH / cheque / card / fee / interest (ISO 20022 BankTransactionCode) | **required**, plus the code list document |
| Cash indicator | CTR and structuring rules | **required** or **derivable** from the code list |
| Branch or teller id | cross-branch structuring (v2) | nice-to-have |
| Channel (teller, ATM, night drop, online, mobile) | ATM anomaly, night-drop roll-forward, P2P detection | nice-to-have; ATM derivable from the code list |
| Memo / description free text | shown to the analyst, escaped | nice-to-have |
| Running balance | small-account tightening for P2P | nice-to-have |

## Feed 2: wire feed (domestic and international, in and out)

| Field we need | Why | Status |
|---|---|---|
| Account number (our side) | aggregation | **required** |
| Value date | dormancy and pass-through windows | **required** |
| Amount and direction | everything | **required** |
| Counterparty name, account, bank identifier (ABA or BIC) | new-beneficiary rule, pass-through counterparty check | **required** |
| Counterparty country | high-risk jurisdiction rule on outbound wires abroad | **required** (or **derivable** from the BIC) |
| Wire reference / UETR | audit trail and de-duplication across hourly runs | nice-to-have |
| Originator / remittance text | shown to the analyst, escaped | nice-to-have |

## Questions for ops and the vendors
1. Is a P2P (Zelle) activity present in either feed, and how is it coded? (Our P2P rule stays in shadow until this is answered.)
2. Can you share a 50-row anonymised sample of each feed, or just the column layout document?
3. How often can each feed be produced: nightly only, or hourly incrementals?
4. Does the core export carry a customer-level id, or only account numbers?
