import logging
import requests
import re
from collections import Counter, defaultdict
from nltk.corpus import stopwords
from textblob import TextBlob
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
from datetime import datetime

# Download NLTK stopwords if not already installed
nltk.download('stopwords')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper functions
def get_class_name(instance):
    return instance.__class__.__name__

def log_execution(func):
    def wrapper(self, *args, **kwargs):
        class_name = get_class_name(self)
        func_name = func.__name__
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"[{timestamp}] Entering {class_name}.{func_name}")
        
        try:
            result = func(self, *args, **kwargs)
            logging.info(f"[{timestamp}] Exiting {class_name}.{func_name}")
            return result
        except Exception as e:
            logging.error(f"[{timestamp}] Error in {class_name}.{func_name}: {e}")
            raise
    return wrapper

# Monitors
class Monitor(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def observe(self, *args, **kwargs):
        pass

    @abstractmethod
    def verify(self, *args, **kwargs):
        pass

    def log_event(self, event):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"[{timestamp}] {self.name} - {event}")

    def trigger_action(self, action):
        self.log_event(f"Action triggered: {action}")

# Article Parser Monitor
class ArticleParserMonitor(Monitor):
    def __init__(self):
        super().__init__("ArticleParserMonitor")

    def observe(self, article_text):
        if not article_text:
            self.trigger_action("No article text found")
        else:
            self.log_event(f"Article text parsed successfully: {article_text[:50]}...")

    def verify(self, article_text):
        if len(article_text) < 100:
            self.trigger_action("Article text is too short")
        else:
            self.log_event("Article text verification passed")

# Keyword Extractor Monitor
class KeywordExtractorMonitor(Monitor):
    def __init__(self):
        super().__init__("KeywordExtractorMonitor")

    def observe(self, keywords):
        if not keywords:
            self.trigger_action("No keywords extracted")
        else:
            self.log_event(f"Keywords extracted: {len(keywords)} keywords found.")

    def verify(self, keywords, min_frequency=2):
        invalid_keywords = [word for word, data in keywords.items() if data["frequency"] < min_frequency]
        if invalid_keywords:
            self.trigger_action(f"Low frequency keywords detected: {invalid_keywords}")
        else:
            self.log_event("Keyword frequency verification passed")

# Sentiment Analyzer Monitor
class SentimentAnalyzerMonitor(Monitor):
    def __init__(self):
        super().__init__("SentimentAnalyzerMonitor")

    def observe(self, sentiment_result):
        if sentiment_result not in ["Positive", "Negative", "Neutral"]:
            self.trigger_action(f"Unexpected sentiment: {sentiment_result}")
        else:
            self.log_event(f"Sentiment detected: {sentiment_result}")

    def verify(self, sentiment_result):
        if sentiment_result == "Neutral":
            self.trigger_action("Neutral sentiment detected")
        else:
            self.log_event(f"Sentiment verified: {sentiment_result}")

