from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from collections import Counter

from sqlalchemy import desc

from aop_wrapper import Aspect
import re
import sys
import mop
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Conv1D, MaxPooling1D, Bidirectional, GlobalMaxPool1D, Input, \
    Dropout
from tensorflow.keras.models import load_model
from nltk.corpus import stopwords

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from model_prep.model_testing import fake_news_det, predict_news
from nlp_analyzer import KeywordExtractor

keyword_extractor = KeywordExtractor

app.config['SQLALCHEMY_DATABASE_URI'] = 'xxxxxx'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

model = load_model('model_prep/fake_news_model.h5')
stop = stopwords.words('english')


@mop.monitor(
    lambda req: req.method in ['GET', 'POST', 'PUT', 'DELETE'] and
                'url' in req.json and len(req.json.get('url', '').strip()) > 0,
    lambda req: "Invalid request: HTTP method or URL field is invalid"
)
def validate_request(req):
    """HTTP request validation."""
    if req.method not in ['GET', 'POST', 'PUT', 'DELETE']:
        print(f"Invalid HTTP method for request with path: {req.path}")
    elif 'url' not in req.json or len(req.json.get('url', '').strip()) == 0:
        print(f"URL validation failed for request with path: {req.path}")
        print(f"Request data: {req.json}")
    else:
        print(f"Request validation passed for request with path: {req.path}")
        print(f"Accessed {req.path} with {req.method}")
    logging.info(f"Validated {req.method} request to {req.path} with data {req.json}")
    return req


def validate_content(req):
    """Validates the content field after scraping."""
    if 'content' in req.json and len(req.json.get('content', '').strip()) > 0:
        print(f"Content validation passed for request with path: {req.path}")
    else:
        print(f"Content validation failed for request with path: {req.path}")
        print(f"Request data: {req.json}")
    return req


def validate_non_null_fields(req):
    """Validates that required fields are not null."""
    required_fields = ['url', 'title', 'content', 'author', 'publish_date']
    for field in required_fields:
        if not req.json.get(field):
            print(f"{field} validation failed for request with path: {req.path}")
            print(f"Request data: {req.json}")
            return req
    print(f"All required fields validation passed for request with path: {req.path}")
    return req


@app.before_request
def monitor_request():
    validate_request(request)


from textblob import TextBlob
import logging

from scraper_engine import BeautifulSoupScraper

