#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

cut -d' ' -f1 ./expired-domains/KAD-unknown_limit.txt >> ./KAD.txt

rm -rf ./expired-domains/KAD-unknown_limit.txt

touch ./expired-domains/KAD-unknown_limit.txt

sed -i "s|^|0.0.0.0 |" ./KAD.txt

NO_RM="true" ./scripts/ECODFF.sh ./KAD.txt
rm -r ./KAD.txt
