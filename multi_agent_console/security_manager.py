"""
Enhanced Security Features for MultiAgentConsole.

This module provides security capabilities:
- More robust sandboxing for code execution
- Permission management system for file and system operations
- Credential management for secure API access
- Encryption for sensitive data in configuration and memory
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
import hashlib
import base64
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from functools import wraps

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False


class PermissionManager:
    """Manages permissions for file and system operations."""
    
    # Permission levels
    PERMISSION_NONE = 0
    PERMISSION_READ = 1
    PERMISSION_WRITE = 2
    PERMISSION_EXECUTE = 4
    PERMISSION_NETWORK = 8
    PERMISSION_ALL = 15
    
    def __init__(self, config_path: str = "data/permissions.json"):
        """Initialize the permission manager.
        
        Args:
            config_path: Path to the permissions configuration file
        """
        self.config_path = config_path
        self.permissions = {}
        self.allowed_paths = {}
        self.allowed_domains = {}
        self.allowed_commands = {}
        self.user_permissions = {}
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Load permissions
        self.load_permissions()
        
        logging.info("Permission Manager initialized")
    
    def load_permissions(self) -> None:
        """Load permissions from the configuration file."""
        if not os.path.exists(self.config_path):
            # Create default permissions
            default_permissions = {
                "default": {
                    "permission_level": self.PERMISSION_READ,
                    "allowed_paths": ["data/"],
                    "allowed_domains": ["api.openweathermap.org", "newsapi.org"],
                    "allowed_commands": ["python"]
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(default_permissions, f, indent=2)
            
            self.permissions = default_permissions
        else:
            try:
                with open(self.config_path, 'r') as f:
                    self.permissions = json.load(f)
            except json.JSONDecodeError:
                logging.error(f"Error parsing permissions file: {self.config_path}")
                self.permissions = {}
        
        # Process permissions
        for user_id, perms in self.permissions.items():
            self.user_permissions[user_id] = perms.get("permission_level", self.PERMISSION_READ)
            self.allowed_paths[user_id] = set(perms.get("allowed_paths", []))
            self.allowed_domains[user_id] = set(perms.get("allowed_domains", []))
            self.allowed_commands[user_id] = set(perms.get("allowed_commands", []))
    
    def save_permissions(self) -> None:
        """Save permissions to the configuration file."""
        # Convert sets to lists for JSON serialization
        serializable_permissions = {}
        
        for user_id in self.user_permissions:
            serializable_permissions[user_id] = {
                "permission_level": self.user_permissions[user_id],
                "allowed_paths": list(self.allowed_paths.get(user_id, [])),
                "allowed_domains": list(self.allowed_domains.get(user_id, [])),
                "allowed_commands": list(self.allowed_commands.get(user_id, []))
            }
        
        with open(self.config_path, 'w') as f:
            json.dump(serializable_permissions, f, indent=2)
    
    def get_user_permission_level(self, user_id: str) -> int:
        """Get the permission level for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Permission level
        """
        return self.user_permissions.get(user_id, self.user_permissions.get("default", self.PERMISSION_READ))
    
    def set_user_permission_level(self, user_id: str, permission_level: int) -> None:
        """Set the permission level for a user.
        
        Args:
            user_id: User identifier
            permission_level: Permission level
        """
        self.user_permissions[user_id] = permission_level
        self.save_permissions()
    
    def check_permission(self, user_id: str, required_permission: int) -> bool:
        """Check if a user has the required permission.
        
        Args:
            user_id: User identifier
            required_permission: Required permission level
            
        Returns:
            True if the user has the required permission, False otherwise
        """
        user_permission = self.get_user_permission_level(user_id)
        return (user_permission & required_permission) == required_permission
    
    def check_path_permission(self, user_id: str, path: str, required_permission: int) -> bool:
        """Check if a user has permission to access a path.
        
        Args:
            user_id: User identifier
            path: Path to check
            required_permission: Required permission level
            
        Returns:
            True if the user has permission to access the path, False otherwise
        """
        # Check if the user has the required permission level
        if not self.check_permission(user_id, required_permission):
            return False
        
        # Check if the path is in the allowed paths
        path = os.path.abspath(path)
        allowed = False
        
        for allowed_path in self.allowed_paths.get(user_id, self.allowed_paths.get("default", [])):
            allowed_path = os.path.abspath(allowed_path)
            if path.startswith(allowed_path):
                allowed = True
                break
        
        return allowed
    
    def check_domain_permission(self, user_id: str, domain: str) -> bool:
        """Check if a user has permission to access a domain.
        
        Args:
            user_id: User identifier
            domain: Domain to check
            
        Returns:
            True if the user has permission to access the domain, False otherwise
        """
        # Check if the user has network permission
        if not self.check_permission(user_id, self.PERMISSION_NETWORK):
            return False
        
        # Check if the domain is in the allowed domains
        allowed_domains = self.allowed_domains.get(user_id, self.allowed_domains.get("default", []))
        
        # Check for exact match
        if domain in allowed_domains:
            return True
        
        # Check for wildcard match
        for allowed_domain in allowed_domains:
            if allowed_domain.startswith("*.") and domain.endswith(allowed_domain[1:]):
                return True
        
        return False
    
    def check_command_permission(self, user_id: str, command: str) -> bool:
        """Check if a user has permission to execute a command.
        
        Args:
            user_id: User identifier
            command: Command to check
            
        Returns:
            True if the user has permission to execute the command, False otherwise
        """
        # Check if the user has execute permission
        if not self.check_permission(user_id, self.PERMISSION_EXECUTE):
            return False
        
        # Extract the command name (first word)
        command_name = command.split()[0]
        
        # Check if the command is in the allowed commands
        allowed_commands = self.allowed_commands.get(user_id, self.allowed_commands.get("default", []))
        return command_name in allowed_commands
    
    def add_allowed_path(self, user_id: str, path: str) -> None:
        """Add a path to the allowed paths for a user.
        
        Args:
            user_id: User identifier
            path: Path to add
        """
        if user_id not in self.allowed_paths:
            self.allowed_paths[user_id] = set()
        
        self.allowed_paths[user_id].add(path)
        self.save_permissions()
    
    def add_allowed_domain(self, user_id: str, domain: str) -> None:
        """Add a domain to the allowed domains for a user.
        
        Args:
            user_id: User identifier
            domain: Domain to add
        """
        if user_id not in self.allowed_domains:
            self.allowed_domains[user_id] = set()
        
        self.allowed_domains[user_id].add(domain)
        self.save_permissions()
    
    def add_allowed_command(self, user_id: str, command: str) -> None:
        """Add a command to the allowed commands for a user.
        
        Args:
            user_id: User identifier
            command: Command to add
        """
        if user_id not in self.allowed_commands:
            self.allowed_commands[user_id] = set()
        
        self.allowed_commands[user_id].add(command)
        self.save_permissions()
    
    def remove_allowed_path(self, user_id: str, path: str) -> None:
        """Remove a path from the allowed paths for a user.
        
        Args:
            user_id: User identifier
            path: Path to remove
        """
        if user_id in self.allowed_paths and path in self.allowed_paths[user_id]:
            self.allowed_paths[user_id].remove(path)
            self.save_permissions()
    
    def remove_allowed_domain(self, user_id: str, domain: str) -> None:
        """Remove a domain from the allowed domains for a user.
        
        Args:
            user_id: User identifier
            domain: Domain to remove
        """
        if user_id in self.allowed_domains and domain in self.allowed_domains[user_id]:
            self.allowed_domains[user_id].remove(domain)
            self.save_permissions()
    
    def remove_allowed_command(self, user_id: str, command: str) -> None:
        """Remove a command from the allowed commands for a user.
        
        Args:
            user_id: User identifier
            command: Command to remove
        """
        if user_id in self.allowed_commands and command in self.allowed_commands[user_id]:
            self.allowed_commands[user_id].remove(command)
            self.save_permissions()


class CodeSandbox:
    """Provides secure code execution in a sandbox."""
    
    def __init__(self, sandbox_dir: str = "data/sandbox"):
        """Initialize the code sandbox.
        
        Args:
            sandbox_dir: Directory for the sandbox
        """
        self.sandbox_dir = sandbox_dir
        
        # Create sandbox directory if it doesn't exist
        os.makedirs(sandbox_dir, exist_ok=True)
        
        # Create a virtual environment for the sandbox
        self._create_virtual_env()
        
        logging.info(f"Code Sandbox initialized at {sandbox_dir}")
    
    def _create_virtual_env(self) -> None:
        """Create a virtual environment for the sandbox."""
        venv_dir = os.path.join(self.sandbox_dir, "venv")
        
        if not os.path.exists(venv_dir):
            try:
                subprocess.run(
                    [sys.executable, "-m", "venv", venv_dir],
                    check=True,
                    capture_output=True
                )
                logging.info(f"Created virtual environment at {venv_dir}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error creating virtual environment: {e}")
    
    def _get_python_executable(self) -> str:
        """Get the path to the Python executable in the virtual environment.
        
        Returns:
            Path to the Python executable
        """
        if os.name == "nt":  # Windows
            return os.path.join(self.sandbox_dir, "venv", "Scripts", "python.exe")
        else:  # Unix-like
            return os.path.join(self.sandbox_dir, "venv", "bin", "python")
    
    def install_package(self, package_name: str) -> str:
        """Install a package in the sandbox.
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            Result of the installation
        """
        # Check if the package name is safe
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', package_name):
            return f"Invalid package name: {package_name}"
        
        try:
            python_executable = self._get_python_executable()
            
            result = subprocess.run(
                [python_executable, "-m", "pip", "install", package_name],
                check=True,
                capture_output=True,
                text=True
            )
            
            return f"Package {package_name} installed successfully:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing package {package_name}: {e}")
            return f"Error installing package {package_name}:\n{e.stderr}"
    
    def execute_code(self, code: str, timeout: int = 10) -> str:
        """Execute code in the sandbox.
        
        Args:
            code: Code to execute
            timeout: Timeout in seconds
            
        Returns:
            Result of the execution
        """
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(suffix=".py", dir=self.sandbox_dir, delete=False) as f:
                f.write(code.encode())
                temp_file = f.name
            
            # Execute the code in the sandbox
            python_executable = self._get_python_executable()
            
            # Set up environment variables
            env = os.environ.copy()
            env["PYTHONPATH"] = self.sandbox_dir
            
            # Run the code
            result = subprocess.run(
                [python_executable, temp_file],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            # Clean up
            os.unlink(temp_file)
            
            # Return the result
            if result.returncode == 0:
                return f"Output:\n{result.stdout}"
            else:
                return f"Error:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Execution timed out after {timeout} seconds"
        except Exception as e:
            logging.exception(f"Error executing code: {e}")
            return f"Error executing code: {str(e)}"


class CredentialManager:
    """Manages secure storage and access to credentials."""
    
    def __init__(self, credentials_path: str = "data/credentials.json"):
        """Initialize the credential manager.
        
        Args:
            credentials_path: Path to the credentials file
        """
        self.credentials_path = credentials_path
        self.credentials = {}
        self.encryption_key = None
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
        
        # Initialize encryption
        self._initialize_encryption()
        
        # Load credentials
        self.load_credentials()
        
        logging.info("Credential Manager initialized")
    
    def _initialize_encryption(self) -> None:
        """Initialize encryption for secure storage."""
        if not ENCRYPTION_AVAILABLE:
            logging.warning("Encryption libraries not available. Credentials will be stored in plaintext.")
            return
        
        # Check if we have an encryption key
        key_path = os.path.join(os.path.dirname(self.credentials_path), "encryption_key")
        
        if os.path.exists(key_path):
            # Load the existing key
            with open(key_path, 'rb') as f:
                self.encryption_key = f.read()
        else:
            # Generate a new key
            self.encryption_key = Fernet.generate_key()
            
            # Save the key
            with open(key_path, 'wb') as f:
                f.write(self.encryption_key)
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as a base64-encoded string
        """
        if not ENCRYPTION_AVAILABLE or not self.encryption_key:
            return data
        
        fernet = Fernet(self.encryption_key)
        encrypted_data = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def _decrypt(self, data: str) -> str:
        """Decrypt data.
        
        Args:
            data: Encrypted data as a base64-encoded string
            
        Returns:
            Decrypted data
        """
        if not ENCRYPTION_AVAILABLE or not self.encryption_key:
            return data
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = base64.b64decode(data)
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            logging.error(f"Error decrypting data: {e}")
            return data
    
    def load_credentials(self) -> None:
        """Load credentials from the credentials file."""
        if not os.path.exists(self.credentials_path):
            self.credentials = {}
            return
        
        try:
            with open(self.credentials_path, 'r') as f:
                encrypted_credentials = json.load(f)
            
            # Decrypt credentials
            self.credentials = {}
            for service, encrypted_creds in encrypted_credentials.items():
                self.credentials[service] = {}
                for key, value in encrypted_creds.items():
                    self.credentials[service][key] = self._decrypt(value)
        except json.JSONDecodeError:
            logging.error(f"Error parsing credentials file: {self.credentials_path}")
            self.credentials = {}
    
    def save_credentials(self) -> None:
        """Save credentials to the credentials file."""
        # Encrypt credentials
        encrypted_credentials = {}
        for service, creds in self.credentials.items():
            encrypted_credentials[service] = {}
            for key, value in creds.items():
                encrypted_credentials[service][key] = self._encrypt(value)
        
        with open(self.credentials_path, 'w') as f:
            json.dump(encrypted_credentials, f, indent=2)
    
    def get_credential(self, service: str, key: str) -> Optional[str]:
        """Get a credential.
        
        Args:
            service: Service name
            key: Credential key
            
        Returns:
            Credential value or None if not found
        """
        if service not in self.credentials or key not in self.credentials[service]:
            return None
        
        return self.credentials[service][key]
    
    def set_credential(self, service: str, key: str, value: str) -> None:
        """Set a credential.
        
        Args:
            service: Service name
            key: Credential key
            value: Credential value
        """
        if service not in self.credentials:
            self.credentials[service] = {}
        
        self.credentials[service][key] = value
        self.save_credentials()
    
    def delete_credential(self, service: str, key: str) -> bool:
        """Delete a credential.
        
        Args:
            service: Service name
            key: Credential key
            
        Returns:
            True if the credential was deleted, False otherwise
        """
        if service not in self.credentials or key not in self.credentials[service]:
            return False
        
        del self.credentials[service][key]
        
        # Remove the service if it's empty
        if not self.credentials[service]:
            del self.credentials[service]
        
        self.save_credentials()
        return True
    
    def list_services(self) -> List[str]:
        """List all services with stored credentials.
        
        Returns:
            List of service names
        """
        return list(self.credentials.keys())
    
    def list_credentials(self, service: str) -> List[str]:
        """List all credential keys for a service.
        
        Args:
            service: Service name
            
        Returns:
            List of credential keys
        """
        if service not in self.credentials:
            return []
        
        return list(self.credentials[service].keys())


