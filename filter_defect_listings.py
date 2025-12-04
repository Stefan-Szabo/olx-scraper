import csv
import json
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin

class OLXDefectFilter:
    def __init__(self):
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Forbidden phrases that indicate items WITHOUT defects or are too good quality
        self.forbidden_phrases = [
            "fără defect",
            "fără defecte",
            "fara defecte",
            "fara-defecte",  # URL version with hyphen
            "ca nou",
            "perfect functional",
            "perfect funcțional",
            "promovat",  # Exclude promoted/sponsored listings
            "impecabil",  # Exclude flawless/perfect items
            "reparatii",  # Exclude repair services
            "reparatie",  # Exclude repair services
            "reparații",  # Exclude repair services (with diacritics)
            "reparație"   # Exclude repair services (with diacritics)
        ]

        # Unwanted PlayStation models to exclude
        self.excluded_ps_models = [
            "ps3", "psp", "playstation 3", "playstation3", "ps3", "psp"
        ]

        # Unwanted Nintendo Switch models to exclude
        self.excluded_switch_models = [
            "lite", "switch lite"
        ]

        # Price limits for different models (in RON)
        self.price_limits = {
            # Xbox models
            "xbox one": 200,
            "xbox one s": 200,
            "xbox one x": 500,
            "xbox series s": 500,
            "xbox series x": 700,
            # PlayStation models
            "ps4": 200,
            "ps4 slim": 250,
            "ps4 pro": 500,
            "ps5": 700,
            "ps5 digital": 600,
            # Nintendo Switch models
            "switch": 400,
            "nintendo switch": 400
        }

    def get_page(self, url, max_retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to fetch {url} after {max_retries} attempts")
                    return None

    def has_forbidden_phrase(self, text):
        """Check if text contains any forbidden phrases"""
        if not text:
            return False

        text_lower = text.lower()

        # Check for exact phrases (not just individual words)
        for phrase in self.forbidden_phrases:
            if phrase in text_lower:
                return True
        return False

    def identify_model(self, title):
        """Identify the console model from the title (Xbox, PS, Switch)"""
        title_lower = title.lower()

        # Check Xbox models (most specific first)
        xbox_models = ["xbox series x", "xbox series s", "xbox one x", "xbox one s", "xbox one"]
        for model in xbox_models:
            if model in title_lower:
                return model

        # Check PlayStation models
        ps_models = ["ps5 digital", "ps5", "ps4 pro", "ps4 slim", "ps4"]
        for model in ps_models:
            if model in title_lower:
                return model

        # Check Nintendo Switch models
        switch_models = ["nintendo switch", "switch"]
        for model in switch_models:
            if model in title_lower:
                return model

        return None

    def identify_xbox_model(self, title):
        """Legacy method for backward compatibility"""
        return self.identify_model(title)

    def parse_price(self, price_string):
        """Parse price string and return numeric value"""
        if not price_string or price_string == "N/A":
            return None

        # Remove currency and clean up
        price_str = price_string.lower().replace("lei", "").replace("ron", "").replace("€", "").replace("eur", "").strip()

        # Handle Romanian number format (1.234,56)
        price_str = price_str.replace(".", "").replace(",", ".")

        try:
            return float(price_str)
        except ValueError:
            return None

    def is_price_too_high(self, title, price_string):
        """Check if the price exceeds the limit for the identified Xbox model"""
        model = self.identify_xbox_model(title)
        if not model:
            return False  # If we can't identify the model, don't exclude based on price

        price_limit = self.price_limits.get(model)
        if not price_limit:
            return False

        price = self.parse_price(price_string)
        if price is None:
            return False  # If we can't parse the price, don't exclude

        return price > price_limit

    def extract_description(self, html_content, base_url):
        """Extract description from OLX listing page"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Common selectors for OLX description
            description_selectors = [
                'div[data-cy="ad-description"]',
                '.description',
                '.ad-description',
                '[data-testid="ad-description"]',
                '.css-1t8sg8s',  # Sometimes they use CSS modules
                '.clr-text-sm'   # Another common pattern
            ]

            for selector in description_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    description = desc_element.get_text(strip=True)
                    if description and len(description) > 20:  # Filter out very short texts
                        return description

            # Fallback: look for any div with substantial text content
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if len(text) > 100 and not any(skip in text.lower() for skip in ['telefon', 'email', 'contact']):
                    return text

        except Exception as e:
            print(f"Error extracting description: {e}")

        return ""

    def get_listing_id(self, link):
        """Extract listing ID from URL"""
        # Extract listing ID from URL pattern like -IDxxxxx.html
        import re
        match = re.search(r'-ID([a-zA-Z0-9]+)\.html', link)
        return match.group(1) if match else link

    def extract_price_from_page(self, html_content):
        """Extract the most accurate price from an individual listing page"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # First, try to find price in OLX-specific price display elements
            olx_price_selectors = [
                'h3[data-testid="ad-price"]',
                '[data-cy="ad-price"]',
                '.css-1q7gvpp',  # OLX price class
                '.css-1hgk2z',   # Another OLX price class
                '.ad-price',
                '.price'
            ]

            for selector in olx_price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Extract just the number and currency
                    price_match = re.search(r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(lei|€|eur|ron)', price_text, re.I)
                    if price_match:
                        price_str, currency = price_match.groups()
                        try:
                            numeric_str = price_str.replace('.', '').replace(',', '.')
                            numeric_value = float(numeric_str)
                            if 10 <= numeric_value <= 10000:  # Reasonable range check
                                final_price = f"{price_str} {currency}"
                                print(f"  Found price in OLX element: {final_price}")
                                return final_price
                        except ValueError:
                            continue

            # Fallback: Look for structured data (JSON-LD)
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict) and 'price' in offers:
                            price_val = offers['price']
                            currency = offers.get('priceCurrency', 'lei')
                            try:
                                numeric_value = float(price_val)
                                if 10 <= numeric_value <= 10000:
                                    final_price = f"{int(numeric_value)} {currency.lower()}"
                                    print(f"  Found price in structured data: {final_price}")
                                    return final_price
                            except (ValueError, TypeError):
                                continue
                except (json.JSONDecodeError, TypeError):
                    continue

            # Last resort: Scan all text but be more selective
            all_text = soup.get_text()
            price_matches = re.findall(r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(lei|€|eur|ron)', all_text, re.I)

            if price_matches:
                # Filter and score prices
                realistic_prices = []
                for match in price_matches:
                    price_str, currency = match
                    try:
                        numeric_str = price_str.replace('.', '').replace(',', '.')
                        numeric_value = float(numeric_str)

                        # Stricter filtering - exclude prices that might be model numbers
                        if 50 <= numeric_value <= 5000:  # Reasonable range for used electronics
                            # Additional check: exclude prices that appear to be model numbers
                            # (prices ending in common model number patterns)
                            if not re.search(r'(g\d{2,}|xbox|one|s|x)$', price_str, re.I):
                                realistic_prices.append((numeric_value, f"{price_str} {currency}"))
                                print(f"  Found text price: {price_str} {currency}")

                    except ValueError:
                        continue

                if realistic_prices:
                    # Sort by confidence (prefer prices in typical ranges)
                    def price_confidence(price_info):
                        price_val = price_info[0]
                        if 200 <= price_val <= 1500:  # Sweet spot for Xbox items
                            return 3
                        elif 100 <= price_val <= 2500:
                            return 2
                        else:
                            return 1

                    realistic_prices.sort(key=lambda x: (price_confidence(x), x[0]), reverse=True)
                    selected_price = realistic_prices[0][1]
                    print(f"  Selected price: {selected_price}")
                    return selected_price

        except Exception as e:
            print(f"Error extracting price from page: {e}")

        return None

    def should_exclude_listing(self, title, link, price=None, excluded_listings=None):
        """Check if a listing should be excluded based on title, URL, description, and price"""
        # Check if listing is in permanent exclusion list
        if excluded_listings:
            listing_id = self.get_listing_id(link)
            if listing_id in excluded_listings:
                print(f"❌ Excluding (manually excluded): {title[:50]}...")
                return True

        # Check title for forbidden phrases
        if self.has_forbidden_phrase(title):
            print(f"❌ Excluding (title quality): {title[:50]}...")
            return True

        # Also check URL for forbidden phrases (since titles might be incomplete)
        url_lower = link.lower()
        if self.has_forbidden_phrase(url_lower):
            print(f"❌ Excluding (URL quality): {title[:50]}...")
            return True

        # Fetch the individual page to get accurate price and description
        print(f"🔍 Checking listing page for: {title[:50]}...")

        html_content = self.get_page(link)
        if not html_content:
            print("⚠️  Could not fetch page, keeping listing")
            return False

        # Get the accurate price from the individual page
        accurate_price = self.extract_price_from_page(html_content)
        if accurate_price:
            print(f"📊 Price from page: {accurate_price} (was: {price})")
            # Use the accurate price for filtering
            price = accurate_price

        # Check for unwanted PlayStation models
        title_lower = title.lower()
        if any(excluded in title_lower for excluded in self.excluded_ps_models):
            print(f"❌ Excluding (unwanted PS model): {title[:50]}...")
            return True

        # Check for unwanted Switch models
        if any(excluded in title_lower for excluded in self.excluded_switch_models):
            print(f"❌ Excluding (unwanted Switch model): {title[:50]}...")
            return True

        # Check if price is too high for the model (using accurate price)
        if self.is_price_too_high(title, price):
            model = self.identify_model(title)
            if model:
                price_limit = self.price_limits.get(model, 0)
                print(f"❌ Excluding (price too high - {price} > {price_limit} for {model}): {title[:50]}...")
                return True

        # Check description for forbidden phrases
        description = self.extract_description(html_content, link)

        if self.has_forbidden_phrase(description):
            print(f"❌ Excluding (description quality): {title[:50]}...")
            return True

        print(f"✅ Keeping: {title[:50]}...")
        return False

    def filter_listings(self, input_file, output_file, max_listings=None):
        """Filter listings from CSV file"""
        filtered_listings = []
        excluded_count = 0

        # Load permanently excluded listings
        excluded_listings = {}
        try:
            with open('excluded_listings.json', 'r', encoding='utf-8') as f:
                excluded_listings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            excluded_listings = {}

        try:
            with open(input_file, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                all_rows = list(reader)
                total_listings = len(all_rows)

                if max_listings:
                    all_rows = all_rows[:max_listings]
                    print(f"🔍 Processing first {max_listings} listings for testing...")

                processed = 0
                for row in all_rows:
                    processed += 1
                    title = row.get('title', '')
                    link = row.get('link', '')

                    print(f"📊 Progress: {processed}/{len(all_rows)} listings")

                    if not title or not link:
                        continue

                    price = row.get('price', '')
                    if self.should_exclude_listing(title, link, price, excluded_listings):
                        excluded_count += 1
                    else:
                        filtered_listings.append(row)

                    # Add small delay between requests to be respectful
                    time.sleep(0.5)

        except FileNotFoundError:
            print(f"❌ Input file '{input_file}' not found")
            return []

        print(f"\n📊 Filtering Summary:")
        print(f"   Total listings: {total_listings}")
        print(f"   Excluded (no defects): {excluded_count}")
        print(f"   Kept (with defects): {len(filtered_listings)}")

        # Save filtered results
        if filtered_listings:
            fieldnames = ['title', 'price', 'location', 'date', 'link']
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered_listings)

            print(f"💾 Saved {len(filtered_listings)} filtered listings to {output_file}")

        return filtered_listings

def main():
    import sys

    # Check for command line argument for testing
    max_listings = None
    if len(sys.argv) > 1:
        try:
            max_listings = int(sys.argv[1])
            print(f"🧪 Testing mode: processing first {max_listings} listings")
        except ValueError:
            print("Usage: python filter_defect_listings.py [max_listings]")
            return

    # Filter the xbox defect listings
    input_file = 'olx_listings.csv'
    output_file = 'olx_defect_only.csv'

    print("🔍 Starting OLX defect filtering...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print("-" * 50)

    filter = OLXDefectFilter()
    filtered_listings = filter.filter_listings(input_file, output_file, max_listings)

    if filtered_listings:
        print(f"\n✅ Success! Filtered {len(filtered_listings)} listings with actual defects.")
        print(f"📄 Check {output_file} for the results.")

        # Show sample of filtered results
        print("\n📋 Sample of filtered listings:")
        for i, listing in enumerate(filtered_listings[:5]):
            print(f"{i+1}. {listing['title'][:60]}... - {listing['price']}")
    else:
        print("\n❌ No listings passed the filter.")

if __name__ == "__main__":
    main()
