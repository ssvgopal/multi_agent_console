"""Test the authentication module."""

import unittest
import os
import tempfile
import shutil
import json
import time
from unittest.mock import patch, MagicMock

from multi_agent_console.auth import AuthManager, PermissionManager, active_sessions, session_timeout


class TestAuthManager(unittest.TestCase):
    """Test the AuthManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.users_file = os.path.join(self.test_dir, "users.json")
        
        # Create an AuthManager with the test directory
        self.auth_manager = AuthManager(self.test_dir)
        
        # Clear active sessions
        active_sessions.clear()

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
        # Clear active sessions
        active_sessions.clear()

    def test_register_user(self):
        """Test registering a new user."""
        # Register a user
        result = self.auth_manager.register_user("testuser", "password123", "test@example.com", "user")
        
        # Check that registration was successful
        self.assertTrue(result)
        
        # Check that the user was added to the users dictionary
        self.assertIn("testuser", self.auth_manager.users)
        
        # Check that the user data is correct
        user_data = self.auth_manager.users["testuser"]
        self.assertEqual(user_data["username"], "testuser")
        self.assertEqual(user_data["email"], "test@example.com")
        self.assertEqual(user_data["role"], "user")
        
        # Check that the password was hashed
        self.assertNotEqual(user_data["password_hash"], "password123")
        
        # Check that the users file was created
        self.assertTrue(os.path.exists(self.users_file))

    def test_register_existing_user(self):
        """Test registering a user that already exists."""
        # Register a user
        self.auth_manager.register_user("testuser", "password123")
        
        # Try to register the same user again
        result = self.auth_manager.register_user("testuser", "newpassword")
        
        # Check that registration failed
        self.assertFalse(result)

    def test_authenticate_valid_user(self):
        """Test authenticating a valid user."""
        # Register a user
        self.auth_manager.register_user("testuser", "password123")
        
        # Authenticate the user
        session_id = self.auth_manager.authenticate("testuser", "password123")
        
        # Check that authentication was successful
        self.assertIsNotNone(session_id)
        
        # Check that a session was created
        self.assertIn(session_id, active_sessions)
        
        # Check that the session data is correct
        session_data = active_sessions[session_id]
        self.assertEqual(session_data["username"], "testuser")
        self.assertIn("created_at", session_data)

    def test_authenticate_invalid_user(self):
        """Test authenticating a user that doesn't exist."""
        # Authenticate a non-existent user
        session_id = self.auth_manager.authenticate("nonexistent", "password123")
        
        # Check that authentication failed
        self.assertIsNone(session_id)

    def test_authenticate_invalid_password(self):
        """Test authenticating a user with an invalid password."""
        # Register a user
        self.auth_manager.register_user("testuser", "password123")
        
        # Authenticate with the wrong password
        session_id = self.auth_manager.authenticate("testuser", "wrongpassword")
        
        # Check that authentication failed
        self.assertIsNone(session_id)

    def test_validate_session_valid(self):
        """Test validating a valid session."""
        # Register and authenticate a user
        self.auth_manager.register_user("testuser", "password123", role="admin")
        session_id = self.auth_manager.authenticate("testuser", "password123")
        
        # Validate the session
        user_data = self.auth_manager.validate_session(session_id)
        
        # Check that validation was successful
        self.assertIsNotNone(user_data)
        
        # Check that the user data is correct
        self.assertEqual(user_data["username"], "testuser")
        self.assertEqual(user_data["role"], "admin")

    def test_validate_session_invalid(self):
        """Test validating an invalid session."""
        # Validate a non-existent session
        user_data = self.auth_manager.validate_session("nonexistent")
        
        # Check that validation failed
        self.assertIsNone(user_data)

    def test_validate_session_expired(self):
        """Test validating an expired session."""
        # Register and authenticate a user
        self.auth_manager.register_user("testuser", "password123")
        session_id = self.auth_manager.authenticate("testuser", "password123")
        
        # Modify the session creation time to make it expired
        active_sessions[session_id]["created_at"] = time.time() - session_timeout - 1
        
        # Validate the session
        user_data = self.auth_manager.validate_session(session_id)
        
        # Check that validation failed
        self.assertIsNone(user_data)
        
        # Check that the session was removed
        self.assertNotIn(session_id, active_sessions)

    def test_logout(self):
        """Test logging out a user."""
        # Register and authenticate a user
        self.auth_manager.register_user("testuser", "password123")
        session_id = self.auth_manager.authenticate("testuser", "password123")
        
        # Log out the user
        result = self.auth_manager.logout(session_id)
        
        # Check that logout was successful
        self.assertTrue(result)
        
        # Check that the session was removed
        self.assertNotIn(session_id, active_sessions)

    def test_logout_invalid_session(self):
        """Test logging out with an invalid session."""
        # Log out with a non-existent session
        result = self.auth_manager.logout("nonexistent")
        
        # Check that logout failed
        self.assertFalse(result)

    def test_update_user_settings(self):
        """Test updating user settings."""
        # Register a user
        self.auth_manager.register_user("testuser", "password123")
        
        # Update user settings
        settings = {"theme": "dark", "notifications": True}
        result = self.auth_manager.update_user_settings("testuser", settings)
        
        # Check that update was successful
        self.assertTrue(result)
        
        # Check that the settings were updated
        user_data = self.auth_manager.users["testuser"]
        self.assertEqual(user_data["settings"], settings)

    def test_update_user_settings_invalid_user(self):
        """Test updating settings for a user that doesn't exist."""
        # Update settings for a non-existent user
        settings = {"theme": "dark"}
        result = self.auth_manager.update_user_settings("nonexistent", settings)
        
        # Check that update failed
        self.assertFalse(result)

    def test_get_user_settings(self):
        """Test getting user settings."""
        # Register a user
        self.auth_manager.register_user("testuser", "password123")
        
        # Update user settings
        settings = {"theme": "dark", "notifications": True}
        self.auth_manager.update_user_settings("testuser", settings)
        
        # Get user settings
        result = self.auth_manager.get_user_settings("testuser")
        
        # Check that the settings are correct
        self.assertEqual(result, settings)

    def test_get_user_settings_invalid_user(self):
        """Test getting settings for a user that doesn't exist."""
        # Get settings for a non-existent user
        result = self.auth_manager.get_user_settings("nonexistent")
        
        # Check that the result is None
        self.assertIsNone(result)

    def test_load_users(self):
        """Test loading users from a file."""
        # Create a users file
        users_data = {
            "testuser": {
                "username": "testuser",
                "password_hash": "hash",
                "salt": "salt",
                "email": "test@example.com",
                "role": "user",
                "created_at": "2023-01-01T00:00:00",
                "last_login": None,
                "settings": {}
            }
        }
        with open(self.users_file, "w") as f:
            json.dump(users_data, f)
        
        # Create a new AuthManager to load the users
        auth_manager = AuthManager(self.test_dir)
        
        # Check that the users were loaded
        self.assertIn("testuser", auth_manager.users)
        self.assertEqual(auth_manager.users["testuser"]["email"], "test@example.com")

    def test_load_users_file_not_found(self):
        """Test loading users when the file doesn't exist."""
        # Create a new AuthManager with a non-existent file
        auth_manager = AuthManager(os.path.join(self.test_dir, "nonexistent"))
        
        # Check that the users dictionary is empty
        self.assertEqual(auth_manager.users, {})

    @patch("json.load")
    def test_load_users_error(self, mock_json_load):
        """Test loading users when an error occurs."""
        # Create a users file
        with open(self.users_file, "w") as f:
            f.write("invalid json")
        
        # Mock json.load to raise an exception
        mock_json_load.side_effect = Exception("Error loading users")
        
        # Create a new AuthManager to load the users
        auth_manager = AuthManager(self.test_dir)
        
        # Check that the users dictionary is empty
        self.assertEqual(auth_manager.users, {})

    @patch("json.dump")
    def test_save_users_error(self, mock_json_dump):
        """Test saving users when an error occurs."""
        # Mock json.dump to raise an exception
        mock_json_dump.side_effect = Exception("Error saving users")
        
        # Register a user (which calls save_users)
        result = self.auth_manager.register_user("testuser", "password123")
        
        # Check that registration was still successful
        self.assertTrue(result)


