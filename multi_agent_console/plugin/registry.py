"""
Plugin registry module for MultiAgentConsole.

This module provides a registry for discovering and managing plugins.
"""

import os
import json
import logging
import requests
import shutil
import zipfile
import tempfile
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

from .base import PluginManager, Plugin

logger = logging.getLogger(__name__)


class PluginInfo:
    """Information about a plugin."""
    
    def __init__(
        self,
        plugin_id: str,
        name: str,
        description: str,
        version: str,
        author: str,
        tags: List[str] = None,
        requirements: List[str] = None,
        installed: bool = False,
        rating: float = 0.0,
        downloads: int = 0,
        repository_url: str = None,
        homepage_url: str = None,
        icon_url: str = None,
    ):
        """Initialize plugin information.
        
        Args:
            plugin_id: Unique identifier for the plugin
            name: Display name of the plugin
            description: Description of the plugin
            version: Version string
            author: Author name
            tags: List of tags
            requirements: List of package requirements
            installed: Whether the plugin is installed
            rating: Average rating (0-5)
            downloads: Number of downloads
            repository_url: URL to the plugin's repository
            homepage_url: URL to the plugin's homepage
            icon_url: URL to the plugin's icon
        """
        self.plugin_id = plugin_id
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.tags = tags or []
        self.requirements = requirements or []
        self.installed = installed
        self.rating = rating
        self.downloads = downloads
        self.repository_url = repository_url
        self.homepage_url = homepage_url
        self.icon_url = icon_url
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "requirements": self.requirements,
            "installed": self.installed,
            "rating": self.rating,
            "downloads": self.downloads,
            "repository_url": self.repository_url,
            "homepage_url": self.homepage_url,
            "icon_url": self.icon_url,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginInfo':
        """Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            PluginInfo instance
        """
        return cls(
            plugin_id=data["plugin_id"],
            name=data["name"],
            description=data["description"],
            version=data["version"],
            author=data["author"],
            tags=data.get("tags", []),
            requirements=data.get("requirements", []),
            installed=data.get("installed", False),
            rating=data.get("rating", 0.0),
            downloads=data.get("downloads", 0),
            repository_url=data.get("repository_url"),
            homepage_url=data.get("homepage_url"),
            icon_url=data.get("icon_url"),
        )


