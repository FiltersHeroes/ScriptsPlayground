#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_pop-ups_supp.txt


./scripts/expired_domains.sh ./PAF_pop-ups_supp.txt

rm -r ./PAF_pop-ups_supp.txt
