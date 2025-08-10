#!/usr/bin/env python3
"""
Script to scrape news articles from The Kansan website.
"""

import json
import re
from pathlib import Path
from datetime import datetime

from src.scrapers.news import NewsArticleScraper
from src.utils.logger import setup_logger


def main():
    # Set up logger
    logger = setup_logger(__name__)
    
    # Initialize scraper
    logger.info("Initializing NewsArticleScraper for The Kansan")
    scraper = NewsArticleScraper()
    
    # Read the links file
    with open('thekansan_links.txt', 'r') as f:
        all_links = [line.strip() for line in f if line.strip()]
    
    # Filter for article links (exclude navigation, category pages, etc.)
    article_patterns = [
        r'/treasurer-responds-to-commission-travel-inquiry/',
        r'/newton-kansan-athletes-of-the-week-voting-opens-\d+/',
        r'/hutchinson-kraken-seattle-hays-reach-semifinals/',
        r'/back-to-school-just-around-the-corner/',
        r'/science-heroes-at-npl/',
        r'/feeling-dizzy-how-physical-therapy-can-help-you-find-your-balance/',
        r'/waymakers-keeps-going-after-pilot-project/',
        r'/county-parks-planning-swinging-bridge-repair/',
        r'/through-the-lens-music-at-the-library/',
        r'/foresters-top-lonestar-to-reach-nbc-semis/',
        r'/kansas-profile-kevin-and-christina-miller-uneak-wood/',
    ]
    
    # Get article URLs
    article_urls = []
    for link in all_links:
        # Skip category pages, navigation links, etc.
        skip_patterns = [
            r'/category/',
            r'/submit-',
            r'/about/',
            r'/login/',
            r'/digital-issues/',
            r'#',
            r'cherryroad',
            r'legacy.com',
            r'bestof.cherryroad.com'
        ]
        
        if any(pattern in link for pattern in skip_patterns):
            continue
            
        # Check if it looks like an article
        if re.search(r'/[a-z-]+-[a-z-]+/', link) and not link.endswith('/category/'):
            article_urls.append(link)
    
    logger.info(f"Found {len(article_urls)} potential article URLs")
    
    # Scrape articles
    articles = []
    for i, url in enumerate(article_urls[:10], 1):  # Limit to first 10 articles
        logger.info(f"Scraping article {i}/{min(len(article_urls), 10)}: {url}")
        
        try:
            article_data = scraper.scrape_article(url)
            articles.append(article_data)
            logger.info(f"Successfully scraped: {article_data.get('title', 'No title')}")
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")
            articles.append({
                'url': url,
                'error': str(e),
                'status': 'failed'
            })
    
    # Save results
    output_file = f'thekansan_articles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    output_path = Path('data') / output_file
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'The Kansan',
            'scrape_date': datetime.now().isoformat(),
            'articles_count': len(articles),
            'articles': articles
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(articles)} articles to {output_path}")
    
    # Print summary
    successful = sum(1 for a in articles if 'error' not in a)
    print(f"\nScraping Summary:")
    print(f"- Total articles scraped: {len(articles)}")
    print(f"- Successful: {successful}")
    print(f"- Failed: {len(articles) - successful}")
    print(f"- Output saved to: {output_path}")
    
    scraper.close()


if __name__ == '__main__':
    main()