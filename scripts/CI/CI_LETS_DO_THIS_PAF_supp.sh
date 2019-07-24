#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/tla_autoreklamy_suplement.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_tagged_internal_links.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/newslettery_suplement.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/inne_nie_dla_ff.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/inne_AG.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/inne_bez_html.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/inne_html.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/inne_suplement.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_pop-ups_supp.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/push_suplement.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/scroll_film_suplement.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB/uBO_AG/scroll_film_AG.txt

mv tla_autoreklamy_suplement.txt PAF_backgrounds_self-advertising_supp.txt
mv newslettery_suplement.txt PAF_newsletters_supp.txt
mv inne_nie_dla_ff.txt PAF_inne_nie_dla_ff.txt
mv inne_AG.txt PAF_inne_AG.txt
mv inne_bez_html.txt PAF_inne_bez_html.txt
mv inne_suplement.txt PAF_inne_suplement.txt
mv push_suplement.txt PAF_push_supp.txt
mv scroll_film_suplement.txt PAF_scroll_film_suplement.txt
mv scroll_film_AG.txt PAF_scroll_film_AG.txt

./scripts/expired_domains.sh ./PAF_backgrounds_self-advertising_supp.txt ./PAF_tagged_internal_links.txt ./PAF_newsletters_supp.txt ./PAF_inne_nie_dla_ff.txt ./PAF_inne_AG.txt ./PAF_inne_bez_html.txt ./PAF_inne_html.txt ./PAF_inne_suplement.txt ./PAF_pop-ups_supp.txt ./PAF_push_supp.txt ./PAF_scroll_film_suplement.txt ./PAF_scroll_film_AG.txt

rm -r ./PAF_backgrounds_self-advertising_supp.txt
rm -r ./PAF_tagged_internal_links.txt
rm -r ./PAF_newsletters_supp.txt
rm -r ./PAF_inne_nie_dla_ff.txt
rm -r ./PAF_inne_AG.txt
rm -r ./PAF_inne_bez_html.txt
rm -r ./PAF_inne_html.txt
rm -r ./PAF_inne_suplement.txt
rm -r ./PAF_pop-ups_supp.txt
rm -r ./PAF_push_supp.txt
rm -r ./PAF_scroll_film_suplement.txt
rm -r ./PAF_scroll_film_AG.txt
