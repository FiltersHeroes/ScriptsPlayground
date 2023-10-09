#!/usr/bin/env python3
# coding=utf-8
import subprocess
import os
import glob
from setuptools import setup

script_path = os.path.dirname(os.path.realpath(__file__))
pj = os.path.join
locales_path = pj(script_path, "GDE", "locales")

for po_path in glob.glob(pj(locales_path, "*", "LC_MESSAGES", "*.po")):
    mo = po_path.replace('.po', '.mo')
    if os.path.isfile(mo):
        os.remove(mo)
    subprocess.run(['msgfmt', '-o', str(mo), po_path], check=True)

setup()