logging.basicConfig(
    filename='logs.txt',
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


class Article(db.Model):
    __tablename__ = 'articles'

    article_id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String, nullable=True)
    publish_date = db.Column(db.DateTime, nullable=True)
    ml_model_prediction = db.Column(db.Float, nullable=True)
    source_credibility = db.Column(db.Float, nullable=True)
    sentiment_subjectivity = db.Column(db.Float, nullable=True)
    content_consistency = db.Column(db.Float, nullable=True)
    trust_score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def to_dict(self):
        return {
            'article_id': self.article_id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'ml_model_prediction': self.ml_model_prediction,
            'source_credibility': self.source_credibility,
            'sentiment_subjectivity': self.sentiment_subjectivity,
            'content_consistency': self.content_consistency,
            'trust_score': self.trust_score,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @log_method_call

    def analyze_sentiment(self, url):


        result = keyword_extractor.process_article_and_keywords(url)  # VADER score (-1 to 1)

        print(result)

        result_normalized = (result + 1) / 2  # Converts -1 to 1 range into 0 to 1

        blob = TextBlob(self.content)

        blob_sentiment = blob.sentiment.polarity  # Sentiment polarity (-1 to 1)

        blob_sentiment_normalized = (blob_sentiment + 1) / 2

        self.sentiment_subjectivity = (0.3 * result_normalized) + (0.7 * blob_sentiment_normalized)

        print(self.sentiment_subjectivity)

        return self.sentiment_subjectivity

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def extract_keywords(self):
        """
        Extracts relevant keywords from the article's content.
        - Used to highlight main themes and assess potential bias.
        """
        # Use a simple keyword extraction algorithm
        keywords = re.findall(r'\w+', self.content)
        return list(set(keywords))[:3]

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @log_method_call
    def check_consistency(self):
        """
        Checks the consistency of the content to assess credibility.
        - Checks for factual alignment with other reputable sources.
        - Checks for the presence of keywords indicating potential misinformation.
        - Checks for the length of the content.
        """
        # Keywords indicating potential misinformation
        misinformation_keywords = ['fake', 'misinformation', 'conspiracy', 'false', 'debunked', 'fraud',
                                   'scam', 'unverified', 'unreliable', 'unsubstantiated', 'rumor', 'fabricated',
                                   'rau', 'fals', 'neadevarat', 'dezinformare', 'conspiratie', 'frauda',
                                   'escrocherie', 'nemotivat', 'nerecunoscut', 'nejustificat', 'zvon', 'fabricat']
        reputable_sources = ['bbc', 'cnn', 'reuters', 'nytimes', 'theguardian',
                             'washingtonpost', 'wsj', 'bloomberg', 'apnews', 'npr',
                             'digi24', 'stirileprotv', 'antena3',
                             'realitatea', 'gandul', 'adevarul', 'ziare']

        # Check for misinformation keywords in title and content
        if any(keyword in self.title.lower() for keyword in misinformation_keywords) or \
                any(keyword in self.content.lower() for keyword in misinformation_keywords):
            content_consistency = 0.3
        else:
            content_consistency = 0.9

        # Check for reputable sources in the content
        if any(self.url in self.content.lower() for source in reputable_sources):
            content_consistency += 0.1

        # Check for content length
        if len(self.content) < 500:
            content_consistency -= 0.1

        blob = TextBlob(self.content)
        sentiment_score = blob.sentiment.polarity
        if sentiment_score < -0.5:
            sentiment_consistency = 0.4
        elif sentiment_score > 0.5:
            sentiment_consistency = 1.0
        else:
            sentiment_consistency = 0.8

        words = self.content.lower().split()
        word_counts = Counter(words)
        # Check for repetitive words = 5 times or more means that the article is not consistent
        repetitive_words = [word for word, count in word_counts.items() if count > 5]
        if repetitive_words:
            content_consistency -= 0.1

        # 5. mean between content and sentiment consistency
        self.content_consistency = (content_consistency + sentiment_consistency) / 2.0

        # Ensure consistency score is within bounds
        self.content_consistency = max(0.0, min(self.content_consistency, 1.0))

        if self.content_consistency < 0.6:
            self.status = "unverified"
        else:
            self.status = "verified"

        return self.content_consistency

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @log_method_call
    def calculate_trust_score(self, strategy):
        """
        Calculates the final trust score based on the selected strategy.
        """
        self.trust_score = strategy.calculate_trust_score(self)
        return self.trust_score

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @log_method_call
    def __str__(self):
        """
        Returns a string summary of the article with title, author, and status.
        - Example: "Title: [Title], Author: [Author], Status: [Status]"
        """
        return f"Title: {self.title}, Author: {self.author}, Status: {self.status}"


@app.route('/articles', methods=['GET'])
def get_all_articles():
    """Get all articles."""
    articles = Article.query.all()
    return jsonify([article.to_dict() for article in articles]), 200


@app.route('/latest-articles', methods=['GET'])
def get_latest_articles():
    # Selectăm ultimele 5 articole ordonate descrescător după created_at
    latest_articles = Article.query.order_by(desc(Article.created_at)).limit(5).all()
    articles_list = [article.to_dict() for article in latest_articles]
    return jsonify(articles_list), 200


@app.route('/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Get a single article by ID."""
    article = Article.query.get(article_id)
    if article is None:
        return jsonify({"error": "Article not found"}), 404
    return jsonify(article.to_dict()), 200


@app.route('/articles/<path:url>', methods=['GET'])
def get_article_url(url):
    """Get a single article by URL."""
    article = Article.query.filter_by(url=url).first()
    if article is None:
        return jsonify({"error": "Article not found"}), 404
    return jsonify(article.to_dict()), 200


@app.route('/articles', methods=['POST'])
def create_article():
    """Create a new article."""
    data = request.json
    try:
        article = Article(
            url=data.get('url'),
            title=data.get('title'),
            content=data.get('content'),
            author=data.get('author'),
            publish_date=datetime.fromisoformat(data.get('publish_date')) if data.get('publish_date') else None,
            ml_model_prediction=data.get('ml_model_prediction', 0.0),
            source_credibility=data.get('source_credibility'),
            sentiment_subjectivity=data.get('sentiment_subjectivity'),
            content_consistency=data.get('content_consistency'),
            trust_score=data.get('trust_score'),
            status=data.get('status')
        )

        # Validate content after creating the article
        request.json['content'] = article.content
        validate_non_null_fields(request)

        db.session.add(article)
        db.session.commit()
        return jsonify(article.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


scraper = BeautifulSoupScraper()


@app.route('/articles/scrape', methods=['POST'])
def scrape_and_create_article():
    """
    For an URL -> use scraper_engine to extract data.
    """
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        article_data = scraper.extract_data(url)

        if not article_data:
            return jsonify({"error": "Failed to extract data from the provided URL"}), 500

        # Validate content after scraping
        request.json['content'] = article_data.get('content', '')
        validate_content(request)

        try:
            publish_date = datetime.fromisoformat(article_data['publish_date']) if article_data.get(
                'publish_date') else None
        except ValueError:
            publish_date = None

        article = Article(
            url=article_data.get('url'),
            title=article_data.get('title'),
            content=article_data.get('content'),
            author=article_data.get('author'),
            publish_date=publish_date,
            ml_model_prediction=0.0,
            source_credibility=0.0,
            sentiment_subjectivity=0.0,
            content_consistency=0.0,
            trust_score=None,
            status="unverified"
        )

        # aici se pot adăuga metode pentru analiza sentimentului și verificarea consistenței - astea sunt doar asa de test
        article.analyze_sentiment(url)
        article.check_consistency()

        article_content_no_paragraphs = article.content.replace('\n', ' ').replace('\r', ' ')
        print(f"Content without paragraphs: {article_content_no_paragraphs}")

        # Preprocess the article content for prediction
        prediction = predict_news(article_content_no_paragraphs)
        print(prediction)
        article.ml_model_prediction = prediction
        article.trust_score = 0.5 * article.ml_model_prediction + 0.3 * article.sentiment_subjectivity + 0.2 * article.content_consistency

        db.session.add(article)
        db.session.commit()

        return jsonify(article.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """Update an existing article."""
    data = request.json
    article = Article.query.get(article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
    try:
        article.url = data.get('url', article.url)
        article.title = data.get('title', article.title)
        article.content = data.get('content', article.content)
        article.author = data.get('author', article.author)
        article.publish_date = data.get('publish_date', article.publish_date)
        article.ml_model_prediction = data.get('ml_model_prediction', article.ml_model_prediction)
        article.source_credibility = data.get('source_credibility', article.source_credibility)
        article.sentiment_subjectivity = data.get('sentiment_subjectivity', article.sentiment_subjectivity)
        article.content_consistency = data.get('content_consistency', article.content_consistency)
        article.trust_score = data.get('trust_score', article.trust_score)
        article.status = data.get('status', article.status)
        db.session.commit()
        return jsonify(article.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@app.route('/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """Delete an article."""
    article = Article.query.get(article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
    try:
        db.session.delete(article)
        db.session.commit()
        return jsonify({"message": "Article deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    

@app.route('/articles/analyze', methods=['POST'])

def analyze_article():

    try:

        data = request.json
        url = data.get('url')

        if not url:

            return jsonify({"error": "URL is required"}), 400

        result = keyword_extractor.process_article_and_keywords(url)

        return jsonify({'score': result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500





if __name__ == "__main__":
    # article = Article("https://example.com", "Sample Title", "This content could contain misinformation.", "Author Name", "2024-11-11")
    # print(article.analyze_sentiment())
    # print(article.extract_keywords())
    # print(article.check_consistency())
    # Presupunem că avem o strategie implementată cu o metodă `calculate_trust_score`
    # În exemplul de mai jos, trebuie definită strategia înainte de a o folosi
    # print(article.calculate_trust_score(strategy))
    # print(article)
    app.run(debug=True)