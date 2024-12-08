# import unittest
# from models.article import Article
# from models.ScoringStrategy_Article import SimpleAverageStrategy, WeightedAverageStrategy

# class TestArticle(unittest.TestCase):
#
#     def setUp(self):
#         # Dummy article for testing
#         self.dummy_article = Article(
#             url="https://www.example.com/fake-news-article",
#             title="Fake News on Climate Change",
#             content="This is some content about fake news...",
#             author="John Doe",
#             publish_date="2024-11-07"
#         )
#
#         # Set the dummy article's metric values
#         self.dummy_article.ml_model_prediction = 0.7
#         self.dummy_article.source_credibility = 80
#         self.dummy_article.sentiment_subjectivity = 50
#         self.dummy_article.content_consistency = 60
#
#     def test_analyze_sentiment(self):
#         # Test the analyze_sentiment method
#         self.dummy_article.analyze_sentiment()
#         self.assertIsNotNone(self.dummy_article.sentiment_subjectivity)
#         self.assertGreater(self.dummy_article.sentiment_subjectivity, 0)
#
#     def test_extract_keywords(self):
#         # Test the extract_keywords method
#         keywords = self.dummy_article.extract_keywords()
#         self.assertIsInstance(keywords, list)
#         self.assertGreater(len(keywords), 0)
#
#     def test_check_consistency(self):
#         # Test the check_consistency method
#         self.dummy_article.check_consistency()
#         self.assertIn(self.dummy_article.status, ["unverified", "verified"])
#         self.assertIsNotNone(self.dummy_article.content_consistency)
#
#     def test_calculate_score_simple_average(self):
#         # Test the calculate_trust_score method with SimpleAverageStrategy
#         simple_average_strategy = SimpleAverageStrategy()
#         score = self.dummy_article.calculate_trust_score(simple_average_strategy)
#         self.assertIsNotNone(score)
#         self.assertAlmostEqual(score, (0.7 + 80 + 50 + 60) / 4, places=2)
#
#     def test_calculate_score_weighted_average(self):
#         # Test the calculate_trust_score method with WeightedAverageStrategy
#         weighted_average_strategy = WeightedAverageStrategy()
#         score = self.dummy_article.calculate_trust_score(weighted_average_strategy)
#         self.assertIsNotNone(score)
#         self.assertAlmostEqual(score, 0.6 * 0.7 + 0.2 * 80 + 0.1 * 50 + 0.1 * 60, places=2)
#
# if __name__ == '__main__':
#     unittest.main()

import os
import unittest
import json
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.article import Article, app

import time
unique_url = f"https://example.com/{int(time.time())}"

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the application context and test client for each test."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        """Prepare test data for each test case."""
        self.article_data = {
            "url": unique_url,
            "title": "Test Article",
            "content": "This is some test content.",
            "author": "John Doe",
            "publish_date": "2024-11-22",
            "ml_model_prediction": 0.8,
            "source_credibility": 0.9,
            "sentiment_subjectivity": 0.5,
            "content_consistency": 0.7,
            "trust_score": 0.85,
            "status": "verified"
        }
    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()
    def test_create_article(self):
        """Test creating a new article."""
        response = self.client.post(
            '/articles',
            data=json.dumps(self.article_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['title'], self.article_data['title'])

    def test_get_all_articles(self):
        """Test retrieving all articles."""
        self.client.post(
            '/articles',
            data=json.dumps(self.article_data),
            content_type='application/json'
        )
        response = self.client.get('/articles')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_get_article(self):
        """Test retrieving a single article by ID."""
        get_response = self.client.get('/articles')
        self.assertEqual(get_response.status_code, 200)
        articles = get_response.get_json()
        self.assertGreater(len(articles), 0, "No articles found.")
        # Extract the article ID from the first article
        article_id = articles[0]['article_id']
        response = self.client.get(f'/articles/{article_id}')
        # Assert the second GET request was successful
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # Assert the article's title matches the title we expect
        self.assertEqual(data['title'], articles[0]['title'])

    def test_update_article(self):
        """Test updating an article."""

        unique_url = f"https://example.com/{uuid.uuid4()}"

        self.article_data = {
            'url': unique_url,
            'title': 'Test Article',
            'content': 'This is some test content.',
            'author': 'John Doe',
            'publish_date': '2024-11-22',
            'ml_model_prediction': 0.8,
            'source_credibility': 0.9,
            'sentiment_subjectivity': 0.5,
            'content_consistency': 0.7,
            'trust_score': 0.85,
            'status': 'verified'
        }

        # First, create an article by sending a POST request
        post_response = self.client.post(
            '/articles',
            data=json.dumps(self.article_data),
            content_type='application/json'
        )

        # Check if the post response contains 'article_id'
        post_response_json = post_response.get_json()
        self.assertIn('article_id', post_response_json, "No article_id returned in the response.")

        article_id = post_response_json['article_id']

        updated_data = {"title": "Updated Test Article"}

        response = self.client.put(
            f'/articles/{article_id}',
            data=json.dumps(updated_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

    def test_delete_article(self):
        """Test deleting an article."""

        unique_url = f"https://example.com/{uuid.uuid4()}"
        print(f"Generated unique URL: {unique_url}")  # Print the URL to verify uniqueness

        post_response = self.client.post('/articles', json={
            'url': unique_url,
            'title': 'Test Article',
            'content': 'This is a test.',
            'author': 'Test Author',
            'publish_date': '2024-12-08',
            'status': 'verified'
        })

        response_data = post_response.get_json()
        print(response_data)

        article_id = response_data.get('article_id')
        if not article_id:
            self.fail(f"Article creation failed, no article_id found in response: {response_data}")

        response = self.client.delete(f'/articles/{article_id}')
        self.assertEqual(response.status_code, 200)

    def test_scrape_and_create_article(self):
        """Test scraping data and creating an article."""
        scrape_data = {"url": "https://www.bbc.com/news/articles/c5yv75nydy3o"}

        response = self.client.post(
            '/articles/scrape',
            data=json.dumps(scrape_data),
            content_type='application/json'
        )

        if response.status_code != 201:
            print("Response content:", response.data)

        self.assertEqual(response.status_code, 201)  # Check if it was created successfully
        data = response.get_json()

        # Assert that the returned URL matches the one sent
        self.assertEqual(data['url'], scrape_data['url'])

if __name__ == '__main__':
    unittest.main()