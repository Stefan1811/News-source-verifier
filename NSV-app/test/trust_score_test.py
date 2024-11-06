import unittest
from ..models.trust_score_calculation import TrustScore, SimpleAverageStrategy, WeightedAverageStrategy

class TestTrustScore(unittest.TestCase):

    def setUp(self):
        # Initialize dummy data for testing
        self.dummy_ml_model_prediction = 0.7
        self.dummy_source_credibility = 80
        self.dummy_sentiment_subjectivity = 50
        self.dummy_content_consistency = 60

    def test_calculate_score(self):
        strategies = [
            (SimpleAverageStrategy(), (
                        self.dummy_ml_model_prediction + self.dummy_source_credibility + self.dummy_sentiment_subjectivity + self.dummy_content_consistency) / 4),
            (WeightedAverageStrategy(),
             0.6 * self.dummy_ml_model_prediction + 0.2 * self.dummy_source_credibility + 0.1 * self.dummy_sentiment_subjectivity + 0.1 * self.dummy_content_consistency)
        ]

        for strategy, expected_score in strategies:
            # Initialize TrustScore with the current strategy
            trust_score = TrustScore(strategy)
            trust_score.ml_model_prediction = self.dummy_ml_model_prediction
            trust_score.source_credibility = self.dummy_source_credibility
            trust_score.sentiment_subjectivity = self.dummy_sentiment_subjectivity
            trust_score.content_consistency = self.dummy_content_consistency

            score = trust_score.calculate_score()
            self.assertIsNotNone(score)

            self.assertAlmostEqual(score, expected_score, places=2)

    def test_display_score(self):
        trust_score = TrustScore(SimpleAverageStrategy())
        result = trust_score.display_score()
        self.assertEqual(result, "Trust Score not calculated")

        trust_score.final_trust_score = 47.67
        result = trust_score.display_score()
        self.assertEqual(result, "Calculated Trust Score: 47.67")


if __name__ == '__main__':
    unittest.main()
