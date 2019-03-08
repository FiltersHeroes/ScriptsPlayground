#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/scroll_film_suplement.txt

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/scroll_film_AG.txt

mv scroll_film_suplement.txt PAF_scroll_film_suplement.txt
mv scroll_film_AG.txt PAF_scroll_film_AG.txt


./scripts/expired_domains.sh ./PAF_scroll_film_suplement.txt
./PAF_scroll_film_AG.txt

rm -r ./PAF_scroll_film_suplement.txt
rm -r ./PAF_scroll_film_AG.txt
