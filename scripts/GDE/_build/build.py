#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import sys
import subprocess

pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))
main_path = pn(pj(script_path, "..", "GDE"))
ingredients_path = pn(pj(main_path, "ingredients"))

if sys.argv[1] == "ui":
    os.chdir(ingredients_path)
    print("Converting UI files to python...")
    about_ui = subprocess.run(["uic", "about.ui", "-o", "about_ui.py", "-tr", "translateGDE", "--idbased", "-g=python"], check=False, capture_output=True,     text=True)
    print(about_ui.stdout)
    main_ui = subprocess.run(["uic", "GDE.ui", "-o", "GDE_ui.py", "-tr", "translateGDE", "--idbased", "-g=python"], check=False, capture_output=True, text=True)
    print(main_ui.stdout)
    group_selection_ui = subprocess.run(["uic", "group_selection.ui", "-o", "group_selection_ui.py", "-tr", "translateGDE", "--idbased", "-g=python"],     check=False, capture_output=True, text=True)
    print(group_selection_ui.stdout)
elif sys.argv[1] == "tr":
    print("Updating translation files")
    os.chdir(main_path)
    import importlib.util
    spec = importlib.util.spec_from_file_location("GDE", pj(main_path, "GDE.py"))
    GDE = importlib.util.module_from_spec(spec)
    sys.modules["GDE"] = GDE
    spec.loader.exec_module(GDE)
    translation_tool = subprocess.run(["xgettext", pn("./GDE.py"), pn("./ingredients/about_ui.py"), pn("./ingredients/GDE_ui.py"), pn("./ingredients/group_selection_ui.py"), "-o", pj(main_path, "locales", "GDE.pot"), "--keyword=translateGDE", "--package-name", "Groups Domains Extractor", "--copyright-holder", "Filters Heroes", "--package-version", GDE.version()], check=False, capture_output=True, text=True)
    print(translation_tool.stdout)
