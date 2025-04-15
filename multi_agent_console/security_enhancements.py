"""
Security enhancements module for MultiAgentConsole.

This module provides utilities for enhancing the security of MultiAgentConsole,
including input validation, output sanitization, and secure credential management.

Author: Sai Sunkara
"""

import os
import re
import json
import base64
import hashlib
import logging
import secrets
import hmac
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast
from pathlib import Path
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from multi_agent_console.monitoring import get_logger

# Set up logger
logger = get_logger(__name__)


class InputValidator:
    """
    Validates and sanitizes user input to prevent security vulnerabilities.
    """
    
    # Regular expressions for validation
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')
    URL_REGEX = re.compile(r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$')
    FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9_\.-]+$')
    PATH_TRAVERSAL_REGEX = re.compile(r'\.\./')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
        
        Returns:
            True if valid, False otherwise
        """
        return bool(InputValidator.EMAIL_REGEX.match(email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate a username.
        
        Args:
            username: Username to validate
        
        Returns:
            True if valid, False otherwise
        """
        return bool(InputValidator.USERNAME_REGEX.match(username))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate a URL.
        
        Args:
            url: URL to validate
        
        Returns:
            True if valid, False otherwise
        """
        return bool(InputValidator.URL_REGEX.match(url))
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate a filename.
        
        Args:
            filename: Filename to validate
        
        Returns:
            True if valid, False otherwise
        """
        return bool(InputValidator.FILENAME_REGEX.match(filename))
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        Sanitize user input to prevent injection attacks.
        
        Args:
            input_str: Input string to sanitize
        
        Returns:
            Sanitized string
        """
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>]', '', input_str)
        
        # Remove potential SQL injection patterns
        sanitized = re.sub(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|UNION|CREATE|WHERE)\b)', 
                          lambda match: match.group(1).lower(), sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """
        Sanitize a file path to prevent path traversal attacks.
        
        Args:
            path: File path to sanitize
        
        Returns:
            Sanitized path
        """
        # Remove path traversal sequences
        sanitized = InputValidator.PATH_TRAVERSAL_REGEX.sub('', path)
        
        # Normalize path
        normalized = os.path.normpath(sanitized)
        
        # Ensure the path doesn't start with / or drive letter
        if normalized.startswith('/') or re.match(r'^[A-Za-z]:', normalized):
            normalized = os.path.basename(normalized)
        
        return normalized
    
    @staticmethod
    def validate_json(json_str: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate a JSON string.
        
        Args:
            json_str: JSON string to validate
        
        Returns:
            Tuple of (is_valid, parsed_json)
        """
        try:
            parsed = json.loads(json_str)
            return True, parsed
        except json.JSONDecodeError:
            return False, None


