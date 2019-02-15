#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/..

wget https://raw.githubusercontent.com/MajkiIT/polish-ads-filter/master/polish-adblock-filters/adblock.txt
wget https://raw.githubusercontent.com/MajkiIT/polish-ads-filter/master/polish-adblock-filters/adblock_ublock.txt
wget https://raw.githubusercontent.com/MajkiIT/polish-ads-filter/master/polish-pihole-filters/hostfile.txt

mv $sciezka/../hostfile.txt $sciezka/../hostfile_MajkiIT.txt

./scripts/expired_domains.sh $sciezka/../adblock.txt $sciezka/../adblock_ublock.txt $sciezka/../hostfile_MajkiIT.txt
rm -r ./adblock.txt
rm -r ./adblock_ublock.txt
rm -r ./hostfile_MajkiIT.txt
git add --all
git commit -m "Check [ci skip]"
git push https://PolishJarvis:${GIT_TOKEN}@github.com/PolishFiltersTeam/ExpiredDomainsFilterListsPlayground.git HEAD:master > /dev/null 2>&1
