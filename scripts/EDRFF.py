#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=C0103
# Expired Domains Remover For Filterlists
# v1.4
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

with open(sys.argv[2], "r", encoding='utf-8') as expired_f:
    for expired_f_line in expired_f:
        expired_f_line = "(.*\.)?" + re.escape(expired_f_line.strip())
        if len(sys.argv) >= 4:
            if len(sys.argv) == 5 and sys.argv[4] == "exclude":
                # Exclude domains with specific TLD
                if re.match(".*\."+sys.argv[3] + "$", expired_f_line):
                    expired_f_line = ""
            else:
                # Include only domains with specific TLD
                if not re.match(".*\."+sys.argv[3] + "$", expired_f_line):
                    expired_f_line = ""

        if expired_f_line != "":
            # ||domain.com
            regex_list.append(re.compile("^\|\|" + expired_f_line + ".*"))
            # $domain=domain.com|
            regex_list.append(re.compile(expired_f_line + "\|"))
            # $domain=|domain.com
            regex_list.append(re.compile("\|" + expired_f_line))
            # $domain=domain.com or ,domain=domain.com
            regex_list.append(re.compile("^(\|\||\/).*(\$|,)domain=" + expired_f_line+"$"))
            # ,domain
            regex_list.append(re.compile("," + expired_f_line))
            # domain,
            regex_list.append(re.compile(expired_f_line + ","))
            # domain##test
            regex_list.append(re.compile("^" + expired_f_line + "\#\#" + ".*"))

for section in sections:
    print(f"Checking {section} ...")
    section_file_path = pj(sys.argv[1], section)
    with open(section_file_path, "r", encoding='utf-8') as section_f, NamedTemporaryFile(dir='.', delete=False) as f_out:
        for line in section_f:
            for regex in regex_list:
                line = regex.sub(r'', line)
            if line.strip():
                f_out.write(line.encode('utf8'))
        os.rename(f_out.name, section_file_path)

os.chdir(main_path)
os.rmdir(temp_path)
