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


class KeywordExtractor:
    def __init__(self, sentiment_analyzers):
        self.sentiment_analyzers = sentiment_analyzers
        self.stop_words = set(stopwords.words('english'))

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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


    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def save_keywords_to_file(self, keywords, filename="keywords_summary.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            for word, data in keywords.items():
                file.write(f"Keyword: {word}, Frequency: {data['frequency']}, Sentiment: {data['sentiment']}, Average VADER Score: {data['vader_score']:.2f}\n")
        logging.info(f"Keywords saved to {filename}")

class ArticleSummary:
    def __init__(self, analysis_results):
        self.analysis_results = analysis_results

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def generate_summary(self):
        sentiment = self.analysis_results["sentiment"]
        article_snippet = self.analysis_results["article_text"]
        summary = f"Article Summary:\n\nSentiment: {sentiment}\n\nArticle Excerpt: {article_snippet}...\n\nFor full article text, please visit the source link."
        return summary
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def save_summary_to_file(self, filename="article_summary.txt"):
        summary = self.generate_summary()
        with open(filename, "w", encoding="utf-8") as file:
            file.write(summary)
        logging.info(f"Article summary saved to {filename}")

class ArticleParser:
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
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
        logging.info(f"Article saved to {filename}")

class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze_text(self, text):
        pass

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
        article_text = parser.extract_article_text(url)
        parser.save_article_text_to_file(article_text, "article_text.txt")
        print("Article text saved to 'article_text.txt'.")

        keywords = keyword_extractor.extract_keywords(article_text)
        keyword_extractor.save_keywords_to_file(keywords, "keywords_summary.txt")
        print("Keywords and their sentiments saved to 'keywords_summary.txt'.")

        print("\nExtracted Keywords and Sentiments:")
        for word, data in keywords.items():
            print(f"Keyword: {word}, Frequency: {data['frequency']}, Sentiment: {data['sentiment']}, Average VADER Score: {data['vader_score']:.2f}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
