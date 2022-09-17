#!/bin/bash
SCRIPT_PATH=$(dirname "$(realpath -s "$0")")

cd "$SCRIPT_PATH"/ || exit

SFLB_VERSION=$(python3 SFLB.py -v | sed 's/Super Filter Lists Builder //')

xgettext SFLB.py -o ./locales/SFLB.pot --package-name="SFLB" --package-version="$SFLB_VERSION" --copyright-holder="Filters Heroes"
