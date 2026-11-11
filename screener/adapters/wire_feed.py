"""Adapter for the bank wire feed.

Layout unknown until the vendor answers docs/14-field-requirements.md.
"""

REQUIRED = [
    "account_id",
    "value_date",
    "amount",
    "direction",
    "counterparty_name",
    "counterparty_account",
    "counterparty_bank_id",
    "counterparty_country",
]
DERIVABLE = ["btc_subfamily", "business_date"]  # DMCT vs XBCT from the counterparty country
NICE_TO_HAVE = ["customer_id", "reference", "uetr", "memo", "originator_name"]


def load(path):
    raise NotImplementedError(
        "wire feed layout not received yet (TRA-58). Required fields: "
        + ", ".join(REQUIRED)
        + "; derivable: "
        + ", ".join(DERIVABLE)
    )
