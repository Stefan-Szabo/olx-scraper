import requests
from bs4 import BeautifulSoup
import re
import json

def extract_price_from_page(html_content):
    soup = BeautifulSoup(html_content, 'lxml')

    # First, try OLX-specific price display elements
    olx_price_selectors = [
        'h3[data-testid="ad-price"]',
        '[data-cy="ad-price"]',
        '.css-1q7gvpp',
        '.css-1hgk2z',
        '.ad-price',
        '.price'
    ]

    for selector in olx_price_selectors:
        price_elem = soup.select_one(selector)
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(lei|€|eur|ron)', price_text, re.I)
            if price_match:
                price_str, currency = price_match.groups()
                try:
                    numeric_str = price_str.replace('.', '').replace(',', '.')
                    numeric_value = float(numeric_str)
                    if 10 <= numeric_value <= 10000:
                        print(f'Found in OLX element: {price_str} {currency}')
                        return f'{price_str} {currency}'
                except ValueError:
                    continue

    # Check structured data
    json_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and 'offers' in data:
                offers = data['offers']
                if isinstance(offers, dict) and 'price' in offers:
                    price_val = offers['price']
                    currency = offers.get('priceCurrency', 'lei')
                    try:
                        numeric_value = float(price_val)
                        if 10 <= numeric_value <= 10000:
                            print(f'Found in structured data: {int(numeric_value)} {currency.lower()}')
                            return f'{int(numeric_value)} {currency.lower()}'
                    except (ValueError, TypeError):
                        continue
        except:
            continue

    print('No price found in structured elements')
    return None

# Test on the problematic URL
url = 'https://www.olx.ro/d/oferta/vand-schimb-xbox-one-s-cu-logitech-g29-g923-IDk3JID.html'
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
result = extract_price_from_page(response.text)
print(f'Final result: {result}')
