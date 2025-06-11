#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import sys
import re
import glob
import subprocess
from tempfile import NamedTemporaryFile
import git
import importlib.util

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


main_expired_file = pj(expired_path, "KADhostsWWW-expired.txt")
main_parked_file = pj(expired_path, "KADhostsWWW-parked.txt")
main_unknown_file = pj(expired_path, "KADhostsWWW-unknown.txt")
main_unknown_limit_file = pj(expired_path, "KADhostsWWW-unknown_limit.txt")
main_unknown_no_internet_file = pj(
    expired_path, "KADhostsWWW-unknown_no_internet.txt")

merge(main_expired_file, glob.glob(pj(expired_path, "KADhostsWWW_*-expired.txt")))
merge(main_parked_file, glob.glob(pj(expired_path, "KADhostsWWW_*-parked.txt")))
merge(main_unknown_file, glob.glob(pj(expired_path, "KADhostsWWW_*-unknown.txt")))
merge(main_unknown_limit_file, glob.glob(
    pj(expired_path, "KADhostsWWW_*-unknown_limit.txt")))
merge(main_unknown_no_internet_file, glob.glob(
    pj(expired_path, "KADhostsWWW_*-unknown_no_internet.txt")))

# Sort and remove duplicates
temp_path = pj(main_path, "temp")
if not os.path.isdir(temp_path):
    os.mkdir(temp_path)
for main_file in [main_expired_file, main_parked_file, main_unknown_file, main_unknown_limit_file, main_unknown_no_internet_file]:
    if os.path.isfile(main_file):
        with open(main_file, "r", encoding="utf-8") as f_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as f_t:
            for line in sorted(set(f_f)):
                if line:
                    f_t.write(f"{line.strip()}\n")
        os.replace(f_t.name, main_file)

for maybe_empty_file in glob.glob(pj(expired_path, "*.txt")):
    if os.path.isfile(maybe_empty_file) and os.path.getsize(maybe_empty_file) <= 0:
        os.remove(maybe_empty_file)

