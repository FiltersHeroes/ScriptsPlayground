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
# Current Version: 1.0.23
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
#  Requires whois
#
# Installation:
#  Copy the shell script to a suitable location
#
# Usage:
#  Refer to the usage() sub-routine, or invoke DSC
#  with the "-h" option.
#
# Global configuration variables:
WARNDAYS=30           # Number of days in the warning threshold (cmdline: -x)
QUIET="FALSE"         # If TRUE, don't print anything on the console (cmdline: -q)
VERSIONENABLE="FALSE" # Don't show the version of the script by default (cmdline: -V)
VERBOSE="FALSE"       # Don't show debug information by default (cmdline: -vv)
VERSION=$(awk -F': ' '/^# Current Version:/ {print $2; exit}' "$0")
VARUSERAGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
MAX_DEFAULT_PARALLEL_JOBS=5 # Max default parallel jobs, can be changed here

# Detect number of CPU cores for parallel processing
CPU_CORES=$(nproc)
# Fallback if nproc is not available (e.g., macOS, or very minimal Linux env)
if [ -z "$CPU_CORES" ] || [ "$CPU_CORES" -eq 0 ]; then
    # Attempt to use grep on /proc/cpuinfo if it exists (Linux-specific)
    if [ -f /proc/cpuinfo ]; then
        CPU_CORES=$(grep -c ^processor /proc/cpuinfo)
        if [ -z "$CPU_CORES" ] || [ "$CPU_CORES" -eq 0 ]; then
            CPU_CORES=4 # Final fallback
        fi
    else
        CPU_CORES=4 # Default if nproc and /proc/cpuinfo are unavailable
    fi
fi

# Set default number of parallel jobs based on CPU_CORES, capped by MAX_DEFAULT_PARALLEL_JOBS.
PARALLEL_JOBS=$CPU_CORES
if [ "$PARALLEL_JOBS" -gt "$MAX_DEFAULT_PARALLEL_JOBS" ]; then
    PARALLEL_JOBS="$MAX_DEFAULT_PARALLEL_JOBS"
fi

# Variable to hold the user-defined cap from -j flag, will be processed after getopts
USER_JOB_CAP=""

#####################################################################
# Purpose: Print a line with the expiration interval details.
# Arguments:
#   $1 -> Domain
#   $2 -> Status of domain (e.g., expired or valid)
#   $3 -> Date when domain will expire
#   $4 -> Days left until the domain will expire
#####################################################################
prints() {
    if [ "${QUIET}" != "TRUE" ]; then
        MIN_DATE=$(echo "$3" | awk '{ print $1, $2, $4 }')
        printf "%-35s %-21s %-31s %-5s\n" "$1" "$2" "$MIN_DATE" "$4"
    fi
}

####################################################
# Purpose: Print a heading with the relevant columns.
# Arguments: None
####################################################
print_heading() {
    if [ "${QUIET}" != "TRUE" ]; then
        printf "\n%-35s %-21s %-31s %-5s\n" "Domain" "Status" "Expires" "Days Left"
        echo "----------------------------------- --------------------- ------------------------------- ---------"
    fi
}

