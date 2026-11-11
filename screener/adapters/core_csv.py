"""Adapter for the bank core export.

Layout unknown until the vendor answers docs/14-field-requirements.md. Field lists use canonical
column names (screener/schema.py) and match the sheet's "Core export" column; `purpose` does not
apply. Read every id column as text: account numbers keep their leading zeros.
"""

REQUIRED = [
    "entry_id",
    "account_id",
    "amount",
    "credit_debit",
    "booking_ts",
    "btc_domain",
    "btc_family",
    "btc_subfamily",
    "cif_id",
]
DERIVABLE = [
    "currency",
    "is_reversal",
    "status",
    "value_date",
    "business_date",
    "btc_proprietary",
    "channel",
    "source_message",
    "raw_ref",
]  # from the transaction code list, the posting date, the calendar and the file itself
NICE_TO_HAVE = [
    "instrument_refs",
    "debtor",
    "creditor",
    "debtor_account",
    "creditor_account",
    "debtor_agent",
    "creditor_agent",
    "branch_id",
    "conductor",
    "memo",
    "cash_detail",
    "card_detail",
]


def load(path):
    raise NotImplementedError(
        "core export layout not received yet (TRA-58, docs/14-field-requirements.md). Required "
        "fields: " + ", ".join(REQUIRED) + "; derivable: " + ", ".join(DERIVABLE)
    )
