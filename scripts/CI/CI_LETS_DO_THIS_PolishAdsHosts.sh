#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/MajkiIT/polish-ads-filter/master/polish-pihole-filters/hostfile.txt

mv hostfile.txt PolishAdsHosts.txt

./scripts/expired_domains.sh ./PolishAdsHosts.txt
rm -r ./PolishAdsHosts.txt
