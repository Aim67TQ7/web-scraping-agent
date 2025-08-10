import asyncio
import time
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin, urlparse
import logging

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

from .utils.logger import setup_logger


class WebScraper:
    """Base web scraper class with common functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the web scraper.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.session = requests.Session()
        self.ua = UserAgent()
        self.logger = setup_logger(__name__)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Configure timeout
        self.timeout = self.config.get('timeout', 30)
        
        # Configure rate limiting
        self.rate_limit = self.config.get('rate_limit', 10)
        self.rate_period = self.config.get('rate_period', 1)
        
    @sleep_and_retry
    @limits(calls=10, period=1)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_page(self, url: str, **kwargs) -> requests.Response:
        """
        Fetch a single page with retry logic and rate limiting.
        
        Args:
            url: The URL to fetch
            **kwargs: Additional arguments to pass to requests.get()
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If the request fails after retries
        """
        self.logger.info(f"Fetching: {url}")
        
        # Rotate user agent
        self.session.headers['User-Agent'] = self.ua.random
        
        # Merge kwargs with defaults
        request_kwargs = {
            'timeout': self.timeout,
            'allow_redirects': True,
        }
        request_kwargs.update(kwargs)
        
        try:
            response = self.session.get(url, **request_kwargs)
            response.raise_for_status()
            
            self.logger.info(f"Successfully fetched: {url} (Status: {response.status_code})")
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {str(e)}")
            raise
    
    def parse_html(self, html: str, parser: str = 'html.parser') -> BeautifulSoup:
        """
        Parse HTML content using BeautifulSoup.
        
        Args:
            html: HTML content as string
            parser: Parser to use (default: 'html.parser')
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, parser)
    
    def scrape_page(self, url: str, parser_func: Optional[callable] = None) -> Dict[str, Any]:
        """
        Scrape a single page and optionally parse it.
        
        Args:
            url: The URL to scrape
            parser_func: Optional function to parse the page content
            
        Returns:
            Dictionary containing scraped data
        """
        response = self.fetch_page(url)
        soup = self.parse_html(response.text)
        
        # Basic data extraction
        data = {
            'url': url,
            'title': soup.title.string if soup.title else None,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'encoding': response.encoding,
        }
        
        # Apply custom parser if provided
        if parser_func:
            parsed_data = parser_func(soup, response)
            data.update(parsed_data)
        
        return data
    
    def scrape_multiple(self, urls: List[str], parser_func: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        Scrape multiple pages.
        
        Args:
            urls: List of URLs to scrape
            parser_func: Optional function to parse each page
            
        Returns:
            List of dictionaries containing scraped data
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Scraping {i}/{len(urls)}: {url}")
            
            try:
                data = self.scrape_page(url, parser_func)
                results.append(data)
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {str(e)}")
                results.append({
                    'url': url,
                    'error': str(e),
                    'status': 'failed'
                })
        
        return results
    
    def extract_links(self, url: str, pattern: Optional[str] = None) -> List[str]:
        """
        Extract all links from a page.
        
        Args:
            url: The page URL
            pattern: Optional regex pattern to filter links
            
        Returns:
            List of absolute URLs
        """
        response = self.fetch_page(url)
        soup = self.parse_html(response.text)
        
        links = []
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(url, link['href'])
            
            # Filter by pattern if provided
            if pattern:
                import re
                if re.search(pattern, absolute_url):
                    links.append(absolute_url)
            else:
                links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates
    
    def save_to_file(self, data: Union[Dict, List], filename: str, format: str = 'json'):
        """
        Save scraped data to file.
        
        Args:
            data: Data to save
            filename: Output filename
            format: Output format ('json', 'csv', 'excel')
        """
        import json
        import csv
        import pandas as pd
        from pathlib import Path
        
        output_path = Path('data') / filename
        output_path.parent.mkdir(exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        elif format == 'csv':
            if isinstance(data, dict):
                data = [data]
            
            if data:
                keys = data[0].keys()
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
                    
        elif format == 'excel':
            df = pd.DataFrame(data if isinstance(data, list) else [data])
            df.to_excel(output_path, index=False)
        
        self.logger.info(f"Data saved to: {output_path}")
    
    def close(self):
        """Close the session."""
        self.session.close()
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()