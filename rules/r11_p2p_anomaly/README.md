# r11_p2p_anomaly

**Owner:** Natalie · **Ticket:** TRA-43 · **Process:** Counterparty & rails

P2P anomaly: >=$2,500/day, or >=10 distinct P2P counterparties in 7 days, or >=5x the 90-day baseline, tighter on small accounts. **Mode: shadow (P3).** The client (2026-11-11) puts P2P last and is not sure it appears in the export at all; the demo P2P rail is synthetic and disclosed. Goes live only if a real export sample shows a P2P rail and the client asks.

Start by copying `rules/r00_example/*` here. Contract: `docs/05-architecture.md`. Rule definition and defaults: `docs/03-rules-catalogue.md`.
