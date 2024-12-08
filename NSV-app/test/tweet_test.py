import csv
import sys
import os
from datetime import datetime
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch
from flask import request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from models.tweet import app, Tweet, validate_http_method, validate_tweet_id_request  # Importă aplicația, baza de date și modelul Tweet
from models.community_notes import extract_tweet_id, get_tweet_info_from_notes, validate_tsv, clean_tsv
from models.tweepy_api import TweepyScraper

import json



class TestTweetModel(unittest.TestCase):
    def test_to_dict(self):
        """Testează metoda to_dict a clasei Tweet."""
        tweet = Tweet(
            url="https://twitter.com/some_tweet",
            content="This is a test tweet",
            author_name="Test User",
            author_username="testuser",
            author_location="New York",
            author_description="Test description",
            author_verified=True,
            author_created_at=datetime(2021, 12, 1, 12, 0, 0),
            tweet_created_at=datetime(2024, 12, 1, 12, 0, 0),
            retweet_count=10,
            reply_count=5,
            like_count=50,
            quote_count=2,
            bookmark_count=1,
            impression_count=100,
            note_id="12345",
            note_author_participant_id="67890",
            note_created_at=datetime(2024, 12, 1, 12, 0, 0),
            tweet_id="123456789",
            classification="NOT_MISLEADING",
            misleading_context=False,
            trustworthy_sources=True,
            summary="This is a test summary"
        )

        expected_dict = {
            'id': None,
            'url': "https://twitter.com/some_tweet",
            'content': "This is a test tweet",
            'author_name': "Test User",
            'author_username': "testuser",
            'author_location': "New York",
            'author_description': "Test description",
            'author_verified': True,
            'author_created_at': "2021-12-01T12:00:00",
            'tweet_created_at': "2024-12-01T12:00:00",
            'retweet_count': 10,
            'reply_count': 5,
            'like_count': 50,
            'quote_count': 2,
            'bookmark_count': 1,
            'impression_count': 100,
            'note_id': "12345",
            'note_author_participant_id': "67890",
            'note_created_at': "2024-12-01T12:00:00",
            'tweet_id': "123456789",
            'classification': "NOT_MISLEADING",
            'misleading_context': False,
            'trustworthy_sources': True,
            'summary': "This is a test summary"
        }

        self.assertEqual(tweet.to_dict(), expected_dict)

    def test_get_all_tweets(self):
        """Testează endpoint-ul GET /tweets."""
        with app.test_client() as client:
            response = client.get('/tweets')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIsInstance(data, list)


class TestGetTweetById(unittest.TestCase):
    def setUp(self):
        """Set up the application context and test client for each test."""
        self.app = app  # Make sure 'app' is the Flask instance
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()

    @patch('models.tweet.Tweet.query.get')  # Mock pentru baza de date
    def test_get_tweet_not_found(self, mock_query_get):
        """Testează endpoint-ul GET /tweets/<tweet_id> pentru un tweet inexistent."""
        mock_query_get.return_value = None  # Simulează că nu există tweet-ul

        with app.test_client() as client:
            response = client.get('/tweets/999')
            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertEqual(data['error'], "Tweet not found")

    @patch('models.tweet.Tweet.query')
    def test_get_tweet_by_id_one(self, mock_query):
        """Test retrieving tweet with ID 1."""
        # Create a mock Tweet object
        mock_tweet = Tweet()
        mock_tweet.id = 1
        mock_tweet.url = "https://x.com/i/web/status/1786492191503753256"
        mock_tweet.content = "A message from President Shafik. https://t.co/zd8i2DE4wp"
        mock_tweet.author_name = "Columbia University"
        mock_tweet.author_username = "Columbia"
        mock_tweet.author_location = "New York, New York"
        mock_tweet.author_description = "News, events, ideas, and perspectives from Columbia University in the City of New York. Social media policy: https://t.co/o6XGMp58vK"
        mock_tweet.author_verified = False
        mock_tweet.author_created_at = datetime.strptime("2011-02-07 18:58:59", "%Y-%m-%d %H:%M:%S")
        mock_tweet.tweet_created_at = datetime.strptime("2024-05-03 20:25:04", "%Y-%m-%d %H:%M:%S")
        mock_tweet.retweet_count = 467
        mock_tweet.reply_count = 9311
        mock_tweet.like_count = 2460
        mock_tweet.quote_count = 2671
        mock_tweet.bookmark_count = 1800
        mock_tweet.impression_count = 8093029
        mock_tweet.note_id = "1786538789428433129"
        mock_tweet.note_author_participant_id = "D004E8957493120443356E0B5A549A5BAA8F624049C26AF18DA5111DCA61E9F7"
        mock_tweet.note_created_at = datetime.strptime("2024-05-04 02:30:14.342", "%Y-%m-%d %H:%M:%S.%f")
        mock_tweet.tweet_id = "1786492191503753256"
        mock_tweet.classification = "NOT_MISLEADING"
        mock_tweet.misleading_context = False
        mock_tweet.trustworthy_sources = True
        mock_tweet.summary = "NNN. This is a statement. It expresses a view. Some proposed notes appear to argue that Ms.Shafik is saying that these are the first protests at the university; however she clearly does not make such a claim. There are no glaring factual errors."

        # Set the mock to return the tweet when get is called with ID 1
        mock_query.get.return_value = mock_tweet

        # Make a GET request to the endpoint
        response = self.client.get('/tweets/1')
        self.assertEqual(response.status_code, 200)

        # Check the returned data
        data = response.get_json()
        self.assertEqual(data['tweet_id'], '1786492191503753256')
        self.assertEqual(data['content'], 'A message from President Shafik. https://t.co/zd8i2DE4wp')


