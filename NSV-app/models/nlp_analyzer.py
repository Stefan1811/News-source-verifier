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
from aop_wrapper import Aspect

nltk.download('stopwords')

def get_class_name(instance):
    return instance.__class__.__name__

class Monitor:
    @staticmethod
    def validate_keyword_extraction(keywords):
        if not keywords:
            logging.error("No keywords extracted.")
            raise ValueError("Keyword extraction failed, no keywords found.")
        else:
            logging.info(f"Keyword extraction validated. {len(keywords)} keywords found.")

    @staticmethod
    def validate_sentiment_analysis(keywords):
        for word, data in keywords.items():
            if data["sentiment"] not in ["Positive", "Negative", "Neutral"]:
                logging.error(f"Invalid sentiment for keyword: {word}")
                raise ValueError(f"Invalid sentiment for keyword: {word}")
        logging.info("Sentiment analysis validated for all keywords.")

    @staticmethod
    def validate_url(url):
        regex = re.compile(r'^(https?://)?[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})')
        if not regex.match(url):
            logging.error(f"Invalid URL: {url}")
            raise ValueError(f"Invalid URL: {url}")
        logging.info(f"URL is valid: {url}")

    @staticmethod
    def validate_article_content(article_text):
        if len(article_text) < 100:  # Minimum length for a valid article
            logging.error("Article content is too short to be valid.")
            raise ValueError("Article content is too short.")
        logging.info(f"Article content validated. Length: {len(article_text)} characters.")

    @staticmethod
    def validate_sentiment_score(sentiment_score, source=""):
        if not (-1 <= sentiment_score <= 1):
            logging.error(f"Sentiment score out of range: {sentiment_score} from {source}")
            raise ValueError(f"Sentiment score out of range: {sentiment_score}")
        logging.info(f"Sentiment score validated for {source}: {sentiment_score}")

    @staticmethod
    def validate_sentiment_distribution(keywords):
        sentiment_counts = Counter([data["sentiment"] for data in keywords.values()])
        if sentiment_counts["Positive"] < 1 or sentiment_counts["Negative"] < 1:
            logging.warning(f"Imbalanced sentiment distribution: {sentiment_counts}")
        else:
            logging.info(f"Sentiment distribution: {sentiment_counts}")

    @staticmethod
    def validate_execution_time(start_time, end_time, process_name):
        elapsed_time = end_time - start_time
        elapsed_seconds = elapsed_time.total_seconds()  # Convert timedelta to seconds
        if elapsed_seconds > 5:  # Arbitrary threshold for process duration in seconds
            logging.warning(f"{process_name} took too long: {elapsed_seconds:.2f} seconds")
        else:
            logging.info(f"{process_name} completed in {elapsed_seconds:.2f} seconds.")


    @staticmethod
    def validate_keyword_frequency(keywords):
        frequencies = [data["frequency"] for data in keywords.values()]
        max_frequency = max(frequencies)
        if max_frequency > 20:  # Arbitrary threshold for frequent keywords
            logging.warning(f"Keyword with excessive frequency detected: {max_frequency}")
        logging.info(f"Keyword frequencies validated. Max frequency: {max_frequency}")

    @staticmethod
    def validate_data_completeness(data):
        required_keys = ["frequency", "sentiment", "vader_score"]
        for word, values in data.items():
            missing_keys = [key for key in required_keys if key not in values]
            if missing_keys:
                logging.error(f"Missing keys for keyword {word}: {missing_keys}")
                raise ValueError(f"Missing keys for keyword {word}: {missing_keys}")
        logging.info("Data completeness validated.")

    @staticmethod
    def validate_exception_handling(exception):
        logging.error(f"Exception encountered: {exception}")
        raise exception  # Reraising the exception can help to propagate the error

    @staticmethod
    def validate_log_integrity():
        log_file = "app.log"  # Or the actual log file name you're using
        with open(log_file, "r") as file:
            logs = file.readlines()
            if len(logs) < 10:  # Ensure enough log entries are generated
                logging.warning("Log file contains insufficient log entries.")
            logging.info("Log file integrity validated.")


