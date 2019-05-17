# import libraries
from bs4 import BeautifulSoup
import certifi
import urllib3

# specify the url
quote_page = 'https://www.legalniewsieci.pl/aktualnosci/podejrzane-sklepy-internetowe'

# query the website and return the html to the variable ‘page’
http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)
page = http.request('GET', quote_page)

# parse the html using beautiful soup and store in variable `soup`
soup = BeautifulSoup(page.data, "html5lib")

data = soup.find_all('div', class_="ul-unsafe")

for div in data:
    links = div.find_all('a', rel="nofollow")
    for a in links:
        print(a['href'])
