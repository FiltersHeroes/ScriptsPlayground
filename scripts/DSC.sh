#!/usr/bin/env bash
#
# Program: DSC <Domain Status Check>
#
# Based on domain-check-2.sh (https://github.com/click0/domain-check-2/blob/master/domain-check-2.sh)
# and domains.sh script (https://github.com/tdulcet/Remote-Servers-Status/blob/master/domains.sh).
# Many thanks for nixcraft (https://github.com/nixcraft), tdulcet (https://github.com/tdulcet), click0 (https://github.com/click0),
# Matty9191 (https://github.com/Matty9191) and all contributors of domain-check-2 script
# (https://github.com/click0/domain-check-2/graphs/contributors) !
#
#
# Current Version: 1.0.19
#
#
# Purpose:
#  DSC checks to see what domain has status (expired, suspended, book blocked, etc).
#  DSC can be run in interactive and batch mode.
#
# License:
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#
# Requirements:
#   Requires whois
#
# Installation:
#   Copy the shell script to a suitable location
#
# Usage:
#  Refer to the usage() sub-routine, or invoke DSC
#  with the "-h" option.
#
#
#
# Number of days in the warning threshhold  (cmdline: -x)
WARNDAYS=30

# If QUIET is set to TRUE, don't print anything on the console (cmdline: -q)
QUIET="FALSE"

# Don't show the version of the script by default (cmdline: -V)
VERSIONENABLE="FALSE"

# Don't show debug information by default (cmdline: -vv)
VERBOSE="FALSE"

# Version of the script
VERSION=$(awk -F': ' '/^# Current Version:/ {print $2; exit}' $0)

# User-Agent
VARUSERAGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"

# Place to stash temporary files
WHOIS_TMP="/var/tmp/whois.$$"
WHOIS_2_TMP="/var/tmp/whois_2.$$"


