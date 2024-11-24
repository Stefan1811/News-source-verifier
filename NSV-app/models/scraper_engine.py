import requests
from bs4 import BeautifulSoup
import logging
import time
import re
import json

# Configure logging format with timestamp
logging.basicConfig(
    filename='logs.txt',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_error(func):
    """Error-handling decorator."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{func.__name__} failed with error: {e}")
            raise e
    return wrapper

def log_execution(func):
    """Decorator for logging method execution."""
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args} and kwargs: {kwargs}")
        result = func(*args, **kwargs)
        return result
    return wrapper

class BeautifulSoupScraper:
    """A scraper class using BeautifulSoup to extract data from web pages."""

    @log_error
    @log_execution
    def extract_data(self, url):
        """Extracts data from a webpage."""
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
            except requests.RequestException as e:
                logging.error(f"Request failed (Attempt {attempt + 1}): {e}")
                time.sleep(2)
        else:
            logging.error("Failed to retrieve webpage after multiple attempts.")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        title = self.extract_text(soup, ['h1', 'title', 'div.article-title']) or "Unknown Title"
        content = self.extract_content(soup) or "No content available"
        author = self.extract_author(soup) or "Unknown Author"
        publish_date = self.extract_publish_date(soup) or "Unknown Date"

        if title == "Unknown Title" or content == "No content available":
            logging.warning(f"Essential data missing from URL: {url}")

        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "publish_date": publish_date
        }

    @log_error
    def extract_text(self, soup, selectors):
        """Extract text using a list of CSS selectors."""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None

    @log_error
    def extract_publish_date(self, soup):
        """Extracts the publish date of the article from the HTML content."""
        return (
            self.extract_published_date_metadata(soup) or
            self.extract_published_date_html(soup) or
            self.extract_published_date_json_ld(soup) or
            self.extract_published_date_regex(soup)
        )

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
                return json_data.get('dateModified')
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

    @log_error
    def extract_content(self, soup):
        """Extracts the main content of the article."""
        for tag in soup(['header', 'footer', 'nav', 'aside', 'form', 'iframe']):
            tag.decompose()  # Remove non-content elements

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
        """Cleans HTML content by removing unwanted tags."""
        for tag in content(['script', 'style', 'form', 'iframe']):
            tag.decompose()
        return content.get_text(separator="\n", strip=True)

    @log_error
    def extract_author(self, soup):
        """Extracts the author's name from metadata or HTML selectors."""
        author_metadata = soup.find('meta', attrs={'name': 'author'})
        if author_metadata:
            return author_metadata.get('content', '').strip()

        author_selectors = ['span.author', 'div.author-name', 'p.byline', 'a[rel="author"]']
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None


if __name__ == "__main__":
    scraper = BeautifulSoupScraper()
    test_url = "https://www.bbc.com/news/articles/ce8dz0n8xldo"
    article_data = scraper.extract_data(test_url)

    if article_data:
        print(f"URL: {article_data['url']}")
        print(f"Title: {article_data['title']}")
        print(f"Content: {article_data['content']}")
        print(f"Author: {article_data['author']}")
        print(f"Publish Date: {article_data['publish_date']}")
    else:
        print("Failed to extract data from the URL.")
