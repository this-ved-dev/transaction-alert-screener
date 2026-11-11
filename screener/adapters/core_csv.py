"""Adapter for the bank core export.

Layout unknown until the vendor answers docs/14-field-requirements.md.
"""

REQUIRED = [
    "account_id",
    "posting_date",
    "effective_date",
    "amount",
    "debit_credit",
    "transaction_code",
    "transaction_description",
]
DERIVABLE = [
    "cash_flag",
    "channel",
    "business_date",
]  # from the transaction code list and the calendar
NICE_TO_HAVE = ["customer_id", "branch_id", "teller_id", "memo", "running_balance"]


def load(path):
    raise NotImplementedError(
        "core export layout not received yet (TRA-58). Required fields: "
        + ", ".join(REQUIRED)
        + "; derivable: "
        + ", ".join(DERIVABLE)
    )