##################################################################
# Purpose: Access whois data to grab the expiration date and determine domain status.
# Arguments:
#   $1 -> Domain to check
##################################################################
check_domain_status() {
    # Define WHOIS_TMP and WHOIS_2_TMP unique to each parallel process.
    WHOIS_TMP="/var/tmp/whois.$$"
    WHOIS_2_TMP="/var/tmp/whois_2.$$"

    NOW=${EPOCHSECONDS:-$(date +%s)}

    # Avoid failing whole job on CI/gracefully fail script
    if [ "$CI" = "true" ]; then
        if [ "$NOW" -ge "$END_TIME" ]; then
            echo "Maximum time limit reached for running on CI."
            exit 0
        fi
    fi

    # Avoid WHOIS LIMIT EXCEEDED - slowdown our whois client by adding 1 sec.
    # This sleep is per individual whois query.
    sleep 1

    DOMAIN=${1}
    TLDTYPE=$(echo "${DOMAIN}" | awk -F. '{print tolower($NF);}')
    if [ "${TLDTYPE}" == "" ]; then
        TLDTYPE=$(echo "${DOMAIN}" | awk -F. '{print tolower($(NF-1));}')
    fi
    if [ "${TLDTYPE}" == "ua" -o "${TLDTYPE}" == "pl" -o "${TLDTYPE}" == "net" ]; then
        SUBTLDTYPE=$(echo "${DOMAIN}" | awk -F. '{print tolower($(NF-1)"."$(NF));}')
    fi

    # Invoke whois or curl to fetch domain information.
    if [ "${TLDTYPE}" == "kz" ]; then
        curl -s -A "$VARUSERAGENT" "https://www.ps.kz/domains/whois/result?q=${1}" |
            env LC_CTYPE=C LC_ALL=C tr -d "\r" >"${WHOIS_2_TMP}"
    else
        whois "${1}" | env LC_CTYPE=C LC_ALL=C tr -d "\r" >"${WHOIS_TMP}"
    fi

    removed=""
    # Check for domain removal/availability status from WHOIS output.
    if [ -f "${WHOIS_TMP}" ]; then
        removed=$(cat "${WHOIS_TMP}" | grep -Ei "(The queried object does not exist: previous registration|is available for registration|Status: AVAILABLE$)")
    fi

    # Set locale for consistent date parsing.
    export LC_ALL=en_US.UTF-8

    adate=""
    date="" # Variable name restored to 'date' as per original script
    DOMAINDATE=""
    DOMAINDIFF=""

    # Attempt to extract expiration date from WHOIS output.
    if [ -f "${WHOIS_TMP}" ] && adate=$(cat "${WHOIS_TMP}" | grep -Ei '(expiration|expires|expiry|renewal|expire|paid-till|valid until|exp date|vencimiento|exp date|validity|vencimiento|registry fee due|fecha de corte)(.*)(:|\])'); then
        adate=$(echo "$adate" | head -n 1 | sed -n 's/^[^]:]\+[]:][.[:blank:]]*//p')
        adate=${adate%.}
        if date=$(date -u -d "$adate" 2>&1) || date=$(date -u -d "${adate//./-}" 2>&1) || date=$(date -u -d "${adate//.//}" 2>&1) || date=$(date -u -d "$(echo "${adate//./-}" | awk -F'[/-]' '{for(i=NF;i>0;i--) printf "%s%s",$i,(i==1?"\n":"-")}')" 2>&1); then
            DOMAINDATE=$(date -d "$date" +"%d-%b-%Y-%T-%Z")
            sec=$(($(date -d "$date" +%s) - NOW))
            DOMAINDIFF=$((sec / 86400))
        else
            DOMAINDATE="Unknown ($adate)"
            DOMAINDIFF="Unknown"
        fi
    elif [ "${TLDTYPE}" == "kz" ] && [ -f "${WHOIS_2_TMP}" ]; then # Special handling for .kz TLD
        adate=$(grep -A 2 'Дата окончания:' "${WHOIS_2_TMP}" | tail -n 1 | awk '{print $1;}' | awk -FT '{print $1}')
        DOMAINDATE=$(date -d "${adate}" +"%d-%b-%Y-%T-%Z")
        sec=$(($(date -d "$date" +%s) - NOW))
        DOMAINDIFF=$((sec / 86400))
    elif [ -n "$removed" ] && [ -f "${WHOIS_TMP}" ]; then # Handle "purged" status
        adate=$(grep -oP -m 1 "was purged on \K.*" "${WHOIS_TMP}" | awk -F\" '{print $1;}')
        DOMAINDATE=$(date -d "${adate}" +"%d-%b-%Y-%T-%Z")
        sec=$(($(date -d "$date" +%s) - NOW))
        DOMAINDIFF=$((sec / 86400))
    else
        DOMAINDATE="Unknown"
        DOMAINDIFF="Unknown"
    fi

    # Initialize variables for various domain statuses.
    book_blocked=""
    suspended=""
    active=""
    free=""
    suspended_reserved=""
    redemption_period=""
    reserved=""
    limit_exceeded=""

    # Check for various domain status indicators in WHOIS output.
    if [ -f "${WHOIS_TMP}" ]; then
        book_blocked=$(cat "${WHOIS_TMP}" | grep "after release from the queue, available for registration")
        suspended=$(cat "${WHOIS_TMP}" | grep "is undergoing proceeding")
        active=$(cat "${WHOIS_TMP}" | grep "Status: [[:space:]]*active")
        free=$(cat "${WHOIS_TMP}" | grep "is free")
        suspended_reserved=$(cat "${WHOIS_TMP}" | grep "cancelled, suspended, refused or reserved at the")
        redemption_period=$(cat "${WHOIS_TMP}" | grep "redemptionPeriod")
        reserved=$(cat "${WHOIS_TMP}" | grep "is queued up for registration")
        limit_exceeded=$(cat "${WHOIS_TMP}" | grep -Ei "request limit exceeded|Query rate exceeded|Server is busy now|too fast|try again|later")
    fi

    # Determine and print the domain status based on checks.
    if [ -n "$removed" ]; then
        prints "${DOMAIN}" "Removed" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$suspended_reserved" ]; then
        prints "${DOMAIN}" "Suspended_or_reserved" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$suspended" ]; then
        prints "${DOMAIN}" "Suspended" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$book_blocked" ]; then
        prints "${DOMAIN}" "Book_blocked" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "$reserved" ]; then
        prints "${DOMAIN}" "Reserved" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! "${DOMAINDIFF}" == "Unknown" ] && [ "${DOMAINDIFF}" -lt 0 ]; then
        prints "${DOMAIN}" "Expired" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "${redemption_period}" ]; then
        prints "${DOMAIN}" "Redemption_period" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! "${DOMAINDIFF}" == "Unknown" ] && [ "${DOMAINDIFF}" -lt "${WARNDAYS}" ]; then
        prints "${DOMAIN}" "Expiring" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "${free}" ]; then
        prints "${DOMAIN}" "Free" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ -n "${limit_exceeded}" ] && [ "$DOMAINDATE" == "Unknown" ]; then
        prints "${DOMAIN}" "Limit_exceeded" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ ! -s "${WHOIS_TMP}" ] && [ ! -s "${WHOIS_2_TMP}" ]; then
        prints "${DOMAIN}" "No_internet" "${DOMAINDATE}" "${DOMAINDIFF}"
    elif [ "${DOMAINDATE}" == "Unknown" ] || [ "${DOMAINDATE}" == "Unknown ($adate)" ] && [ -z "$active" ]; then
        prints "${DOMAIN}" "Unknown" "${DOMAINDATE}" "${DOMAINDIFF}"
    else
        prints "${DOMAIN}" "Valid" "${DOMAINDATE}" "${DOMAINDIFF}"
    fi

    # Clean up temporary files unique to this process.
    [ -f "${WHOIS_TMP}" ] && rm -f "${WHOIS_TMP}"
    [ -f "${WHOIS_2_TMP}" ] && rm -f "${WHOIS_2_TMP}"
}

