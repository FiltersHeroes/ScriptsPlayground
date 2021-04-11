#!/bin/bash

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH="$(dirname "$(realpath -s "$0")")"/../..

cd "$MAIN_PATH" || exit

rm -rf ./split/*

cd ./expired-domains || exit

rm -rf ./KADhosts-expired.txt ./KADhosts-parked.txt ./KADhosts-unknown.txt ./KADhosts-unknown_limit.txt
rm -rf ./*-unknown_no_internet.txt

cat ./KADhosts_0*-expired.txt >> ./KADhosts-expired.txt
cat ./KADhosts_0*-unknown.txt >> ./KADhosts-unknown.txt
cat ./KADhosts_0*-unknown_limit.txt >> ./KADhosts-unknown_limit.txt

sort -u -o ./KADhosts-expired.txt ./KADhosts-expired.txt
sort -u -o ./KADhosts-unknown.txt ./KADhosts-unknown.txt
sort -u -o ./KADhosts-unknown_limit.txt ./KADhosts-unknown_limit.txt

rm -rf ./KADhosts_0*-expired.txt ./KADhosts_0*-parked.txt ./KADhosts_0*-unknown.txt ./KADhosts_0*-unknown_limit.txt

for file in *.txt; do if [[ ! -s $file ]]; then rm -r "$file"; fi; done

cd "$MAIN_PATH" || exit

if [ "$GITHUB_ACTIONS" = "true" ]; then
    git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git config --global user.name "github-actions[bot]"
else
    git config --global user.email "PolishJarvis@int.pl"
    git config --global user.name "PolishJarvis"
fi

git add --all
git commit -m "Expired domains check" -m "[ci skip]"

if [ "$GITHUB_ACTIONS" = "true" ]; then
    git push https://github-actions[bot]:"${GIT_TOKEN}"@github.com/PolishFiltersTeam/ScriptsPlayground.git HEAD:master > /dev/null 2>&1
else
    git push https://PolishJarvis:"${GIT_TOKEN}"@github.com/PolishFiltersTeam/ScriptsPlayground.git HEAD:master > /dev/null 2>&1
fi
