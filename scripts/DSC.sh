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
# Current Version: 1.0.24
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
#  Requires 'whois'. 'netcat' ('nc') is recommended for extended internet checks, 'timeout' command is also required. 'jq' is recommended for JSON output.
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
QUIET="FALSE"         # If TRUE, suppress console output (cmdline: -q)
VERSIONENABLE="FALSE" # If TRUE, show script version and exit (cmdline: -V)
VERBOSE="FALSE"       # If TRUE, show debug information (cmdline: -v)
JSON_OUTPUT="FALSE"   # If TRUE, output results in JSON format (cmdline: --json-output)
RATE_LIMIT_DELAY=0.5  # Default delay in seconds between WHOIS/cURL queries to avoid rate limiting (cmdline: -i)
VERSION=$(awk -F': ' '/^# Current Version:/ {print $2; exit}' "$0")
VARUSERAGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
MAX_DEFAULT_PARALLEL_JOBS=5 # Max default parallel jobs
JQ_PATH=$(command -v jq) # Check if jq is available

# Variables for CI Timeout (used with -t)
END_TIME="" # Global variable to store the timestamp when the script should stop
START_TIME=$(date +%s) # Script start time in seconds since epoch

# Detect number of CPU cores for parallel processing
CPU_CORES=$(nproc 2>/dev/null)
# Fallback if nproc is not available
if [ -z "$CPU_CORES" ] || [ "$CPU_CORES" -eq 0 ]; then
    if [ -f /proc/cpuinfo ]; then
        CPU_CORES=$(grep -c ^processor /proc/cpuinfo)
        if [ -z "$CPU_CORES" ] || [ "$CPU_CORES" -eq 0 ]; then
            CPU_CORES=4
        fi
    else
        CPU_CORES=4
    fi
fi

# Set default number of parallel jobs based on CPU_CORES, capped by MAX_DEFAULT_PARALLEL_JOBS.
PARALLEL_JOBS=$CPU_CORES
if [ "$PARALLEL_JOBS" -gt "$MAX_DEFAULT_PARALLEL_JOBS" ]; then
    PARALLEL_JOBS="$MAX_DEFAULT_PARALLEL_JOBS"
fi

USER_JOB_CAP="" # Variable to hold the user-defined cap from -j flag

#####################################################################
# Purpose: Print a line with the expiration interval details.
# Arguments:
#   $1 -> Domain
#   $2 -> Status of domain (e.g., expired or valid)
#   $3 -> Date when domain will expire
#   $4 -> Days left until the domain will expire
#####################################################################
prints() {
    if [ "${QUIET}" != "TRUE" ] && [ "${JSON_OUTPUT}" != "TRUE" ]; then
        MIN_DATE=$(echo "$3" | awk '{ print $1, $2, $4 }')
        printf "%-35s %-21s %-31s %-5s\n" "$1" "$2" "$MIN_DATE" "$4"
    fi
}

####################################################
# Purpose: Print a heading with the relevant columns.
# Arguments: None
####################################################
print_heading() {
    if [ "${QUIET}" != "TRUE" ] && [ "${JSON_OUTPUT}" != "TRUE" ]; then
        printf "\n%-35s %-21s %-31s %-5s\n" "Domain" "Status" "Expires" "Days Left"
        echo "----------------------------------- --------------------- ------------------------------- ---------"
    fi
}

