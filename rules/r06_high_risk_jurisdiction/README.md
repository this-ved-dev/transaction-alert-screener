# r06_high_risk_jurisdiction

**Owner:** Natalie · **Ticket:** TRA-41 · **Process:** Counterparty & rails

High-risk jurisdiction transfers against a point-in-time country-risk table (FATF black/grey as of the transaction date, plus the bank's internal tier). **Scope per the 2026-11-11 reply:** the bank is domestic with some outbound wires abroad, so version 1 covers outbound wires (PMNT/ICDT/XBCT) first; inbound cross-border carries a lower weight. Priority P1 (wires first).

Start by copying `rules/r00_example/*` here. Contract: `docs/05-architecture.md`. Rule definition and defaults: `docs/03-rules-catalogue.md`.
