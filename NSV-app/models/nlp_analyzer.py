import requests
import re
import nltk
import nltk
import re
from collections import Counter
from langdetect import detect
from textblob import TextBlob
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from collections import Counter
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

nltk.download('stopwords')

class KeywordExtractor:
    """
    Extracts keywords from text, calculates their frequency, and assigns sentiment to each keyword.
    """
    def __init__(self, sentiment_analyzer):
        self.sentiment_analyzer = sentiment_analyzer
        self.stop_words = set(stopwords.words('english'))  # Using NLTK stopwords

    def extract_keywords(self, text):
        
    
        words = [word.lower() for word in re.findall(r'\b\w+\b', text) if word.lower() not in self.stop_words]
        word_freq = Counter(words)

        keyword_sentiments = {}
        for word in word_freq:
            sentiment = self.sentiment_analyzer.analyze_text(word)
            keyword_sentiments[word] = (word_freq[word], sentiment["sentiment"])

        return keyword_sentiments

    def save_keywords_to_file(self, keywords, filename="keywords_summary.txt"):
       
        with open(filename, "w", encoding="utf-8") as file:
            for word, (freq, sentiment) in keywords.items():
                file.write(f"Keyword: {word}, Frequency: {freq}, Sentiment: {sentiment}\n")
        print(f"Keywords saved to {filename}")


class ArticleSummary:
  
    def __init__(self, analysis_results):
        self.analysis_results = analysis_results

    def generate_summary(self):
       
        sentiment = self.analysis_results["sentiment"]
        article_snippet = self.analysis_results["article_text"]

        summary = f"Article Summary:\n\nSentiment: {sentiment}\n\nArticle Excerpt: {article_snippet}...\n\nFor full article text, please visit the source link."
        return summary

    def save_summary_to_file(self, filename="article_summary.txt"):
      
        summary = self.generate_summary()
        with open(filename, "w", encoding="utf-8") as file:
            file.write(summary)
        print(f"Article summary saved to {filename}")



class ArticleParser:
    """
    Responsible for extracting the text content from a given article URL.
    """
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
    
    def remove_unwanted_content(self, soup):

        for unwanted in soup(['header', 'footer', 'nav', 'aside', 'script', 'style']): 
            unwanted.decompose()  

    def save_article_text_to_file(self, article_text, filename="article_text.txt"):
    
        with open(filename, "w", encoding="utf-8") as file:
            file.write(article_text)
        print(f"Article saved to {filename}")


class SentimentAnalyzer(ABC):
    """
    An abstract base class for sentiment analysis strategies.
    """
    @abstractmethod
    def analyze_text(self, text):
        """
        Analyzes the sentiment of the provided text.
        """
        pass


class TextBlobSentimentAnalyzer(SentimentAnalyzer):
    """
    A sentiment analyzer using TextBlob for more accurate sentiment analysis.
    """
    def analyze_text(self, text):
    
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        # Classify sentiment based on polarity
        if polarity > 0:
            sentiment = "Positive"
        elif polarity < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        return {"sentiment": sentiment}


class VaderSentimentAnalyzer(SentimentAnalyzer):
    """
    A sentiment analyzer using VADER for more accurate sentiment analysis.
    """
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_text(self, text):
       
        score = self.analyzer.polarity_scores(text)['compound']
        
        # Classify sentiment based on score
        if score > 0.05:
            sentiment = "Positive"
        elif score < -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        return {"sentiment": sentiment}


class ArticleVerifier:
    """
    The main orchestrator of the NLP analysis, bringing together the various components.
    """
    def __init__(self):
        self.parser = ArticleParser()
        self.sentiment_analyzer = TextBlobSentimentAnalyzer()  # Or VaderSentimentAnalyzer()

    def process_article(self, url):
        """
        Takes the article URL as input, performs the NLP analysis, and returns a summary of the results.
        """

        article_text = self.parser.extract_article_text(url)

 
        sentiment = self.sentiment_analyzer.analyze_text(article_text)


        analysis_results = {
            "sentiment": sentiment["sentiment"],
            "article_text": article_text[:30000]  
        }

        return analysis_results



