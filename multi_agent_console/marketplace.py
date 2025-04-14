"""
Agent Marketplace and Extensibility for MultiAgentConsole.

This module provides marketplace and extensibility capabilities:
- Agent marketplace
- Plugin system
- Custom agent creation
- Extension management
"""

import os
import json
import logging
import time
import hashlib
import zipfile
import shutil
import importlib.util
import inspect
from typing import Dict, List, Optional, Any, Callable, Type
from pathlib import Path
import requests
from datetime import datetime


class AgentDefinition:
    """Defines an agent with its capabilities and metadata."""
    
    def __init__(self, name: str, description: str, system_prompt: str, 
                tools: List[str] = None, author: str = None, version: str = "1.0.0",
                tags: List[str] = None, requirements: List[str] = None):
        """Initialize an agent definition.
        
        Args:
            name: Agent name
            description: Agent description
            system_prompt: System prompt for the agent
            tools: List of tool names the agent can use
            author: Agent author
            version: Agent version
            tags: List of tags for categorization
            requirements: List of required packages
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.author = author or "Unknown"
        self.version = version
        self.tags = tags or []
        self.requirements = requirements or []
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent definition to a dictionary.
        
        Returns:
            Dictionary representation of the agent definition
        """
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "requirements": self.requirements,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentDefinition':
        """Create an agent definition from a dictionary.
        
        Args:
            data: Dictionary representation of the agent definition
            
        Returns:
            AgentDefinition instance
        """
        agent = cls(
            name=data["name"],
            description=data["description"],
            system_prompt=data["system_prompt"],
            tools=data.get("tools", []),
            author=data.get("author", "Unknown"),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            requirements=data.get("requirements", [])
        )
        
        if "created_at" in data:
            agent.created_at = data["created_at"]
        
        return agent


