# r02_structuring_multi_day

**Owner:** Vedant · **Ticket:** TRA-16 · **Process:** Cash & CTR

**Version 1 (client, 2026-11-11):** "near-limit deposits between $9,000 and $10,000": any single cash deposit in [$9,000, $10,000] fires. **Version 2 (ours, after backtest and client walkthrough):** (a) >=3 cash deposits $2,000–$9,999 within 5 business days totalling >=$15,000; (b) 30-day cash-in >=$25,000 with none above $9,999. Graded on SAML-D Smurfing (v2a must reproduce 90% precision / 57% recall). The Oct 2025 SAR FAQ is shown in the evidence panel: a near-limit deposit alone is a review item, not SAR grounds.

Start by copying `rules/r00_example/*` here. Contract: `docs/05-architecture.md`. Rule definition and defaults: `docs/03-rules-catalogue.md`.
