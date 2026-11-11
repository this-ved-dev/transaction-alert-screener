# Reference data

Run `./fetch_lists.sh` to download every public list; it writes `fetch_log.txt` with a SHA-256 per file.
Downloaded files are gitignored. Committed here: the hand-maintained tables.

| File | What | Source | Licence |
|---|---|---|---|
| `country_risk.csv` | point-in-time country tiers (FATF black/grey with effective dates, bank internal tier) | FATF site (read in a browser; blocks scripts), SAML-D paper | public / policy |
| `tran_code_map.csv` | source transaction type → ISO 20022 BankTransactionCode triplet + channel | BTC description v8.0 Nov 2025 | ISO 20022 free use |
| `holidays_us.csv` | US federal holidays in the SAML-D window | OPM | public |
| `ofac/` | SDN, ADD, ALT, Consolidated | sanctionslistservice.ofac.treas.gov | US public domain |
| `un/` | UN Security Council consolidated list | scsanctions.un.org | free |
| `opensanctions/` | us_ofac_sdn, us_sanctions, us_fincen_special_measures, peps | data.opensanctions.org | CC BY-NC 4.0 (class use only) |
| `iso20022/` | external code sets, BTC codification, camt.054.001.13 XSD | iso20022.org | free |
| `iso20022/btc_codification.csv` (committed) | the 1,561 permitted BankTransactionCode triplets, from `BTC_Codification_21March2024.xlsx` (SHA-256 `7070c3bf…7c2b`) via `screener.btc.refresh()` | iso20022.org | ISO 20022 free use |
| `branches_fdic_nj_raw.json` | NJ branches of $1–5B banks, 2025 | api.fdic.gov/banks/sod | US public |
| `country_codes.csv` | ISO 3166 | github.com/datasets/country-codes | mixed open |

Not available anywhere: FinCEN 314(a) lists (mocked in fixtures), Zelle participant schema, core-vendor export layouts.
