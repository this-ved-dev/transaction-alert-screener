#!/usr/bin/env bash
# Downloads every public reference asset the screener uses and records a SHA-256 for each.
# All URLs were checked on 2026-11-11 (docs/04-data-plan.md § D7). Nothing here is committed; see .gitignore.
set -euo pipefail
cd "$(dirname "$0")"
LOG="fetch_log.txt"; : > "$LOG"
get() { # get <subdir> <url> [filename]
  local dir="$1" url="$2" name="${3:-$(basename "${2%%\?*}")}"
  mkdir -p "$dir"; echo "-> $dir/$name"
  curl -fsSL --retry 3 -A "transaction-alert-screener/0.0.1" -o "$dir/$name" "$url"
  echo "$(date -u +%FT%TZ)  $(shasum -a 256 "$dir/$name" | cut -d' ' -f1)  $dir/$name  $url" >> "$LOG"
}
# OFAC (US public domain)
get ofac "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV"
get ofac "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADD.CSV"
get ofac "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ALT.CSV"
get ofac "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONS_PRIM.CSV"
# UN Security Council consolidated list
get un "https://scsanctions.un.org/resources/xml/en/consolidated.xml" consolidated.xml
# OpenSanctions bulk (CC BY-NC 4.0: class use only; a real bank licenses it or uses OFAC direct)
for ds in us_ofac_sdn us_sanctions us_fincen_special_measures peps; do
  get "opensanctions/$ds" "https://data.opensanctions.org/datasets/latest/$ds/targets.simple.csv"
  get "opensanctions/$ds" "https://data.opensanctions.org/datasets/latest/$ds/index.json"
done
# ISO 20022 external code sets, BankTransactionCode codification and camt.054 schema (free, no login)
get iso20022 "https://www.iso20022.org/sites/default/files/media/file/ExternalCodeSets_XLSX.zip"
get iso20022 "https://www.iso20022.org/sites/default/files/media/file/BTC_ExternalCodeListDescription_Nov2025.docx"
get iso20022 "https://www.iso20022.org/sites/default/files/media/file/BTC_Codification_21March2024.xlsx"
get iso20022 "https://www.iso20022.org/sites/default/files/documents/messages/camt/schemas/camt.054.001.13.xsd"
# FDIC Summary of Deposits: NJ branches of $1–5B banks, 2025 (public). Rename to the fictional bank in the US layer.
get . "https://api.fdic.gov/banks/sod?filters=YEAR:2025%20AND%20STALPBR:NJ%20AND%20ASSET:%5B1000000%20TO%205000000%5D&fields=NAMEFULL,NAMEBR,CITYBR,STALPBR,ZIPBR,DEPSUMBR,ASSET,BRNUM,UNINUMBR,BRSERTYP,SIMS_LATITUDE,SIMS_LONGITUDE&limit=10000&format=json" branches_fdic_nj_raw.json
# ISO 3166 country codes
get . "https://raw.githubusercontent.com/datasets/country-codes/main/data/country-codes.csv" country_codes.csv
echo "FATF lists are NOT fetched: the site blocks scripts. Read https://www.fatf-gafi.org/en/countries/black-and-grey-lists.html in a browser and update country_risk.csv with verified_on." | tee -a "$LOG"
echo "done; log in $LOG"
