from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.tweepy_api import TweepyScraper
from models.community_notes import get_tweet_info_from_notes
import logging
import mop

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'xxxxx'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@mop.monitor(
    lambda req: req.method in ['GET', 'POST', 'PUT', 'DELETE'],
    lambda req: "Invalid HTTP method"
)
def validate_http_method(req):
    """Validates the HTTP method of the request."""
    if req.method not in ['GET', 'POST', 'PUT', 'DELETE']:
        print(f"Invalid HTTP method for request with path: {req.path}")
        logging.error(f"Invalid HTTP method: {req.method} for request to {req.path}")
    else:
        print(f"HTTP method validation passed: {req.method}")
        logging.info(f"Validated HTTP method {req.method} for request to {req.path}")
    return req


@mop.monitor(
    lambda req: req.view_args and 'tweet_id' in req.view_args and req.view_args['tweet_id'].isdigit(),
    lambda req: "Invalid Tweet ID: must be numeric"
)
def validate_tweet_id_request(req):
    """Validates the Tweet ID from the request URL using guard clauses."""
    tweet_id = req.view_args.get('tweet_id')
    if not tweet_id or not tweet_id.isdigit():
        error_message = f"Invalid Tweet ID: {tweet_id} for request to {req.path}"
        logging.error(error_message)
        raise ValueError(error_message)
    logging.info(f"Validated Tweet ID {tweet_id} for request to {req.path}")
    return req



@app.before_request
def monitor_request():
    validate_http_method(request)  # Validează metoda HTTP
    if 'tweet_id' in (request.view_args or {}):  # Verifică doar dacă există un tweet_id în URL
        validate_tweet_id_request(request)  # Validează Tweet ID-ul


class Tweet(db.Model):
    __tablename__ = 'twitter_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # ID-ul generat automat de PostgreSQL
    url = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.Text, nullable=False)
    author_username = db.Column(db.Text, nullable=False)
    author_location = db.Column(db.Text, nullable=True)
    author_description = db.Column(db.Text, nullable=True)
    author_verified = db.Column(db.Boolean, nullable=False, default=False)
    author_created_at = db.Column(db.DateTime, nullable=True)  # Timestamp fără time zone
    tweet_created_at = db.Column(db.DateTime, nullable=False)  # Timestamp fără time zone
    retweet_count = db.Column(db.Integer, nullable=False, default=0)
    reply_count = db.Column(db.Integer, nullable=False, default=0)
    like_count = db.Column(db.Integer, nullable=False, default=0)
    quote_count = db.Column(db.Integer, nullable=False, default=0)
    bookmark_count = db.Column(db.Integer, nullable=False, default=0)
    impression_count = db.Column(db.Integer, nullable=False, default=0)
    note_id = db.Column(db.Text, nullable=True)
    note_author_participant_id = db.Column(db.Text, nullable=True)
    note_created_at = db.Column(db.DateTime, nullable=True)  # Timestamp fără time zone
    tweet_id = db.Column(db.Text, nullable=False, unique=True)  # ID-ul unic al tweet-ului (unic)
    classification = db.Column(db.Text, nullable=True)
    misleading_context = db.Column(db.Boolean, nullable=True)
    trustworthy_sources = db.Column(db.Boolean, nullable=True)
    summary = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'content': self.content,
            'author_name': self.author_name,
            'author_username': self.author_username,
            'author_location': self.author_location,
            'author_description': self.author_description,
            'author_verified': self.author_verified,
            'author_created_at': self.author_created_at.isoformat() if self.author_created_at else None,
            'tweet_created_at': self.tweet_created_at.isoformat() if self.tweet_created_at else None,
            'retweet_count': self.retweet_count,
            'reply_count': self.reply_count,
            'like_count': self.like_count,
            'quote_count': self.quote_count,
            'bookmark_count': self.bookmark_count,
            'impression_count': self.impression_count,
            'note_id': self.note_id,
            'note_author_participant_id': self.note_author_participant_id,
            'note_created_at': self.note_created_at.isoformat() if self.note_created_at else None,
            'tweet_id': self.tweet_id,
            'classification': self.classification,
            'misleading_context': self.misleading_context,
            'trustworthy_sources': self.trustworthy_sources,
            'summary': self.summary
        }


# Initialize TweepyScraper
BEARER_TOKEN = "xxxxx"
tweepy_scraper = TweepyScraper(BEARER_TOKEN)

@app.route('/tweets', methods=['GET'])
def get_all_tweets():
    """Get all tweets."""
    tweets = Tweet.query.all()
    return jsonify([tweet.to_dict() for tweet in tweets]), 200

def retrieve_tweet_by_id(tweet_id):
    """Retrieve a tweet by its ID from the database."""
    return Tweet.query.get(tweet_id)

def validate_tweet_existence(tweet_id):
    """Validate if the tweet exists in the database."""
    tweet = retrieve_tweet_by_id(tweet_id)
    if not tweet:
        raise ValueError("Tweet not found")
    return tweet