class TestPermissionManager(unittest.TestCase):
    """Test the PermissionManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a mock AuthManager
        self.auth_manager = MagicMock()
        
        # Create a PermissionManager with the mock AuthManager
        self.permission_manager = PermissionManager(self.auth_manager)
        
        # Clear active sessions
        active_sessions.clear()

    def tearDown(self):
        """Clean up after the test."""
        # Clear active sessions
        active_sessions.clear()

    def test_check_permission_valid(self):
        """Test checking a valid permission."""
        # Mock validate_session to return a user with admin role
        self.auth_manager.validate_session.return_value = {"role": "admin"}
        
        # Check a permission
        result = self.permission_manager.check_permission("session_id", "can_manage_users")
        
        # Check that the permission check was successful
        self.assertTrue(result)
        
        # Check that validate_session was called
        self.auth_manager.validate_session.assert_called_once_with("session_id")

    def test_check_permission_invalid_session(self):
        """Test checking a permission with an invalid session."""
        # Mock validate_session to return None
        self.auth_manager.validate_session.return_value = None
        
        # Check a permission
        result = self.permission_manager.check_permission("session_id", "can_manage_users")
        
        # Check that the permission check failed
        self.assertFalse(result)

    def test_check_permission_invalid_role(self):
        """Test checking a permission with an invalid role."""
        # Mock validate_session to return a user with an invalid role
        self.auth_manager.validate_session.return_value = {"role": "invalid"}
        
        # Check a permission
        result = self.permission_manager.check_permission("session_id", "can_manage_users")
        
        # Check that the permission check failed
        self.assertFalse(result)

    def test_check_permission_invalid_permission(self):
        """Test checking an invalid permission."""
        # Mock validate_session to return a user with admin role
        self.auth_manager.validate_session.return_value = {"role": "admin"}
        
        # Check an invalid permission
        result = self.permission_manager.check_permission("session_id", "invalid_permission")
        
        # Check that the permission check failed
        self.assertFalse(result)

    def test_get_user_permissions_valid(self):
        """Test getting permissions for a valid user."""
        # Mock validate_session to return a user with admin role
        self.auth_manager.validate_session.return_value = {"role": "admin"}
        
        # Get user permissions
        permissions = self.permission_manager.get_user_permissions("session_id")
        
        # Check that the permissions are correct
        self.assertEqual(permissions, self.permission_manager.role_permissions["admin"])
        
        # Check that validate_session was called
        self.auth_manager.validate_session.assert_called_once_with("session_id")

    def test_get_user_permissions_invalid_session(self):
        """Test getting permissions with an invalid session."""
        # Mock validate_session to return None
        self.auth_manager.validate_session.return_value = None
        
        # Get user permissions
        permissions = self.permission_manager.get_user_permissions("session_id")
        
        # Check that an empty dictionary was returned
        self.assertEqual(permissions, {})

    def test_get_user_permissions_invalid_role(self):
        """Test getting permissions with an invalid role."""
        # Mock validate_session to return a user with an invalid role
        self.auth_manager.validate_session.return_value = {"role": "invalid"}
        
        # Get user permissions
        permissions = self.permission_manager.get_user_permissions("session_id")
        
        # Check that an empty dictionary was returned
        self.assertEqual(permissions, {})


if __name__ == "__main__":
    unittest.main()
