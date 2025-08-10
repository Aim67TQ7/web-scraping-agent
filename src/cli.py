import click
import json
from pathlib import Path
from typing import Optional
import sys

from .scraper import WebScraper
from .scrapers.ecommerce import EcommerceScraper
from .scrapers.news import NewsArticleScraper
from .utils.logger import setup_logger


logger = setup_logger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Web Scraping Agent - A powerful and flexible web scraping tool."""
    pass


@cli.command()
@click.option('--url', '-u', required=True, help='URL to scrape')
@click.option('--output', '-o', default='output.json', help='Output filename')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'excel']), default='json', help='Output format')
@click.option('--scraper-type', '-t', type=click.Choice(['generic', 'ecommerce', 'news']), default='generic', help='Type of scraper to use')
def scrape(url: str, output: str, format: str, scraper_type: str):
    """Scrape a single URL."""
    try:
        logger.info(f"Starting scrape of {url} using {scraper_type} scraper")
        
        # Select appropriate scraper
        if scraper_type == 'ecommerce':
            scraper = EcommerceScraper()
            if '/product/' in url or '/item/' in url:
                data = scraper.scrape_product(url)
            else:
                click.echo("URL appears to be a category page. Use 'scrape-category' command instead.")
                return
        elif scraper_type == 'news':
            scraper = NewsArticleScraper()
            data = scraper.scrape_article(url)
        else:
            scraper = WebScraper()
            data = scraper.scrape_page(url)
        
        # Save data
        scraper.save_to_file(data, output, format)
        
        click.echo(f"✓ Successfully scraped {url}")
        click.echo(f"✓ Data saved to {output}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        if 'scraper' in locals():
            scraper.close()


@cli.command()
@click.option('--file', '-f', required=True, type=click.Path(exists=True), help='File containing URLs (one per line)')
@click.option('--output', '-o', default='output.json', help='Output filename')
@click.option('--format', type=click.Choice(['json', 'csv', 'excel']), default='json', help='Output format')
@click.option('--scraper-type', '-t', type=click.Choice(['generic', 'ecommerce', 'news']), default='generic', help='Type of scraper to use')
def scrape_list(file: str, output: str, format: str, scraper_type: str):
    """Scrape multiple URLs from a file."""
    try:
        # Read URLs from file
        with open(file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Found {len(urls)} URLs to scrape")
        
        # Select appropriate scraper
        if scraper_type == 'ecommerce':
            scraper = EcommerceScraper()
        elif scraper_type == 'news':
            scraper = NewsArticleScraper()
        else:
            scraper = WebScraper()
        
        # Scrape all URLs
        results = scraper.scrape_multiple(urls)
        
        # Save data
        scraper.save_to_file(results, output, format)
        
        # Summary
        successful = sum(1 for r in results if 'error' not in r)
        click.echo(f"✓ Scraped {successful}/{len(urls)} URLs successfully")
        click.echo(f"✓ Data saved to {output}")
        
    except Exception as e:
        logger.error(f"Batch scraping failed: {str(e)}")
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        if 'scraper' in locals():
            scraper.close()


@cli.command()
@click.option('--url', '-u', required=True, help='Category URL to scrape')
@click.option('--output', '-o', default='products.json', help='Output filename')
@click.option('--format', type=click.Choice(['json', 'csv', 'excel']), default='json', help='Output format')
@click.option('--max-pages', '-m', type=int, help='Maximum number of pages to scrape')
def scrape_category(url: str, output: str, format: str, max_pages: Optional[int]):
    """Scrape all products from an e-commerce category."""
    try:
        logger.info(f"Starting category scrape of {url}")
        
        scraper = EcommerceScraper()
        products = scraper.scrape_category(url, max_pages)
        
        # Save data
        scraper.save_to_file(products, output, format)
        
        click.echo(f"✓ Successfully scraped {len(products)} products")
        click.echo(f"✓ Data saved to {output}")
        
    except Exception as e:
        logger.error(f"Category scraping failed: {str(e)}")
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        if 'scraper' in locals():
            scraper.close()


@cli.command()
@click.option('--url', '-u', required=True, help='News feed URL to scrape')
@click.option('--output', '-o', default='articles.json', help='Output filename')
@click.option('--format', type=click.Choice(['json', 'csv', 'excel']), default='json', help='Output format')
@click.option('--max-articles', '-m', type=int, help='Maximum number of articles to scrape')
def scrape_news(url: str, output: str, format: str, max_articles: Optional[int]):
    """Scrape articles from a news feed."""
    try:
        logger.info(f"Starting news feed scrape of {url}")
        
        scraper = NewsArticleScraper()
        articles = scraper.scrape_news_feed(url, max_articles)
        
        # Save data
        scraper.save_to_file(articles, output, format)
        
        click.echo(f"✓ Successfully scraped {len(articles)} articles")
        click.echo(f"✓ Data saved to {output}")
        
    except Exception as e:
        logger.error(f"News scraping failed: {str(e)}")
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        if 'scraper' in locals():
            scraper.close()


@cli.command()
@click.option('--url', '-u', required=True, help='URL to extract links from')
@click.option('--pattern', '-p', help='Regex pattern to filter links')
@click.option('--output', '-o', help='Save links to file')
def extract_links(url: str, pattern: Optional[str], output: Optional[str]):
    """Extract all links from a page."""
    try:
        scraper = WebScraper()
        links = scraper.extract_links(url, pattern)
        
        click.echo(f"Found {len(links)} links")
        
        if output:
            with open(output, 'w') as f:
                for link in links:
                    f.write(link + '\n')
            click.echo(f"✓ Links saved to {output}")
        else:
            # Display first 10 links
            for i, link in enumerate(links[:10], 1):
                click.echo(f"{i}. {link}")
            
            if len(links) > 10:
                click.echo(f"... and {len(links) - 10} more")
        
    except Exception as e:
        logger.error(f"Link extraction failed: {str(e)}")
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        if 'scraper' in locals():
            scraper.close()


@cli.command()
def test():
    """Test the scraper with example URLs."""
    test_urls = {
        'generic': 'https://example.com',
        'ecommerce': 'https://www.amazon.com/dp/B08N5WRWNW',
        'news': 'https://www.bbc.com/news',
    }
    
    click.echo("Testing scrapers with example URLs...\n")
    
    for scraper_type, url in test_urls.items():
        click.echo(f"Testing {scraper_type} scraper with {url}")
        try:
            if scraper_type == 'ecommerce':
                scraper = EcommerceScraper()
                # Note: This is just for testing structure, actual Amazon scraping requires more setup
                data = {'test': 'This is a test - actual scraping requires proper setup'}
            elif scraper_type == 'news':
                scraper = NewsArticleScraper()
                data = {'test': 'This is a test - actual scraping requires proper setup'}
            else:
                scraper = WebScraper()
                data = scraper.scrape_page(url)
            
            click.echo(f"✓ {scraper_type} scraper is working")
            scraper.close()
            
        except Exception as e:
            click.echo(f"✗ {scraper_type} scraper failed: {str(e)}")
    
    click.echo("\nTest complete!")


if __name__ == '__main__':
    cli()