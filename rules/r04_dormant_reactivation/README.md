# r04_dormant_reactivation

**Owner:** Vedanshu · **Ticket:** TRA-25 · **Process:** Account behaviour

**Version 1 (client, 2026-11-11):** no customer-initiated entry for >=180 days (interest and fees do not reset the clock; any deposit does), then **outbound >= $2,000** within 7 days. **Version 2 (ours):** >=$5,000 in or out, or >=10x the prior 12-month average. Natural dormancy exists in SAML-D (10,420 reactivations); recall is proven on injected cases. The backtest demo rule (180 → 120 → 365 days).

Start by copying `rules/r00_example/*` here. Contract: `docs/05-architecture.md`. Rule definition and defaults: `docs/03-rules-catalogue.md`.
