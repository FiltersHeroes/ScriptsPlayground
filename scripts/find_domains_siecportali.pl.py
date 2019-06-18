# import libraries
from bs4 import BeautifulSoup
import certifi
import urllib3
import re

# specify the url
quote_page = 'http://siecportali.pl/realizacje'

# query the website and return the html to the variable ‘page’
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)
page = http.request('GET', quote_page)

# parse the html using beautiful soup and store in variable `soup`
soup = BeautifulSoup(page.data, "html5lib")

data = soup.find_all('div', class_="portal-logos")

final_links = []

for div in data:
    links = div.find_all('a')
    for a in links:
        a['href'] = re.sub('http(s)?:\/\/', "", a['href'])
        a['href'] = re.sub('[\/]$', "", a['href'])
        final_links.append(a['href'])
        break

final_links.sort()
print(','.join(final_links))
