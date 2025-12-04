import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.olx.ro/d/oferta/oferta-xbox-series-x-1tb-garantie-12-luni-controller-joc-bonus-IDjaAnn.html'
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(response.text, 'lxml')

print(f"Testing updated price extraction on: {url}")
print("=" * 60)

# Simulate the updated price extraction logic
text = soup.get_text()
price_matches = re.findall(r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(lei|€|eur|ron)', text, re.I)

print("All price matches found:")
for match in price_matches:
    print(f"  {match[0]} {match[1]}")

if price_matches:
    # Convert prices to numeric values and find the highest
    prices_with_values = []
    for match in price_matches:
        price_str, currency = match
        try:
            # Convert Romanian format (1.234,56) to float
            numeric_str = price_str.replace('.', '').replace(',', '.')
            numeric_value = float(numeric_str)
            prices_with_values.append((numeric_value, f"{price_str} {currency}"))
            print(f"  Converted {price_str} {currency} -> {numeric_value}")
        except ValueError:
            print(f"  Failed to convert: {price_str} {currency}")
            continue

    if prices_with_values:
        # Select the highest price value
        prices_with_values.sort(key=lambda x: x[0], reverse=True)
        selected_price = prices_with_values[0][1]
        print(f"\n🎯 SELECTED PRICE: {selected_price}")
        print(f"   (Highest value: {prices_with_values[0][0]})")
    else:
        print("No valid prices found")
else:
    print("No price matches found")
