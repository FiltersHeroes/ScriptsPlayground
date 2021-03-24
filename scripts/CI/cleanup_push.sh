#!/bin/bash

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH="$(dirname "$(realpath -s "$0")")"/../..

cd "$MAIN_PATH" || exit

cd ./expired-domains || exit
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
