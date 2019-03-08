#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/push_suplement.txt

mv push_suplement.txt PAF_push_supp.txt

./scripts/expired_domains.sh ./PAF_push_supp.txt

rm -r ./PAF_push_supp.txt