# Keyword Extractor Class
class KeywordExtractor:
    def __init__(self, sentiment_analyzers):
        self.sentiment_analyzers = sentiment_analyzers
        self.stop_words = set(stopwords.words('english'))

    @log_execution
    def extract_keywords(self, text):
        sentences = text.split('.') 
        word_freq = Counter(re.findall(r'\b\w+\b', text.lower()))
        
        keyword_sentiments = defaultdict(lambda: {"frequency": 0, "vader_score": 0, "sentiment_counts": Counter()})
        
        for sentence in sentences:
            sentence = sentence.strip()
            words = [word for word in re.findall(r'\b\w+\b', sentence.lower()) if word not in self.stop_words]
            for word in words:
                keyword_sentiments[word]["frequency"] += 1
                
                for analyzer in self.sentiment_analyzers:
                    result = analyzer.analyze_text(sentence)
                    
                    if "vader_score" in result:
                        keyword_sentiments[word]["vader_score"] += result["vader_score"]
                    
                    keyword_sentiments[word]["sentiment_counts"][result["sentiment"]] += 1

        for word, data in keyword_sentiments.items():
            data["vader_score"] /= data["frequency"]  
            data["sentiment"] = data["sentiment_counts"].most_common(1)[0][0]

        sorted_keywords = dict(sorted(keyword_sentiments.items(), key=lambda item: item[1]["frequency"], reverse=True))
        return sorted_keywords

    @log_execution
    def save_keywords_to_file(self, keywords, filename="keywords_summary.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            for word, data in keywords.items():
                file.write(f"Keyword: {word}, Frequency: {data['frequency']}, Sentiment: {data['sentiment']}, Average VADER Score: {data['vader_score']:.2f}\n")
        logging.info(f"Keywords saved to {filename}")

# Article Summary Class
class ArticleSummary:
    def __init__(self, analysis_results):
        self.analysis_results = analysis_results

    @log_execution
    def generate_summary(self):
        sentiment = self.analysis_results["sentiment"]
        article_snippet = self.analysis_results["article_text"]
        summary = f"Article Summary:\n\nSentiment: {sentiment}\n\nArticle Excerpt: {article_snippet}...\n\nFor full article text, please visit the source link."
        return summary

    @log_execution
    def save_summary_to_file(self, filename="article_summary.txt"):
        summary = self.generate_summary()
        with open(filename, "w", encoding="utf-8") as file:
            file.write(summary)
        logging.info(f"Article summary saved to {filename}")

# Article Parser Class
class ArticleParser:
    @log_execution
    def extract_article_text(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            self.remove_unwanted_content(soup)

            article = soup.find("article")
            if article:
                text = article.get_text()
            else:
                paragraphs = soup.find_all("p")
                text = ' '.join([p.get_text() for p in paragraphs])

            return text.strip()

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error fetching the article: {e}")
        except Exception as e:
            raise Exception(f"An error occurred while processing the article: {e}")

    @log_execution
    def remove_unwanted_content(self, soup):
        for unwanted in soup(['header', 'footer', 'nav', 'aside', 'script', 'style']):
            unwanted.decompose()

    @log_execution
    def save_article_text_to_file(self, article_text, filename="article_text.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            file.write(article_text)
        logging.info(f"Article saved to {filename}")

# Sentiment Analyzer Interface
class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze_text(self, text):
        pass

# TextBlob Sentiment Analyzer
class TextBlobSentimentAnalyzer(SentimentAnalyzer):
    @log_execution
    def analyze_text(self, text):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
        return {"sentiment": sentiment}

# VADER Sentiment Analyzer
class VaderSentimentAnalyzer(SentimentAnalyzer):
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    @log_execution
    def analyze_text(self, text):
        score = self.analyzer.polarity_scores(text)['compound']
        sentiment = "Positive" if score > 0.05 else "Negative" if score < -0.05 else "Neutral"
        return {"sentiment": sentiment, "vader_score": score}

# Main Function
def main():
    url = "https://edition.cnn.com/2024/11/12/politics/trump-team-loyalists-analysis/index.html"

    sentiment_analyzers = [TextBlobSentimentAnalyzer(), VaderSentimentAnalyzer()]
    keyword_extractor = KeywordExtractor(sentiment_analyzers)
    parser = ArticleParser()

    # Create monitor instances
    article_monitor = ArticleParserMonitor()
    keyword_monitor = KeywordExtractorMonitor()
    sentiment_monitor = SentimentAnalyzerMonitor()

    try:
        # Parse the article
        article_text = parser.extract_article_text(url)
        parser.save_article_text_to_file(article_text, "article_text.txt")
        print("Article text saved to 'article_text.txt'.")
        article_monitor.observe(article_text)
        article_monitor.verify(article_text)

        # Extract keywords
        keywords = keyword_extractor.extract_keywords(article_text)
        keyword_extractor.save_keywords_to_file(keywords, "keywords_summary.txt")
        keyword_monitor.observe(keywords)
        keyword_monitor.verify(keywords)

        # Sentiment analysis
        sentiments = []
        for analyzer in sentiment_analyzers:
            sentiment_result = analyzer.analyze_text(article_text)
            sentiment_monitor.observe(sentiment_result['sentiment'])
            sentiment_monitor.verify(sentiment_result['sentiment'])
            sentiments.append(sentiment_result)
        
        # Generate summary and save
        summary = ArticleSummary({
            "article_text": article_text,
            "sentiment": sentiments[0]['sentiment'],
        })
        summary.save_summary_to_file("article_summary.txt")
        logging.info("Article analysis completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during the process: {e}")

if __name__ == "__main__":
    main()
