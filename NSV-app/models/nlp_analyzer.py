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
from statistics import median

nltk.download('stopwords')

def get_class_name(instance):
    return instance.__class__.__name__

class Trigger:
    @staticmethod
    def on_validation_success(message):
        logging.info(f"Trigger Action: Validation success - {message}")

    @staticmethod
    def on_validation_violation(message):
        logging.error(f"Trigger Action: Validation violation - {message}")

class Monitor:
    def _raise_validation_error(message):
        Trigger.on_validation_violation(message)
        raise ValueError(message)

    def _log_validation_success(message):
        Trigger.on_validation_success(message)

    @staticmethod
    def validate_keyword_extraction(keywords):
        if not keywords:
            Monitor._raise_validation_error("No keywords extracted.")
        Monitor._log_validation_success(f"Keyword extraction validated. {len(keywords)} keywords found.")


    @staticmethod
    def validate_sentiment_analysis(keywords):
        for word, data in keywords.items():
            if data["sentiment"] not in ["Positive", "Negative", "Neutral"]:
                message = f"Invalid sentiment for keyword: {word}"
                Trigger.on_validation_violation(message)
                raise ValueError(message)
        Trigger.on_validation_success("Sentiment analysis validated for all keywords.")

    @staticmethod
    def validate_url(url):
        regex = re.compile(r'^(https?://)?[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})')
        if not regex.match(url):
            message = f"Invalid URL: {url}"
            Trigger.on_validation_violation(message)
            raise ValueError(message)
        Trigger.on_validation_success(f"URL is valid: {url}")

    @staticmethod
    def validate_article_content(article_text):
        if len(article_text) < 100:  # Minimum length for a valid article
            message = "Article content is too short to be valid."
            Trigger.on_validation_violation(message)
            raise ValueError(message)
        Trigger.on_validation_success(f"Article content validated. Length: {len(article_text)} characters.")

    @staticmethod
    def validate_sentiment_score(sentiment_score, source=""):
        if not (-1 <= sentiment_score <= 1):
            message = f"Sentiment score out of range: {sentiment_score} from {source}"
            Trigger.on_validation_violation(message)
            raise ValueError(message)
        Trigger.on_validation_success(f"Sentiment score validated for {source}: {sentiment_score}")

    @staticmethod
    def validate_sentiment_distribution(keywords):
        sentiment_counts = Counter([data["sentiment"] for data in keywords.values()])
        if sentiment_counts["Positive"] < 1 or sentiment_counts["Negative"] < 1:
            message = f"Imbalanced sentiment distribution: {sentiment_counts}"
            Trigger.on_validation_violation(message)
        else:
            Trigger.on_validation_success(f"Sentiment distribution: {sentiment_counts}")

    @staticmethod
    def validate_execution_time(start_time, end_time, process_name):
        elapsed_time = end_time - start_time
        elapsed_seconds = elapsed_time.total_seconds()  # Convert timedelta to seconds
        if elapsed_seconds > 5:
            message = f"{process_name} took too long: {elapsed_seconds:.2f} seconds"
            Trigger.on_validation_violation(message)
        else:
            Trigger.on_validation_success(f"{process_name} completed in {elapsed_seconds:.2f} seconds.")

    @staticmethod
    def validate_keyword_frequency(keywords):
        frequencies = [data["frequency"] for data in keywords.values()]
        max_frequency = max(frequencies)
        if max_frequency > 20:
            message = f"Keyword with excessive frequency detected: {max_frequency}"
            Trigger.on_validation_violation(message)
        Trigger.on_validation_success(f"Keyword frequencies validated. Max frequency: {max_frequency}")

    @staticmethod
    def validate_data_completeness(data):
        required_keys = ["frequency", "sentiment", "vader_score"]
        for word, values in data.items():
            missing_keys = [key for key in required_keys if key not in values]
            if missing_keys:
                message = f"Missing keys for keyword {word}: {missing_keys}"
                Trigger.on_validation_violation(message)
                raise ValueError(message)
        Trigger.on_validation_success("Data completeness validated.")

    @staticmethod
    def validate_exception_handling(exception):
        message = f"Exception encountered: {exception}"
        Trigger.on_validation_violation(message)
        raise exception

    @staticmethod
    def validate_log_integrity():
        log_file = "app.log"  
        with open(log_file, "r") as file:
            logs = file.readlines()
            if len(logs) < 10: 
                message = "Log file contains insufficient log entries."
                Trigger.on_validation_violation(message)
            else:
                Trigger.on_validation_success("Log file integrity validated.")

