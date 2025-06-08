#!/usr/bin/env python3
# coding=utf-8

"""
Program: DSC <Domain Status Check> (Python Version)
Current Version: 1.1

Based on domain-check-2.sh (https://github.com/click0/domain-check-2/blob/master/domain-check-2.sh)
and domains.sh script (https://github.com/tdulcet/Remote-Servers-Status/blob/master/domains.sh).

Purpose:
 DSC checks to see what domain has status (expired, suspended, book blocked, etc).
 DSC can be run in interactive and batch mode.

Requirements:
 - 'whois' command-line tool installed on your system (for most TLDs)
 - requests library (pip install requests) (for .kz domains)
 - beautifulsoup4 library (pip install beautifulsoup4) (for .kz domains)
 - Python 3.9+ for --tz flag (uses 'zoneinfo' standard library module)

Usage:
 Refer to the --help option.

License:
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
"""

import argparse
import datetime
import os
import re
import sys
import time
import asyncio
import subprocess
import json
import socket # Added for Pythonic ping check
from concurrent.futures import ThreadPoolExecutor
from datetime import timezone
from pathlib import Path

# Try to import zoneinfo for timezone support (Python 3.9+)
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False
    # Define a dummy class to avoid NameError if zoneinfo is not available
    class ZoneInfo:
        def __init__(self, key):
            raise ImportError("zoneinfo module is not available. Requires Python 3.9+")
    class ZoneInfoNotFoundError(Exception):
        pass

import requests
from bs4 import BeautifulSoup

# --- Global Configuration ---
# Number of days before expiration to consider a domain "expiring"
WARNDAYS = 30
# Flag to suppress all console output
QUIET = False
# Flag to enable verbose debug output
VERBOSE = False

def get_script_version() -> str:
    """Reads the version from the 'Current Version:' line in the script's docstring."""
    script_path = Path(__file__).resolve()
    with open(script_path, 'r', encoding='utf-8') as f:
        # Read the docstring content
        content = f.read()
        # Search for the main docstring block
        docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        if docstring_match:
            docstring_content = docstring_match.group(1)
            # Search for "Current Version:" within the extracted docstring
            version_match = re.search(r'Current Version:\s*(.*?)$', docstring_content, re.MULTILINE)
            if version_match:
                return version_match.group(1).strip()
    return "Unknown" # Fallback if version line is not found

VERSION = get_script_version()

# User-Agent string for HTTP requests, especially for web scraping
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"

# Number of retry attempts for WHOIS lookups in case of transient errors
RETRY_ATTEMPTS = 3
# Base delay in seconds between retry attempts
BASE_RETRY_DELAY = 1

# Maximum number of parallel jobs to run concurrently
MAX_DEFAULT_PARALLEL_JOBS = 5

