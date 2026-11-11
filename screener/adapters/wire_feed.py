"""Adapter for the bank wire feed.

Layout unknown until the vendor answers docs/14-field-requirements.md. Field lists use canonical
column names (screener/schema.py) and match the sheet's "Wire feed" column; `branch_id`,
`conductor`, `cash_detail` and `card_detail` do not apply. Read every id column as text: account
numbers keep their leading zeros.
"""

REQUIRED = [
    "entry_id",
    "account_id",
    "amount",
    "credit_debit",
    "booking_ts",
    "value_date",
    "debtor",
    "creditor",
    "debtor_account",
    "creditor_account",
    "debtor_agent",
    "creditor_agent",
    "cif_id",
]
DERIVABLE = [
    "currency",
    "is_reversal",
    "status",
    "business_date",
    "btc_domain",
    "btc_family",
    "btc_subfamily",
    "btc_proprietary",
    "channel",
    "source_message",
    "raw_ref",
]  # DMCT vs XBCT and the counterparty country from the BIC; channel is always WIRE_ROOM
NICE_TO_HAVE = ["instrument_refs", "purpose", "memo"]


def load(path):
    raise NotImplementedError(
        "wire feed layout not received yet (TRA-58, docs/14-field-requirements.md). Required "
        "fields: " + ", ".join(REQUIRED) + "; derivable: " + ", ".join(DERIVABLE)
    )
