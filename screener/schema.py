"""Canonical entry schema: one row per booked entry, shaped like an ISO 20022 camt.054 ``Ntry``.

Every adapter writes ``ENTRY``; rules read it through the ``entries`` view and never see
``typology_label``. Column-to-XPath table: docs/05-architecture.md § Canonical entry schema.
Arrow fields are nullable on purpose: ``validate()`` enforces ``REQUIRED`` so a bad row is set
aside with a reason instead of failing the whole load (client rule: never drop).
"""

from __future__ import annotations

import json

import polars as pl
import pyarrow as pa

from screener import btc

PARTY = pa.struct([("name", pa.string()), ("cif_id", pa.string()), ("country", pa.string())])
AGENT = pa.struct([("routing", pa.string()), ("bic", pa.string()), ("country", pa.string())])
MONEY = pa.decimal128(18, 2)

ENTRY = pa.schema(
    [
        ("entry_id", pa.string()),
        ("account_id", pa.string()),
        ("amount", MONEY),  # always positive; direction is credit_debit
        ("currency", pa.string()),
        ("credit_debit", pa.string()),
        ("is_reversal", pa.bool_()),
        ("status", pa.string()),
        ("booking_ts", pa.timestamp("us")),  # bank local time, no offset: same result on any host
        ("value_date", pa.date32()),
        ("business_date", pa.date32()),
        ("btc_domain", pa.string()),
        ("btc_family", pa.string()),
        ("btc_subfamily", pa.string()),
        ("btc_proprietary", pa.string()),
        ("channel", pa.string()),
        (
            "instrument_refs",
            pa.struct(
                [
                    ("end_to_end_id", pa.string()),
                    ("uetr", pa.string()),
                    ("trace_no", pa.string()),
                    ("cheque_no", pa.string()),
                ]
            ),
        ),
        ("debtor", PARTY),
        ("creditor", PARTY),
        ("debtor_account", pa.string()),
        ("creditor_account", pa.string()),
        ("debtor_agent", AGENT),
        ("creditor_agent", AGENT),
        ("branch_id", pa.string()),
        ("conductor", PARTY),  # person at the counter, may differ from the account owner
        ("cif_id", pa.string()),  # account owner's customer number
        ("purpose", pa.string()),
        ("memo", pa.string()),  # stored verbatim, rendered escaped, never parsed
        ("cash_detail", pa.list_(pa.struct([("denomination", MONEY), ("count", pa.int32())]))),
        (
            "card_detail",
            pa.struct(
                [("masked_pan", pa.string()), ("mcc", pa.string()), ("terminal_id", pa.string())]
            ),
        ),
        ("source_message", pa.string()),
        ("raw_ref", pa.string()),
        ("typology_label", pa.string()),  # hidden from rules and injectors
    ]
)

REQUIRED = (
    "entry_id",
    "account_id",
    "amount",
    "currency",
    "credit_debit",
    "is_reversal",
    "status",
    "booking_ts",
    "value_date",
    "business_date",
    "btc_domain",
    "btc_family",
    "btc_subfamily",
    "channel",
    "cif_id",
    "source_message",
)
CHANNELS = (
    "TELLER",
    "BRANCH",
    "NIGHT_DROP",
    "ATM",
    "POS",
    "ONLINE",
    "MOBILE",
    "WIRE_ROOM",
    "SYSTEM",
)
HIT_COLUMNS = ("customer_id", "account_id", "business_day", "matched_txn_ids", "computed_values")


def validate(table: pa.Table) -> tuple[pa.Table, list[dict]]:
    """Split entries into (valid, rejected). Each rejected item is ``{"reason", "raw_row"}``.

    The caller adds load_batch_id, source and created_at and writes them to ``rejected_entry``.
    """
    triplet = pl.concat_str(["btc_domain", "btc_family", "btc_subfamily"], separator="/")
    known = ["/".join(t) for t in btc.triplets()]
    checks = [(pl.col(c).is_null(), pl.lit(f"missing {c}")) for c in REQUIRED] + [
        (pl.col("amount") <= 0, pl.lit("amount is not positive")),
        (~pl.col("currency").str.contains(r"^[A-Z]{3}$"), pl.lit("currency is not ISO 4217")),
        (~pl.col("credit_debit").is_in(["CRDT", "DBIT"]), pl.lit("credit_debit not CRDT/DBIT")),
        (~pl.col("status").is_in(["BOOK", "PDNG"]), pl.lit("status not BOOK/PDNG")),
        (~pl.col("channel").is_in(CHANNELS), pl.lit("unknown channel ") + pl.col("channel")),
        (~triplet.is_in(known), pl.lit("BankTransactionCode not in ISO codification ") + triplet),
        (
            pl.col("business_date") < pl.col("booking_ts").dt.date(),
            pl.lit("business_date before booking date"),
        ),
    ]
    reason = pl.lit(None, dtype=pl.String)
    for failed, message in reversed(checks):  # first failing check wins
        reason = pl.when(failed).then(message).otherwise(reason)
    df = pl.from_arrow(table).with_columns(reason.alias("_reason"))

    rejected = []
    for row in df.filter(pl.col("_reason").is_not_null()).to_dicts():
        rejected.append({"reason": row.pop("_reason"), "raw_row": json.dumps(row, default=str)})
    valid = df.filter(pl.col("_reason").is_null()).drop("_reason").to_arrow().cast(ENTRY)
    return valid, rejected
