import sys
import os
import logging
from user import User
from admin import Admin
from aop_wrapper import Aspect
from mop.monitor import monitor, rule, violation  # Importing MOP monitoring and rules

# Define validation rule for create_user
@rule("validate_user_factory_creation")
def validate_create_user_inputs(user_id: int, username: str, email: str, role: str):
    if not isinstance(user_id, int) or user_id <= 0:
        raise violation(f"Invalid user_id '{user_id}'. It must be a positive integer.")
    if not isinstance(username, str) or not username.strip():
        raise violation(f"Invalid username '{username}'. It must be a non-empty string.")
    if "@" not in email or "." not in email:
        raise violation(f"Invalid email '{email}'. It must be a valid email address.")
    if role not in {"user", "admin"}:
        raise violation(f"Invalid role '{role}'. It must be either 'user' or 'admin'.")
    return True  # Pass validation if no issues are found

@monitor  # Apply monitoring to the class
class UserFactory:
    @staticmethod
    @validate_create_user_inputs  # Use MOP validation for user creation
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


# main
if __name__ == "__main__":
    try:
        user = UserFactory.create_user(1, "alice", "alice@email.org", "user")
        print(f"Created user: {user.get_user_info()}")

        admin = UserFactory.create_user(2, "bob", "bob@email.org", "admin")
        print(f"Created admin: {admin.get_user_info()}")

    except Exception as e:
        print(f"Validation Error: {e}")
