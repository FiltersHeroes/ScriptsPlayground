#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/social_filters_uB_AG.txt
./scripts/expired_domains.sh ./social_filters_uB_AG.txt
rm -r ./social_filters_uB_AG.txt