# --- Pre-compiled Regex Patterns ---
# Patterns to extract expiration dates from WHOIS output
DATE_PATTERNS = [
    re.compile(r"(?:expiration|expires|expiry|renewal|expire|paid-till|valid until|exp date|vencimiento|validity|registry fee due|fecha de corte).*?[:\]]\s*(.*?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"Дата окончания:\s*(\d{4}\.\d{2}\.\d{2}\s*\d{2}:\d{2}:\d{2})", re.IGNORECASE) # Specific pattern for .kz domains
]

# Patterns to identify various domain statuses from WHOIS output
STATUS_PATTERNS = {
    "Removed": [re.compile(r"The queried object does not exist: previous registration", re.IGNORECASE),
                re.compile(r"is available for registration", re.IGNORECASE),
                re.compile(r"Status: AVAILABLE$", re.IGNORECASE)],
    "Suspended_or_reserved": [re.compile(r"cancelled", re.IGNORECASE),
                              re.compile(r"suspended", re.IGNORECASE),
                              re.compile(r"refused", re.IGNORECASE),
                              re.compile(r"reserved at the", re.IGNORECASE)],
    "Suspended": [re.compile(r"is undergoing proceeding", re.IGNORECASE)],
    "Book_blocked": [re.compile(r"after release from the queue", re.IGNORECASE),
                     re.compile(r"book_blocked", re.IGNORECASE)],
    "Reserved": [re.compile(r"is queued up for registration", re.IGNORECASE)],
    "Redemption_period": [re.compile(r"redemptionPeriod", re.IGNORECASE)],
    "Free": [re.compile(r"is free", re.IGNORECASE)],
    "Limit_exceeded": [re.compile(r"request limit exceeded", re.IGNORECASE),
                       re.compile(r"Query rate exceeded", re.IGNORECASE),
                       re.compile(r"Server is busy now", re.IGNORECASE),
                       re.compile(r"too fast", re.IGNORECASE),
                       re.compile(r"try again", re.IGNORECASE),
                       re.compile(r"later", re.IGNORECASE)],
    "Active_Explicit": [re.compile(r"Status: [ \t]*active", re.IGNORECASE)],
}

# --- Requests Session for .kz lookups (recycles HTTP connections) ---
# Use a session to improve performance by reusing TCP connections
requests_session = requests.Session()
requests_session.headers.update({'User-Agent': USER_AGENT})


# --- Helper Functions ---

def get_cpu_cores() -> int:
    """Detect CPU cores for parallel processing."""
    cores = os.cpu_count()
    return cores if cores is not None and cores > 0 else 4

# Dynamically determine the number of CPU cores and set parallel jobs
CPU_CORES = get_cpu_cores()
PARALLEL_JOBS = min(CPU_CORES * 2, MAX_DEFAULT_PARALLEL_JOBS)

def prints_formatted(domain: str, status: str, expiry_date: [datetime.datetime, str], days_left: [int, str], display_tz_obj: [ZoneInfo, None]):
    """Print domain status info in a human-readable table format."""
    if not QUIET:
        expiry_date_str = str(expiry_date) # Default to string for "Unknown" cases or if datetime conversion fails

        if isinstance(expiry_date, datetime.datetime):
            target_expiry_datetime = expiry_date
            if display_tz_obj:
                # Convert to the user-specified timezone if provided
                target_expiry_datetime = expiry_date.astimezone(display_tz_obj)
            elif ZONEINFO_AVAILABLE:
                # Fallback to system's local timezone if no specific TZ is requested and zoneinfo is present
                local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
                target_expiry_datetime = expiry_date.astimezone(local_timezone)
            # If zoneinfo not available and no explicit TZ, expiry_date remains UTC from parsing

            # Format the datetime object for display
            expiry_date_str = target_expiry_datetime.strftime("%d-%b-%Y-%H:%M:%S-%Z")

        # Print the formatted output using f-strings for alignment
        print(f"{domain:<35} {status:<21} {expiry_date_str:<31} {str(days_left):<5}")

def print_heading():
    """Print output table header."""
    if not QUIET:
        print(f"\n{'Domain':<35} {'Status':<21} {'Expires':<31} {'Days Left':<5}")
        print("-" * 35 + " " + "-" * 21 + " " + "-" * 31 + " " + "-" * 9)

def normalize_date_string(date_str: str) -> str:
    """Normalizes a date string for parsing: pads microseconds, standardizes timezone offsets."""
    normalized = date_str.strip()
    # Handle 'Z' (Zulu time) by replacing with '+00:00' for consistent parsing
    if normalized.endswith('Z'):
        normalized = normalized[:-1] + '+00:00'
    # Pad microseconds to 6 digits if present (e.g., '.123' -> '.123000')
    normalized = re.sub(r'(\.\d+)(?=[+-]\d{2}:?\d{2}|$)', lambda m: m.group(1).ljust(7, '0'), normalized)
    # Normalize timezone offsets: e.g., +0200 -> +02:00
    normalized = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', normalized)
    return normalized

def parse_whois_date(date_str: str) -> [datetime.datetime, None]:
    """Parse various WHOIS date formats to a UTC-aware datetime object.
    Returns None if parsing fails for all known formats."""
    if not date_str:
        return None

    normalized_date_str = normalize_date_string(date_str)

    # Date and time formats with various components (year, month, day, hour, minute, second, fractional seconds, timezone)
    datetime_formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z", # ISO 8601 with microseconds and TZ (e.g., 2023-10-26T10:00:00.123456+00:00)
        "%Y-%m-%dT%H:%M:%S%z",    # ISO 8601 with TZ (e.g., 2023-10-26T10:00:00+00:00)
        "%Y-%m-%dT%H:%M:%S.%f",   # ISO 8601 with microseconds (assume UTC if no TZ)
        "%Y-%m-%dT%H:%M:%S",      # ISO 8601 (assume UTC if no TZ)
        "%Y-%m-%d %H:%M:%S%z",    #YYYY-MM-DD HH:MM:SS with TZ (e.g., 2023-10-26 10:00:00+00:00)
        "%Y-%m-%d %H:%M:%S",      #YYYY-MM-DD HH:MM:SS (assume UTC if no TZ)
        "%Y/%m/%d %H:%M:%S",      #YYYY/MM/DD HH:MM:SS (assume UTC if no TZ)
        "%Y.%m.%d %H:%M:%S",      #YYYY.MM.DD HH:MM:SS (for .kz, assume UTC if no TZ)
        "%d-%b-%Y %H:%M:%S",      # DD-Mon-YYYY HH:MM:SS (e.g., 26-Oct-2023 10:00:00, assume UTC)
        "%d/%b/%Y %H:%M:%S",      # DD/Mon/YYYY HH:MM:SS (e.g., 26/Oct/2023 10:00:00, assume UTC)
        "%d %b %Y %H:%M:%S",      # DD Mon Date HH:MM:SS (assume UTC)
        "%a %b %d %H:%M:%S %Z %Y", # Weekday Mon Day HH:MM:SS TZ Year (e.g., Thu Oct 26 10:00:00 UTC 2023)
        "%Y%m%d%H%M%S",            # CompactYYYYMMDDHHMMSS (e.g., 20231026100000, assume UTC)
    ]

    # Try parsing with datetime formats
    for fmt in datetime_formats:
        try:
            dt_obj = datetime.datetime.strptime(normalized_date_str, fmt)
            if dt_obj.tzinfo is None:
                # If parsed without explicit timezone, assume UTC
                dt_obj = dt_obj.replace(tzinfo=timezone.utc)
            else:
                # If a timezone is present, convert it to UTC
                dt_obj = dt_obj.astimezone(timezone.utc)
            return dt_obj
        except ValueError:
            continue

    # Attempt to parse date-only formats, after stripping any time components
    cleaned_date_part = re.sub(r'([T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{4}|Z| UTC| GMT)?)$', '', normalized_date_str, flags=re.IGNORECASE).strip()
    
    date_only_formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", #YYYY-MM-DD variations
        "%d-%b-%Y", "%d/%b/%Y", "%d %b %Y", # DD-Mon-YYYY variations (e.g., 26-Oct-2023)
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", # DD-MM-YYYY variations
        "%m-%d-%Y", "%m/%d-%Y", "%m.%d.%Y", # MM-DD-YYYY variations
        "%b-%d-%Y", "%b/%d-%Y", "%b %d %Y", # Mon-DD-YYYY variations
        "%B %d %Y", "%d %B %Y",             # Full Month Day Year variations (e.g., October 26 2023)
        "%Y%m%d",                           # CompactYYYYMMDD
    ]

    # Standardize separators in the date part for more consistent parsing attempts
    date_part_normalized_separators = cleaned_date_part.replace('.', '-').replace('/', '-')
    
    # List of date strings to attempt parsing, prioritizing common orders
    date_variations = [
        date_part_normalized_separators,
    ]
    
    # If the date string has three parts separated by hyphens (e.g., '26-10-2023'),
    # try reordering them to cover common date formats (e.g., YYYY-MM-DD, MM-DD-YYYY)
    parts = date_part_normalized_separators.split('-')
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        if len(parts[0]) == 2 and len(parts[2]) == 4: # Likely DD-MM-YYYY
            date_variations.append(f"{parts[2]}-{parts[1]}-{parts[0]}") # Try YYYY-MM-DD
        elif len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4: # Likely MM-DD-YYYY (can overlap with DD-MM-YYYY)
            date_variations.append(f"{parts[2]}-{parts[0]}-{parts[1]}") # Try YYYY-DD-MM
        # If already YYYY-MM-DD, no reversal needed
        elif len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2:
            pass

    # Remove duplicates from variations while maintaining order
    date_variations = list(dict.fromkeys(date_variations))

    # Try parsing with date-only formats
    for var_str in date_variations:
        for fmt in date_only_formats:
            try:
                dt_obj = datetime.datetime.strptime(var_str, fmt)
                # For date-only, assume start of day (midnight) in UTC
                return dt_obj.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    
    return None

