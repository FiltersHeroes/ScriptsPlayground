#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import re
import sys
import subprocess
import asyncio
import aiohttp
import git


pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))

git_repo = git.Repo(script_path, search_parent_directories=True)
# Main_path is where the root of the repository is located
main_path = git_repo.git.rev_parse("--show-toplevel")
expired_path = pj(main_path, "expired-domains")

def merge(main_file, files_to_merge):
    with open(main_file, "w", encoding="utf-8") as mf:
        for file_to_merge in files_to_merge:
            if os.path.isfile(file_to_merge):
                if os.path.getsize(file_to_merge) > 0:
                    with open(file_to_merge, "r", encoding="utf-8") as ef:
                        for line in ef:
                            mf.write(f"{line}\n")
                os.remove(file_to_merge)

def mergeWithPat(main_file, files_to_merge_pat):
    with open(main_file, "w", encoding="utf-8") as mf:
        for expired_file_name in os.listdir(expired_path):
            if files_to_merge_pat.match(expired_file_name):
                expired_file = pj(expired_path, expired_file_name)
                if os.path.getsize(expired_file) > 0:
                    with open(expired_file, "r", encoding="utf-8") as ef:
                        for line_m in ef:
                            mf.write(f"{line_m}\n")
                    os.remove(expired_file)

def get_dynamic_connections(num_jobs_str):
    """
    Dynamically adjusts the number of connections per job based on the total number of GitHub Actions jobs.
    This version uses an inverse relationship with an adjustable scaling factor.
    """
    try:
        num_jobs = int(num_jobs_str)
    except (ValueError, TypeError):
        print(f"Warning: NUMBER_OF_KAD_JOBS '{num_jobs_str}' is not a valid integer or not set. Using a sensible default for connections.", file=sys.stderr)
        return 10 # Fallback to a safe default

    MIN_CONNECTIONS_PER_JOB = 5
    MAX_CONNECTIONS_PER_JOB = 20 # Max an individual job will ever try

    # Adjust this value to control the decay rate.
    # A higher value means connections stay higher for more jobs before hitting MIN.
    # Experiment with values:
    # 1.0 (original behavior, aggressive decay)
    # 1.5 (moderate decay, recommended starting point for more speed with few jobs)
    # 2.0 (slower decay, more aggressive total concurrency)
    INVERSE_SCALING_FACTOR = 1.5

    if num_jobs > 0:
        # Multiply MAX_CONNECTIONS_PER_JOB by the scaling factor
        raw_connections = (MAX_CONNECTIONS_PER_JOB * INVERSE_SCALING_FACTOR) / num_jobs
    else:
        raw_connections = MAX_CONNECTIONS_PER_JOB # Fallback if num_jobs somehow is 0 or less

    # Clamp the raw_connections value between MIN and MAX
    connections = max(MIN_CONNECTIONS_PER_JOB, raw_connections)
    connections = min(MAX_CONNECTIONS_PER_JOB, connections)
    
    # Round to the nearest integer
    connections = round(connections)

    print(f"Dynamic connections calculation: {num_jobs} jobs -> {connections} connections per job.", file=sys.stderr)
    return connections

async def lets_go(session: aiohttp.ClientSession, url, limit):
    async with limit:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    file_name = os.path.basename(url)
                    if url == "https://raw.githubusercontent.com/FiltersHeroes/KADhosts/master/sections/hostsplus.txt":
                        file_name = "KADhosts.txt"
                    with open(pj(main_path, file_name), "wb") as fd:
                        async for chunk in resp.content.iter_chunked(10):
                            fd.write(chunk)
        except Exception as e:
            file_name = ""
            print(e)
    return file_name

dns_first = "9.9.9.10"
dns_second = "149.112.112.10"

connections_number = get_dynamic_connections(os.getenv('NUMBER_OF_KAD_JOBS'))

async def bulk_lets_go(limit_value, urls):
    limit = asyncio.Semaphore(limit_value)
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[lets_go(session, url, limit) for url in urls])
        for result in results:
            if result:
                ECO_result = subprocess.run([pj(main_path, "scripts", "ECODFF.py"), pj(
                    main_path, result), "-c", str(connections_number), "--dns", dns_first, dns_second], check=False, capture_output=True, text=True)
                if ECO_error := ECO_result.stderr:
                    print(ECO_error)
                if ECO_output := ECO_result.stdout:
                    print(ECO_output)

PAF_base = "https://raw.githubusercontent.com/FiltersHeroes/PolishAnnoyanceFilters/master/"

PAF_urls = [f"{PAF_base}PAF_arrows.txt",
            f"{PAF_base}PAF_backgrounds_self-advertising.txt",
            f"{PAF_base}PAF_contact_feedback_widgets.txt",
            f"{PAF_base}PAF_e_newspaper.txt",
            f"{PAF_base}PAF_newsletters.txt",
            f"{PAF_base}PAF_other_widgets.txt",
            f"{PAF_base}PAF_pop-ups.txt",
            f"{PAF_base}PAF_push.txt",
            f"{PAF_base}PAF_scrolling_videos.txt"]

PAF_supp_urls = [f"{PAF_base}PAF_backgrounds_self-adv_supp.txt",
                 f"{PAF_base}PAF_comeback_titles.txt",
                 f"{PAF_base}PAF_contact_feedback_widgets_supp.txt",
                 f"{PAF_base}PAF_newsletters_supp.txt",
                 f"{PAF_base}PAF_other_elements_supp.txt",
                 f"{PAF_base}PAF_pop-ups_supp.txt",
                 f"{PAF_base}PAF_push_supp.txt",
                 f"{PAF_base}PAF_scrolling_videos_supp.txt",
                 f"{PAF_base}PAF_tagged_internal_links.txt"]
