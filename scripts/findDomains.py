# import libraries
from bs4 import BeautifulSoup
import certifi
import urllib3
import tldextract
import PySimpleGUI as sg
from tkinter import Tk
import configparser
from appdirs import *

appname = "GroupsDomainsExtractor"
appversion = "1.1"

def extractDomains():
    # specify the url
    quote_page = values[0]

    # query the website and return the html to the variable ‘page’
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )
    page = http.request('GET', quote_page)

    # parse the html using beautiful soup and store in variable `soup`
    soup = BeautifulSoup(page.data, "html5lib")

    data = soup.select(values[1])

    final_links = []

    for a in data:
        a['href'] = tldextract.extract(a['href']).registered_domain
        final_links.append(a['href'])

    final_links = sorted(set(final_links))

    if values[2] == 'przecinek':
        separator = ","
    elif values[2] == 'pipe':
        separator = "|"

    print(separator.join(final_links))
    r = Tk()
    r.clipboard_append(separator.join(final_links))
    r.update()
    r.destroy()
    if final_links:
        sg.Popup("Gotowe", "Domeny zostały skopiowane do schowka :-)")
    else:
        sg.Popup("Błąd","Domeny nie zostały znalezione. Sprawdź wpisane dane i spróbuj ponownie!")

def saveGroup():
    config = configparser.ConfigParser()

    if not os.path.exists(user_config_dir(appname)):
        os.mkdir(user_config_dir(appname))

    cfilepath=user_config_dir(appname)+'/groups.ini'
    config.read(cfilepath)
    if not values['GROUP_NAME']:
        sg.Popup("Błąd", "Nie tak szybko kowboju, wprowadź nazwę grupy!")

    if values['GROUP_NAME']:
        if config.has_section(values['GROUP_NAME']):
            config.remove_section(values['GROUP_NAME'])

        config[values['GROUP_NAME']] = {'url': values['URL'], 'css': values['CSS'], 'separator': values['SEPARATOR']}
        cfile = open(cfilepath, 'w')
        config.write(cfile)
        cfile.close()
        window.FindElement('GROUP').Update(values=([*loadGroupList()]))

        sg.Popup("Gotowe", "Grupa "+values['GROUP_NAME']+" została zapisana do pliku: "+cfilepath)

def loadGroupList():
    config = configparser.ConfigParser()
    cfilepath = user_config_dir(appname)+'/groups.ini'
    config.read(cfilepath)
    sections = []
    for each_section in config.sections():
        sections.append(each_section)
    return sections

def loadGroup():
    config = configparser.ConfigParser()
    cfilepath = user_config_dir(appname)+'/groups.ini'
    config.read(cfilepath)
    window.Element('URL').Update(config[values['GROUP']]['url'])
    window.Element('CSS').Update(config[values['GROUP']]['css'])
    window.Element('SEPARATOR').Update(config[values['GROUP']]['separator'])
    window.Element('GROUP_NAME').Update(values['GROUP'])


layout = [
          [sg.Text('Adres strony:', size=(30, 1)), sg.InputText('http://siecportali.pl/realizacje', key='URL')],
          [sg.Text('Ścieżka CSS:', size=(30, 1)), sg.InputText('.portal-logos a', key="CSS")],
          [sg.Text('Separator:', size=(30, 1)), sg.Combo(['przecinek', 'pipe'], key="SEPARATOR")],
          [sg.Text('Nazwa grupy:', size=(30, 1)), sg.InputText('Sieć portali', key="GROUP_NAME")],
          [sg.Text('Konfiguracja grupy:', size=(30, 1)), sg.Combo([*loadGroupList()], key="GROUP", size=(35,1))],
          [sg.Submit('Wyodrębnij domeny'), sg.Submit('Wczytaj grupę'), sg.Submit('Zapisz grupę'), sg.Cancel('Zamknij mnie'), ]
         ]

window = sg.Window('Ekstraktor domen grup '+appversion).Layout(layout)
while True:
    event, values = window.Read()
    if event == 'Wyodrębnij domeny':
        extractDomains()
    if event == 'Zapisz grupę':
        saveGroup()
    if event == 'Wczytaj grupę':
        loadGroup()
    if event is None or event == 'Zamknij mnie':
        break

