#!/bin/bash

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"/../..

cd "$MAIN_PATH" || exit

cd ./expired-domains
for file in *.txt; do if [[ ! -s $file ]]; then rm -r $file; fi; done

cd ../novelties
for file in *.txt; do if [[ ! -s $file ]]; then rm -r $file; fi; done

cd "$MAIN_PATH" || exit

git config --global user.email "PolishJarvis@int.pl"
git config --global user.name "PolishJarvis"
git add --all
git commit -m "Expired domains check [ci skip]"
git push https://PolishJarvis:${GIT_TOKEN}@github.com/PolishFiltersTeam/ScriptsPlayground.git HEAD:master > /dev/null 2>&1
