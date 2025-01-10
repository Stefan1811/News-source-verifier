import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from user import User
from aop_wrapper import Aspect

class Admin(User):
    """
    The Admin class represents an admin user with elevated permissions.
    It uses monitoring and AOP techniques to enhance functionality.
    """

    def __init__(self, user_id: int, username: str, email: str):
        """
        Initialize an Admin user.
        """
        super().__init__(user_id, username, email)
        self.role = "admin"

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def manage_users(self, action: str, **kwargs):
        """
        Manage users within the system.
        """
        if not self._is_valid_action(action):
            return {"success": False, "message": "Invalid action"}

        return self._execute_user_action(action, **kwargs)

    def _is_valid_action(self, action: str) -> bool:
        """Check if the action is valid."""
        return action in {"add", "remove", "update"}

    def _execute_user_action(self, action: str, **kwargs):
        """Execute the user management action."""
        actions_map = {
            "add": self._add_user,
            "remove": self._remove_user,
            "update": self._update_user
        }
        return actions_map[action](**kwargs)

    def _add_user(self, **kwargs):
        # Implementation for adding a user
        return {"success": True, "message": "User added successfully"}

    def _remove_user(self, **kwargs):
        # Implementation for removing a user
        return {"success": True, "message": "User removed successfully"}

    def _update_user(self, **kwargs):
        # Implementation for updating a user
        return {"success": True, "message": "User updated successfully"}

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def view_all_verifications(self):
        """
        View all verification results across the platform.
        """
        return self._fetch_verifications()

    def _fetch_verifications(self):
        """Fetch verification data."""
        return [
            {"article_id": 1, "status": "verified", "score": 0.9},
            {"article_id": 2, "status": "pending", "score": None}
        ]

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def edit_trustscore_parameters(self, parameters: dict):
        """
        Edit the trust score parameters for the platform.
        """
        return self._update_trustscore_parameters(parameters)

    def _update_trustscore_parameters(self, parameters: dict):
        """Update trust score parameters."""
        return {
            "success": True,
            "message": "Trust score parameters updated",
            "new_parameters": parameters
        }

# Main Execution
if __name__ == "__main__":
    admin = Admin(1, "admin", "test@email.org")
    try:
        print(admin.manage_users("add", username="user1", email="user@email.org"))
        print(admin.manage_users("invalid_action", username="user1", email="user@email.org"))
    except Exception as e:
        print(f"Validation Error: {e}")

    print(admin.view_all_verifications())
    print(admin.edit_trustscore_parameters({"param1": 0.5, "param2": 0.3}))
