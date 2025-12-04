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

### Custom Search Terms (Recommended)

Use the convenient wrapper script to search for any term:

```bash
python run_scraper.py "xbox defect" 10
python run_scraper.py "iphone 12" 5
python run_scraper.py "masina second hand" 20
```

The script will automatically:
- Create the correct OLX URL
- Save results to files named after your search term
- Show a sample of results

### Advanced Usage

Edit the `search_url` variable in `olx_scraper.py` to scrape any specific OLX search URL:

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
- `price`: Price in RON/lei or EUR (extracted successfully ✅)
- `location`: City/region where the item is located (currently shows "N/A" - needs refinement)
- `date`: When the listing was posted (currently shows "N/A" - needs refinement)
- `link`: Direct link to the listing (extracted successfully ✅)

**Current Status**: The scraper successfully extracts titles, prices, and links. Location and date extraction may need updates as OLX changes their page structure.

## Configuration

You can modify these settings in `olx_scraper.py`:

- `max_pages`: Maximum number of pages to scrape (default: 5)
- `max_retries`: Number of retries for failed requests (default: 3)
- Delay between requests: Currently 1 second (can be adjusted)

## 🚀 GitHub Pages Website

This repository includes a GitHub Pages website that displays the filtered listings with an interactive interface.

### Features:
- **📊 Live Dashboard**: View all current defect listings (Xbox, PlayStation, Nintendo Switch)
- **⭐ Follow Listings**: Save interesting listings to a personal watchlist
- **🚫 Permanent Exclusions**: Hide unwanted listings forever
- **📈 Price Tracking**: Get notifications when followed items change price
- **🔄 Auto Updates**: Site updates automatically every hour via GitHub Actions
- **📱 Responsive Design**: Works on desktop and mobile devices

### Supported Consoles & Filters:

#### 🎮 **Xbox Series**
- **Models**: One, One S, One X, Series S, Series X
- **Price Limits**: 200-800 RON depending on model
- **Exclusions**: Items described as flawless/perfect

#### 🎮 **PlayStation**
- **Wanted**: PS4 (normal/slim/pro), PS5 (all variants)
- **Excluded**: PS3, PSP, and other old models
- **Price Limits**: PS4 (200-500 RON), PS5 (600 RON max)

#### 🎮 **Nintendo Switch**
- **Wanted**: Standard Switch models
- **Excluded**: Switch Lite variants
- **Price Limit**: 400 RON max

### Accessing the Website:
1. Go to your repository settings
2. Scroll down to "Pages" section
3. Set Source to "Deploy from a branch"
4. Select "main" branch and "/ (root)" folder
5. The site will be available at: `https://[your-username].github.io/olx-scraper/`

### Website Functionality:
- **Available Listings**: Shows all current defect listings that passed the filters
- **Followed Listings**: Personal watchlist that persists across updates
- **Auto Cleanup**: Expired listings are automatically removed from followed list
- **Selection Interface**: Checkboxes and buttons to manage your followed listings

**Note**: The "followed listings" feature uses localStorage for demonstration. For production use, consider implementing a backend service for persistent storage across devices.

## 🤖 Automation

The scraper runs automatically every hour via GitHub Actions:

- **Schedule**: Every hour at :00 minutes
- **Searches**: Xbox defect, PlayStation defect, Nintendo Switch defect
- **Process**: Scrape all searches → Filter → Update website → Commit changes
- **Triggers**: Also runs on code changes or manual trigger

## Legal Note

Please respect OLX's terms of service and robots.txt. This scraper is for educational purposes only. Consider the ethical implications and legal restrictions before using it for commercial purposes.

## Troubleshooting

If the scraper doesn't find listings:
1. OLX may have changed their page structure
2. Check if the website is blocking automated requests
3. The search URL might be invalid

The scraper tries multiple CSS selectors to find listings, but if OLX changes their design significantly, you may need to update the selectors in the `get_listings_from_page` method.
