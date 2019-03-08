#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/newslettery_suplement.txt

mv newslettery_suplement.txt PAF_newsletters_supp.txt

./scripts/expired_domains.sh ./PAF_newsletters_supp.txt

rm -r ./PAF_newsletters_supp.txt
