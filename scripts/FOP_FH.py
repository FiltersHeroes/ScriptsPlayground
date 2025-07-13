#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
""" FOP_FH
    Filter Orderer and Preener (tweaked by Filters Heroes Team)
    Copyright (C) 2011 Michael

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>."""
# Import the key modules
import re
import os
import sys
import filecmp
import argparse

# FOP version number
VERSION = 3.32

# Welcome message
greeting = f"FOP (Filter Orderer and Preener) {VERSION}"

ap = argparse.ArgumentParser()
ap.add_argument('--dir', '-d', nargs='+', help='Set directories', default=None)
ap.add_argument('--ignore', '-i', nargs='+', help='List the files that should not be sorted, either because they have a special sorting system or because they are not filter files', default=("output", "requirements.txt", "templates", "node_modules"))
ap.add_argument("--version", "-v",
                action='store_true', help="Show script's version number and exit")

args = []

# Compile regular expressions to match important filter parts
# (derived from Wladimir Palant's Adblock Plus source code)
ELEMENTDOMAINPATTERN = re.compile(r"^([^\/\*\|\@\"\!]*?)(#|\$)\@?\??\@?(#|\$)")
FILTERDOMAINPATTERN = re.compile(r"(?:\$|\,)(?:denyallow|domain|from|method|to)\=([^\,\s]+)$")
ELEMENTPATTERN = re.compile(
    r"^([^\/\*\|\@\"\!]*?)(\$\@?\$|##\@?\$|#[\@\?]?#\+?)(.*)$")
OPTIONPATTERN = re.compile(
    r"^(.*)\$(~?[\w\-]+(?:=[^,\s]+)?(?:,~?[\w\-]+(?:=[^,\s]+)?)*)$")

# Compile regular expressions that match element tags and
# pseudo classes and strings and tree selectors;
# "@" indicates either the beginning or the end of a selector
SELECTORPATTERN = re.compile(
    r"(?<=[\s\[@])([a-zA-Z]*[A-Z][a-zA-Z0-9]*)((?=([\[\]\^\*\$=:@#\.]))|(?=(\s(?:[+>~]|\*|[a-zA-Z][a-zA-Z0-9]*[\[:@\s#\.]|[#\.][a-zA-Z][a-zA-Z0-9]*))))")
PSEUDOPATTERN = re.compile(
    r"(\:[:][a-zA-Z\-]*[A-Z][a-zA-Z\-]*)(?=([\(\:\@\s]))")
REMOVALPATTERN = re.compile(
    r"((?<=([>+~,]\s))|(?<=(@|\s|,)))()(?=(?:[#\.\[]|\:(?!-abp-)))")
ATTRIBUTEVALUEPATTERN = re.compile(
    r"^([^\'\"\\]|\\.)*(\"(?:[^\"\\]|\\.)*\"|\'(?:[^\'\\]|\\.)*\')|\*")
TREESELECTOR = re.compile(r"(\\.|[^\+\>\~\\\ \t])\s*([\+\>\~\ \t])\s*(\D)")
UNICODESELECTOR = re.compile(r"\\[0-9a-fA-F]{1,6}\s[a-zA-Z]*[A-Z]")

# Compile a regular expression that describes a completely blank line
BLANKPATTERN = re.compile(r"^\s*$")

# Compile a regular expression that describes uBO's scriptlets pattern
UBO_JS_PATTERN = re.compile(r"^@js\(")

# List all Adblock Plus, uBlock Origin and AdGuard options
# (excepting domain, denyallow, from, method, permissions, redirect, redirect-rule, rewrite and to, which is handled separately)
KNOWNOPTIONS = (
    "document", "elemhide", "font", "genericblock", "generichide", "image", "match-case", "media", "object", "other", "ping", 
    "popup", "script", "stylesheet", "subdocument", "third-party", "webrtc", "websocket", "xmlhttprequest",

    # uBlock Origin
    "_", "1p", "3p", "all", "badfilter", "cname", "csp", "css", "doc", "ehide", "empty", "first-party", "frame",
    "ghide", "header", "important", "inline-font", "inline-script", "ipaddress", "match-case", "mp4", "object-subrequest",
    "popunder", "shide", "specifichide", "xhr", "strict1p", "strict3p", "uritransform", "urlskip"

    # AdGuard
    "app", "content", "cookie", "extension", "jsinject", "network", "replace", "stealth", "urlblock", "removeparam"
)

