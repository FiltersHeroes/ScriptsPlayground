#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
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

async def bulk_lets_go(limit_value, urls):
    limit = asyncio.Semaphore(limit_value)
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[lets_go(session, url, limit) for url in urls])
        for result in results:
            if result:
                ECO_result = subprocess.run([pj(main_path, "scripts", "ECODFF.py"), pj(
                    main_path, result), "-c 20", "--dns", dns_first, dns_second], check=False, capture_output=True, text=True)
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
    asyncio.run(download("KADhosts.txt",
                "https://raw.githubusercontent.com/FiltersHeroes/KADhosts/master/sections/hostsplus.txt"))
    if not os.path.isdir(pj(main_path, "split")):
        os.makedirs(pj(main_path, "split"))
    s_result = subprocess.run(["split", "--numeric=1", "-d", "-n", f"l/{os.getenv('numberParts')}", pj(main_path, "KADhosts.txt"), pj(
        main_path, "split", "KADhosts_")], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print(s_result.stdout)
elif sys.argv[1].startswith("KAD_") or sys.argv[1].startswith("KADhosts_"):
    ECO_result = subprocess.run([pj(main_path, "scripts", "ECODFF.py"), pj(
        main_path, "split", sys.argv[1]), "--ar", "-c 20", "--dns", dns_first, dns_second], check=False, capture_output=True, text=True)
    if ECO_error := ECO_result.stderr:
        print(ECO_error)
    if ECO_output := ECO_result.stdout:
        print(ECO_output)
    os.remove(pj(main_path, "split", sys.argv[1]))