##################################################################
# Purpose: Access whois data to grab the expiration date and determine domain status.
# Arguments:
#   $1 -> Domain to check
#   $2 -> Global END_TIME (epoch seconds) for CI timeout
#   $3 -> Flag for internet_connected (TRUE/FALSE)
#   $4 -> Flag for JSON_OUTPUT (TRUE/FALSE)
##################################################################
check_domain_status() {
    local DOMAIN="$1"
    local SCRIPT_END_TIME="$2"
    local INTERNET_CONNECTED="$3"
    local IS_JSON_OUTPUT="$4"

    if [ "${INTERNET_CONNECTED}" != "TRUE" ]; then
        if [ "${IS_JSON_OUTPUT}" == "TRUE" ]; then
            echo "{\"domain\": \"${DOMAIN}\", \"status\": \"No_internet\", \"expiry_date\": \"N/A\", \"days_left\": \"N/A\"}"
        else
            prints "${DOMAIN}" "No_internet" "N/A" "N/A"
        fi
        return 0
    fi

    # Check against the script-wide time limit
    if [ -n "$SCRIPT_END_TIME" ] && [ "$(date +%s)" -ge "$SCRIPT_END_TIME" ]; then
        if [ "${IS_JSON_OUTPUT}" == "TRUE" ]; then
             echo "{\"domain\": \"${DOMAIN}\", \"status\": \"Timed_out\", \"expiry_date\": \"N/A\", \"days_left\": \"N/A\"}"
        else
            prints "${DOMAIN}" "Timed_out" "N/A" "N/A"
        fi
        return 0
    fi

    local WHOIS_TMP="/var/tmp/whois.$$.${RANDOM}"
    local WHOIS_2_TMP="/var/tmp/whois_2.$$.${RANDOM}"
    local NOW_EPOCH=$(date +%s)

    local DOMAIN="${1}"
    local TLDTYPE=$(echo "${DOMAIN}" | awk -F. '{print tolower($NF);}')
    if [ "${TLDTYPE}" == "" ]; then
        TLDTYPE=$(echo "${DOMAIN}" | awk -F. '{print tolower($(NF-1));}')
    fi
    if [ "${TLDTYPE}" == "ua" -o "${TLDTYPE}" == "pl" -o "${TLDTYPE}" == "net" ]; then
        local SUBTLDTYPE=$(echo "${DOMAIN}" | awk -F. '{print tolower($(NF-1)"."$(NF));}')
    fi

    local WHOIS_CMD=""
    local CURL_CMD=""
    local WHOIS_TIMEOUT=20 # Timeout for individual whois/curl commands

    if [ "${TLDTYPE}" == "kz" ]; then
        CURL_CMD="timeout ${WHOIS_TIMEOUT} curl -s -A \"${VARUSERAGENT}\" \"https://www.ps.kz/domains/whois/result?q=${DOMAIN}\""
        if ! eval "${CURL_CMD}" >"${WHOIS_2_TMP}" 2>/dev/null; then
            if [ "${VERBOSE}" == "TRUE" ]; then echo "DEBUG: curl failed for ${DOMAIN} (kz)." >&2; fi
            rm -f "${WHOIS_2_TMP}"
            if [ "$(date +%s)" -ge "$((NOW_EPOCH + WHOIS_TIMEOUT))" ]; then
                FINAL_STATUS="Timeout"
            else
                FINAL_STATUS="Network_Issue"
            fi
            if [ "${IS_JSON_OUTPUT}" == "TRUE" ]; then
                echo "{\"domain\": \"${DOMAIN}\", \"status\": \"${FINAL_STATUS}\", \"expiry_date\": \"Unknown\", \"days_left\": \"Unknown\"}"
            else
                prints "${DOMAIN}" "${FINAL_STATUS}" "Unknown" "Unknown"
            fi
            # Add a delay after a failed or timed out query
            sleep "${RATE_LIMIT_DELAY}"
            return 0
        fi
    else
        WHOIS_CMD="timeout ${WHOIS_TIMEOUT} whois \"${DOMAIN}\""
        if ! eval "${WHOIS_CMD}" | env LC_CTYPE=C LC_ALL=C tr -d "\r" >"${WHOIS_TMP}" 2>/dev/null; then
            if [ "${VERBOSE}" == "TRUE" ]; then echo "DEBUG: whois command failed for ${DOMAIN}." >&2; fi
            rm -f "${WHOIS_TMP}"
            if [ "$(date +%s)" -ge "$((NOW_EPOCH + WHOIS_TIMEOUT))" ]; then
                FINAL_STATUS="Timeout"
            else
                FINAL_STATUS="Tool_Failed"
            fi
            if [ "${IS_JSON_OUTPUT}" == "TRUE" ]; then
                echo "{\"domain\": \"${DOMAIN}\", \"status\": \"${FINAL_STATUS}\", \"expiry_date\": \"Unknown\", \"days_left\": \"Unknown\"}"
            else
                prints "${DOMAIN}" "${FINAL_STATUS}" "Unknown" "Unknown"
            fi
            # Add a delay after a failed or timed out query
            sleep "${RATE_LIMIT_DELAY}"
            return 0
        fi
    fi

    # Set locale for consistent date parsing.
    export LC_ALL=en_US.UTF-8

    local adate=""
    local parsed_date_epoch=""
    local DOMAINDATE="Unknown"
    local DOMAINDIFF="Unknown"
    local FINAL_STATUS="Unknown"

    # Attempt to extract expiration date from WHOIS output.
    if [ -f "${WHOIS_TMP}" ]; then
        adate=$(cat "${WHOIS_TMP}" | grep -Ei '(expiration|expires|expiry|renewal|expire|paid-till|valid until|exp date|vencimiento|exp date|validity|vencimiento|registry fee due|fecha de corte)(.*)(:|\])' | head -n 1 | sed -n 's/^[^]:]\+[]:][.[:blank:]]*//p')
        adate=${adate%.}

        if [ -n "$adate" ]; then
            if parsed_date_epoch=$(date -u -d "$adate" +%s 2>/dev/null) || \
               parsed_date_epoch=$(date -u -d "${adate//./-}" +%s 2>/dev/null) || \
               parsed_date_epoch=$(date -u -d "${adate//.//}" +%s 2>/dev/null) || \
               parsed_date_epoch=$(date -u -d "$(echo "${adate//./-}" | awk -F'[/-]' '{for(i=NF;i>0;i--) printf "%s%s",$i,(i==1?"\n":"-")}')" +%s 2>/dev/null); then
                DOMAINDATE=$(date -d "@${parsed_date_epoch}" +"%d-%b-%Y-%H:%M:%S-UTC")
                DOMAINDIFF=$(((parsed_date_epoch - NOW_EPOCH) / 86400))
            else
                DOMAINDATE="Unknown ($adate)"
                DOMAINDIFF="Unknown"
            fi
        fi
    fi

    # Special handling for .kz TLD
    if [ "${TLDTYPE}" == "kz" ] && [ -f "${WHOIS_2_TMP}" ] && [ -z "$parsed_date_epoch" ]; then
        adate=$(grep -A 2 'Дата окончания:' "${WHOIS_2_TMP}" | tail -n 1 | awk '{print $1;}' | awk -FT '{print $1}')
        if [ -n "$adate" ]; then
            if parsed_date_epoch=$(date -u -d "${adate}" +%s 2>/dev/null); then
                DOMAINDATE=$(date -d "@${parsed_date_epoch}" +"%d-%b-%Y-%H:%M:%S-UTC")
                DOMAINDIFF=$(((parsed_date_epoch - NOW_EPOCH) / 86400))
            else
                DOMAINDATE="Unknown (kz: $adate)"
                DOMAINDIFF="Unknown"
            fi
        fi
    fi

    # Check for domain removal/availability status from WHOIS output.
    local removed=""
    if [ -f "${WHOIS_TMP}" ]; then
        removed=$(cat "${WHOIS_TMP}" | grep -Ei "(The queried object does not exist: previous registration|is available for registration|Status: AVAILABLE$)")
    fi

    # Initialize variables for various domain statuses.
    local book_blocked=""
    local suspended=""
    local active=""
    local free=""
    local suspended_reserved=""
    local redemption_period=""
    local reserved=""
    local limit_exceeded=""

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
        FINAL_STATUS="Removed"
    elif [ -n "$suspended_reserved" ]; then
        FINAL_STATUS="Suspended_or_reserved"
    elif [ -n "$suspended" ]; then
        FINAL_STATUS="Suspended"
    elif [ -n "$book_blocked" ]; then
        FINAL_STATUS="Book_blocked"
    elif [ -n "$reserved" ]; then
        FINAL_STATUS="Reserved"
    elif [ "${DOMAINDIFF}" != "Unknown" ] && [ "${DOMAINDIFF}" -lt 0 ]; then
        FINAL_STATUS="Expired"
    elif [ -n "${redemption_period}" ]; then
        FINAL_STATUS="Redemption_period"
    elif [ "${DOMAINDIFF}" != "Unknown" ] && [ "${DOMAINDIFF}" -lt "${WARNDAYS}" ]; then
        FINAL_STATUS="Expiring"
    elif [ -n "${free}" ]; then
        FINAL_STATUS="Free"
    elif [ -n "${limit_exceeded}" ] && [ "$DOMAINDATE" == "Unknown" ]; then
        FINAL_STATUS="Limit_exceeded"
    elif [ "${DOMAINDATE}" == "Unknown" ] && [ -z "$active" ]; then
        FINAL_STATUS="Unknown"
    else
        FINAL_STATUS="Valid"
    fi

    if [ "${IS_JSON_OUTPUT}" == "TRUE" ]; then
        # Escape double quotes and backslashes in domain and date for JSON
        local ESCAPED_DOMAIN=$(printf %s "$DOMAIN" | sed 's/"/\\"/g' | sed 's/\\/\\\\/g')
        local ESCAPED_DOMAINDATE=$(printf %s "$DOMAINDATE" | sed 's/"/\\"/g' | sed 's/\\/\\\\/g')
        echo "{\"domain\": \"${ESCAPED_DOMAIN}\", \"status\": \"${FINAL_STATUS}\", \"expiry_date\": \"${ESCAPED_DOMAINDATE}\", \"days_left\": \"${DOMAINDIFF}\"}"
    else
        prints "${DOMAIN}" "${FINAL_STATUS}" "${DOMAINDATE}" "${DOMAINDIFF}"
    fi

    # Add a delay after each successful or processed query to avoid hitting WHOIS server rate limits.
    # This sleep applies per individual whois/curl query processed by each parallel job.
    sleep "${RATE_LIMIT_DELAY}"

    # Clean up temporary files unique to this process.
    [ -f "${WHOIS_TMP}" ] && rm -f "${WHOIS_TMP}"
    [ -f "${WHOIS_2_TMP}" ] && rm -f "${WHOIS_2_TMP}"
}

####################################################
# Purpose: Check for internet connectivity.
# Returns: 0 if connected, 1 if not.
####################################################
check_internet_connection() {
    local PING_HOST="8.8.8.8"
    local CURL_URL="http://www.google.com/generate_204"
    local TIMEOUT_SECONDS=5 # Timeout for ping and curl

    # Try ping first (ICMP)
    if ping -c 1 -W 1 "${PING_HOST}" >/dev/null 2>&1; then
        [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: Ping to ${PING_HOST} successful." >&2
        return 0
    else
        [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: Ping to ${PING_HOST} failed." >&2
    fi

    # Try curl to a known HTTP endpoint (HTTP over TCP)
    if curl --head --silent --fail --max-time "${TIMEOUT_SECONDS}" "${CURL_URL}" >/dev/null 2>&1; then
        [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: HTTP HEAD to ${CURL_URL} successful." >&2
        return 0
    else
        [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: HTTP HEAD to ${CURL_URL} failed." >&2
    fi

    # Define targets for TCP checks.
    local TCP_TARGETS=(
        "8.8.8.8 53 TCP_DNS"      # Google Public DNS
        "1.1.1.1 53 TCP_DNS"      # Cloudflare DNS
        "8.8.8.8 80 TCP_HTTP"     # Google Public DNS
        "google.com 80 TCP_HTTP"  # Google HTTP
        "google.com 443 TCP_HTTPS" # Google HTTPS
    )

    local NC_FOUND=false
    # Check if 'nc' (netcat) command is available.
    if command -v nc >/dev/null; then
        NC_FOUND=true
        local NC_TIMEOUT=3 # Shorter timeout for individual nc attempts
        [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: nc (netcat) found. Using nc for advanced TCP checks." >&2
    else
        local DEV_TCP_TIMEOUT=3 # Shorter timeout for individual /dev/tcp attempts
        [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: nc (netcat) not found. Falling back to /dev/tcp for TCP checks." >&2
    fi


    for target_info in "${TCP_TARGETS[@]}"; do
        read -r host port protocol_type <<< "$target_info" # Parse host, port, protocol_type

        # Prefer 'nc' for TCP checks if available.
        if "${NC_FOUND}"; then
            [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: Trying TCP ${protocol_type} to ${host}:${port} using nc..." >&2
            if nc -zvw"${NC_TIMEOUT}" "${host}" "${port}" >/dev/null 2>&1; then
                [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: TCP ${protocol_type} to ${host}:${port} successful." >&2
                return 0 # Connection successful
            else
                [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: TCP ${protocol_type} to ${host}:${port} failed." >&2
            fi
        # Fallback to /dev/tcp if 'nc' is not found.
        else
            [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: Trying TCP ${protocol_type} to ${host}:${port} using /dev/tcp..." >&2
            # Attempt TCP connection using /dev/tcp (Bash built-in feature) with 'timeout' command to prevent hanging.
            # 'cat < /dev/null' is used to initiate the connection and immediately close it without sending data.
            if timeout "${DEV_TCP_TIMEOUT}" bash -c "cat < /dev/null > /dev/tcp/${host}/${port}" >/dev/null 2>&1; then
                [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: TCP ${protocol_type} to ${host}:${port} successful." >&2
                return 0 # Connection successful
            else
                [ "${VERBOSE}" == "TRUE" ] && echo "DEBUG: Internet check: TCP ${protocol_type} to ${host}:${port} failed." >&2
            fi
        fi
    done

    # If all checks fail, declare no internet
    if [ "${QUIET}" == "FALSE" ] && [ "${JSON_OUTPUT}" == "FALSE" ]; then
        echo "General internet connection check failed after trying all strategies. Domains will be marked as 'No_internet'." >&2
    fi
    return 1
}

##########################################
# Purpose: Describe how the script works.
# Arguments: None
##########################################
usage() {
    echo "Usage: $0 [ -x expir_days ] [ -q ] [ -h ] [ -v ] [ -V ] [ -t time_limit ] [ -j jobs_cap ] [ -i delay_seconds ] [ --json-output ]"
    echo "    {[ -d domain_namee ]} || { -f domainfile}"
    echo ""
    echo "  -d domain        : Domain to analyze (interactive mode)"
    echo "  -f domain file   : File with a list of domains"
    echo "  -h               : Print this screen"
    echo "  -q               : Don't print anything on the console (overrides text output when --json-output is used)"
    echo "  -x days          : Domain expiration interval (e.g., if domain_date < days)"
    echo "  -v               : Show debug information when running script"
    echo "  -V               : Print version of the script"
    echo "  -t time limit    : Time limit for running script on CI (in seconds). Stops processing new domains after this limit."
    echo "  -j jobs_cap      : Maximum number of parallel jobs (caps the default, currently min(CPU_CORES, ${MAX_DEFAULT_PARALLEL_JOBS}) is ${PARALLEL_JOBS})"
    echo "  -i delay_seconds : Delay in seconds between WHOIS/cURL queries to avoid rate limiting (default: ${RATE_LIMIT_DELAY})"
    echo "  --json-output    : Output results in JSON format. Requires 'jq' for pretty printing if installed."
    echo ""
}

# Export global variables and functions for parallel execution with xargs.
export -f check_domain_status
export -f prints
export -f print_heading
export WARNDAYS QUIET VERBOSE VARUSERAGENT JQ_PATH END_TIME START_TIME RATE_LIMIT_DELAY

# Evaluate the options passed on the command line.
while getopts d:f:x:t:vVj:qi:-: option; do
    case "${option}" in
    d) DOMAIN=${OPTARG} ;;
    f) SERVERFILE=$OPTARG ;;
    t) END_TIME=$(( START_TIME + OPTARG )) ;;
    q) QUIET="TRUE" ;;
    x) WARNDAYS=$OPTARG ;;
    v) VERBOSE="TRUE" ;;
    V) VERSIONENABLE="TRUE" ;;
    j) USER_JOB_CAP=$OPTARG ;;
    i) RATE_LIMIT_DELAY=${OPTARG} ;;
    -) # Handle long options
        case "${OPTARG}" in
            json-output) JSON_OUTPUT="TRUE" ;;
            *) echo "ERROR: Unknown option --${OPTARG}"; usage; exit 1 ;;
        esac ;;
    \?)
        usage
        exit 1
        ;;
    esac
