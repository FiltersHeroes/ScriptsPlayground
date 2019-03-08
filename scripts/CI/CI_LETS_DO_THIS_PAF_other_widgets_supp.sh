#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/widgety_nie_dla_ff.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/widgety_AG.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/widgety_bez_html.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/widgety_suplement.txt


mv widgety_nie_dla_ff.txt PAF_widgety_nie_dla_ff.txt
mv widgety_AG.txt PAF_widgety_AG.txt
mv widgety_bez_html.txt PAF_widgety_bez_html.txt
mv widgety_suplement.txt PAF_widgety_suplement.txt

./scripts/expired_domains.sh ./PAF_widgety_nie_dla_ff.txt ./PAF_widgety_AG.txt ./PAF_widgety_bez_html.txt ./PAF_widgety_suplement.txt

rm -r ./PAF_widgety_nie_dla_ff.txt
rm -r ./PAF_widgety_AG.txt
rm -r ./PAF_widgety_bez_html.txt
rm -r ./PAF_widgety_suplement.txt
