from abc import ABC, abstractmethod


class TrustScore:
    """Class to calculate the trustworthiness of a news article based on various metrics."""

    def __init__(self, strategy):
        self.strategy = strategy  # strategy for calculating the score
        self.ml_model_prediction = 0.0
        self.source_credibility = 0
        self.sentiment_subjectivity = 0
        self.content_consistency = 0

    def calculate_score(self):
        """Calculates the final trust score based on the selected strategy."""
        pass

    def display_score(self):
        """Displays the calculated trust score."""
        pass


class ScoringStrategy(ABC):
    """Abstract base class for scoring strategy."""

    @abstractmethod
    def calculate(self, trust_score):
        pass


class SimpleAverageStrategy(ScoringStrategy):
    """Strategy for calculating score as a simple average."""

    def calculate(self, trust_score):
        pass


class WeightedAverageStrategy(ScoringStrategy):
    """Strategy for calculating score as a weighted average."""

    # trust_score = (0.6 * ml_model_prediction + 0.2 * source_credibility +
    #                0.1 * sentiment_subjectivity +  0.1 * content_consistency)

    def calculate(self, trust_score):
        pass
