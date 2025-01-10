import logging
from aop_wrapper import Aspect

# Define a custom exception for rule violations
class RuleViolationError(Exception):
    """Exception raised for rule violations."""
    pass

class User:
    """
    Represents a basic user with functionality for validation and verification.
    """

    def __init__(self, user_id: int, username: str, email: str):
        """
        Initialize a User with basic information.
        """
        self._validate_initialization(user_id, username, email)
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = "user"

    def _validate_initialization(self, user_id: int, username: str, email: str):
        """Validate inputs for User initialization."""
        if not isinstance(user_id, int) or user_id <= 0:
            raise RuleViolationError(f"Invalid user_id '{user_id}'. It must be a positive integer.")
        if not isinstance(username, str) or not username.strip():
            raise RuleViolationError(f"Invalid username '{username}'. It must be a non-empty string.")
        if "@" not in email or "." not in email:
            raise RuleViolationError(f"Invalid email '{email}'. It must be a valid email address.")

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def get_user_info(self):
        """
        Retrieve basic user information.
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role
        }

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def verify_article(self, article):
        """
        Submit an article for verification.
        """
        return self._process_article_verification(article)

    def _process_article_verification(self, article):
        """Process the article for verification."""
        # Basic implementation
        return {
            "article_id": article["id"],
            "status": "pending",
            "timestamp": "2024-11-07"
        }

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def view_verification_result(self, article_id: int):
        """
        View the verification result for a specific article.
        """
        self._validate_verification_request(article_id)
        return self._fetch_verification_result(article_id)

    def _validate_verification_request(self, article_id: int):
        """Validate the article ID for viewing verification results."""
        if not isinstance(article_id, int) or article_id <= 0:
            raise RuleViolationError(f"Invalid article_id '{article_id}'. It must be a positive integer.")

    def _fetch_verification_result(self, article_id: int):
        """Fetch verification result for the given article ID."""
        return {
            "article_id": article_id,
            "status": "verified",
            "score": 0.85,
            "timestamp": "2024-11-07"
        }

if __name__ == "__main__":
    try:
        user1 = User(1, "alice", "alice@email.org")  # Valid initialization
        user_info = user1.get_user_info()
        print(user_info)

        article = {"id": 123, "title": "Example Article", "content": "This is an example article."}
        verification_result = user1.verify_article(article)  # Valid article submission
        print(verification_result)

        result = user1.view_verification_result(123)  # Valid verification request
        print(result)

        # Uncomment to test validation errors
        # invalid_user = User(-1, "", "invalid-email")
        # user1.verify_article({"id": -1, "title": "", "content": ""})
        # user1.view_verification_result(-123)

    except RuleViolationError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Unhandled Error: {e}")
