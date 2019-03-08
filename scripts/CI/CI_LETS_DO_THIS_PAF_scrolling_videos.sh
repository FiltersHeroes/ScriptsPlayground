#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_scrolling_videos.txt


./scripts/expired_domains.sh ./PAF_scrolling_videos.txt

rm -r ./PAF_scrolling_videos.txt
