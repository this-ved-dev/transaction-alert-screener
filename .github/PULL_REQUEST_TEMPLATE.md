## TRA-___: <title>

**What** — one or two sentences.

**Why** — the client need or ticket context.

**How tested** — commands run, fixture or answer-key results, measured volume if a rule changed.

**Screenshots** — required for any UI change.

### Checklist
- [ ] One Linear issue, linked by branch name (`<name>/tra-NN-...`)
- [ ] Tests added or updated; `make test` green locally
- [ ] No data rows committed (pre-commit large-file hook passed)
- [ ] `rule.yaml` version bumped if parameters or SQL changed; backtest delta noted
- [ ] Docs touched: `docs/…`
- [ ] If labelled `contract`: all four owners reviewed
