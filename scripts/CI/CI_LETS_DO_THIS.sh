#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath -s "$0")")

# MAIN_PATH to miejsce, w którym znajduje się główny katalog repozytorium
MAIN_PATH=$(git -C "$SCRIPT_PATH" rev-parse --show-toplevel)

cd "$MAIN_PATH" || exit

function letsGo() {
    for i in "$@"; do
        F_NAME=$(basename "$i")
        if [[ "$i" = "https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/sections/hostsplus.txt" ]]; then
            F_NAME="KADhosts.txt"
        elif [[ "$i" = "https://raw.githubusercontent.com/PolishFiltersTeam/PolishAntiAnnoyingSpecialSupplement/master/sections/suplement.txt" ]]; then
            F_NAME="polish_rss_filters_supp.txt"
        fi
        wget -O "$F_NAME" "$i"
        ./scripts/ECODFF.sh "$F_NAME"
        rm -rf ./"$F_NAME"
    done
}

PAFbase="https://raw.githubusercontent.com/PolishFiltersTeam/PolishAnnoyanceFilters/master/"

if [[ $1 == "KAD" ]]; then
    wget -O KAD.txt https://raw.githubusercontent.com/PolishFiltersTeam/KAD/master/KAD.txt
    mkdir -p "$MAIN_PATH"/split/
    split -d -n l/5 "$MAIN_PATH"/KAD.txt "$MAIN_PATH"/split/KAD_
elif [ "$1" == "Cert" ]; then
    mkdir -p "$MAIN_PATH"/split/
    split -d -n l/10 "$MAIN_PATH"/VICHS_Test/Cert.txt "$MAIN_PATH"/split/Cert_
elif [[ $1 == "KAD_00" || $1 == "KAD_01" || $1 == "KAD_02" || $1 == "KAD_03" || $1 == "KAD_04" || $1 == "KAD_05" || $1 == "KAD_06" || $1 == "KAD_07" || $1 == "KAD_08" || $1 == "KAD_09" || $1 == "KAD_10" || $1 == "KADhosts_00" || $1 == "KADhosts_01" || $1 == "KADhosts_02" || $1 == "KADhosts_03" ||
$1 == "Cert_00" || $1 == "Cert_01" || $1 == "Cert_02" || $1 == "Cert_03" || $1 == "Cert_04" || $1 == "Cert_05" || $1 == "Cert_06" || $1 == "Cert_07" || $1 == "Cert_08" || $1 == "Cert_09" || $1 == "Cert_10" ]]; then
    ./scripts/ECODFF.sh ./split/"$1"
    rm -rf ./"$1"
elif [[ $1 == "KADhosts" ]]; then
    wget -O KADhosts.txt https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/sections/hostsplus.txt
    mkdir -p "$MAIN_PATH"/split/
    split -d -n l/2 "$MAIN_PATH"/KADhosts.txt "$MAIN_PATH"/split/KADhosts_
elif [[ $1 == "PAF" ]]; then
    letsGo "$PAFbase"PAF_arrows.txt \
    "$PAFbase"PAF_backgrounds_self-advertising.txt \
    "$PAFbase"PAF_contact_feedback_widgets.txt \
    "$PAFbase"PAF_e_newspaper \
    "$PAFbase"PAF_newsletters.txt \
    "$PAFbase"PAF_other_widgets.txt \
    "$PAFbase"PAF_pop-ups.txt \
    "$PAFbase"PAF_push.txt \
    "$PAFbase"PAF_scrolling_videos.txt
elif [[ $1 == "PAF_supp" ]]; then
    letsGo "$PAFbase"PAF_backgrounds_self-adv_supp.txt \
    "$PAFbase"PAF_comeback_titles.txt \
    "$PAFbase"PAF_contact_feedback_widgets_supp.txt \
    "$PAFbase"PAF_newsletters_supp.txt \
    "$PAFbase"PAF_other_elements_supp.txt \
    "$PAFbase"PAF_pop-ups_supp.txt \
    "$PAFbase"PAF_push_supp.txt \
    "$PAFbase"PAF_scrolling_videos_supp.txt \
    "$PAFbase"PAF_tagged_internal_links.txt
elif [[ $1 == "PAF_C" ]]; then
    letsGo "$PAFbase"PAF_arrows.txt \
    "$PAFbase"PAF_backgrounds_self-advertising.txt \
    "$PAFbase"PAF_contact_feedback_widgets.txt \
    "$PAFbase"PAF_e_newspaper \
    "$PAFbase"PAF_newsletters.txt \
    "$PAFbase"PAF_other_widgets.txt \
    "$PAFbase"PAF_pop-ups.txt \
    "$PAFbase"PAF_push.txt \
    "$PAFbase"PAF_scrolling_videos.txt \
    "$PAFbase"PAF_backgrounds_self-adv_supp.txt \
    "$PAFbase"PAF_comeback_titles.txt \
    "$PAFbase"PAF_contact_feedback_widgets_supp.txt \
    "$PAFbase"PAF_newsletters_supp.txt \
    "$PAFbase"PAF_other_elements_supp.txt \
    "$PAFbase"PAF_pop-ups_supp.txt \
    "$PAFbase"PAF_push_supp.txt \
    "$PAFbase"PAF_scrolling_videos_supp.txt \
    "$PAFbase"PAF_tagged_internal_links.txt
elif [ "$1" == "PASS" ]; then
    letsGo https://raw.githubusercontent.com/PolishFiltersTeam/PolishAntiAnnoyingSpecialSupplement/master/polish_rss_filters.txt \
    https://raw.githubusercontent.com/PolishFiltersTeam/PolishAntiAnnoyingSpecialSupplement/master/sections/suplement.txt
elif [ "$1" == "Social" ]; then
    letsGo https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/adblock_social_list.txt
elif [ "$1" == "Social_supp" ]; then
    letsGo https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/social_filters_uB_AG.txt
elif [ "$1" == "Social_C" ]; then
    letsGo https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/adblock_social_list.txt https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/adblock_social_filters/social_filters_uB_AG.txt
elif [ "$1" == "Cookies" ]; then
    letsGo https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/cookies_filters/adblock_cookies.txt
elif [ "$1" == "Cookies_supp" ]; then
    letsGo https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/cookies_filters/cookies_uB_AG.txt
elif [ "$1" == "Cookies_C" ]; then
    letsGo https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/cookies_filters/adblock_cookies.txt https://raw.githubusercontent.com/PolishFiltersTeam/PolishSocialCookiesFiltersDev/master/cookies_filters/cookies_uB_AG.txt
fi
