#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import sys
import subprocess
import hashlib
import shutil
from tempfile import NamedTemporaryFile
import git

pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))
main_path = pn(pj(script_path, "..", "GDE"))
ingredients_path = pn(pj(main_path, "ingredients"))

if sys.argv[1] == "ui":
    os.chdir(ingredients_path)
    print("Converting UI files to python...")
    temp_path = pj(main_path, "temp")
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)
    for ui in ["about.ui", "GDE.ui", "group_selection.ui"]:
        py_file = f"{ui.replace('.ui', '_ui')}.py"
        uic_tool = "uic"
        if sys.platform == "win32":
            uic_tool = "pyside2-uic"
        ui_out = subprocess.run([uic_tool, ui, "-o", py_file, "-tr", "translateGDE", "--idbased", "-g=python"], check=False, capture_output=True, text=True)
        print(ui_out.stdout)
        with open(py_file, "r", encoding="utf-8") as py_f, NamedTemporaryFile(dir=temp_path, delete=False, mode="w") as f_t:
            for line in py_f:
                f_t.write(line.replace("PySide2", "qtpy"))
        os.replace(f_t.name, py_file)
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
elif sys.argv[1] == "icons":
    git_repo = git.Repo(script_path, search_parent_directories=True)
    main_git_path = git_repo.git.rev_parse("--show-toplevel")
    icons_path = pn(pj(main_path, "icons"))
    if os.path.exists(pj(icons_path)):
        shutil.rmtree(pj(icons_path))
    icons_src_dirs = [pn(pj(main_git_path, "..", "papirus-icon-theme", "Papirus")), pn(pj(main_git_path, "..", "papirus-icon-theme", "Papirus-Dark")),]
    needed_icons = ["help-about.svg", "document-open.svg", "document-save.svg", "edit-delete.svg", "application-exit.svg", "window-close.svg", "index.theme"]

    for icons_src_dir in icons_src_dirs:
        icons_theme_path = pj(icons_path, os.path.basename(icons_src_dir))
        if not os.path.exists(icons_theme_path):
            os.makedirs(icons_theme_path)
        shutil.copy2(pn(pj(main_git_path, "..", "papirus-icon-theme", "LICENSE")), icons_theme_path)
        for root, dirs, files in os.walk(icons_src_dir):
            for file in files:
                if file in needed_icons:
                    dst = pn(pj(icons_theme_path, os.path.relpath(root, icons_src_dir)))
                    if not os.path.exists(dst):
                        os.makedirs(dst)
                    shutil.copy2(pj(root, file), pj(dst, file))
                    if file == "application-exit.svg":
                        os.rename(pj(dst, file), pj(dst, "exit.svg"))
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
elif sys.argv[1] == "package":
    main_path = pn(pj(script_path, ".."))
    dirs_needs_cleaned = [
        pj(main_path, "build"),
        pj(main_path, "dist"),
        pj(main_path, "GDE.egg-info")
    ]
    for dir_needs_cleaned in dirs_needs_cleaned:
        if os.path.exists(dir_needs_cleaned):
            shutil.rmtree(dir_needs_cleaned)
    os.chdir(main_path)
    print("Packaging...")
    build_tool = subprocess.run(["python", "-m", "build"], check=False, capture_output=True, text=True)
    print(build_tool.stdout)
    print(build_tool.stderr)
    print("Creating installer for Windows...")
    pynsist = subprocess.run(["pynsist", "pynsist.cfg"], check=False, capture_output=True, text=True)
    print(pynsist.stdout)
    print(pynsist.stderr)
    import importlib.util
    spec = importlib.util.spec_from_file_location("GDE", pj(main_path, "GDE", "GDE.py"))
    GDE = importlib.util.module_from_spec(spec)
    sys.modules["GDE"] = GDE
    spec.loader.exec_module(GDE)
    GDE_version = GDE.version()
    shutil.copy2(pj(main_path, "build", "nsis", f"GDE_{GDE_version}-x64_W10.exe"), pj(main_path, "dist"))
    print("Creating checksums...")
    dist_files = [
        pj(main_path, "dist", f"GDE-{GDE_version}.tar.gz"),
        pj(main_path, "dist", f"GDE-{GDE_version}-py3-none-any.whl"),
        pj(main_path, "dist", f"GDE_{GDE_version}-x64_W10.exe"),
    ]
    for dist_file in dist_files:
        if os.path.exists(dist_file):
            with open(dist_file, 'rb') as file_to_check:
                data = file_to_check.read()
            checksum_ext = hashlib.sha256(data).hexdigest()
            checksum_file_path = pj("dist", f"GDE-{GDE_version}.sha256")
            with open(checksum_file_path, "a", encoding='utf-8') as checksum_file:
                checksum_file.write(
                    checksum_ext+"  "+os.path.basename(dist_file)+"\n")
    shutil.rmtree(pj(main_path, "build"))
    shutil.rmtree(pj(main_path, "GDE.egg-info"))