done

# Apply user-defined cap if provided and it's lower than the current PARALLEL_JOBS
if [ -n "$USER_JOB_CAP" ]; then
    if [ "$USER_JOB_CAP" -lt "$PARALLEL_JOBS" ]; then
        PARALLEL_JOBS="$USER_JOB_CAP"
    fi
fi

# If JSON output is requested, force QUIET to TRUE for text output
if [ "${JSON_OUTPUT}" == "TRUE" ]; then
    QUIET="TRUE"
fi

# Show debug information if VERBOSE is true.
if [ "${VERBOSE}" == "TRUE" ]; then
    set -x
fi

# Print script version if VERSIONENABLE is true.
if [ "${VERSIONENABLE}" == "TRUE" ]; then
    if [ "${JSON_OUTPUT}" == "TRUE" ]; then
        echo "{\"version\": \"${VERSION}\"}"
    else
        printf "%-15s %-10s\n" "Script version: " "${VERSION}"
    fi
    exit 0
fi

# Main execution block.
# ALL_RESULTS array is only populated for JSON output collection.
# If JSON_OUTPUT is TRUE, results are collected into ALL_RESULTS and printed at the end.
# If JSON_OUTPUT is FALSE, check_domain_status will print directly.
ALL_RESULTS=() # Initialized once globally.