os.chdir(main_path)
if "CI" in os.environ:
    with git_repo.config_writer() as cw:
        mail = "35114429+PolishRoboDog@users.noreply.github.com"
        name = "PolishRoboDog"
        if "GITHUB_ACTIONS" in os.environ:
            mail = "41898282+github-actions[bot]@users.noreply.github.com"
            name = "github-actions[bot]"
        cw.set_value("user", "name", name).release()
        cw.set_value("user", "email", mail).release()
    git_repo.git.add(expired_path)
    diffs = git_repo.head.commit.diff()
    filterlists = []
    for d in diffs:
        if not d.deleted_file:
            if "KAD" in d.a_path and "KAD" not in filterlists:
                filterlists.append("KAD")
            if "KADhosts" in d.a_path and "KADhosts" not in filterlists:
                filterlists.append("KADhosts")
            if "PAF" in d.a_path and "PolishAnnoyanceFilters" not in filterlists:
                filterlists.append("PolishAnnoyanceFilters")
            if "social" in d.a_path and "PolishSocialCookiesFiltersDev" not in filterlists:
                filterlists.append("PolishSocialCookiesFiltersDev")
            if "polish_rss_filters" in d.a_path and "PolishAntiAnnoyingSpecialSupplement" not in filterlists:
                filterlists.append("PolishAntiAnnoyingSpecialSupplement")
            if "PASS_supp" in d.a_path and "PolishAntiAnnoyingSpecialSupplement" not in filterlists:
                filterlists.append("PolishAntiAnnoyingSpecialSupplement")
            if "cookies" in d.a_path and "PolishSocialCookiesFiltersDev" not in filterlists:
                filterlists.append("PolishSocialCookiesFiltersDev")

    git_mode = "ssh"
    with git_repo.config_reader() as cr:
        url = cr.get_value('remote "origin"', 'url')
        if url.startswith('http'):
            git_mode = "http"
    SFLB_path = pn(main_path+"/scripts/SFLB.py")
    spec = importlib.util.spec_from_file_location("SFLB", SFLB_path)
    SFLB = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(SFLB)
    os.chdir(pn(main_path+"/.."))
    for filterlist in filterlists:
        git_clone_url = ""
        if git_mode == "http":
            git_clone_url = f"https://github.com/FiltersHeroes/{filterlist}.git"
        else:
            git_clone_url = f"git@github.com:FiltersHeroes/{filterlist}.git"
        git.Repo.clone_from(git_clone_url, pj(os.getcwd(), filterlist))
        os.chdir(pn(filterlist))
        conf = SFLB.getValuesFromConf([pj(os.getcwd(), ".SFLB.config")])
        sections_path = pj(os.getcwd(), "sections")
        if hasattr(conf(), 'sectionsPath'):
            sections_path = pn(pj(os.getcwd(), conf().sectionsPath))
        expired_files = []
        f_files = []

        for d in diffs:
            if re.search(r"(expired|unknown|parked)\.txt$", d.a_path) and not d.deleted_file:
                if "PAF" in d.a_path and filterlist == "PolishAnnoyanceFilters":
                    expired_files.append(d.a_path)
                elif d.a_path in ("cookies", "social") and filterlist == "PolishSocialCookiesFiltersDev":
                    expired_files.append(d.a_path)
                elif d.a_path in ("rss", "PASS_supp") and filterlist == "PolishAntiAnnoyingSpecialSupplement":
                    expired_files.append(d.a_path)
                elif "KAD" in d.a_path and filterlist == "KAD" and not "parked" in d.a_path:
                    expired_files.append(d.a_path)
                elif "KADhosts" in d.a_path and filterlist == "KADhosts":
                    expired_files.append(d.a_path)

        f_git_repo = git.Repo(pj(os.getcwd(), ".SFLB.config"), search_parent_directories=True)
        for i, expired_file in enumerate(expired_files):
            f_type = ""
            if not os.path.isdir(temp_path):
                os.mkdir(temp_path)
            if "unknown" in expired_file:
                f_type = "unknown"
            elif "parked" in expired_file:
                f_type = "parked"
            elif "expired" in expired_file:
                f_type = "expired"
            if f_type == "unknown":
                with open(pn(pj(main_path, expired_file)), "r", encoding="utf-8") as e_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w", encoding='utf-8') as f_out:
                    for line in e_f:
                        if line != "":
                            if not ".eu " in line:
                                f_out.write(line.replace(" 000", ""))
                os.replace(f_out.name, pn(pj(main_path, expired_file)))
            print(pn(pj(main_path, expired_file)))
            EDRFF_result = subprocess.run([pj(main_path, "scripts", "EDRFF.py"), sections_path, pn(pj(main_path, expired_file))], check=False, capture_output=True, text=True)
            if EDRFF_error := EDRFF_result.stderr:
                print(EDRFF_error)
            if EDRFF_output := EDRFF_result.stdout:
                print(EDRFF_output)

            if filterlist == "KAD":
                update3pExpired_result = subprocess.run([pj(os.getcwd(), "scripts", "update3pExpired.py"), "CERT", pn(pj(main_path, expired_file))], check=False, capture_output=True, text=True)
                if update3pExpired_error := update3pExpired_result.stderr:
                    print(update3pExpired_error)
                if update3pExpired_output := update3pExpired_result.stdout:
                    print(update3pExpired_output)
                update3pExpired_result = subprocess.run([pj(os.getcwd(), "scripts", "update3pExpired.py"), "LWS", pn(pj(main_path, expired_file))], check=False, capture_output=True, text=True)
                if update3pExpired_error := update3pExpired_result.stderr:
                    print(update3pExpired_error)
                if update3pExpired_output := update3pExpired_result.stdout:
                    print(update3pExpired_output)

            f_git_repo.git.add(sections_path)
            if filterlist == "KAD":
                f_git_repo.git.add(pj(os.getcwd(), "exclusions"))
            patch_content = f_git_repo.git.diff(cached=True)
            patch_file_name = f"{filterlist}_{i}-{f_type}.patch"
            with open(pj(main_path, "expired-domains", "patches", patch_file_name), "w", encoding="utf-8") as patch_file:
                for line in patch_content:
                    patch_file.write(line)
            f_git_repo.index.commit(f"Added to {patch_file_name}\n[ci skip]")

    os.chdir(main_path)
    git_repo.git.add(pj(expired_path, "patches"))
    git_repo.index.commit("Expired domains check\n[ci skip]")
    GIT_SLUG = git_repo.remotes.origin.url.replace(
        'https://', "").replace("git@", "").replace(":", "/")
    git_repo.git.push(f"https://{name}:{os.environ['GIT_TOKEN']}@{GIT_SLUG}")