class SecurityManager:
    """Manages security features for MultiAgentConsole."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the security manager.
        
        Args:
            data_dir: Directory for security data
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize components
        self.permission_manager = PermissionManager(os.path.join(data_dir, "permissions.json"))
        self.code_sandbox = CodeSandbox(os.path.join(data_dir, "sandbox"))
        self.credential_manager = CredentialManager(os.path.join(data_dir, "credentials.json"))
        
        logging.info("Security Manager initialized")
    
    def secure_execute_code(self, user_id: str, code: str, timeout: int = 10) -> str:
        """Execute code securely.
        
        Args:
            user_id: User identifier
            code: Code to execute
            timeout: Timeout in seconds
            
        Returns:
            Result of the execution
        """
        # Check if the user has execute permission
        if not self.permission_manager.check_permission(user_id, PermissionManager.PERMISSION_EXECUTE):
            return "Permission denied: You do not have execute permission."
        
        # Check for potentially dangerous code
        if self._is_dangerous_code(code):
            return "Permission denied: The code contains potentially dangerous operations."
        
        # Execute the code in the sandbox
        return self.code_sandbox.execute_code(code, timeout)
    
    def _is_dangerous_code(self, code: str) -> bool:
        """Check if code contains potentially dangerous operations.
        
        Args:
            code: Code to check
            
        Returns:
            True if the code is potentially dangerous, False otherwise
        """
        # Check for imports of potentially dangerous modules
        dangerous_modules = [
            "os", "subprocess", "sys", "shutil", "socket", "requests",
            "urllib", "ftplib", "telnetlib", "smtplib", "ctypes"
        ]
        
        for module in dangerous_modules:
            if re.search(rf"(^|\s)import\s+{module}(\s|$)", code) or re.search(rf"(^|\s)from\s+{module}\s+import", code):
                return True
        
        # Check for file operations
        if re.search(r"open\s*\(", code):
            return True
        
        # Check for eval or exec
        if re.search(r"(^|\s)(eval|exec)\s*\(", code):
            return True
        
        return False
    
    def secure_file_read(self, user_id: str, file_path: str) -> str:
        """Read a file securely.
        
        Args:
            user_id: User identifier
            file_path: Path to the file
            
        Returns:
            File contents or error message
        """
        # Check if the user has read permission for the file
        if not self.permission_manager.check_path_permission(user_id, file_path, PermissionManager.PERMISSION_READ):
            return f"Permission denied: You do not have read permission for {file_path}."
        
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {str(e)}"
    
    def secure_file_write(self, user_id: str, file_path: str, content: str) -> str:
        """Write to a file securely.
        
        Args:
            user_id: User identifier
            file_path: Path to the file
            content: Content to write
            
        Returns:
            Success message or error message
        """
        # Check if the user has write permission for the file
        if not self.permission_manager.check_path_permission(user_id, file_path, PermissionManager.PERMISSION_WRITE):
            return f"Permission denied: You do not have write permission for {file_path}."
        
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return f"File {file_path} written successfully."
        except Exception as e:
            logging.error(f"Error writing to file {file_path}: {e}")
            return f"Error writing to file: {str(e)}"
    
    def secure_http_request(self, user_id: str, url: str, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                           params: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None) -> str:
        """Make an HTTP request securely.
        
        Args:
            user_id: User identifier
            url: URL to request
            method: HTTP method
            headers: HTTP headers
            params: Query parameters
            data: Request body data
            
        Returns:
            Response or error message
        """
        # Extract domain from URL
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
        # Check if the user has permission to access the domain
        if not self.permission_manager.check_domain_permission(user_id, domain):
            return f"Permission denied: You do not have permission to access {domain}."
        
        try:
            import requests
            
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            )
            
            # Check if the response is JSON
            try:
                json_response = response.json()
                return json.dumps(json_response, indent=2)
            except ValueError:
                return response.text
        except Exception as e:
            logging.error(f"Error making HTTP request to {url}: {e}")
            return f"Error making HTTP request: {str(e)}"
    
    def secure_command_execution(self, user_id: str, command: str, timeout: int = 10) -> str:
        """Execute a command securely.
        
        Args:
            user_id: User identifier
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Command output or error message
        """
        # Check if the user has permission to execute the command
        if not self.permission_manager.check_command_permission(user_id, command):
            return f"Permission denied: You do not have permission to execute {command}."
        
        try:
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Return the result
            if result.returncode == 0:
                return f"Output:\n{result.stdout}"
            else:
                return f"Error (exit code {result.returncode}):\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return f"Command execution timed out after {timeout} seconds"
        except Exception as e:
            logging.error(f"Error executing command {command}: {e}")
            return f"Error executing command: {str(e)}"
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get an API key securely.
        
        Args:
            service: Service name
            
        Returns:
            API key or None if not found
        """
        return self.credential_manager.get_credential(service, "api_key")
    
    def set_api_key(self, service: str, api_key: str) -> None:
        """Set an API key securely.
        
        Args:
            service: Service name
            api_key: API key
        """
        self.credential_manager.set_credential(service, "api_key", api_key)
    
    def get_user_permission_summary(self, user_id: str) -> str:
        """Get a summary of a user's permissions.
        
        Args:
            user_id: User identifier
            
        Returns:
            Permission summary as a string
        """
        permission_level = self.permission_manager.get_user_permission_level(user_id)
        allowed_paths = self.permission_manager.allowed_paths.get(user_id, set())
        allowed_domains = self.permission_manager.allowed_domains.get(user_id, set())
        allowed_commands = self.permission_manager.allowed_commands.get(user_id, set())
        
        summary = f"Permissions for user {user_id}:\n\n"
        
        # Permission level
        summary += "Permission Level:\n"
        summary += f"- Read: {'Yes' if permission_level & PermissionManager.PERMISSION_READ else 'No'}\n"
        summary += f"- Write: {'Yes' if permission_level & PermissionManager.PERMISSION_WRITE else 'No'}\n"
        summary += f"- Execute: {'Yes' if permission_level & PermissionManager.PERMISSION_EXECUTE else 'No'}\n"
        summary += f"- Network: {'Yes' if permission_level & PermissionManager.PERMISSION_NETWORK else 'No'}\n\n"
        
        # Allowed paths
        summary += "Allowed Paths:\n"
        if allowed_paths:
            for path in allowed_paths:
                summary += f"- {path}\n"
        else:
            summary += "- None\n"
        summary += "\n"
        
        # Allowed domains
        summary += "Allowed Domains:\n"
        if allowed_domains:
            for domain in allowed_domains:
                summary += f"- {domain}\n"
        else:
            summary += "- None\n"
        summary += "\n"
        
        # Allowed commands
        summary += "Allowed Commands:\n"
        if allowed_commands:
            for command in allowed_commands:
                summary += f"- {command}\n"
        else:
            summary += "- None\n"
        
        return summary
