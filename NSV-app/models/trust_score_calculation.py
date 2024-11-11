import logging
from abc import ABC, abstractmethod
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_execution(func):
    """Decorator for logging method execution and return values."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        class_name = args[0].__class__.__name__
        function_name = func.__name__

        try:
            result = func(*args, **kwargs)
            logging.info(f"{class_name} _ {function_name} _ returned: {result}")
            return result

        except Exception as e:
            logging.error(f"{class_name} _ {function_name} _ raised an error: {e}")
            raise

    return wrapper

class TrustScore:
    """Class to calculate the trustworthiness of a news article based on various metrics."""

    def __init__(self, strategy):
        self.strategy = strategy  # strategy for calculating the score
        self.ml_model_prediction = 0.0
        self.source_credibility = 0
        self.sentiment_subjectivity = 0
        self.content_consistency = 0
        self.final_trust_score = None

    @log_execution
    def calculate_score(self):
        """Calculates the final trust score based on the selected strategy."""
        self.final_trust_score = self.strategy.calculate(self)
        return self.final_trust_score

    @log_execution
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

    @log_execution
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

    @log_execution
    def calculate(self, trust_score):
        # Calculate the weighted average based on predefined weights
        return (
            (0.6 * trust_score.ml_model_prediction +
             0.2 * trust_score.source_credibility +
             0.1 * trust_score.sentiment_subjectivity +
             0.1 * trust_score.content_consistency)
        )