# List all methods which should be used together with uBO's method option
KNOWN_METHODS = ("connect", "delete", "get", "head", "options", "patch", "post", "put")

# Compile regex with all valid redirect resources
# (https://help.adblockplus.org/hc/en-us/articles/360062733293-How-to-write-filters,
# https://github.com/gorhill/uBlock/wiki/Resources-Library#available-empty-redirect-resources,
# https://github.com/gorhill/uBlock/wiki/Resources-Library#available-url-specific-sanitized-redirect-resources-surrogates
# and aliases from https://github.com/gorhill/uBlock/blob/master/src/js/redirect-resources.js)
KNOWN_REDIRECT_RESOURCES = re.compile(r"""
    (
    (abp-resource:)?1x1(-transparent)?(\.|-)gif|(2x2|3x2|32x32)(-transparent)?(\.|-)png|
    abp-resource:blank-(css|html|js|text|mp3|mp4)|
    empty|noopframe|noopjs|nooptext|
    noop\.(css|html|js|txt)|
    noop-(0\.1|0\.5)s\.mp3|noopmp3-0.1s|
    noop-1s\.mp4|noopmp4-1s|
    none|click2load\.html|
    (addthis_widget|addthis\.com\/addthis_widget|amazon_ads|amazon-adsystem\.com\/aax2\/amzn_ads|amazon_apstag|
    ampproject_v0|ampproject\.org\/v0|
    doubleclick_instream_ad_status|doubleclick\.net\/instream\/ad_status|
    fingerprint(2|3)|
    google-analytics_analytics|google-analytics\.com\/analytics|googletagmanager_gtm|googletagmanager\.com\/gtm|
    google-analytics_cx_api|google-analytics\.com\/cx\/api|
    google-analytics_ga|google-analytics\.com\/ga|
    google-analytics_inpage_linkid|google-analytics\.com\/inpage_linkid|
    google-ima|google-ima3|
    googlesyndication_adsbygoogle|googlesyndication\.com\/adsbygoogle|googlesyndication-adsbygoogle|
    googletagservices_gpt|googletagservices\.com\/gpt|googletagservices-gpt|
    hd-main|mxpnl_mixpanel|monkeybroker|d3pkae9owd2lcf\.cloudfront\.net\/mb105|
    nobab(2)?|bab-defuser|prevent-bab|
    noeval|noeval-silent|silent-noeval|nofab|fuckadblock\.js-3\.2\.0|
    outbrain-widget|widgets\.outbrain.com\/outbrain|
    popads|popads\.net|prevent-popads-net|popads-dummy|prebid-ads|
    scorecardresearch_beacon|scorecardresearch\.com\/beacon)(\.js)?
    )(:\d+)?$
""", re.X)


def start():
    """ Print a greeting message and run FOP in the directories
    specified via the command line, or the current working directory if
    no arguments have been passed."""
    if args.version:
        print(greeting)
        sys.exit(0)
    characters = len(str(greeting))
    print("=" * characters)
    print(greeting)
    print("=" * characters)

    # Convert the directory names to absolute references and visit each unique location
    places = args.dir
    if places:
        places = [os.path.abspath(place) for place in places]
        for place in sorted(set(places)):
            main(place)
            print()
    else:
        main(os.getcwd())


def main(location):
    """ Find and sort all the files in a given directory."""
    # Check that the directory exists, otherwise return
    if not os.path.isdir(location):
        print(f"{location} does not exist or is not a folder.")
        return

    # Work through the directory and any subdirectories, ignoring hidden directories
    print(f'\nPrimary location: {os.path.join(os.path.abspath(location), "")}')
    for path, directories, files in os.walk(location):
        for direct in directories[:]:
            if direct.startswith(".") or direct in args.ignore:
                directories.remove(direct)
        print(f'Current directory: {os.path.join(os.path.abspath(path), "")}')
        directories.sort()
        for filename in sorted(files):
            address = os.path.join(path, filename)
            extension = os.path.splitext(filename)[1]
            # Sort all text files that are not blacklisted
            if extension == ".txt" and filename not in args.ignore:
                fopsort(address)
            # Delete unnecessary backups and temporary files
            if extension in (".orig", ".temp"):
                try:
                    os.remove(address)
                except(IOError, OSError):
                    # Ignore errors resulting from deleting files, as they likely indicate that the file has already been deleted
                    pass


