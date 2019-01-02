#!/bin/bash

git config --global user.email "PolishJarvis@int.pl"
git config --global user.name "PolishJarvis"

ost_commit_katalog=$(dirname $(git diff-tree --no-commit-id --name-only -r master))
ost_commit_plik=$(git diff-tree --no-commit-id --name-only -r master)

if [ "$ost_commit_katalog" == "Test" ]; then
    glowna_lista="Test.txt"
elif [ "$ost_commit_katalog" == "Test/uBO_AG" ]; then
    glowna_lista="Test.txt Test_uBO_AG.txt"
fi

./scripts/VICHS.sh $glowna_lista