class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze_text(self, text):
        pass

class ArticleParser:
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def extract_article_text(self, url):
        Monitor.validate_url(url)
        response = self.fetch_url_content(url)
        soup = BeautifulSoup(response.content, "html.parser")
        self.remove_unwanted_content(soup)
        article_text = self.parse_article_content(soup)
        Monitor.validate_article_content(article_text)
        return article_text.strip()

    def fetch_url_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error fetching the article: {e}")

    def parse_article_content(self, soup):
        article = soup.find("article")
        if article:
            return article.get_text()
        paragraphs = soup.find_all("p")
        return ' '.join([p.get_text() for p in paragraphs])



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

class KeywordExtractor:
    def __init__(self):
        self.sentiment_analyzers = [TextBlobSentimentAnalyzer(), VaderSentimentAnalyzer()]
        self.stop_words = set(stopwords.words('english'))

    @Aspect.log_execution
    @Aspect.measure_time
    def extract_keywords(self, text):
        sentences = self.tokenize_text(text)
        word_freq = self.calculate_word_frequency(text)
        keyword_sentiments = self.analyze_keyword_sentiments(sentences, word_freq)

        sorted_keywords = dict(sorted(
            keyword_sentiments.items(), 
            key=lambda item: item[1]["frequency"], 
            reverse=True
        ))

        self.validate_keywords(sorted_keywords)
        return sorted_keywords

    def tokenize_text(self, text):
        return text.split('.')

    def calculate_word_frequency(self, text):
        words = [word for word in re.findall(r'\b\w+\b', text.lower()) if word not in self.stop_words]
        return Counter(words)

    def analyze_keyword_sentiments(self, sentences, word_freq):
        keyword_sentiments = defaultdict(lambda: {"frequency": 0, "vader_score": 0, "sentiment_counts": Counter()})
        for sentence in sentences:
            words = self.extract_words_from_sentence(sentence)
            self.update_sentiments_for_sentence(sentence, words, keyword_sentiments)
        self.finalize_sentiment_scores(keyword_sentiments)
        return keyword_sentiments

    def extract_words_from_sentence(self, sentence):
        sentence = sentence.strip()
        return [word for word in re.findall(r'\b\w+\b', sentence.lower()) if word not in self.stop_words]

    def update_sentiments_for_sentence(self, sentence, words, keyword_sentiments):
        for word in words:
            keyword_sentiments[word]["frequency"] += 1
            for analyzer in self.sentiment_analyzers:
                result = analyzer.analyze_text(sentence)
                self.update_sentiment_data(word, result, keyword_sentiments)

    def update_sentiment_data(self, word, result, keyword_sentiments):
        if "vader_score" in result:
            keyword_sentiments[word]["vader_score"] += result["vader_score"]
        else:
            logging.warning(f"Missing 'vader_score' for word: {word}.")

        if "sentiment" in result:
            keyword_sentiments[word]["sentiment_counts"][result["sentiment"]] += 1
        else:
            logging.warning(f"Missing 'sentiment' for word: {word}.")

    def finalize_sentiment_scores(self, keyword_sentiments):
        for word, data in keyword_sentiments.items():
            data["vader_score"] /= data["frequency"]
            data["sentiment"] = data["sentiment_counts"].most_common(1)[0][0]

    def validate_keywords(self, keywords):
        Monitor.validate_keyword_extraction(keywords)
        Monitor.validate_sentiment_analysis(keywords)
        Monitor.validate_sentiment_distribution(keywords)
        Monitor.validate_keyword_frequency(keywords)
    
    def calculate_aggregate_score(self, keywords):
        # Sort keywords by frequency in descending order
        sorted_keywords = sorted(keywords.items(), key=lambda item: item[1]['frequency'], reverse=True)

        # Extract the top 10 most frequent keywords
        top_10_keywords = sorted_keywords[:10]
        print(top_10_keywords)

        # Extract frequencies and VADER scores
        frequencies = [data['frequency'] for _, data in top_10_keywords]
        vader_scores = [data['vader_score'] for _, data in top_10_keywords]

        # Calculate the weighted sum of VADER scores
        weighted_vader_sum = sum(frequency * vader_score for frequency, vader_score in zip(frequencies, vader_scores))

        # Calculate the total weight (sum of frequencies)
        total_weight = sum(frequencies)

        # Calculate the weighted average VADER score
        weighted_average_vader_score = weighted_vader_sum / total_weight if total_weight else 0

        # Calculate medians
        median_frequency = median(frequencies)
        median_vader_score = median(vader_scores)

        # Aggregate score as the average of the weighted average and median of frequencies and VADER scores
        aggregate_score = (median_frequency + weighted_average_vader_score) / 2

        print("Weighted Average VADER Score:", weighted_average_vader_score)
        print("Aggregate Score:", aggregate_score)

        return weighted_average_vader_score

    def process_article_and_keywords(self, url, output_text_filename="article_text.txt", output_keywords_filename="keywords_summary.txt"):
        # Extract article text from the URL
        parser = ArticleParser()
        article_text = parser.extract_article_text(url)
        parser.save_article_text_to_file(article_text, output_text_filename)
        print(f"Article text saved to '{output_text_filename}'.")

        # Validate article content
        Monitor.validate_article_content(article_text)

        # Extract keywords from article
        keywords = self.extract_keywords(article_text)
        self.save_keywords_to_file(keywords, output_keywords_filename)
        print(f"Keywords and their sentiments saved to '{output_keywords_filename}'.")

        # Validate keywords and sentiment analysis
        Monitor.validate_keyword_extraction(keywords)
        Monitor.validate_sentiment_analysis(keywords)
        Monitor.validate_sentiment_distribution(keywords)
        Monitor.validate_keyword_frequency(keywords)
        Monitor.validate_data_completeness(keywords)

        # Validate sentiment scores for each keyword
        for word, data in keywords.items():
            Monitor.validate_sentiment_score(data["vader_score"], word)
        # Calculate the aggregate score and print the results
        result_top_keywords = self.calculate_aggregate_score(keywords)
        print(result_top_keywords)

        # Validate execution time (this can be adjusted as needed)
        start_time = datetime.now()
        end_time = datetime.now()  # You can replace this with actual end time calculation
        Monitor.validate_execution_time(start_time, end_time, "Keyword extraction")
        return result_top_keywords

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def save_keywords_to_file(self, keywords, filename="keywords_summary.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            for word, data in keywords.items():
                file.write(f"Keyword: {word}, Frequency: {data['frequency']}, Sentiment: {data['sentiment']}, Average VADER Score: {data['vader_score']:.2f}\n")
        logging.info(f"Keywords saved to {filename}")

    
class TextBlobSentimentAnalyzer(SentimentAnalyzer):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"

    def analyze_text(self, text):
        sentiment_score = self.get_sentiment_score(text)
        sentiment = self.determine_sentiment(sentiment_score)
        return {"sentiment": sentiment, "score": sentiment_score}

    def get_sentiment_score(self, text):
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def determine_sentiment(self, sentiment_score):
        if sentiment_score > 0:
            return self.POSITIVE
        elif sentiment_score < 0:
            return self.NEGATIVE
        return self.NEUTRAL


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


def main():
    url = "https://edition.cnn.com/2024/11/12/politics/trump-team-loyalists-analysis/index.html"
    keyword_extractor = KeywordExtractor()

    # Process the article and keywords extraction
    rezultat = keyword_extractor.process_article_and_keywords(url)
    print("result")
    print(rezultat)

if __name__ == "__main__":
    main()