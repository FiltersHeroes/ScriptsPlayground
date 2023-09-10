#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# Expired Domains Remover For Filterlists
# v1.6
# Usage: EDRFF.py pathToSections listOfExpiredDomains.txt TLD (optional) "exclude"(optional)

import os
import sys
import shutil
import re
from tempfile import NamedTemporaryFile

pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))
main_path = pn(script_path+"/..")
temp_path = pj(main_path, "temp")

sections_path = sys.argv[1]
sections = sorted(os.listdir(sections_path))

regex_list = []

if os.path.isdir(temp_path):
    shutil.rmtree(temp_path)

os.makedirs(temp_path)
os.chdir(temp_path)

expired_f_list = []
with open(sys.argv[2], "r", encoding='utf-8') as expired_f:
    for expired_f_line in expired_f:
        if len(sys.argv) >= 4:
            if len(sys.argv) == 5 and sys.argv[4] == "exclude":
                # Exclude domains with specific TLD
                if re.match(".*\."+sys.argv[3] + "$", expired_f_line):
                    expired_f_line = ""
            else:
                # Include only domains with specific TLD
                if not re.match(".*\."+sys.argv[3] + "$", expired_f_line):
                    expired_f_line = ""
        if expired_f_line:
            expired_f_list.append(re.escape(expired_f_line.strip()))

regex_list = []
regex_part_domains = '|'.join(expired_f_list)
regex_part_domains = f"(.*\.)?({regex_part_domains})"
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

for section in sections:
    print(f"Checking {section} ...")
    section_file_path = pj(sys.argv[1], section)
    with open(section_file_path, "r", encoding='utf-8') as section_f, NamedTemporaryFile(dir='.', delete=False, mode="w", encoding='utf-8') as f_out:
        for line in section_f:
            line = line.strip()
            if line := new_regex.sub("", line):
                f_out.write(f"{line}\n")
        os.rename(f_out.name, section_file_path)

os.chdir(main_path)
os.rmdir(temp_path)
