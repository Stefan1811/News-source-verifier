import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.user import User
from models.admin import Admin
from models.user_factory import UserFactory
import unittest


class TestUser(unittest.TestCase):
    def setUp(self):
        """Set up test cases with a basic user"""
        self.test_user = User(1, "testuser", "test@example.com")
        
    def test_user_initialization(self):
        """Test if user is initialized with correct attributes"""
        self.assertEqual(self.test_user.user_id, 1)
        self.assertEqual(self.test_user.username, "testuser")
        self.assertEqual(self.test_user.email, "test@example.com")
        self.assertEqual(self.test_user.role, "user")
        
    def test_get_user_info(self):
        """Test if get_user_info returns correct user information"""
        expected_info = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "user"
        }
        self.assertEqual(self.test_user.get_user_info(), expected_info)
        
    def test_verify_article(self):
        """Test article verification functionality"""
        article = {"id": 1, "content": "Test article"}
        result = self.test_user.verify_article(article)
        # Implementation pending, but we expect it to return a verification status
        self.assertIsNotNone(result)
        
    def test_view_verification_result(self):
        """Test viewing verification results"""
        result = self.test_user.view_verification_result(1)
        # Implementation pending, but we expect it to return verification details
        self.assertIsNotNone(result)


class TestAdmin(unittest.TestCase):
    def setUp(self):
        """Set up test cases with an admin user"""
        self.test_admin = Admin(1, "adminuser", "admin@example.com")
        
    def test_admin_initialization(self):
        """Test if admin is initialized with correct attributes"""
        self.assertEqual(self.test_admin.user_id, 1)
        self.assertEqual(self.test_admin.username, "adminuser")
        self.assertEqual(self.test_admin.email, "admin@example.com")
        self.assertEqual(self.test_admin.role, "admin")
        
    def test_manage_users(self):
        """Test user management functionality"""
        # Test adding a new user
        new_user = {"user_id": 2, "username": "newuser", "email": "new@example.com"}
        result = self.test_admin.manage_users(action="add", user_data=new_user)
        self.assertTrue(result["success"])
        
        # Test removing a user
        result = self.test_admin.manage_users(action="remove", user_id=2)
        self.assertTrue(result["success"])
        
    def test_view_all_verifications(self):
        """Test viewing all verification results"""
        verifications = self.test_admin.view_all_verifications()
        self.assertIsInstance(verifications, list)
        
    def test_edit_trustscore_parameters(self):
        """Test editing trust score parameters"""
        new_params = {"threshold": 0.8, "weight_factor": 1.2}
        result = self.test_admin.edit_trustscore_parameters(new_params)
        self.assertTrue(result["success"])


class TestUserFactory(unittest.TestCase):
    def test_create_user(self):
        """Test user creation through factory based on role"""
        # Test creating a regular user
        user = UserFactory.create_user(1, "testuser", "test@example.com", "user")
        self.assertEqual(user.role, "user")
        self.assertEqual(user.user_id, 1)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")

        # Test creating an admin user
        admin = UserFactory.create_user(2, "adminuser", "admin@example.com", "admin")
        self.assertEqual(admin.role, "admin")
        self.assertEqual(admin.user_id, 2)
        self.assertEqual(admin.username, "adminuser")
        self.assertEqual(admin.email, "admin@example.com")


if __name__ == '__main__':
    unittest.main()
