#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/..

wget https://raw.githubusercontent.com/PolishFiltersTeam/KAD/master/KAD.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/sections/hostsplus.txt

./scripts/expired_domains.sh $sciezka/../KAD.txt $sciezka/../hostsplus.txt
rm -r ./KAD.txt
rm -r ./hostsplus.txt

git add --all
git commit -m "Check [ci skip]"
git push https://PolishJarvis:${GIT_TOKEN}@github.com/PolishFiltersTeam/ExpiredDomainsFilterListsPlayground.git HEAD:master > /dev/null 2>&1
