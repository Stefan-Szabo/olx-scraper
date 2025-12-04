# OLX Romania Scraper

A Python scraper for extracting listings from OLX Romania (olx.ro).

## Features

- Scrapes OLX search results automatically
- Handles pagination to get all results
- Extracts title, price, location, date, and links
- Saves data to both JSON and CSV formats
- Respects rate limits with delays between requests
- Robust error handling and retry logic

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd olx-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper with the default search URL (xbox defect):

```bash
python olx_scraper.py
```

### Custom Search URL

Edit the `search_url` variable in `olx_scraper.py` to scrape any OLX search:

```python
search_url = "https://www.olx.ro/oferte/q-your-search-term/"
```

### Output

The scraper will create two output files:
- `olx_listings.json` - Detailed JSON format
- `olx_listings.csv` - CSV format for easy viewing in Excel/spreadsheets

## Data Structure

Each listing contains:
- `title`: The listing title
- `price`: Price in RON/lei or EUR
- `location`: City/region where the item is located
- `date`: When the listing was posted
- `link`: Direct link to the listing

## Configuration

You can modify these settings in `olx_scraper.py`:

- `max_pages`: Maximum number of pages to scrape (default: 5)
- `max_retries`: Number of retries for failed requests (default: 3)
- Delay between requests: Currently 1 second (can be adjusted)

## Legal Note

Please respect OLX's terms of service and robots.txt. This scraper is for educational purposes only. Consider the ethical implications and legal restrictions before using it for commercial purposes.

## Troubleshooting

If the scraper doesn't find listings:
1. OLX may have changed their page structure
2. Check if the website is blocking automated requests
3. The search URL might be invalid

The scraper tries multiple CSS selectors to find listings, but if OLX changes their design significantly, you may need to update the selectors in the `get_listings_from_page` method.
