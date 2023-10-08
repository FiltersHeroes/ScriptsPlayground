#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=missing-function-docstring
import sys
import os
import gettext
import builtins

def i18n(msgid):
    script_path = os.path.dirname(os.path.realpath(__file__))
    localedir = os.path.normpath(os.path.join(script_path, "..", 'locales'))
    translate = gettext.translation('GDE', localedir, fallback=True)
    return translate.gettext(msgid)


def install(_app):
    if sys.platform == "win32":
        import ctypes
        import locale
        windll = ctypes.windll.kernel32
        lang = locale.windows_locale[windll.GetUserDefaultUILanguage()]
        os.environ['LANG'] = os.environ['LANGUAGE'] = lang
        from qtpy.QtCore import QTranslator, QLibraryInfo, QLocale
        translator = QTranslator(_app)
        translator.load('qt_' + lang, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        _app.installTranslator(translator)
    builtins.translateGDE = i18n
