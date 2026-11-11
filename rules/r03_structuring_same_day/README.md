# r03_structuring_same_day

**Owner:** Vedant · **Ticket:** TRA-17 · **Process:** Cash & CTR

**Version 1 (client, 2026-11-11):** "one customer, two or more deposits at or under $10,000, adding past $10,000 across ALL their accounts, one flag per customer per day". Params: min_count 2, max_single 10000, day_total_over 10000; key = customer across all accounts. **Version 2 (ours):** >=2 branches/channels with a day total of $8,000–$10,000. A split day is also a CTR candidate (R01) by design. Fixtures: $5,000 + $5,000.01 fires; $5,000 + $5,000 does not; a single $12,000 deposit is R01 only.

Start by copying `rules/r00_example/*` here. Contract: `docs/05-architecture.md`. Rule definition and defaults: `docs/03-rules-catalogue.md`.
