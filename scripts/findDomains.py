# import libraries
from bs4 import BeautifulSoup
import certifi
import urllib3
import tldextract
import PySimpleGUI as sg
from tkinter import Tk

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
    print(','.join(final_links))
    r = Tk()
    r.clipboard_append(','.join(final_links))
    r.update()
    r.destroy()
    if final_links:
        sg.Popup("Gotowe", "Domeny zostały skopiowane do schowka :-)")
    else:
        sg.Popup("Błąd","Domeny nie zostały znalezione. Sprawdź wpisane dane i spróbuj ponownie!")

layout = [
          [sg.Text('Adres strony:', size=(30, 1)), sg.InputText('http://siecportali.pl/realizacje')],
          [sg.Text('Ścieżka CSS:', size=(30, 1)), sg.InputText('.portal-logos a')],
          [sg.Submit('Wyodrębnij domeny'), sg.Cancel('Zamknij mnie')]
         ]

window = sg.Window('Ekstraktor domen').Layout(layout)
while True:
    event, values = window.Read()
    if event == 'Wyodrębnij domeny':
        extractDomains()
    if event is None or event == 'Zamknij mnie':
        break

