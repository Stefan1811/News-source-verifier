import logging
import requests
import re
from collections import Counter
from nltk.corpus import stopwords
from textblob import TextBlob
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
from datetime import datetime

nltk.download('stopwords')

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper to get the class name from instance methods
def get_class_name(instance):
    return instance.__class__.__name__

# Define a decorator for logging
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

class KeywordExtractor:
    def __init__(self, sentiment_analyzer):
        self.sentiment_analyzer = sentiment_analyzer
        self.stop_words = set(stopwords.words('english'))

    @log_execution
    def extract_keywords(self, text):
        words = [word.lower() for word in re.findall(r'\b\w+\b', text) if word.lower() not in self.stop_words]
        word_freq = Counter(words)

        keyword_sentiments = {}
        for word in word_freq:
            sentiment = self.sentiment_analyzer.analyze_text(word)
            keyword_sentiments[word] = (word_freq[word], sentiment["sentiment"])

        return keyword_sentiments

    @log_execution
    def save_keywords_to_file(self, keywords, filename="keywords_summary.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            for word, (freq, sentiment) in keywords.items():
                file.write(f"Keyword: {word}, Frequency: {freq}, Sentiment: {sentiment}\n")
        logging.info(f"Keywords saved to {filename}")

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

class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze_text(self, text):
        pass

class TextBlobSentimentAnalyzer(SentimentAnalyzer):
    @log_execution
    def analyze_text(self, text):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
        return {"sentiment": sentiment}

class VaderSentimentAnalyzer(SentimentAnalyzer):
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    @log_execution
    def analyze_text(self, text):
        score = self.analyzer.polarity_scores(text)['compound']
        sentiment = "Positive" if score > 0.05 else "Negative" if score < -0.05 else "Neutral"
        return {"sentiment": sentiment}

class ArticleVerifier:
    def __init__(self):
        self.parser = ArticleParser()
        self.sentiment_analyzer = TextBlobSentimentAnalyzer() 

    @log_execution
    def process_article(self, url):
        article_text = self.parser.extract_article_text(url)
        sentiment = self.sentiment_analyzer.analyze_text(article_text)
        analysis_results = {
            "sentiment": sentiment["sentiment"],
            "article_text": article_text[:30000]
        }
        return analysis_results


def main():
 
    url = "https://www.digi24.ro/stiri/actualitate/trump-este-primul-inculpat-penal-ales-presedinte-ce-se-intampla-acum-cu-dosarele-sale-penale-si-civile-2997019" 

    sentiment_analyzer = TextBlobSentimentAnalyzer()
    keyword_extractor = KeywordExtractor(sentiment_analyzer)
    parser = ArticleParser()

    try:
        article_text = parser.extract_article_text(url)
        parser.save_article_text_to_file(article_text, "article_text.txt")
        print("Article text saved to 'article_text.txt'.")


        keywords = keyword_extractor.extract_keywords(article_text)
        keyword_extractor.save_keywords_to_file(keywords, "keywords_summary.txt")
        print("Keywords and their sentiments saved to 'keywords_summary.txt'.")


        print("\nExtracted Keywords and Sentiments:")
        for word, (freq, sentiment) in keywords.items():
            print(f"Keyword: {word}, Frequency: {freq}, Sentiment: {sentiment}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
