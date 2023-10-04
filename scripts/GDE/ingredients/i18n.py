#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=missing-function-docstring
import sys
import os
import gettext
import builtins
import locale


def i18n(msgid):
    localedir = os.path.join(sys.path[0], 'locales')
    translate = gettext.translation('GDE', localedir, fallback=True)
    return translate.gettext(msgid)


def set_locale_for_windows():
    if sys.platform == "win32" and os.getenv('LANG') is None:
        lang, enc = locale.getlocale()
        os.environ['LANG'] = lang


def install():
    set_locale_for_windows()
    builtins.translateGDE = i18n
