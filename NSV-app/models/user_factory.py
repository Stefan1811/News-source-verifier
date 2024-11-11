import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from user import User
from admin import Admin
import logging
logging.basicConfig(filename='logs.txt', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class UserFactory:


    @staticmethod
    def create_user(user_id: int, username: str, email: str, role: str):
        """
        Factory method to create a User or Admin based on role.

        """
        logging.info(f"Creating user with role: {role}")
        if role == "admin":
            return Admin(user_id, username, email)
        else:
            return User(user_id, username, email)

