import os
import re
import sys

from textblob import TextBlob
import logging
log_file_path = os.path.join("..", "..", "logs.txt")

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_method_call(func):
    """returnată
    Decorator pentru apelurile functiilor, numele functiei, argumentele si valoarea returnata.
    """
    def wrapper(*args, **kwargs):
        class_name = args[0].__class__.__name__
        method_name = func.__name__

        logging.info(f"Calling {class_name}.{method_name} with args={args[1:]}, kwargs={kwargs}")

        result = func(*args, **kwargs)

        logging.info(f"{class_name}.{method_name} returned: {result}")

        return result
    return wrapper


class Article:
    """
    Represents a news article to be analyzed for authenticity.
    """

    def __init__(self, url, title, content, author=None, publish_date=None):
        self.url = url  # URL of the article
        self.title = title  # Title of the article
        self.content = content  # Main text content of the article
        self.author = author  # Author of the article
        self.publish_date = publish_date  # Publication date of the article
        self.ml_model_prediction = 0.0  # Prediction from a machine learning model
        self.source_credibility = 0  # Credibility of the source
        self.sentiment_subjectivity = 0  # Sentiment subjectivity of the content
        self.content_consistency = 0  # Consistency of the content
        self.trust_score = None  # Score representing the article's credibility
        self.status = "unverified"  # Status of the article: "unverified" or "verified"

    @log_method_call
    def analyze_sentiment(self):
        """
        Analyzes the sentiment of the article's content.
        - Sentiment score will be used as a factor in the trust score calculation.
        """
        # Use TextBlob to perform sentiment analysis
        blob = TextBlob(self.content)
        self.sentiment_subjectivity = blob.sentiment.subjectivity
        return self.sentiment_subjectivity


    def extract_keywords(self):
        """
        Extracts relevant keywords from the article's content.
        - Used to highlight main themes and assess potential bias.
        """
        # Use a simple keyword extraction algorithm
        keywords = re.findall(r'\w+', self.content)
        return list(set(keywords))[:3]

    @log_method_call
    def check_consistency(self):
        """
        Checks the consistency of the content to assess credibility.
        - Checks for factual alignment with other reputable sources.
        """
        # Simulate a basic consistency check
        if 'fake' in self.title.lower() or 'misinformation' in self.content.lower():
            self.status = "unverified"
            self.content_consistency = 0.3
        else:
            self.status = "verified"
            self.content_consistency = 0.9
        return self.content_consistency

    @log_method_call
    def calculate_trust_score(self, strategy):
        """
        Calculates the final trust score based on the selected strategy.
        """
        self.trust_score = strategy.calculate_trust_score(self)
        return self.trust_score

    @log_method_call
    def __str__(self):
        """
        Returns a string summary of the article with title, author, and status.
        - Example: "Title: [Title], Author: [Author], Status: [Status]"
        """
        return f"Title: {self.title}, Author: {self.author}, Status: {self.status}"

if __name__ == "__main__":
    article = Article("https://example.com", "Sample Title", "This content could contain misinformation.", "Author Name", "2024-11-11")
    print(article.analyze_sentiment())
    print(article.extract_keywords())
    print(article.check_consistency())
    # Presupunem că avem o strategie implementată cu o metodă `calculate_trust_score`
    # În exemplul de mai jos, trebuie definită strategia înainte de a o folosi
    # print(article.calculate_trust_score(strategy))
    print(article)
