#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_backgrounds_self-advertising.txt

./scripts/expired_domains.sh ./PAF_backgrounds_self-advertising.txt

rm -r ./PAF_backgrounds_self-advertising.txt
