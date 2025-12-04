#!/usr/bin/env python3
"""
Simple script to run the OLX scraper with custom search terms
"""

import sys
import os
from olx_scraper import OLXScraper

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_scraper.py <search_term> [max_pages]")
        print("Example: python run_scraper.py 'xbox defect' 10")
        print("Or: python run_scraper.py 'iphone 12' 5")
        return

    search_term = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    # Create the OLX search URL
    # Replace spaces with dashes and encode the search term
    search_term_encoded = search_term.replace(' ', '-').lower()
    search_url = f"https://www.olx.ro/oferte/q-{search_term_encoded}/"

    print(f"Searching for: '{search_term}'")
    print(f"URL: {search_url}")
    print(f"Max pages: {max_pages}")
    print("-" * 50)

    # Create scraper and run it
    scraper = OLXScraper()
    listings = scraper.scrape_search(search_url, max_pages=max_pages)

    if listings:
        print(f"\n✅ Successfully scraped {len(listings)} listings!")

        # Generate filenames based on search term
        safe_filename = search_term.replace(' ', '_').replace('-', '_').lower()
        json_file = f"olx_{safe_filename}.json"
        csv_file = f"olx_{safe_filename}.csv"

        # Save with custom filenames
        scraper.save_to_json(listings, json_file)
        scraper.save_to_csv(listings, csv_file)

        print(f"📄 Saved to: {json_file} and {csv_file}")

        # Show sample
        print("\n📋 Sample results:")
        for i, listing in enumerate(listings[:5]):
            print(f"{i+1}. {listing['title'][:50]}... - {listing['price']}")
    else:
        print("❌ No listings found or scraping failed")

if __name__ == "__main__":
    main()
