#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_other_widgets.txt

./scripts/expired_domains.sh ./PAF_other_widgets.txt

rm -r ./PAF_other_widgets.txt
