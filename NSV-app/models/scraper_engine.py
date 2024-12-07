import urllib
from copy import deepcopy
from functools import wraps
import requests
from bs4 import BeautifulSoup
import logging
import time
import re
import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.aop_wrapper import Aspect


class ScrapperMonitor:
    def __init__(self, validate=None, clean=None):
        """
        ScrapperMonitor will take validate and clean functions as arguments.
        """
        self.validate = validate
        self.clean = clean

    def __call__(self, func):
        """
        This allows ScrapperMonitor to be used as a decorator with the given validate and clean functions.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # First, attempt to apply the validation
            try:
                if self.validate:
                    self.validate(*args, **kwargs)  # Apply the validation
            except Exception as e:
                print(f"Validation failed: {e}")

                if self.clean:
                    print("Applying cleaning function...")
                    self.clean(*args, **kwargs)  # Apply the cleaning

                # Re-raise the exception after cleaning
                raise e

            # If validation passes, call the original function
            return func(*args, **kwargs)

        return wrapper

def validate_url(*args, **kwargs):
    """Validates the URL format and checks if it's accessible."""
    print("EXECUTING VALIDATE - URL")
    url = kwargs.get('url') or args[1]
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    if not re.match(url_pattern, url):
        raise ValueError(f"Invalid URL format: {url}")
def validate_soup(*args, **kwargs):
    """Validates the soup object before extraction."""
    print("EXECUTING VALIDATE - soup")
    soup = kwargs.get('soup')
    if soup is None and len(args) >= 2:
        soup = args[1]  # Assuming the second argument is soup
    if soup is None:
        raise ValueError("Invalid soup object: None")
    if not isinstance(soup, BeautifulSoup):
        raise ValueError(f"Invalid soup object.")

# Validates the CSS selector before extraction
def validate_selectors(*args, **kwargs):
    """Validates the CSS selector before extraction."""
    print("EXECUTING VALIDATE - Selectors")
    selectors = kwargs.get('selectors') or args[2]
    for i, sel in enumerate(selectors):
        if not isinstance(sel, str):
            raise ValueError(f"Invalid selector at index {i}: {sel} is not a string.")
        cleaned_sel = sel.strip()
        if sel != cleaned_sel:
            print(f"Selector with leading/trailing spaces: {sel}")
            raise ValueError(f"Selector at index {i} contains leading/trailing spaces: {sel}")
    return selectors


@Aspect.log_execution
@Aspect.measure_time
@Aspect.handle_exceptions
def clean_url(*args, **kwargs):
    """Removes unnecessary query parameters from URLs."""
    print("EXECUTING CLEAN - URL")
    url = kwargs.get('url') or args[1]
    logging.info(f"Cleaning URL: {url}")
    parsed_url = urllib.parse.urlparse(url)
    cleaned_url = urllib.parse.urlunparse(parsed_url._replace(query=''))
    kwargs['url'] = cleaned_url  # Pass the cleaned URL to the next function
    print(f"Cleaned URL: {cleaned_url}")

@Aspect.log_execution
@Aspect.measure_time
@Aspect.handle_exceptions
def clean_selectors(*args, **kwargs):
    """Cleans the CSS selector before extraction."""
    print("EXECUTING CLEAN - Selectors")
    selectors = kwargs.get('selectors') or args[2]
    for i, sel in enumerate(selectors):
        temp_sel = deepcopy(sel)
        selectors[i] = str(sel).strip()
        if selectors[i] != temp_sel:
            print(f"Selector cleaned: {temp_sel} -> {selectors[i]}")

