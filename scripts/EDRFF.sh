#!/bin/bash

# Expired Domains Remover For Filterlists
# v1.0
# Usage: EDRFF.sh pathToSections listOfExpiredDomains.txt

SECTIONS_DIR=$1

if [ -d "${SECTIONS_DIR}" ]; then
    for file in "${SECTIONS_DIR}"/*.txt; do
        grep -v -f $2 $file > $file.temp
        mv $file.temp $file
    done
fi
