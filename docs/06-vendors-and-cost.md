<!-- Generated from docs/PLAN.md on 2026-11-11. Edit PLAN.md for research changes; edit this file for working detail. -->

## A5. Vendors, agents and cost
Verafin (Nasdaq) and Abrigo dominate US banks under $10B; a $1–5B bank likely pays **$75–200k/yr licence + $25–75k implementation** [estimated] [S71–S73]. Prices found elsewhere: Unit21 average $157k (Vendr), Lucinity from $54k, ComplyAdvantage $30k fintech package, Marble SaaS from about €2.5k/month [anecdotal]. **Agentic offerings the client asked us to study:** NICE Actimize X-Sight ActOne InvestigateAI (Apr 2025) builds investigation plans from the bank's own policy documents, the closest match to the "policy harness"; Hawk AML Investigative Agent (Mar 2026) is model-agnostic; Verafin Agentic AI Workforce (650+ institutions, Jun 2026); FIS + Anthropic Financial Crimes Agent (May 2026); FNBO runs Verafin agents on Bedrock with ~50% time saved and analysts keeping the decision [anecdotal]. SR 26-2 excludes GenAI and agentic AI, so the bank needs its own agent control set [verified]. Labor: a 4+1 BSA team ≈ **$506k/yr** loaded [estimated]; US+Canada compliance cost $61B/yr [S79]. Independent validation **$15–40k every 1–2 yrs** [estimated]. In-house infrastructure plus LLM ≈ $40–200k/yr at scale; LLM at ~$0.25 per alert ≈ $15k/yr at 5k alerts/month [estimated]; for the prototype, Sonnet at ~3k in / 500 out tokens per alert is ≈ $11/month at 1,000 alerts [S85].

| | Status quo | Buy | Build the harness in-bank (hybrid) |
|---|---|---|---|
| Year 1, ex-labor | ~$0 + exam exposure | **$115–315k** | **$20–60k + build labor**; $40–200k/yr at production scale |
| Steady state | ~$0 | **$90–240k/yr** | **$10–30k/yr** prototype; vendor bake-off optional |

Vendor-neutral recommendation from the discovery brief: build the data foundation, policy harness and audit layer in-bank because every option needs them; bake off our agent against one or two vendors in a 90-day shadow pilot.