class PluginRegistry:
    """Registry for discovering and managing plugins."""
    
    def __init__(
        self,
        plugins_dir: str = "plugins",
        registry_url: str = None,
        plugin_manager: Optional[PluginManager] = None
    ):
        """Initialize the plugin registry.
        
        Args:
            plugins_dir: Directory for storing plugins
            registry_url: URL to the plugin registry
            plugin_manager: Optional plugin manager instance
        """
        self.plugins_dir = plugins_dir
        self.registry_url = registry_url or "https://raw.githubusercontent.com/ssvgopal/multi_agent_console/main/registry/plugins.json"
        self.plugin_manager = plugin_manager
        self.installed_plugins: Dict[str, PluginInfo] = {}
        self.available_plugins: Dict[str, PluginInfo] = {}
        
        # Create plugins directory if it doesn't exist
        os.makedirs(plugins_dir, exist_ok=True)
        
        # Load installed plugins
        self.load_installed_plugins()
        
        logger.info(f"Plugin Registry initialized with {len(self.installed_plugins)} installed plugins")
    
    def load_installed_plugins(self) -> None:
        """Load installed plugins from the plugins directory."""
        self.installed_plugins = {}
        
        for plugin_dir in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, plugin_dir)
            if not os.path.isdir(plugin_path):
                continue
            
            # Check for plugin.json
            plugin_json_path = os.path.join(plugin_path, "plugin.json")
            if not os.path.exists(plugin_json_path):
                continue
            
            try:
                with open(plugin_json_path, "r") as f:
                    plugin_data = json.load(f)
                    
                    # Create plugin info
                    plugin_info = PluginInfo(
                        plugin_id=plugin_data.get("id", plugin_dir),
                        name=plugin_data.get("name", plugin_dir),
                        description=plugin_data.get("description", ""),
                        version=plugin_data.get("version", "0.0.0"),
                        author=plugin_data.get("author", "Unknown"),
                        tags=plugin_data.get("tags", []),
                        requirements=plugin_data.get("requirements", []),
                        installed=True,
                        rating=plugin_data.get("rating", 0.0),
                        downloads=plugin_data.get("downloads", 0),
                        repository_url=plugin_data.get("repository_url"),
                        homepage_url=plugin_data.get("homepage_url"),
                        icon_url=plugin_data.get("icon_url")
                    )
                    
                    self.installed_plugins[plugin_info.plugin_id] = plugin_info
                    logger.info(f"Loaded installed plugin: {plugin_info.name} ({plugin_info.plugin_id})")
            except Exception as e:
                logger.error(f"Error loading plugin from {plugin_json_path}: {e}")
    
    def refresh_registry(self) -> bool:
        """Refresh the plugin registry from the remote source.
        
        Returns:
            True if successful, False otherwise
        """
        self.available_plugins = {}
        
        try:
            # Fetch registry from remote
            response = requests.get(self.registry_url)
            response.raise_for_status()
            registry_data = response.json()
            
            # Process registry data
            for plugin_data in registry_data.get("plugins", []):
                plugin_info = PluginInfo.from_dict(plugin_data)
                
                # Check if already installed
                if plugin_info.plugin_id in self.installed_plugins:
                    plugin_info.installed = True
                
                self.available_plugins[plugin_info.plugin_id] = plugin_info
            
            logger.info(f"Refreshed plugin registry with {len(self.available_plugins)} available plugins")
            return True
        except Exception as e:
            logger.error(f"Error refreshing plugin registry: {e}")
            return False
    
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """Get list of available plugins.
        
        Returns:
            List of plugin dictionaries
        """
        return [plugin.to_dict() for plugin in self.available_plugins.values()]
    
    def get_installed_plugins(self) -> List[Dict[str, Any]]:
        """Get list of installed plugins.
        
        Returns:
            List of plugin dictionaries
        """
        return [plugin.to_dict() for plugin in self.installed_plugins.values()]
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Plugin information dictionary or None if not found
        """
        if plugin_id in self.installed_plugins:
            return self.installed_plugins[plugin_id].to_dict()
        elif plugin_id in self.available_plugins:
            return self.available_plugins[plugin_id].to_dict()
        return None
    
    def install_plugin(self, plugin_id: str) -> bool:
        """Install a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if successful, False otherwise
        """
        # Check if plugin is available
        if plugin_id not in self.available_plugins:
            logger.error(f"Plugin {plugin_id} not found in registry")
            return False
        
        # Get plugin info
        plugin_info = self.available_plugins[plugin_id]
        
        # Check if already installed
        if plugin_id in self.installed_plugins:
            logger.warning(f"Plugin {plugin_id} is already installed")
            return True
        
        try:
            # Create plugin directory
            plugin_dir = os.path.join(self.plugins_dir, plugin_id)
            os.makedirs(plugin_dir, exist_ok=True)
            
            # Download plugin package
            if plugin_info.repository_url:
                # Download from repository
                self._download_from_repository(plugin_info, plugin_dir)
            else:
                # Create basic structure
                self._create_basic_structure(plugin_info, plugin_dir)
            
            # Install requirements
            if plugin_info.requirements:
                self._install_requirements(plugin_info.requirements)
            
            # Mark as installed
            plugin_info.installed = True
            self.installed_plugins[plugin_id] = plugin_info
            
            # Update plugin manager if available
            if self.plugin_manager:
                self.plugin_manager.add_plugin_directory(plugin_dir)
                self.plugin_manager.load_plugins()
            
            logger.info(f"Installed plugin: {plugin_info.name} ({plugin_id})")
            return True
        except Exception as e:
            logger.error(f"Error installing plugin {plugin_id}: {e}")
            # Clean up
            plugin_dir = os.path.join(self.plugins_dir, plugin_id)
            if os.path.exists(plugin_dir):
                shutil.rmtree(plugin_dir)
            return False
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if successful, False otherwise
        """
        # Check if plugin is installed
        if plugin_id not in self.installed_plugins:
            logger.error(f"Plugin {plugin_id} is not installed")
            return False
        
        try:
            # Disable plugin in plugin manager if available
            if self.plugin_manager:
                plugin = self.plugin_manager.get_plugin(plugin_id)
                if plugin:
                    self.plugin_manager.disable_plugin(plugin_id)
            
            # Remove plugin directory
            plugin_dir = os.path.join(self.plugins_dir, plugin_id)
            if os.path.exists(plugin_dir):
                shutil.rmtree(plugin_dir)
            
            # Remove from installed plugins
            if plugin_id in self.installed_plugins:
                del self.installed_plugins[plugin_id]
            
            # Update available plugins
            if plugin_id in self.available_plugins:
                self.available_plugins[plugin_id].installed = False
            
            logger.info(f"Uninstalled plugin: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error uninstalling plugin {plugin_id}: {e}")
            return False
    
    def _download_from_repository(self, plugin_info: PluginInfo, plugin_dir: str) -> None:
        """Download plugin from repository.
        
        Args:
            plugin_info: Plugin information
            plugin_dir: Directory to install to
        """
        # Download from repository
        response = requests.get(plugin_info.repository_url)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        try:
            # Extract to plugin directory
            with zipfile.ZipFile(temp_path, "r") as zip_ref:
                zip_ref.extractall(plugin_dir)
            
            # Create plugin.json if it doesn't exist
            plugin_json_path = os.path.join(plugin_dir, "plugin.json")
            if not os.path.exists(plugin_json_path):
                with open(plugin_json_path, "w") as f:
                    json.dump({
                        "id": plugin_info.plugin_id,
                        "name": plugin_info.name,
                        "description": plugin_info.description,
                        "version": plugin_info.version,
                        "author": plugin_info.author,
                        "tags": plugin_info.tags,
                        "requirements": plugin_info.requirements,
                        "repository_url": plugin_info.repository_url,
                        "homepage_url": plugin_info.homepage_url,
                        "icon_url": plugin_info.icon_url
                    }, f, indent=2)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _create_basic_structure(self, plugin_info: PluginInfo, plugin_dir: str) -> None:
        """Create basic plugin structure.
        
        Args:
            plugin_info: Plugin information
            plugin_dir: Directory to install to
        """
        # Create plugin.json
        with open(os.path.join(plugin_dir, "plugin.json"), "w") as f:
            json.dump({
                "id": plugin_info.plugin_id,
                "name": plugin_info.name,
                "description": plugin_info.description,
                "version": plugin_info.version,
                "author": plugin_info.author,
                "tags": plugin_info.tags,
                "requirements": plugin_info.requirements,
                "repository_url": plugin_info.repository_url,
                "homepage_url": plugin_info.homepage_url,
                "icon_url": plugin_info.icon_url
            }, f, indent=2)
        
        # Create __init__.py
        with open(os.path.join(plugin_dir, "__init__.py"), "w") as f:
            f.write(f'"""\n{plugin_info.name} - {plugin_info.description}\n\nAuthor: {plugin_info.author}\nVersion: {plugin_info.version}\n"""\n\n')
        
        # Create plugin.py
        with open(os.path.join(plugin_dir, "plugin.py"), "w") as f:
            f.write(f'''"""
{plugin_info.name} - {plugin_info.description}

Author: {plugin_info.author}
Version: {plugin_info.version}
"""

from multi_agent_console.plugin.base import Plugin


class {plugin_info.plugin_id.title().replace("_", "")}Plugin(Plugin):
    """Plugin implementation."""
    
    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return "{plugin_info.plugin_id}"
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "{plugin_info.name}"
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "{plugin_info.version}"
    
    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "{plugin_info.description}"
    
    @property
    def author(self) -> str:
        """Get the plugin author."""
        return "{plugin_info.author}"
    
    def initialize(self, context):
        """Initialize the plugin."""
        return True
    
    def shutdown(self):
        """Shutdown the plugin."""
        return True
    
    def get_capabilities(self):
        """Get the plugin capabilities."""
        return ["example"]
    
    def handle_event(self, event_type, event_data):
        """Handle an event."""
        if event_type == "example":
            return {{"response": "Hello from {plugin_info.name}!"}}
        return None
''')
    
    def _install_requirements(self, requirements: List[str]) -> None:
        """Install package requirements.
        
        Args:
            requirements: List of package requirements
        """
        if not requirements:
            return
        
        try:
            import subprocess
            for req in requirements:
                subprocess.check_call(["pip", "install", req])
        except Exception as e:
            logger.error(f"Error installing requirements: {e}")
            raise
    
    def rate_plugin(self, plugin_id: str, rating: float) -> bool:
        """Rate a plugin.
        
        Args:
            plugin_id: Plugin ID
            rating: Rating (0-5)
            
        Returns:
            True if successful, False otherwise
        """
        # Validate rating
        if rating < 0 or rating > 5:
            logger.error(f"Invalid rating: {rating} (must be between 0 and 5)")
            return False
        
        # Check if plugin exists
        if plugin_id not in self.installed_plugins and plugin_id not in self.available_plugins:
            logger.error(f"Plugin {plugin_id} not found")
            return False
        
        # TODO: Submit rating to registry
        logger.info(f"Rated plugin {plugin_id}: {rating}")
        return True
    
    def search_plugins(self, query: str) -> List[Dict[str, Any]]:
        """Search for plugins.
        
        Args:
            query: Search query
            
        Returns:
            List of matching plugin dictionaries
        """
        query = query.lower()
        results = []
        
        for plugin in self.available_plugins.values():
            # Search in name, description, tags, and author
            if (query in plugin.name.lower() or
                query in plugin.description.lower() or
                query in plugin.author.lower() or
                any(query in tag.lower() for tag in plugin.tags)):
                results.append(plugin.to_dict())
        
        return results
