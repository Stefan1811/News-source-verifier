from abc import ABC, abstractmethod
import requests
import os 
import sys 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.article import Article
from bs4 import BeautifulSoup
import time
import logging
import re
import json

class Scraper(ABC):
    """Abstract Scraper class for web scraping."""

    @abstractmethod
    def extract_data(self, url):
        pass

    def process_data(self, data):
        """Method for transforming data into a specified format after extraction."""
        pass

    def handle_error(self, error):
        """Method for error handling during scraping."""
        pass


class BeautifulSoupScraper(Scraper):
    def extract_data(self, url):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/87.0.4280.88 Safari/537.36"
            )
        }

        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    break
                else:
                    self.handle_error(
                        f"Attempt {attempt + 1}: Failed to retrieve the webpage. "
                        f"Status code: {response.status_code}"
                    )
                    time.sleep(2)
            except requests.RequestException as e:
                self.handle_error(
                    f"Attempt {attempt + 1}: Network error occurred - {e}"
                )
                time.sleep(2)
        else:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        title_selectors = ['h1', 'title', 'div.article-title']
        content_selectors = [
            'div.article-content', 'div.content-body', 'div.post-content'
        ]

        def extract_text(selectors):
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        return element.get('content', '').strip()
                    return element.get_text(strip=True)
            return None

        title = extract_text(title_selectors) or "Unknown Title"
        content = self.extract_content(soup) or "No content available"
        author = self.extract_author(soup) or "Unknown Author"
        publish_date = self.extract_publish_date(soup) or "Unknown Date"

        if title == "Unknown Title" or content == "No content available":
            logging.warning(f"Essential data missing from URL: {url}")

        return url, title, content, author, publish_date

    def extract_publish_date(self, soup):
        """Extracts the publish date of the article from the HTML content. """
        publish_date = (
            self.extract_published_date_metadata(soup) or
            self.extract_published_date_html(soup) or
            self.extract_published_date_json_ld(soup) or
            self.extract_published_date_regex(soup)
        )
        return publish_date

    def extract_published_date_metadata(self, soup):
        """Extract the published date from metadata tags."""
        date_tag = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_tag:
            return date_tag.get('content', '').strip()
        return None

    def extract_published_date_html(self, soup):
        """Extract the published date from HTML selectors."""
        date_selectors = [
            'time.publish-date', 'span.date', 'div.pub-date',
            'meta[property="article:published_time"]', 'meta[name="publish-date"]', 'meta[name="dcterms.modified"]'
        ]
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True) if element.name != 'meta' else element.get('content', '').strip()
        return None
    def extract_published_date_json_ld(self, soup):
        """Extract the dateModified from JSON-LD metadata."""
        json_ld_script = soup.find("script", type="application/ld+json")
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.string)
                if isinstance(json_data, list):
                    json_data = json_data[0]  # Handle array case
                return json_data.get('dateModified')  # Return dateModified instead of datePublished
            except json.JSONDecodeError:
                logging.warning("Failed to decode JSON-LD data for published date extraction.")
        return None

    def extract_published_date_regex(self, soup):
        """Extract the published date using regex patterns."""
        date_patterns = [re.compile(r'Published on\s+(\w+\s\d{1,2},\s\d{4})')]
        text = soup.get_text(separator=' ', strip=True)
        for pattern in date_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None

    def extract_content(self, soup):
        # Exclude common non-article sections
        for tag in soup(['header', 'footer', 'nav', 'aside', 'form', 'iframe']):
            tag.decompose()

        content_selectors = ['div.article-content', 'div.content-body', 'div.post-content']
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element)

        paragraphs = soup.find_all('p')
        filtered_paragraphs = [
            p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50
        ]
        return "\n".join(filtered_paragraphs) if filtered_paragraphs else None

    def clean_text(self, content):
        """Clean text by removing unnecessary whitespace and non-content elements."""
        for tag in content(['script', 'style', 'form', 'iframe']):
            tag.decompose()  # Remove scripts, styles, forms, and iframes
        return content.get_text(separator="\n", strip=True)

    def extract_author(self, soup):
        """
        Attempts to extract the author's name using different strategies:
        JSON-LD metadata, HTML selectors, or byline patterns, in that order.
        """
        extraction_methods = [
            ('metadata', self.extract_author_metadata),
            ('JSON-LD', self.extract_author_json_ld),
            ('HTML selectors', self.extract_author_html),
            ('regex patterns', self.extract_author_regex)
        ]

        for method_name, method in extraction_methods:
            author = method(soup)
            if author:
                logging.debug(f"Author extracted using {method_name}.")
                return author

        logging.info("Author not found using any predefined methods.")
        return None

    def extract_author_metadata(self, soup):
        article_tags = soup.find_all('meta', attrs={'property': re.compile(r'.*author.*', re.I)})
        for tag in article_tags:
            author = tag.get('content', '').strip()
            if author:
                return author

    def extract_author_html(self, soup):
        author_selectors = [
            'span.author', 'div.author-name', 'p.byline',
            'a[rel="author"]', 'meta[name="author"]'
        ]
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)

    def extract_author_regex(self, soup):
        byline_patterns = [
            re.compile(r'By\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)'),
            re.compile(r'Written by\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)')
        ]
        text = soup.get_text(separator=' ', strip=True)
        for pattern in byline_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
    def extract_author_json_ld(self, soup):
        json_ld_script = soup.find("script", type="application/ld+json")
        if json_ld_script:
            try:
                json_data = json.loads(json_ld_script.string)
                if isinstance(json_data, list):
                    json_data = json_data[0]  # In case it's an array
                if "author" in json_data:
                    author_data = json_data["author"]
                    # Check if author_data is a list and extract from the first item if it is
                    if isinstance(author_data, list) and len(author_data) > 0:
                        author_data = author_data[0]
                    if isinstance(author_data, dict) and "name" in author_data:
                        return author_data["name"].strip()
                    elif isinstance(author_data, str):
                        return author_data.strip()
            except json.JSONDecodeError:
                logging.warning("Failed to decode JSON-LD data for author extraction.")

    def process_data(self, data):
        """Process the extracted data into an Article object."""
        url, title, content, author, publish_date = data
        article = Article(url, title, content, [author], publish_date)
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


#main to test
if __name__ == '__main__':
    url = "https://www.bbc.com/news/articles/ce8dz0n8xldo"
    scraper = ScraperFactory.create_scraper('beautifulsoup')
    data = scraper.extract_data(url)
    if data:
        article = scraper.process_data(data)
        #print all the data
        print(article.url)
        print(article.title)
        print(article.content)
        print(article.author)
        print(article.publish_date)
    else:
        print("Failed to extract data from the URL.")