class BeautifulSoupScraper:
    """A scraper class using BeautifulSoup to extract data from web pages."""

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_url, clean=clean_url)
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

        title = self.extract_title(soup) or "Unknown Title"
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

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def extract_title(self, soup):
        """Extract title from HTML, JSON-LD, or metadata."""

        # First, try to extract the title from the article (e.g., from <h1>, <h2>, etc.)
        title = self.extract_title_from_article(soup)
        if title:
            logging.debug(f"Title found in article: {title}")
            return title

        # If no article title found, try to extract from JSON-LD
        title = self.extract_title_from_json_ld(soup)
        if title:
            logging.debug(f"Title found in JSON-LD: {title}")
            return title

        # If still no title, try extracting from metadata (og:title, meta[name="title"])
        title = self.extract_title_from_metadata(soup)
        if title:
            logging.debug(f"Title found in metadata: {title}")
            return title

        # Finally, fallback to the <title> tag in HTML (usually the page title)
        title = soup.title.string if soup.title else None
        if title:
            logging.debug(f"Title found in <title> tag: {title}")
            return title

        # If no title found, return the default fallback
        logging.warning("No title found in any source, using default.")
        return "Unknown Title"

    def extract_title_from_article(self, soup):
        """Try extracting the article's title from HTML (e.g., <h1>, <h2>, etc.)."""
        title = self.extract_text(soup, ['h1', 'h2', 'div.article-title'])
        return title

    def extract_title_from_json_ld(self, soup):
        """Extract title from JSON-LD data."""
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        if not json_ld_scripts:
            return None

        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, list):
                    for item in json_data:
                        if item.get('@type') in {"NewsArticle", "Article"}:
                            title = item.get('headline') or item.get('name')
                            if title:
                                return title
                elif isinstance(json_data, dict):
                    if json_data.get('@type') in {"NewsArticle", "Article"}:
                        title = json_data.get('headline') or json_data.get('name')
                        if title:
                            return title
            except json.JSONDecodeError:
                logging.warning("Failed to decode JSON-LD script.")
        return None

    def extract_title_from_metadata(self, soup):
        """Extract title from metadata tags (og:title, meta[name="title"])."""
        meta_tag = soup.find('meta', attrs={'property': 'og:title'}) or \
                   soup.find('meta', attrs={'name': 'title'})
        if meta_tag:
            return meta_tag.get('content', '').strip()
        return None


    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_selectors, clean=clean_selectors)
    @ScrapperMonitor(validate=validate_soup)
    def extract_text(self, soup, selectors):
        """Extract text using a list of CSS selectors."""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_publish_date(self, soup):
        """Extracts the publishing date of the article from the HTML content."""
        return (
                self.extract_published_date_json_ld(soup) or
                self.extract_published_date_metadata(soup) or
                self.extract_published_date_html(soup) or
                self.extract_published_date_regex(soup)
        )

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_published_date_metadata(self, soup):
        """Extract the published date from metadata tags."""
        date_tag = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_tag:
            return date_tag.get('content', '').strip()
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_published_date_html(self, soup):
        """Extract the published date from HTML selectors."""
        date_selectors = [
            'time.publish-date   ', 'span.date', 'div.pub-date',
            'meta[property="article:published_time"]', 'meta[name="publish-date"]', 'meta[name="dcterms.modified"]'
        ]
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True) if element.name != 'meta' else element.get('content', '').strip()
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_published_date_json_ld(self, soup):
        """
        Extract the published date from all JSON-LD scripts in the HTML.
        Checks all scripts of type application/ld+json.
        """
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        if not json_ld_scripts:
            logging.warning("No JSON-LD scripts found.")
            return None

        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.string)
                # Handle cases where the JSON-LD contains an array of objects
                if isinstance(json_data, list):
                    for item in json_data:
                        if item.get('@type') in {"NewsArticle", "ReportageNewsArticle", "Article"}:
                            if 'dateModified' in item:
                                return item['dateModified']
                            elif 'datePublished' in item:
                                return item['datePublished']
                # Single JSON-LD object case
                elif isinstance(json_data, dict):
                    if json_data.get('@type') in {"NewsArticle", "ReportageNewsArticle", "Article"}:
                        if 'dateModified' in json_data:
                            return json_data['dateModified']
                        if 'datePublished' in json_data:
                            return json_data['datePublished']
            except json.JSONDecodeError as e:
                logging.warning(f"Failed to decode JSON-LD script: {e}")
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_published_date_regex(self, soup):
        """Extract the published date using regex patterns."""
        date_patterns = [re.compile(r'Published on\s+(\w+\s\d{1,2},\s\d{4})')]
        text = soup.get_text(separator=' ', strip=True)
        for pattern in date_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_content(self, soup):
        """Extracts the main content of the article."""
        # Elimină elementele non-content
        for tag in soup(['header', 'footer', 'nav', 'aside', 'form', 'iframe', 'img', 'div.social', 'figure']):
            tag.decompose()

        # Încercăm să găsim conținutul principal folosind selectori CSS
        content_selectors = ['article', 'div.article-content', 'div.content-body', 'div.post-content',
                             'div.data-app-meta-article']
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Extragem doar paragrafele din acest element
                paragraphs = element.find_all('p')
                filtered_paragraphs = [
                    p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50
                ]

                # Dacă avem paragrafe semnificative, le returnăm
                if filtered_paragraphs:
                    return "\n".join(filtered_paragraphs)

            # Dacă nu am găsit conținutul dorit, returnăm None
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_author(self, soup):
        """
        Attempts to extract the author's name using different strategies:
        JSON-LD metadata, HTML selectors, or byline patterns, in that order.
        Returns authors as a comma-separated string if multiple authors are found.
        """
        extraction_methods = [
            ('JSON-LD', self.extract_author_json_ld),
            ('metadata', self.extract_author_metadata),
            ('HTML selectors', self.extract_author_html),
            ('regex patterns', self.extract_author_regex)
        ]

        author = None
        for method_name, method in extraction_methods:
            if author is None:
                print(f"Trying extraction method: {method_name}")  # Debug print
                author = method(soup)
                print(f"Author found using {method_name}: {author}")  # Debug print
            if author:
                if isinstance(author, list):
                    author_str = ', '.join(author)
                    print(f"Authors extracted: {author_str}")  # Debug print
                    return author_str
                elif isinstance(author, str):
                    print(f"Author extracted: {author}")  # Debug print
                    return author

        print("No author found.")  # Debug print
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_author_metadata(self, soup):
        """Extract the author from metadata tags."""
        article_tags = soup.find_all('meta', attrs={'name': re.compile(r'.*author.*', re.I)})

        # Debugging: Print all meta tags found
        print(f"Found {len(article_tags)} meta tags with author information.")
        for tag in article_tags:
            print(f"Found meta tag: {tag}")

        for tag in article_tags:
            author = tag.get('content', '').strip()
            if author:
                return author
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
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

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
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

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @ScrapperMonitor(validate=validate_soup)
    def extract_author_json_ld(self, soup):
        """Extract all authors from JSON-LD."""
        json_ld_scripts = soup.find_all("script", type="application/ld+json")

        if not json_ld_scripts:
            return []

        authors = []
        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, list):
                    # In case of a list of JSON objects, iterate through each item
                    for item in json_data:
                        if item.get("@type") in {"NewsArticle", "ReportageNewsArticle", "Article"}:
                            author_data = item.get("author", None)
                            authors.extend(self.process_author(author_data))  # Add authors to the list

                elif isinstance(json_data, dict):  # Single JSON-LD object
                    if json_data.get("@type") in {"NewsArticle", "ReportageNewsArticle", "Article"}:
                        author_data = json_data.get("author", None)
                        authors.extend(self.process_author(author_data))  # Add authors to the list

                if '@graph' in json_data:
                    # If @graph exists in the JSON-LD, process it as well
                    graph_items = json_data['@graph']
                    for item in graph_items:
                        if item.get('@type') in {"NewsArticle", "ReportageNewsArticle", "Article"}:
                            author_data = item.get('author', None)
                            authors.extend(self.process_author(author_data))  # Add authors to the list

            except json.JSONDecodeError:
                logging.error("Cannot parse JSON-LD", exc_info=True)

        logging.warning("Authors extracted from JSON-LD: %s", authors)
        return authors

    @staticmethod
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def process_author(author_data):
        """Procesează datele autorului și le returnează sub formă de listă."""
        authors = []

        if isinstance(author_data, list):
            for author in author_data:
                if isinstance(author, dict) and "name" in author:
                    authors.append(author["name"].strip())
                elif isinstance(author, str):
                    authors.append(author.strip())
        elif isinstance(author_data, dict) and "name" in author_data:
            authors.append(author_data["name"].strip())
        elif isinstance(author_data, str):
            authors.append(author_data.strip())

        return authors


