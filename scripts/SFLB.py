#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=no-member
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=line-too-long
#
"""
    SFLB - Super Filter Lists Builder
    Copyright (c) 2022 Filters Heroes

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
import os
import time
from datetime import timedelta, datetime
import locale
import re
import argparse
import gettext
import shutil
from tempfile import NamedTemporaryFile
import requests
import git
from natsort import natsorted
from natsort import ns
try:
    import FOP_FH as FOP
except ImportError:
    FOP = None

# Version number
SCRIPT_VERSION = "3.0"

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('pathToFinalList', type=str, nargs='+', action='store')
parser.add_argument("-v", "--version",
                    action='version', version="Super Filter Lists Builder" + ' ' + SCRIPT_VERSION)
args = parser.parse_args()


pj = os.path.join
pn = os.path.normpath
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


def special_chars_first(x):
    '''
    Ensure special characters are sorted first.
    https://stackoverflow.com/a/45747571
    '''
    return re.sub(r'^(\W)', r'0\1', x)


def getTranslations():
    # Location of translations
    # We assume that they are in the locales directory,
    # which is in the same directory as the script.
    # However, we allow to set a different path
    # using the SFLB_LOCALES_PATH variable.
    if "SFLB_LOCALES_PATH" not in os.environ:
        locale_path = pj(SCRIPT_PATH, 'locales')
    else:
        locale_path = os.environ.get("SFLB_LOCALES_PATH")

    # Initialize translation
    domain = "SFLB"
    gettext.bindtextdomain(domain, locale_path)
    gettext.textdomain(domain)
    _ = gettext.gettext
    return _


def getGitRepo(pathToFinalLists):
    git_repo = git.Repo(os.path.dirname(os.path.realpath(
        pathToFinalLists[0])), search_parent_directories=True)
    return git_repo


def getMainPath(pathToFinalLists):
    # Main_path is where the root of the repository is located
    # We allow to set a different path using the SFLB_MAIN_PATH variable.
    if "SFLB_MAIN_PATH" not in os.environ:
        if pathToFinalLists:
            git_repo = getGitRepo(pathToFinalLists)
            main_path = git_repo.git.rev_parse("--show-toplevel")
        else:
            main_path = SCRIPT_PATH
    else:
        main_path = os.environ.get("SFLB_MAIN_PATH")
    return pn(main_path)


def getConfigPath(pathToFinalLists):
    # Location of the configuration file
    # We assume it's in main path of the git repository.
    # However, we allow to set a different path
    # using the SFLB_CONFIG_PATH variable.
    if "SFLB_CONFIG_PATH" not in os.environ:
        config_path = pj(getMainPath(pathToFinalLists), ".SFLB.config")
    else:
        config_path = os.environ.get("SFLB_CONFIG_PATH")
    return pn(config_path)


def getValuesFromConf(pathToFinalLists):
    class conf():
        # Read settings from config file
        def __init__(self):
            if os.path.isfile(getConfigPath(pathToFinalLists)):
                with open(getConfigPath(pathToFinalLists), "r", encoding="utf8") as cf:
                    for lineConf in cf:
                        cfProperty = lineConf.strip().split()[
                            0].replace("@", "")
                        if matchC := re.search(r'@'+cfProperty+' (.*)$', lineConf):
                            self[cfProperty] = matchC.group(1)

        def __setitem__(self, key, value):
            setattr(self, key, value)

        def __getitem__(self, key):
            return getattr(self, key)
    return conf


def doItAgainIfNeed(pathToFinalLists):
    SFLB_CHANGED_FILES_PATH = pj(
        getMainPath(pathToFinalLists), "changed_files", "SFLB_CHANGED_FILES.txt")
    if os.path.exists(SFLB_CHANGED_FILES_PATH):
        listOfLists = []
        config_path = getConfigPath(pathToFinalLists)
        with open(config_path, "r", encoding="utf8") as cf:
            PAT = re.compile(r"^@updateListIfAnotherListUpdated (.*)$")
            for line in cf:
                if matchC := PAT.search(line):
                    listOfLists.append(matchC.group(1))
        if listOfLists:
            main_filter_lists = []
            with open(SFLB_CHANGED_FILES_PATH, "r", encoding="utf8") as changed_f:
                changed_f_contents = changed_f.read()
            for someLists in listOfLists:
                listWhichShouldBeUpdated = someLists.split()[0].strip()
                dependentList = someLists.split()[1].strip()
                if listWhichShouldBeUpdated not in changed_f_contents and dependentList in changed_f_contents:
                    main_filter_lists.append(
                        pn(pj(getMainPath(pathToFinalLists), listWhichShouldBeUpdated)))
            main_filter_lists = sorted(set(main_filter_lists))
            if main_filter_lists:
                main(main_filter_lists, "true", "")
        if not "NO_RM_SFLB_CHANGED_FILES" in os.environ:
            os.remove(SFLB_CHANGED_FILES_PATH)


def main(pathToFinalLists, forced, saveChangedFN):
    _ = getTranslations()

    # Go to the directory where the local git repository is located
    git_repo = getGitRepo(pathToFinalLists)
    main_path = getMainPath(pathToFinalLists)
    os.chdir(main_path)

    conf = getValuesFromConf(pathToFinalLists)
    # Configuration of the username and email for CI
    if "CI" in os.environ and "git_repo" in locals():
        with git_repo.config_writer() as cw:
            if hasattr(conf(), 'CIusername'):
                cw.set_value("user", "name", conf().CIusername).release()
            if hasattr(conf(), 'CIemail'):
                cw.set_value("user", "email", conf().CIemail).release()

    if hasattr(conf(), 'messagesLang'):
        os.environ["LANGUAGE"] = conf().messagesLang

    for pathToFinalList in pathToFinalLists:
        # FILTERLIST is filename (without extension), which we want to build
        FILTERLIST = os.path.splitext(os.path.basename(pathToFinalList))[0]

        # Set the path to template
        if hasattr(conf(), 'templatesPath'):
            template_path = pn(pj(main_path, conf().templatesPath,
                               FILTERLIST+".template"))
        else:
            template_path = pj(main_path, "templates", FILTERLIST+".template")

        BACKUP_PATH = pj(os.path.dirname(
            pathToFinalList), FILTERLIST+".backup")

        # Make a copy of the initial file
        shutil.copy(pathToFinalList, BACKUP_PATH)

        # Replace the content of the final file with the content of the template
        shutil.copy(template_path, pathToFinalList)

        # Set the path to sections and set sections extension
        sections_path = pj(main_path, "sections", FILTERLIST)
        sections_ext = "txt"
        if hasattr(conf(), 'sectionsPath'):
            sections_path = pn(pj(main_path, conf().sectionsPath))
        if hasattr(conf(), 'sectionsExt'):
            sections_ext = conf().sectionsExt

        # Set the path to exclusions and set exclusions extension
        exclusions_path = pj(main_path, "exclusions", FILTERLIST)
        exclusions_ext = "txt"
        if hasattr(conf(), 'exclusionsPath'):
            exclusions_path = pn(pj(main_path, conf().exclusionsPath))
        if hasattr(conf(), 'sectionsExt'):
            exclusions_ext = conf().exclusionsExt

        if os.path.isfile(template_path):
            with open(template_path, "r", encoding="utf8") as tf:
                SP_I_PAT = re.compile(r'@sectionsPath (.*)$')
                SE_I_PAT = re.compile(r'@sectionsExt (.*)$')
                EP_I_PAT = re.compile(r'@exclusionsPath (.*)$')
                EE_I_PAT = re.compile(r'@exclusionsExt (.*)$')
                VALID_INSTRUCTIONS_PAT = re.compile(
                    r'^@((sections|exclusions)(Path|Ext)|(HOSTS|DOMAINS|PH|B?NWL)?include)')
                INSTRUCTIONS_START_PAT = re.compile(r'^@')
                for lineT in tf:
                    if not VALID_INSTRUCTIONS_PAT.match(lineT) and INSTRUCTIONS_START_PAT.match(lineT):
                        print(_("Invalid instruction {wrongInstruction} in {fileWithWrongInstruction}.").format(
                            wrongInstruction=lineT.strip(), fileWithWrongInstruction=os.path.basename(tf.name)))
                    if matchT := SP_I_PAT.search(lineT):
                        sections_path = pn(pj(main_path, matchT.group(1)))
                    if matchT := SE_I_PAT.search(lineT):
                        sections_ext = matchT.group(1)
                    if matchT := EP_I_PAT.search(lineT):
                        exclusions_path = matchT.group(1)
                    if matchT := EE_I_PAT.search(lineT):
                        exclusions_ext = matchT.group(1)

        if os.path.exists(sections_path):
            for root, _dirs, files in os.walk(sections_path):
                for sectionF in sorted(files):
                    sectionFpath = pj(root, sectionF)
                    if os.path.isfile(sectionFpath):
                        # Combine some of the filters if FOP is present
                        if FOP is not None:
                            FOP.fopsort(sectionFpath)
                        # Remove blank lines and whitespace from sections
                        with open(sectionFpath, "r", encoding='utf-8') as s_f, NamedTemporaryFile(dir=root, delete=False) as f_out:
                            for lineS in natsorted(set(s_f), alg=ns.GROUPLETTERS, key=special_chars_first):
                                if lineS.strip():
                                    f_out.write(lineS.encode('utf8'))
                        os.replace(f_out.name, sectionFpath)

            # Add modified sections to git repository
            sectionsWereModified = ""
            if not "RTM" in os.environ and "git_repo" in locals():
                M_S_PAT = re.compile(
                    r"^"+re.escape(os.path.basename(sections_path) + "/"))
                for item in git_repo.index.diff(None):
                    if M_S_PAT.search(item.a_path):
                        sectionsWereModified = "true"
                if sectionsWereModified:
                    git_repo.index.add(sections_path)
                    git_repo.index.commit(_("Update sections")+"\n[ci skip]")

        # Let's do some @include magic now
        tempDir = os.path.join(os.path.dirname(pathToFinalList), "temp")
        if os.path.exists(tempDir):
            shutil.rmtree(tempDir)
        os.mkdir(tempDir)
        with open(pathToFinalList, "r", encoding='utf-8') as f_final, NamedTemporaryFile(dir=tempDir, delete=False) as final_tmp:
            INCLUDE_I_PAT = re.compile(r'^@.*?include (.*)$')
            EXTERNAL_PAT = re.compile(r'^(http(s):|ftp:)')
            USELESS_PAT = re.compile(
                r"^(! Checksum)|(!#include)|(\[Adblock Plus 2.0\])|(! Dołączenie listy)")
            USELESS_I_PAT = re.compile(r'@(sections|exclusions)(Path|Ext) (.*)$')

            for lineF in f_final:
                if INCLUDE_I_PAT.search(lineF):
                    lineF_words = lineF.split()
                    instruction = lineF_words[0].replace("@", "")
                    external = lineF_words[1]

                    section = pj(sections_path, external+"."+sections_ext)
                    section2 = ""

                    cloned_external = None
                    cloned_external2 = None
                    external2 = ""
                    exclusions = ""

                    argLen = len(lineF_words) - 1
                    if lineF_words[-2] == "-":
                        exclusions = lineF_words[-1]
                        exclusions_path = pj(
                            exclusions_path, lineF_words[-1]+"."+exclusions_ext)
                        lineF_words.remove(lineF_words[-1])
                        lineF_words.remove(lineF_words[-1])
                        argLen = len(lineF_words) - 1
                    if argLen >= 2:
                        if lineF_words[2] != "+" and lineF_words[2] != "-":
                            cloned_external = lineF_words[2]
                        if argLen == 3:
                            if lineF_words[2] == "+":
                                external2 = lineF_words[3]
                        if argLen == 4:
                            if lineF_words[2] == "+":
                                external2 = lineF_words[3]
                                cloned_external2 = lineF_words[4]
                            elif lineF_words[3] == "+":
                                external2 = lineF_words[4]
                        if argLen >= 5:
                            if lineF_words[3] == "+":
                                external2 = lineF_words[4]
                                cloned_external2 = lineF_words[5]
                        if external2:
                            section2 = pj(
                                sections_path, external2+"."+sections_ext)

                    if VALID_INSTRUCTIONS_PAT.match(lineF_words[0]):
                        external_temp = None
                        if EXTERNAL_PAT.search(external):
                            with NamedTemporaryFile(dir=tempDir, delete=False) as external_temp:
                                # We assume that the directory containing other cloned repository is higher than
                                # the directory of our own list
                                if cloned_external is not None and os.path.exists(pj(main_path, "..", cloned_external)):
                                    cloned_external_file = pj(
                                        main_path, "..", cloned_external)
                                    shutil.copy(cloned_external_file,
                                                external_temp.name)
                                else:
                                    try:
                                        print(_("Downloading file from: {URL} ...").format(
                                            URL=external))
                                        external_response = requests.get(
                                            external, allow_redirects=True)
                                        external_temp.write(
                                            external_response.text.encode('utf8'))
                                    except requests.exceptions.RequestException as ex:
                                        git_repo.git.checkout(pathToFinalList)
                                        shutil.rmtree(tempDir)
                                        raise SystemExit(ex) from ex
                                section = external_temp.name
                        if EXTERNAL_PAT.search(external2) and external2:
                            with NamedTemporaryFile(dir=tempDir, delete=False) as external_temp2:
                                # We assume that the directory containing other cloned repository is higher than
                                # the directory of our own list
                                if cloned_external2 is not None and os.path.exists(pj(main_path, "..", cloned_external2)):
                                    cloned_external_file = pj(
                                        main_path, "..", cloned_external2)
                                    shutil.copy(cloned_external_file,
                                                external_temp2.name)
                                else:
                                    try:
                                        print(_("Downloading file from: {URL} ...").format(
                                            URL=external2))
                                        external_response = requests.get(
                                            external2, allow_redirects=True)
                                        external_temp2.write(
                                            external_response.text.encode('utf8'))
                                    except requests.exceptions.RequestException as ex:
                                        git_repo.git.checkout(pathToFinalList)
                                        shutil.rmtree(tempDir)
                                        raise SystemExit(ex) from ex
                                section2 = external_temp2.name

                        if section2:
                            with open(section, "r", encoding='utf-8') as section_content, open(section2, "r", encoding='utf-8') as section2_content, NamedTemporaryFile(dir=tempDir, delete=False) as combined_temp:
                                for lineS1 in section_content:
                                    if lineS1.strip():
                                        combined_temp.write(lineS1.encode())
                                for lineS2 in section2_content:
                                    if lineS2.strip():
                                        combined_temp.write(lineS2.encode())
                            if FOP is not None:
                                FOP.fopsort(combined_temp.name)
                            with open(combined_temp.name, "r", encoding='utf-8') as combined_content, NamedTemporaryFile(dir=tempDir, delete=False) as external_temp:
                                for lineCC in natsorted(set(combined_content), alg=ns.GROUPLETTERS, key=special_chars_first):
                                    if lineCC.strip():
                                        external_temp.write(lineCC.encode())
                            section = external_temp.name

                        # Remove lines matching exclusions file
                        if exclusions:
                            with open(exclusions_path, "r", encoding='utf-8') as exclusions_content, open(section, "r", encoding='utf-8') as section_content, NamedTemporaryFile(dir=tempDir, delete=False) as external_temp:
                                regex_exclusions = []
                                normal_exclusions = []
                                EXCLUSIONS_RE_PAT = re.compile(r"^\/.*\/$")
                                for lineE in exclusions_content:
                                    if lineE := lineE.strip():
                                        if EXCLUSIONS_RE_PAT.search(lineE):
                                            lineE = lineE.lstrip(
                                                "/").rstrip("/")
                                            regex_exclusions.append(lineE)
                                        else:
                                            normal_exclusions.append(lineE)
                                for lineS in section_content:
                                    if regex_exclusions:
                                        for regex_e in regex_exclusions:
                                            if re.search(regex_e, lineS.strip()):
                                                lineS = ""
                                    if normal_exclusions:
                                        for normal_e in normal_exclusions:
                                            if lineS.strip() == normal_e:
                                                lineS = ""
                                    external_temp.write(lineS.encode())
                            section = external_temp.name

                        if EXTERNAL_PAT.search(external) or EXTERNAL_PAT.search(external2):
                            if instruction == "include":
                                with open(external_temp.name, "r", encoding='utf-8') as external_temp, NamedTemporaryFile(dir=tempDir, delete=False) as external_temp_final:
                                    for i, lineET in enumerate(external_temp):
                                        if USELESS_PAT.search(lineET):
                                            lineET = lineET.replace(lineET, "")
                                        lineET = re.sub(
                                            r"^"+"!($|\s)", "!@ ", lineET)
                                        if i == 0:
                                            commentSourceStart = "!@ >>>>>>>> "+external
                                            if argLen >= 2:
                                                if external2:
                                                    commentSourceStart += " + "+external2
                                                if exclusions:
                                                    commentSourceStart += " - "+exclusions
                                            commentSourceStart += "\n"
                                            lineET = re.sub(
                                                r"^", commentSourceStart, lineET)
                                        external_temp_final.write(
                                            lineET.encode())
                                    commentSourceEnd = "!@ <<<<<<<< "+external
                                    if argLen >= 2:
                                        if external2:
                                            commentSourceEnd += " + "+external2
                                        if exclusions:
                                            commentSourceEnd += " - "+exclusions
                                    commentSourceEnd += "\n"
                                    external_temp_final.write(
                                        str(commentSourceEnd).encode())
                                os.replace(external_temp_final.name,
                                           external_temp.name)
                            section = external_temp.name

                        if re.match(r"(HOSTS|DOMAINS|PH|B?NWL)include", instruction):
                            with open(section, "r", encoding='utf-8') as section_content, NamedTemporaryFile(dir=tempDir, delete=False) as external_temp_final:
                                unsortedLinesC = []
                                for lineC in section_content:
                                    lineCwww = ""
                                    convertItems = ""
                                    if instruction in ("HOSTSinclude", "DOMAINSinclude"):
                                        if not re.match(r"^(0\.0\.0\.0.*|\|\|.*\^(\$all)?$)", lineC) or re.match(r"\*|\/", lineC):
                                            lineC = ""
                                        else:
                                            convertItems = [
                                                (r"\$all$", ""),
                                                (r"[\^]", ""),
                                                (r".*\*(.*)?", "")
                                            ]
                                            if instruction == "DOMAINSinclude":
                                                convertItems.append(
                                                    [r"^[|][|]", ""])
                                            if instruction == "HOSTSinclude":
                                                convertItems.extend([
                                                    (r"^[|][|]", "0.0.0.0 "),
                                                    (r"^0\.0\.0\.0 [0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]", "")
                                                ])
                                    elif instruction == "PHinclude":
                                        if not re.search(r"^\|\|.*\*.*\^(\$all)?$", lineC):
                                            lineC = ""
                                        else:
                                            convertItems = [
                                                (r"[\^]\$all$", "$"),
                                                (r"[|][|]", ""),
                                                (r"[\^]$", "$"),
                                                (r"^[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]", ""),
                                                (r"^0\.0\.0\.0", ""),
                                                (r"\.", "\\."),
                                                (r"^", "(^\|\\.)"),
                                                (r"\*", ".*")
                                            ]
                                    elif instruction == "NWLinclude":
                                        if not re.search(r"^\|\|.*\^$", lineC):
                                            lineC = ""
                                        else:
                                            convertItems = [
                                                (r"[|][|]", "@@"),
                                                (r"[\^]", ""),
                                            ]
                                    elif instruction == "BNWLinclude":
                                        if not re.search(r"^|\|\|.*\^(\$all)?$", lineC):
                                            lineC = ""
                                        else:
                                            convertItems = [
                                                (r"\$all$", "$all,badfilter"),
                                                (r"[\^]$", "^$badfilter"),
                                            ]
                                    for old, new in convertItems:
                                        lineC = re.sub(old, new, lineC)
                                    lineC = re.sub(
                                        r'(?m)^[ \t]*$\n?', '', lineC)
                                    if lineC:
                                        if instruction == "HOSTSinclude":
                                            if not re.match(r"^0\.0\.0\.0 (www\.|www[0-9]\.|www\-|pl\.|pl[0-9]\.)", lineC):
                                                lineCwww = lineC.replace(
                                                    "0.0.0.0 ", "0.0.0.0 www.")
                                        if instruction == "DOMAINSinclude":
                                            if not re.match(r"^(www\.|www[0-9]\.|www\-|pl\.|pl[0-9]\.|[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9]\.[0-9]?[0-9]?[0-9])", lineC):
                                                lineCwww = "www." + lineC
                                        if lineCwww:
                                            unsortedLinesC.append(lineCwww)
                                        unsortedLinesC.append(lineC)
                                cType = instruction.replace(
                                    "include", "").lower()
                                if instruction == "PHinclude":
                                    cType = "Pi-hole RegEx"
                                for i, sortedLineC in enumerate(natsorted(set(unsortedLinesC), alg=ns.GROUPLETTERS, key=special_chars_first)):
                                    if i == 0:
                                        commentSourceStart = "#@ >>>>>>>> "+external
                                        if external2:
                                            commentSourceStart += " + "+external2
                                        if exclusions:
                                            commentSourceStart += " - "+exclusions
                                        commentSourceStart += " =>"+cType+"\n"
                                        sortedLineC = re.sub(
                                            r"^", commentSourceStart, sortedLineC)
                                    external_temp_final.write(
                                        sortedLineC.encode())
                                section = None
                                if unsortedLinesC:
                                    commentSourceEnd = "#@ <<<<<<<< "+external
                                    if external2:
                                        commentSourceEnd += " + "+external2
                                    if exclusions:
                                        commentSourceEnd += " - "+exclusions
                                    commentSourceEnd += " =>"+cType+"\n"
                                    external_temp_final.write(
                                        str(commentSourceEnd).encode())
                                    section = external_temp_final.name

                        if section is not None:
                            with open(section, "r", encoding='utf-8') as section_content:
                                lineF = lineF.replace(
                                    lineF, section_content.read())

                # Remove useless instructions and write all processed lines to final file
                if not USELESS_I_PAT.match(lineF):
                    final_tmp.write(lineF.encode())
        os.replace(final_tmp.name, pathToFinalList)

        # Set timezone
        if hasattr(conf(), 'tz'):
            os.environ['TZ'] = conf().tz
            time.tzset()

        # Set a code name (shorter filerlist name) to description of commit, depending on what
        # is typed in the "Codename:" field. If there is no such field, then codename=filename.
        with open(pathToFinalList, "r", encoding='utf-8') as f_final:
            CODENAME_PAT = re.compile(r"\! Codename\:")
            codename = FILTERLIST
            for lineF in f_final:
                if CODENAME_PAT.match(lineF):
                    codename = lineF.strip().replace("! Codename: ", "")

        # Check if update is really necessary
        oldFL = []
        COMMENT_PAT = re.compile(r"^(\!|#) ")
        with open(BACKUP_PATH, "r", encoding='utf-8') as f_backup:
            for oldLine in f_backup:
                if not COMMENT_PAT.match(oldLine):
                    oldFL.append(oldLine)
        newFL = []
        with open(pathToFinalList, "r", encoding='utf-8') as f_final:
            for newLine in f_final:
                if not COMMENT_PAT.match(newLine):
                    newFL.append(newLine)

        if "FORCED" in os.environ:
            forced = "true"
        if oldFL != newFL or forced:
            with open(pathToFinalList, "r", encoding='utf-8') as f_final, NamedTemporaryFile(dir=tempDir, delete=False) as final_tmp:
                today = datetime.now().astimezone()
                DEV_PAT = re.compile(r"\! Title\:.*DEV")
                MODIFIED_PAT = re.compile(r"@modified")
                LOCALIZED_DT_PAT = re.compile(r"@localizedDT")
                VERSION_PAT = re.compile(r"@version")

                # Determine version number
                if hasattr(conf(), 'versionFormat'):
                    versionFormat = conf().versionFormat
                    if versionFormat == "Year.Month.NumberOfCommitsInMonth":
                        lastDayOfMonth = (today.replace(
                            day=1) - timedelta(days=1)).strftime("%Y-%m-%d 23:59")
                        version = f"{today.year}.{today.month}." + git_repo.git.rev_list(
                            "HEAD", "--date=local", "--count", "--after", lastDayOfMonth, pathToFinalList)
                    elif versionFormat == "Year.Month.Day.TodayNumberOfCommits":
                        tomorrow = (today + timedelta(days=1)
                                    ).strftime("%Y-%m-%d 24:00")
                        yesterday = (today - timedelta(days=1)
                                     ).strftime("%Y-%m-%d 23:59")
                        version = f"{today.year}.{today.month}.{today.day}." + git_repo.git.rev_list(
                            "HEAD", "--date=local", "--count", "--before", tomorrow, "--after", yesterday, pathToFinalList)
                    else:
                        version = today.strftime(conf().versionFormat)
                else:
                    version = today.strftime("%Y%m%d%H%M")

                for lineF in f_final:
                    # Remove DEV from filter list name if RTM mode is active
                    if "RTM" in os.environ and DEV_PAT.search(lineF):
                        lineF = lineF.replace("DEV", "")

                    # Set date and time in "Last modified" field
                    if MODIFIED_PAT.search(lineF):
                        locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
                        tzOffset = today.strftime("%z")
                        dateFormat = "%a, %d %b %Y, %H:%M UTC" + \
                            f"{tzOffset[:-2]}:{tzOffset[-2:]}"
                        if hasattr(conf(), 'dateFormat'):
                            dateFormat = conf().dateFormat
                        modified = today.strftime(dateFormat)
                        lineF = lineF.replace("@modified", modified)

                    # Set version
                    if VERSION_PAT.search(lineF):
                        if "version" in locals():
                            lineF = lineF.replace("@version", version)

                    # Set localized date and time
                    if LOCALIZED_DT_PAT.search(lineF) and hasattr(conf(), 'timeLang'):
                        locale.setlocale(
                            locale.LC_TIME, conf().timeLang+".UTF-8")
                        tzOffset = today.strftime("%z")
                        dateFormat = "%a, %d %b %Y, %H:%M UTC" + \
                            f"{tzOffset[:-2]}:{tzOffset[-2:]}"
                        if hasattr(conf(), 'dateFormat'):
                            dateFormat = conf().dateFormat
                        localizedDT = today.strftime(dateFormat)
                        lineF = lineF.replace("@localizedDT", localizedDT)
                    final_tmp.write(lineF.encode())
            os.replace(final_tmp.name, pathToFinalList)

            # Add modified files to git repository
            git_repo.index.add(pathToFinalList)

            # Save names of modified files
            if saveChangedFN:
                if not os.path.exists(pj(main_path, "changed_files")):
                    os.mkdir(pj(main_path, "changed_files"))
                SFLB_CHANGED_FILES_PATH = pj(
                    main_path, "changed_files", "SFLB_CHANGED_FILES.txt")
                if not os.path.exists(SFLB_CHANGED_FILES_PATH):
                    with open(SFLB_CHANGED_FILES_PATH, mode='a', encoding='utf-8'):
                        pass
                modifiedFiles = []
                with open(SFLB_CHANGED_FILES_PATH, "r", encoding='utf-8') as changed_f_f, NamedTemporaryFile(dir=main_path, delete=False) as changed_files_temp:
                    for line in changed_f_f:
                        if line:
                            modifiedFiles.append(line)
                    modifiedFiles.append(os.path.relpath(
                        pathToFinalList, start=main_path))
                    changed_files_temp.write(
                        str('\n'.join(sorted(set(modifiedFiles)))).encode())
                os.replace(changed_files_temp.name, SFLB_CHANGED_FILES_PATH)

            # Commit modified files
            commit_message = _("Update {codename} to version {versionNumber}").format(
                codename=codename, versionNumber=version)
            if "CI" in os.environ:
                if hasattr(conf(), 'commitDesc'):
                    commit_message += "\n"+conf().commitDesc
            else:
                commit_description = input(
                    _("Enter extended commit description to {codename} list, e.g 'Fix #1, fix #2' (without quotation marks; if you do not want an extended description, you can simply enter nothing): ").format(codename=codename))
                if commit_description:
                    commit_message += "\n"+commit_description
            git_repo.index.commit(commit_message)

        else:
            print(_("Nothing new has been added to {codename} list. If you still want to update it, then set the variable FORCED and run script again.").format(
                codename=codename))
            git_repo.git.checkout(pathToFinalList)

        # Remove all temporary files
        os.remove(BACKUP_PATH)
        shutil.rmtree(tempDir)


def push(pathToFinalLists):
    _ = getTranslations()
    conf = getValuesFromConf(pathToFinalLists)

    # Send changed files to git repository
    git_repo = getGitRepo(pathToFinalLists)
    if "git_repo" in locals():
        commited = git_repo.git.cherry("-v")
        if commited and "NO_PUSH" not in os.environ:
            if "CI" in os.environ:
                GIT_SLUG = git_repo.remotes.origin.url.replace(
                    'https://', "").replace("git@", "").replace(":", "/")
                if hasattr(conf(), 'CIusername') and "GIT_TOKEN" in os.environ:
                    git_repo.git.push("https://"+conf().CIusername +
                                      ":"+os.environ["GIT_TOKEN"]+"@"+GIT_SLUG)
            else:
                print(_("Do you want to send changed files to git now?"))
                options = [_("Yes"), _("No")]
                for idx, option in enumerate(options, 1):
                    print(f"{idx}) {option}")
                choice = input(_('Enter your choice: '))
                option = options[int(choice) - 1]
                if option == _("Yes"):
                    git_repo.git.push()


if __name__ == '__main__':
    main(args.pathToFinalList, "", "true")
    doItAgainIfNeed(args.pathToFinalList)
    push(args.pathToFinalList)
