#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/cookies_filters/cookies_uB_AG.txt
./scripts/ECODFF.sh ./cookies_uB_AG.txt
rm -r ./cookies_uB_AG.txt
