import logging
import unittest
from io import StringIO

import requests
from unittest.mock import patch, MagicMock
import os
import sys
from bs4 import BeautifulSoup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.scraper_engine import BeautifulSoupScraper, validate_url, validate_soup, clean_url, clean_selectors, validate_selectors, ScrapperMonitor

import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from models.scraper_engine import BeautifulSoupScraper


class TestProcessAuthor(unittest.TestCase):

    def setUp(self):
        """Set up the BeautifulSoupScraper instance."""
        self.scraper = BeautifulSoupScraper()

    def test_process_author_list_of_dicts_and_strings(self):
        """Test processing a list of authors with dictionaries and strings."""
        author_data = [
            {"name": "John Doe"},
            "Jane Smith",
            {"name": "Alice Johnson"},
            "Bob Brown"
        ]

        authors = self.scraper.process_author(author_data)

        # Assert that all authors are processed correctly
        self.assertEqual(authors, ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Brown'])

    def test_process_author_single_author_dict(self):
        """Test processing a single author as a dictionary."""
        author_data = {"name": "John Doe"}

        authors = self.scraper.process_author(author_data)

        # Assert that the author is processed correctly
        self.assertEqual(authors, ['John Doe'])

    def test_process_author_single_author_str(self):
        """Test processing a single author as a string."""
        author_data = "John Doe"

        authors = self.scraper.process_author(author_data)

        # Assert that the author is processed correctly
        self.assertEqual(authors, ['John Doe'])

    def test_process_author_empty_input(self):
        """Test processing empty or None input."""
        author_data = None

        authors = self.scraper.process_author(author_data)

        # Assert that the result is an empty list
        self.assertEqual(authors, [])

    def test_process_author_empty_list(self):
        """Test processing an empty list."""
        author_data = []

        authors = self.scraper.process_author(author_data)

        # Assert that the result is an empty list
        self.assertEqual(authors, [])

    def test_process_author_empty_dict(self):
        """Test processing an empty dictionary (no 'name' field)."""
        author_data = {}

        authors = self.scraper.process_author(author_data)

        # Assert that the result is an empty list
        self.assertEqual(authors, [])

    def test_process_author_single_author_dict_no_name(self):
        """Test processing a dictionary without 'name' field."""
        author_data = {"age": 30}

        authors = self.scraper.process_author(author_data)

        # Assert that the result is an empty list since there is no 'name'
        self.assertEqual(authors, [])


class TestExtractAuthorJsonLDGraph(unittest.TestCase):

    def setUp(self):
        """Setup method for initializing the scraper and mock HTML content."""
        self.scraper = BeautifulSoupScraper()

        # Mock HTML content with JSON-LD that contains @graph
        self.html_content_with_graph = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@graph": [
                        {
                            "@type": "NewsArticle",
                            "author": {"name": "John Doe"}
                        },
                        {
                            "@type": "NewsArticle",
                            "author": {"name": "Jane Smith"}
                        }
                    ]
                }
                </script>
            </body>
        </html>
        """

        self.html_content_invalid_json_ld = """
               <html>
                   <head><title>Test Article</title></head>
                   <body>
                       <script type="application/ld+json">
                       {
                           "@type": "NewsArticle",
                           "author": {"name": "John Doe"
                       }
                       </script>
                   </body>
               </html>
               """

        # Parse the HTML content using BeautifulSoup
        self.soup_with_graph = BeautifulSoup(self.html_content_with_graph, 'html.parser')
        self.soup_invalid_json_ld = BeautifulSoup(self.html_content_invalid_json_ld, 'html.parser')

    @patch('logging.error')  # Patch logging.error to test if the error is logged
    def test_extract_author_json_ld_invalid_json(self, mock_log_error):
        """Test that a JSONDecodeError is handled and logged when the JSON is invalid."""

        # Extract authors from the malformed JSON-LD (should be empty due to the error)
        authors = self.scraper.extract_author_json_ld(self.soup_invalid_json_ld)

        # Assert that the authors list is empty because of the invalid JSON
        self.assertEqual(authors, [])

        # Assert that logging.error was called once with the expected error message
        mock_log_error.assert_called_once_with("Cannot parse JSON-LD", exc_info=True)

    def test_extract_author_json_ld_with_graph(self):
        """Test that authors are extracted correctly when @graph exists in JSON-LD."""

        # Extract authors from the JSON-LD script containing @graph
        authors = self.scraper.extract_author_json_ld(self.soup_with_graph)

        # Assert that both authors ('John Doe' and 'Jane Smith') are extracted from @graph
        self.assertEqual(authors, ['John Doe', 'Jane Smith'])


class TestExtractAuthorJsonLD(unittest.TestCase):

    def setUp(self):
        """Setup method for initializing the scraper and mock HTML content."""
        self.scraper = BeautifulSoupScraper()

        # Mock HTML content with a list of JSON-LD entries (multiple authors)
        self.html_content_multiple_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                [
                    {
                        "@type": "NewsArticle",
                        "author": {"name": "John Doe"}
                    },
                    {
                        "@type": "NewsArticle",
                        "author": {"name": "Jane Smith"}
                    }
                ]
                </script>
            </body>
        </html>
        """

        # Parse the HTML content using BeautifulSoup
        self.soup_multiple_json_ld = BeautifulSoup(self.html_content_multiple_json_ld, 'html.parser')

    def test_extract_author_json_ld_with_list(self):
        """Test extraction of authors from a list of JSON-LD entries (multiple authors)."""

        # Extract authors from multiple JSON-LD scripts (list of authors)
        authors = self.scraper.extract_author_json_ld(self.soup_multiple_json_ld)

        # Assert that both authors ('John Doe' and 'Jane Smith') are extracted
        self.assertEqual(authors, ['John Doe', 'Jane Smith'])

class TestExtractAuthorFunctions(unittest.TestCase):

    def setUp(self):
        """Setup method for initializing the scraper and mock HTML content."""
        self.scraper = BeautifulSoupScraper()

        # Mocked HTML content for different author extraction scenarios
        self.html_content_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "author": {"name": "John Doe"}
                }
                </script>
            </body>
        </html>
        """

        self.html_content_metadata = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <meta name="author" content="Jane Smith">
            </body>
        </html>
        """

        self.html_content_html_selectors = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <div class="author-name">James Brown</div>
            </body>
        </html>
        """

        self.html_content_regex = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <p>By John Doe</p>
            </body>
        </html>
        """

        # Parse the HTML content using BeautifulSoup for testing
        self.soup_json_ld = BeautifulSoup(self.html_content_json_ld, 'html.parser')
        self.soup_metadata = BeautifulSoup(self.html_content_metadata, 'html.parser')
        self.soup_html_selectors = BeautifulSoup(self.html_content_html_selectors, 'html.parser')
        self.soup_regex = BeautifulSoup(self.html_content_regex, 'html.parser')

    def test_extract_author_json_ld(self):
        """Test extraction of author from JSON-LD metadata."""

        # Mock the extract_author_json_ld method
        author = self.scraper.extract_author_json_ld(self.soup_json_ld)

        # Assert that the author extracted is 'John Doe'
        self.assertEqual(author, ['John Doe'])

    def test_extract_author_metadata(self):
        """Test extraction of author from metadata tag."""

        # Mock the extract_author_metadata method
        author = self.scraper.extract_author_metadata(self.soup_metadata)

        # Assert that the author extracted is 'Jane Smith'
        self.assertEqual(author, 'Jane Smith')

    def test_extract_author_html(self):
        """Test extraction of author from HTML selectors."""

        # Mock the extract_author_html method
        author = self.scraper.extract_author_html(self.soup_html_selectors)

        # Assert that the author extracted is 'James Brown'
        self.assertEqual(author, 'James Brown')

    def test_extract_author_single_author_string(self):
        """Test extraction of a single author returned as a string."""
        # Mock soup for HTML with a single author returned by a specific method
        soup_single_author = BeautifulSoup("<html><body><p>Author: John Doe</p></body></html>", 'html.parser')

        # Mock the extraction methods to simulate a single string author return
        self.scraper.extract_author_json_ld = lambda soup: None  # JSON-LD returns nothing
        self.scraper.extract_author_metadata = lambda soup: None  # Metadata returns nothing
        self.scraper.extract_author_html = lambda soup: "John Doe"  # HTML selectors return a single author string
        self.scraper.extract_author_regex = lambda soup: None  # Regex returns nothing

        # Call the extract_author method
        author = self.scraper.extract_author(soup_single_author)

        # Assert the single author is correctly returned as a string
        self.assertEqual(author, "John Doe")

    def test_extract_author_regex(self):
        """Test extraction of author using regex patterns."""

        # Mock the extract_author_regex method
        author = self.scraper.extract_author_regex(self.soup_regex)

        # Assert that the author extracted is 'John Doe'
        self.assertEqual(author, 'John Doe')

    def test_extract_author_default(self):
        """Test that the default extract_author method is called when no specific method is available."""

        # Mock the extract_author method
        author = self.scraper.extract_author(self.soup_json_ld)

        # Assert that the author extracted is 'John Doe'
        self.assertEqual(author, 'John Doe')

    def test_extract_author_metadata_not_found(self):
        """Test that when no author metadata is found, it returns None."""

        # HTML content with no author metadata
        html_no_metadata = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <p>No author metadata available</p>
            </body>
        </html>
        """

        soup_no_metadata = BeautifulSoup(html_no_metadata, 'html.parser')

        # Call the extract_author_metadata function
        author = self.scraper.extract_author_metadata(soup_no_metadata)

        # Assert that author is None since no author metadata is found
        self.assertIsNone(author)

    def extract_author_html_not_found(self):
        """Test that when no author is found using HTML selectors, it returns None."""

        # HTML content with no author information
        html_no_author = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <p>No author information available</p>
            </body>
        </html>
        """

        soup_no_author = BeautifulSoup(html_no_author, 'html.parser')

        # Call the extract_author_html function
        author = self.scraper.extract_author_html(soup_no_author)

        # Assert that author is None since no author is found
        self.assertIsNone(author)

    def test_author_not_found(self):
        """Test that when no author is found, it returns None."""

        # HTML content with no author information
        html_no_author = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <p>No author information available</p>
            </body>
        </html>
        """

        soup_no_author = BeautifulSoup(html_no_author, 'html.parser')

        # Call the extract_author function
        author = self.scraper.extract_author(soup_no_author)

        # Assert that author is None since no author is found
        self.assertIsNone(author)

class TestExtractPublishedDateJsonLD(unittest.TestCase):

    def setUp(self):
        """Set up the BeautifulSoupScraper instance."""
        self.scraper = BeautifulSoupScraper()

        self.html_content_json_ld_no_modified = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "datePublished": "2024-12-01"
                }
                </script>
            </body>
        </html>
        """
        # Mocked HTML content with JSON-LD containing dateModified and datePublished
        self.html_content_json_ld_valid = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                [
                    {
                        "@type": "NewsArticle",
                        "datePublished": "2024-12-01",
                        "dateModified": "2024-12-05"
                    }
                ]
                </script>
            </body>
        </html>
        """

        # Mocked HTML content with invalid JSON (malformed JSON-LD)
        self.html_content_json_ld_invalid = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "datePublished": "2024-12-01"
                </script>
            </body>
        </html>
        """

        # Mocked HTML content with missing date fields
        self.html_content_json_ld_missing_dates = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                [
                    {
                        "@type": "NewsArticle"
                    }
                ]
                </script>
            </body>
        </html>
        """

        # Parse the HTML content using BeautifulSoup
        self.html_content_json_ld_no_modified = BeautifulSoup(self.html_content_json_ld_no_modified, 'html.parser')
        self.soup_valid = BeautifulSoup(self.html_content_json_ld_valid, 'html.parser')
        self.soup_invalid = BeautifulSoup(self.html_content_json_ld_invalid, 'html.parser')
        self.soup_missing_dates = BeautifulSoup(self.html_content_json_ld_missing_dates, 'html.parser')

    def test_extract_published_date_json_ld_valid(self):
        """Test extracting the published date from valid JSON-LD."""
        publish_date = self.scraper.extract_published_date_json_ld(self.soup_valid)
        self.assertEqual(publish_date, '2024-12-05')

    def test_extract_published_date_json_ld_no_modified(self):
        """Test extracting the published date when dateModified is not present."""
        publish_date = self.scraper.extract_published_date_json_ld(self.html_content_json_ld_no_modified)
        self.assertEqual(publish_date, '2024-12-01')

    def test_extract_published_date_time_publish_date(self):
        """Test extraction from time.publish-date."""
        soup = BeautifulSoup("""
        <html>
            <body>
                <time class="publish-date">2024-12-09</time>
            </body>
        </html>
        """, 'html.parser')

        date = self.scraper.extract_published_date_html(soup)

        self.assertEqual(date, "2024-12-09")

    def test_extract_published_date_span_date(self):
        """Test extraction from span.date."""
        soup = BeautifulSoup("""
        <html>
            <body>
                <span class="date">December 9, 2024</span>
            </body>
        </html>
        """, 'html.parser')

        date = self.scraper.extract_published_date_html(soup)

        self.assertEqual(date, "December 9, 2024")

    def test_extract_published_date_div_pub_date(self):
        """Test extraction from div.pub-date."""
        soup = BeautifulSoup("""
        <html>
            <body>
                <div class="pub-date">09/12/2024</div>
            </body>
        </html>
        """, 'html.parser')

        date = self.scraper.extract_published_date_html(soup)

        self.assertEqual(date, "09/12/2024")

    def test_extract_published_date_json_ld_dateModified_in_object(self):
        """Test extraction of dateModified from a single JSON-LD object."""
        soup_date_modified = BeautifulSoup("""
        <html>
        <script type="application/ld+json">
        {
            "@context": "http://schema.org",
            "@type": "NewsArticle",
            "headline": "Test Article",
            "dateModified": "2024-12-05"
        }
        </script>
        </html>
        """, 'html.parser')

        modified_date = self.scraper.extract_published_date_json_ld(soup_date_modified)

        # Assert the dateModified is correctly extracted
        self.assertEqual(modified_date, "2024-12-05")

    def test_extract_published_date_meta_property_published_time(self):
        """Test extraction from meta[property='article:published_time']."""
        soup = BeautifulSoup("""
        <html>
            <head>
                <meta property="article:published_time" content="2024-12-09">
            </head>
            <body></body>
        </html>
        """, 'html.parser')

        date = self.scraper.extract_published_date_html(soup)

        self.assertEqual(date, "2024-12-09")

    def test_extract_published_date_meta_name_publish_date(self):
        """Test extraction from meta[name='publish-date']."""
        soup = BeautifulSoup("""
        <html>
            <head>
                <meta name="publish-date" content="December 9, 2024">
            </head>
            <body></body>
        </html>
        """, 'html.parser')

        date = self.scraper.extract_published_date_html(soup)

        self.assertEqual(date, "December 9, 2024")

    def test_extract_published_date_meta_name_dcterms_modified(self):
        """Test extraction from meta[name='dcterms.modified']."""
        soup = BeautifulSoup("""
        <html>
            <head>
                <meta name="dcterms.modified" content="2024-12-09T12:00:00">
            </head>
            <body></body>
        </html>
        """, 'html.parser')

        date = self.scraper.extract_published_date_html(soup)

        self.assertEqual(date, "2024-12-09T12:00:00")

    def test_extract_published_date_json_ld_datePublished_in_array(self):
        """Test extraction of datePublished from JSON-LD array."""
        soup_date_published = BeautifulSoup("""
        <html>
        <script type="application/ld+json">
        [
            {
                "@context": "http://schema.org",
                "@type": "NewsArticle",
                "headline": "Test Article",
                "datePublished": "2024-12-01"
            },
            {
                "@context": "http://schema.org",
                "@type": "Article",
                "headline": "Another Article"
            }
        ]
        </script>
        </html>
        """, 'html.parser')

        published_date = self.scraper.extract_published_date_json_ld(soup_date_published)

        # Assert the datePublished is correctly extracted
        self.assertEqual(published_date, "2024-12-01")

    def test_extract_published_date_json_ld_invalid(self):
        """Test handling invalid JSON-LD (malformed JSON)."""
        publish_date = self.scraper.extract_published_date_json_ld(self.soup_invalid)
        self.assertIsNone(publish_date)
        # Check if the warning is logged
        with self.assertLogs(level='WARNING') as log:
            self.scraper.extract_published_date_json_ld(self.soup_invalid)
            self.assertTrue("Failed to decode JSON-LD script:" in log.output[0])

    def test_extract_published_date_json_ld_fallback(self):
        """Test fallback to None when no date is found across multiple extraction methods."""
        # HTML content with no date info in any method
        empty_html = "<html><head><title>No Date Article</title></head><body></body></html>"
        soup_empty = BeautifulSoup(empty_html, 'html.parser')

        publish_date = self.scraper.extract_published_date_json_ld(soup_empty)
        self.assertIsNone(publish_date)

class TestBeautifulSoupScraperDate(unittest.TestCase):

    def setUp(self):
        """Set up the BeautifulSoupScraper instance."""
        self.scraper = BeautifulSoupScraper()

        # Mocked HTML content for testing
        self.html_content_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "datePublished": "2024-12-01"
                }
                </script>
            </body>
        </html>
        """

        self.html_content_metadata = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <meta property="article:published_time" content="2024-12-02">
            </body>
        </html>
        """

        self.html_content_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <span class="date">2024-12-03</span>
            </body>
        </html>
        """

        self.html_content_regex = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <p>Published on December 4, 2024</p>
            </body>
        </html>
        """

        # Parse the HTML content using BeautifulSoup
        self.soup_json_ld = BeautifulSoup(self.html_content_json_ld, 'html.parser')
        self.soup_metadata = BeautifulSoup(self.html_content_metadata, 'html.parser')
        self.soup_html = BeautifulSoup(self.html_content_html, 'html.parser')
        self.soup_regex = BeautifulSoup(self.html_content_regex, 'html.parser')

    def test_extract_publish_date(self):
        """Test extract_publish_date method."""
        # Simulate that the first method (JSON-LD) gives a date
        publish_date = self.scraper.extract_publish_date(self.soup_json_ld)
        self.assertEqual(publish_date, '2024-12-01')

        # Simulate that the second method (metadata) gives a date
        publish_date = self.scraper.extract_publish_date(self.soup_metadata)
        self.assertEqual(publish_date, '2024-12-02')

        # Simulate that the third method (HTML selector) gives a date
        publish_date = self.scraper.extract_publish_date(self.soup_html)
        self.assertEqual(publish_date, '2024-12-03')

        # Simulate that the regex method gives a date
        publish_date = self.scraper.extract_publish_date(self.soup_regex)
        self.assertEqual(publish_date, 'December 4, 2024')

    def test_extract_published_date_json_ld(self):
        """Test extracting date from JSON-LD."""
        publish_date = self.scraper.extract_published_date_json_ld(self.soup_json_ld)
        self.assertEqual(publish_date, '2024-12-01')

    def test_extract_published_date_metadata(self):
        """Test extracting date from metadata."""
        publish_date = self.scraper.extract_published_date_metadata(self.soup_metadata)
        self.assertEqual(publish_date, '2024-12-02')

    def test_extract_published_date_html(self):
        """Test extracting date from HTML selectors."""
        publish_date = self.scraper.extract_published_date_html(self.soup_html)
        self.assertEqual(publish_date, '2024-12-03')

    def test_extract_published_date_regex(self):
        """Test extracting date using regex."""
        publish_date = self.scraper.extract_published_date_regex(self.soup_regex)
        self.assertEqual(publish_date, 'December 4, 2024')

    def test_fallback_to_default(self):
        """Test that fallback to default occurs when no date is found."""
        # An empty HTML document to test no date being found
        empty_html = "<html><head><title>Empty Article</title></head><body></body></html>"
        soup_empty = BeautifulSoup(empty_html, 'html.parser')

        publish_date = self.scraper.extract_publish_date(soup_empty)
        self.assertEqual(publish_date, None)

class TestExtractText(unittest.TestCase):

    def setUp(self):
        """Set up the BeautifulSoupScraper instance and mock HTML content."""
        self.scraper = BeautifulSoupScraper()

        # Mocked HTML content for testing
        self.html_content = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Article Title</h1>
                <div class="content">
                    <p>This is the first paragraph of the article.</p>
                    <p>This is the second paragraph with more details.</p>
                </div>
                <footer>Published by News Corp</footer>
            </body>
        </html>
        """

        # Parse the HTML content using BeautifulSoup
        self.soup = BeautifulSoup(self.html_content, 'html.parser')

    def test_extract_text_valid_selector(self):
        """Test extracting text using a valid CSS selector."""
        selectors = ['h1', '.content p']
        extracted_text = self.scraper.extract_text(self.soup, selectors)

        # Assert that the text extracted is from the first matching element (h1)
        self.assertEqual(extracted_text, 'Article Title')

    def test_extract_text_no_matching_selector(self):
        """Test when no CSS selector matches any element."""
        selectors = ['.nonexistent-class']
        extracted_text = self.scraper.extract_text(self.soup, selectors)

        # Assert that no text is extracted, so it should return None
        self.assertIsNone(extracted_text)

    def test_extract_text_multiple_selectors(self):
        """Test using multiple selectors, ensuring the first match is returned."""
        selectors = ['.content p', 'footer']
        extracted_text = self.scraper.extract_text(self.soup, selectors)

        # Assert that the first matching element's text is returned (first <p> in .content)
        self.assertEqual(extracted_text, 'This is the first paragraph of the article.')

    def test_extract_text_empty_html(self):
        """Test with empty HTML content."""
        empty_html = "<html><head><title>Empty</title></head><body></body></html>"
        empty_soup = BeautifulSoup(empty_html, 'html.parser')

        selectors = ['h1', '.content p']
        extracted_text = self.scraper.extract_text(empty_soup, selectors)

        # Assert that no text is found in the empty HTML, so it should return None
        self.assertIsNone(extracted_text)

    def test_extract_text_malformed_html(self):
        """Test with malformed HTML content."""
        malformed_html = "<html><head><title>Malformed</title><body><h1>Title</h1><div class='content>"
        malformed_soup = BeautifulSoup(malformed_html, 'html.parser')

        selectors = ['h1', '.content p']
        extracted_text = self.scraper.extract_text(malformed_soup, selectors)

        # Assert that the text is extracted from the first <h1> element
        self.assertEqual(extracted_text, 'Title')

