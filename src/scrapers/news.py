from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
import re

from bs4 import BeautifulSoup
from ..scraper import WebScraper


class NewsArticleScraper(WebScraper):
    """Scraper specialized for news websites and articles."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger.info("Initialized NewsArticleScraper")
    
    def scrape_article(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single news article.
        
        Args:
            url: Article URL
            
        Returns:
            Dictionary containing article information
        """
        response = self.fetch_page(url)
        soup = self.parse_html(response.text)
        
        article_data = {
            'url': url,
            'title': self._extract_title(soup),
            'author': self._extract_author(soup),
            'publish_date': self._extract_publish_date(soup),
            'content': self._extract_content(soup),
            'summary': self._extract_summary(soup),
            'categories': self._extract_categories(soup),
            'tags': self._extract_tags(soup),
            'images': self._extract_article_images(soup, url),
            'videos': self._extract_videos(soup, url),
            'related_articles': self._extract_related_articles(soup, url),
            'comments_count': self._extract_comments_count(soup),
            'meta_description': self._extract_meta_description(soup),
            'keywords': self._extract_keywords(soup),
        }
        
        return article_data
    
    def scrape_news_feed(self, url: str, max_articles: int = None) -> List[Dict[str, Any]]:
        """
        Scrape articles from a news feed or category page.
        
        Args:
            url: Feed URL
            max_articles: Maximum number of articles to scrape
            
        Returns:
            List of article dictionaries
        """
        articles = []
        article_urls = self._extract_article_urls_from_feed(url)
        
        # Limit articles if specified
        if max_articles:
            article_urls = article_urls[:max_articles]
        
        for i, article_url in enumerate(article_urls, 1):
            self.logger.info(f"Scraping article {i}/{len(article_urls)}: {article_url}")
            
            try:
                article_data = self.scrape_article(article_url)
                articles.append(article_data)
            except Exception as e:
                self.logger.error(f"Failed to scrape article {article_url}: {str(e)}")
                articles.append({
                    'url': article_url,
                    'error': str(e),
                    'status': 'failed'
                })
        
        return articles
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title."""
        # Try Open Graph first
        og_title = soup.find('meta', {'property': 'og:title'})
        if og_title:
            return og_title.get('content', '').strip()
        
        # Common title selectors
        selectors = [
            'h1[itemprop="headline"]',
            'h1.article-title',
            'h1.entry-title',
            'h1.post-title',
            '[data-testid="article-title"]',
            'article h1',
            'h1',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        # Check schema.org markup
        author_elem = soup.find(attrs={'itemprop': 'author'})
        if author_elem:
            # Could be nested in a span with itemprop="name"
            name_elem = author_elem.find(attrs={'itemprop': 'name'})
            if name_elem:
                return name_elem.get_text(strip=True)
            return author_elem.get_text(strip=True)
        
        # Common author selectors
        selectors = [
            '.author-name',
            '.by-author',
            '.article-author',
            '[data-testid="author-name"]',
            'span.author',
            'p.author',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                author_text = element.get_text(strip=True)
                # Clean up common patterns
                author_text = re.sub(r'^by\s+', '', author_text, flags=re.IGNORECASE)
                return author_text
        
        return None
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article publish date."""
        # Try different date formats
        date_properties = [
            'datePublished',
            'dateCreated',
            'publishDate',
        ]
        
        for prop in date_properties:
            date_elem = soup.find(attrs={'itemprop': prop})
            if date_elem:
                # Check datetime attribute first
                if date_elem.get('datetime'):
                    return date_elem['datetime']
                # Then content attribute
                elif date_elem.get('content'):
                    return date_elem['content']
                # Finally text content
                else:
                    return date_elem.get_text(strip=True)
        
        # Check meta tags
        meta_selectors = [
            {'property': 'article:published_time'},
            {'name': 'publish_date'},
            {'name': 'publication_date'},
        ]
        
        for selector in meta_selectors:
            meta = soup.find('meta', selector)
            if meta and meta.get('content'):
                return meta['content']
        
        # Common date selectors
        selectors = [
            'time[datetime]',
            '.publish-date',
            '.article-date',
            '.post-date',
            '[data-testid="publish-date"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.get('datetime'):
                    return element['datetime']
                return element.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main article content."""
        # Common article body selectors
        selectors = [
            '[itemprop="articleBody"]',
            '.article-body',
            '.article-content',
            '.entry-content',
            '.post-content',
            '[data-testid="article-body"]',
            'article .content',
            'article',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Remove script and style elements
                for script in element(['script', 'style']):
                    script.decompose()
                
                # Get text with proper spacing
                paragraphs = element.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6'])
                content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                
                if content:
                    return content
        
        return None
    
    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article summary or description."""
        # Check meta description
        meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # Check for explicit summary
        selectors = [
            '[itemprop="description"]',
            '.article-summary',
            '.article-excerpt',
            '.post-excerpt',
            '[data-testid="article-summary"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None
    
    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract article categories."""
        categories = []
        
        # Check schema.org markup
        category_elems = soup.find_all(attrs={'itemprop': 'articleSection'})
        categories.extend(elem.get_text(strip=True) for elem in category_elems)
        
        # Common category selectors
        selectors = [
            '.article-category',
            '.post-category',
            '.category-tag',
            '[data-testid="article-category"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            categories.extend(elem.get_text(strip=True) for elem in elements)
        
        return list(set(categories))  # Remove duplicates
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags."""
        tags = []
        
        # Check for keywords in itemprop
        keyword_elems = soup.find_all(attrs={'itemprop': 'keywords'})
        for elem in keyword_elems:
            # Could be comma-separated
            tag_text = elem.get_text(strip=True)
            if ',' in tag_text:
                tags.extend(t.strip() for t in tag_text.split(','))
            else:
                tags.append(tag_text)
        
        # Common tag selectors
        selectors = [
            '.article-tag',
            '.post-tag',
            '.tag',
            '[data-testid="article-tag"]',
            'a[rel="tag"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            tags.extend(elem.get_text(strip=True) for elem in elements)
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_article_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from article with captions."""
        images = []
        
        # Find images in article content
        content_selectors = [
            '.article-content img',
            '.article-body img',
            'article img',
            'figure img',
        ]
        
        for selector in content_selectors:
            for img in soup.select(selector):
                image_data = {
                    'url': urljoin(base_url, img.get('src', '')),
                    'alt': img.get('alt', ''),
                    'caption': None,
                }
                
                # Try to find caption
                parent_figure = img.find_parent('figure')
                if parent_figure:
                    figcaption = parent_figure.find('figcaption')
                    if figcaption:
                        image_data['caption'] = figcaption.get_text(strip=True)
                
                if image_data['url']:
                    images.append(image_data)
        
        return images
    
    def _extract_videos(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract embedded videos."""
        videos = []
        
        # YouTube embeds
        youtube_iframes = soup.find_all('iframe', src=re.compile(r'youtube\.com|youtu\.be'))
        for iframe in youtube_iframes:
            videos.append({
                'type': 'youtube',
                'url': iframe.get('src', ''),
                'title': iframe.get('title', ''),
            })
        
        # Video tags
        for video in soup.find_all('video'):
            video_data = {
                'type': 'html5',
                'sources': [],
            }
            
            # Get all sources
            for source in video.find_all('source'):
                video_data['sources'].append({
                    'url': urljoin(base_url, source.get('src', '')),
                    'type': source.get('type', ''),
                })
            
            if video_data['sources']:
                videos.append(video_data)
        
        return videos
    
    def _extract_related_articles(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract related article links."""
        related = []
        
        # Common related article selectors
        selectors = [
            '.related-articles a',
            '.related-posts a',
            '.more-articles a',
            '[data-testid="related-articles"] a',
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    related.append({
                        'title': link.get_text(strip=True),
                        'url': urljoin(base_url, href),
                    })
            
            if related:  # Stop if we found related articles
                break
        
        return related
    
    def _extract_comments_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of comments."""
        # Common comment count selectors
        selectors = [
            '.comments-count',
            '.comment-count',
            '[data-testid="comments-count"]',
            '.disqus-comment-count',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                count_text = element.get_text(strip=True)
                # Extract number
                match = re.search(r'(\d+)', count_text)
                if match:
                    return int(match.group(1))
        
        return None
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        meta = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
        if meta:
            return meta.get('content', '').strip()
        return None
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract meta keywords."""
        meta = soup.find('meta', {'name': 'keywords'})
        if meta:
            keywords = meta.get('content', '')
            return [k.strip() for k in keywords.split(',') if k.strip()]
        return []
    
    def _extract_article_urls_from_feed(self, feed_url: str) -> List[str]:
        """Extract article URLs from a news feed page."""
        response = self.fetch_page(feed_url)
        soup = self.parse_html(response.text)
        
        article_urls = []
        
        # Common article link patterns
        selectors = [
            'article a[href]',
            '.article-link',
            '.post-title a',
            'h2 a',
            'h3 a',
            '[data-testid="article-link"]',
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    absolute_url = urljoin(feed_url, href)
                    # Basic filtering to avoid non-article links
                    if not any(skip in absolute_url.lower() for skip in ['tag/', 'category/', 'author/', '#']):
                        article_urls.append(absolute_url)
        
        return list(set(article_urls))  # Remove duplicates