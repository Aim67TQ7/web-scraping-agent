# Web Scraping Agent

A powerful and flexible web scraping agent built with Python, featuring multiple scraping strategies, rate limiting, and robust error handling.

## Features

- 🚀 Multiple scraping backends (requests, Selenium, async)
- 🔄 Automatic retry logic with exponential backoff
- ⏱️ Built-in rate limiting
- 🔐 Proxy and user-agent rotation support
- 📊 Multiple data export formats (CSV, JSON, Excel, Database)
- 🛡️ Robust error handling and logging
- 🧪 Comprehensive test coverage
- 🎯 Easy-to-use CLI interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/web-scraping-agent.git
cd web-scraping-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.scraper import WebScraper

# Create a scraper instance
scraper = WebScraper()

# Scrape a single page
data = scraper.scrape_page("https://example.com")

# Scrape multiple pages
urls = ["https://example.com/page1", "https://example.com/page2"]
results = scraper.scrape_multiple(urls)

# Save results
scraper.save_to_csv(results, "output.csv")
```

### CLI Usage

```bash
# Scrape a single URL
python -m src.cli scrape --url https://example.com --output data.json

# Scrape from URL list
python -m src.cli scrape-list --file urls.txt --output results.csv

# Run with custom config
python -m src.cli scrape --url https://example.com --config config/custom.json
```

## Configuration

Create a `.env` file in the root directory:

```env
# Scraping settings
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
RATE_LIMIT=10  # requests per second
TIMEOUT=30  # seconds
RETRY_COUNT=3
RETRY_DELAY=5  # seconds

# Proxy settings (optional)
PROXY_URL=http://proxy.example.com:8080
PROXY_USER=username
PROXY_PASS=password

# Database settings (optional)
DATABASE_URL=postgresql://user:password@localhost/scraping_db

# Selenium settings (optional)
CHROME_DRIVER_PATH=/path/to/chromedriver
HEADLESS=true
```

## Project Structure

```
web-scraping-agent/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Base scraper class
│   ├── scrapers/           # Specific scraper implementations
│   │   ├── __init__.py
│   │   ├── static.py       # For static websites
│   │   ├── dynamic.py      # For JavaScript-heavy sites
│   │   └── api.py          # For API endpoints
│   ├── parsers/            # HTML/JSON parsers
│   │   ├── __init__.py
│   │   ├── html_parser.py
│   │   └── json_parser.py
│   ├── storage/            # Data storage handlers
│   │   ├── __init__.py
│   │   ├── csv_handler.py
│   │   ├── json_handler.py
│   │   └── db_handler.py
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── rate_limiter.py
│   │   ├── proxy_manager.py
│   │   └── user_agent.py
│   └── cli.py              # Command-line interface
├── config/
│   └── default.json        # Default configuration
├── data/                   # Scraped data storage
├── logs/                   # Application logs
├── tests/                  # Test suite
├── requirements.txt
├── README.md
└── .env.example
```

## Examples

### E-commerce Product Scraper

```python
from src.scrapers.ecommerce import EcommerceScraper

scraper = EcommerceScraper()
products = scraper.scrape_products("https://shop.example.com/products")

for product in products:
    print(f"{product['name']} - ${product['price']}")
```

### News Article Scraper

```python
from src.scrapers.news import NewsArticleScraper

scraper = NewsArticleScraper()
articles = scraper.scrape_articles("https://news.example.com")

scraper.save_to_json(articles, "news_articles.json")
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=src tests/
```

## Best Practices

1. **Respect robots.txt**: Always check and follow website scraping policies
2. **Rate limiting**: Use appropriate delays between requests
3. **Error handling**: Implement proper error handling and retries
4. **Data validation**: Validate scraped data before storage
5. **Logging**: Monitor scraping activities through logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and legitimate data collection purposes only. Users are responsible for complying with website terms of service and applicable laws.