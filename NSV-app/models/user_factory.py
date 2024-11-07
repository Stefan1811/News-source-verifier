import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from user import User
from admin import Admin

class UserFactory:
    @staticmethod
    def create_user(user_id: int, username: str, email: str, role: str):
        """
        Factory method to create a User or Admin based on role.

        """
        if role == "admin":
            return Admin(user_id, username, email)
        else:
            return User(user_id, username, email)
