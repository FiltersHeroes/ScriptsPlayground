# import libraries
from bs4 import BeautifulSoup
import certifi
import urllib3
import tldextract

# specify the url
quote_page = 'http://cmcmedia.pl/testowa/'

# query the website and return the html to the variable ‘page’
http = urllib3.PoolManager()
page = http.request('GET', quote_page)

# parse the html using beautiful soup and store in variable `soup`
soup = BeautifulSoup(page.data, "html5lib")

data = soup.select('.container.vc_row-fluid a')

final_links = []

for a in data:
    a['href'] = tldextract.extract(a['href']).registered_domain
    final_links.append(a['href'])

final_links = sorted(set(final_links))
print(','.join(final_links))
