class User:
    def __init__(self, user_id: int, username: str, email: str):
        """
        Initialize a User with basic information.

        """
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = "user"  # Default role as "user"

    def get_user_info(self):
        """
        Retrieve basic user information.
        
        """
        return {"user_id": self.user_id, "username": self.username, "email": self.email, "role": self.role}

    def verify_article(self, article):
        """
        Submit an article for verification.

        """
        pass  # To be implemented

    def view_verification_result(self, article_id: int):
        """
        View the verification result for a specific article.

        """
        pass  # To be implemented