##################################################################
# Purpose: Access whois data to grab the expiration date
# Arguments:
#   $1 -> Domain to check
##################################################################
check_domain_status()
{
    NOW=${EPOCHSECONDS:-$(date +%s)}

    # Avoid failing whole job on CI/gracefully fail script
    if [ "$CI" = "true" ];
    then
        if [ "$NOW" -ge "$END_TIME" ];
        then
            echo "Maximum time limit reached for running on CI."
            exit 0
        fi
    fi

    # Avoid WHOIS LIMIT EXCEEDED - slowdown our whois client by adding 3 sec
    sleep 3
    # Save the domain since set will trip up the ordering
    DOMAIN=${1}
    TLDTYPE=$(echo ${DOMAIN} | awk -F. '{print tolower($NF);}')
    if [ "${TLDTYPE}"  == "" ];
    then
        TLDTYPE=$(echo ${DOMAIN} | awk -F. '{print tolower($(NF-1));}')
    fi
    if [ "${TLDTYPE}"  == "ua" -o "${TLDTYPE}"  == "pl" -o "${TLDTYPE}"  == "net" ];
    then
        SUBTLDTYPE=$(echo ${DOMAIN} | awk -F. '{print tolower($(NF-1)"."$(NF));}')
    fi

    # Invoke whois to find the domain expiration date
    if [ "${TLDTYPE}" == "kz" ];
    then
        curl -s -A "$VARUSERAGENT" "https://www.ps.kz/domains/whois/result?q=${1}" \
        | env LC_CTYPE=C LC_ALL=C tr -d "\r" > ${WHOIS_2_TMP}
    else
        whois "${1}" | env LC_CTYPE=C LC_ALL=C tr -d "\r" > ${WHOIS_TMP}
    fi

    removed=$(cat ${WHOIS_TMP} | grep -Ei "(The queried object does not exist: previous registration|is available for registration|Status: AVAILABLE$)")

    # The whois Expiration data should resemble the following: "Expiration Date: 09-may-2008-16:00:00-CEST"
    export LC_ALL=en_US.UTF-8

    if adate=$(cat ${WHOIS_TMP} | grep -Ei '(expiration|expires|expiry|renewal|expire|paid-till|valid until|exp date|vencimiento|exp date|validity|vencimiento|registry fee due|fecha de corte)(.*)(:|\])'); then
			adate=$(echo "$adate" | head -n 1 | sed -n 's/^[^]:]\+[]:][.[:blank:]]*//p')
			adate=${adate%.}
			if date=$(date -u -d "$adate" 2>&1) || date=$(date -u -d "${adate//./-}" 2>&1) || date=$(date -u -d "${adate//.//}" 2>&1) || date=$(date -u -d "$(echo "${adate//./-}" | awk -F'[/-]' '{for(i=NF;i>0;i--) printf "%s%s",$i,(i==1?"\n":"-")}')" 2>&1); then
				DOMAINDATE=$(date -d "$date" +"%d-%b-%Y-%T-%Z")
				sec=$(( $(date -d "$date" +%s) - NOW ))
				DOMAINDIFF=$(( sec / 86400 ))
			else
				DOMAINDATE="Unknown ($adate)" # date="Error: Could not input domain expiration date ($adate)."
                DOMAINDIFF="Unknown"
			fi
    elif [ "${TLDTYPE}" == "kz" ]; # for .kz @click0 2019/02/23
    then
        adate=$(grep -A 2 'Дата окончания:' ${WHOIS_2_TMP} | tail -n 1 | awk '{print $1;}' | awk -FT '{print $1}')
        DOMAINDATE=$(date -d "${adate}" +"%d-%b-%Y-%T-%Z")
        sec=$(( $(date -d "$date" +%s) - NOW ))
        DOMAINDIFF=$(( sec / 86400 ))
    elif [ -n "$removed" ]
    then
        adate=$(grep -oP -m 1 "was purged on \K.*" ${WHOIS_TMP} | awk -F\" '{print $1;}')
        DOMAINDATE=$(date -d "${adate}" +"%d-%b-%Y-%T-%Z")
        sec=$(( $(date -d "$date" +%s) - NOW ))
        DOMAINDIFF=$(( sec / 86400 ))
	else
        DOMAINDATE="Unknown" # date="Error: Could not get domain expiration date."
        DOMAINDIFF="Unknown"
    fi

    book_blocked=$(cat ${WHOIS_TMP} | grep "after release from the queue, available for registration")
    suspended=$(cat ${WHOIS_TMP} | grep "is undergoing proceeding")
    active=$(cat ${WHOIS_TMP} | grep "Status: [[:space:]]*active")
    free=$(cat ${WHOIS_TMP} | grep "is free")
    suspended_reserved=$(cat ${WHOIS_TMP} | grep "cancelled, suspended, refused or reserved at the" )
    redemption_period=$(cat ${WHOIS_TMP} | grep "redemptionPeriod" )
    reserved=$(cat ${WHOIS_TMP} | grep "is queued up for registration" )
    limit_exceeded=$(cat ${WHOIS_TMP} | grep -Ei "request limit exceeded|Query rate exceeded")

    if [ -n "$removed" ]
    then
        prints "${DOMAIN}" "Removed" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$suspended_reserved" ]
    then
        prints "${DOMAIN}" "Suspended_or_reserved" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$suspended" ]
    then
        prints "${DOMAIN}" "Suspended" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$book_blocked" ]
    then
        prints "${DOMAIN}" "Book_blocked" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$reserved" ]
    then
        prints "${DOMAIN}" "Reserved" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! ${DOMAINDIFF} == "Unknown" ] && [ ${DOMAINDIFF} -lt 0 ]
    then
        prints "${DOMAIN}" "Expired" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "${redemption_period}" ]
    then
        prints "${DOMAIN}" "Redemption_period" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! ${DOMAINDIFF} == "Unknown" ] && [ ${DOMAINDIFF} -lt "${WARNDAYS}" ]
    then
        prints "${DOMAIN}" "Expiring" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "${free}" ]
    then
        prints "${DOMAIN}" "Free" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "${limit_exceeded}" ]
    then
        prints "${DOMAIN}" "Limit_exceeded" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -s "${WHOIS_TMP}" ] && [ ! -s "${WHOIS_2_TMP}" ]
    then
        prints "${DOMAIN}" "No_internet" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ "${DOMAINDATE}" == "Unknown" ] || [ "${DOMAINDATE}" == "Unknown ($adate)" ] && [ -z "$active" ]
    then
        prints "${DOMAIN}" "Unknown" "${DOMAINDATE}" "${DOMAINDIFF}"
    else
        prints "${DOMAIN}" "Valid" "${DOMAINDATE}"  "${DOMAINDIFF}"
    fi
}

