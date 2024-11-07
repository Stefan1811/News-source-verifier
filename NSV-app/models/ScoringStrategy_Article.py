from abc import ABC, abstractmethod

class ScoringStrategy(ABC):
    """Abstract base class for scoring strategy."""
    @abstractmethod
    def calculate_trust_score(self, article):
        pass

class SimpleAverageStrategy(ScoringStrategy):
    """Strategy for calculating trust score as a simple average."""
    def calculate_trust_score(self, article):
        # Calculate the simple average of the metrics
        return (
            (article.ml_model_prediction +
             article.source_credibility +
             article.sentiment_subjectivity +
             article.content_consistency) / 4
        )

class WeightedAverageStrategy(ScoringStrategy):
    """Strategy for calculating trust score as a weighted average."""
    def calculate_trust_score(self, article):
        # Calculate the weighted average based on predefined weights
        return (
            (0.6 * article.ml_model_prediction +
             0.2 * article.source_credibility +
             0.1 * article.sentiment_subjectivity +
             0.1 * article.content_consistency)
        )
