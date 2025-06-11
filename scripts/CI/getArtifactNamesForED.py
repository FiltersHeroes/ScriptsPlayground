#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import sys

names=[]
needed_env = 2

if sys.argv[1] == "KAD" and "NUMBER_OF_KAD_JOBS" in os.environ:
    needed_env = int(os.getenv("NUMBER_OF_KAD_JOBS"))
elif sys.argv[1] == "KADhostsWWW" and "NUMBER_OF_KADHOSTSWWW_JOBS" in os.environ:
    needed_env = int(os.getenv("NUMBER_OF_KADHOSTSWWW_JOBS"))

for i in range(1, needed_env + 1):
    if i < 10:
        file_number = f"0{i}"
    else:
        file_number = i
    names.append(f"E_{sys.argv[1]}_{file_number}")

env_file = os.getenv("GITHUB_ENV")
with open(env_file, "a", encoding="utf-8") as env_file_c:
    env_file_c.write(f"E_{sys.argv[1]}_NAMES<<EOF\n")
    for file_name in names:
        env_file_c.write(f"{file_name}\n")
    env_file_c.write("EOF\n")
