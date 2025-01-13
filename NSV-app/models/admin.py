import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from user import User
from aop_wrapper import Aspect

# Define a monitoring rule for input validation


class Admin(User):
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def __init__(self, user_id: int, username: str, email: str):
        """Initialize an Admin user with elevated permissions."""
        super().__init__(user_id, username, email)
        self.role = "admin"

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def manage_users(self, action: str, **kwargs):
        """Manage users within the system."""    
        if action == "add":
            # Implementation for adding a user
            return {"success": True, "message": "User added successfully"}
        elif action == "remove":
            # Implementation for removing a user
            return {"success": True, "message": "User removed successfully"}
        elif action == "update":
            # Implementation for updating a user
            return {"success": True, "message": "User updated successfully"}
        return {"success": False, "message": "Invalid action"}

    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def view_all_verifications(self):
        """View all verification results across the platform.""" 
        # Basic implementation
        return [
            {"article_id": 1, "status": "verified", "score": 0.9},
            {"article_id": 2, "status": "pending", "score": None}
        ]
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def edit_trustscore_parameters(self, parameters: dict):
        """Edit the trust score parameters for the platform."""       
        # Basic implementation
        return {
            "success": True,
            "message": "Trust score parameters updated",
            "new_parameters": parameters
        }

# main
if __name__ == "__main__":
    admin = Admin(1, "admin", "test@email.org")
    try:
        print(admin.manage_users("add", username="user1", email="user@email.org"))
        print(admin.manage_users("invalid_action", username="user1", email="user@email.org"))  # This should trigger a violation
    except Exception as e:
        print(f"Validation Error: {e}")
    print(admin.view_all_verifications())
    print(admin.edit_trustscore_parameters({"param1": 0.5, "param2": 0.3}))