def get_whois_kz(domain: str) -> str:
    """Performs WHOIS lookup for .kz domains by scraping the ps.kz website.
    Raises requests.exceptions.RequestException on HTTP errors or timeouts."""
    response = requests_session.get(f"https://www.ps.kz/domains/whois/result?q={domain}", timeout=15)
    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def get_whois_generic(domain: str) -> dict:
    """Performs generic WHOIS lookup using the 'whois' command-line tool.
    Returns a dictionary containing the output and return code of the subprocess."""
    cmd = ["whois", domain]
    process = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False, # Do not raise CalledProcessError for non-zero exit codes
        timeout=20 # Increased timeout for potential slow WHOIS servers
    )
    # Combine stdout and stderr for full WHOIS output
    return {"output": process.stdout + process.stderr, "returncode": process.returncode}

# Maps TLDs to their specific WHOIS lookup functions.
WHOIS_HANDLERS = {
    "kz": get_whois_kz,
}

# --- Domain Checker ---

def check_domain_status(domain: str) -> dict:
    """Retrieves WHOIS data, parses expiry, and determines domain status.
    Returns a dictionary containing domain, status, expiry_date, and days_left."""
    if VERBOSE:
        print(f"DEBUG: Checking domain: {domain}", file=sys.stderr)

    expiry_datetime = None
    whois_output_text = ""
    error_status = None # Stores errors like "Limit_exceeded", "Tool_missing", etc.
    adate_for_unknown_status = "" # Holds the raw date string if parsing fails but a date was found

    # Determine the Top-Level Domain (TLD) and select the appropriate WHOIS handler
    tld = domain.split('.')[-1].lower()
    whois_function = WHOIS_HANDLERS.get(tld, get_whois_generic)

    for attempt in range(RETRY_ATTEMPTS):
        try:
            # Handle .kz domains which require web scraping and return raw string
            if tld == "kz":
                raw_whois_data = whois_function(domain)
                # Check for rate limit specific to .kz web WHOIS first
                if any(p.search(raw_whois_data) for p in STATUS_PATTERNS["Limit_exceeded"]):
                    error_status = "Limit_exceeded"
                    break # Break retry loop if rate limited
                whois_output_text = raw_whois_data
                
            # Handle generic domains which use the `whois` command and return a dict
            else: # Generic TLDs using `whois` command
                raw_whois_data = whois_function(domain) # This now returns {'output': ..., 'returncode': ...}
                whois_output_text = raw_whois_data["output"]
                whois_return_code = raw_whois_data["returncode"]

                # If the whois command returned a non-zero exit code AND no output,
                # then it's a command error. Otherwise, proceed with parsing output.
                if not whois_output_text.strip() and whois_return_code != 0:
                    error_status = f"WHOIS_Cmd_Error_{whois_return_code}"
                    if VERBOSE:
                        print(f"DEBUG: 'whois {domain}' returned exit code {whois_return_code} with no output.", file=sys.stderr)
                    # This error is considered non-retryable in this context if no output
                    break # Exit retry loop

            if VERBOSE:
                print(f"DEBUG: WHOIS output for {domain}:\n{whois_output_text[:500]}...", file=sys.stderr)

            # Extract the expiration date string from the WHOIS output
            extracted_date_str = None
            for pattern in DATE_PATTERNS:
                date_match = pattern.search(whois_output_text)
                if date_match:
                    extracted_date_str = date_match.group(1).strip()
                    break

            if extracted_date_str:
                adate_for_unknown_status = extracted_date_str # Store raw date string
                expiry_datetime = parse_whois_date(extracted_date_str)

            if VERBOSE and not expiry_datetime:
                print(f"DEBUG: No valid expiration date found/parsed for {domain} from raw: '{extracted_date_str}'.", file=sys.stderr)

            error_status = None # Clear error status if we got any output to parse
            break # Exit retry loop on successful WHOIS data retrieval and initial parsing attempt

        except FileNotFoundError:
            error_status = "Tool_missing"
            print(f"ERROR: 'whois' command not found. Please install it. Domain: {domain}", file=sys.stderr)
            break # No point in retrying if the tool is missing

        except requests.exceptions.RequestException as e:
            # Handle specific request exceptions for .kz or generic network issues
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None and e.response.status_code in [429, 503, 504]:
                error_status = f"HTTP_Rate_Limit_{e.response.status_code}"
            elif isinstance(e, requests.exceptions.ConnectionError):
                error_status = "Network_Issue"
            elif isinstance(e, requests.exceptions.Timeout):
                error_status = "Timeout"
            else:
                error_status = "HTTP_Request_Error"
            # Allow retries for these specific network/HTTP errors
            if attempt < RETRY_ATTEMPTS - 1:
                delay = BASE_RETRY_DELAY * (2 ** attempt)
                if VERBOSE:
                    print(f"DEBUG: Retrying {domain} in {delay:.2f} seconds...", file=sys.stderr)
                time.sleep(delay)
            else:
                break # No more retries after all attempts

        except subprocess.TimeoutExpired: # Catch timeouts from subprocess.run
            error_status = "Timeout"
            if VERBOSE:
                print(f"DEBUG: 'whois {domain}' subprocess timed out.", file=sys.stderr)
            # Allow retries for timeout
            if attempt < RETRY_ATTEMPTS - 1:
                delay = BASE_RETRY_DELAY * (2 ** attempt)
                if VERBOSE:
                    print(f"DEBUG: Retrying {domain} in {delay:.2f} seconds...", file=sys.stderr)
                time.sleep(delay)
            else:
                break # No more retries after all attempts

        except Exception as e: # Catch any other unexpected errors
            error_status = "Unknown_Error"
            if VERBOSE:
                print(f"DEBUG: An unexpected error occurred for {domain} on attempt {attempt + 1}/{RETRY_ATTEMPTS}: {e}", file=sys.stderr)
            break # Unknown errors are usually not retryable

    current_date = datetime.datetime.now(timezone.utc)
    days_left = "Unknown"
    expiry_date_display = "Unknown" # Will hold datetime object or string representation

    if expiry_datetime:
        time_difference = expiry_datetime - current_date
        days_left = time_difference.days
        expiry_date_display = expiry_datetime # Keep as datetime object for later flexible formatting
    elif adate_for_unknown_status:
        expiry_date_display = f"Unknown ({adate_for_unknown_status})" # Preserve raw date string if parsing failed

    final_status = ""

    # Check for explicit "Status: active" in WHOIS output, often indicates a valid domain
    is_explicitly_active = any(p.search(whois_output_text) for p in STATUS_PATTERNS["Active_Explicit"])

    # Determine the final status based on extracted data and patterns
    if error_status:
        final_status = error_status
    elif any(p.search(whois_output_text) for p in STATUS_PATTERNS["Removed"]):
        final_status = "Removed"
    elif any(p.search(whois_output_text) for p in STATUS_PATTERNS["Suspended_or_reserved"]):
        final_status = "Suspended_or_reserved"
    elif any(p.search(whois_output_text) for p in STATUS_PATTERNS["Suspended"]):
        final_status = "Suspended"
    elif any(p.search(whois_output_text) for p in STATUS_PATTERNS["Book_blocked"]):
        final_status = "Book_blocked"
    elif any(p.search(whois_output_text) for p in STATUS_PATTERNS["Reserved"]):
        final_status = "Reserved"
    elif expiry_datetime and days_left is not None and days_left < 0:
        final_status = "Expired"
    elif any(p.search(whois_output_text) for p in STATUS_PATTERNS["Redemption_period"]):
        final_status = "Redemption_period"
    elif expiry_datetime and days_left is not None and days_left < WARNDAYS:
        final_status = "Expiring"
    elif any(p.search(whois_output_text) for p in STATUS_PATTERNS["Free"]):
        final_status = "Free"
    elif not whois_output_text.strip(): # This branch handles cases where no WHOIS output was obtained
        final_status = "No_internet" # Renamed to match bash script's "No_internet" status
    # This is the crucial part to match the Bash script's logic:
    # If the date is unknown AND it's NOT explicitly marked as active, then it's Unknown.
    elif (expiry_date_display == "Unknown" or (isinstance(expiry_date_display, str) and "Unknown" in expiry_date_display)) and not is_explicitly_active:
        final_status = "Unknown"
    else:
        # Otherwise, if a date was found (and not expired/expiring/etc.), OR
        # if the date is unknown but it *is* explicitly marked as active, it's Valid.
        final_status = "Valid"

    return {
        "domain": domain,
        "status": final_status,
        "expiry_date": expiry_date_display,
        "days_left": days_left
    }

