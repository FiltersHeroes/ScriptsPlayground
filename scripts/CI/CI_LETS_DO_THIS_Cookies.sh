#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/cookies_filters/adblock_cookies.txt
./scripts/expired_domains.sh ./adblock_cookies.txt
rm -r ./adblock_cookies.txt
