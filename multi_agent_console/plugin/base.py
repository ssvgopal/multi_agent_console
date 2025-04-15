"""
Base plugin module for MultiAgentConsole.

This module defines the base plugin interface and plugin manager.
"""

import os
import sys
import importlib
import importlib.util
import inspect
import json
import logging
import pkgutil
from typing import Dict, List, Any, Optional, Type, Callable, Union, Set
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Get the plugin ID.
        
        Returns:
            Plugin ID
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the plugin name.
        
        Returns:
            Plugin name
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Get the plugin version.
        
        Returns:
            Plugin version
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the plugin description.
        
        Returns:
            Plugin description
        """
        pass
    
    @property
    def author(self) -> str:
        """Get the plugin author.
        
        Returns:
            Plugin author
        """
        return "Unknown"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the plugin dependencies.
        
        Returns:
            List of plugin IDs that this plugin depends on
        """
        return []
    
    @property
    def settings_schema(self) -> Dict[str, Any]:
        """Get the plugin settings schema.
        
        Returns:
            JSON schema for plugin settings
        """
        return {}
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the plugin.
        
        Args:
            context: Plugin initialization context
            
        Returns:
            True if initialization was successful, False otherwise
        """
        return True
    
    def shutdown(self) -> bool:
        """Shutdown the plugin.
        
        Returns:
            True if shutdown was successful, False otherwise
        """
        return True
    
    def get_capabilities(self) -> List[str]:
        """Get the plugin capabilities.
        
        Returns:
            List of capability strings
        """
        return []
    
    def get_settings(self) -> Dict[str, Any]:
        """Get the plugin settings.
        
        Returns:
            Dictionary of plugin settings
        """
        return {}
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update the plugin settings.
        
        Args:
            settings: New settings
            
        Returns:
            True if settings were updated successfully, False otherwise
        """
        return True
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, str]:
        """Validate plugin settings.
        
        Args:
            settings: Settings to validate
            
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        return {}
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Get UI components provided by the plugin.
        
        Returns:
            Dictionary of UI component definitions
        """
        return {}
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle an event.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Optional response data
        """
        return None


class PluginManager:
    """Manager for loading and managing plugins."""
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """Initialize the plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or []
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_modules: Dict[str, Any] = {}
        self.disabled_plugins: Set[str] = set()
        self.plugin_dependencies: Dict[str, List[str]] = {}
        self.plugin_dependents: Dict[str, List[str]] = {}
        self.plugin_errors: Dict[str, str] = {}
        self.plugin_context: Dict[str, Any] = {}
    
    def add_plugin_directory(self, directory: str):
        """Add a directory to search for plugins.
        
        Args:
            directory: Directory path
        """
        if os.path.isdir(directory) and directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
    
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """Discover available plugins.
        
        Returns:
            List of plugin metadata
        """
        discovered_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.isdir(plugin_dir):
                logger.warning(f"Plugin directory not found: {plugin_dir}")
                continue
            
            # Add to Python path if not already there
            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
            
            # Look for plugin.json files
            for root, dirs, files in os.walk(plugin_dir):
                if 'plugin.json' in files:
                    plugin_json_path = os.path.join(root, 'plugin.json')
                    try:
                        with open(plugin_json_path, 'r') as f:
                            plugin_info = json.load(f)
                            
                            # Add plugin path
                            plugin_info['path'] = root
                            
                            # Add to discovered plugins
                            discovered_plugins.append(plugin_info)
                    except Exception as e:
                        logger.error(f"Error loading plugin.json from {plugin_json_path}: {e}")
        
        return discovered_plugins
    
    def load_plugin(self, plugin_path: str) -> Optional[Plugin]:
        """Load a plugin from a path.
        
        Args:
            plugin_path: Path to the plugin directory
            
        Returns:
            Plugin instance or None if loading failed
        """
        try:
            # Check if plugin.json exists
            plugin_json_path = os.path.join(plugin_path, 'plugin.json')
            if not os.path.isfile(plugin_json_path):
                logger.error(f"plugin.json not found in {plugin_path}")
                return None
            
            # Load plugin metadata
            with open(plugin_json_path, 'r') as f:
                plugin_info = json.load(f)
            
            # Get plugin module name
            module_name = plugin_info.get('module', 'plugin')
            
            # Load the plugin module
            module_path = os.path.join(plugin_path, f"{module_name}.py")
            if not os.path.isfile(module_path):
                logger.error(f"Plugin module not found: {module_path}")
                return None
            
            # Import the module
            spec = importlib.util.spec_from_file_location(
                f"multi_agent_console.plugins.{os.path.basename(plugin_path)}.{module_name}",
                module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the plugin class
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj is not Plugin):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                logger.error(f"No Plugin subclass found in {module_path}")
                return None
            
            # Create plugin instance
            plugin = plugin_class()
            
            # Store the module
            self.plugin_modules[plugin.id] = module
            
            return plugin
        
        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_path}: {e}")
            return None
    
    def load_plugins(self) -> Dict[str, Plugin]:
        """Load all available plugins.
        
        Returns:
            Dictionary mapping plugin IDs to plugin instances
        """
        # Discover plugins
        discovered_plugins = self.discover_plugins()
        
        # Load each plugin
        for plugin_info in discovered_plugins:
            plugin_path = plugin_info['path']
            plugin = self.load_plugin(plugin_path)
            
            if plugin:
                self.plugins[plugin.id] = plugin
                self.plugin_dependencies[plugin.id] = plugin.dependencies
                
                # Update dependents
                for dep_id in plugin.dependencies:
                    if dep_id not in self.plugin_dependents:
                        self.plugin_dependents[dep_id] = []
                    self.plugin_dependents[dep_id].append(plugin.id)
        
        return self.plugins
    
    def initialize_plugins(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """Initialize all loaded plugins.
        
        Args:
            context: Plugin initialization context
            
        Returns:
            Dictionary mapping plugin IDs to initialization success
        """
        self.plugin_context = context
        initialization_results = {}
        
        # Initialize plugins in dependency order
        for plugin_id in self._get_initialization_order():
            if plugin_id in self.disabled_plugins:
                initialization_results[plugin_id] = False
                continue
            
            plugin = self.plugins.get(plugin_id)
            if not plugin:
                initialization_results[plugin_id] = False
                continue
            
            try:
                success = plugin.initialize(context)
                initialization_results[plugin_id] = success
                
                if not success:
                    logger.warning(f"Plugin {plugin_id} initialization failed")
                    self.plugin_errors[plugin_id] = "Initialization failed"
                    self.disabled_plugins.add(plugin_id)
            except Exception as e:
                logger.error(f"Error initializing plugin {plugin_id}: {e}")
                initialization_results[plugin_id] = False
                self.plugin_errors[plugin_id] = str(e)
                self.disabled_plugins.add(plugin_id)
        
        return initialization_results
    
    def shutdown_plugins(self) -> Dict[str, bool]:
        """Shutdown all loaded plugins.
        
        Returns:
            Dictionary mapping plugin IDs to shutdown success
        """
        shutdown_results = {}
        
        # Shutdown plugins in reverse dependency order
        for plugin_id in reversed(self._get_initialization_order()):
            if plugin_id in self.disabled_plugins:
                shutdown_results[plugin_id] = False
                continue
            
            plugin = self.plugins.get(plugin_id)
            if not plugin:
                shutdown_results[plugin_id] = False
                continue
            
            try:
                success = plugin.shutdown()
                shutdown_results[plugin_id] = success
                
                if not success:
                    logger.warning(f"Plugin {plugin_id} shutdown failed")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_id}: {e}")
                shutdown_results[plugin_id] = False
        
        return shutdown_results
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_id)
    
    def get_plugins_by_capability(self, capability: str) -> List[Plugin]:
        """Get plugins that provide a specific capability.
        
        Args:
            capability: Capability string
            
        Returns:
            List of plugin instances
        """
        return [
            plugin for plugin in self.plugins.values()
            if plugin.id not in self.disabled_plugins and capability in plugin.get_capabilities()
        ]
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a disabled plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if the plugin was enabled, False otherwise
        """
        if plugin_id in self.disabled_plugins:
            self.disabled_plugins.remove(plugin_id)
            
            # Re-initialize the plugin
            plugin = self.plugins.get(plugin_id)
            if plugin:
                try:
                    success = plugin.initialize(self.plugin_context)
                    if not success:
                        self.disabled_plugins.add(plugin_id)
                        return False
                    return True
                except Exception as e:
                    logger.error(f"Error re-initializing plugin {plugin_id}: {e}")
                    self.disabled_plugins.add(plugin_id)
                    self.plugin_errors[plugin_id] = str(e)
                    return False
        
        return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if the plugin was disabled, False otherwise
        """
        if plugin_id not in self.disabled_plugins and plugin_id in self.plugins:
            # Check if any enabled plugins depend on this one
            dependents = [
                dep_id for dep_id in self.plugin_dependents.get(plugin_id, [])
                if dep_id not in self.disabled_plugins
            ]
            
            if dependents:
                logger.warning(
                    f"Cannot disable plugin {plugin_id} because it is required by: {', '.join(dependents)}"
                )
                return False
            
            # Shutdown the plugin
            plugin = self.plugins.get(plugin_id)
            if plugin:
                try:
                    plugin.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down plugin {plugin_id}: {e}")
            
            self.disabled_plugins.add(plugin_id)
            return True
        
        return False
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            True if the plugin was reloaded, False otherwise
        """
        if plugin_id not in self.plugins:
            return False
        
        # Get the plugin path
        plugin = self.plugins[plugin_id]
        module = self.plugin_modules.get(plugin_id)
        if not module:
            return False
        
        # Get the plugin path from the module
        module_path = module.__file__
        if not module_path:
            return False
        
        plugin_path = os.path.dirname(module_path)
        
        # Shutdown the plugin
        try:
            plugin.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down plugin {plugin_id}: {e}")
        
        # Remove the plugin
        del self.plugins[plugin_id]
        del self.plugin_modules[plugin_id]
        
        if plugin_id in self.disabled_plugins:
            self.disabled_plugins.remove(plugin_id)
        
        if plugin_id in self.plugin_errors:
            del self.plugin_errors[plugin_id]
        
        # Reload the plugin
        new_plugin = self.load_plugin(plugin_path)
        if not new_plugin:
            return False
        
        self.plugins[plugin_id] = new_plugin
        self.plugin_dependencies[plugin_id] = new_plugin.dependencies
        
        # Update dependents
        for dep_id in new_plugin.dependencies:
            if dep_id not in self.plugin_dependents:
                self.plugin_dependents[dep_id] = []
            if plugin_id not in self.plugin_dependents[dep_id]:
                self.plugin_dependents[dep_id].append(plugin_id)
        
        # Initialize the plugin
        try:
            success = new_plugin.initialize(self.plugin_context)
            if not success:
                logger.warning(f"Plugin {plugin_id} initialization failed after reload")
                self.plugin_errors[plugin_id] = "Initialization failed"
                self.disabled_plugins.add(plugin_id)
                return False
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_id} after reload: {e}")
            self.plugin_errors[plugin_id] = str(e)
            self.disabled_plugins.add(plugin_id)
            return False
        
        return True
    
    def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """Get information about a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Dictionary with plugin information
        """
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return {}
        
        return {
            'id': plugin.id,
            'name': plugin.name,
            'version': plugin.version,
            'description': plugin.description,
            'author': plugin.author,
            'dependencies': plugin.dependencies,
            'capabilities': plugin.get_capabilities(),
            'settings_schema': plugin.settings_schema,
            'settings': plugin.get_settings(),
            'enabled': plugin_id not in self.disabled_plugins,
            'error': self.plugin_errors.get(plugin_id, None),
            'dependents': self.plugin_dependents.get(plugin_id, [])
        }
    
    def get_all_plugin_info(self) -> List[Dict[str, Any]]:
        """Get information about all plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        return [self.get_plugin_info(plugin_id) for plugin_id in self.plugins]
    
    def broadcast_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast an event to all enabled plugins.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Dictionary mapping plugin IDs to their responses
        """
        responses = {}
        
        for plugin_id, plugin in self.plugins.items():
            if plugin_id in self.disabled_plugins:
                continue
            
            try:
                response = plugin.handle_event(event_type, event_data)
                if response is not None:
                    responses[plugin_id] = response
            except Exception as e:
                logger.error(f"Error handling event {event_type} in plugin {plugin_id}: {e}")
        
        return responses
    
    def _get_initialization_order(self) -> List[str]:
        """Get the order in which plugins should be initialized.
        
        Returns:
            List of plugin IDs in initialization order
        """
        # Build dependency graph
        graph = {}
        for plugin_id, deps in self.plugin_dependencies.items():
            graph[plugin_id] = deps
        
        # Topological sort
        visited = set()
        temp = set()
        order = []
        
        def visit(node):
            if node in temp:
                raise ValueError(f"Circular dependency detected: {node}")
            if node in visited:
                return
            
            temp.add(node)
            
            for dep in graph.get(node, []):
                if dep in self.plugins:  # Only visit dependencies that are loaded
                    visit(dep)
            
            temp.remove(node)
            visited.add(node)
            order.append(node)
        
        for plugin_id in self.plugins:
            if plugin_id not in visited:
                visit(plugin_id)
        
        return order