@app.route('/tweets/<tweet_id>', methods=['GET'])
def get_tweet(tweet_id):
    """Retrieve a single tweet by its ID."""
    try:
        tweet = validate_tweet_existence(tweet_id)
        return jsonify(tweet.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


def extract_tweet_data(tweet_url):
    """Extracts tweet data from Tweepy API and community notes."""
    if not tweet_url:
        raise ValueError("Tweet URL is required")
    tweepy_data = json.loads(tweepy_scraper.extract_data(tweet_url))
    tweet_id = tweepy_scraper._extract_tweet_id(tweet_url)
    notes_data = get_tweet_info_from_notes(tweet_id, "notes.tsv") or {}
    return tweepy_data, tweet_id, notes_data

def create_tweet_object(tweepy_data, notes_data):
    """Creates a Tweet object from Tweepy and community notes data."""
    return Tweet(
        url=tweepy_data.get('url'),
        content=tweepy_data.get('content'),
        author_name=tweepy_data.get('author_name'),
        author_username=tweepy_data.get('author_username'),
        author_location=tweepy_data.get('author_location'),
        author_description=tweepy_data.get('author_description'),
        author_verified=tweepy_data.get('author_verified'),
        author_created_at=datetime.fromisoformat(tweepy_data.get('author_created_at')) if tweepy_data.get(
            'author_created_at') else None,
        tweet_created_at=datetime.fromisoformat(tweepy_data.get('tweet_created_at')) if tweepy_data.get(
            'tweet_created_at') else None,
        retweet_count=tweepy_data.get('metrics', {}).get('retweet_count', 0),
        reply_count=tweepy_data.get('metrics', {}).get('reply_count', 0),
        like_count=tweepy_data.get('metrics', {}).get('like_count', 0),
        quote_count=tweepy_data.get('metrics', {}).get('quote_count', 0),
        bookmark_count=tweepy_data.get('metrics', {}).get('bookmark_count', 0),
        impression_count=tweepy_data.get('metrics', {}).get('impression_count', 0),
        note_id=notes_data.get('noteId'),
        note_author_participant_id=notes_data.get('noteAuthorParticipantId', None),
        note_created_at=datetime.fromtimestamp(
            int(notes_data.get('createdAtMillis')) / 1000
        ) if notes_data.get('createdAtMillis') else None,
        tweet_id=notes_data.get('tweetId'),
        classification=notes_data.get('classification'),
        misleading_context=bool(int(notes_data.get("misleadingMissingImportantContext", "0"))) if notes_data.get(
            "misleadingMissingImportantContext") else None,
        trustworthy_sources=bool(int(notes_data.get("trustworthySources", "0"))) if notes_data.get(
            "trustworthySources") else None,
        summary=notes_data.get('summary')
    )
@app.route('/tweets', methods=['POST'])
def create_tweet():
    """Create a new tweet."""
    data = request.json
    try:
        tweepy_data, tweet_id, notes_data = extract_tweet_data(data.get('url'))
        tweet = create_tweet_object(tweepy_data, notes_data)

        # Display the created object in the console
        print("Tweet object created:")
        print(tweet.to_dict())

        # Add to database
        db.session.add(tweet)
        db.session.commit()
        return jsonify(tweet.to_dict()), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@mop.monitor(lambda tweet_id: isinstance(tweet_id, int) and tweet_id > 0, lambda _: 1)
def validate_tweet_id(tweet_id):
    return tweet_id
@app.route('/tweets/<tweet_id>', methods=['DELETE'])
def delete_tweet(tweet_id):
    """Delete a tweet by ID."""
    try:
        tweet = validate_tweet_existence(tweet_id)
        db.session.delete(tweet)
        db.session.commit()
        return jsonify({"message": "Tweet deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def update_fields(tweet, data):
    """Update fields of tweet based on provided data."""
    for field in ['url', 'content', 'author_name', 'author_username', 'author_location',
                  'author_description', 'author_verified', 'author_created_at', 'tweet_created_at',
                  'retweet_count', 'reply_count', 'like_count', 'quote_count', 'bookmark_count',
                  'impression_count', 'note_id', 'note_author_participant_id', 'note_created_at',
                  'tweet_id', 'classification', 'misleading_context', 'trustworthy_sources', 'summary']:
        if field in data:
            setattr(tweet, field, data.get(field, getattr(tweet, field)))
@app.route('/tweets/<tweet_id>', methods=['PUT'])
def update_tweet(tweet_id):
    """Update a tweet by ID using a helper function for database query and field update."""
    data = request.json
    tweet = retrieve_tweet_by_id(tweet_id)
    if not tweet:
        return jsonify({"error": "Tweet not found"}), 404
    try:
        update_fields(tweet, data)
        db.session.commit()
        return jsonify(tweet.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":

    app.run(debug=True)