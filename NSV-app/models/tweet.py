from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from tweepy_api import TweepyScraper
from community_notes import get_tweet_info_from_notes
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
    """Validates the Tweet ID from the request URL."""
    tweet_id = req.view_args.get('tweet_id') if req.view_args else None
    if tweet_id and not tweet_id.isdigit():
        print(f"Tweet ID validation failed: {tweet_id}")
        logging.error(f"Invalid Tweet ID: {tweet_id} for request to {req.path}")
    elif tweet_id:
        print(f"Tweet ID validation passed: {tweet_id}")
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
BEARER_TOKEN = "bearer_token"
tweepy_scraper = TweepyScraper(BEARER_TOKEN)

@app.route('/tweets', methods=['GET'])
def get_all_tweets():
    """Get all tweets."""
    tweets = Tweet.query.all()
    return jsonify([tweet.to_dict() for tweet in tweets]), 200

@app.route('/tweets/<tweet_id>', methods=['GET'])
def get_tweet(tweet_id):
    """Get a single tweet by ID."""
    try:
        validate_tweet_id(tweet_id)  # Validează tweet_id
    except ValueError as e:
        logging.error(f"Invalid Tweet ID: {tweet_id}. Error: {e}")
        return jsonify({"error": str(e)}), 400
    tweet = Tweet.query.get(tweet_id)
    if not tweet:
        return jsonify({"error": "Tweet not found"}), 404
    return jsonify(tweet.to_dict()), 200


@app.route('/tweets', methods=['POST'])
def create_tweet():
    """Create a new tweet."""
    data = request.json
    try:
        # Extract data from Tweepy API and community notes
        tweet_url = data.get('url')
        if not tweet_url:
            return jsonify({"error": "Tweet URL is required"}), 400

        # Extract Tweepy and community notes data
        tweepy_data = json.loads(tweepy_scraper.extract_data(tweet_url))
        tweet_id = tweepy_scraper._extract_tweet_id(tweet_url)
        notes_data = get_tweet_info_from_notes(tweet_id, "notes.tsv") or {}

        # Create Tweet object
        tweet = Tweet(
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

        # Afișează obiectul creat în consolă
        print("Tweet object created:")
        print(tweet.to_dict())  # sau str(tweet) dacă implementezi __str__

        # Add to database
        db.session.add(tweet)
        db.session.commit()
        return jsonify(tweet.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@mop.monitor(lambda tweet_id: isinstance(tweet_id, int) and tweet_id > 0, lambda _: 1)
def validate_tweet_id(tweet_id):
    return tweet_id
@app.route('/tweets/<tweet_id>', methods=['DELETE'])
def delete_tweet(tweet_id):
    """Delete a tweet."""
    tweet = Tweet.query.get(tweet_id)
    if not tweet:
        return jsonify({"error": "Tweet not found"}), 404
    try:
        db.session.delete(tweet)
        db.session.commit()
        return jsonify({"message": "Tweet deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/tweets/<tweet_id>', methods=['PUT'])
def update_tweet(tweet_id):
    """Update a tweet by ID."""
    data = request.json
    tweet = Tweet.query.get(tweet_id)

    if not tweet:
        return jsonify({"error": "Tweet not found"}), 404

    try:
        # Actualizare câmpuri doar dacă există în payload
        tweet.url = data.get('url', tweet.url)
        tweet.content = data.get('content', tweet.content)
        tweet.author_name = data.get('author_name', tweet.author_name)
        tweet.author_username = data.get('author_username', tweet.author_username)
        tweet.author_location = data.get('author_location', tweet.author_location)
        tweet.author_description = data.get('author_description', tweet.author_description)
        tweet.author_verified = data.get('author_verified', tweet.author_verified)
        tweet.author_created_at = datetime.fromisoformat(data['author_created_at']) if data.get(
            'author_created_at') else tweet.author_created_at
        tweet.tweet_created_at = datetime.fromisoformat(data['tweet_created_at']) if data.get(
            'tweet_created_at') else tweet.tweet_created_at
        tweet.retweet_count = data.get('retweet_count', tweet.retweet_count)
        tweet.reply_count = data.get('reply_count', tweet.reply_count)
        tweet.like_count = data.get('like_count', tweet.like_count)
        tweet.quote_count = data.get('quote_count', tweet.quote_count)
        tweet.bookmark_count = data.get('bookmark_count', tweet.bookmark_count)
        tweet.impression_count = data.get('impression_count', tweet.impression_count)
        tweet.note_id = data.get('note_id', tweet.note_id)
        tweet.note_author_participant_id = data.get('note_author_participant_id', tweet.note_author_participant_id)
        tweet.note_created_at = datetime.fromisoformat(data['note_created_at']) if data.get(
            'note_created_at') else tweet.note_created_at
        tweet.tweet_id = data.get('tweet_id', tweet.tweet_id)
        tweet.classification = data.get('classification', tweet.classification)
        tweet.misleading_context = data.get('misleading_context', tweet.misleading_context)
        tweet.trustworthy_sources = data.get('trustworthy_sources', tweet.trustworthy_sources)
        tweet.summary = data.get('summary', tweet.summary)

        # Salvează modificările în baza de date
        db.session.commit()
        return jsonify(tweet.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":

    app.run(debug=True)