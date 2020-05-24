#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/ScriptsPlayground/master/expired-domains/KAD-unknown.txt

sed -i 's/ 000//g' ./KAD-unknown.txt
./scripts/DSC.sh -f ./KAD-unknown.txt
