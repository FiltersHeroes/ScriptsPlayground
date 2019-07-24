#!/bin/bash

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH=$(dirname "$0")/../..

cd "$MAIN_PATH"

cd ./expired-domains
for file in *.txt; do if [[ ! -s $file ]]; then rm -r $file; fi; done

cd ./LWS
for file in *.txt; do if [[ ! -s $file ]]; then rm -r $file; fi; done

cd $MAIN_PATH

git config --global user.email "PolishJarvis@int.pl"
git config --global user.name "PolishJarvis"
git add --all
git commit -m "Check [ci skip]"
git push https://PolishJarvis:${GIT_TOKEN}@github.com/PolishFiltersTeam/ScriptsPlayground.git HEAD:master > /dev/null 2>&1