# Perform initial internet connection check
INTERNET_OK="TRUE"
if ! check_internet_connection; then
    INTERNET_OK="FALSE"
    if [ "${QUIET}" == "FALSE" ] && [ "${JSON_OUTPUT}" == "FALSE" ]; then
        echo "Warning: No internet connection detected. All domains will be marked as 'No_internet'." >&2
    fi
fi

if [ "${DOMAIN}" != "" ]; then
    if [ "${JSON_OUTPUT}" != "TRUE" ]; then
        print_heading
        check_domain_status "${DOMAIN}" "${END_TIME}" "${INTERNET_OK}" "${JSON_OUTPUT}"
    else
        RESULT=$(check_domain_status "${DOMAIN}" "${END_TIME}" "${INTERNET_OK}" "${JSON_OUTPUT}")
        ALL_RESULTS+=("${RESULT}")
    fi
elif [ -f "${SERVERFILE}" ]; then
    if [ "${JSON_OUTPUT}" != "TRUE" ]; then
        print_heading
    fi

    DOMAINS_TO_PROCESS=()
    while IFS= read -r line || [[ -n "$line" ]]; do
        line=$(echo "$line" | sed 's/^#.*//' | xargs)
        if [ -n "$line" ]; then
            DOMAINS_TO_PROCESS+=("$line")
        fi
    done < "${SERVERFILE}"

    # Check if time limit has already expired before starting tasks
    if [ -n "$END_TIME" ] && [ "$(date +%s)" -ge "$END_TIME" ]; then
        if [ "${QUIET}" == "FALSE" ] && [ "${JSON_OUTPUT}" == "FALSE" ]; then
            echo -e "\nTime limit of $((END_TIME - START_TIME)) seconds already elapsed. No domains will be processed." >&2
        fi
        if [ "${JSON_OUTPUT}" == "TRUE" ]; then
            for d in "${DOMAINS_TO_PROCESS[@]}"; do
                ALL_RESULTS+=("{\"domain\": \"${d}\", \"status\": \"Timed_out\", \"expiry_date\": \"N/A\", \"days_left\": \"N/A\"}")
            done
        fi
    else
        if [ "${JSON_OUTPUT}" == "TRUE" ]; then
            TMP_RESULTS_FILE=$(mktemp)
            trap "rm -f ${TMP_RESULTS_FILE}" EXIT

            printf "%s\n" "${DOMAINS_TO_PROCESS[@]}" | xargs -I {} -P "${PARALLEL_JOBS}" \
                bash -c 'check_domain_status "$1" "$2" "$3" "$4" >> "$5"' _ {} "${END_TIME}" "${INTERNET_OK}" "${JSON_OUTPUT}" "${TMP_RESULTS_FILE}"

            while IFS= read -r line || [[ -n "$line" ]]; do
                ALL_RESULTS+=("$line")
            done < "${TMP_RESULTS_FILE}"
        else
            printf "%s\n" "${DOMAINS_TO_PROCESS[@]}" | xargs -I {} -P "${PARALLEL_JOBS}" \
                bash -c 'check_domain_status "$1" "$2" "$3" "$4"' _ {} "${END_TIME}" "${INTERNET_OK}" "${JSON_OUTPUT}"
        fi
    fi

else
    usage
    exit 1
fi

# Final JSON output (if requested)
if [ "${JSON_OUTPUT}" == "TRUE" ]; then
    if [ -n "$JQ_PATH" ]; then
        printf '%s\n' "${ALL_RESULTS[@]}" | ${JQ_PATH} -s '.'
    else
        echo "["
        FIRST=true
        for res in "${ALL_RESULTS[@]}"; do
            if [ "$FIRST" = true ]; then
                echo "  ${res}"
                FIRST=false
            else
                echo ", ${res}"
            fi
        done
        echo "]"
        echo "Warning: 'jq' is not installed. JSON output is not pretty-printed." >&2
    fi
fi

# Add an extra newline for cleaner output if not JSON
if [ "${JSON_OUTPUT}" != "TRUE" ]; then
    echo
fi

exit 0