####################################################
# Purpose: Print a heading with the relevant columns
# Arguments:
#   None
####################################################
print_heading()
{
    if [ "${QUIET}" != "TRUE" ]
    then
        printf "\n%-35s %-21s %-31s %-5s\n" "Domain" "Status" "Expires" "Days Left"
        echo "----------------------------------- --------------------- ------------------------------- ---------"
    fi
}

#####################################################################
# Purpose: Print a line with the expiraton interval
# Arguments:
#   $1 -> Domain
#   $2 -> Status of domain (e.g., expired or valid)
#   $3 -> Date when domain will expire
#   $4 -> Days left until the domain will expire
#####################################################################
prints()
{
    if [ "${QUIET}" != "TRUE" ]
    then
        MIN_DATE=$(echo $3 | awk '{ print $1, $2, $4 }')
        printf "%-35s %-21s %-31s %-5s\n" "$1" "$2" "$MIN_DATE" "$4"
    fi
}

##########################################
# Purpose: Describe how the script works
# Arguments:
#   None
##########################################
usage()
{
    echo "Usage: $0 [ -x expir_days ] [ -s whois server ] [ -q ] [ -h ] [ -v ] [ -V ] [ -t time limit]"
    echo "	  {[ -d domain_namee ]} || { -f domainfile}"
    echo ""
    echo "  -d domain        : Domain to analyze (interactive mode)"
    echo "  -f domain file   : File with a list of domains"
    echo "  -h               : Print this screen"
    echo "  -q               : Don't print anything on the console"
    echo "  -x days          : Domain expiration interval (eg. if domain_date < days)"
    echo "  -v               : Show debug information when running script"
    echo "  -V               : Print version of the script"
    echo "  -t time limit    : Time limit for running script on CI"
    echo ""
}

### Evaluate the options passed on the command line
while getopts d:f:s:qx:t:vV option
do
    case "${option}"
    in
        d) DOMAIN=${OPTARG};;
        f) SERVERFILE=$OPTARG;;
        t) END_TIME=$(date -d "+$OPTARG" +%s);;
        q) QUIET="TRUE";;
        x) WARNDAYS=$OPTARG;;
        v) VERBOSE="TRUE";;
        V) VERSIONENABLE="TRUE";;
        \?) usage
        exit 1;;
    esac
done

### Show debug information when running script
if [ "${VERBOSE}" == "TRUE" ]
then
    set -x
fi

### Print version of the script
if [ "${VERSIONENABLE}" == "TRUE" ]
then
    printf "%-15s %-10s\n" "Script version: " "${VERSION}"
    exit 1
fi


### Touch the files prior to using them
touch ${WHOIS_TMP}

### If a HOST and PORT were passed on the cmdline, use those values
if [ "${DOMAIN}" != "" ]
then
    print_heading
    check_domain_status "${DOMAIN}"
### If a file and a "-a" are passed on the command line, check all
### of the domains in the file to see if they are about to expire
elif [ -f "${SERVERFILE}" ]
then
    print_heading
    while read DOMAIN
    do
        check_domain_status "${DOMAIN}"

    done < ${SERVERFILE}

### There was an error, so print a detailed usage message and exit
else
    usage
    exit 1
fi

# Add an extra newline
echo

### Remove the temporary files
[ -f "${WHOIS_TMP}" ] && rm -f ${WHOIS_TMP};
[ -f "${WHOIS_2_TMP}" ] && rm -f ${WHOIS_2_TMP};

### Exit with a success indicator
exit 0
