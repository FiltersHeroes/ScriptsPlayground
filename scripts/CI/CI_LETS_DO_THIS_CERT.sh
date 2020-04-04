#!/bin/bash
# SCRIPT_PATH to miejsce, w którym znajduje się skrypt
SCRIPT_PATH=$(dirname "$0")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH=$(dirname "$0")/../..

cd "$MAIN_PATH" || exit
rm -r "$MAIN_PATH"/novelties/przekrety_CERT.txt
CERT=$SCRIPT_PATH/CERTHole.temp
wget -O "$CERT" https://hole.cert.pl/domains/domains.txt
wget https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/KADhosts.txt
pcregrep -o1 '^.*?0.0.0.0 (.*)' ./KADhosts.txt >> ./KADhosts_temp.txt
rm -rf ./KADhosts.txt
mv ./KADhosts_temp.txt ./KADhosts.txt
sort -u -o ./KADhosts.txt ./KADhosts.txt
sort -u -o "$CERT" "$CERT"
comm -1 -3 ./KADhosts.txt "$CERT" >> "$CERT".2
rm -r "$CERT"
rm -r ./KADhosts.txt
mv "$CERT".2 "$SCRIPT_PATH"/CERTHole_temp.txt
sed -i 's/^www.//g' "$SCRIPT_PATH"/CERTHole_temp.txt
sed -i -r "s|^|\|\||" "$SCRIPT_PATH"/CERTHole_temp.txt
sed -i -r 's|$|\^\$all|' "$SCRIPT_PATH"/CERTHole_temp.txt
sort -u -o "$SCRIPT_PATH"/CERTHole_temp.txt "$SCRIPT_PATH"/CERTHole_temp.txt

NO_SC="true" ./scripts/ECODFF.sh "$SCRIPT_PATH"/CERTHole_temp.txt

EXPIRED=$MAIN_PATH/expired-domains/CERT_temp-expired.txt
UNKNOWN=$MAIN_PATH/expired-domains/CERT_temp-unknown.txt

if [ -f "$EXPIRED" ] || [ -f "$UNKNOWN" ]; then
    sed -i "s|[|][|]||" "$SCRIPT_PATH"/CERTHole_temp.txt
    sed -i 's/\^\$all//g' "$SCRIPT_PATH"/CERTHole_temp.txt
fi

if [ -f "$EXPIRED" ]; then
    comm -2 -3 "$SCRIPT_PATH"/CERTHole_temp.txt "$EXPIRED" >> "$MAIN_PATH"/novelties/przekrety_CERT.txt
    rm -r "$SCRIPT_PATH"/CERTHole_temp.txt
    mv "$MAIN_PATH"/novelties/przekrety_CERT.txt "$SCRIPT_PATH"/CERTHole_temp.txt
fi

if [ -f "$UNKNOWN" ]; then
    comm -2 -3 "$SCRIPT_PATH"/CERTHole_temp.txt "$UNKNOWN" >> "$MAIN_PATH"/novelties/przekrety_CERT.txt
    rm -r "$SCRIPT_PATH"/CERTHole_temp.txt
fi

if [ ! -f "$MAIN_PATH/novelties/przekrety_CERT.txt" ]; then
    mv "$SCRIPT_PATH"/CERTHole_temp.txt "$MAIN_PATH"/novelties/przekrety_CERT.txt
fi

if [ -f "$EXPIRED" ]; then
    rm -r "$EXPIRED"
fi

if [ -f "$UNKNOWN" ]; then
    rm -r "$UNKNOWN"
fi

# GIT_SLUG=$(git ls-remote --get-url | sed "s|https://||g" | sed "s|git@||g" | sed "s|:|/|g")
# git config --global user.email "PolishJarvis@int.pl"
# git config --global user.name "PolishJarvis"
# git add $MAIN_PATH/novelties/przekrety_CERT.txt
# git commit -m "Check [ci skip]"
# git push https://PolishJarvis:${GH_TOKEN}@${GIT_SLUG} HEAD:master > /dev/null 2>&1
