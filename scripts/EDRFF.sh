#!/bin/bash

# Expired Domains Remover For Filterlists
# v1.2 (beta)
# Usage: EDRFF.sh pathToSections listOfExpiredDomains.txt TLD (optional)

SCRIPT_PATH=$(dirname "$(realpath -s "$0")")

if [ -z "$MAIN_PATH" ]; then
    MAIN_PATH=$(git -C "$SCRIPT_PATH" rev-parse --show-toplevel)
fi

SECTIONS_DIR=$1

TMP_DIR="$MAIN_PATH"/tmp

if [ ! -d "$TMP_DIR" ]; then
    mkdir -p "$TMP_DIR"
fi

removeE() {
    cp "$2" "$TMP_DIR"/expired1.tmp
    cp "$2" "$TMP_DIR"/expired2.tmp
    sed -i "s/^/||/" "$TMP_DIR"/expired1.tmp
    sed -i "s/$/|/" "$TMP_DIR"/expired2.tmp
    grep -v -f "$TMP_DIR"/expired1.tmp "$1" > "$1".temp
    mv "$1".temp "$1"
    sed -i "$(sed 's:.*:s/&//ig:' "$TMP_DIR"/expired2.tmp)" "$1"
    rm -rf "$TMP_DIR"/*
}

if [ -d "${SECTIONS_DIR}" ]; then
    for file in "${SECTIONS_DIR}"/*.txt; do
        # Remove domains only with specific TLD
        if [ "$3" ]; then
            grep ".$3$" "$2" > "$file".temp_"$3"
            removeE "$file" "$file".temp_"$3"
            rm -rf "$file".temp_"$3"
        else
            removeE "$file" "$2"
        fi
    done
fi

rm -rf "$TMP_DIR"
