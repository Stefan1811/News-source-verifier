from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from newspaper import Article


class Scraper(ABC):
    """Abstract Scraper class for web scraping."""

    @abstractmethod
    def extract_data(self, url):
        pass

    def process_data(self, data):
        """Method for transforming data into a specified format after extraction."""
        pass

    def validate_data(self, data):
        """Method for validating extracted data consistency and structure."""
        pass

    def handle_error(self, error):
        """Method for error handling during scraping."""
        pass


class BeautifulSoupScraper(Scraper):
    def extract_data(self, url):
        response = requests.get(url)

        if response.status_code != 200:
            self.handle_error(f"Failed to retrieve the webpage: {url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        title_selector = 'h1'
        content_selector = 'div.article-content'
        author_selector = 'span.author'
        publish_date_selector = 'time.publish-date'

        title = soup.select_one(title_selector).text.strip() if soup.select_one(title_selector) else "Unknown Title"
        content = soup.select_one(content_selector).text.strip() if soup.select_one(
            content_selector) else "No content available"
        author = soup.select_one(author_selector).text.strip() if soup.select_one(author_selector) else "Unknown Author"
        publish_date = soup.select_one(publish_date_selector).text.strip() if soup.select_one(
            publish_date_selector) else "Unknown Date"

        return url, title, content, author, publish_date
    def process_data(self, data):
        url, title, content, author, publish_date = data
        article = Article(url)
        article.title = title
        article.text = content
        article.authors = [author]
        article.publish_date = publish_date
        return article
class TweepyScraper(Scraper):
    def extract_data(self, url):
        pass


class TwarcScraper(Scraper):
    def extract_data(self, url):
        pass


class ScraperFactory:
    @staticmethod
    def create_scraper(scraper_type, **kwargs):
        scraper = None
        if scraper_type == 'beautifulsoup':
            scraper = BeautifulSoupScraper()
        elif scraper_type == 'tweepy':
            scraper = TweepyScraper()
        elif scraper_type == 'twarc':
            scraper = TwarcScraper()
        else:
            raise ValueError('Invalid scraper type')
        return scraper
