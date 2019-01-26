#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/..

wget -O ./PAF_backgrounds_self-advertising.txt https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/PAF_backgrounds_self-advertising.txt

./scripts/expired_domains.sh $sciezka/../PPB.txt

git push https://PolishJarvis:${GIT_TOKEN}@${TRAVIS_REPO_SLUG} HEAD:master > /dev/null 2>&1
