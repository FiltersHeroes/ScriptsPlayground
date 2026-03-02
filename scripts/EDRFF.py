#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# Expired Domains Remover For Filterlists
# v1.9
# Usage: EDRFF.py pathToSections listOfExpiredDomains.txt TLD (optional) "exclude"(optional)

import os
import sys
import shutil
import re
import multiprocessing as mp
import subprocess

pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))
main_path = pn(script_path+"/..")
temp_path = pj(main_path, "temp")

sections_path = sys.argv[1]

regex_list = []
expired_f_list = []
with open(sys.argv[2], "r", encoding='utf-8') as expired_f:
    for expired_f_line in expired_f:
        if len(sys.argv) >= 4:
            tlds = sys.argv[3].split(",")
            for tld in tlds:
                if len(sys.argv) == 5 and sys.argv[4] == "exclude":
                    # Exclude domains with specific TLD
                    if re.match(".*\."+sys.argv[3] + "$", expired_f_line):
                        expired_f_line = ""
                else:
                    # Include only domains with specific TLD
                    if not re.match(".*\."+sys.argv[3] + "$", expired_f_line):
                        expired_f_line = ""
        if expired_f_line := expired_f_line.strip():
            expired_f_list.append(re.escape(expired_f_line))

regex_list = []
regex_part_domains = '|'.join(expired_f_list)
regex_part_domains = f"(?<![\\w-])((?:[\\w-]+\\.)+)?({regex_part_domains})(?![\\w-])"
# ||domain.com
regex_list.append(f"^\|\|{regex_part_domains}.*")
# $domain=domain.com|
regex_list.append(f"{regex_part_domains}\|")
# $domain=|domain.com
regex_list.append(f"\|{regex_part_domains}")
# $domain=domain.com or ,domain=domain.com
regex_list.append(f"^(\|\||\/).*(\$|,)domain={regex_part_domains}$")
# ,domain
regex_list.append(f",{regex_part_domains}")
# domain,
regex_list.append(f"{regex_part_domains},")
# domain##test or domain#?#test or domain$$test
regex_list.append(f"^{regex_part_domains}(\#(\#|\?)|\$\$).*")
merged_regex_list = '|'.join(regex_list)

new_regex = re.compile(f"({merged_regex_list})")
del regex_part_domains, regex_list, merged_regex_list


def remove_domains(line):
    line = line.strip()
    if line := new_regex.sub("", line):
        line = f"{line}\n"
    return line

def process_sections(sections_path):
    ctx = mp.get_context("spawn")
    old_cwd = os.getcwd()

    try:
        with ctx.Pool() as p:
            for root, dirs, files in os.walk(sections_path):
                for section in files:
                    file_path = os.path.join(root, section)
                    print(f"Checking {section} ...")

                    tmp_path = file_path + ".tmp"
                    chunk = []

                    with open(file_path, "r", encoding="utf-8") as f_in, \
                         open(tmp_path, "w", encoding="utf-8") as f_out:

                        for line in f_in:
                            chunk.append(line)
                            if len(chunk) >= 10000:
                                results = p.map(remove_domains, chunk)
                                f_out.writelines(results)
                                chunk = []

                        if chunk:
                            results = p.map(remove_domains, chunk)
                            f_out.writelines(results)

                    os.replace(tmp_path, file_path)

    except KeyboardInterrupt:
        print("Stopping workers gracefully...")
        p.terminate()

    finally:
        os.chdir(old_cwd)

if __name__ == "__main__":
    if os.path.isdir(temp_path):
        shutil.rmtree(temp_path)
    os.makedirs(temp_path, exist_ok=True)
    os.chdir(temp_path)
    process_sections(sections_path)
    os.chdir(main_path)
    if os.path.isdir(temp_path):
        shutil.rmtree(temp_path)

if "KAD" in sections_path and not "KADhosts" in sections_path:
    tp_names = ["CERT", "LWS"]
    main_path = pn(pj(sections_path, ".."))
    for tp_name in tp_names:
        U3E_result = subprocess.run([pj(main_path, "scripts", "update3pExpired.py"), tp_name, sys.argv[2]], check=False, capture_output=True, text=True)
        print(U3E_result.stdout)
        if U3E_result := U3E_result:
            print(U3E_result)
