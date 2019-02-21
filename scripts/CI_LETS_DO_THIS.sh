#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/..

wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB_uBlock_AdGuard.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishRSSFilters/master/polish_rss_filters.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/adblock_social_list.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/social_filters_uB_AG.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/KAD/master/KAD.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/sections/hostsplus.txt

./scripts/expired_domains.sh $sciezka/../PPB.txt $sciezka/../PPB_uBlock_AdGuard.txt $sciezka/../polish_rss_filters.txt $sciezka/../adblock_social_list.txt $sciezka/../social_filters_uB_AG.txt $sciezka/../KAD.txt $sciezka/../hostsplus.txt

rm -r ./PPB.txt
rm -r ./PPB_uBlock_AdGuard.txt
rm -r ./polish_rss_filters.txt
rm -r ./adblock_social_list.txt
rm -r ./social_filters_uB_AG.txt
rm -r ./KAD.txt
rm -r ./hostsplus.txt


git add --all
git commit -m "Check [ci skip]"
git push https://PolishJarvis:${GIT_TOKEN}@github.com/PolishFiltersTeam/ExpiredDomainsFilterListsPlayground.git HEAD:master > /dev/null 2>&1