class TestValidateHttpMethod(unittest.TestCase):

    def setUp(self):
        """Setează contextul aplicației pentru fiecare test."""
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Înlătură contextul aplicației după fiecare test."""
        self.app_context.pop()
    def test_validate_http_method_valid(self):
        """Testează o metodă HTTP validă."""
        with app.test_request_context('/', method='GET'):
            response = validate_http_method(request)
            self.assertEqual(request.method, 'GET')  # Verificăm metoda request-ului

    def test_validate_http_method_invalid(self):
        """Testează o metodă HTTP invalidă."""
        with self.assertLogs('root', level='ERROR') as cm:
            with app.test_request_context('/', method='PATCH'):
                response = validate_http_method(request)
                self.assertEqual(request.method, 'PATCH')  # Verificăm că metoda PATCH este acceptată
                # Verificăm că logul conține mesajul corect
                self.assertIn("Invalid HTTP method: PATCH", cm.output[0])




class TestCreateTweet(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('models.tweepy_api.TweepyScraper.extract_data')
    @patch('models.community_notes.get_tweet_info_from_notes')
    @patch('models.tweet.db.session.add')
    @patch('models.tweet.db.session.commit')
    def test_create_tweet_success(self, mock_commit, mock_add, mock_get_info, mock_extract_data):
        # Setup mock return values
        mock_extract_data.return_value = json.dumps({
            'url': 'https://x.com/i/web/status/1786492191503753256',
            'content': 'A message from President Shafik.',
            'author_name': 'Columbia University',
            'author_username': 'Columbia',
            'author_location': 'New York, New York',
            'author_description': 'News, events, ideas, and perspectives from Columbia University.',
            'author_verified': False,
            'author_created_at': '2011-02-07T18:58:59',
            'tweet_created_at': '2024-05-03T20:25:04',
            'metrics': {
                'retweet_count': 467,
                'reply_count': 9311,
                'like_count': 2460,
                'quote_count': 2671,
                'bookmark_count': 1800,
                'impression_count': 8093029
            }
        })

        mock_get_info.return_value = {
            'noteId': '1786538789428433129',
            'noteAuthorParticipantId': 'D004E8957493120443356E0B5A549A5BAA8F624049C26AF18DA5111DCA61E9F7',
            'createdAtMillis': '1651659014342',
            'tweetId': '1786492191503753256',
            'classification': 'NOT_MISLEADING',
            'misleadingMissingImportantContext': '0',
            'trustworthySources': '1',
            'summary': 'This is a statement from President Shafik.'
        }

        # Data to be sent to POST endpoint
        data = {
            'url': 'https://x.com/i/web/status/1786492191503753256'
        }

        # Send POST request
        response = self.app.post('/tweets', data=json.dumps(data), content_type='application/json')

        # Check the response
        self.assertEqual(response.status_code, 201)
        self.assertIn('Columbia University', str(response.data))

    @patch('models.tweepy_api.TweepyScraper.extract_data', side_effect=Exception("Failed to extract data"))
    def test_create_tweet_failure(self, mock_extract_data):
        # Data to be sent to POST endpoint
        data = {
            'url': 'https://x.com/i/web/status/invalid_url'
        }

        # Send POST request
        response = self.app.post('/tweets', data=json.dumps(data), content_type='application/json')

        # Check the response for failure
        self.assertEqual(response.status_code, 500)
        self.assertIn('Failed to extract data', str(response.data))

class TestCreateTweetMissingURL(unittest.TestCase):
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True

    def test_create_tweet_missing_url(self):
        """Test creating a tweet without a URL in the request."""
        # Data without 'url'
        data = {}

        # Send POST request
        response = self.app.post('/tweets', data=json.dumps(data), content_type='application/json')

        # Check that the status code is 400
        self.assertEqual(response.status_code, 400)

        # Check the error message
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], "Tweet URL is required")


class TestDeleteTweet(unittest.TestCase):
    def setUp(self):
        """Set up the application context and test client for each test."""
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()

    @patch('models.tweet.Tweet.query')
    def test_delete_tweet_success(self, mock_query):
        """Test deleting an existing tweet successfully."""
        mock_tweet = MagicMock()
        mock_query.get.return_value = mock_tweet

        with patch('models.tweet.db.session.delete') as mock_delete, \
                patch('models.tweet.db.session.commit') as mock_commit:
            response = self.app.delete('/tweets/1')
            mock_delete.assert_called_once_with(mock_tweet)
            mock_commit.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {'message': 'Tweet deleted successfully'})

    @patch('models.tweet.Tweet.query')
    def test_delete_tweet_not_found(self, mock_query):
        """Test deleting a tweet that does not exist."""
        mock_query.get.return_value = None

        response = self.app.delete('/tweets/999')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {'error': 'Tweet not found'})

    @patch('models.tweet.Tweet.query')
    def test_delete_tweet_exception(self, mock_query):
        """Test exception handling when an error occurs during the delete operation."""
        mock_tweet = MagicMock()
        mock_query.get.return_value = mock_tweet

        with patch('models.tweet.db.session.delete') as mock_delete, \
                patch('models.tweet.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("Database error")
            response = self.app.delete('/tweets/1')
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.get_json(), {'error': 'Database error'})


class TestUpdateTweet(unittest.TestCase):
    def setUp(self):
        """Set up the application context and test client for each test."""
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()

    class TestUpdateTweet(unittest.TestCase):
        def setUp(self):
            """Set up the application context and test client for each test."""
            self.app = app.test_client()
            self.app_context = app.app_context()
            self.app_context.push()

        def tearDown(self):
            """Clean up after tests."""
            self.app_context.pop()

        @patch('models.tweet.Tweet.query')
        @patch('models.tweet.db.session.commit')
        def test_update_tweet_success(self, mock_commit, mock_query):
            """Test updating an existing tweet successfully."""
            # Creează un obiect Tweet mock
            mock_tweet = MagicMock()
            mock_tweet.url = "https://example.com/original"
            mock_tweet.content = "Original content"
            mock_query.get.return_value = mock_tweet  # Simulează găsirea tweet-ului în baza de date

            # Payload pentru actualizare
            data = {
                'url': 'https://example.com/updated',
                'content': 'Updated content'
            }

            # Trimite cererea PUT către endpoint
            response = self.app.put('/tweets/1', json=data)

            # Asigură-te că răspunsul este de succes (200 OK)
            self.assertEqual(response.status_code, 200)

            # Verifică dacă câmpurile tweet-ului au fost actualizate
            self.assertEqual(mock_tweet.url, 'https://example.com/updated')
            self.assertEqual(mock_tweet.content, 'Updated content')

            # Asigură-te că metoda commit() a fost apelată
            mock_commit.assert_called_once()

            # Verifică dacă răspunsul conține tweet-ul actualizat
            response_data = response.get_json()
            self.assertEqual(response_data['url'], 'https://example.com/updated')
            self.assertEqual(response_data['content'], 'Updated content')

    @patch('models.tweet.Tweet.query')
    def test_update_tweet_not_found(self, mock_query):
        """Test updating a tweet that does not exist."""
        mock_query.get.return_value = None

        data = {'content': 'Updated content'}
        response = self.app.put('/tweets/999', json=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {'error': 'Tweet not found'})

    @patch('models.tweet.Tweet.query')
    def test_update_tweet_exception(self, mock_query):
        """Test exception handling when an error occurs during the update."""
        mock_tweet = MagicMock()
        mock_query.get.return_value = mock_tweet

        data = {'content': 'Updated content'}

        with patch('models.tweet.db.session.commit', side_effect=Exception("Database error")):
            response = self.app.put('/tweets/1', json=data)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.get_json(), {'error': 'Database error'})

class TestUtilityFunctions(unittest.TestCase):

    def test_extract_tweet_id_valid_url(self):
        """Test extragerea unui tweet ID valid din URL."""
        url = "https://twitter.com/user/status/1234567890"
        tweet_id = extract_tweet_id(url)
        self.assertEqual(tweet_id, "1234567890")

    def test_extract_tweet_id_invalid_url(self):
        """Test extragerea unui tweet ID dintr-un URL invalid."""
        url = "https://twitter.com/user/1234567890"
        tweet_id = extract_tweet_id(url)
        self.assertIsNone(tweet_id)

    def test_get_tweet_info_from_notes_found(self):
        """Test găsirea unui tweet în fișierul TSV."""
        with NamedTemporaryFile(mode="w+", delete=False, suffix=".tsv") as temp_file:
            temp_file.write("tweetId\tclassification\n1234567890\tNOT_MISLEADING\n")
            temp_file.flush()
            temp_file.close()  # Închide fișierul înainte de a-l folosi

            result = get_tweet_info_from_notes("1234567890", file_name=temp_file.name)
            expected = {
                "noteId": "N/A", "noteAuthorParticipantId": "N/A", "createdAtMillis": "N/A",
                "tweetId": "1234567890", "classification": "NOT_MISLEADING", "believable": "N/A",
                "harmful": "N/A", "validationDifficulty": "N/A", "misleadingOther": "N/A",
                "misleadingFactualError": "N/A", "misleadingManipulatedMedia": "N/A",
                "misleadingOutdatedInformation": "N/A", "misleadingMissingImportantContext": "N/A",
                "misleadingUnverifiedClaimAsFact": "N/A", "misleadingSatire": "N/A",
                "notMisleadingOther": "N/A", "notMisleadingFactuallyCorrect": "N/A",
                "notMisleadingOutdatedButNotWhenWritten": "N/A", "notMisleadingClearlySatire": "N/A",
                "notMisleadingPersonalOpinion": "N/A", "trustworthySources": "N/A", "summary": "N/A",
                "isMediaNote": "N/A"
            }
            self.assertEqual(result, expected)

            os.unlink(temp_file.name)  # Șterge fișierul după ce este închis

    def test_get_tweet_info_from_notes_not_found(self):
        """Test căutarea unui tweet care nu există în fișierul TSV."""
        with NamedTemporaryFile(mode="w+", delete=False, suffix=".tsv") as temp_file:
            temp_file.write("tweetId\tclassification\n1234567890\tNOT_MISLEADING\n")
            temp_file.flush()
            temp_file.close()  # Închide explicit fișierul înainte de a-l șterge

            result = get_tweet_info_from_notes("987654321", file_name=temp_file.name)
            self.assertIsNone(result)

            os.unlink(temp_file.name)  # Șterge fișierul după ce este închis

    def test_validate_tsv_invalid_classification(self):
        """Test validarea unui fișier TSV cu clasificare invalidă."""
        with NamedTemporaryFile(mode="w+", delete=False, suffix=".tsv") as temp_file:
            temp_file.write(
                "noteId\tnoteAuthorParticipantId\tcreatedAtMillis\ttweetId\tclassification\tbelievable\tharmful\tvalidationDifficulty\tmisleadingOther\tmisleadingFactualError\tmisleadingManipulatedMedia\tmisleadingOutdatedInformation\tmisleadingMissingImportantContext\tmisleadingUnverifiedClaimAsFact\tmisleadingSatire\tnotMisleadingOther\tnotMisleadingFactuallyCorrect\tnotMisleadingOutdatedButNotWhenWritten\tnotMisleadingClearlySatire\tnotMisleadingPersonalOpinion\ttrustworthySources\tsummary\tisMediaNote\n")
            temp_file.write(
                "123\tparticipant123\t1651659014342\t1234567890\tINVALID_CLASSIFICATION\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t1\t1\t1\t1\t1\tsummary\t0\n")
            temp_file.flush()
            temp_file.close()  # Închide fișierul înainte de a-l șterge

            is_valid = validate_tsv(temp_file.name)
            self.assertFalse(is_valid)

            os.unlink(temp_file.name)  # Șterge fișierul după ce este închis

    def test_validate_tsv_invalid_classification(self):
        """Test validarea unui fișier TSV cu clasificare invalidă."""
        with NamedTemporaryFile(mode="w+", delete=False, suffix=".tsv") as temp_file:
            temp_file.write(
                "noteId\tnoteAuthorParticipantId\tcreatedAtMillis\ttweetId\tclassification\tbelievable\tharmful\tvalidationDifficulty\tmisleadingOther\tmisleadingFactualError\tmisleadingManipulatedMedia\tmisleadingOutdatedInformation\tmisleadingMissingImportantContext\tmisleadingUnverifiedClaimAsFact\tmisleadingSatire\tnotMisleadingOther\tnotMisleadingFactuallyCorrect\tnotMisleadingOutdatedButNotWhenWritten\tnotMisleadingClearlySatire\tnotMisleadingPersonalOpinion\ttrustworthySources\tsummary\tisMediaNote\n")
            temp_file.write(
                "123\tparticipant123\t1651659014342\t1234567890\tINVALID_CLASSIFICATION\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t1\t1\t1\t1\t1\tsummary\t0\n")
            temp_file.flush()
            temp_file.close()

            is_valid = validate_tsv(temp_file.name)
            self.assertFalse(is_valid)  # Testul ar trebui să treacă acum, dacă funcția returnează False

            os.unlink(temp_file.name)

    def test_clean_tsv(self):
        """Test curățarea unui fișier TSV."""
        with NamedTemporaryFile(mode="w+", delete=False, suffix=".tsv") as temp_file:
            temp_file.write(
                "noteId\tnoteAuthorParticipantId\tcreatedAtMillis\ttweetId\tclassification\tbelievable\tharmful\tvalidationDifficulty\tmisleadingOther\tmisleadingFactualError\tmisleadingManipulatedMedia\tmisleadingOutdatedInformation\tmisleadingMissingImportantContext\tmisleadingUnverifiedClaimAsFact\tmisleadingSatire\tnotMisleadingOther\tnotMisleadingFactuallyCorrect\tnotMisleadingOutdatedButNotWhenWritten\tnotMisleadingClearlySatire\tnotMisleadingPersonalOpinion\ttrustworthySources\tsummary\tisMediaNote\n")
            temp_file.write(
                "123\tparticipant123\t1651659014342\t1234567890\tNOT_MISLEADING\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t1\t1\t1\t1\t1\tsummary\t0\n")
            temp_file.write(
                "124\tparticipant124\t1651659014343\t987654321\tINVALID_CLASSIFICATION\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t1\t1\t1\t1\t1\t1\tsummary\t0\n")
            temp_file.flush()
            temp_file.close()  # Închide fișierul înainte de a-l șterge

            clean_tsv(temp_file.name)

            with open(temp_file.name, "r", encoding="utf-8") as cleaned_file:
                reader = list(csv.DictReader(cleaned_file, delimiter="\t"))
                self.assertEqual(len(reader), 1)
                self.assertEqual(reader[0]["tweetId"], "1234567890")

            os.unlink(temp_file.name)  # Șterge fișierul după închidere

class TestTweepyScraper(unittest.TestCase):
    def setUp(self):
        """Set up TweepyScraper with a mocked Tweepy client."""
        self.mock_client = MagicMock()
        with patch("models.tweepy_api.tweepy.Client", return_value=self.mock_client):
            self.scraper = TweepyScraper(bearer_token="dummy_token")

    def test_extract_data_valid_tweet(self):
        """Test extracting data from a valid tweet."""
        tweet_id = "1234567890"
        url = f"https://twitter.com/user/status/{tweet_id}"

        # Mock the Tweepy client response
        self.mock_client.get_tweet.return_value = MagicMock(
            data=MagicMock(
                text="This is a test tweet",
                created_at="2023-12-01T12:00:00Z",
                public_metrics={"retweet_count": 100, "like_count": 200},
            ),
            includes={
                "users": [
                    {
                        "name": "Test User",
                        "username": "testuser",
                        "location": "Test City",
                        "description": "A user for testing.",
                        "verified": True,
                        "created_at": "2020-01-01T00:00:00Z",
                    }
                ]
            },
        )

        result = self.scraper.extract_data(url)
        expected_result = {
            "url": url,
            "content": "This is a test tweet",
            "author_name": "Test User",
            "author_username": "testuser",
            "author_location": "Test City",
            "author_description": "A user for testing.",
            "author_verified": True,
            "author_created_at": "2020-01-01T00:00:00Z",
            "tweet_created_at": "2023-12-01T12:00:00Z",
            "metrics": {"retweet_count": 100, "like_count": 200},
        }

        self.assertEqual(json.loads(result), expected_result)



if __name__ == "__main__":
    unittest.main()
