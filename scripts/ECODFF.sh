#!/bin/bash

# ECODFF - Expiration Check Of Domains From Filterlists
# v1.14.1

# MIT License

# Copyright (c) 2019 Polish Filters Team

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

SCRIPT_PATH=$(dirname "$0")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium (zakładamy, że skrypt znajduje się w katalogu o 1 niżej od głównego katalogu repozytorium)
MAIN_PATH=$(dirname "$0")/..

cd "$MAIN_PATH" || exit

for i in "$@"; do

    pageComma=$(pcregrep -o1 '^([a-z0-9-~][^\/\*\|\@\"\!]*?)(#|\$)' "$i")

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
        hostname=$(host "${domain}")
        if [[ "${hostname}" =~ "NXDOMAIN" ]]; then
            echo "$domain" >>"$TEMPORARY".2
        else
            echo "Test"
        fi
    done <"$TEMPORARY"

    if [ -f "$TEMPORARY.2" ]; then
        sed -i "s/^www[0-9]\.//" "$TEMPORARY".2
        sed -i "s/^www\.//" "$TEMPORARY".2
        sort -u -o "$TEMPORARY".2 "$TEMPORARY".2

        # Kopiujemy adresy zawierające subdomeny do osobnego pliku
        grep -E '(.+\.)+.+\..+$' "$TEMPORARY".2 >"$TEMPORARY".sub

        # Zamieniamy subdomeny na domeny
        python3 "$SCRIPT_PATH"/Sd2D.py "$TEMPORARY".2 >>"$TEMPORARY".3
        sort -u -o "$TEMPORARY".3 "$TEMPORARY".3
    fi

    if [ -f "$TEMPORARY.3" ]; then
        "$SCRIPT_PATH"/DSC.sh -f "$TEMPORARY".3 | tee "$TEMPORARY".4

        touch "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt

        {
            sed '/Expired/!d' "$TEMPORARY".4 | cut -d' ' -f1
            sed '/Book_blocked/!d' "$TEMPORARY".4 | cut -d' ' -f1
            sed '/Suspended/!d' "$TEMPORARY".4 | cut -d' ' -f1
            sed '/Removed/!d' "$TEMPORARY".4 | cut -d' ' -f1
            sed '/Free/!d' "$TEMPORARY".4 | cut -d' ' -f1
            sed '/Redemption_period/!d' "$TEMPORARY".4 | cut -d' ' -f1
            sed '/Suspended_or_reserved/!d' "$TEMPORARY".4 | cut -d' ' -f1
        } >>"$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt

        awk -F' ' '$2=="Unknown"' "$TEMPORARY".4 | cut -d' ' -f1 >>"$TEMPORARY".5
    fi

    if [ -f "$TEMPORARY.5" ]; then
        while IFS= read -r domain; do
            status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' "$domain")
            if [ "$status_code" -eq "000" ]; then
                echo "$domain" >>"$TEMPORARY".6
            elif [ "$status_code" -ne "200" ] && [ "$status_code" -ne "000" ] && [ ! "$NO_SC" ]; then
                echo "$domain $status_code" >>"$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
            elif [ "$status_code" -ne "200" ] && [ "$status_code" -ne "000" ] && [ "$NO_SC" = "true" ]; then
                echo "$domain" >>"$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
            else
                echo "Test"
            fi
        done <"$TEMPORARY".5
    fi

    if [ -f "$TEMPORARY.6" ]; then
        "$SCRIPT_PATH"/DSC.sh -f "$TEMPORARY".6 | tee "$TEMPORARY".7

        {
            sed '/Expired/!d' "$TEMPORARY".7 | cut -d' ' -f1
            sed '/Book_blocked/!d' "$TEMPORARY".7 | cut -d' ' -f1
            sed '/Suspended/!d' "$TEMPORARY".7 | cut -d' ' -f1
            sed '/Removed/!d' "$TEMPORARY".7 | cut -d' ' -f1
            sed '/Free/!d' "$TEMPORARY".7 | cut -d' ' -f1
            sed '/Redemption_period/!d' "$TEMPORARY".7 | cut -d' ' -f1
            sed '/Suspended_or_reserved/!d' "$TEMPORARY".7 | cut -d' ' -f1
        } >>"$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt

        awk -F' ' '$2=="Unknown"' "$TEMPORARY".7 | cut -d' ' -f1 >>"$TEMPORARY".8

        # Musimy wiedzieć, które domeny subdomen są ok
        sed '/Valid/!d' "$TEMPORARY".7 | cut -d' ' -f1 >>"$TEMPORARY".d
    fi

    if [ -f "$TEMPORARY.d" ]; then
        while IFS= read -r domain; do
            # Jeżeli subdomeny padły, ale ich domeny działają, to subdomeny trafiają do kolejnego pliku tymczasowego
            if grep -q "$domain" "$TEMPORARY.sub"; then
                grep "$domain" "$TEMPORARY.sub" >>"$TEMPORARY".8
            fi
        done <"$TEMPORARY".d

        rm -rf "$TEMPORARY.d"
    fi

    if [ -f "$TEMPORARY.sub" ]; then
        rm -rf "$TEMPORARY.sub"
    fi

    if [ -f "$TEMPORARY.8" ]; then
        while IFS= read -r domain; do
            status_code=$(curl -o /dev/null --silent --head --write-out '%{http_code}\n' "$domain")
            if [ "$status_code" -ne "200" ] && [ ! "$NO_SC" ]; then
                echo "$domain $status_code" >>"$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
            elif [ "$status_code" -ne "200" ] && [ "$NO_SC" = "true" ]; then
                echo "$domain" >>"$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
            else
                echo "Test"
            fi
        done <"$TEMPORARY".8
    fi

    if [ -f "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt ]; then
        sort -u -o "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt "$MAIN_PATH"/expired-domains/"$FILTERLIST"-expired.txt
    fi
    if [ -f "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt ]; then
        sort -u -o "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt "$MAIN_PATH"/expired-domains/"$FILTERLIST"-unknown.txt
    fi

    rm -rf "$TEMPORARY".*
    rm -rf "$TEMPORARY"

done

# Lokalizacja pliku konfiguracyjnego
CONFIG=$SCRIPT_PATH/ECODFF.config
if [ -f "$CONFIG" ]; then
    COMMIT_MODE=$(grep -oP -m 1 '@commit_mode true' "$CONFIG")
    commit_message=$(grep -oP -m 1 '@commit \K.*' "$CONFIG")
fi

if [ "$COMMIT_MODE" ] && [ -n "$(git status --porcelain)" ]; then
    cd ./expired-domains || exit
    for file in *.txt; do if [[ ! -s $file ]]; then rm -r "$file"; fi; done
    cd "$MAIN_PATH" || exit
    if [ "$CI" = "true" ]; then
        CI_USERNAME=$(grep -oP -m 1 '@CIusername \K.*' "$CONFIG")
        CI_EMAIL=$(grep -oP -m 1 '@CIemail \K.*' "$CONFIG")
        git config --global user.name "${CI_USERNAME}"
        git config --global user.email "${CI_EMAIL}"
    fi
    git add "$MAIN_PATH"/expired-domains/
    if [ "$commit_message" ] && [ ! "$CI" ]; then
        git commit -m "$commit_message"
    elif [ ! "$commit_message" ] && [ ! "$CI" ]; then
        git commit -m "Expired domains check"
    elif [ ! "$commit_message" ] && [ "$CI" ]; then
        git commit -m "Expired domains check [ci skip]"
    elif [ "$commit_message" ] && [ "$CI" ]; then
        git commit -m "$commit_message [ci skip]"
    fi
    commited=$(git cherry -v)
    if [ "$commited" ]; then
        if [ "$CI" = "true" ]; then
            GIT_SLUG=$(git ls-remote --get-url | sed "s|https://||g" | sed "s|git@||g" | sed "s|:|/|g")
            git push https://"${CI_USERNAME}":"${GIT_TOKEN}"@"${GIT_SLUG}" HEAD:master >/dev/null 2>&1
        else
            printf "%s\n" "Do you want to send changed files to git now?"
            select yn in "Yes" "No"; do
                case $yn in
                Yes)
                    git push
                    break
                    ;;
                No) break ;;
                esac
            done
        fi
    fi
fi