# if __name__ == "__main__":
#     scraper = BeautifulSoupScraper()
#     test_url = ("https://www.digi24.ro/stiri/actualitate/politica/marcel-ciolacu-anunta-ca-si-a-dat-demisia-dupa"
#                 "-rezultatul-din-alegeri-sedinta-azi-la-psd-3020621")
#     test_url2 = "https://www.bbc.com/news/articles/cgk18pdnxmmo"
#     test_url3 = ("https://www.digi24.ro/stiri/economie/amiralul-rob-bauer-avertisment-pentru-oamenii-de-afaceri-din"
#                  "-tarile-nato-companiile-sa-fie-pregatite-pentru-un-scenariu-de-razboi-3020709")
#     test_url4 = "https://thepeoplesvoice.tv/npr-ceo-truth-and-facts-are-inherently-racist/"
#     test_url5 = ("https://www.digi24.ro/alegeri-prezidentiale-2024/alegeri-prezidentiale-2024-calin-georgescu-16-in"
#                  "-exit-poll-tot-ce-s-a-intamplat-astazi-a-fost-o-trezire-uluitoare-a-constiintei-3019623")
#     test_url_random = "https://www.jpost.com/breaking-news/article-761462"
#     article_data = scraper.extract_data(test_url4)
#     print(article_data)
#     if article_data:
#         print(f"URL: {article_data['url']}")
#         print(f"Title: {article_data['title']}")
#         print(f"Content: {article_data['content']}")
#         print(f"Author: {article_data['author']}")
#         print(f"Publish Date: {article_data['publish_date']}")
#     else:
#         print("Failed to extract data from the URL.")
