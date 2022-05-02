#!/bin/bash

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH="$(dirname "$(realpath -s "$0")")"/../..

cd "$MAIN_PATH" || exit

rm -rf ./split/*

cd ./expired-domains || exit

cat ./Cert_0*-expired.txt >> ./Cert-expired.txt
cat ./Cert_0*-unknown.txt >> ./Cert-unknown.txt
cat ./Cert_0*-unknown_limit.txt >> ./Cert-unknown_limit.txt
sort -u -o ./Cert-expired.txt ./Cert-expired.txt
sort -u -o ./Cert-unknown.txt ./Cert-unknown.txt
sort -u -o ./Cert-unknown_limit.txt ./Cert-unknown_limit.txt
rm -rf ./Cert_0*-expired.txt ./Cert_0*-parked.txt ./Cert_0*-unknown.txt ./Cert_0*-unknown_limit.txt

rm -rf ./KAD_0*-expired.txt ./KAD_0*-parked.txt ./KAD_0*-unknown.txt ./KAD_0*-unknown_limit.txt

rm -rf ./KADhosts-expired.txt ./KADhosts-parked.txt ./KADhosts-unknown.txt ./KADhosts-unknown_limit.txt
rm -rf ./*-unknown_no_internet.txt

cat ./KADhosts_0*-expired.txt >> ./KADhosts-expired.txt
cat ./KADhosts_0*-unknown.txt >> ./KADhosts-unknown.txt
cat ./KADhosts_0*-unknown_limit.txt >> ./KADhosts-unknown_limit.txt

sort -u -o ./KADhosts-expired.txt ./KADhosts-expired.txt
sort -u -o ./KADhosts-unknown.txt ./KADhosts-unknown.txt
sort -u -o ./KADhosts-unknown_limit.txt ./KADhosts-unknown_limit.txt


rm -rf ./KADhosts_0*-expired.txt ./KADhosts_0*-parked.txt ./KADhosts_0*-unknown.txt ./KADhosts_0*-unknown_limit.txt
rm -rf ./KAD_0*-expired.txt ./KAD_0*-parked.txt ./KAD_0*-unknown.txt ./KADhosts_0*-unknown_limit.txt
rm -rf ./Cert_0*-expired.txt ./Cert_0*-parked.txt ./Cert_0*-unknown.txt

for file in *.txt; do if [[ ! -s $file ]]; then rm -r "$file"; fi; done

cd "$MAIN_PATH" || exit

if [ "$GITHUB_ACTIONS" = "true" ]; then
    git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git config --global user.name "github-actions[bot]"
else
    git config --global user.email "35114429+PolishRoboDog@users.noreply.github.com"
    git config --global user.name "PolishRoboDog"
fi

git add --all
git commit -m "Expired domains check" -m "[ci skip]"

if [ "$GITHUB_ACTIONS" = "true" ]; then
    git push https://github-actions[bot]:"${GIT_TOKEN}"@github.com/FiltersHeroes/ScriptsPlayground.git HEAD:master > /dev/null 2>&1
else
    git push https://PolishRoboDog:"${GIT_TOKEN}"@github.com/FiltersHeroes/ScriptsPlayground.git HEAD:master > /dev/null 2>&1
fi
