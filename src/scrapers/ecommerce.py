from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup, Tag
from ..scraper import WebScraper


class EcommerceScraper(WebScraper):
    """Scraper specialized for e-commerce websites."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger.info("Initialized EcommerceScraper")
    
    def scrape_product(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single product page.
        
        Args:
            url: Product page URL
            
        Returns:
            Dictionary containing product information
        """
        response = self.fetch_page(url)
        soup = self.parse_html(response.text)
        
        product_data = {
            'url': url,
            'name': self._extract_product_name(soup),
            'price': self._extract_price(soup),
            'currency': self._extract_currency(soup),
            'description': self._extract_description(soup),
            'images': self._extract_images(soup, url),
            'availability': self._extract_availability(soup),
            'rating': self._extract_rating(soup),
            'reviews_count': self._extract_reviews_count(soup),
            'specifications': self._extract_specifications(soup),
            'breadcrumbs': self._extract_breadcrumbs(soup),
        }
        
        return product_data
    
    def scrape_category(self, url: str, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Scrape all products from a category page.
        
        Args:
            url: Category page URL
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product dictionaries
        """
        products = []
        current_url = url
        page_count = 0
        
        while current_url and (max_pages is None or page_count < max_pages):
            self.logger.info(f"Scraping category page {page_count + 1}: {current_url}")
            
            response = self.fetch_page(current_url)
            soup = self.parse_html(response.text)
            
            # Extract product URLs from listing
            product_urls = self._extract_product_urls(soup, current_url)
            
            # Scrape each product
            for product_url in product_urls:
                try:
                    product_data = self.scrape_product(product_url)
                    products.append(product_data)
                except Exception as e:
                    self.logger.error(f"Failed to scrape product {product_url}: {str(e)}")
            
            # Get next page URL
            current_url = self._get_next_page_url(soup, current_url)
            page_count += 1
        
        return products
    
    def _extract_product_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product name using common patterns."""
        selectors = [
            'h1[itemprop="name"]',
            'h1.product-name',
            'h1.product-title',
            '[data-testid="product-title"]',
            'h1',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product price."""
        selectors = [
            '[itemprop="price"]',
            '.price-now',
            '.product-price',
            '[data-testid="product-price"]',
            '.price',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract numeric price
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    return float(price_match.group())
        
        return None
    
    def _extract_currency(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract currency from price or meta tags."""
        # Check meta tags first
        meta_currency = soup.find('meta', {'itemprop': 'priceCurrency'})
        if meta_currency:
            return meta_currency.get('content')
        
        # Common currency symbols
        currency_map = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR',
        }
        
        price_elements = soup.select('[itemprop="price"], .price, .product-price')
        for element in price_elements:
            text = element.get_text()
            for symbol, currency in currency_map.items():
                if symbol in text:
                    return currency
        
        return 'USD'  # Default
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description."""
        selectors = [
            '[itemprop="description"]',
            '.product-description',
            '[data-testid="product-description"]',
            '#product-description',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product images."""
        images = []
        
        # Common image selectors
        selectors = [
            'img[itemprop="image"]',
            '.product-image img',
            '.product-photo img',
            '[data-testid="product-image"] img',
        ]
        
        for selector in selectors:
            for img in soup.select(selector):
                src = img.get('src') or img.get('data-src')
                if src:
                    absolute_url = urljoin(base_url, src)
                    images.append(absolute_url)
        
        return list(set(images))  # Remove duplicates
    
    def _extract_availability(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product availability."""
        # Check schema.org markup
        availability_meta = soup.find('link', {'itemprop': 'availability'})
        if availability_meta:
            href = availability_meta.get('href', '')
            if 'InStock' in href:
                return 'In Stock'
            elif 'OutOfStock' in href:
                return 'Out of Stock'
        
        # Check common text patterns
        availability_selectors = [
            '.availability',
            '.stock-status',
            '[data-testid="availability"]',
        ]
        
        for selector in availability_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True).lower()
                if 'in stock' in text or 'available' in text:
                    return 'In Stock'
                elif 'out of stock' in text or 'unavailable' in text:
                    return 'Out of Stock'
        
        return None
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product rating."""
        # Check schema.org markup
        rating_elem = soup.find('span', {'itemprop': 'ratingValue'})
        if rating_elem:
            try:
                return float(rating_elem.get_text(strip=True))
            except ValueError:
                pass
        
        # Check common rating patterns
        rating_selectors = [
            '.rating-value',
            '.star-rating',
            '[data-testid="rating"]',
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                # Try to extract rating from text or attributes
                rating_text = element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/)\s*5', rating_text)
                if rating_match:
                    return float(rating_match.group(1))
                
                # Check aria-label or title
                for attr in ['aria-label', 'title']:
                    attr_value = element.get(attr, '')
                    rating_match = re.search(r'(\d+\.?\d*)', attr_value)
                    if rating_match:
                        return float(rating_match.group(1))
        
        return None
    
    def _extract_reviews_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of reviews."""
        selectors = [
            '[itemprop="reviewCount"]',
            '.review-count',
            '.reviews-count',
            '[data-testid="review-count"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                count_text = element.get_text(strip=True)
                count_match = re.search(r'(\d+)', count_text.replace(',', ''))
                if count_match:
                    return int(count_match.group(1))
        
        return None
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product specifications."""
        specs = {}
        
        # Common specification table selectors
        spec_selectors = [
            '.product-specs table',
            '.specifications table',
            '[data-testid="specifications"] table',
        ]
        
        for selector in spec_selectors:
            table = soup.select_one(selector)
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        specs[key] = value
                break
        
        # Also check definition lists
        dl_elements = soup.find_all('dl', class_=re.compile('spec|feature'))
        for dl in dl_elements:
            dt_elements = dl.find_all('dt')
            dd_elements = dl.find_all('dd')
            for dt, dd in zip(dt_elements, dd_elements):
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                specs[key] = value
        
        return specs
    
    def _extract_breadcrumbs(self, soup: BeautifulSoup) -> List[str]:
        """Extract breadcrumb navigation."""
        breadcrumbs = []
        
        # Check schema.org markup
        breadcrumb_list = soup.find('ol', {'itemtype': 'https://schema.org/BreadcrumbList'})
        if breadcrumb_list:
            items = breadcrumb_list.find_all('li', {'itemprop': 'itemListElement'})
            for item in items:
                name_elem = item.find(attrs={'itemprop': 'name'})
                if name_elem:
                    breadcrumbs.append(name_elem.get_text(strip=True))
        else:
            # Common breadcrumb selectors
            selectors = [
                '.breadcrumb',
                '.breadcrumbs',
                '[data-testid="breadcrumbs"]',
            ]
            
            for selector in selectors:
                breadcrumb_elem = soup.select_one(selector)
                if breadcrumb_elem:
                    links = breadcrumb_elem.find_all('a')
                    breadcrumbs = [link.get_text(strip=True) for link in links]
                    break
        
        return breadcrumbs
    
    def _extract_product_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product URLs from a category/listing page."""
        urls = []
        
        # Common product link selectors
        selectors = [
            'a.product-link',
            'a.product-item-link',
            '.product-item a',
            '[data-testid="product-link"]',
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href:
                        absolute_url = urljoin(base_url, href)
                        urls.append(absolute_url)
                break
        
        return list(set(urls))  # Remove duplicates
    
    def _get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """Get the URL of the next page in pagination."""
        # Common next page selectors
        selectors = [
            'a.next',
            'a[rel="next"]',
            '.pagination .next a',
            '[data-testid="pagination-next"]',
        ]
        
        for selector in selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get('href'):
                return urljoin(current_url, next_link['href'])
        
        return None