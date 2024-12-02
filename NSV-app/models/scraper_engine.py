import requests
from bs4 import BeautifulSoup
import logging
import time
import re
import json
from aop_wrapper import Aspect

class BeautifulSoupScraper:
    """A scraper class using BeautifulSoup to extract data from web pages."""

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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
    def extract_publish_date(self, soup):
        """Extracts the publish date of the article from the HTML content."""
        return (
            self.extract_published_date_metadata(soup) or
            self.extract_published_date_html(soup) or
            self.extract_published_date_json_ld(soup) or
            self.extract_published_date_regex(soup)
        )

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def extract_published_date_metadata(self, soup):
        """Extract the published date from metadata tags."""
        date_tag = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_tag:
            return date_tag.get('content', '').strip()
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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
    def extract_content(self, soup):
        """Extracts the main content of the article."""
        # Elimină elementele non-content
        for tag in soup(['header', 'footer', 'nav', 'aside', 'form', 'iframe', 'img', 'div.social', 'figure']):
            tag.decompose()

        # Încercăm să găsim conținutul principal folosind selectori CSS
        content_selectors = ['article', 'div.article-content', 'div.content-body', 'div.post-content', 'div.data-app-meta-article']
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
    def clean_text(self, content):
        """Cleans HTML content by removing unwanted tags."""
        for tag in content(['script', 'style', 'form', 'iframe']):
            tag.decompose()
        return content.get_text(separator="\n", strip=True)

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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
                author = method(soup)
            if author:
                if isinstance(author, list):
                    author_str = ', '.join(author)
                    logging.debug(f"Authors extracted using {method_name}: {author_str}")
                    return author_str
                elif isinstance(author, str):
                    logging.debug(f"Author extracted using {method_name}: {author}")
                    return author

        logging.info("Author not found using any predefined methods.")
        return None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def extract_author_metadata(self, soup):
        article_tags = soup.find_all('meta', attrs={'property': re.compile(r'.*author.*', re.I)})
        for tag in article_tags:
            author = tag.get('content', '').strip()
            if author:
                return author

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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
    def extract_author_json_ld(self, soup):
        """Extrage autorul din JSON-LD."""
        json_ld_scripts = soup.find_all("script", type="application/ld+json")

        if not json_ld_scripts:
            return []

        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, list):
                    json_data = next((item for item in json_data if "@type" in item), {})


                if json_data.get("@type") in {"NewsArticle", "ReportageNewsArticle", "Article"}:
                    author_data = json_data.get("author", None)
                    authors = self.process_author(author_data)
                    if authors:
                        return authors

                if '@graph' in json_data:
                    graph_items = json_data['@graph']
                    for item in graph_items:
                        if item.get('@type') in {"NewsArticle", "ReportageNewsArticle", "Article"}:
                            author_data = item.get('author', None)
                            if author_data:
                                authors = self.process_author(author_data)
                                if authors:
                                    return authors

            except json.JSONDecodeError:
                logging.error("Cannot parse JSON-LD", exc_info=True)

        logging.warning("No author in JSON-LD found.")
        return []

    @staticmethod
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

if __name__ == "__main__":
    scraper = BeautifulSoupScraper()
    test_url = "https://www.digi24.ro/stiri/actualitate/politica/marcel-ciolacu-anunta-ca-si-a-dat-demisia-dupa-rezultatul-din-alegeri-sedinta-azi-la-psd-3020621"
    test_url2 ="https://www.bbc.com/news/articles/cgk18pdnxmmo"
    test_url3="https://www.digi24.ro/stiri/economie/amiralul-rob-bauer-avertisment-pentru-oamenii-de-afaceri-din-tarile-nato-companiile-sa-fie-pregatite-pentru-un-scenariu-de-razboi-3020709"
    test_url4 = "https://thepeoplesvoice.tv/npr-ceo-truth-and-facts-are-inherently-racist/"
    test_url5="https://www.digi24.ro/alegeri-prezidentiale-2024/alegeri-prezidentiale-2024-calin-georgescu-16-in-exit-poll-tot-ce-s-a-intamplat-astazi-a-fost-o-trezire-uluitoare-a-constiintei-3019623"
    article_data = scraper.extract_data(test_url2)

    if article_data:
        print(f"URL: {article_data['url']}")
        print(f"Title: {article_data['title']}")
        print(f"Content: {article_data['content']}")
        print(f"Author: {article_data['author']}")
        print(f"Publish Date: {article_data['publish_date']}")
    else:
        print("Failed to extract data from the URL.")
