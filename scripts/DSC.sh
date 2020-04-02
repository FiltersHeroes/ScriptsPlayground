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
# Current Version: 1.0.9
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
PATH=/bin:/usr/bin:/usr/local/bin:/usr/local/ssl/bin:/usr/sfw/bin
export PATH

# Number of days in the warning threshhold  (cmdline: -x)
WARNDAYS=30

# If QUIET is set to TRUE, don't print anything on the console (cmdline: -q)
QUIET="FALSE"

# Don't show the version of the script by default (cmdline: -V)
VERSIONENABLE="FALSE"

# Don't show debug information by default (cmdline: -vv)
VERBOSE="FALSE"

# Whois server to use (cmdline: -s)
WHOIS_SERVER="whois.internic.org"

# Location of system binaries
AWK=`which awk`
WHOIS=`which whois`
DATE=`which date`
CUT=`which cut`
GREP=`which grep`
TR=`which tr`
CURL=`which curl`

# Version of the script
VERSION=$(${AWK} -F': ' '/^# Current Version:/ {print $2; exit}' $0)

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
    # Avoid WHOIS LIMIT EXCEEDED - slowdown our whois client by adding 3 sec
    sleep 3
    # Save the domain since set will trip up the ordering
    DOMAIN=${1}
    TLDTYPE=$(echo ${DOMAIN} | ${AWK} -F. '{print tolower($NF);}')
    if [ "${TLDTYPE}"  == "" ];
    then
        TLDTYPE=$(echo ${DOMAIN} | ${AWK} -F. '{print tolower($(NF-1));}')
    fi
    if [ "${TLDTYPE}"  == "ua" -o "${TLDTYPE}"  == "pl" -o "${TLDTYPE}"  == "net" ];
    then
        SUBTLDTYPE=$(echo ${DOMAIN} | ${AWK} -F. '{print tolower($(NF-1)"."$(NF));}')
    fi

    # Invoke whois to find the domain expiration date
    #${WHOIS} -h ${WHOIS_SERVER} "=${1}" > ${WHOIS_TMP}
    # Let whois select server

    if [ "${TLDTYPE}" == "kz" ];
    then
        ${CURL} -s "https://api.ps.kz/kzdomain/domain-whois?username=test&password=test&input_format=http&output_format=get&dname=${1}" \
        | env LC_CTYPE=C LC_ALL=C ${TR} -d "\r" > ${WHOIS_2_TMP}
    else
        ${WHOIS} "${1}" | env LC_CTYPE=C LC_ALL=C ${TR} -d "\r" > ${WHOIS_TMP}
    fi

    removed=$(cat ${WHOIS_TMP} | ${GREP} "The queried object does not exist: previous registration")

    # The whois Expiration data should resemble the following: "Expiration Date: 09-may-2008-16:00:00-CEST"
    export LC_ALL=en_US.UTF-8

    if adate=$(cat ${WHOIS_TMP} | ${GREP} -i 'expiration\|expires\|expiry\|renewal\|expire\|paid-till\|valid until\|exp date\|vencimiento'); then
			adate=$(echo "$adate" | head -n 1 | sed -n 's/^[^]:]\+[]:][.[:blank:]]*//p')
			adate=${adate%.}
			if date=$(${DATE}  -u -d "$adate" 2>&1) || date=$(${DATE}  -u -d "${adate//./-}" 2>&1) || date=$(${DATE}  -u -d "${adate//.//}" 2>&1) || date=$(${DATE} -u -d "$(echo "${adate//./-}" | ${AWK} -F'[/-]' '{for(i=NF;i>0;i--) printf "%s%s",$i,(i==1?"\n":"-")}')" 2>&1); then
				DOMAINDATE=$(${DATE} -d "$date" +"%d-%b-%Y-%T-%Z")
				sec=$(( $(${DATE} -d "$date" +%s) - $(${DATE} -d "$NOW" +%s) ))
				DOMAINDIFF=$(( sec / 86400 ))
			else
				DOMAINDATE="Unknown ($adate)" # date="Error: Could not input domain expiration date ($adate)."
                DOMAINDIFF="Unknown"
			fi
    elif [ "${TLDTYPE}" == "kz" ]; # for .kz @click0 2019/02/23
    then
        adate=`${GREP} -A 1 "expire" ${WHOIS_2_TMP} | ${GREP} "utc" | ${AWK} -F\" '{print $4;}'`
        DOMAINDATE=$(${DATE} -d "${adate}" +"%d-%b-%Y-%T-%Z")
        sec=$(( $(${DATE} -d "$adate" +%s) - $(${DATE} -d "$NOW" +%s) ))
        DOMAINDIFF=$(( sec / 86400 ))
    elif [ ! -z "$removed" ]
    then
        adate=`${GREP} -oP -m 1 "was purged on \K.*" ${WHOIS_TMP} | ${AWK} -F\" '{print $1;}'`
        DOMAINDATE=$(${DATE} -d "${adate}" +"%d-%b-%Y-%T-%Z")
        sec=$(( $(${DATE} -d "$adate" +%s) - $(${DATE} -d "$NOW" +%s) ))
        DOMAINDIFF=$(( sec / 86400 ))
	else
        DOMAINDATE="Unknown" # date="Error: Could not get domain expiration date."
        DOMAINDIFF="Unknown"
    fi

    book_blocked=$(cat ${WHOIS_TMP} | ${GREP} "after release from the queue, available for registration")
    suspended=$(cat ${WHOIS_TMP} | ${GREP} "is undergoing proceeding")
    active=$(cat ${WHOIS_TMP} | ${GREP} "Status: [[:space:]]*active")
    free=$(cat ${WHOIS_TMP} | ${GREP} "is free")
    suspended_reserved=$(cat ${WHOIS_TMP} | ${GREP} "cancelled, suspended, refused or reserved at the" )
    redemption_period=$(cat ${WHOIS_TMP} | ${GREP} "redemptionPeriod" )
    reserved=$(cat ${WHOIS_TMP} | ${GREP} "is queued up for registration" )
    limit_exceeded=$(cat ${WHOIS_TMP} | ${GREP} "request limit exceeded")

    if [ ! -z "$removed" ]
    then
        prints "${DOMAIN}" "Removed" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -z "$suspended_reserved" ]
    then
        prints "${DOMAIN}" "Suspended_or_reserved" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -z "$suspended" ]
    then
        prints "${DOMAIN}" "Suspended" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -z "$book_blocked" ]
    then
        prints "${DOMAIN}" "Book_blocked" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -z "$reserved" ]
    then
        prints "${DOMAIN}" "Reserved" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! ${DOMAINDIFF} == "Unknown" ] && [ ${DOMAINDIFF} -lt 0 ]
    then
        prints "${DOMAIN}" "Expired" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -z "${redemption_period}" ]
    then
        prints "${DOMAIN}" "Redemption_period" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! ${DOMAINDIFF} == "Unknown" ] && [ ${DOMAINDIFF} -lt ${WARNDAYS} ]
    then
        prints "${DOMAIN}" "Expiring" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -z "${free}" ]
    then
        prints "${DOMAIN}" "Free" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ "${DOMAINDATE}" == "Unknown" ] || [ "${DOMAINDATE}" == "Unknown ($adate)" ] && [ -z "$active" ]
    then
        prints "${DOMAIN}" "Unknown" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -z "${limit_exceeded}" ] && [ "${TLDTYPE}" == "pl" ]
    then
        # If whois request limit exceeded, then wait 16 minutes for counter reset and try again
        sleep 16m && check_domain_status "${DOMAIN}"
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
        MIN_DATE=$(echo $3 | ${AWK} '{ print $1, $2, $4 }')
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
    echo "Usage: $0 [ -x expir_days ] [ -s whois server ] [ -q ] [ -h ] [ -v ] [ -V ]"
    echo "	  {[ -d domain_namee ]} || { -f domainfile}"
    echo ""
    echo "  -d domain        : Domain to analyze (interactive mode)"
    echo "  -f domain file   : File with a list of domains"
    echo "  -h               : Print this screen"
    echo "  -s whois server  : Whois sever to query for information"
    echo "  -q               : Don't print anything on the console"
    echo "  -x days          : Domain expiration interval (eg. if domain_date < days)"
    echo "  -v               : Show debug information when running script"
    echo "  -V               : Print version of the script"
    echo ""
}

### Evaluate the options passed on the command line
while getopts ad:e:f:hs:qx:vV option
do
    case "${option}"
    in
        d) DOMAIN=${OPTARG};;
        f) SERVERFILE=$OPTARG;;
        s) WHOIS_SERVER=$OPTARG;;
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

### Check to see if the whois binary exists
if [ ! -f ${WHOIS} ]
then
    echo "ERROR: The whois binary does not exist in ${WHOIS} ."
    echo "  FIX: Please modify the \$WHOIS variable in the program header."
    exit 1
fi

### Check to make sure a date utility is available
if [ ! -f ${DATE} ]
then
    echo "ERROR: The date binary does not exist in ${DATE} ."
    echo "  FIX: Please modify the \$DATE variable in the program header."
    exit 1
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
