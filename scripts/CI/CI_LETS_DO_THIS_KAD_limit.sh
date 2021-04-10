#!/bin/bash
SCRIPT_PATH=$(dirname "$(realpath -s "$0")")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH=$(git -C "$SCRIPT_PATH" rev-parse --show-toplevel)

cd "$MAIN_PATH"/ || exit

{
    cut -d' ' -f1 ./expired-domains/KAD_0*-unknown_limit.txt
    cut -d' ' -f1 ./expired-domains/KAD_0*-unknown_no_internet.txt
} >> ./KAD.txt

rm -rf ./expired-domains/KAD_0*-unknown_limit.txt
rm -rf ./expired-domains/KAD_0*-unknown_no_internet.txt

sed -i "s|^|0.0.0.0 |" ./KAD.txt
sort -u -o ./KAD.txt ./KAD.txt

./scripts/ECODFF.sh ./KAD.txt
rm -r ./KAD.txt
rm -rf ./expired-domains/KAD-unknown_no_internet.txt


cd "$MAIN_PATH"/expired-domains/ || exit

cat ./KAD_0*-expired.txt >> ./KAD-expired.txt
cat ./KAD_0*-parked.txt >> ./KAD-parked.txt
cat ./KAD_0*-unknown.txt >> ./KAD-unknown.txt
cat ./KAD_0*-unknown_limit.txt >> ./KAD-unknown_limit.txt
cat ./KAD_10-expired.txt >> ./KAD-expired.txt
cat ./KAD_10-parked.txt >> ./KAD-parked.txt
cat ./KAD_10-unknown.txt >> ./KAD-unknown.txt
cat ./KAD_10-unknown_limit.txt >> ./KAD-unknown_limit.txt

sort -u -o ./KAD-expired.txt ./KAD-expired.txt
sort -u -o ./KAD-parked.txt ./KAD-parked.txt
sort -u -o ./KAD-unknown.txt ./KAD-unknown.txt
sort -u -o ./KAD-unknown_limit.txt ./KAD-unknown_limit.txt

rm -rf ./KAD_0*-expired.txt ./KAD_0*-parked.txt ./KAD_0*-unknown.txt ./KAD_0*-unknown_limit.txt
rm -rf ./KAD_10-expired.txt ./KAD_10-parked.txt ./KAD_10-unknown.txt ./KAD_10-unknown_limit.txt
