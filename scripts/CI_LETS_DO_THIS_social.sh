#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/adblock_social_list.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/social_filters_uB_AG.txt
./scripts/expired_domains.sh $sciezka/../adblock_social_list.txt $sciezka/../social_filters_uB_AG.txt
rm -r ./adblock_social_list.txt
rm -r ./social_filters_uB_AG.txt
git add --all
git commit -m "Check [ci skip]"
git push https://PolishJarvis:${GIT_TOKEN}@github.com/PolishFiltersTeam/ExpiredDomainsFilterListsPlayground.git HEAD:master > /dev/null 2>&1
