import unittest
import requests
from unittest.mock import patch
from ..models.scraper_engine import ScraperFactory, BeautifulSoupScraper, TweepyScraper, TwarcScraper
class ScraperFactoryTest(unittest.TestCase):
    def test_create_scraper_valid_types(self):
        # Test valid scraper types
        bs_scraper = ScraperFactory.create_scraper('beautifulsoup')
        self.assertIsInstance(bs_scraper, BeautifulSoupScraper)

        tweepy_scraper = ScraperFactory.create_scraper('tweepy')
        self.assertIsInstance(tweepy_scraper, TweepyScraper)

        twarc_scraper = ScraperFactory.create_scraper('twarc')
        self.assertIsInstance(twarc_scraper, TwarcScraper)

    def test_create_scraper_invalid_type(self):
        # Test invalid scraper type should raise ValueError
        with self.assertRaises(ValueError):
            ScraperFactory.create_scraper('unknown')

class BeautifulSoupScraperTests(unittest.TestCase):
    def setUp(self):
        self.scraper = BeautifulSoupScraper()
    @patch('requests.get')
    def test_bss_extract_data(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = (
            "<html><head><title>Example Title</title></head>"
            "<body><h1>Example Title</h1><div class='article-content'>Example content</div></body></html>"
        )

        url = "http://example.com"
        expected_data = (url, "Example Title", "Example content", "Unknown Author", "Unknown Date")
        result = self.scraper.extract_data(url)
        self.assertEqual(result, expected_data)

    @patch('requests.get')
    def test_bss_extract_data_url_not_found(self, mock_get):
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = ""

        url = "http://nonexistenturl.com"
        result = self.scraper.extract_data(url)
        self.assertIsNone(result)

    def test_process_data(self):
        # Sample data to pass to process_data
        sample_data = (
            "http://example.com",
            "Sample Title",
            "This is sample content.",
            "John Doe",
            "2024-11-07"
        )

        # Process the data
        article = self.scraper.process_data(sample_data)

        # Assertions
        self.assertEqual(article.url, "http://example.com")
        self.assertEqual(article.title, "Sample Title")
        self.assertEqual(article.content, "This is sample content.")
        self.assertEqual(article.author, ["John Doe"])
        self.assertEqual(article.publish_date, "2024-11-07")

if __name__ == '__main__':
    unittest.main()
