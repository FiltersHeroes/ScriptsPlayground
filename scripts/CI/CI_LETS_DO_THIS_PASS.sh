#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAntiAnnoyingSpecialSupplement/master/polish_rss_filters.txt

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAntiAnnoyingSpecialSupplement/master/sections/suplement.txt

mv suplement.txt polish_rss_filters_supp.txt

./scripts/ECODFF.sh ./polish_rss_filters.txt ./polish_rss_filters_supp.txt
rm -r ./polish_rss_filters.txt
rm -r ./polish_rss_filters_supp.txt
