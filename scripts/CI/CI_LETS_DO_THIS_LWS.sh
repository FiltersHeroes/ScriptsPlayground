#!/bin/bash
# SCRIPT_PATH to miejsce, w którym znajduje się skrypt
SCRIPT_PATH=$(dirname "$0")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH=$(dirname "$0")/../..

cd "$MAIN_PATH" || exit
rm -r "$MAIN_PATH"/novelties/podejrzane_LWS.txt
LWS=$SCRIPT_PATH/LWS.temp
python3 "$SCRIPT_PATH"/../findSuspiciousDomains_LWS.py >> "$LWS"
wget https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/KADhosts.txt
pcregrep -o1 '^.*?0.0.0.0 (.*)' ./KADhosts.txt >> ./KADhosts_temp.txt
sed -i 's/^www.//g' "$LWS"
rm -rf ./KADhosts.txt
mv ./KADhosts_temp.txt ./KADhosts.txt
sort -u -o ./KADhosts.txt ./KADhosts.txt
sort -u -o "$LWS" "$LWS"
comm -1 -3 ./KADhosts.txt "$LWS" >> "$LWS".2
rm -r "$CERT"
rm -r ./KADhosts.txt
mv "$LWS".2 "$SCRIPT_PATH"/LWS_temp.txt
sed -i 's/^www.//g' "$SCRIPT_PATH"/LWS_temp.txt
sed -i -r "s|^|\|\||" "$SCRIPT_PATH"/LWS_temp.txt
sed -i -r 's|$|\^\$all|' "$SCRIPT_PATH"/LWS_temp.txt
sort -u -o "$SCRIPT_PATH"/LWS_temp.txt "$SCRIPT_PATH"/LWS_temp.txt

NO_SC="true" ./scripts/ECODFF.sh "$SCRIPT_PATH"/LWS_temp.txt

EXPIRED=$MAIN_PATH/expired-domains/LWS_temp-expired.txt
UNKNOWN=$MAIN_PATH/expired-domains/LWS_temp-unknown.txt
UNKNOWN_LIMIT=$MAIN_PATH/expired-domains/LWS_temp-unknown_limit.txt

if [ -f "$EXPIRED" ] || [ -f "$UNKNOWN" ] || [ -f "$UNKNOWN_LIMIT" ]; then
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
    mv "$MAIN_PATH"/novelties/podejrzane_LWS.txt "$SCRIPT_PATH"/LWS_temp.txt
fi

if [ -f "$UNKNOWN_LIMIT" ]; then
    comm -2 -3 "$SCRIPT_PATH"/LWS_temp.txt "$UNKNOWN_LIMIT" >> "$MAIN_PATH"/novelties/podejrzane_LWS.txt
    rm -r "$SCRIPT_PATH"/LWS_temp.txt
    mv "$MAIN_PATH"/novelties/podejrzane_LWS.txt "$SCRIPT_PATH"/LWS_temp.txt
fi

if [ -f "$EXPIRED" ]; then
    rm -r "$EXPIRED"
fi

if [ -f "$UNKNOWN" ]; then
    rm -r "$UNKNOWN"
fi

if [ -f "$UNKNOWN_LIMIT" ]; then
    rm -r "$UNKNOWN_LIMIT"
fi

if [ -f "$SCRIPT_PATH"/LWS_temp.txt ]; then
    sort -u -o "$SCRIPT_PATH"/LWS_temp.txt "$SCRIPT_PATH"/LWS_temp.txt
fi

if [ -f "$MAIN_PATH"/novelties/LWS_whitelist.txt ]; then
    sort -u -o "$MAIN_PATH"/novelties/LWS_whitelist.txt "$MAIN_PATH"/novelties/LWS_whitelist.txt
    comm -23 "$SCRIPT_PATH"/LWS_temp.txt "$MAIN_PATH"/novelties/LWS_whitelist.txt > "$MAIN_PATH"/novelties/podejrzane_LWS.txt
    mv "$MAIN_PATH"/novelties/podejrzane_LWS.txt "$SCRIPT_PATH"/LWS_temp.txt
fi

while IFS= read -r domain; do
    parked=$(host -t ns "${domain}" | grep -E "parkingcrew.net|parklogic.com|sedoparking.com")
    if [ ! -z "${parked}" ]; then
        echo "$domain" >> "$SCRIPT_PATH"/LWS_parked.txt
    fi
done < "$SCRIPT_PATH"/LWS_temp.txt

if [ -f "$SCRIPT_PATH"/LWS_parked.txt ]; then
    sort -u -o "$SCRIPT_PATH"/LWS_parked.txt "$SCRIPT_PATH"/LWS_parked.txt
    comm -23 "$SCRIPT_PATH"/LWS_temp.txt "$SCRIPT_PATH"/LWS_parked.txt > "$MAIN_PATH"/novelties/podejrzane_LWS.txt
    rm -rf "$SCRIPT_PATH"/LWS_parked.txt
fi

if [ ! -f "$MAIN_PATH/novelties/podejrzane_LWS.txt" ]; then
    mv "$SCRIPT_PATH"/LWS_temp.txt "$MAIN_PATH"/novelties/podejrzane_LWS.txt
fi

if [ -f "$SCRIPT_PATH"/LWS_temp.txt ]; then
    rm -rf "$SCRIPT_PATH"/LWS_temp.txt
fi

sed -i -r "s|^|\|\||" "$MAIN_PATH"/novelties/podejrzane_LWS.txt
sed -i -r 's|$|\^\$all|' "$MAIN_PATH"/novelties/podejrzane_LWS.txt

# GIT_SLUG=$(git ls-remote --get-url | sed "s|https://||g" | sed "s|git@||g" | sed "s|:|/|g")
# git config --global user.email "PolishJarvis@int.pl"
# git config --global user.name "PolishJarvis"
# git add $MAIN_PATH/novelties/podejrzane_LWS.txt
# git commit -m "Check [ci skip]"
# git push https://PolishJarvis:${GH_TOKEN}@${GIT_SLUG} HEAD:master > /dev/null 2>&1
