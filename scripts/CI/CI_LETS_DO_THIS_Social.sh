#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/adblock_social_list.txt

./scripts/expired_domains.sh ./adblock_social_list.txt
rm -r ./adblock_social_list.txt
