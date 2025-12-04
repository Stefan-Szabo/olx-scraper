import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.olx.ro/d/oferta/vand-schimb-xbox-one-s-cu-logitech-g29-g923-IDk3JID.html'
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(response.text, 'lxml')

print(f'Checking URL: {url}')
print('=' * 50)

# Simple search: does "599 lei" appear anywhere?
all_text = soup.get_text()
has_599_lei = '599 lei' in all_text or '599lei' in all_text
print(f'Contains "599 lei": {has_599_lei}')

# Find all instances of "599" followed by "lei"
matches_599_lei = re.findall(r'599\s*lei', all_text, re.I)
print(f'Found "599 lei" patterns: {matches_599_lei}')

# Check the raw HTML for the price
html_content = str(soup)
html_599_lei = re.findall(r'599[^0-9]*lei', html_content, re.I)
print(f'Found in HTML: {html_599_lei}')

# Look for any data attributes that might contain price
price_data = soup.find_all(attrs={'data-price': True})
print(f'Data-price attributes: {[elem.get("data-price") for elem in price_data]}')

# Check if there's a canonical price element
canonical_price = soup.find('meta', property='product:price:amount')
if canonical_price:
    print(f'Canonical price: {canonical_price.get("content")}')