class KeywordExtractor:
    def __init__(self, sentiment_analyzers):
        self.sentiment_analyzers = sentiment_analyzers
        self.stop_words = set(stopwords.words('english'))

    @Aspect.log_execution
    @Aspect.measure_time
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

        Monitor.validate_keyword_extraction(sorted_keywords)
        Monitor.validate_sentiment_analysis(sorted_keywords)
        Monitor.validate_sentiment_distribution(sorted_keywords)
        Monitor.validate_keyword_frequency(sorted_keywords)

        return sorted_keywords

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def save_keywords_to_file(self, keywords, filename="keywords_summary.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            for word, data in keywords.items():
                file.write(f"Keyword: {word}, Frequency: {data['frequency']}, Sentiment: {data['sentiment']}, Average VADER Score: {data['vader_score']:.2f}\n")
        logging.info(f"Keywords saved to {filename}")

class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze_text(self, text):
        pass

class TextBlobSentimentAnalyzer(SentimentAnalyzer):
    def analyze_text(self, text):
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity
        sentiment = "Neutral"
        if sentiment_score > 0:
            sentiment = "Positive"
        elif sentiment_score < 0:
            sentiment = "Negative"
        return {"sentiment": sentiment, "score": sentiment_score}

class VaderSentimentAnalyzer(SentimentAnalyzer):
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_text(self, text):
        sentiment_score = self.analyzer.polarity_scores(text)["compound"]
        sentiment = "Neutral"
        if sentiment_score > 0:
            sentiment = "Positive"
        elif sentiment_score < 0:
            sentiment = "Negative"
        return {"sentiment": sentiment, "vader_score": sentiment_score}

class ArticleParser:
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def extract_article_text(self, url):
        Monitor.validate_url(url)
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

            Monitor.validate_article_content(text)
            return text.strip()

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error fetching the article: {e}")
        except Exception as e:
            raise Exception(f"An error occurred while processing the article: {e}")

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def remove_unwanted_content(self, soup):
        for unwanted in soup(['header', 'footer', 'nav', 'aside', 'script', 'style']):
            unwanted.decompose()

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def save_article_text_to_file(self, article_text, filename="article_text.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            file.write(article_text)
        logging.info(f"Article text saved to {filename}")


# Abstract SentimentAnalyzer class
class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze_text(self, text):
        pass

# TextBlob-based SentimentAnalyzer implementation
class TextBlobSentimentAnalyzer(SentimentAnalyzer):
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def analyze_text(self, text):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
        return {"sentiment": sentiment}


class VaderSentimentAnalyzer(SentimentAnalyzer):
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def analyze_text(self, text):
        score = self.analyzer.polarity_scores(text)['compound']
        sentiment = "Positive" if score > 0.05 else "Negative" if score < -0.05 else "Neutral"
        return {"sentiment": sentiment, "vader_score": score}

def main():
    url = "https://edition.cnn.com/2024/11/12/politics/trump-team-loyalists-analysis/index.html"

    sentiment_analyzers = [TextBlobSentimentAnalyzer(), VaderSentimentAnalyzer()]
    keyword_extractor = KeywordExtractor(sentiment_analyzers)
    parser = ArticleParser()

    try:
        # Extract article text from the URL
        article_text = parser.extract_article_text(url)
        parser.save_article_text_to_file(article_text, "article_text.txt")
        print("Article text saved to 'article_text.txt'.")

        # Validate article content
        Monitor.validate_article_content(article_text)

        # Extract and analyze keywords from the article text
        keywords = keyword_extractor.extract_keywords(article_text)
        keyword_extractor.save_keywords_to_file(keywords, "keywords_summary.txt")
        print("Keywords and their sentiments saved to 'keywords_summary.txt'.")

        # Validate keyword extraction and sentiment analysis
        Monitor.validate_keyword_extraction(keywords)
        Monitor.validate_sentiment_analysis(keywords)
        Monitor.validate_sentiment_distribution(keywords)
        Monitor.validate_keyword_frequency(keywords)
        Monitor.validate_data_completeness(keywords)

        # Validate sentiment analysis scores for individual keywords
        for word, data in keywords.items():
            Monitor.validate_sentiment_score(data["vader_score"], word)

        # Simulate monitoring execution time by comparing start and end times
        start_time = datetime.now()
        # Assuming some operation happens here...
        end_time = datetime.now()
        Monitor.validate_execution_time(start_time, end_time, "Keyword extraction")

        print("\nExtracted Keywords and Sentiments:")
        for word, data in keywords.items():
            print(f"Keyword: {word}, Frequency: {data['frequency']}, Sentiment: {data['sentiment']}, Average VADER Score: {data['vader_score']:.2f}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the main function if the script is executed
if __name__ == "__main__":
    main()

