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
LIMIT_FILES = [glob.glob(pj(expired_path, "KAD_*-unknown_*.txt"))]

for limit_file in LIMIT_FILES:
    if os.path.isfile(limit_file):
        with open(limit_file, "r", encoding="utf-8") as l_f, open(pj(main_path, "KADl.txt"), "w", encoding="utf-8") as k_f:
            for entry in sorted(set(l_f)):
                if entry := entry.strip().split():
                    k_f.write(f"0.0.0.0 {entry[0]}")
        os.remove(limit_file)

os.environ["CI_TIME_LIMIT"] = "2 hours"

if os.path.isfile(pj(main_path, "KADl.txt")) and os.path.getsize(pj(main_path, "KADl.txt")) > 0:
    ECO_result = subprocess.run([pj(main_path, "scripts", "ECODFF.py"), pj(
        main_path, "KADl.txt")], check=True, capture_output=True)
    print(ECO_result.stdout.decode())
    os.remove(pj(main_path, "KADl.txt"))


expired_files = [glob.glob(pj(expired_path, "KAD_*-expired.txt")),
                 glob.glob(pj(expired_path, "KADl_*-expired.txt"))]
parked_files = [glob.glob(pj(expired_path, "KAD_*-parked.txt")),
                glob.glob(pj(expired_path, "KADl_*-parked.txt"))]
unknown_files = [glob.glob(pj(expired_path, "KAD_*-unknown.txt")),
                 glob.glob(pj(expired_path, "KADl_*-unknown.txt"))]
unknown_limit_files = [glob.glob(pj(expired_path, "KAD_*-unknown_limit.txt")),
                       glob.glob(pj(expired_path, "KADl_*-unknown_limit.txt"))]
unknown_no_internet_files = [glob.glob(pj(expired_path, "KAD_*-unknown_no_internet.txt")),
                             glob.glob(pj(expired_path, "KADl_*-unknown_no_internet.txt"))]

main_expired_file = pj(expired_path, "KAD-expired.txt")
with open(main_expired_file, "w", encoding="utf-8") as mf:
    for expired_file in expired_files:
        if os.path.isfile(expired_file) and os.path.getsize(expired_file) > 0:
            with open(expired_file, "r", encoding="utf-8") as ef:
                for line in ef:
                    mf.write(f"{line}\n")
            os.remove(expired_file)

main_parked_file = pj(expired_path, "KAD-parked.txt")
with open(main_parked_file, "w", encoding="utf-8") as mf:
    for parked_file in parked_files:
        if os.path.isfile(parked_file) and os.path.getsize(parked_file) > 0:
            with open(parked_file, "r", encoding="utf-8") as ef:
                for line in ef:
                    mf.write(f"{line}\n")
            os.remove(parked_file)

main_unknown_file = pj(expired_path, "KAD-unknown.txt")
with open(main_unknown_file, "w", encoding="utf-8") as mf:
    for unknown_file in unknown_files:
        if os.path.isfile(unknown_file) and os.path.getsize(unknown_file) > 0:
            with open(unknown_file, "r", encoding="utf-8") as ef:
                for line in ef:
                    mf.write(f"{line}\n")
            os.remove(unknown_file)

main_unknown_limit_file = pj(expired_path, "KAD-unknown_limit.txt")
with open(main_unknown_limit_file, "w", encoding="utf-8") as mf:
    for unknown_limit_file in unknown_limit_files:
        if os.path.isfile(unknown_limit_file) and os.path.getsize(unknown_limit_file) > 0:
            with open(unknown_limit_file, "r", encoding="utf-8") as ef:
                for line in ef:
                    mf.write(f"{line}\n")
            os.remove(unknown_limit_file)

main_unknown_no_internet_file = pj(expired_path, "KAD-unknown_no_internet.txt")
with open(main_unknown_no_internet_file, "w", encoding="utf-8") as mf:
    for unknown_no_internet_file in unknown_no_internet_files:
        if os.path.isfile(unknown_no_internet_file) and os.path.getsize(unknown_no_internet_file) > 0:
            with open(unknown_no_internet_file, "r", encoding="utf-8") as ef:
                for line in ef:
                    mf.write(f"{line}\n")
            os.remove(unknown_no_internet_file)

# Sort and remove duplicates
temp_path = pj(main_path, "temp")
for main_file in [main_expired_file, main_parked_file, main_unknown_file, main_unknown_limit_file, main_unknown_no_internet_file]:
    if os.path.isfile(main_file):
        with open(main_file, "r", encoding="utf-8") as f_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as f_t:
            for line in sorted(set(f_f)):
                if line:
                    f_t.write(f"{line.strip()}\n")
        os.replace(f_t.name, main_file)
