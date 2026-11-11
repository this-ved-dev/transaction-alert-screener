# r09_new_beneficiary

**Owner:** Natalie · **Ticket:** TRA-42 · **Process:** Counterparty & rails

Wire to new beneficiary: first outbound wire >=$10,000 (>=$3,000 High tier) to a beneficiary unseen in 90 days; weight up at >=3 new beneficiaries in 7 days. Debasish's second pain point.

Start by copying `rules/r00_example/*` here. Contract: `docs/05-architecture.md`. Rule definition and defaults: `docs/03-rules-catalogue.md`.
