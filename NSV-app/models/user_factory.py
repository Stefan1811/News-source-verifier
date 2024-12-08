import sys
import os
from user import User
from admin import Admin
import logging
from aop_wrapper import Aspect

class UserFactory:


    @staticmethod
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def create_user(user_id: int, username: str, email: str, role: str):
        """
        Factory method to create a User or Admin based on role.

        """
        logging.info(f"Creating user with role: {role}")
        if role == "admin":
            return Admin(user_id, username, email)
        else:
            return User(user_id, username, email)