class OutputSanitizer:
    """
    Sanitizes output to prevent information disclosure and other vulnerabilities.
    """
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        """
        Sanitize HTML to prevent XSS attacks.
        
        Args:
            html: HTML string to sanitize
        
        Returns:
            Sanitized HTML
        """
        # Replace < and > with their HTML entities
        sanitized = html.replace('<', '&lt;').replace('>', '&gt;')
        
        # Replace quotes with their HTML entities
        sanitized = sanitized.replace('"', '&quot;').replace("'", '&#39;')
        
        return sanitized
    
    @staticmethod
    def sanitize_json(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a JSON object to prevent information disclosure.
        
        Args:
            data: JSON object to sanitize
        
        Returns:
            Sanitized JSON object
        """
        # Define sensitive keys to redact
        sensitive_keys = {'password', 'api_key', 'secret', 'token', 'key', 'credential'}
        
        def _sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for k, v in d.items():
                if any(sk in k.lower() for sk in sensitive_keys):
                    result[k] = '********'
                elif isinstance(v, dict):
                    result[k] = _sanitize_dict(v)
                elif isinstance(v, list):
                    result[k] = [_sanitize_dict(i) if isinstance(i, dict) else i for i in v]
                else:
                    result[k] = v
            return result
        
        return _sanitize_dict(data)
    
    @staticmethod
    def sanitize_error_message(message: str) -> str:
        """
        Sanitize error messages to prevent information disclosure.
        
        Args:
            message: Error message to sanitize
        
        Returns:
            Sanitized error message
        """
        # Remove file paths
        sanitized = re.sub(r'(\/[\w\-\.\/]+)+', '[PATH]', message)
        
        # Remove IP addresses
        sanitized = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', sanitized)
        
        # Remove email addresses
        sanitized = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', sanitized)
        
        return sanitized


class SecureCredentialManager:
    """
    Manages credentials securely using encryption.
    """
    
    def __init__(self, storage_path: str = 'data/credentials.enc'):
        """
        Initialize the credential manager.
        
        Args:
            storage_path: Path to the encrypted credentials file
        """
        self.storage_path = storage_path
        self.key = None
        self.fernet = None
        self.credentials = {}
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    
    def initialize(self, master_password: str) -> bool:
        """
        Initialize the credential manager with a master password.
        
        Args:
            master_password: Master password for encryption
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Generate a key from the master password
            salt = b'MultiAgentConsole'  # Fixed salt for simplicity
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            self.key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            self.fernet = Fernet(self.key)
            
            # Load existing credentials if available
            if os.path.exists(self.storage_path):
                self.load_credentials()
            else:
                self.credentials = {}
                self.save_credentials()
            
            return True
        except Exception as e:
            logger.error(f"Error initializing credential manager: {e}")
            return False
    
    def load_credentials(self) -> bool:
        """
        Load encrypted credentials from storage.
        
        Returns:
            True if loading was successful, False otherwise
        """
        if not self.fernet:
            logger.error("Credential manager not initialized")
            return False
        
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    encrypted_data = f.read()
                
                if encrypted_data:
                    decrypted_data = self.fernet.decrypt(encrypted_data)
                    self.credentials = json.loads(decrypted_data.decode())
                else:
                    self.credentials = {}
            else:
                self.credentials = {}
            
            return True
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return False
    
    def save_credentials(self) -> bool:
        """
        Save encrypted credentials to storage.
        
        Returns:
            True if saving was successful, False otherwise
        """
        if not self.fernet:
            logger.error("Credential manager not initialized")
            return False
        
        try:
            encrypted_data = self.fernet.encrypt(json.dumps(self.credentials).encode())
            
            with open(self.storage_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False
    
    def set_credential(self, service: str, key: str, value: str) -> bool:
        """
        Set a credential for a service.
        
        Args:
            service: Service name
            key: Credential key
            value: Credential value
        
        Returns:
            True if setting was successful, False otherwise
        """
        if not self.fernet:
            logger.error("Credential manager not initialized")
            return False
        
        try:
            if service not in self.credentials:
                self.credentials[service] = {}
            
            self.credentials[service][key] = value
            return self.save_credentials()
        except Exception as e:
            logger.error(f"Error setting credential: {e}")
            return False
    
    def get_credential(self, service: str, key: str) -> Optional[str]:
        """
        Get a credential for a service.
        
        Args:
            service: Service name
            key: Credential key
        
        Returns:
            Credential value or None if not found
        """
        if not self.fernet:
            logger.error("Credential manager not initialized")
            return None
        
        try:
            return self.credentials.get(service, {}).get(key)
        except Exception as e:
            logger.error(f"Error getting credential: {e}")
            return None
    
    def delete_credential(self, service: str, key: str) -> bool:
        """
        Delete a credential for a service.
        
        Args:
            service: Service name
            key: Credential key
        
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.fernet:
            logger.error("Credential manager not initialized")
            return False
        
        try:
            if service in self.credentials and key in self.credentials[service]:
                del self.credentials[service][key]
                
                # Remove the service if it has no credentials
                if not self.credentials[service]:
                    del self.credentials[service]
                
                return self.save_credentials()
            
            return True  # Key didn't exist, so deletion is technically successful
        except Exception as e:
            logger.error(f"Error deleting credential: {e}")
            return False
    
    def list_services(self) -> List[str]:
        """
        List all services with stored credentials.
        
        Returns:
            List of service names
        """
        if not self.fernet:
            logger.error("Credential manager not initialized")
            return []
        
        return list(self.credentials.keys())
    
    def list_credentials(self, service: str) -> List[str]:
        """
        List all credential keys for a service.
        
        Args:
            service: Service name
        
        Returns:
            List of credential keys
        """
        if not self.fernet:
            logger.error("Credential manager not initialized")
            return []
        
        return list(self.credentials.get(service, {}).keys())


class AuthenticationManager:
    """
    Manages user authentication and session management.
    """
    
    def __init__(self, storage_path: str = 'data/users.json'):
        """
        Initialize the authentication manager.
        
        Args:
            storage_path: Path to the user database file
        """
        self.storage_path = storage_path
        self.users = {}
        self.sessions = {}
        self.session_expiry = {}
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Load existing users if available
        if os.path.exists(storage_path):
            self.load_users()
    
    def load_users(self) -> bool:
        """
        Load users from storage.
        
        Returns:
            True if loading was successful, False otherwise
        """
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
            
            return True
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return False
    
    def save_users(self) -> bool:
        """
        Save users to storage.
        
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.users, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving users: {e}")
            return False
    
    def register_user(self, username: str, password: str) -> bool:
        """
        Register a new user.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            True if registration was successful, False otherwise
        """
        # Validate username
        if not InputValidator.validate_username(username):
            logger.error(f"Invalid username: {username}")
            return False
        
        # Check if username already exists
        if username in self.users:
            logger.error(f"Username already exists: {username}")
            return False
        
        # Generate salt
        salt = secrets.token_hex(16)
        
        # Hash password with salt
        password_hash = self._hash_password(password, salt)
        
        # Store user
        self.users[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        return self.save_users()
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate a user and create a session.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            Session ID if authentication was successful, None otherwise
        """
        # Check if username exists
        if username not in self.users:
            logger.error(f"Username not found: {username}")
            return None
        
        # Get user data
        user = self.users[username]
        
        # Hash password with stored salt
        password_hash = self._hash_password(password, user['salt'])
        
        # Check if password matches
        if password_hash != user['password_hash']:
            logger.error(f"Invalid password for user: {username}")
            return None
        
        # Generate session ID
        session_id = secrets.token_hex(32)
        
        # Store session
        self.sessions[session_id] = username
        
        # Set session expiry (24 hours)
        self.session_expiry[session_id] = datetime.now() + timedelta(hours=24)
        
        # Update last login
        user['last_login'] = datetime.now().isoformat()
        self.save_users()
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            User data if session is valid, None otherwise
        """
        # Check if session exists
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return None
        
        # Check if session has expired
        if datetime.now() > self.session_expiry[session_id]:
            logger.error(f"Session expired: {session_id}")
            self.invalidate_session(session_id)
            return None
        
        # Get username
        username = self.sessions[session_id]
        
        # Get user data
        user = self.users[username]
        
        # Return user data
        return {
            'username': username,
            'created_at': user['created_at'],
            'last_login': user['last_login']
        }
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            True if invalidation was successful, False otherwise
        """
        # Check if session exists
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return False
        
        # Remove session
        del self.sessions[session_id]
        
        # Remove session expiry
        if session_id in self.session_expiry:
            del self.session_expiry[session_id]
        
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            username: Username
            old_password: Old password
            new_password: New password
        
        Returns:
            True if password change was successful, False otherwise
        """
        # Check if username exists
        if username not in self.users:
            logger.error(f"Username not found: {username}")
            return False
        
        # Get user data
        user = self.users[username]
        
        # Hash old password with stored salt
        old_password_hash = self._hash_password(old_password, user['salt'])
        
        # Check if old password matches
        if old_password_hash != user['password_hash']:
            logger.error(f"Invalid old password for user: {username}")
            return False
        
        # Generate new salt
        salt = secrets.token_hex(16)
        
        # Hash new password with new salt
        password_hash = self._hash_password(new_password, salt)
        
        # Update user
        user['password_hash'] = password_hash
        user['salt'] = salt
        
        return self.save_users()
    
    def delete_user(self, username: str, password: str) -> bool:
        """
        Delete a user.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            True if deletion was successful, False otherwise
        """
        # Check if username exists
        if username not in self.users:
            logger.error(f"Username not found: {username}")
            return False
        
        # Get user data
        user = self.users[username]
        
        # Hash password with stored salt
        password_hash = self._hash_password(password, user['salt'])
        
        # Check if password matches
        if password_hash != user['password_hash']:
            logger.error(f"Invalid password for user: {username}")
            return False
        
        # Remove user
        del self.users[username]
        
        # Invalidate all sessions for this user
        for session_id, session_username in list(self.sessions.items()):
            if session_username == username:
                self.invalidate_session(session_id)
        
        return self.save_users()
    
    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash a password with a salt.
        
        Args:
            password: Password
            salt: Salt
        
        Returns:
            Hashed password
        """
        # Convert salt to bytes
        salt_bytes = bytes.fromhex(salt)
        
        # Hash password with salt
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt_bytes,
            100000
        ).hex()


class CSRFProtection:
    """
    Provides protection against Cross-Site Request Forgery (CSRF) attacks.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret key for token generation (generated if None)
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.tokens = {}
    
    def generate_token(self, session_id: str) -> str:
        """
        Generate a CSRF token for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            CSRF token
        """
        # Generate a random token
        token = secrets.token_hex(16)
        
        # Store token with session ID
        self.tokens[session_id] = token
        
        return token
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """
        Validate a CSRF token for a session.
        
        Args:
            session_id: Session ID
            token: CSRF token
        
        Returns:
            True if token is valid, False otherwise
        """
        # Check if session has a token
        if session_id not in self.tokens:
            logger.error(f"No token found for session: {session_id}")
            return False
        
        # Check if token matches
        if token != self.tokens[session_id]:
            logger.error(f"Invalid CSRF token for session: {session_id}")
            return False
        
        return True
    
    def clear_token(self, session_id: str) -> bool:
        """
        Clear a CSRF token for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            True if clearing was successful, False otherwise
        """
        # Check if session has a token
        if session_id not in self.tokens:
            return True  # Token already cleared
        
        # Remove token
        del self.tokens[session_id]
        
        return True


class RateLimiter:
    """
    Provides rate limiting to prevent abuse.
    """
    
    def __init__(self, limit: int = 100, window: int = 3600):
        """
        Initialize rate limiting.
        
        Args:
            limit: Maximum number of requests per window
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.requests = {}
    
    def check_limit(self, key: str) -> bool:
        """
        Check if a key has exceeded the rate limit.
        
        Args:
            key: Key to check (e.g., IP address, user ID)
        
        Returns:
            True if limit is not exceeded, False otherwise
        """
        # Get current time
        now = datetime.now()
        
        # Initialize requests for key if not exists
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove expired requests
        self.requests[key] = [t for t in self.requests[key] if now - t < timedelta(seconds=self.window)]
        
        # Check if limit is exceeded
        if len(self.requests[key]) >= self.limit:
            logger.warning(f"Rate limit exceeded for key: {key}")
            return False
        
        # Add current request
        self.requests[key].append(now)
        
        return True
    
    def get_remaining(self, key: str) -> int:
        """
        Get the number of remaining requests for a key.
        
        Args:
            key: Key to check
        
        Returns:
            Number of remaining requests
        """
        # Get current time
        now = datetime.now()
        
        # Initialize requests for key if not exists
        if key not in self.requests:
            return self.limit
        
        # Remove expired requests
        self.requests[key] = [t for t in self.requests[key] if now - t < timedelta(seconds=self.window)]
        
        # Calculate remaining requests
        return max(0, self.limit - len(self.requests[key]))
    
    def reset(self, key: str) -> None:
        """
        Reset the rate limit for a key.
        
        Args:
            key: Key to reset
        """
        if key in self.requests:
            del self.requests[key]


# Global instances
input_validator = InputValidator()
output_sanitizer = OutputSanitizer()
credential_manager = SecureCredentialManager()
auth_manager = AuthenticationManager()
csrf_protection = CSRFProtection()
rate_limiter = RateLimiter()


def setup_security(
    master_password: Optional[str] = None,
    csrf_secret_key: Optional[str] = None,
    rate_limit: int = 100,
    rate_window: int = 3600
) -> bool:
    """
    Set up security features.
    
    Args:
        master_password: Master password for credential encryption
        csrf_secret_key: Secret key for CSRF token generation
        rate_limit: Maximum number of requests per window
        rate_window: Time window in seconds
    
    Returns:
        True if setup was successful, False otherwise
    """
    global credential_manager, csrf_protection, rate_limiter
    
    try:
        # Initialize credential manager if master password is provided
        if master_password:
            if not credential_manager.initialize(master_password):
                logger.error("Failed to initialize credential manager")
                return False
        
        # Initialize CSRF protection
        csrf_protection = CSRFProtection(csrf_secret_key)
        
        # Initialize rate limiter
        rate_limiter = RateLimiter(rate_limit, rate_window)
        
        logger.info("Security features initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up security features: {e}")
        return False
