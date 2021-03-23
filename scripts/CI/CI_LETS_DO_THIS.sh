#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath -s "$0")")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH=$(git -C "$SCRIPT_PATH" rev-parse --show-toplevel)

cd "$MAIN_PATH" || exit

for i in "$@"; do
    F_NAME=$(basename "$i")
    if [[ "$F_NAME" = "hostsplus.txt" ]]; then
        F_NAME="KADhosts.txt"
    elif [[ "$F_NAME" = "suplement.txt" ]]; then
        F_NAME="polish_rss_filters_supp.txt"
    fi
    wget -O "$i"
    ./scripts/ECODFF.sh "$F_NAME"
    rm -rf ./"$F_NAME"
done
