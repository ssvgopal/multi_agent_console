"""
Agent Marketplace for MultiAgentConsole.

This module provides functionality for discovering, installing, and managing agents.
"""

import os
import json
import logging
import requests
import shutil
import zipfile
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path


class AgentInfo:
    """Information about an agent."""

    def __init__(
        self,
        agent_id: str,
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
        """Initialize agent information.

        Args:
            agent_id: Unique identifier for the agent
            name: Display name of the agent
            description: Description of the agent
            version: Version string
            author: Author name
            tags: List of tags
            requirements: List of package requirements
            installed: Whether the agent is installed
            rating: Average rating (0-5)
            downloads: Number of downloads
            repository_url: URL to the agent's repository
            homepage_url: URL to the agent's homepage
            icon_url: URL to the agent's icon
        """
        self.agent_id = agent_id
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
            "agent_id": self.agent_id,
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
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentInfo':
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            AgentInfo instance
        """
        return cls(
            agent_id=data["agent_id"],
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


class AgentMarketplace:
    """Agent marketplace for discovering and installing agents."""

    def __init__(self, agents_dir: str = "agents", registry_url: str = None):
        """Initialize the agent marketplace.

        Args:
            agents_dir: Directory for storing agents
            registry_url: URL to the agent registry
        """
        self.agents_dir = agents_dir
        self.registry_url = registry_url or "https://raw.githubusercontent.com/ssvgopal/multi_agent_console/main/registry/agents.json"
        self.installed_agents: Dict[str, AgentInfo] = {}
        self.available_agents: Dict[str, AgentInfo] = {}

        # Create agents directory if it doesn't exist
        os.makedirs(agents_dir, exist_ok=True)

        # Load installed agents
        self.load_installed_agents()

        logging.info(f"Agent Marketplace initialized with {len(self.installed_agents)} installed agents")

    def load_installed_agents(self) -> None:
        """Load installed agents from the agents directory."""
        self.installed_agents = {}

        for agent_dir in os.listdir(self.agents_dir):
            agent_path = os.path.join(self.agents_dir, agent_dir)
            if not os.path.isdir(agent_path):
                continue

            # Check for agent.json
            agent_json_path = os.path.join(agent_path, "agent.json")
            if not os.path.exists(agent_json_path):
                continue

            try:
                with open(agent_json_path, "r") as f:
                    agent_data = json.load(f)
                    agent_data["installed"] = True
                    agent_info = AgentInfo.from_dict(agent_data)
                    self.installed_agents[agent_info.agent_id] = agent_info
                    logging.info(f"Loaded installed agent: {agent_info.name} ({agent_info.agent_id})")
            except Exception as e:
                logging.error(f"Error loading agent from {agent_json_path}: {e}")

    def refresh_registry(self) -> bool:
        """Refresh the agent registry from the remote source.

        Returns:
            True if successful, False otherwise
        """
        self.available_agents = {}

        try:
            # Fetch registry from remote
            response = requests.get(self.registry_url)
            response.raise_for_status()
            registry_data = response.json()

            # Process registry data
            for agent_data in registry_data.get("agents", []):
                agent_info = AgentInfo.from_dict(agent_data)
                
                # Check if already installed
                if agent_info.agent_id in self.installed_agents:
                    agent_info.installed = True
                
                self.available_agents[agent_info.agent_id] = agent_info

            logging.info(f"Refreshed agent registry with {len(self.available_agents)} available agents")
            return True
        except Exception as e:
            logging.error(f"Error refreshing agent registry: {e}")
            return False

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents.

        Returns:
            List of agent dictionaries
        """
        return [agent.to_dict() for agent in self.available_agents.values()]

    def get_installed_agents(self) -> List[Dict[str, Any]]:
        """Get list of installed agents.

        Returns:
            List of agent dictionaries
        """
        return [agent.to_dict() for agent in self.installed_agents.values()]

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Agent information dictionary or None if not found
        """
        if agent_id in self.installed_agents:
            return self.installed_agents[agent_id].to_dict()
        elif agent_id in self.available_agents:
            return self.available_agents[agent_id].to_dict()
        return None

    def install_agent(self, agent_id: str) -> bool:
        """Install an agent.

        Args:
            agent_id: Agent ID

        Returns:
            True if successful, False otherwise
        """
        # Check if agent is available
        if agent_id not in self.available_agents:
            logging.error(f"Agent {agent_id} not found in registry")
            return False

        # Get agent info
        agent_info = self.available_agents[agent_id]

        # Check if already installed
        if agent_id in self.installed_agents:
            logging.warning(f"Agent {agent_id} is already installed")
            return True

        try:
            # Create agent directory
            agent_dir = os.path.join(self.agents_dir, agent_id)
            os.makedirs(agent_dir, exist_ok=True)

            # Download agent package
            if agent_info.repository_url:
                # Download from repository
                self._download_from_repository(agent_info, agent_dir)
            else:
                # Create basic structure
                self._create_basic_structure(agent_info, agent_dir)

            # Install requirements
            if agent_info.requirements:
                self._install_requirements(agent_info.requirements)

            # Mark as installed
            agent_info.installed = True
            self.installed_agents[agent_id] = agent_info

            logging.info(f"Installed agent: {agent_info.name} ({agent_id})")
            return True
        except Exception as e:
            logging.error(f"Error installing agent {agent_id}: {e}")
            # Clean up
            agent_dir = os.path.join(self.agents_dir, agent_id)
            if os.path.exists(agent_dir):
                shutil.rmtree(agent_dir)
            return False

    def uninstall_agent(self, agent_id: str) -> bool:
        """Uninstall an agent.

        Args:
            agent_id: Agent ID

        Returns:
            True if successful, False otherwise
        """
        # Check if agent is installed
        if agent_id not in self.installed_agents:
            logging.error(f"Agent {agent_id} is not installed")
            return False

        try:
            # Remove agent directory
            agent_dir = os.path.join(self.agents_dir, agent_id)
            if os.path.exists(agent_dir):
                shutil.rmtree(agent_dir)

            # Remove from installed agents
            if agent_id in self.installed_agents:
                del self.installed_agents[agent_id]

            # Update available agents
            if agent_id in self.available_agents:
                self.available_agents[agent_id].installed = False

            logging.info(f"Uninstalled agent: {agent_id}")
            return True
        except Exception as e:
            logging.error(f"Error uninstalling agent {agent_id}: {e}")
            return False

    def _download_from_repository(self, agent_info: AgentInfo, agent_dir: str) -> None:
        """Download agent from repository.

        Args:
            agent_info: Agent information
            agent_dir: Directory to install to
        """
        # Download from repository
        response = requests.get(agent_info.repository_url)
        response.raise_for_status()

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        try:
            # Extract to agent directory
            with zipfile.ZipFile(temp_path, "r") as zip_ref:
                zip_ref.extractall(agent_dir)

            # Create agent.json
            with open(os.path.join(agent_dir, "agent.json"), "w") as f:
                json.dump(agent_info.to_dict(), f, indent=2)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _create_basic_structure(self, agent_info: AgentInfo, agent_dir: str) -> None:
        """Create basic agent structure.

        Args:
            agent_info: Agent information
            agent_dir: Directory to install to
        """
        # Create agent.json
        with open(os.path.join(agent_dir, "agent.json"), "w") as f:
            json.dump(agent_info.to_dict(), f, indent=2)

        # Create __init__.py
        with open(os.path.join(agent_dir, "__init__.py"), "w") as f:
            f.write(f'"""\n{agent_info.name} - {agent_info.description}\n\nAuthor: {agent_info.author}\nVersion: {agent_info.version}\n"""\n\n')

        # Create agent.py
        with open(os.path.join(agent_dir, "agent.py"), "w") as f:
            f.write(f'''"""
{agent_info.name} - {agent_info.description}

Author: {agent_info.author}
Version: {agent_info.version}
"""

class Agent:
    """Agent implementation."""

    def __init__(self):
        """Initialize the agent."""
        self.name = "{agent_info.name}"
        self.description = "{agent_info.description}"
        self.version = "{agent_info.version}"
        self.author = "{agent_info.author}"

    def process_message(self, message, context=None):
        """Process a message.

        Args:
            message: User message
            context: Message context

        Returns:
            Response message
        """
        # TODO: Implement agent logic
        return f"Hello! I am {self.name}. You said: {{message}}"
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
            logging.error(f"Error installing requirements: {e}")
            raise

    def rate_agent(self, agent_id: str, rating: float) -> bool:
        """Rate an agent.

        Args:
            agent_id: Agent ID
            rating: Rating (0-5)

        Returns:
            True if successful, False otherwise
        """
        # Validate rating
        if rating < 0 or rating > 5:
            logging.error(f"Invalid rating: {rating} (must be between 0 and 5)")
            return False

        # Check if agent exists
        if agent_id not in self.installed_agents and agent_id not in self.available_agents:
            logging.error(f"Agent {agent_id} not found")
            return False

        # TODO: Submit rating to registry
        logging.info(f"Rated agent {agent_id}: {rating}")
        return True

    def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """Search for agents.

        Args:
            query: Search query

        Returns:
            List of matching agent dictionaries
        """
        query = query.lower()
        results = []

        for agent in self.available_agents.values():
            # Search in name, description, tags, and author
            if (query in agent.name.lower() or
                query in agent.description.lower() or
                query in agent.author.lower() or
                any(query in tag.lower() for tag in agent.tags)):
                results.append(agent.to_dict())

        return results
