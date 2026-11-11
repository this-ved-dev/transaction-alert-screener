<!-- Generated from docs/PLAN.md on 2026-11-11 (client reply applied). Edit PLAN.md for research changes; edit this file for working detail. -->

## A6. Friction and our answers

| Friction | Evidence | Answer |
|---|---|---|
| Scattered data, no warehouse, Excel and VB scripts | kickoff | Canonical schema with one adapter per source; hourly incremental batch, no streaming (client: "not real-time") |
| Core data access; tran codes; account-only keys | [S86–S88] | Editable tran-code map; CIF keys; reconciliation report per load |
| Vendor risk (OCC 2023-17; SOC 2) | [S89] | Everything runs inside the bank, including the LLM on the bank's credentials |
| Alert flood; auto-close is a finding | Block, USAA, OCC 2026 | Encode current thresholds as v1; shadow mode; no auto-close by rules or agent |
| Undocumented tuning | FFIEC [S18] | Maker-checker threshold changes in the admin console; backtest attached |
| Switching needs a parallel run | Shinhan | Daily alert export |
| SAR confidentiality | [S12][S15][S16] | Role-gated status; access log |
| Black-box fear; SR 26-2 silent on agents | [S91][S20] | Deterministic rules decide what is flagged; the agent only gathers and drafts, with citations; autonomy grows in graduated steps against measured accuracy |
| Seasonal peak Nov–Jan with contract analysts | kickoff | Seasonal threshold profiles (versioned) and a queue that onboards a contractor in minutes |
