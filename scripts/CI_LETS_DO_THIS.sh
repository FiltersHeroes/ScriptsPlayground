#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/..

wget -O ./PPB.txt https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PPB.txt

./scripts/expired_domains.sh ./PPB.txt

git push https://PolishJarvis:${GIT_TOKEN}@${TRAVIS_REPO_SLUG} HEAD:master > /dev/null 2>&1