Social_url = "https://raw.githubusercontent.com/FiltersHeroes/PolishSocialCookiesFiltersDev/master/adblock_social_filters/adblock_social_list.txt"
Social_supp_url = "https://raw.githubusercontent.com/FiltersHeroes/PolishSocialCookiesFiltersDev/master/adblock_social_filters/social_filters_uB_AG.txt"
Cookies_url = "https://raw.githubusercontent.com/FiltersHeroes/PolishSocialCookiesFiltersDev/master/cookies_filters/adblock_cookies.txt"
Cookies_supp_url = "https://raw.githubusercontent.com/FiltersHeroes/PolishSocialCookiesFiltersDev/master/cookies_filters/cookies_uB_AG.txt"

urls = []
if sys.argv[1] == "PAF":
    urls.extend(PAF_urls)
elif sys.argv[1] == "PAF_supp":
    urls.extend(PAF_supp_urls)
elif sys.argv[1] == "PAF_C":
    urls.extend(PAF_urls)
    urls.extend(PAF_supp_urls)
elif sys.argv[1] == "PASS":
    urls.extend(["https://raw.githubusercontent.com/FiltersHeroes/PolishAntiAnnoyingSpecialSupplement/master/polish_rss_filters.txt",
                 "https://raw.githubusercontent.com/FiltersHeroes/PolishAntiAnnoyingSpecialSupplement/master/PASS_supp.txt"])
elif sys.argv[1] == "Social":
    urls.append(Social_url)
elif sys.argv[1] == "Social_supp":
    urls.append(Social_supp_url)
elif sys.argv[1] == "Social_C":
    urls.append(Social_url)
    urls.append(Social_supp_url)
elif sys.argv[1] == "Cookies":
    urls.append(Cookies_url)
elif sys.argv[1] == "Cookies_supp":
    urls.append(Cookies_supp_url)
elif sys.argv[1] == "Cookies_C":
    urls.append(Cookies_url)
    urls.append(Cookies_supp_url)

if not sys.argv[1].startswith("KAD") and not sys.argv[1].startswith("KADhosts"):
    asyncio.run(bulk_lets_go(2, urls))


async def download(file_name, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                content = await resp.text()
                with open(pj(main_path, file_name), "w", encoding="utf8") as fd:
                    fd.write(content)

if sys.argv[1] == "KAD":
    asyncio.run(download(
        "KAD.txt", "https://raw.githubusercontent.com/FiltersHeroes/KAD/master/KAD.txt"))
    if not os.path.isdir(pj(main_path, "split")):
        os.makedirs(pj(main_path, "split"))
    s_result = subprocess.run(["split", "--numeric=1", "-d", "-n", f"l/{os.getenv('numberParts')}", pj(main_path, "KAD.txt"), pj(
        main_path, "split", "KAD_")], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print(s_result.stdout)
elif sys.argv[1] == "KADhosts":
    asyncio.run(download("KADhosts-hostsplus.txt",
                "https://raw.githubusercontent.com/FiltersHeroes/KADhosts/master/sections/hostsplus.txt"))
    asyncio.run(download("KADhosts-hostsplus-cert.txt",
                "https://raw.githubusercontent.com/FiltersHeroes/KADhosts/master/sections/hostsplus-cert.txt"))
    merge(pj(main_path, "KADhosts.txt"), [pj(main_path, "KADhosts-hostsplus.txt"), pj(main_path, "KADhosts-hostsplus-cert.txt")])
    ECO_result = subprocess.run([pj(main_path, "scripts", "ECODFF.py"), pj(
                    main_path, "KADhosts.txt"), "-c", str(connections_number), "--dns", dns_first, dns_second], check=False, capture_output=True, text=True)
    if ECO_error := ECO_result.stderr:
        print(ECO_error)
    if ECO_output := ECO_result.stdout:
        print(ECO_output)
elif sys.argv[1] == "KADhostsWWW":
    online_pat = re.compile(r"KAD(l)?_\d+-online\.txt")
    mergeWithPat(pj(main_path, "KAD-online.txt"), online_pat)
    if not os.path.isdir(pj(main_path, "split")):
        os.makedirs(pj(main_path, "split"))
    WWW_PAT = re.compile(r"^(www[0-9]\.|www\.)")
    with open(pj(main_path, "KAD-online.txt"), "r", encoding="utf-8") as khf, open(pj(main_path, "KADhostsWWW.txt"), "w", encoding="utf-8") as khf_www:
        for line in khf:
            if not WWW_PAT.match(line):
                line = f"0.0.0.0 www.{line}"
                khf_www.write(line)
    os.remove(pj(main_path, "KAD-online.txt"))
    s_result = subprocess.run(["split", "--numeric=1", "-d", "-n", f"l/{os.getenv('numberParts')}", pj(main_path, "KADhostsWWW.txt"), pj(
        main_path, "split", "KADhostsWWW_")], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print(s_result.stdout)
elif sys.argv[1].startswith("KAD_") or sys.argv[1].startswith("KADhostsWWW_"):
    extra_flag = ""
    if not sys.argv[1].startswith("KADhostsWWW_"):
        extra_flag = "--ar --save-online"
    else:
        extra_flag = "--www-only"
    ECO_result = subprocess.run([pj(main_path, "scripts", "ECODFF.py"), pj(
        main_path, "split", sys.argv[1]), extra_flag, "-c", str(connections_number), "--dns", dns_first, dns_second], check=False, capture_output=True, text=True)
    if ECO_error := ECO_result.stderr:
        print(ECO_error)
    if ECO_output := ECO_result.stdout:
        print(ECO_output)
    os.remove(pj(main_path, "split", sys.argv[1]))
