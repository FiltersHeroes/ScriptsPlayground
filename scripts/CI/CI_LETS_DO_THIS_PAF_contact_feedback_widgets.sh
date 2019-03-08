#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_contact_feedback_widgets.txt

./scripts/expired_domains.sh ./PAF_contact_feedback_widgets.txt

rm -r ./PAF_contact_feedback_widgets.txt
