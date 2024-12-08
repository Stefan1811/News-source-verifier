import pytest
from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from ..models.tweet import Tweet

# Creează o aplicație Flask pentru testare și inițializează SQLAlchemy
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    # Conectează modelul Tweet la acest db
    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture
def db(app):
    return SQLAlchemy(app)

@pytest.fixture
def client(app, db):
    with app.test_client() as testing_client:
        yield testing_client

@pytest.fixture
def add_sample_tweet(db):
    with db.session.begin():  # Deschidem o sesiune de DB pentru testare
        tweet = Tweet(
            url="http://example.com",
            content="Sample tweet for testing",
            author_name="Tester",
            author_username="testuser",
            tweet_id="test123"
        )
        db.session.add(tweet)
    return tweet

def test_get_all_tweets(client, db):
    response = client.get(url_for('get_all_tweets'))
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_get_specific_tweet(client, add_sample_tweet):
    tweet = add_sample_tweet
    response = client.get(url_for('get_tweet', tweet_id=tweet.tweet_id))
    assert response.status_code == 200
    data = response.get_json()
    assert data['content'] == tweet.content
    assert data['tweet_id'] == tweet.tweet_id