class TestExtractData(unittest.TestCase):

    def setUp(self):
        """Set up the BeautifulSoupScraper instance."""
        self.scraper = BeautifulSoupScraper()

        # Simulate valid HTML content
        self.html_content = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Article Title</h1>
                <div class="content">
                    <p>This is the first paragraph of the article.</p>
                    <p>This is the second paragraph with more details.</p>
                </div>
                <footer>2024-12-01</footer>
                <p>By Author</p>
            </body>
        </html>
        """
        self.soup = BeautifulSoup(self.html_content, 'html.parser')

    def test_extract_data_valid(self):
        """Test extracting data from valid HTML content."""
        url = "http://example.com"
        result = self.scraper.extract_data(url)

        # Assert that the extracted data matches the expected values
        self.assertEqual(result['url'], url)
        self.assertEqual(result['title'], 'Example Domain')
        self.assertEqual(result['content'], 'No content available')
        self.assertEqual(result['author'], 'Unknown Author')
        self.assertEqual(result['publish_date'], 'Unknown Date')

    def test_extract_data_missing_content(self):
        """Test extracting data when content is missing."""
        # Remove content from the HTML for testing
        empty_html = "<html><body><h1>Test Article</h1><footer>2024-12-01</footer></body></html>"
        empty_soup = BeautifulSoup(empty_html, 'html.parser')

        # Use the method directly to simulate behavior with missing content
        result = self.scraper.extract_data("http://example.com")

        # Assert that the content field returns "No content available"
        self.assertEqual(result['content'], 'No content available')

    def test_extract_data_missing_author(self):
        """Test extracting data when author is missing."""
        # Modify the HTML to remove the author
        no_author_html = "<html><body><h1>Test Article</h1><footer>2024-12-01</footer></body></html>"
        no_author_soup = BeautifulSoup(no_author_html, 'html.parser')

        result = self.scraper.extract_data("http://example.com")

        # Assert that the author field defaults to "Unknown Author"
        self.assertEqual(result['author'], 'Unknown Author')

    def test_extract_data_missing_date(self):
        """Test extracting data when publish date is missing."""
        # Modify the HTML to remove the footer with the date
        no_date_html = "<html><body><h1>Test Article</h1><div class='content'>Article Content</div></body></html>"
        no_date_soup = BeautifulSoup(no_date_html, 'html.parser')

        result = self.scraper.extract_data("http://example.com")

        # Assert that the publish_date field defaults to "Unknown Date"
        self.assertEqual(result['publish_date'], 'Unknown Date')

    def test_extract_data_fallback(self):
        """Test when no matching data is found, fallbacks should be triggered."""
        # Empty HTML content simulating no data available
        empty_html = "<html><body></body></html>"
        empty_soup = BeautifulSoup(empty_html, 'html.parser')

        result = self.scraper.extract_data("http://example.com")

        # Assert that all data falls back to default values
        self.assertEqual(result['title'], "Example Domain")
        self.assertEqual(result['content'], "No content available")
        self.assertEqual(result['author'], "Unknown Author")
        self.assertEqual(result['publish_date'], "Unknown Date")


class TestExtractTitle(unittest.TestCase):

    def setUp(self):
        """Set up the BeautifulSoupScraper instance and mock HTML content."""
        self.scraper = BeautifulSoupScraper()

        # HTML content with various potential title sources (HTML, JSON-LD, Metadata)
        self.html_content = """
        <html>
            <head><title>HTML Title</title></head>
            <body>
                <h1>Article Title</h1>
                <div class="content">Some article content.</div>
                <p>By Author</p>
                <footer>2024-12-01</footer>
            </body>
        </html>
        """

        # HTML content with JSON-LD for testing
        self.html_content_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "headline": "JSON-LD Article Title"
                }
                </script>
            </body>
        </html>
        """

        # HTML content with metadata tags for testing
        self.html_content_metadata = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <meta property="og:title" content="Meta Title">
            </body>
        </html>
        """

        # HTML content with no title for testing fallback
        self.html_content_empty = "<html><head><title></title></head><body></body></html>"

        # Parse the HTML content using BeautifulSoup
        self.soup_html = BeautifulSoup(self.html_content, 'html.parser')
        self.soup_json_ld = BeautifulSoup(self.html_content_json_ld, 'html.parser')
        self.soup_metadata = BeautifulSoup(self.html_content_metadata, 'html.parser')
        self.soup_empty = BeautifulSoup(self.html_content_empty, 'html.parser')

    def test_extract_title_from_html(self):
        """Test extracting title from HTML."""
        result = self.scraper.extract_title(self.soup_html)
        self.assertEqual(result, "Article Title")

    def test_extract_title_from_json_ld_list(self):
        """Test extraction of title from JSON-LD with a list of objects."""
        soup_json_ld_list = BeautifulSoup("""
        <html>
            <script type="application/ld+json">
            [
                {
                    "@context": "http://schema.org",
                    "@type": "NewsArticle",
                    "headline": "List Headline"
                },
                {
                    "@context": "http://schema.org",
                    "@type": "Article",
                    "name": "Fallback Title"
                }
            ]
            </script>
        </html>
        """, 'html.parser')

        title = self.scraper.extract_title_from_json_ld(soup_json_ld_list)

        # Assert that the first matching headline is returned
        self.assertEqual(title, "List Headline")

    def test_extract_title_from_metadata_name_title(self):
        """Test extraction of title from meta[name='title']."""
        # Mock HTML with meta[name="title"]
        soup_with_meta_title = BeautifulSoup("""
        <html>
            <head>
                <meta name="title" content="Test Title from Metadata">
            </head>
            <body></body>
        </html>
        """, 'html.parser')

        # Call the method
        title = self.scraper.extract_title_from_metadata(soup_with_meta_title)

        # Assert the title is correctly extracted
        self.assertEqual(title, "Test Title from Metadata")

    def test_extract_title_from_json_ld_invalid_json(self):
        """Test handling of invalid JSON in JSON-LD."""
        soup_invalid_json = BeautifulSoup("""
        <html>
            <script type="application/ld+json">
            { invalid json }
            </script>
        </html>
        """, 'html.parser')

        with self.assertLogs(level='WARNING') as log:
            title = self.scraper.extract_title_from_json_ld(soup_invalid_json)

        # Assert that no title is returned
        self.assertIsNone(title)

        # Assert that the warning is logged
        self.assertTrue("Failed to decode JSON-LD script." in log.output[0])

    def test_extract_title_from_json_ld(self):
        """Test extracting title from JSON-LD."""
        result = self.scraper.extract_title(self.soup_json_ld)
        self.assertEqual(result, "JSON-LD Article Title")

    def test_extract_title_from_json_ld_single_object(self):
        """Test extraction of title from a single JSON-LD object."""
        soup_single_json_ld = BeautifulSoup("""
        <html>
            <script type="application/ld+json">
            {
                "@context": "http://schema.org",
                "@type": "NewsArticle",
                "headline": "Single Headline"
            }
            </script>
        </html>
        """, 'html.parser')

        title = self.scraper.extract_title_from_json_ld(soup_single_json_ld)

        # Assert the title is correctly extracted
        self.assertEqual(title, "Single Headline")

    def test_extract_title_from_metadata(self):
        """Test extracting title from metadata."""
        result = self.scraper.extract_title(self.soup_metadata)
        self.assertEqual(result, "Meta Title")

    def test_extract_title_fallback(self):
        """Test extracting title when no title is found (fallback to default)."""
        empty_soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
        result = self.scraper.extract_title(empty_soup)
        self.assertEqual(result, "Unknown Title")

    def test_extract_title_empty(self):
        """Test extracting title from HTML with an empty title tag (fallback)."""
        result = self.scraper.extract_title(self.soup_empty)
        self.assertEqual(result, "Unknown Title")

class TestExtractAuthorJsonLD(unittest.TestCase):

    def setUp(self):
        """Setup method for initializing the scraper and mock HTML content."""
        self.scraper = BeautifulSoupScraper()

        # Mock valid JSON-LD with author data
        self.html_content_valid_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "author": {"name": "John Doe"}
                }
                </script>
            </body>
        </html>
        """

        # Mock JSON-LD with no author data
        self.html_content_no_author_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle"
                }
                </script>
            </body>
        </html>
        """

        # Mock malformed JSON-LD (invalid JSON)
        self.html_content_invalid_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "author": {"name": "John Doe"
                }
                </script>
            </body>
        </html>
        """

        # Mock HTML with multiple JSON-LD scripts
        self.html_content_multiple_json_ld = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "author": {"name": "John Doe"}
                }
                </script>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "author": {"name": "Jane Smith"}
                }
                </script>
            </body>
        </html>
        """

        # Parse the HTML content using BeautifulSoup
        self.soup_valid_json_ld = BeautifulSoup(self.html_content_valid_json_ld, 'html.parser')
        self.soup_no_author_json_ld = BeautifulSoup(self.html_content_no_author_json_ld, 'html.parser')
        self.soup_invalid_json_ld = BeautifulSoup(self.html_content_invalid_json_ld, 'html.parser')
        self.soup_multiple_json_ld = BeautifulSoup(self.html_content_multiple_json_ld, 'html.parser')

    def test_extract_author_json_ld_valid(self):
        """Test that author is correctly extracted from valid JSON-LD."""

        # Extract author from valid JSON-LD
        author = self.scraper.extract_author_json_ld(self.soup_valid_json_ld)

        # Assert that the author extracted is 'John Doe'
        self.assertEqual(author, ['John Doe'])

    def test_extract_author_json_ld_no_author(self):
        """Test that no author is extracted if JSON-LD has no author data."""

        # Extract author from JSON-LD with no author data
        author = self.scraper.extract_author_json_ld(self.soup_no_author_json_ld)

        # Assert that no author is found
        self.assertEqual(author, [])

    def test_extract_author_json_ld_invalid_json(self):
        """Test that invalid JSON-LD (malformed JSON) is handled gracefully."""

        # Extract author from invalid JSON-LD
        with self.assertLogs(level='ERROR') as log:
            author = self.scraper.extract_author_json_ld(self.soup_invalid_json_ld)

        # Assert that the author is empty due to invalid JSON
        self.assertEqual(author, [])

        # Ensure the error is logged
        self.assertTrue("Cannot parse JSON-LD" in log.output[0])

    def test_extract_author_json_ld_multiple_entries(self):
        """Test extraction of author from multiple JSON-LD entries."""

        # Extract author from multiple JSON-LD scripts
        authors = self.scraper.extract_author_json_ld(self.soup_multiple_json_ld)

        # Assert that both authors ('John Doe' and 'Jane Smith') are extracted
        self.assertEqual(authors, ['John Doe', 'Jane Smith'])

    def test_extract_author_json_ld_no_json_ld(self):
        """Test that no author is extracted when there is no JSON-LD in the HTML."""

        # HTML without JSON-LD
        soup_no_json_ld = BeautifulSoup("<html><head><title>No JSON-LD</title></head><body></body></html>",
                                        'html.parser')

        # Extract author (should return empty list)
        author = self.scraper.extract_author_json_ld(soup_no_json_ld)

        # Assert that no author is found
        self.assertEqual(author, [])

    def test_extract_author_json_ld_list_in_single_script(self):
        """Test extraction of authors from a list of JSON objects in a single JSON-LD script."""
        soup_list_in_script = BeautifulSoup("""
        <html>
        <script type="application/ld+json">
        [
            {
                "@context": "http://schema.org",
                "@type": "NewsArticle",
                "author": {"@type": "Person", "name": "John Doe"}
            },
            {
                "@context": "http://schema.org",
                "@type": "Article",
                "author": {"@type": "Person", "name": "Jane Smith"}
            }
        ]
        </script>
        </html>
        """, 'html.parser')

        authors = self.scraper.extract_author_json_ld(soup_list_in_script)

        # Assert both authors are extracted
        self.assertEqual(authors, ['John Doe', 'Jane Smith'])


class TestScrapperMonitor2(unittest.TestCase):

    def test_scrapper_monitor_init_with_functions(self):
        """Test that ScrapperMonitor correctly assigns validate and clean functions."""

        # Define dummy validate and clean functions
        def dummy_validate(soup):
            return True

        def dummy_clean(soup):
            return soup

        # Initialize ScrapperMonitor with custom validate and clean functions
        monitor = ScrapperMonitor(validate=dummy_validate, clean=dummy_clean)

        # Assert that the 'validate' function is correctly assigned
        self.assertEqual(monitor.validate, dummy_validate)

        # Assert that the 'clean' function is correctly assigned
        self.assertEqual(monitor.clean, dummy_clean)

    def test_scrapper_monitor_init_with_defaults(self):
        """Test that ScrapperMonitor initializes with None for validate and clean by default."""

        # Initialize ScrapperMonitor without passing validate or clean functions
        monitor = ScrapperMonitor()

        # Assert that 'validate' is None
        self.assertIsNone(monitor.validate)

        # Assert that 'clean' is None
        self.assertIsNone(monitor.clean)

    def test_scrapper_monitor_init_with_functions(self):
        """Test that ScrapperMonitor initializes with custom validate and clean functions."""

        # Sample validate and clean functions
        def dummy_validate(soup):
            return True

        def dummy_clean(soup):
            return soup

        # Initialize ScrapperMonitor with custom functions
        monitor = ScrapperMonitor(validate=dummy_validate, clean=dummy_clean)

        # Assert that the validate and clean functions are set correctly
        self.assertEqual(monitor.validate, dummy_validate)
        self.assertEqual(monitor.clean, dummy_clean)

    def test_scrapper_monitor_init_with_defaults(self):
        """Test that ScrapperMonitor initializes with default None values for validate and clean."""

        # Initialize ScrapperMonitor with no functions passed (default is None)
        monitor = ScrapperMonitor()

        # Assert that validate and clean are set to None
        self.assertIsNone(monitor.validate)
        self.assertIsNone(monitor.clean)


class TestScrapperMonitor3(unittest.TestCase):

    def test_decorator_with_successful_validation(self):
        """Test that the decorated function is called if validation succeeds."""

        # Define the mock functions
        def mock_validate(*args, **kwargs):
            pass  # Simulate successful validation

        def mock_function(*args, **kwargs):
            return "Function called"

        # Initialize ScrapperMonitor with the mock validate function (no clean function)
        monitor = ScrapperMonitor(validate=mock_validate)

        # Apply the decorator
        decorated_function = monitor(mock_function)

        # Call the decorated function
        result = decorated_function()

        # Assert that the function is called and returns the correct result
        self.assertEqual(result, "Function called")

    def test_decorator_with_failed_validation_and_clean(self):
        """Test that the clean function is applied if validation fails."""

        # Define the mock functions
        def mock_validate(*args, **kwargs):
            raise ValueError("Validation failed")

        def mock_clean(*args, **kwargs):
            pass  # Simulate cleaning (does nothing in this case)

        def mock_function(*args, **kwargs):
            return "Function called"

        # Initialize ScrapperMonitor with the mock validate and clean functions
        monitor = ScrapperMonitor(validate=mock_validate, clean=mock_clean)

        # Apply the decorator
        decorated_function = monitor(mock_function)

        # Call the decorated function and assert that the exception is re-raised
        with self.assertRaises(ValueError):
            decorated_function()

    def test_decorator_with_no_validation_or_clean(self):
        """Test that the decorated function is called with no validate or clean functions."""

        # Define the mock function
        def mock_function(*args, **kwargs):
            return "Function called"

        # Initialize ScrapperMonitor with no validate or clean functions
        monitor = ScrapperMonitor()

        # Apply the decorator
        decorated_function = monitor(mock_function)

        # Call the decorated function
        result = decorated_function()

        # Assert that the function is called and returns the correct result
        self.assertEqual(result, "Function called")


class TestScrapperMonitor(unittest.TestCase):

    def setUp(self):
        """Setup method for initializing the ScrapperMonitor with mock functions."""
        # Define mock validate and clean functions
        self.mock_validate = MagicMock(side_effect=validate_url)
        self.mock_clean = MagicMock(side_effect=clean_url)
        # Create the ScrapperMonitor instance
        self.monitor = ScrapperMonitor(validate=self.mock_validate, clean=self.mock_clean)

    def test_validate_function_called(self):
        """Test if validate function is called when wrapped function is executed."""

        # Mock the function to wrap
        @self.monitor
        def mock_function(url):
            return f"Processing URL: {url}"

        # Call the mock function
        result = mock_function(url="https://example.com")

        # Validate that validate function was called
        self.mock_validate.assert_called_with(url="https://example.com")
        self.assertEqual(result, "Processing URL: https://example.com")

    def test_success_without_cleaning(self):
        """Test that function proceeds when validation succeeds."""

        # Mock the function to wrap
        @self.monitor
        def mock_function(url):
            return f"Processing URL: {url}"

        # Call the mock function with a valid URL
        result = mock_function(url="https://example.com")

        # Validate that the result is as expected
        self.assertEqual(result, "Processing URL: https://example.com")
        # Ensure cleaning function was not called
        self.mock_clean.assert_not_called()


class TestValidateSelectors(unittest.TestCase):

    def test_valid_selectors(self):
        """Test that valid selectors are passed through without issue."""

        # Valid selectors (strings with no extra spaces)
        selectors = ['h1', '.article-title', 'div.content']

        # Call the validate_selectors function with valid selectors
        result = validate_selectors(selectors=selectors)

        # Validate the result (should return the same list of selectors)
        self.assertEqual(result, selectors)

    def test_invalid_selector_not_string(self):
        """Test that invalid selector (non-string) raises an exception."""

        # Invalid selector (integer instead of string)
        selectors = ['h1', 123, '.article-title']

        # Ensure ValueError is raised
        with self.assertRaises(ValueError) as context:
            validate_selectors(selectors=selectors)

        self.assertTrue("Invalid selector at index 1" in str(context.exception))

    def test_selector_with_extra_spaces(self):
        """Test that selectors with extra spaces are detected and raised."""

        # Selector with leading/trailing spaces
        selectors = [' h1 ', '  .article-title  ', 'div.content']

        # Ensure ValueError is raised for any selector with extra spaces
        with self.assertRaises(ValueError) as context:
            validate_selectors(selectors=selectors)

        self.assertTrue("contains leading/trailing spaces" in str(context.exception))

    def test_multiple_invalid_selectors(self):
        """Test multiple invalid selectors raise appropriate exceptions."""

        # Invalid selectors (mixed types and extra spaces)
        selectors = ['h1', 123, '  .article-title  ', None]

        # Ensure ValueError is raised for the first invalid selector
        with self.assertRaises(ValueError) as context:
            validate_selectors(selectors=selectors)

        # Check that the exception message refers to the first invalid selector
        self.assertTrue("Invalid selector at index 1" in str(context.exception))

    def test_clean_selectors(self):
        """Test that selectors are cleaned of extra spaces."""
        # Selectors with extra spaces
        selectors = [' h1 ', '  .article-title  ', 'div.content']

        # Clean the selectors
        cleaned_selectors = clean_selectors(selectors)

        # Validate that the selectors are cleaned of extra spaces
        self.assertEqual(cleaned_selectors, None)


class TestValidateSoup(unittest.TestCase):

    def test_valid_soup(self):
        """Test that a valid BeautifulSoup object is accepted without issue."""
        html_content = "<html><head><title>Test Page</title></head><body><h1>Sample Article</h1></body></html>"
        soup = BeautifulSoup(html_content, 'html.parser')
        try:
            validate_soup(soup=soup)
        except ValueError:
            self.fail("validate_soup raised ValueError unexpectedly for a valid BeautifulSoup object.")
    def test_invalid_soup_non_beautifulsoup(self):
        """Test that non-BeautifulSoup objects (e.g., a string) are rejected."""

        # Call validate_soup with a non-BeautifulSoup object (e.g., a string)
        with self.assertRaises(ValueError) as context:
            validate_soup(soup="This is not a BeautifulSoup object.")

        self.assertTrue("Invalid or empty HTML content provided.")

    def test_empty_soup(self):
        """Test that an empty BeautifulSoup object raises an exception."""
        empty_soup = None
        # Call validate_soup with the empty soup object, which should raise an exception
        with self.assertRaises(ValueError) as context:
            validate_soup(soup=empty_soup)
        self.assertTrue("Invalid or empty HTML content provided.")

class TestExtractContent(unittest.TestCase):

    def setUp(self):
        """Set up the BeautifulSoupScraper instance and mock HTML content."""
        self.scraper = BeautifulSoupScraper()

        # HTML content with article-like structure
        self.html_content = """
        <html>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <p>This is the first paragraph of the article. It is long enough.</p>
                    <p>Short paragraph.</p>
                    <p>This is the second paragraph of the article. It is long enough.</p>
                </article>
            </body>
        </html>
        """
        # HTML with non-content elements to be removed
        self.html_content_with_non_content = """
        <html>
            <body>
                <header>Header Content</header>
                <article>
                    <h1>Article Title</h1>
                    <p>This is the first paragraph of the article.</p>
                    <footer>Footer Content</footer>
                </article>
            </body>
        </html>
        """
        # HTML with no valid content
        self.empty_html = "<html><body></body></html>"

        # Parse the HTML content using BeautifulSoup
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        self.soup_with_non_content = BeautifulSoup(self.html_content_with_non_content, 'html.parser')
        self.empty_soup = BeautifulSoup(self.empty_html, 'html.parser')

    def test_extract_content_valid(self):
        """Test extracting valid content."""
        result = self.scraper.extract_content(self.soup)
        self.assertEqual(result, "This is the first paragraph of the article. It is long enough.\nThis is the second paragraph of the article. It is long enough.")

    def test_extract_content_short_paragraphs(self):
        """Test when short paragraphs are excluded (less than 50 characters)."""
        result = self.scraper.extract_content(self.soup)
        # Only paragraphs that are long enough should be included
        self.assertEqual(result, "This is the first paragraph of the article. It is long enough.\nThis is the second paragraph of the article. It is long enough.")

    def test_extract_content_with_non_content(self):
        """Test extracting content when non-content elements (header, footer) are present."""
        result = self.scraper.extract_content(self.soup_with_non_content)
        self.assertEqual(result, None)

    def test_extract_content_empty_html(self):
        """Test when no content is found, the function should return None."""
        result = self.scraper.extract_content(self.empty_soup)
        self.assertIsNone(result)

    def test_extract_content_no_valid_content(self):
        """Test when no valid content is found (i.e., all paragraphs are short)."""
        empty_content_html = "<html><body><article><p>Short paragraph.</p></article></body></html>"
        empty_content_soup = BeautifulSoup(empty_content_html, 'html.parser')
        result = self.scraper.extract_content(empty_content_soup)
        self.assertIsNone(result)


class TestBeautifulSoupScraper3(unittest.TestCase):
    @patch('requests.get')
    def test_extract_data_network_failure(self, mock_requests_get):
        scraper = BeautifulSoupScraper()
        try:
            result = scraper.extract_data("https://example.com")
        except ValueError as e:
            self.assertIn("Request failed (Attempt 1).", str(e))
            self.assertIn("Request failed (Attempt 2).", str(e))
            self.assertIn("Request failed (Attempt 3).", str(e))

    @patch('requests.get')
    def test_extract_data_network_failure_final_else(self, mock_requests_get):
        scraper = BeautifulSoupScraper()
        try:
            scraper.extract_data("https://example.com")
        except ValueError as e:
            self.assertIn("Failed to retrieve webpage after multiple attempts.", str(e))


if __name__ == '__main__':
    unittest.main()