##########################################
# Purpose: Describe how the script works.
# Arguments: None
##########################################
usage() {
    echo "Usage: $0 [ -x expir_days ] [ -s whois server ] [ -q ] [ -h ] [ -v ] [ -V ] [ -t time limit] [ -j jobs_cap ]"
    echo "    {[ -d domain_namee ]} || { -f domainfile}"
    echo ""
    echo "  -d domain        : Domain to analyze (interactive mode)"
    echo "  -f domain file   : File with a list of domains"
    echo "  -h               : Print this screen"
    echo "  -q               : Don't print anything on the console"
    echo "  -x days          : Domain expiration interval (e.g., if domain_date < days)"
    echo "  -v               : Show debug information when running script"
    echo "  -V               : Print version of the script"
    echo "  -t time limit    : Time limit for running script on CI"
    echo "  -j jobs_cap      : Maximum number of parallel jobs (caps the default, currently min(CPU_CORES, ${MAX_DEFAULT_PARALLEL_JOBS}) is ${PARALLEL_JOBS})"
    echo ""
}

# Export functions for parallel execution with xargs.
export -f check_domain_status
export -f prints
export -f print_heading

# Evaluate the options passed on the command line.
while getopts d:f:s:qx:t:vVj: option; do
    case "${option}" in

    d) DOMAIN=${OPTARG} ;;
    f) SERVERFILE=$OPTARG ;;
    t) END_TIME=$(date -d "+$OPTARG" +%s) ;;
    q) QUIET="TRUE" ;;
    x) WARNDAYS=$OPTARG ;;
    v) VERBOSE="TRUE" ;;
    V) VERSIONENABLE="TRUE" ;;
    j) USER_JOB_CAP=$OPTARG ;; # Store the user-defined cap
    \?)
        usage
        exit 1
        ;;
    esac
done

# Apply user-defined cap if provided and it's lower than the current PARALLEL_JOBS
if [ -n "$USER_JOB_CAP" ]; then
    if [ "$USER_JOB_CAP" -lt "$PARALLEL_JOBS" ]; then
        PARALLEL_JOBS=$USER_JOB_CAP
    fi
fi

# Show debug information if VERBOSE is true.
if [ "${VERBOSE}" == "TRUE" ]; then
    set -x
fi

# Print script version if VERSIONENABLE is true.
if [ "${VERSIONENABLE}" == "TRUE" ]; then
    printf "%-15s %-10s\n" "Script version: " "${VERSION}"
    exit 1
fi

# Main execution block.
if [ "${DOMAIN}" != "" ]; then
    print_heading
    check_domain_status "${DOMAIN}"
elif [ -f "${SERVERFILE}" ]; then
    print_heading
    # Export global variables needed by functions in subshells.
    export WARNDAYS QUIET VERBOSE VARUSERAGENT END_TIME CI

    # Process domains from file in parallel using xargs.
    # -P ${PARALLEL_JOBS}: Use the calculated or user-capped number of parallel processes.
    # -n 1: Pass one domain at a time to each process.
    # bash -c '...' : Execute a shell command string in a new bash instance.
    # check_domain_status "$1" : Call the exported function with the domain.
    # _ : This argument sets $0 for the bash -c subshell, preventing unintended behavior.
    cat "${SERVERFILE}" | xargs -P "${PARALLEL_JOBS}" -n 1 bash -c 'check_domain_status "$1"' _

else
    usage
    exit 1
fi

echo # Add an extra newline for cleaner output.

exit 0
