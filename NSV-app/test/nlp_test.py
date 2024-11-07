import unittest
from src.article_processing import ArticleParser, KeywordExtractor, TextBlobSentimentAnalyzer  

class TestArticleProcessing(unittest.TestCase):

    def setUp(self):
        self.parser = ArticleParser()
        self.sentiment_analyzer = TextBlobSentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor(self.sentiment_analyzer)

    def test_extract_article_text_valid_url(self):
   
        url = "https://www.digi24.ro/stiri/actualitate/trump-este-primul-inculpat-penal-ales-presedinte-ce-se-intampla-acum-cu-dosarele-sale-penale-si-civile-2997019"
        
        try:
            result = self.parser.extract_article_text(url)
            self.assertIsInstance(result, str, "Expected a string response from extract_article_text")
            self.assertGreater(len(result), 0, "Expected non-empty article text")
        except ValueError:
            self.fail("extract_article_text raised ValueError unexpectedly!")

    def test_extract_article_text_invalid_url(self):
        
        invalid_url = "https://thisurldoesnotexist.fake"
        
        with self.assertRaises(ValueError, msg="Expected ValueError for invalid URL"):
            self.parser.extract_article_text(invalid_url)

  
    def test_extract_keywords_with_valid_text(self):
        text = "This is a sample text with some common words and unique keywords."
        
        result = self.keyword_extractor.extract_keywords(text)
        self.assertIsInstance(result, dict, "Expected a dictionary response from extract_keywords")
        self.assertGreater(len(result), 0, "Expected non-empty keyword extraction")

    def test_extract_keywords_empty_text(self):
        empty_text = ""
        
        result = self.keyword_extractor.extract_keywords(empty_text)
        self.assertIsInstance(result, dict, "Expected a dictionary response from extract_keywords")
        self.assertEqual(len(result), 0, "Expected empty dictionary for empty input text")

    def test_extract_keywords_stopwords_only(self):
        stopwords_text = "the and or but if when"
        
   
        result = self.keyword_extractor.extract_keywords(stopwords_text)
        self.assertEqual(result, {}, "Expected an empty dictionary when input text has only stopwords")


if __name__ == "__main__":
    unittest.main()
