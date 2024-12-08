import logging
from abc import ABC, abstractmethod
from functools import wraps
from aop_wrapper import Aspect

class TrustScore:
    """Class to calculate the trustworthiness of a news article based on various metrics."""

    def __init__(self, strategy):
        self.strategy = strategy  # strategy for calculating the score
        self.ml_model_prediction = 0.0
        self.source_credibility = 0
        self.sentiment_subjectivity = 0
        self.content_consistency = 0
        self.final_trust_score = None

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def calculate_score(self):
        """Calculates the final trust score based on the selected strategy."""
        self.final_trust_score = self.strategy.calculate(self)
        return self.final_trust_score
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def display_score(self):
        """Displays the calculated trust score."""
        return (
            f"Calculated Trust Score: {self.final_trust_score:.2f}"
            if self.final_trust_score is not None
            else "Trust Score not calculated"
        )

class ScoringStrategy(ABC):
    """Abstract base class for scoring strategy."""

    @abstractmethod
    def calculate(self, trust_score):
        pass

class SimpleAverageStrategy(ScoringStrategy):
    """Strategy for calculating score as a simple average."""

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def calculate(self, trust_score):
        # Calculate the simple average of the metrics
        return (
            (trust_score.ml_model_prediction +
             trust_score.source_credibility +
             trust_score.sentiment_subjectivity +
             trust_score.content_consistency) / 4
        )

class WeightedAverageStrategy(ScoringStrategy):
    """Strategy for calculating score as a weighted average."""

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def calculate(self, trust_score):
        # Calculate the weighted average based on predefined weights
        return (
            (0.6 * trust_score.ml_model_prediction +
             0.2 * trust_score.source_credibility +
             0.1 * trust_score.sentiment_subjectivity +
             0.1 * trust_score.content_consistency)
        )
