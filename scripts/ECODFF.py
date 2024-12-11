#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
#
# ECODFF - Expiration Check Of Domains From Filterlists
"""MIT License

Copyright (c) 2024 Filters Heroes

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
import importlib.util
import dns.asyncresolver
from dns.resolver import NoNameservers, NXDOMAIN, NoAnswer, Timeout
import aiohttp
import git

# Version number
SCRIPT_VERSION = "2.0.37"

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('path_to_file', type=str, nargs='+', action='store')
parser.add_argument("-c", "--connections", type=int, action='store', default=20)
parser.add_argument("-v", "--version", action='version',
                    version="ECODFF" + ' ' + SCRIPT_VERSION)
parser.add_argument("--dns", action='store', type=str, nargs="+")
parser.add_argument("--ar", "--allow-redirects", action='store_true')

args = parser.parse_args()

pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))

git_repo = git.Repo(script_path, search_parent_directories=True)
# Main_path is where the root of the repository is located
main_path = git_repo.git.rev_parse("--show-toplevel")

temp_path = pj(main_path, "temp")

os.chdir(main_path)

DSC = [pj(script_path, "DSC.sh")]

if "CI_TIME_LIMIT" in os.environ:
    DSC += ["-t", os.getenv("CI_TIME_LIMIT")]

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

    pages = []
    if os.path.isfile(path_to_file):
        with open(path_to_file, "r", encoding="utf-8") as lf:
            for line_lf in lf:
                if match_2p := PAGE_DOUBLE_PIPE_PAT.match(line_lf):
                    pages.append(match_2p.group(1))
                if match_p := PAGE_PIPE_PAT.search(line_lf):
                    pages.extend(match_p.group(2).split("|"))
                if match_c := PAGE_COMMA_PAT.match(line_lf):
                    pages.extend(match_c.group(1).split(","))
                if match_h := PAGE_HOSTS_PAT.match(line_lf):
                    pages.append(match_h.group(1))

    WWW_PAT = re.compile(r"^(www[0-9]\.|www\.)")
    for i, page in enumerate(pages):
        pages[i] = re.sub(WWW_PAT, "", page.replace("~", ""), count=1)

    PAGE_PAT = re.compile(r".*(?<!\*)\..*(?<!\*)$")
    IP_PAT = re.compile(r"\d+\.\d+\.\d+\.\d+")
    pages = sorted(
        {i for i in pages if PAGE_PAT.search(i) and not IP_PAT.match(i)})


    PARKED_PAT = []
    with open(pj(main_path, "domainParking.txt"), "r", encoding='utf-8') as parkersFile:
        for park_line in parkersFile:
            PARKED_PAT.append(park_line.strip())

    parked_domains = []
    offline_pages = []
    online_pages = []
    unknown_pages = []

    sem_value = args.connections

    custom_resolver = dns.asyncresolver.Resolver()
    if DNS_a:
        custom_resolver.nameservers = DNS_a

    SUB_PAT = re.compile(r"(.+\.)+.+\..+$")

    async def domain_dns_check(domain, limit):
        async with limit:
            status = "online"
            try:
                print(f"Checking the status of {domain}...")
                await asyncio.sleep(1)
                answers_NS = await custom_resolver.resolve(domain, "NS")
            except NXDOMAIN:
                status = "offline"
            except (NoAnswer, NoNameservers, Timeout) as ex:
                try:
                    print(f"{ex} ({domain})")
                    print(f"Checking the status of {domain} again...")
                    await asyncio.sleep(1)
                    await custom_resolver.resolve(domain)
                except (NXDOMAIN, Timeout, NoAnswer, NoNameservers):
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
            if splitted_result[1] == "offline":
                offline_pages.append(splitted_result[0])
            elif splitted_result[1] == "parked":
                parked_domains.append(splitted_result[0])
            elif SUB_PAT.search(splitted_result[0]):
                online_pages.append(splitted_result[0])

    asyncio.run(bulk_domain_dns_check(sem_value))

    if parked_domains:
        with open(PARKED_FILE, 'w', encoding="utf-8") as p_f:
            for parked_domain in parked_domains:
                p_f.write(f"{parked_domain}\n")
        del parked_domains

    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
    os.mkdir(temp_path)

    # Copying URLs containing subdomains
    if offline_pages:
        with NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as sub_temp_file:
            for page in offline_pages:
                if SUB_PAT.search(page):
                    sub_temp_file.write(f"{page}\n")

        spec = importlib.util.spec_from_file_location(
            "Sd2D", pj(script_path, "Sd2D.py"))
        Sd2D = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(Sd2D)
        results_Sd2D = sorted(set(Sd2D.main(offline_pages)))

        with NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as Sd2D_result_file:
            Sd2D_result_file.write('\n'.join(results_Sd2D))
            Sd2D_result_file.write('\n')

        DSC_result = subprocess.run(
            DSC + ["-f", Sd2D_result_file.name], check=False, capture_output=True, text=True)
        DSC_decoded_result = DSC_result.stdout

        os.remove(Sd2D_result_file.name)

        EXPIRED_SW = ["Expired", "Book_blocked", "Suspended", "Removed",
                    "Free", "Redemption_period", "Suspended_or_reserved"]

        if DSC_error := DSC_result.stderr:
            print(DSC_error)

        if DSC_decoded_result:
            print(DSC_decoded_result)
            with open(EXPIRED_FILE, 'w', encoding="utf-8") as e_f, open(LIMIT_FILE, 'w', encoding="utf-8") as l_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as no_internet_temp_file, NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as valid_pages_temp_file:
                for entry in DSC_decoded_result.strip().splitlines():
                    splitted_entry = entry.split()
                    if splitted_entry[1] in EXPIRED_SW:
                        e_f.write(f"{splitted_entry[0]}\n")
                    elif splitted_entry[1] == "Limit_exceeded":
                        l_f.write(f"{splitted_entry[0]}\n")
                    elif splitted_entry[1] == "Unknown":
                        unknown_pages.append(splitted_entry[0])
                    elif splitted_entry[1] == "No_internet":
                        no_internet_temp_file.write(
                            f"{splitted_entry[0]}\n")
                    # We need to know which domains of subdomains are working
                    elif splitted_entry[1] == "Valid":
                        valid_pages_temp_file.write(
                            f"{splitted_entry[0]}\n")
            del DSC_decoded_result, DSC_result

        if os.path.isfile(no_internet_temp_file.name) and os.path.getsize(no_internet_temp_file.name) > 0:
            DSC_result = subprocess.run(
                DSC + ["-f", no_internet_temp_file.name], check=False, capture_output=True, text=True)
            DSC_decoded_result = DSC_result.stdout

            os.remove(no_internet_temp_file.name)

            if DSC_error := DSC_result.stderr:
                print(DSC_error)

            if DSC_decoded_result:
                print(DSC_decoded_result)
                with open(EXPIRED_FILE, 'a', encoding="utf-8") as e_f, open(LIMIT_FILE, 'a', encoding="utf-8") as l_f, open(NO_INTERNET_FILE, 'w', encoding="utf-8") as no_i_f, open(valid_pages_temp_file.name, "a", encoding="utf-8") as valid_temp_file:
                    for entry in DSC_decoded_result.strip().splitlines():
                        splitted_entry = entry.split()
                        if splitted_entry[1] in EXPIRED_SW:
                            e_f.write(f"{splitted_entry[0]}\n")
                        elif splitted_entry[1] == "Limit_exceeded":
                            l_f.write(f"{splitted_entry[0]}\n")
                        elif splitted_entry[1] == "Unknown":
                            unknown_pages.append(splitted_entry[0])
                        elif splitted_entry[1] == "No_internet":
                            no_i_f.write(f"{splitted_entry[0]}\n")
                        # We need to know which domains of subdomains are working
                        elif splitted_entry[1] == "Valid":
                            valid_temp_file.write(
                                f"{splitted_entry[0]}\n")

        if os.path.isfile(valid_pages_temp_file.name) and os.path.isfile(sub_temp_file.name):
            valid_domains = []
            regex_domains = ""
            with open(valid_pages_temp_file.name, "r", encoding="utf-8") as valid_tmp_file:
                for entry in valid_tmp_file:
                    if entry := entry.strip():
                        valid_domains.append(entry)
            if valid_domains:
                regex_domains = re.compile(f"({'|'.join(valid_domains)})")

        with open(sub_temp_file.name, "r", encoding="utf-8") as sub_tmp_file:
            if regex_domains:
                for sub_entry in sub_tmp_file:
                    sub_entry = sub_entry.strip()
                    # If subdomains aren't working, but their domains are working, then include subdomains for additional checking
                    if regex_domains.search(sub_entry):
                        if not sub_entry in valid_domains:
                            unknown_pages.append(sub_entry)
        os.remove(sub_temp_file.name)
        del valid_domains

    request_headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        'Connection': 'keep-alive',
    }

    async def get_status_code(session: aiohttp.ClientSession, url: str, limit, redirect: bool):
        async with limit:
            try:
                print(f"Checking the status of {url}...")
                await asyncio.sleep(1)
                resp = await session.get(f"http://{url}", allow_redirects=redirect)
                status_code = resp.status
                if (400 <= int(status_code) <= 499) and SUB_PAT.search(url):
                    print(f"Checking the status of {url} again...")
                    resp = await session.get(f"https://{url}", allow_redirects=redirect)
                    if resp.status != "000":
                        status_code = resp.status
                if status_code in (301, 302, 307, 308):
                    location = str(resp).split(
                        "Location': \'")[1].split("\'")[0]
                    if url in location:
                        status_code = 200
            except (aiohttp.ClientOSError, aiohttp.ClientConnectorError) as ex:
                print(f"{ex} ({url})")
                if "reset by peer" in str(ex) or (not SUB_PAT.search(url) and not WWW_PAT.search(url)):
                    try:
                        await asyncio.sleep(1)
                        print(f"Checking the status of {url} again...")
                        newUrl = f"http://{url}"
                        if not SUB_PAT.search(url) and not WWW_PAT.search(url):
                            newUrl = f"http://www.{url}"
                        resp = await session.get(newUrl, allow_redirects=redirect)
                        status_code = resp.status
                        if status_code in (301, 302, 307, 308):
                            location = str(resp).split("Location': \'")[1].split("\'")[0]
                            if url in location:
                                status_code = 200
                    except Exception as ex2:
                        print(f"{ex2} ({url})")
                        if "reset by peer" not in str(ex2):
                            status_code = "000"
                        else:
                            status_code = "200"
                else:
                    status_code = "000"
            except (aiohttp.ServerDisconnectedError, asyncio.TimeoutError) as ex:
                print(f"{ex} ({url})")
                try:
                    await asyncio.sleep(1)
                    print(f"Checking the status of {url} again...")
                    resp = await session.get(f"http://{url}", allow_redirects=redirect)
                    status_code = resp.status
                    if status_code in (301, 302, 307, 308):
                        location = str(resp).split("Location': \'")[1].split("\'")[0]
                        if url in location:
                            status_code = 200
                except Exception as ex2:
                    print(f"{ex2} ({url})")
                    if "reset by peer" not in str(ex2):
                        status_code = "000"
                    else:
                        status_code = "200"
            except aiohttp.client_exceptions.ClientResponseError as ex:
                print(f"{ex} ({url})")
                status_code = "000"
            finally:
                result = ""
                if "status_code" in locals():
                    result = f"{str(url)} {str(status_code)}"
        return result

    async def save_status_code(timeout_time, limit_value):
        session_timeout = aiohttp.ClientTimeout(
            total=None, sock_connect=timeout_time, sock_read=timeout_time)
        limit = asyncio.Semaphore(limit_value)
        resolver = aiohttp.AsyncResolver()
        if DNS_a:
            resolver = aiohttp.AsyncResolver(nameservers=DNS_a)
        async with aiohttp.ClientSession(timeout=session_timeout, connector=aiohttp.TCPConnector(resolver=resolver), headers=request_headers) as session:
            allow_redirects = False
            if args.ar:
                allow_redirects = True
            statuses = await asyncio.gather(*[get_status_code(session, url, limit, allow_redirects) for url in unknown_pages])
            with open(UNKNOWN_FILE, 'w', encoding="utf-8") as u_f:
                for status in statuses:
                    print(status)
                    if len(status.split()) > 1:
                        status_code = status.split()[1]
                        if SUB_PAT.search(status) and status_code == "000":
                            status_code = 200
                        if not (200 <= int(status_code) <= 299) and status_code != "403":
                            u_f.write(f"{status}\n")

    if online_pages:
        for online_page in online_pages:
            unknown_pages.append(online_page)
        del online_pages
    
    if unknown_pages:
        new_unknown_pages = sorted(set(unknown_pages))
        unknown_pages = new_unknown_pages
        del new_unknown_pages
        asyncio.run(save_status_code(10, sem_value))

    # Sort and remove duplicated domains
    for e_file in [EXPIRED_FILE, UNKNOWN_FILE, LIMIT_FILE, NO_INTERNET_FILE, PARKED_FILE]:
        if os.path.isfile(e_file):
            with open(e_file, "r", encoding="utf-8") as f_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as f_t:
                for line in sorted(set(f_f)):
                    if line:
                        f_t.write(f"{line.strip()}\n")
            os.replace(f_t.name, e_file)

    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
