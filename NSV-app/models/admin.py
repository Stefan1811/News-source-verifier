from user import User

class Admin(User):
    def __init__(self, user_id: int, username: str, email: str):
        """
        Initialize an Admin user with elevated permissions.
        
        """
        super().__init__(user_id, username, email)
        self.role = "admin"

    def manage_users(self):
        """
        Manage users within the system. Admins can add, remove, or update user information.
        """
        pass  # To be implemented

    def view_all_verifications(self):
        """
        View all verification results across the platform.
        """
        pass  # To be implemented

    def edit_trustscore_parameters(self):
        """
        Edit the trust score parameters for the platform.
        """
        pass  # To be implemented