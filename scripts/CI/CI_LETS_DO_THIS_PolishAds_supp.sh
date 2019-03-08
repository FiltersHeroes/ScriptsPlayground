#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/MajkiIT/polish-ads-filter/master/polish-adblock-filters/adblock_ublock.txt


./scripts/expired_domains.sh ./adblock_ublock.txt
rm -r ./adblock_ublock.txt