def check_internet_connection() -> bool:
    """Attempts to connect to a reliable host (Google DNS) on a common port (53 or 80)
    to check for internet connectivity.
    Returns True if connected, False otherwise. Prints errors if not quiet mode."""
    host = "8.8.8.8" # Google Public DNS
    ports = [53, 80] # Try DNS port first, then HTTP port
    timeout = 3 # Shorter timeout for a quick check

    for port in ports:
        try:
            # Create a socket object
            s = socket.create_connection((host, port), timeout)
            s.close() # Close the connection immediately as we only need to check connectivity
            return True # Connection successful
        except (socket.timeout, socket.error) as e:
            if VERBOSE:
                print(f"DEBUG: Connection to {host}:{port} failed: {e}", file=sys.stderr)
            continue # Try the next port
        except Exception as e:
            if not QUIET:
                print(f"An unexpected error occurred during general internet connection check: {e}", file=sys.stderr)
            return False # For any other unexpected error, assume no connection

    if not QUIET:
        print("General internet connection check failed after trying all ports. Domains will be marked as 'No_internet'.", file=sys.stderr)
    return False

# --- Main Execution ---

async def main():
    """Main function: parses arguments, sets global configuration, runs domain checks."""
    global QUIET, VERBOSE, WARNDAYS, PARALLEL_JOBS

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="DSC (Domain Status Check) - Checks domain expiration status."
    )
    parser.add_argument(
        "-d", "--domain",
        help="Domain to analyze (interactive mode)."
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="File with a list of domains."
    )
    parser.add_argument(
        "-x", "--expir-days",
        type=int,
        default=WARNDAYS,
        help=f"Domain expiration interval (default: {WARNDAYS} days)."
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Don't print anything to console (overrides --json-output for text output)."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show debug information."
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Print script version."
    )
    parser.add_argument(
        "-t", "--time-limit",
        type=int,
        help="Time limit for running script on CI (in seconds)."
    )
    parser.add_argument(
        "-j", "--jobs-cap",
        type=int,
        help=f"Max parallel jobs (default: min(CPU_CORES*2, {MAX_DEFAULT_PARALLEL_JOBS}) is {PARALLEL_JOBS})."
    )
    parser.add_argument(
        "--tz", "--timezone",
        dest="display_timezone_str",
        help="Display expiration date in specified timezone (e.g., 'UTC', 'Europe/Warsaw'). Requires Python 3.9+."
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output results in JSON format."
    )

    args = parser.parse_args()

    # Apply command-line arguments to global configuration
    QUIET = args.quiet
    VERBOSE = args.verbose
    WARNDAYS = args.expir_days
    JSON_OUTPUT = args.json_output

    # JSON output implies quiet mode for text output
    if JSON_OUTPUT:
        QUIET = True

    if VERBOSE:
        print("DEBUG: Verbose mode enabled.", file=sys.stderr)

    # Set parallel jobs, considering user cap and default limits
    if args.jobs_cap is not None:
        PARALLEL_JOBS = min(args.jobs_cap, MAX_DEFAULT_PARALLEL_JOBS)
    else:
        PARALLEL_JOBS = min(CPU_CORES * 2, MAX_DEFAULT_PARALLEL_JOBS)

    time_limit = args.time_limit

    display_tz_obj = None
    if args.display_timezone_str:
        if not ZONEINFO_AVAILABLE:
            print("ERROR: The --tz/--timezone flag requires Python 3.9+ for the 'zoneinfo' module.", file=sys.stderr)
            print("Please upgrade your Python version or remove the --tz/--timezone flag.", file=sys.stderr)
            sys.exit(1)
        try:
            display_tz_obj = ZoneInfo(args.display_timezone_str)
        except ZoneInfoNotFoundError:
            print(f"ERROR: Invalid timezone specified: '{args.display_timezone_str}'.", file=sys.stderr)
            print("Please provide a valid IANA timezone name (e.g., 'Europe/Warsaw', 'America/New_York', 'UTC').", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Error creating timezone object: {e}", file=sys.stderr)
            sys.exit(1)

    all_results = []
    domains_to_process = []

    # Determine domains to process from either -d or -f argument
    if args.domain:
        domains_to_process.append(args.domain)
    elif args.file:
        if not args.file.is_file():
            print(f"ERROR: Domain file '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
        # Read domains from file, stripping whitespace and ignoring comment lines
        domains_to_process = [line.strip() for line in args.file.read_text(encoding='utf-8').splitlines() if line.strip() and not line.startswith('#')]
    else:
        # If no domain or file is provided, show help message and exit
        parser.print_help()
        sys.exit(1)

    # Perform internet connection check first to quickly mark domains if offline
    is_internet_connected = check_internet_connection()

    # Print table heading if not in quiet or JSON output mode
    if not JSON_OUTPUT and not QUIET:
        print_heading()

    if not is_internet_connected:
        # If no internet, populate all results with "No_internet" status immediately without WHOIS lookups
        for domain in domains_to_process:
            all_results.append({
                "domain": domain,
                "status": "No_internet",
                "expiry_date": "N/A",
                "days_left": "N/A"
            })
    else:
        # Proceed with actual WHOIS lookups if connected to the internet
        start_time = time.monotonic()
        # Use ThreadPoolExecutor for concurrent WHOIS lookups
        with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as executor:
            loop = asyncio.get_event_loop()
            # Create a list of tasks to run check_domain_status for each domain
            tasks = [loop.run_in_executor(executor, check_domain_status, d) for d in domains_to_process]

            if tasks:
                if time_limit:
                    # Calculate remaining time if a time limit is set
                    remaining_time = time_limit - (time.monotonic() - start_time)
                    if remaining_time <= 0:
                        if not QUIET:
                            print(f"\nTime limit of {time_limit} seconds already elapsed. No tasks will be awaited.", file=sys.stderr)
                        # Cancel any tasks that were created but not started due to time limit
                        for task in tasks:
                            task.cancel()
                        tasks = [] # Clear tasks as none will be executed
                    else:
                        # Wait for tasks to complete or for the time limit to be reached
                        done, pending = await asyncio.wait(tasks, timeout=remaining_time)
                        
                        # Add results from completed tasks
                        for fut in done:
                            result = await fut
                            all_results.append(result)

                        # Cancel any pending tasks if the time limit was hit
                        for task in pending:
                            task.cancel()
                            if VERBOSE:
                                print(f"DEBUG: Cancelling pending task: {task}", file=sys.stderr)

                        if pending and not QUIET:
                            print(f"\nTime limit of {time_limit} seconds reached. Remaining {len(pending)} domain checks were cancelled.", file=sys.stderr)
                else:
                    # If no time limit, wait for all tasks to complete
                    results = await asyncio.gather(*tasks)
                    all_results.extend(results)
            else:
                if not QUIET and time_limit:
                    print(f"No domains processed as time limit of {time_limit} seconds was already met or exceeded.", file=sys.stderr)


    # Output results based on the chosen format (JSON or formatted table)
    if JSON_OUTPUT:
        json_ready_results = []
        for result in all_results:
            # Convert datetime objects to ISO format strings for JSON compatibility
            if isinstance(result["expiry_date"], datetime.datetime):
                target_expiry_datetime = result["expiry_date"]
                if display_tz_obj:
                    target_expiry_datetime = result["expiry_date"].astimezone(display_tz_obj)
                elif ZONEINFO_AVAILABLE:
                    local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
                    target_expiry_datetime = result["expiry_date"].astimezone(local_timezone)
                result["expiry_date"] = target_expiry_datetime.isoformat()
            
            json_ready_results.append(result)
        
        print(json.dumps(json_ready_results, indent=2))
    else:
        # Print results in the human-readable table format
        for result in all_results:
            prints_formatted(result["domain"], result["status"], result["expiry_date"], result["days_left"], display_tz_obj)
        if not QUIET:
            print() # Print a newline for better readability at the end

# Entry point for the script execution
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unhandled error occurred: {e}", file=sys.stderr)
        sys.exit(1)