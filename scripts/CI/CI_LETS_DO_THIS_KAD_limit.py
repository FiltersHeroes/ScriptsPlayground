#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import glob
import re
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
LIMIT_FILES = glob.glob(pj(expired_path, "KAD_*-unknown_*.txt"))

temp_path = pj(main_path, "temp")
if not os.path.isdir(temp_path):
    os.mkdir(temp_path)
with NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as t_f:
    for limit_file in LIMIT_FILES:
        if os.path.isfile(limit_file) and os.path.getsize(limit_file) > 0:
            with open(limit_file, "r", encoding="utf-8") as l_f:
                for entry in l_f:
                    if entry := entry.strip().split():
                        t_f.write(f"0.0.0.0 {entry[0]}\n")
            os.remove(limit_file)

with open(pj(main_path, "KADl_01.txt"), "w", encoding="utf-8") as k_f, open(t_f.name, "r", encoding="utf-8") as tfc:
    if os.path.getsize(t_f.name) > 0:
        for entry in sorted(set(tfc)):
            if entry := entry.strip():
                k_f.write(f"{entry}\n")
os.remove(t_f.name)

if os.path.isfile(pj(main_path, "KADl_01.txt")) and os.path.getsize(pj(main_path, "KADl_01.txt")) > 0:
    ECO_result = subprocess.run([pj(main_path, "scripts", "ECODFF.py"), pj(
        main_path, "KADl_01.txt"), "-c 200"], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(ECO_result.stdout)
    os.remove(pj(main_path, "KADl_01.txt"))


main_expired_file = pj(expired_path, "KAD-expired.txt")
main_parked_file = pj(expired_path, "KAD-parked.txt")
main_unknown_file = pj(expired_path, "KAD-unknown.txt")
main_unknown_limit_file = pj(expired_path, "KAD-unknown_limit.txt")

expired_pat = re.compile(r"KAD(l)?_\d+-expired\.txt")
parked_pat = re.compile(r"KAD(l)?_\d+-parked\.txt")
unknown_pat = re.compile(r"KAD(l)?_\d+-unknown\.txt")
unknown_limit_pat = re.compile(r"KAD(l)?_\d+-unknown_limit\.txt")


def merge(main_file, files_to_merge_pat):
    with open(main_file, "w", encoding="utf-8") as mf:
        for expired_file_name in os.listdir(expired_path):
            if files_to_merge_pat.match(expired_file_name):
                expired_file = pj(expired_path, expired_file_name)
                if os.path.getsize(expired_file) > 0:
                    with open(expired_file, "r", encoding="utf-8") as ef:
                        for line_m in ef:
                            mf.write(f"{line_m}\n")
                    os.remove(expired_file)


merge(main_expired_file, expired_pat)
merge(main_parked_file, parked_pat)
merge(main_unknown_file, unknown_pat)
merge(main_unknown_limit_file, unknown_limit_pat)

# Sort and remove duplicates
if not os.path.isdir(temp_path):
    os.mkdir(temp_path)
for main_file in [main_expired_file, main_parked_file, main_unknown_file, main_unknown_limit_file]:
    if os.path.isfile(main_file):
        with open(main_file, "r", encoding="utf-8") as f_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as f_t:
            for line in sorted(set(f_f)):
                if line := line.strip():
                    f_t.write(f"{line}\n")
        os.replace(f_t.name, main_file)
