#!/usr/bin/env python3
# coding=utf-8
"""MIT License

Copyright (c) 2019 Polish Filters Team

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

# import libraries
from bs4 import BeautifulSoup
import certifi
import urllib3
import tldextract
import PySimpleGUI as sg
from tkinter import Tk
import configparser
from appdirs import *
import os
import gettext
import sys
import platform

if platform.system() == "Windows":
    import locale
    if os.getenv('LANG') is None:
        lang, enc = locale.getdefaultlocale()
        os.environ['LANG'] = lang

appname = "GroupsDomainsExtractor"
appversion = "1.2.2"

localedir = os.path.join(sys.path[0], 'locales')
translate = gettext.translation('GDE', localedir, fallback=True)
_ = translate.gettext
cfilepath = os.path.join(user_config_dir(), appname, 'groups.ini')

def extractDomains():
    # specify the url
    quote_page = values['URL']

    # query the website and return the html to the variable ‘page’
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )
    page = http.request('GET', quote_page)

    # parse the html using Beautiful Soup and store in variable `soup`
    soup = BeautifulSoup(page.data, "html5lib")

    data = soup.select(values['CSS'])

    final_links = []

    for a in data:
        a['href'] = tldextract.extract(a['href']).registered_domain
        final_links.append(a['href'])

    final_links = sorted(set(final_links))

    if values['SEPARATOR'] == _('comma'):
        separator = ","
    elif values['SEPARATOR'] == _('pipe'):
        separator = "|"

    print(separator.join(final_links))
    r = Tk()
    r.clipboard_append(separator.join(final_links))
    r.update()
    r.destroy()
    if final_links:
        sg.Popup(_("Domains have been copied to the clipboard :-)"), title=_("Done"))
    else:
        sg.Popup(_("Domains not found. Check the entered data and try again!"), title=_("Error"))

def saveGroup():
    config = configparser.ConfigParser()

    if not os.path.exists(os.path.join(user_config_dir(), appname)):
        os.mkdir(os.path.join(user_config_dir(), appname))

    config.read(cfilepath)
    if not values['GROUP_NAME']:
        sg.Popup(_("Not so fast, cowboy, enter group's name!"), title=_("Error"))

    if values['GROUP_NAME']:
        if config.has_section(values['GROUP_NAME']):
            config.remove_section(values['GROUP_NAME'])

        if values['SEPARATOR'] == _('comma'):
            values['SEPARATOR'] = "comma"
        elif values['SEPARATOR'] == _('pipe'):
            values['SEPARATOR'] = "pipe"

        config[values['GROUP_NAME']] = {'url': values['URL'], 'css': values['CSS'], 'separator': values['SEPARATOR']}
        cfile = open(cfilepath, 'w')
        config.write(cfile)
        cfile.close()
        window.FindElement('GROUP').Update(values=([*loadGroupList()]))

        sg.Popup(_("{} group has been saved to file:").format(values['GROUP_NAME'])+" "+cfilepath, title=_("Done"))

def loadGroupList():
    config = configparser.ConfigParser()
    config.read(cfilepath)
    sections = []
    for each_section in config.sections():
        sections.append(each_section)
    if not sections:
        sections = [""]
    return sections

def loadGroup():
    config = configparser.ConfigParser()
    config.read(cfilepath)
    if not values['GROUP']:
        sg.Popup( _("Tell me what to load, cuz unfortunately my glass ball broke."), title=_("Error"))

    if values['GROUP']:
        if config[values['GROUP']]['separator'] == "comma":
            config[values['GROUP']]['separator'] = _('comma')
        if config[values['GROUP']]['separator'] == "pipe":
            config[values['GROUP']]['separator'] = _('pipe')
        window.Element('URL').Update(config[values['GROUP']]['url'])
        window.Element('CSS').Update(config[values['GROUP']]['css'])
        window.Element('SEPARATOR').Update(config[values['GROUP']]['separator'])
        window.Element('GROUP_NAME').Update(values['GROUP'])

def removeGroup():
    config = configparser.ConfigParser()
    config.read(cfilepath)

    if config.has_section(values['GROUP']):
        button_pressed = sg.Popup(_("Are you sure you want to remove configuration of {} group?").format(values['GROUP']), title=_('Confirmation'), custom_text=(_("Yes"), _("No")))
        if button_pressed == _("Yes"):
            config.remove_section(values['GROUP'])
            cfile = open(cfilepath, 'w')
            config.write(cfile)
            cfile.close()
            window.FindElement('GROUP').Update(values=([*loadGroupList()]))

if platform.system() == "Windows":
      sg.change_look_and_feel('Dark2')
      sg.set_options(button_color=('white', '#082567'), background_color="#292f34", text_element_background_color="#292f34", input_text_color="black")
else:
      sg.change_look_and_feel('SystemDefault')

layout = [
          [sg.Text(_('Site address:'), size=(30, 1)), sg.InputText('http://siecportali.pl/realizacje', key='URL')],
          [sg.Text(_('CSS path:'), size=(30, 1)), sg.InputText('.portal-logos a', key="CSS")],
          [sg.Text(_('Separator:'), size=(30, 1)), sg.Combo([_('comma'), _('pipe')], default_value=_('comma'), readonly=True, size=(43,1), key="SEPARATOR")],
          [sg.Text(_("Group’s name:"), size=(30, 1)), sg.InputText('Sieć portali', key="GROUP_NAME")],
          [sg.Text(_("Group’s configuration:"), size=(30, 1)), sg.Combo([*loadGroupList()], readonly=True, key="GROUP", size=(43,1))],
          [sg.Submit(_('Extract domains'), key="EXTRACT"), sg.Submit(_('Load group'), key="LOAD"), sg.Submit(_('Save group'), key="SAVE"), sg.Submit(_('Remove group'), key="REMOVE"), sg.Cancel(_('About GDE'), key="ABOUT"), ]
         ]

window = sg.Window(_('Groups Domains Extractor')).Layout(layout)
while True:
    event, values = window.Read()
    if event == "EXTRACT":
        extractDomains()
    if event == "SAVE":
        saveGroup()
    if event == "LOAD":
        loadGroup()
    if event == "REMOVE":
        removeGroup()
    if event == "ABOUT":
        sg.Popup(_('Groups Domains Extractor')+' '+appversion, _('License:')+' '+'MIT', 'Copyright © 2019 Polish Filters Team', _('Groups Domains Extractor helps in finding all domains of specific group and copies it to clipboard. It also has the ability to save configuration of group to file and load it.'), _('This program uses following modules:')+' '+'beautifulsoup4, certifi, urllib3, tldextract, PySimpleGUI '+_('and')+' appdirs.', title=_('About Groups Domains Extractor'))
    if event is None:
        break
