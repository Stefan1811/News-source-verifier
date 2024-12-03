import tweepy
import logging
import re
import json
from aop_wrapper import Aspect

class TweepyScraper:
    def __init__(self, bearer_token):
        """Initialize Tweepy client with Bearer Token."""
        self.client = tweepy.Client(bearer_token=bearer_token)

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def extract_data(self, url):
        """
        Extracts information about a tweet based on its URL and returns it in JSON format.
        """
        # Extract tweet ID from the URL
        tweet_id = self._extract_tweet_id(url)
        if not tweet_id:
            logging.error(f"Invalid Twitter URL: {url}")
            return json.dumps({"error": "Invalid Twitter URL"})

        try:
            # Fetch tweet data using Tweepy
            logging.info(f"Fetching data for tweet ID: {tweet_id}")
            tweet = self.client.get_tweet(
                id=tweet_id,
                expansions=["author_id"],
                tweet_fields=["created_at", "public_metrics"],
                user_fields=["name", "username", "location", "description", "verified", "created_at"]
            )

            # Validate response
            if not tweet.data:
                logging.error(f"No data found for tweet ID: {tweet_id}")
                return json.dumps({"error": "No data found for the given tweet ID"})

            # Extract tweet details
            tweet_content = tweet.data.text
            created_at = tweet.data.created_at
            public_metrics = tweet.data.public_metrics

            # Extract author details
            author = tweet.includes["users"][0] if "users" in tweet.includes else {}
            author_name = author.get("name", "Unknown name")
            author_username = author.get("username", "Unknown username")
            author_location = author.get("location", "Unknown location")
            author_description = author.get("description", "No description")
            author_verified = author.get("verified", False)
            author_created_at = author.get("created_at", "Unknown date")

            # Prepare the data in JSON format
            result = {
                "url": url,
                "content": tweet_content,
                "author_name": author_name,
                "author_username": author_username,
                "author_location": author_location,
                "author_description": author_description,
                "author_verified": author_verified,
                "author_created_at": str(author_created_at),
                "tweet_created_at": str(created_at),
                "metrics": public_metrics,
            }

            return json.dumps(result, indent=4)

        except Exception as e:
            logging.error(f"Error fetching tweet data: {e}")
            return json.dumps({"error": f"Error fetching tweet data: {e}"})

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def _extract_tweet_id(self, url):
        """Extracts the tweet ID from a Twitter URL."""
        match = re.search(r"/status/(\d+)", url)
        return match.group(1) if match else None


