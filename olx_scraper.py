import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse
import re

class OLXScraper:
    def __init__(self):
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_page(self, url, max_retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e

    def parse_listing(self, listing_element):
        """Extract data from a single listing element"""
        try:
            # Find the link (usually in an <a> tag)
            link_element = listing_element.find('a', href=True)
            if not link_element:
                return None

            link = link_element['href']
            # Make sure it's an absolute URL
            if not link.startswith('http'):
                link = urljoin('https://www.olx.ro', link)

            # Find title (usually in the link or a nearby element)
            title = link_element.get('title') or link_element.get_text(strip=True)
            if not title:
                title_element = listing_element.find(['h3', 'h4', 'h5', 'h6'])
                title = title_element.get_text(strip=True) if title_element else "No title"

            # Find price (usually in a span or div with price-related class)
            price = "N/A"
            price_element = listing_element.find(['span', 'div', 'p'], class_=re.compile(r'(price|pret)', re.I))
            if price_element:
                price = price_element.get_text(strip=True)
            else:
                # Look for any text containing lei or € or numbers that might be prices
                text = listing_element.get_text()
                # Find all price matches and select the highest value one
                price_matches = re.findall(r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*(lei|€|eur|ron)', text, re.I)

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
                        except ValueError:
                            continue

                    if prices_with_values:
                        # Select the highest price value
                        prices_with_values.sort(key=lambda x: x[0], reverse=True)
                        price = prices_with_values[0][1]  # Use the formatted price string

            # Find location (usually contains city/region info)
            location = "N/A"
            location_element = listing_element.find(['span', 'div', 'p'], class_=re.compile(r'(location|locatie|city|oras)', re.I))
            if location_element:
                location = location_element.get_text(strip=True)

            # Find date (usually contains "azi" or date info)
            date = "N/A"
            date_element = listing_element.find(['span', 'div', 'p'], class_=re.compile(r'(date|data|time|timp)', re.I))
            if date_element:
                date = date_element.get_text(strip=True)

            return {
                'title': title,
                'price': price,
                'location': location,
                'date': date,
                'link': link
            }
        except Exception as e:
            print(f"Error parsing listing: {e}")
            return None

    def get_listings_from_page(self, html_content, base_url):
        """Extract all listings from a page"""
        soup = BeautifulSoup(html_content, 'lxml')
        listings = []

        # Common selectors for OLX listings - try multiple patterns
        selectors = [
            'table#offers_table tbody tr',  # Sometimes they use tables
            'div[data-cy="l-card"]',        # Newer OLX structure
            '.offer-wrapper',               # Common wrapper class
            '.listing-item',                # Generic listing item
            'div.offer',                    # Offer containers
            'article[data-cy="ad-card"]',   # Another common pattern
            '.css-1sw7q4x'                  # Sometimes they use CSS modules
        ]

        found_listings = False
        for selector in selectors:
            listing_elements = soup.select(selector)
            if listing_elements:
                print(f"Found {len(listing_elements)} listings using selector: {selector}")
                found_listings = True

                for element in listing_elements:
                    listing_data = self.parse_listing(element)
                    if listing_data:
                        listings.append(listing_data)
                break

        # If no specific selectors work, try to find all links that look like listing URLs
        if not found_listings:
            print("No standard selectors worked, trying to find listing links...")
            all_links = soup.find_all('a', href=re.compile(r'/oferta/|/d/oferta/'))
            for link in all_links:
                href = link['href']
                if not href.startswith('http'):
                    href = urljoin(base_url, href)

                title = link.get('title') or link.get_text(strip=True)
                if title and len(title) > 10:  # Filter out very short titles
                    listings.append({
                        'title': title,
                        'price': 'N/A',
                        'location': 'N/A',
                        'date': 'N/A',
                        'link': href
                    })

        return listings

    def get_next_page_url(self, html_content, base_url):
        """Find the next page URL for pagination"""
        soup = BeautifulSoup(html_content, 'lxml')

        # Look for pagination links
        pagination_selectors = [
            'a[data-cy="pagination-forward"]',
            '.pagination a.next',
            'a.next',
            'a[rel="next"]',
            'link[rel="next"]'
        ]

        for selector in pagination_selectors:
            next_link = soup.select_one(selector)
            if next_link:
                href = next_link.get('href')
                if href:
                    return urljoin(base_url, href)

        # Try to find pagination by looking for page=2, page=3, etc.
        current_url = urlparse(base_url)
        query_params = current_url.query

        # If there's already a page parameter, increment it
        if 'page=' in query_params:
            page_match = re.search(r'page=(\d+)', query_params)
            if page_match:
                current_page = int(page_match.group(1))
                next_page_url = base_url.replace(f'page={current_page}', f'page={current_page + 1}')
                return next_page_url
        else:
            # Add page parameter if it doesn't exist
            separator = '&' if query_params else '?'
            return base_url + separator + 'page=2'

        return None

    def scrape_search(self, search_url, max_pages=10):
        """Scrape all listings from a search URL"""
        all_listings = []
        current_url = search_url
        page_count = 0

        while current_url and page_count < max_pages:
            page_count += 1
            print(f"Scraping page {page_count}: {current_url}")

            try:
                html_content = self.get_page(current_url)
                listings = self.get_listings_from_page(html_content, current_url)

                if not listings:
                    print(f"No listings found on page {page_count}, stopping...")
                    break

                all_listings.extend(listings)
                print(f"Found {len(listings)} listings on page {page_count} (total: {len(all_listings)})")

                # Get next page URL
                next_url = self.get_next_page_url(html_content, current_url)
                if next_url and next_url != current_url:
                    current_url = next_url
                    time.sleep(1)  # Be respectful, add delay between requests
                else:
                    print("No more pages found")
                    break

            except Exception as e:
                print(f"Error scraping page {page_count}: {e}")
                break

        return all_listings

    def save_to_json(self, listings, filename='olx_listings.json'):
        """Save listings to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(listings, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(listings)} listings to {filename}")

    def save_to_csv(self, listings, filename='olx_listings.csv'):
        """Save listings to CSV file"""
        import csv

        if not listings:
            print("No listings to save")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'price', 'location', 'date', 'link']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(listings)
        print(f"Saved {len(listings)} listings to {filename}")


def main():
    # Example usage
    scraper = OLXScraper()

    # The URL you provided
    search_url = "https://www.olx.ro/oferte/q-xbox-defect/"

    print(f"Starting scrape of: {search_url}")
    listings = scraper.scrape_search(search_url, max_pages=5)  # Limit to 5 pages for testing

    if listings:
        print(f"\nScraped {len(listings)} total listings")

        # Save to both JSON and CSV
        scraper.save_to_json(listings)
        scraper.save_to_csv(listings)

        # Show a sample of what was scraped
        print("\nSample of scraped data:")
        for i, listing in enumerate(listings[:3]):
            print(f"{i+1}. {listing['title']} - {listing['price']} - {listing['link']}")
    else:
        print("No listings were scraped. The page structure might have changed.")


if __name__ == "__main__":
    main()
