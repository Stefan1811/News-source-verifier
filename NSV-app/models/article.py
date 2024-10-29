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
        self.trust_score = None  # Score representing the article's credibility
        self.status = "unverified"  # Status of the article: "unverified" or "verified"
        
    def analyze_sentiment(self):
        """
        Analyzes the sentiment of the article's content.
        - Sentiment score will be used as a factor in the trust score calculation.
        """
        pass
    
    def extract_keywords(self):
        """
        Extracts relevant keywords from the article's content.
        - Used to highlight main themes and assess potential bias.
        """
        pass

    def check_consistency(self):
        """
        Checks the consistency of the content to assess credibility.
        - Checks for factual alignment with other reputable sources.
        """
        pass

    def __str__(self):
        """
        Returns a string summary of the article with title, author, and status.
        - Example: "Title: [Title], Author: [Author], Status: [Status]"
        """
        pass