def fopsort(filename):
    """ Sort the sections of the file and save any modifications."""
    temporaryfile = f"{filename}.temp"
    CHECKLINES = 10
    section = []
    lineschecked = 1
    filterlines = elementlines = 0

    # Read in the input and output files concurrently to allow filters to be saved as soon as they are finished with
    with open(filename, "r", encoding="utf-8", newline="\n") as inputfile, open(temporaryfile, "w", encoding="utf-8", newline="\n") as outputfile:

        # Combines domains for (further) identical rules
        def combinefilters(uncombinedFilters, DOMAINPATTERN, domainseparator):
            combinedFilters = []
            for i, uncombinedFilter in enumerate(uncombinedFilters):
                domains1 = re.search(DOMAINPATTERN, uncombinedFilter)
                if i+1 < len(uncombinedFilters) and domains1:
                    domains2 = re.search(DOMAINPATTERN, uncombinedFilters[i+1])
                    domain1str = domains1.group(1)

                if not domains1 or i+1 == len(uncombinedFilters) or not domains2 or len(domain1str) == 0 or len(domains2.group(1)) == 0:
                    # last filter or filter didn't match regex or no domains
                    combinedFilters.append(uncombinedFilter)
                else:
                    domain2str = domains2.group(1)
                    if domains1.group(0).replace(domain1str, domain2str, 1) != domains2.group(0):
                        # non-identical filters shouldn't be combined
                        combinedFilters.append(uncombinedFilter)
                    elif re.sub(DOMAINPATTERN, "", uncombinedFilter) == re.sub(DOMAINPATTERN, "", uncombinedFilters[i+1]):
                        # identical filters. Try to combine them...
                        newDomains = f"{domain1str}{domainseparator}{domain2str}"
                        newDomains = domainseparator.join(sorted(
                            set(newDomains.split(domainseparator)), key=lambda domain: domain.strip("~")))
                        if (domain1str.count("~") != domain1str.count(domainseparator) + 1) != (domain2str.count("~") != domain2str.count(domainseparator) + 1):
                            # do not combine rules containing included domains with rules containing only excluded domains
                            combinedFilters.append(uncombinedFilter)
                        else:
                            # either both contain one or more included domains, or both contain only excluded domains
                            domainssubstitute = domains1.group(
                                0).replace(domain1str, newDomains, 1)
                            uncombinedFilters[i+1] = re.sub(
                                DOMAINPATTERN, domainssubstitute, uncombinedFilter)
                    else:
                        # non-identical filters shouldn't be combined
                        combinedFilters.append(uncombinedFilter)
            return combinedFilters

        # Writes the filter lines to the file
        def writefilters():
            newLineSign = '\n'
            if elementlines > filterlines:
                uncombinedFilters = sorted(
                    set(section), key=lambda rule: re.sub(ELEMENTDOMAINPATTERN, "", rule))
                outputfile.write(f"{newLineSign.join(combinefilters(uncombinedFilters, ELEMENTDOMAINPATTERN, ","))}\n")
            else:
                uncombinedFilters = sorted(set(section), key=str.lower)
                outputfile.write(f"{newLineSign.join(combinefilters(uncombinedFilters, FILTERDOMAINPATTERN, "|"))}\n")

        for line in inputfile:
            line = line.strip()
            if not re.match(BLANKPATTERN, line):
                # Include comments verbatim and, if applicable, sort the preceding section of filters and save them in the new version of the file
                if line[0] == "!" or line[:8] == "%include" or line[0] == "[" and line[-1] == "]":
                    if section:
                        writefilters()
                        section = []
                        lineschecked = 1
                        filterlines = elementlines = 0
                    outputfile.write(f"{line}\n")
                else:
                    # Neaten up filters and, if necessary, check their type for the sorting algorithm
                    elementparts = re.match(ELEMENTPATTERN, line)
                    if elementparts:
                        domains = elementparts.group(1).lower()
                        if lineschecked <= CHECKLINES:
                            elementlines += 1
                            lineschecked += 1
                        line = elementtidy(domains, elementparts.group(
                            2), elementparts.group(3))
                    else:
                        if lineschecked <= CHECKLINES:
                            filterlines += 1
                            lineschecked += 1
                        line = filtertidy(line, filename)
                    # Add the filter to the section
                    section.append(line)
        # At the end of the file, sort and save any remaining filters
        if section:
            writefilters()

    # Replace the existing file with the new one only if alterations have been made
    if not filecmp.cmp(temporaryfile, filename):
        os.replace(temporaryfile, filename)
        print(f"Sorted: {os.path.abspath(filename)}")
    else:
        os.remove(temporaryfile)


