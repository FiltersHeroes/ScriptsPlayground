#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_tagged_internal_links.txt


./scripts/expired_domains.sh ./PAF_tagged_internal_links.txt

rm -r ./PAF_tagged_internal_links.txt
