"""
User Authentication for MultiAgentConsole.

This module provides user authentication and session management.
"""

import os
import json
import logging
import secrets
import hashlib
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

# Session storage
active_sessions = {}  # session_id -> user_data
session_timeout = 24 * 60 * 60  # 24 hours in seconds


class AuthManager:
    """Manages user authentication and sessions."""

    def __init__(self, data_dir: str = "data/users"):
        """Initialize the authentication manager.

        Args:
            data_dir: Directory for storing user data
        """
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.users = {}

        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Load users from file
        self.load_users()

        logging.info("Authentication Manager initialized")

    def load_users(self) -> None:
        """Load users from the users file."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r") as f:
                    self.users = json.load(f)
                logging.info(f"Loaded {len(self.users)} users from {self.users_file}")
            except Exception as e:
                logging.error(f"Error loading users from {self.users_file}: {e}")
                self.users = {}
        else:
            logging.info(f"Users file {self.users_file} not found, creating empty users dictionary")
            self.users = {}

    def save_users(self) -> None:
        """Save users to the users file."""
        try:
            with open(self.users_file, "w") as f:
                json.dump(self.users, f, indent=2)
            logging.info(f"Saved {len(self.users)} users to {self.users_file}")
        except Exception as e:
            logging.error(f"Error saving users to {self.users_file}: {e}")

    def register_user(self, username: str, password: str, email: str = "", role: str = "user") -> bool:
        """Register a new user.

        Args:
            username: Username
            password: Password
            email: Email address
            role: User role (default: "user")

        Returns:
            True if registration was successful, False otherwise
        """
        # Check if username already exists
        if username in self.users:
            logging.warning(f"User {username} already exists")
            return False

        # Hash the password
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)

        # Create user
        self.users[username] = {
            "username": username,
            "password_hash": password_hash,
            "salt": salt,
            "email": email,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "settings": {}
        }

        # Save users
        self.save_users()

        logging.info(f"User {username} registered successfully")
        return True

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user.

        Args:
            username: Username
            password: Password

        Returns:
            Session ID if authentication was successful, None otherwise
        """
        # Check if username exists
        if username not in self.users:
            logging.warning(f"User {username} not found")
            return None

        # Get user
        user = self.users[username]

        # Check password
        password_hash = self._hash_password(password, user["salt"])
        if password_hash != user["password_hash"]:
            logging.warning(f"Invalid password for user {username}")
            return None

        # Update last login
        user["last_login"] = datetime.now().isoformat()
        self.save_users()

        # Create session
        session_id = self._create_session(username)

        logging.info(f"User {username} authenticated successfully")
        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate a session.

        Args:
            session_id: Session ID

        Returns:
            User data if session is valid, None otherwise
        """
        # Check if session exists
        if session_id not in active_sessions:
            logging.warning(f"Session {session_id} not found")
            return None

        # Get session
        session = active_sessions[session_id]

        # Check if session has expired
        if time.time() - session["created_at"] > session_timeout:
            logging.warning(f"Session {session_id} has expired")
            del active_sessions[session_id]
            return None

        # Get user
        username = session["username"]
        if username not in self.users:
            logging.warning(f"User {username} not found")
            del active_sessions[session_id]
            return None

        # Return user data
        return self.users[username]

    def logout(self, session_id: str) -> bool:
        """Log out a user.

        Args:
            session_id: Session ID

        Returns:
            True if logout was successful, False otherwise
        """
        # Check if session exists
        if session_id not in active_sessions:
            logging.warning(f"Session {session_id} not found")
            return False

        # Delete session
        del active_sessions[session_id]

        logging.info(f"Session {session_id} logged out successfully")
        return True

    def update_user_settings(self, username: str, settings: Dict[str, Any]) -> bool:
        """Update user settings.

        Args:
            username: Username
            settings: User settings

        Returns:
            True if update was successful, False otherwise
        """
        # Check if username exists
        if username not in self.users:
            logging.warning(f"User {username} not found")
            return False

        # Update settings
        self.users[username]["settings"] = settings

        # Save users
        self.save_users()

        logging.info(f"Settings for user {username} updated successfully")
        return True

    def get_user_settings(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user settings.

        Args:
            username: Username

        Returns:
            User settings if user exists, None otherwise
        """
        # Check if username exists
        if username not in self.users:
            logging.warning(f"User {username} not found")
            return None

        # Return settings
        return self.users[username]["settings"]

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash a password with a salt.

        Args:
            password: Password
            salt: Salt

        Returns:
            Hashed password
        """
        # Combine password and salt
        salted_password = password + salt

        # Hash the salted password
        return hashlib.sha256(salted_password.encode()).hexdigest()

    def _create_session(self, username: str) -> str:
        """Create a new session for a user.

        Args:
            username: Username

        Returns:
            Session ID
        """
        # Generate session ID
        session_id = secrets.token_hex(32)

        # Create session
        active_sessions[session_id] = {
            "username": username,
            "created_at": time.time()
        }

        logging.info(f"Session {session_id} created for user {username}")
        return session_id


class PermissionManager:
    """Manages user permissions."""

    def __init__(self, auth_manager: AuthManager):
        """Initialize the permission manager.

        Args:
            auth_manager: Authentication manager
        """
        self.auth_manager = auth_manager
        self.role_permissions = {
            "admin": {
                "can_manage_users": True,
                "can_manage_settings": True,
                "can_use_tools": True,
                "can_use_graph": True,
                "can_use_multimodal": True,
                "can_use_advanced_features": True
            },
            "user": {
                "can_manage_users": False,
                "can_manage_settings": False,
                "can_use_tools": True,
                "can_use_graph": True,
                "can_use_multimodal": True,
                "can_use_advanced_features": False
            },
            "guest": {
                "can_manage_users": False,
                "can_manage_settings": False,
                "can_use_tools": False,
                "can_use_graph": True,
                "can_use_multimodal": False,
                "can_use_advanced_features": False
            }
        }

        logging.info("Permission Manager initialized")

    def check_permission(self, session_id: str, permission: str) -> bool:
        """Check if a user has a permission.

        Args:
            session_id: Session ID
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        # Validate session
        user_data = self.auth_manager.validate_session(session_id)
        if not user_data:
            logging.warning(f"Invalid session {session_id}")
            return False

        # Get user role
        role = user_data.get("role", "guest")

        # Check if role has permission
        if role not in self.role_permissions:
            logging.warning(f"Role {role} not found")
            return False

        # Check if permission exists
        if permission not in self.role_permissions[role]:
            logging.warning(f"Permission {permission} not found for role {role}")
            return False

        # Return permission value
        return self.role_permissions[role][permission]

    def get_user_permissions(self, session_id: str) -> Dict[str, bool]:
        """Get all permissions for a user.

        Args:
            session_id: Session ID

        Returns:
            Dictionary of permissions
        """
        # Validate session
        user_data = self.auth_manager.validate_session(session_id)
        if not user_data:
            logging.warning(f"Invalid session {session_id}")
            return {}

        # Get user role
        role = user_data.get("role", "guest")

        # Check if role exists
        if role not in self.role_permissions:
            logging.warning(f"Role {role} not found")
            return {}

        # Return permissions for role
        return self.role_permissions[role]
