#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/sections/hostsplus.txt

mv hostsplus.txt KADhosts.txt

./scripts/ECODFF.sh ./KADhosts.txt
rm -r ./KADhosts.txt