class PluginDefinition:
    """Defines a plugin with its capabilities and metadata."""
    
    def __init__(self, name: str, description: str, entry_point: str,
                author: str = None, version: str = "1.0.0", tags: List[str] = None,
                requirements: List[str] = None, tools: List[Dict[str, Any]] = None):
        """Initialize a plugin definition.
        
        Args:
            name: Plugin name
            description: Plugin description
            entry_point: Entry point module
            author: Plugin author
            version: Plugin version
            tags: List of tags for categorization
            requirements: List of required packages
            tools: List of tools provided by the plugin
        """
        self.name = name
        self.description = description
        self.entry_point = entry_point
        self.author = author or "Unknown"
        self.version = version
        self.tags = tags or []
        self.requirements = requirements or []
        self.tools = tools or []
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the plugin definition to a dictionary.
        
        Returns:
            Dictionary representation of the plugin definition
        """
        return {
            "name": self.name,
            "description": self.description,
            "entry_point": self.entry_point,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "requirements": self.requirements,
            "tools": self.tools,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginDefinition':
        """Create a plugin definition from a dictionary.
        
        Args:
            data: Dictionary representation of the plugin definition
            
        Returns:
            PluginDefinition instance
        """
        plugin = cls(
            name=data["name"],
            description=data["description"],
            entry_point=data["entry_point"],
            author=data.get("author", "Unknown"),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            requirements=data.get("requirements", []),
            tools=data.get("tools", [])
        )
        
        if "created_at" in data:
            plugin.created_at = data["created_at"]
        
        return plugin


class AgentMarketplace:
    """Manages agent marketplace functionality."""
    
    def __init__(self, data_dir: str = "data/marketplace/agents"):
        """Initialize the agent marketplace.
        
        Args:
            data_dir: Directory for storing agent definitions
        """
        self.data_dir = data_dir
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load available agents
        self.agents = self._load_agents()
        
        logging.info(f"Agent Marketplace initialized with {len(self.agents)} agents")
    
    def _load_agents(self) -> Dict[str, AgentDefinition]:
        """Load agent definitions from the data directory.
        
        Returns:
            Dictionary of agent definitions
        """
        agents = {}
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.data_dir, filename), 'r') as f:
                        agent_data = json.load(f)
                    
                    agent = AgentDefinition.from_dict(agent_data)
                    agents[agent.name] = agent
                except Exception as e:
                    logging.error(f"Error loading agent definition from {filename}: {e}")
        
        return agents
    
    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """Get an agent definition by name.
        
        Args:
            name: Agent name
            
        Returns:
            AgentDefinition instance or None if not found
        """
        return self.agents.get(name)
    
    def list_agents(self, tag: Optional[str] = None) -> List[AgentDefinition]:
        """List available agents.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of agent definitions
        """
        if tag:
            return [agent for agent in self.agents.values() if tag in agent.tags]
        return list(self.agents.values())
    
    def add_agent(self, agent: AgentDefinition) -> bool:
        """Add an agent definition.
        
        Args:
            agent: AgentDefinition instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save the agent definition
            file_path = os.path.join(self.data_dir, f"{agent.name}.json")
            with open(file_path, 'w') as f:
                json.dump(agent.to_dict(), f, indent=2)
            
            # Add to in-memory cache
            self.agents[agent.name] = agent
            
            logging.info(f"Added agent definition: {agent.name}")
            return True
        except Exception as e:
            logging.error(f"Error adding agent definition: {e}")
            return False
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent definition.
        
        Args:
            name: Agent name
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.agents:
            return False
        
        try:
            # Remove the agent definition file
            file_path = os.path.join(self.data_dir, f"{name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove from in-memory cache
            del self.agents[name]
            
            logging.info(f"Removed agent definition: {name}")
            return True
        except Exception as e:
            logging.error(f"Error removing agent definition: {e}")
            return False
    
    def search_agents(self, query: str) -> List[AgentDefinition]:
        """Search for agents.
        
        Args:
            query: Search query
            
        Returns:
            List of matching agent definitions
        """
        query = query.lower()
        results = []
        
        for agent in self.agents.values():
            # Check name, description, and tags
            if (query in agent.name.lower() or
                query in agent.description.lower() or
                any(query in tag.lower() for tag in agent.tags)):
                results.append(agent)
        
        return results
    
    def import_agent_from_url(self, url: str) -> Optional[AgentDefinition]:
        """Import an agent definition from a URL.
        
        Args:
            url: URL to the agent definition JSON
            
        Returns:
            AgentDefinition instance or None if import failed
        """
        try:
            # Download the agent definition
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the agent definition
            agent_data = response.json()
            agent = AgentDefinition.from_dict(agent_data)
            
            # Save the agent definition
            self.add_agent(agent)
            
            return agent
        except Exception as e:
            logging.error(f"Error importing agent from URL {url}: {e}")
            return None


class PluginManager:
    """Manages plugins for extending functionality."""
    
    def __init__(self, data_dir: str = "data/marketplace/plugins"):
        """Initialize the plugin manager.
        
        Args:
            data_dir: Directory for storing plugins
        """
        self.data_dir = data_dir
        self.plugins_dir = os.path.join(data_dir, "installed")
        self.definitions_dir = os.path.join(data_dir, "definitions")
        
        # Create directories if they don't exist
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs(self.definitions_dir, exist_ok=True)
        
        # Load available plugins
        self.plugins = self._load_plugins()
        
        # Dictionary to store loaded plugin modules
        self.loaded_modules = {}
        
        logging.info(f"Plugin Manager initialized with {len(self.plugins)} plugins")
    
    def _load_plugins(self) -> Dict[str, PluginDefinition]:
        """Load plugin definitions from the data directory.
        
        Returns:
            Dictionary of plugin definitions
        """
        plugins = {}
        
        for filename in os.listdir(self.definitions_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.definitions_dir, filename), 'r') as f:
                        plugin_data = json.load(f)
                    
                    plugin = PluginDefinition.from_dict(plugin_data)
                    plugins[plugin.name] = plugin
                except Exception as e:
                    logging.error(f"Error loading plugin definition from {filename}: {e}")
        
        return plugins
    
    def get_plugin(self, name: str) -> Optional[PluginDefinition]:
        """Get a plugin definition by name.
        
        Args:
            name: Plugin name
            
        Returns:
            PluginDefinition instance or None if not found
        """
        return self.plugins.get(name)
    
    def list_plugins(self, tag: Optional[str] = None) -> List[PluginDefinition]:
        """List available plugins.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of plugin definitions
        """
        if tag:
            return [plugin for plugin in self.plugins.values() if tag in plugin.tags]
        return list(self.plugins.values())
    
    def install_plugin(self, plugin_zip_path: str) -> Optional[PluginDefinition]:
        """Install a plugin from a ZIP file.
        
        Args:
            plugin_zip_path: Path to the plugin ZIP file
            
        Returns:
            PluginDefinition instance or None if installation failed
        """
        try:
            # Extract the plugin ZIP file
            with zipfile.ZipFile(plugin_zip_path, 'r') as zip_ref:
                # Check if the ZIP contains a plugin.json file
                if "plugin.json" not in zip_ref.namelist():
                    logging.error(f"Invalid plugin ZIP: missing plugin.json")
                    return None
                
                # Read the plugin definition
                with zip_ref.open("plugin.json") as f:
                    plugin_data = json.loads(f.read().decode('utf-8'))
                
                plugin = PluginDefinition.from_dict(plugin_data)
                
                # Create a directory for the plugin
                plugin_dir = os.path.join(self.plugins_dir, plugin.name)
                os.makedirs(plugin_dir, exist_ok=True)
                
                # Extract the plugin files
                zip_ref.extractall(plugin_dir)
            
            # Save the plugin definition
            self._save_plugin_definition(plugin)
            
            # Add to in-memory cache
            self.plugins[plugin.name] = plugin
            
            logging.info(f"Installed plugin: {plugin.name}")
            return plugin
        except Exception as e:
            logging.error(f"Error installing plugin: {e}")
            return None
    
    def _save_plugin_definition(self, plugin: PluginDefinition) -> None:
        """Save a plugin definition.
        
        Args:
            plugin: PluginDefinition instance
        """
        file_path = os.path.join(self.definitions_dir, f"{plugin.name}.json")
        with open(file_path, 'w') as f:
            json.dump(plugin.to_dict(), f, indent=2)
    
    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.plugins:
            return False
        
        try:
            # Remove the plugin directory
            plugin_dir = os.path.join(self.plugins_dir, name)
            if os.path.exists(plugin_dir):
                shutil.rmtree(plugin_dir)
            
            # Remove the plugin definition file
            definition_file = os.path.join(self.definitions_dir, f"{name}.json")
            if os.path.exists(definition_file):
                os.remove(definition_file)
            
            # Remove from in-memory cache
            del self.plugins[name]
            
            # Unload the module if loaded
            if name in self.loaded_modules:
                del self.loaded_modules[name]
            
            logging.info(f"Uninstalled plugin: {name}")
            return True
        except Exception as e:
            logging.error(f"Error uninstalling plugin: {e}")
            return False
    
    def load_plugin(self, name: str) -> Any:
        """Load a plugin module.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin module or None if loading failed
        """
        if name not in self.plugins:
            logging.error(f"Plugin not found: {name}")
            return None
        
        if name in self.loaded_modules:
            return self.loaded_modules[name]
        
        try:
            plugin = self.plugins[name]
            plugin_dir = os.path.join(self.plugins_dir, name)
            
            # Get the entry point module path
            module_path = os.path.join(plugin_dir, plugin.entry_point)
            
            # Load the module
            spec = importlib.util.spec_from_file_location(name, module_path)
            if spec is None:
                logging.error(f"Could not find module: {module_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Store the loaded module
            self.loaded_modules[name] = module
            
            logging.info(f"Loaded plugin module: {name}")
            return module
        except Exception as e:
            logging.error(f"Error loading plugin module: {e}")
            return None
    
    def get_plugin_tools(self, name: str) -> List[Callable]:
        """Get the tools provided by a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            List of tool functions
        """
        module = self.load_plugin(name)
        if not module:
            return []
        
        tools = []
        
        # Look for functions with the 'tool' attribute
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and hasattr(attr, 'is_tool') and attr.is_tool:
                tools.append(attr)
        
        return tools
    
    def search_plugins(self, query: str) -> List[PluginDefinition]:
        """Search for plugins.
        
        Args:
            query: Search query
            
        Returns:
            List of matching plugin definitions
        """
        query = query.lower()
        results = []
        
        for plugin in self.plugins.values():
            # Check name, description, and tags
            if (query in plugin.name.lower() or
                query in plugin.description.lower() or
                any(query in tag.lower() for tag in plugin.tags)):
                results.append(plugin)
        
        return results
    
    def import_plugin_from_url(self, url: str) -> Optional[PluginDefinition]:
        """Import a plugin from a URL.
        
        Args:
            url: URL to the plugin ZIP file
            
        Returns:
            PluginDefinition instance or None if import failed
        """
        try:
            # Download the plugin ZIP file
            response = requests.get(url)
            response.raise_for_status()
            
            # Save the ZIP file temporarily
            temp_zip_path = os.path.join(self.data_dir, "temp_plugin.zip")
            with open(temp_zip_path, 'wb') as f:
                f.write(response.content)
            
            # Install the plugin
            plugin = self.install_plugin(temp_zip_path)
            
            # Remove the temporary ZIP file
            os.remove(temp_zip_path)
            
            return plugin
        except Exception as e:
            logging.error(f"Error importing plugin from URL {url}: {e}")
            return None


class ExtensionRegistry:
    """Registry for custom extensions."""
    
    def __init__(self, data_dir: str = "data/marketplace/extensions"):
        """Initialize the extension registry.
        
        Args:
            data_dir: Directory for storing extension data
        """
        self.data_dir = data_dir
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Dictionary to store registered extensions
        self.extensions = {}
        
        logging.info("Extension Registry initialized")
    
    def register_extension(self, name: str, extension_class: Type) -> bool:
        """Register an extension.
        
        Args:
            name: Extension name
            extension_class: Extension class
            
        Returns:
            True if successful, False otherwise
        """
        if name in self.extensions:
            logging.warning(f"Extension already registered: {name}")
            return False
        
        self.extensions[name] = extension_class
        logging.info(f"Registered extension: {name}")
        return True
    
    def unregister_extension(self, name: str) -> bool:
        """Unregister an extension.
        
        Args:
            name: Extension name
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.extensions:
            return False
        
        del self.extensions[name]
        logging.info(f"Unregistered extension: {name}")
        return True
    
    def get_extension(self, name: str) -> Optional[Type]:
        """Get an extension class by name.
        
        Args:
            name: Extension name
            
        Returns:
            Extension class or None if not found
        """
        return self.extensions.get(name)
    
    def list_extensions(self) -> List[str]:
        """List registered extensions.
        
        Returns:
            List of extension names
        """
        return list(self.extensions.keys())


class MarketplaceManager:
    """Manages the agent marketplace and extensibility features."""
    
    def __init__(self, data_dir: str = "data/marketplace"):
        """Initialize the marketplace manager.
        
        Args:
            data_dir: Directory for storing marketplace data
        """
        self.data_dir = data_dir
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize components
        self.agent_marketplace = AgentMarketplace(os.path.join(data_dir, "agents"))
        self.plugin_manager = PluginManager(os.path.join(data_dir, "plugins"))
        self.extension_registry = ExtensionRegistry(os.path.join(data_dir, "extensions"))
        
        logging.info("Marketplace Manager initialized")
    
    def create_agent_definition(self, name: str, description: str, system_prompt: str,
                              tools: List[str] = None, author: str = None,
                              version: str = "1.0.0", tags: List[str] = None,
                              requirements: List[str] = None) -> AgentDefinition:
        """Create a new agent definition.
        
        Args:
            name: Agent name
            description: Agent description
            system_prompt: System prompt for the agent
            tools: List of tool names the agent can use
            author: Agent author
            version: Agent version
            tags: List of tags for categorization
            requirements: List of required packages
            
        Returns:
            AgentDefinition instance
        """
        agent = AgentDefinition(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tools=tools,
            author=author,
            version=version,
            tags=tags,
            requirements=requirements
        )
        
        # Add the agent to the marketplace
        self.agent_marketplace.add_agent(agent)
        
        return agent
    
    def get_agent_definition(self, name: str) -> Optional[AgentDefinition]:
        """Get an agent definition by name.
        
        Args:
            name: Agent name
            
        Returns:
            AgentDefinition instance or None if not found
        """
        return self.agent_marketplace.get_agent(name)
    
    def list_agent_definitions(self, tag: Optional[str] = None) -> List[AgentDefinition]:
        """List available agent definitions.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of agent definitions
        """
        return self.agent_marketplace.list_agents(tag)
    
    def search_agent_definitions(self, query: str) -> List[AgentDefinition]:
        """Search for agent definitions.
        
        Args:
            query: Search query
            
        Returns:
            List of matching agent definitions
        """
        return self.agent_marketplace.search_agents(query)
    
    def install_plugin(self, plugin_zip_path: str) -> Optional[PluginDefinition]:
        """Install a plugin.
        
        Args:
            plugin_zip_path: Path to the plugin ZIP file
            
        Returns:
            PluginDefinition instance or None if installation failed
        """
        return self.plugin_manager.install_plugin(plugin_zip_path)
    
    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if successful, False otherwise
        """
        return self.plugin_manager.uninstall_plugin(name)
    
    def list_plugins(self, tag: Optional[str] = None) -> List[PluginDefinition]:
        """List installed plugins.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of plugin definitions
        """
        return self.plugin_manager.list_plugins(tag)
    
    def search_plugins(self, query: str) -> List[PluginDefinition]:
        """Search for plugins.
        
        Args:
            query: Search query
            
        Returns:
            List of matching plugin definitions
        """
        return self.plugin_manager.search_plugins(query)
    
    def get_plugin_tools(self, name: str) -> List[Callable]:
        """Get the tools provided by a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            List of tool functions
        """
        return self.plugin_manager.get_plugin_tools(name)
    
    def register_extension(self, name: str, extension_class: Type) -> bool:
        """Register an extension.
        
        Args:
            name: Extension name
            extension_class: Extension class
            
        Returns:
            True if successful, False otherwise
        """
        return self.extension_registry.register_extension(name, extension_class)
    
    def unregister_extension(self, name: str) -> bool:
        """Unregister an extension.
        
        Args:
            name: Extension name
            
        Returns:
            True if successful, False otherwise
        """
        return self.extension_registry.unregister_extension(name)
    
    def list_extensions(self) -> List[str]:
        """List registered extensions.
        
        Returns:
            List of extension names
        """
        return self.extension_registry.list_extensions()
    
    def import_agent_from_url(self, url: str) -> Optional[AgentDefinition]:
        """Import an agent definition from a URL.
        
        Args:
            url: URL to the agent definition JSON
            
        Returns:
            AgentDefinition instance or None if import failed
        """
        return self.agent_marketplace.import_agent_from_url(url)
    
    def import_plugin_from_url(self, url: str) -> Optional[PluginDefinition]:
        """Import a plugin from a URL.
        
        Args:
            url: URL to the plugin ZIP file
            
        Returns:
            PluginDefinition instance or None if import failed
        """
        return self.plugin_manager.import_plugin_from_url(url)
