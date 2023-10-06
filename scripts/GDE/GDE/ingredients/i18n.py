#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=missing-function-docstring
import sys
import os
import gettext
import builtins


def i18n(msgid):
    localedir = os.path.join(sys.path[0], 'locales')
    translate = gettext.translation('GDE', localedir, fallback=True)
    return translate.gettext(msgid)


def set_locale_for_windows():
    if sys.platform == "win32" and os.getenv("LANG") is None:
        import ctypes
        import locale
        windll = ctypes.windll.kernel32
        lang = locale.windows_locale[windll.GetUserDefaultUILanguage()]
        os.environ['LANG'] = os.environ['LANGUAGE'] = lang


def install():
    set_locale_for_windows()
    builtins.translateGDE = i18n