def filtertidy(filterin, filename):
    """ Sort the options of blocking filters and make the filter text
    lower case if applicable."""
    optionsplit = re.match(OPTIONPATTERN, filterin)

    if not optionsplit:
        # Remove unnecessary asterisks from filters without any options and return them
        return removeunnecessarywildcards(filterin)

    # If applicable, separate and sort the filter options in addition to the filter text
    filtertext = removeunnecessarywildcards(optionsplit.group(1))
    optionlist = optionsplit.group(2).lower().split(",")

    domainlist = []
    denyallowlist = []
    fromlist = []
    methodlist = []
    permissionslist = []
    tolist = []
    removeentries = []
    for option in optionlist:
        optionName = option.split("=", 1)[0].strip("~")
        optionLength = len(optionName) + 1
        # Detect and separate domain options
        argList = []
        if optionName in ("domain", "denyallow", "from", "method", "to", "permissions"):
            if optionName == "domain":
                argList = domainlist
            elif optionName == "from":
                argList = fromlist
            elif optionName == "to":
                argList = tolist
            elif optionName == "denyallow":
                argList = denyallowlist
                if "domain=" not in filterin and "from=" not in filterin:
                    print(f"\nWarning: The option \"denyallow\" used on the filter \"{filterin}\" requires the \"domain\" option [{filename}].")
            elif optionName == "method":
                argList = methodlist
                methods = option[optionLength:].split("|")
                for method in methods:
                    if method and method not in KNOWN_METHODS:
                        print(f"\nWarning: The method \"{method}\" used on the filter \"{filterin}\" is not recognised by FOP [{filename}].")
            elif optionName == "permissions":
                argList = permissionslist
            argList.extend(option[optionLength:].split("|"))
            removeentries.append(option)
        elif optionName in ("redirect", "redirect-rule", "rewrite"):
            redirectResource = option[optionLength:]
            if redirectResource and not re.match(KNOWN_REDIRECT_RESOURCES, redirectResource):
                print(f"\nWarning: Redirect resource \"{redirectResource}\" used on the filter \"{filterin}\" is not recognised by FOP [{filename}].")
        elif optionName not in KNOWNOPTIONS:
            print(
                f"\nWarning: The option \"{option}\" used on the filter \"{filterin}\" is not recognised by FOP [{filename}].")
    # Sort all options other than domain, from, to, denyallow, method and permissions alphabetically
    # For identical options, the inverse always follows the non-inverse option ($image,~image instead of $~image,image)
    optionlist = sorted(set(filter(lambda option: option not in removeentries, optionlist)),
                        key=lambda option: (option[1:] + "~") if option[0] == "~" else option)
    # If applicable, sort domain restrictions and append them to the list of options
    if domainlist:
        optionlist.append(f'domain={"|".join(sorted(set(filter(lambda domain: domain != "", domainlist)), key=lambda domain: domain.strip("~")))}')
    if denyallowlist:
        optionlist.append(f'denyallow={"|".join(sorted(set(filter(lambda domain: domain != "", denyallowlist)), key=lambda domain: domain.strip("~")))}')
    if fromlist:
        optionlist.append(f'from={"|".join(sorted(set(filter(lambda domain: domain != "", fromlist)), key=lambda domain: domain.strip("~")))}')
    if tolist:
        optionlist.append(f'to={"|".join(sorted(set(filter(lambda domain: domain != "", tolist)), key=lambda domain: domain.strip("~")))}')
    if methodlist:
        optionlist.append(f'method={"|".join(sorted(set(filter(lambda domain: domain != "", methodlist)), key=lambda domain: domain.strip("~")))}')
    if permissionslist:
        optionlist.append(f'permissions={"|".join(sorted(set(filter(lambda domain: domain != "", permissionslist)), key=lambda domain: domain.strip("~")))}')

    # Return the full filter
    return f'{filtertext}${",".join(optionlist)}'


