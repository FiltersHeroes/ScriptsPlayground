#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/..

wget https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/sections/hostsplus.txt

./scripts/expired_domains.sh $sciezka/../hostsplus.txt
rm -r ./hostsplus.txt
