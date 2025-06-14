#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
#
# ECODFF - Expiration Check Of Domains From Filterlists
"""MIT License

Copyright (c) 2025 Filters Heroes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import os
import argparse
import re
import subprocess
import shutil
import asyncio
from tempfile import NamedTemporaryFile
import sys
import time
import importlib.util
import json
import dns.asyncresolver
from dns.resolver import NoNameservers, NXDOMAIN, NoAnswer, Timeout
import aiohttp
import git

# Version number
SCRIPT_VERSION = "2.0.48"

# Global variable for sleep delay
RATE_LIMIT_DELAY = 0.5 # Seconds

# Define timeouts
DNS_TIMEOUT = 10 # Seconds for DNS queries
HTTP_TIMEOUT = 10 # Seconds for HTTP requests (per connection)

# Helper function to parse time strings to seconds
def parse_time_to_seconds(time_str):
    """
    Parses a human-readable time string (e.g., "2 hours", "30 minutes", "3600") into seconds.
    Supports "seconds", "minutes", "hours", "days".
    If only a number is provided, it's assumed to be in seconds.
    """
    time_str = time_str.strip().lower()
    parts = time_str.split()

    if len(parts) == 1:
        try:
            return int(parts[0]) # Assume it's already in seconds if just a number
        except ValueError:
            pass # Fall through to more complex parsing if not a simple int

    if len(parts) >= 2:
        try:
            value = int(parts[0])
            unit = parts[1]
            if unit.startswith("second"):
                return value
            elif unit.startswith("minute"):
                return value * 60
            elif unit.startswith("hour"):
                return value * 3600
            elif unit.startswith("day"):
                return value * 86400
        except ValueError:
            pass # Invalid number format or unit

    raise ValueError(f"Invalid time format for CI_TIME_LIMIT: '{time_str}'. Expected format like '3600', '2 hours', '30 minutes', or '1 day'.")


# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('path_to_file', type=str, nargs='+', action='store')
parser.add_argument("-c", "--connections", type=int,
                    action='store', default=5)
parser.add_argument("-v", "--version", action='version',
                    version="ECODFF" + ' ' + SCRIPT_VERSION)
parser.add_argument("--dns", action='store', type=str, nargs="+")
parser.add_argument("--ar", "--allow-redirects", action='store_true')
parser.add_argument("--www-only", action='store_true',
                    help="Process only lines containing 'www' and do not remove 'www' prefix. These domains will not be processed with DSC.sh.")
args = parser.parse_args()

pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))

git_repo = git.Repo(script_path, search_parent_directories=True)
# Main_path is where the root of the repository is located
main_path = git_repo.git.rev_parse("--show-toplevel")

temp_path = pj(main_path, "temp")

os.chdir(main_path)

# Initialize SCRIPT_END_TIME based on CI_TIME_LIMIT environment variable
SCRIPT_END_TIME = None
if "CI_TIME_LIMIT" in os.environ:
    ci_time_limit_str = os.getenv("CI_TIME_LIMIT")
    try:
        time_limit_seconds = parse_time_to_seconds(ci_time_limit_str)
        SCRIPT_END_TIME = time.time() + time_limit_seconds
        print(f"CI time limit set for ECODFF: {time_limit_seconds} seconds from now.", file=sys.stderr)
    except ValueError as e:
        print(f"Error parsing CI_TIME_LIMIT for ECODFF: {e}", file=sys.stderr)
        print("ECODFF will proceed without a time limit.", file=sys.stderr)


DSC_CMD_PREFIX = [pj(script_path, "DSC.sh")]
DSC_COMMON_ARGS = ["--json-output", "-q"]


EXPIRED_DIR = pj(main_path, "expired-domains")
if not os.path.isdir(EXPIRED_DIR):
    os.mkdir(EXPIRED_DIR)
    with open(pj(EXPIRED_DIR, ".keep"), 'w', encoding="utf-8") as fp:
        pass

DNS_a = ""
if args.dns:
    DNS_a = args.dns

for path_to_file in args.path_to_file:
    FILTERLIST = os.path.splitext(os.path.basename(path_to_file))[0]
    EXPIRED_FILE = pj(EXPIRED_DIR, FILTERLIST + "-expired.txt")
    UNKNOWN_FILE = pj(EXPIRED_DIR, FILTERLIST + "-unknown.txt")
    LIMIT_FILE = pj(EXPIRED_DIR, FILTERLIST + "-unknown_limit.txt")
    NO_INTERNET_FILE = pj(EXPIRED_DIR, FILTERLIST + "-unknown_no_internet.txt")
    PARKED_FILE = pj(EXPIRED_DIR, FILTERLIST + "-parked.txt")

    FILES_TO_CLEAN = [EXPIRED_FILE, UNKNOWN_FILE,
                      LIMIT_FILE, NO_INTERNET_FILE, PARKED_FILE]
    for file_to_clean in FILES_TO_CLEAN:
        with open(file_to_clean, "w", encoding="utf-8") as file_to_clean_c:
            pass

    PAGE_DOUBLE_PIPE_PAT = re.compile(r"^@?@?\|\|([^\/|^|$\*]+\.\w+)")
    PAGE_PIPE_PAT = re.compile(
        r"(?:\$|\,)(denyallow|domain|from|method|to)\=([^\,\s]+)$")
    PAGE_COMMA_PAT = re.compile(r"^([a-z0-9-~][^\/\*\|\@\"\!]*?)(#|\$\$)")
    PAGE_HOSTS_PAT = re.compile(r"^.*?\d+\.\d+\.\d+\.\d+ (.*)")

    temp_domains_for_processing = []
    WWW_PAT = re.compile(r"^(www[0-9]\.|www\.)")
    IP_PAT = re.compile(r"\d+\.\d+\.\d+\.\d+")
    PAGE_PAT = re.compile(r".*(?<!\*)\..*(?<!\*)$")

    if os.path.isfile(path_to_file):
        with open(path_to_file, "r", encoding="utf-8") as lf:
            for line_lf in lf:
                temp_extracted_domains = []
                if match_2p := PAGE_DOUBLE_PIPE_PAT.match(line_lf):
                    temp_extracted_domains.append(match_2p.group(1))
                if match_p := PAGE_PIPE_PAT.search(line_lf):
                    temp_extracted_domains.extend(match_p.group(2).split("|"))
                if match_c := PAGE_COMMA_PAT.match(line_lf):
                    temp_extracted_domains.extend(match_c.group(1).split(","))
                if match_h := PAGE_HOSTS_PAT.match(line_lf):
                    temp_extracted_domains.append(match_h.group(1))

                for domain_candidate in temp_extracted_domains:
                    domain_candidate = domain_candidate.replace(
                        "~", "")  # Always remove tilde
                    if PAGE_PAT.search(domain_candidate) and not IP_PAT.match(domain_candidate):
                        if args.www_only:
                            # If --www-only is active, only add domains that start with www
                            # and retain the www prefix.
                            if WWW_PAT.match(domain_candidate):
                                temp_domains_for_processing.append(
                                    domain_candidate)
                        else:
                            # If --www-only is NOT active, remove www and add all valid domains.
                            temp_domains_for_processing.append(
                                re.sub(WWW_PAT, "", domain_candidate, count=1))

    # Filter and sort the main 'pages' list after all domains are collected
    pages = sorted(
        {i for i in temp_domains_for_processing if PAGE_PAT.search(i) and not IP_PAT.match(i)})

    PARKED_PAT = []
    with open(pj(main_path, "domainParking.txt"), "r", encoding='utf-8') as parkersFile:
        for park_line in parkersFile:
            PARKED_PAT.append(park_line.strip())

    parked_domains = []
    offline_pages = []
    online_pages = []
    unknown_pages = []
    limit_pages = []

    sem_value = args.connections

    custom_resolver = dns.asyncresolver.Resolver()
    if DNS_a:
        custom_resolver.nameservers = DNS_a
    # Set the global timeout for the resolver
    custom_resolver.timeout = DNS_TIMEOUT
    custom_resolver.lifetime = DNS_TIMEOUT

    SUB_PAT = re.compile(r"(.+\.)+.+\..+$")

    async def domain_dns_check(domain, limit):
        async with limit:
            if SCRIPT_END_TIME and time.time() >= SCRIPT_END_TIME:
                print(f"Skipping DNS check for {domain} due to time limit.")
                return f"{domain} Limit_exceeded"
            status = "online"
            try:
                print(f"Checking the status of {domain}...")
                await asyncio.sleep(RATE_LIMIT_DELAY)
                answers_NS = await custom_resolver.resolve(domain, "NS")
            except NXDOMAIN:
                status = "offline"
            except (NoAnswer, NoNameservers, Timeout) as ex:
                try:
                    print(f"{ex} ({domain})")
                    print(f"Checking the status of {domain} again...")
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                    await custom_resolver.resolve(domain)
                except (NXDOMAIN, Timeout, NoAnswer, NoNameservers):
                    status = "offline"
                except Exception as e:
                    print(f"An unexpected error occurred during DNS retry for {domain}: {e}", file=sys.stderr)
                    status = "offline"
            except Exception as e: # Catch any other unexpected exceptions
                print(f"An unexpected error occurred during DNS check for {domain}: {e}", file=sys.stderr)
                status = "offline"
            else:
                for answer in answers_NS:
                    if any(parked_d in (str(answer)) for parked_d in PARKED_PAT):
                        status = "parked"
            finally:
                result = f"{domain} {status}"
        return result

    async def bulk_domain_dns_check(limit_value):
        limit = asyncio.Semaphore(limit_value)
        entries = await asyncio.gather(*[domain_dns_check(domain, limit) for domain in pages])
        for result in entries:
            splitted_result = result.split()
            if len(splitted_result) < 2:
                continue
            domain_val = splitted_result[0]
            status_val = splitted_result[1]

            if status_val == "offline":
                offline_pages.append(domain_val)
            elif status_val == "parked":
                parked_domains.append(domain_val)
            elif status_val == "Limit_exceeded":
                limit_pages.append(domain_val)
            elif SUB_PAT.search(domain_val):
                online_pages.append(domain_val)

    if not args.www_only:
        asyncio.run(bulk_domain_dns_check(sem_value))
        del pages

    if parked_domains:
        with open(PARKED_FILE, 'w', encoding="utf-8") as p_f:
            for parked_domain in parked_domains:
                p_f.write(f"{parked_domain}\n")
        del parked_domains

    if limit_pages:
        with open(LIMIT_FILE, 'a', encoding="utf-8") as l_f:
            for domain in limit_pages:
                l_f.write(f"{domain}\n")
        del limit_pages

    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
    os.mkdir(temp_path)

    # Conditionally execute DSC.sh processing
    if not args.www_only:
        if offline_pages:
            # Copying URLs containing subdomains
            with NamedTemporaryFile(dir=temp_path, delete=False, mode="w", encoding="utf-8") as sub_temp_file:
                for page in offline_pages:
                    if SUB_PAT.search(page):
                        sub_temp_file.write(f"{page}\n")

            spec = importlib.util.spec_from_file_location(
                "Sd2D", pj(script_path, "Sd2D.py"))
            Sd2D = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(Sd2D)
            results_Sd2D = sorted(set(Sd2D.main(offline_pages)))

            # Variables for collecting results from individual DSC checks
            expired_domains_dsc = []
            limit_domains_dsc = []
            unknown_domains_dsc_collected = []
            valid_domains_dsc = []

            async def domain_dsc_check(domain_to_check, limit):
                async with limit:
                    if SCRIPT_END_TIME and time.time() >= SCRIPT_END_TIME:
                        print(f"Skipping DSC check for {domain_to_check} due to time limit.")
                        return {"domain": domain_to_check, "status": "Limit_exceeded"}

                    await asyncio.sleep(RATE_LIMIT_DELAY)

                    # Calling DSC.sh for a single domain
                    dsc_command = DSC_CMD_PREFIX + ["-d", domain_to_check] + DSC_COMMON_ARGS
                    try:
                        DSC_result = subprocess.run(
                            dsc_command, check=False, capture_output=True, text=True, encoding="utf-8")
                        DSC_raw_output = DSC_result.stdout

                        if DSC_error := DSC_result.stderr:
                            print(f"DSC.sh error for {domain_to_check}: {DSC_error}", file=sys.stderr)

                        if DSC_raw_output:
                            try:
                                # Expecting a JSON array with a single item for individual domain checks
                                dsc_results_json = json.loads(DSC_raw_output)
                                if dsc_results_json and isinstance(dsc_results_json, list) and len(dsc_results_json) > 0:
                                    item = dsc_results_json[0]
                                    domain = item.get("domain", "N/A")
                                    status = item.get("status", "N/A")
                                    print(f"{domain:<35} {status:<21} {item.get('expiry_date', 'Unknown'):<31} {item.get('days_left', 'Unknown'):<5}")
                                    return item
                            except json.JSONDecodeError as e:
                                print(f"ERROR: Could not decode JSON from DSC.sh output for {domain_to_check}: {e}", file=sys.stderr)
                                print(f"Raw DSC.sh output: \n{DSC_raw_output}", file=sys.stderr)
                                return {"domain": domain_to_check, "status": "JSON_decode_error"}
                        return {"domain": domain_to_check, "status": "Unknown"}
                    except subprocess.TimeoutExpired:
                        print(f"DSC.sh command timed out for {domain_to_check}", file=sys.stderr)
                        return {"domain": domain_to_check, "status": "Timed_out"}
                    except Exception as e:
                        print(f"An unexpected error occurred running DSC.sh for {domain_to_check}: {e}", file=sys.stderr)
                        return {"domain": domain_to_check, "status": "Unknown"}


            async def bulk_domain_dsc_check(domains_to_check, limit_value):
                limit = asyncio.Semaphore(limit_value)
                tasks = [domain_dsc_check(domain, limit) for domain in domains_to_check]
                return await asyncio.gather(*tasks)

            # Run bulk DSC checks
            dsc_results = asyncio.run(bulk_domain_dsc_check(results_Sd2D, sem_value))

            EXPIRED_SW = ["Expired", "Book_blocked", "Suspended", "Removed",
                          "Free", "Redemption_period", "Suspended_or_reserved"]

            for item in dsc_results:
                domain = item.get("domain", "N/A")
                status = item.get("status", "N/A")

                if status in EXPIRED_SW:
                    expired_domains_dsc.append(domain)
                elif status in ["Limit_exceeded", "Timed_out", "Timeout", "No_internet", "JSON_decode_error", "Tool_Failed", "Network_Issue"]:
                    limit_domains_dsc.append(domain)
                elif status == "Unknown":
                    unknown_domains_dsc_collected.append(domain)
                elif status == "Valid":
                    valid_domains_dsc.append(domain)

            # Write collected DSC results to files
            with open(EXPIRED_FILE, 'a', encoding="utf-8") as e_f:
                for domain in expired_domains_dsc:
                    e_f.write(f"{domain}\n")
            with open(LIMIT_FILE, 'a', encoding="utf-8") as l_f:
                for domain in limit_domains_dsc:
                    l_f.write(f"{domain}\n")
            # Unknown pages from DSC are added to global unknown_pages for HTTP checks
            unknown_pages.extend(unknown_domains_dsc_collected)

            if valid_domains_dsc:
                regex_domains = re.compile(f"({'|'.join(re.escape(d) for d in valid_domains_dsc)})")
                with open(sub_temp_file.name, "r", encoding="utf-8") as sub_tmp_file:
                    # If subdomains aren't working, but their domains are working, then include subdomains for additional checking
                    for sub_entry in sub_tmp_file:
                        sub_entry = sub_entry.strip()
                        if regex_domains.search(sub_entry):
                            if not sub_entry in valid_domains_dsc: # Ensure no duplicates
                                unknown_pages.append(f"{sub_entry} nonZeroStatus")
                os.remove(sub_temp_file.name)


    request_headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        'Connection': 'keep-alive',
    }

    async def get_status_code(session: aiohttp.ClientSession, url: str, limit, redirect: bool):
        async with limit:
            if SCRIPT_END_TIME and time.time() >= SCRIPT_END_TIME:
                print(f"Skipping HTTP check for {url} due to time limit.")
                return f"{url} Limit_exceeded"
            status_code = "000" # Default to '000' for network issues / unhandled exceptions
            if len(url.split()) > 1:
                url = url.split()[0]
                status_code = "200"
            try:
                print(f"Checking the status of {url}...")
                await asyncio.sleep(RATE_LIMIT_DELAY)
                resp = await session.get(f"http://{url}", allow_redirects=redirect, timeout=HTTP_TIMEOUT)
                status_code = resp.status
                if (400 <= int(status_code) <= 499) and SUB_PAT.search(url):
                    print(f"Checking the status of {url} again...")
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                    resp = await session.get(f"https://{url}", allow_redirects=redirect, timeout=HTTP_TIMEOUT)
                    if resp.status != "000":
                        status_code = resp.status
                if status_code in (301, 302, 307, 308):
                    location = resp.headers.get('Location', '')
                    if location and url in location:
                        status_code = 200
            except (aiohttp.ClientOSError, aiohttp.ClientConnectorError) as ex:
                print(f"{ex} ({url})")
                if "reset by peer" in str(ex) or (not SUB_PAT.search(url)):
                    try:
                        await asyncio.sleep(RATE_LIMIT_DELAY)
                        print(f"Checking the status of {url} again...")
                        newUrl = f"http://{url}"
                        if not SUB_PAT.search(url) and not WWW_PAT.search(url) and not args.www_only:
                            newUrl = f"http://www.{url}"
                        resp = await session.get(newUrl, allow_redirects=redirect, timeout=HTTP_TIMEOUT)
                        status_code = resp.status
                        if status_code in (301, 302, 307, 308):
                            location = resp.headers.get('Location', '')
                            if url in location:
                                status_code = 200
                    except Exception as ex2:
                        print(f"Error during HTTP retry for {url}: {ex2}")
                        if "reset by peer" in str(ex2):
                            status_code = "200"
            except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError) as ex:
                print(f"{ex} ({url})")
                try:
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                    print(f"Checking the status of {url} again...")
                    resp = await session.get(f"http://{url}", allow_redirects=redirect, timeout=HTTP_TIMEOUT)
                    status_code = resp.status
                    if status_code in (301, 302, 307, 308):
                        location = resp.headers.get('Location', '')
                        if url in location:
                            status_code = 200
                except Exception as ex2:
                    print(f"Error during HTTP retry for {url}: {ex2}")
                    if "reset by peer" in str(ex2):
                        status_code = "200"
            except aiohttp.client_exceptions.ClientResponseError as ex:
                print(f"Client response error for {url}: {ex}")
            except Exception as e:
                print(f"An unexpected error occurred during HTTP check for {url}: {e}", file=sys.stderr)
            finally:
                result = f"{str(url)} {str(status_code)}"
        return result

    async def save_status_code(timeout_time, limit_value):
        session_timeout = aiohttp.ClientTimeout(
            total=None, sock_connect=timeout_time, sock_read=timeout_time)
        limit = asyncio.Semaphore(limit_value)

        resolver = aiohttp.AsyncResolver()
        if DNS_a:
            resolver = aiohttp.AsyncResolver(nameservers=DNS_a)

        async with aiohttp.ClientSession(timeout=session_timeout, connector=aiohttp.TCPConnector(resolver=resolver, limit=0), headers=request_headers) as session:
            allow_redirects = False
            if args.ar:
                allow_redirects = True
            statuses = await asyncio.gather(*[get_status_code(session, url, limit, allow_redirects) for url in unknown_pages])
            unknown_pages.clear()
            with open(UNKNOWN_FILE, 'a', encoding="utf-8") as u_f, \
                 open(LIMIT_FILE, 'a', encoding="utf-8") as l_f:
                for status in statuses:
                    print(status)
                    if len(status.split()) > 1:
                        domain_val = status.split()[0]
                        status_code = status.split()[1]

                        if status_code == "Limit_exceeded":
                            l_f.write(f"{domain_val}\n")
                        else: # Only attempt int conversion if not "Limit_exceeded"
                            try:
                                status_code_int = int(status_code)
                                if not (200 <= status_code_int <= 299) and status_code_int != 403:
                                    u_f.write(f"{domain_val} {status_code}\n")
                            except ValueError:
                                # Handle cases where status_code is not an integer
                                if status_code == "Timed_out":
                                    l_f.write(f"{domain_val}\n")
                    else:
                        unknown_pages.append(status.strip())

    if online_pages:
        for online_page in online_pages:
            unknown_pages.append(online_page)
        del online_pages

    if args.www_only:
        unknown_pages = pages
        del pages

    if unknown_pages:
        new_unknown_pages = sorted(set(unknown_pages))
        unknown_pages = new_unknown_pages
        del new_unknown_pages
        # The HTTP_TIMEOUT constant is passed to save_status_code,
        # which then configures the aiohttp.ClientTimeout.
        asyncio.run(save_status_code(HTTP_TIMEOUT, sem_value))

    # Sort and remove duplicated domains
    for e_file in [EXPIRED_FILE, UNKNOWN_FILE, LIMIT_FILE, NO_INTERNET_FILE, PARKED_FILE]:
        if os.path.isfile(e_file):
            with open(e_file, "r", encoding="utf-8") as f_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w", encoding="utf-8") as f_t:
                for line in sorted(set(f_f)):
                    if line:
                        f_t.write(f"{line.strip()}\n")
            os.replace(f_t.name, e_file)

    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
