import unittest
from unittest.mock import patch, Mock
from models.nlp_analyzer import KeywordExtractor, TextBlobSentimentAnalyzer, VaderSentimentAnalyzer, ArticleParser, Monitor
import logging

# Setting up logging
logging.basicConfig(level=logging.DEBUG)
import time

class TestNonFunctional(unittest.TestCase):
    def setUp(self):
        self.sentiment_analyzers = [TextBlobSentimentAnalyzer(), VaderSentimentAnalyzer()]
        self.keyword_extractor = KeywordExtractor(self.sentiment_analyzers)
        self.article_parser = ArticleParser()
        self.sample_text = "Python is an amazing programming language. It is widely used in data science." * 50  # Large input
        self.sample_url = "https://www.digi24.ro/stiri/actualitate/trump-este-primul-inculpat-penal-ales-presedinte-ce-se-intampla-acum-cu-dosarele-sale-penale-si-civile-2997019"

    def test_performance_keyword_extraction(self):
        # Measure the time taken for keyword extraction on a large input
        start_time = time.time()
        keywords = self.keyword_extractor.extract_keywords(self.sample_text)
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.assertLess(elapsed_time, 5, f"Keyword extraction took too long: {elapsed_time:.2f} seconds")
        print(f"Keyword extraction completed in {elapsed_time:.2f} seconds.")

    def test_logging_integrity(self):
        # Ensure the log file contains sufficient entries
        log_file = "logs.txt"
        with open(log_file, "r") as file:
            logs = file.readlines()
        self.assertGreater(len(logs), 10, "Insufficient log entries detected")
        print("Log file integrity validated.")

    def test_large_article_processing(self):
        # Simulate processing a large article
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<article>" + (b"<p>Test content.</p>" * 1000) + b"</article>"
        with patch("models.nlp_analyzer.requests.get", return_value=mock_response):
            start_time = time.time()
            article_content = self.article_parser.extract_article_text(self.sample_url)
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.assertGreater(len(article_content), 1000, "Article content too short")
            self.assertLess(elapsed_time, 5, "Processing took too long")
            print(f"Large article processed in {elapsed_time:.2f} seconds.")
            
class TestMain(unittest.TestCase):
    def setUp(self):
        # Initialize required components for testing
        self.sentiment_analyzers = [TextBlobSentimentAnalyzer(), VaderSentimentAnalyzer()]
        self.keyword_extractor = KeywordExtractor(self.sentiment_analyzers)
        self.article_parser = ArticleParser()
        self.sample_text = "Python is an amazing programming language. It is widely used in data science."
        self.sample_url = "https://example.com"

    def test_keyword_extraction(self):
        # Test keyword extraction functionality
        keywords = self.keyword_extractor.extract_keywords(self.sample_text)
        self.assertTrue(keywords)
        self.assertIn("python", keywords)
        self.assertGreaterEqual(keywords["python"]["frequency"], 1)

    def test_save_keywords_to_file(self):
        # Test saving keywords to a file
        keywords = self.keyword_extractor.extract_keywords(self.sample_text)
        self.keyword_extractor.save_keywords_to_file(keywords, "test_keywords.txt")
        with open("test_keywords.txt", "r") as file:
            lines = file.readlines()
        self.assertGreater(len(lines), 0)

    @patch("models.nlp_analyzer.Monitor.validate_url")
    @patch("models.nlp_analyzer.requests.get")
    def test_article_parser_with_mock(self, mock_get, mock_validate_url):
        # Mock a valid URL response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<article><p>This is a test article.</p></article>"
        mock_get.return_value = mock_response


    def test_monitor_validations(self):
        # Test individual validation methods
        keywords = {"python": {"frequency": 2, "vader_score": 0.5, "sentiment": "Positive"}}
        Monitor.validate_keyword_extraction(keywords)
        Monitor.validate_sentiment_analysis(keywords)
        Monitor.validate_sentiment_score(0.5, "python")

        # Ensure validation does not raise errors for valid data
        self.assertTrue(True)

    def test_invalid_url(self):
        # Test URL validation failure
        invalid_url = "not-a-valid-url"
        with self.assertRaises(ValueError):
            Monitor.validate_url(invalid_url)

    def test_short_article_content(self):
        # Test validation for short article content
        short_text = "Too short."
        with self.assertRaises(ValueError):
            Monitor.validate_article_content(short_text)

    def test_empty_keyword_extraction(self):
        # Test extracting keywords from empty text
        with self.assertRaises(ValueError):
            self.keyword_extractor.extract_keywords("")

if __name__ == "__main__":
    unittest.main()
