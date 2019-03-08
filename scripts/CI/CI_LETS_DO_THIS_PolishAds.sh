#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/MajkiIT/polish-ads-filter/master/polish-adblock-filters/adblock.txt


./scripts/expired_domains.sh ./adblock.txt
rm -r ./adblock.txt
