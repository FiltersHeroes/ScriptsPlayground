#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_backgrounds_self-advertising_supp.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_tagged_internal_links.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_newsletters_supp.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_other_elements_supp.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_pop-ups_supp.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_push_supp.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_scrolling_videos_supp.txt


./scripts/ECODFF.sh PAF_backgrounds_self-advertising_supp.txt PAF_tagged_internal_links.txt PAF_newsletters_supp.txt PAF_other_elements_supp.txt PAF_pop-ups_supp.txt PAF_push_supp.txt PAF_scrolling_videos_supp.txt


rm -r ./PAF_backgrounds_self-advertising_supp.txt
rm -r ./PAF_tagged_internal_links.txt
rm -r ./PAF_newsletters_supp.txt
rm -r ./PAF_other_elements_supp.txt
rm -r ./PAF_pop-ups_supp.txt
rm -r ./PAF_push_supp.txt
rm -r ./PAF_scrolling_videos_supp.txt