def elementtidy(domains, separator, selector):
    """ Sort the domains of element hiding rules, remove unnecessary
    tags and make the relevant sections of the rule lower case."""
    # Order domain names alphabetically, ignoring exceptions
    if "," in domains:
        domains = ",".join(sorted(set(domains.split(",")),
                           key=lambda domain: domain.strip("~")))
    # Mark the beginning and end of the selector with "@"
    selector = f"@{selector}@"
    each = re.finditer
    # Make sure we don't match items in strings (e.g., don't touch Width in ##[style="height:1px; Width: 123px;"])
    selectorwithoutstrings = selector
    selectoronlystrings = ""
    while True:
        stringmatch = re.match(ATTRIBUTEVALUEPATTERN, selectorwithoutstrings)
        if stringmatch is None:
            break
        selectorwithoutstrings = selectorwithoutstrings.replace(
            f"{stringmatch.group(1)}{stringmatch.group(2)}", f"{stringmatch.group(1)}", 1)
        selectoronlystrings = f"{selectoronlystrings}{stringmatch.group(2)}"
    # Clean up tree selectors
    for tree in each(TREESELECTOR, selector):
        if tree.group(0) in selectoronlystrings or not tree.group(0) in selectorwithoutstrings:
            continue
        if tree.group(1) == "(":
            replaceby = f"{tree.group(2)} "
        else:
            replaceby = f" {tree.group(2)} "
        if replaceby == "   ":
            replaceby = " "
        # Make sure we don't match arguments of uBO scriptlets
        if not UBO_JS_PATTERN.match(selector):
            selector = selector.replace(tree.group(
                0), f"{tree.group(1)}{replaceby}{tree.group(3)}", 1)
    # Remove unnecessary tags
    for untag in each(REMOVALPATTERN, selector):
        untagname = untag.group(4)
        if untagname in selectoronlystrings or not untagname in selectorwithoutstrings:
            continue
        bc = untag.group(2)
        if bc is None:
            bc = untag.group(3)
        ac = untag.group(5)
        selector = selector.replace(f"{bc}{untagname}{ac}", f"{bc}{ac}", 1)
    # Make pseudo classes lower case where possible
    for pseudo in each(PSEUDOPATTERN, selector):
        pseudoclass = pseudo.group(1)
        if pseudoclass in selectoronlystrings or not pseudoclass in selectorwithoutstrings:
            continue
        ac = pseudo.group(3)
        selector = selector.replace(
            f"{pseudoclass}{ac}", f"{pseudoclass}{ac}", 1)
    # Remove the markers from the beginning and end of the selector and return the complete rule
    return f"{domains}{separator}{selector[1:-1]}"


def removeunnecessarywildcards(filtertext):
    # Where possible, remove unnecessary wildcards from the beginnings and ends of blocking filters.
    allowlist = False
    hadStar = False
    if filtertext[0:2] == "@@":
        allowlist = True
        filtertext = filtertext[2:]
    while len(filtertext) > 1 and filtertext[0] == "" and not filtertext[1] == "|" and not filtertext[1] == "!":
        filtertext = filtertext[1:]
        hadStar = True
    while len(filtertext) > 1 and filtertext[-1] == "" and not filtertext[-2] == "|":
        filtertext = filtertext[:-1]
        hadStar = True
    if hadStar and filtertext[0] == "/" and filtertext[-1] == "/":
        filtertext = f"{filtertext}*"
    if filtertext == "":
        filtertext = ""
    if allowlist:
        filtertext = f"@@{filtertext}"
    return filtertext


if __name__ == '__main__':
    args = ap.parse_args()
    start()
