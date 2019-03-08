#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/tla_autoreklamy_suplement.txt

mv tla_autoreklamy_suplement.txt PAF_backgrounds_self-advertising_supp.txt

./scripts/expired_domains.sh ./PAF_backgrounds_self-advertising_supp.txt

rm -r ./PAF_backgrounds_self-advertising_supp.txt
