#!/bin/bash
# Sciezka to miejsce, w którym znajduje się skrypt
sciezka=$(dirname "$0")

cd $sciezka/../..

wget https://raw.githubusercontent.com/PolishFiltersTeam/KAD/master/KAD.txt

sed -i 's/ 000//g' ./KAD-unknown.txt
./scripts/DSC.sh -f ./KAD-unknown.txt

pageComma=$(pcregrep -o1 '^([a-z0-9-~][^\/\*\|\@\"\!]*?)(#|\$\$)' ./KAD.txt)
pagePipe=$(pcregrep -o3 '(domain)(=)([^,]+)' ./KAD.txt)
pageDoublePipe=$(pcregrep -o1 '^@?@?\|\|([^\/|^|$]+)' ./KAD.txt)
hosts=$(pcregrep -o1 '^.*?0.0.0.0 (.*)' ./KAD.txt)
FILTERLIST="KAD"
TEMPORARY=$MAIN_PATH/${FILTERLIST}.temp

if [ ! -d "$MAIN_PATH/expired-domains" ]; then
    mdkir "$MAIN_PATH"/expired-domains
    touch "$MAIN_PATH"/expired-domains/.keep
fi

if [ -z "$NO_RM" ] ; then
    rm -rf "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt
    rm -rf "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
    rm -rf "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown_limit.txt
    rm -rf "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown_no_internet.txt
    rm -rf "$MAIN_PATH"/expired-domains/"$FILTERLIST"-parked.txt
fi

{
    echo "$pageComma"
    echo "$pagePipe"
    echo "$pageDoublePipe"
    echo "$hosts"
} >>"$TEMPORARY"

sed -i "s/[|]/\n/g" "$TEMPORARY"
sed -i "s/\,/\n/g" "$TEMPORARY"
sed -i "s/\ /\n/g" "$TEMPORARY"
sed -i "s|\~||" "$TEMPORARY"
sed -i '/[/\*]/d' "$TEMPORARY"
sed -ni '/\./p' "$TEMPORARY"
sed -i -r "s/[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]//" "$TEMPORARY"
sed -i '/^$/d' "$TEMPORARY"
sort -u -o "$TEMPORARY" "$TEMPORARY"

while IFS= read -r domain; do
    hostname=$(host -t ns "${domain}")
    parked=$(echo "${hostname}" | grep -E "parkingcrew.net|parklogic.com|sedoparking.com")
    echo "Checking the status of domains..."
    if [[ "${hostname}" =~ "NXDOMAIN" ]]; then
        echo "$domain" >>"$TEMPORARY".2
    fi
done <"$TEMPORARY"

if [ -f "$TEMPORARY.2" ]; then
    sed -i "s/^www[0-9]\.//" "$TEMPORARY".2
    sed -i "s/^www\.//" "$TEMPORARY".2
    sort -u -o "$TEMPORARY".2 "$TEMPORARY".2

    while IFS= read -r domain; do
        whois "${domain}"
    done <"$TEMPORARY.2"
fi
