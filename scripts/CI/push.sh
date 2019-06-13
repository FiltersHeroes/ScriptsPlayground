#!/bin/bash
GIT_SLUG=$(git ls-remote --get-url | sed "s|https://||g" | sed "s|git@||g" | sed "s|:|/|g")
git config --global user.email "PolishJarvis@int.pl"
git config --global user.name "PolishJarvis"
git add --all
git commit -m "Check [ci skip]"
git push https://PolishJarvis:${GIT_TOKEN}@${GIT_SLUG} HEAD:master > /dev/null 2>&1
