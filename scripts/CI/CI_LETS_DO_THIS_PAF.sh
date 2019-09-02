#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_arrows.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_backgrounds_self-advertising.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_contact_feedback_widgets.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_newsletters.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_other_widgets.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_pop-ups.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_push.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_scrolling_videos.txt

./scripts/ECODFF.sh PAF_arrows.txt PAF_backgrounds_self-advertising.txt PAF_contact_feedback_widgets.txt PAF_newsletters.txt PAF_other_widgets.txt PAF_pop-ups.txt PAF_push.txt PAF_scrolling_videos.txt

rm -r ./PAF_arrows.txt
rm -r ./PAF_backgrounds_self-advertising.txt
rm -r ./PAF_contact_feedback_widgets.txt
rm -r ./PAF_newsletters.txt
rm -r ./PAF_other_widgets.txt
rm -r ./PAF_pop-ups.txt
rm -r ./PAF_push.txt
rm -r ./PAF_scrolling_videos.txt
