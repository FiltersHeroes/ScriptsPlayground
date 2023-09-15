#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-function-docstring
# Subdomain to Domain

"""MIT License

Copyright (c) 2023 Filters Heroes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import os
from pathlib import Path
import tldextract


def main(subdomains):
    domains = []
    home = str(Path.home())
    cachePath = os.path.join(home, '.cache')

    if not os.path.exists(cachePath):
        os.mkdir(cachePath)

    extract = tldextract.TLDExtract(include_psl_private_domains=True)

    for line in subdomains:
        if extract(line).registered_domain != "":
            domains.append(extract(line).registered_domain)
        else:
            domains.append(line.strip())
    return domains
