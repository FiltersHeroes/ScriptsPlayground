#!/bin/bash

# Expired Domains Remover For Filterlists
# v1.1
# Usage: EDRFF.sh pathToSections listOfExpiredDomains.txt TLD (optional)

SECTIONS_DIR=$1

removeE() {
    grep -v -f "$2" "$1" > "$1".temp
    mv "$1".temp "$1"
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
