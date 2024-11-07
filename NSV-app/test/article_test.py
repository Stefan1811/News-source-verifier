import unittest
from models.article import Article
from models.ScoringStrategy_Article import SimpleAverageStrategy, WeightedAverageStrategy

class TestArticle(unittest.TestCase):

    def setUp(self):
        # Dummy article for testing
        self.dummy_article = Article(
            url="https://www.example.com/fake-news-article",
            title="Fake News on Climate Change",
            content="This is some content about fake news...",
            author="John Doe",
            publish_date="2024-11-07"
        )

        # Set the dummy article's metric values
        self.dummy_article.ml_model_prediction = 0.7
        self.dummy_article.source_credibility = 80
        self.dummy_article.sentiment_subjectivity = 50
        self.dummy_article.content_consistency = 60

    def test_analyze_sentiment(self):
        # Test the analyze_sentiment method
        self.dummy_article.analyze_sentiment()
        self.assertIsNotNone(self.dummy_article.sentiment_subjectivity)
        self.assertGreater(self.dummy_article.sentiment_subjectivity, 0)

    def test_extract_keywords(self):
        # Test the extract_keywords method
        keywords = self.dummy_article.extract_keywords()
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)

    def test_check_consistency(self):
        # Test the check_consistency method
        self.dummy_article.check_consistency()
        self.assertIn(self.dummy_article.status, ["unverified", "verified"])
        self.assertIsNotNone(self.dummy_article.content_consistency)

    def test_calculate_score_simple_average(self):
        # Test the calculate_trust_score method with SimpleAverageStrategy
        simple_average_strategy = SimpleAverageStrategy()
        score = self.dummy_article.calculate_trust_score(simple_average_strategy)
        self.assertIsNotNone(score)
        self.assertAlmostEqual(score, (0.7 + 80 + 50 + 60) / 4, places=2)

    def test_calculate_score_weighted_average(self):
        # Test the calculate_trust_score method with WeightedAverageStrategy
        weighted_average_strategy = WeightedAverageStrategy()
        score = self.dummy_article.calculate_trust_score(weighted_average_strategy)
        self.assertIsNotNone(score)
        self.assertAlmostEqual(score, 0.6 * 0.7 + 0.2 * 80 + 0.1 * 50 + 0.1 * 60, places=2)

if __name__ == '__main__':
    unittest.main()
