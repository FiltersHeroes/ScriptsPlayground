#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import sys
import glob
import subprocess
from tempfile import NamedTemporaryFile
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


main_expired_file = pj(expired_path, "KADhosts-expired.txt")
main_parked_file = pj(expired_path, "KADhosts-parked.txt")
main_unknown_file = pj(expired_path, "KADhosts-unknown.txt")
main_unknown_limit_file = pj(expired_path, "KADhosts-unknown_limit.txt")
main_unknown_no_internet_file = pj(
    expired_path, "KADhosts-unknown_no_internet.txt")

merge(main_expired_file, glob.glob(pj(expired_path, "KADhosts_*-expired.txt")))
merge(main_parked_file, glob.glob(pj(expired_path, "KADhosts_*-parked.txt")))
merge(main_unknown_file, glob.glob(pj(expired_path, "KADhosts_*-unknown.txt")))
merge(main_unknown_limit_file, glob.glob(
    pj(expired_path, "KADhosts_*-unknown_limit.txt")))
merge(main_unknown_no_internet_file, glob.glob(
    pj(expired_path, "KADhosts_*-unknown_no_internet.txt")))

# Sort and remove duplicates
temp_path = pj(main_path, "temp")
if not os.path.isdir(temp_path):
    os.mkdir(temp_path)
temp_path = pj(main_path, "temp")
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
    git_repo.git.add(expired_path, update=True)
    git_repo.index.commit("Expired domains check\n[ci skip]")
    GIT_SLUG = git_repo.remotes.origin.url.replace(
        'https://', "").replace("git@", "").replace(":", "/")
    git_repo.git.push(f"https://{name}:{os.environ['GIT_TOKEN']}@{GIT_SLUG}")
