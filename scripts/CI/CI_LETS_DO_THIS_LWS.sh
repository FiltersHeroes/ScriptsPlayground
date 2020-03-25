#!/bin/bash
# SCRIPT_PATH to miejsce, w którym znajduje się skrypt
SCRIPT_PATH=$(dirname "$0")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH=$(dirname "$0")/../..

cd "$MAIN_PATH" || exit
rm -r "$MAIN_PATH"/novelties/podejrzane_LWS.txt
LWS=$SCRIPT_PATH/LWS.temp
python3 "$SCRIPT_PATH"/../findSuspiciousDomains_LWS.py >> "$LWS"
sed -i -r "s|^|\|\||" "$LWS"
sed -i -r 's|$|\^\$all|' "$LWS"
wget https://raw.githubusercontent.com/PolishFiltersTeam/KAD/master/sections/podejrzane_inne_oszustwa.txt
sed -i -r "s/^[|][|]www[0-9]\.//" ./podejrzane_inne_oszustwa.txt
sed -i -r "s/^[|][|]www\.//" ./podejrzane_inne_oszustwa.txt
#sed -i -r "s/^[|][|]//" ./podejrzane_inne_oszustwa.txt
#sed -i -r "s|^|\|\||" ./podejrzane_inne_oszustwa.txt
sort -u -o ./podejrzane_inne_oszustwa.txt ./podejrzane_inne_oszustwa.txt
sort -u -o "$LWS" "$LWS"
comm -1 -3 ./podejrzane_inne_oszustwa.txt "$LWS" >> "$LWS".2
rm -r "$LWS"
rm -r ./podejrzane_inne_oszustwa.txt
mv "$LWS".2 "$SCRIPT_PATH"/LWS_temp.txt

NO_SC="true" ./scripts/ECODFF.sh "$SCRIPT_PATH"/LWS_temp.txt

EXPIRED=$MAIN_PATH/expired-domains/LWS_temp-expired.txt
UNKNOWN=$MAIN_PATH/expired-domains/LWS_temp-unknown.txt

if [ -f "$EXPIRED" ] || [ -f "$UNKNOWN" ]; then
    sed -i "s|[|][|]||" "$SCRIPT_PATH"/LWS_temp.txt
    sed -i 's/\^\$all//g' "$SCRIPT_PATH"/LWS_temp.txt
fi

if [ -f "$EXPIRED" ]; then
    comm -2 -3 "$SCRIPT_PATH"/LWS_temp.txt "$EXPIRED" >> "$MAIN_PATH"/novelties/podejrzane_LWS.txt
    rm -r "$SCRIPT_PATH"/LWS_temp.txt
    mv "$MAIN_PATH"/novelties/podejrzane_LWS.txt "$SCRIPT_PATH"/LWS_temp.txt
fi

if [ -f "$UNKNOWN" ]; then
    comm -2 -3 "$SCRIPT_PATH"/LWS_temp.txt "$UNKNOWN" >> "$MAIN_PATH"/novelties/podejrzane_LWS.txt
    rm -r "$SCRIPT_PATH"/LWS_temp.txt
fi

if [ ! -f "$MAIN_PATH/novelties/podejrzane_LWS.txt" ]; then
    mv "$SCRIPT_PATH"/LWS_temp.txt "$MAIN_PATH"/novelties/podejrzane_LWS.txt
fi

sed -i -r "s|^|\|\||" "$MAIN_PATH"/novelties/podejrzane_LWS.txt
sed -i -r 's|$|\^\$all|' "$MAIN_PATH"/novelties/podejrzane_LWS.txt

if [ -f "$EXPIRED" ]; then
    rm -r "$EXPIRED"
fi

if [ -f "$UNKNOWN" ]; then
    rm -r "$UNKNOWN"
fi

# GIT_SLUG=$(git ls-remote --get-url | sed "s|https://||g" | sed "s|git@||g" | sed "s|:|/|g")
# git config --global user.email "PolishJarvis@int.pl"
# git config --global user.name "PolishJarvis"
# git add $MAIN_PATH/novelties/podejrzane_LWS.txt
# git commit -m "Check [ci skip]"
# git push https://PolishJarvis:${GH_TOKEN}@${GIT_SLUG} HEAD:master > /dev/null 2>&1
