#!/bin/bash

# ECODFF - Expiration Check Of Domains From Filterlists
# v1.11

SCRIPT_PATH=$(dirname "$0")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium (zakładamy, że skrypt znajduje się w katalogu o 1 niżej od głównego katalogu repozytorium)
MAIN_PATH=$(dirname "$0")/..

cd "$MAIN_PATH" || exit

for i in "$@"; do

    pageComma=$(pcregrep -o1 '^([a-z0-9-~][^\/\*\|\@\"\!]*?)\@?(#|\$\$)\K.*' "$i")

    pagePipe=$(pcregrep -o3 '(domain)(=)([^,]+)' "$i")

    pageDoublePipe=$(pcregrep -o1 '^@?@?\|\|([^\/|^|$]+)' "$i")

    hosts=$(pcregrep -o1 '^.*?0.0.0.0 (.*)' "$i")

    FILTERLIST=$(basename "$i" .txt)
    TEMPORARY=$MAIN_PATH/${FILTERLIST}.temp

    if [ ! -d "$MAIN_PATH/expired-domains" ]; then
        mdkir "$MAIN_PATH"/expired-domains
        touch "$MAIN_PATH"/expired-domains/.keep
    fi

    rm -rf "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt
    rm -rf "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt

    {
        echo "$pageComma"
        echo "$pagePipe"
        echo "$pageDoublePipe"
        echo "$hosts"
    } >> "$TEMPORARY"

    sed -i "s/[|]/\n/g" "$TEMPORARY"
    sed -i "s/\,/\n/g" "$TEMPORARY"
    sed -i "s/\ /\n/g" "$TEMPORARY"
    sed -i "s|\~||" "$TEMPORARY"
    sed -i '/[/\*]/d' "$TEMPORARY"
    sed -ni '/\./p' "$TEMPORARY"
    sed -i -r "s/[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]//" $TEMPORARY
    sort -u -o "$TEMPORARY" "$TEMPORARY"

    while IFS= read -r domain; do
        hostname=$(host "${domain}")
        if [[ "${hostname}" =~ "NXDOMAIN" ]]; then
            echo "$domain" >> "$TEMPORARY".2
        else
            echo "Test"
        fi
    done < "$TEMPORARY"

    sed -i "s/^www[0-9]\.//" "$TEMPORARY".2
    sed -i "s/^www\.//" "$TEMPORARY".2
    sort -u -o "$TEMPORARY".2 "$TEMPORARY".2

    "$SCRIPT_PATH"/DSC.sh -f "$TEMPORARY".2 | tee "$TEMPORARY".3

    touch "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt

    {
        sed '/Expired/!d' "$TEMPORARY".3 | cut -d' ' -f1
        sed '/Book_blocked/!d' "$TEMPORARY".3 | cut -d' ' -f1
        sed '/Suspended/!d' "$TEMPORARY".3 | cut -d' ' -f1
        sed '/Removed/!d' "$TEMPORARY".3 | cut -d' ' -f1
        sed '/Free/!d' "$TEMPORARY".3 | cut -d' ' -f1
        sed '/Redemption_period/!d' "$TEMPORARY".3 | cut -d' ' -f1
        sed '/Suspended_or_reserved/!d' "$TEMPORARY".3 | cut -d' ' -f1
    } >> "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt

    awk -F' ' '$2=="Unknown"' "$TEMPORARY".3 | cut -d' ' -f1 >> "$TEMPORARY".4

    while IFS= read -r domain; do
        status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' "$domain")
        if [ "$status_code" -eq "000" ]; then
            echo "$domain" >> "$TEMPORARY".5
        elif [ "$status_code" -ne "200" ] && [ "$status_code" -ne "000" ]; then
            echo "$domain $status_code" >> "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
        else
            echo "Test"
        fi
    done < "$TEMPORARY".4

    # Kopiujemy adresy zawierające subdomeny do osobnego pliku
    grep -E '(.+\.)+.+\..+$' "$TEMPORARY".5 >"$TEMPORARY".sub

    # Zamieniamy subdomeny na domeny (beta)
    # https://ubuntuforums.org/showthread.php?t=873034&s=99fb8190182be62fbf8f81352b2fa4fa&p=5477397#post5477397
    awk -F. '{if ($(NF-1) == "co"|| $(NF-1) == "com" || $(NF-1) == "net" || $(NF-1) == "edu" || $(NF-1) == "org" || $(NF-1) == "info" || $(NF-1) == "gov" || $(NF-1) == "biz" || $(NF-1) == "art" || $(NF-1) == "aid" || $(NF-1) == "agro" || $(NF-1) == "atm" || $(NF-1) == "auto" || $(NF-1) == "chem" || $(NF-1) == "gmina" || $(NF-1) == "gsm" || $(NF-1) == "mail" || $(NF-1) == "med" || $(NF-1) == "miasta" || $(NF-1) == "media" || $(NF-1) == "mil" || $(NF-1) == "nieruchomosci" || $(NF-1) == "nom" || $(NF-1) == "pc" || $(NF-1) == "powiat" || $(NF-1) == "priv" || $(NF-1) == "realestate" || $(NF-1) == "rel" || $(NF-1) == "sci" || $(NF-1) == "shop" || $(NF-1) == "sklep" || $(NF-1) == "sos" || $(NF-1) == "szkola" || $(NF-1) == "targi" || $(NF-1) == "tm" || $(NF-1) == "tourism" || $(NF-1) == "travel" || $(NF-1) == "turystyka" || $(NF-1) == "in" ) printf $(NF-2)"."; printf $(NF-1)"."$(NF)"\n";}' "$TEMPORARY".5 >> "$TEMPORARY".6
    sort -u -o "$TEMPORARY".6 "$TEMPORARY".6

    "$SCRIPT_PATH"/DSC.sh -f "$TEMPORARY".6 | tee "$TEMPORARY".7

    {
        sed '/Expired/!d' "$TEMPORARY".7 | cut -d' ' -f1
        sed '/Book_blocked/!d' "$TEMPORARY".7 | cut -d' ' -f1
        sed '/Suspended/!d' "$TEMPORARY".7 | cut -d' ' -f1
        sed '/Removed/!d' "$TEMPORARY".7 | cut -d' ' -f1
        sed '/Free/!d' "$TEMPORARY".7 | cut -d' ' -f1
        sed '/Redemption_period/!d' "$TEMPORARY".7 | cut -d' ' -f1
        sed '/Suspended_or_reserved/!d' "$TEMPORARY".3 | cut -d' ' -f1
    } >> "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt

    awk -F' ' '$2=="Unknown"' "$TEMPORARY".7 | cut -d' ' -f1 >> "$TEMPORARY".8

    # Musimy wiedzieć, które domeny subdomen są ok
    sed '/Valid/!d' "$TEMPORARY".7 | cut -d' ' -f1 >> "$TEMPORARY".d

    while IFS= read -r domain; do
        # Jeżeli subdomeny padły, ale ich domeny działają, to subdomeny trafiają do kolejnego pliku tymczasowego
        if grep -q "$domain" "$TEMPORARY.sub"; then
            grep "$domain" "$TEMPORARY.sub" >> "$TEMPORARY".8
        fi
    done < "$TEMPORARY".d

    rm -rf "$TEMPORARY.d"
    rm -rf "$TEMPORARY.sub"

    while IFS= read -r domain; do
        status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' "$domain")
        if [ "$status_code" -ne "200" ]; then
            echo "$domain $status_code" >> "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
        else
            echo "Test"
        fi
    done < "$TEMPORARY".8

    sort -u -o "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt
    sort -u -o "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
    rm -rf "$TEMPORARY".*
    rm -rf "$TEMPORARY"

done
