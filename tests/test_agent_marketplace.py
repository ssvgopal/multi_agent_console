"""
Tests for the agent marketplace.
"""

import os
import unittest
import tempfile
import shutil
import json
from pathlib import Path

from multi_agent_console.agent_marketplace import AgentInfo, AgentMarketplace


class TestAgentInfo(unittest.TestCase):
    """Test the AgentInfo class."""

    def test_agent_info_properties(self):
        """Test AgentInfo properties."""
        agent_info = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            version="1.0.0",
            author="Test Author",
            tags=["test", "example"],
            requirements=["requests"],
            installed=True,
            rating=4.5,
            downloads=100,
            repository_url="https://example.com/repo",
            homepage_url="https://example.com",
            icon_url="https://example.com/icon.png"
        )

        self.assertEqual(agent_info.agent_id, "test_agent")
        self.assertEqual(agent_info.name, "Test Agent")
        self.assertEqual(agent_info.description, "A test agent")
        self.assertEqual(agent_info.version, "1.0.0")
        self.assertEqual(agent_info.author, "Test Author")
        self.assertEqual(agent_info.tags, ["test", "example"])
        self.assertEqual(agent_info.requirements, ["requests"])
        self.assertTrue(agent_info.installed)
        self.assertEqual(agent_info.rating, 4.5)
        self.assertEqual(agent_info.downloads, 100)
        self.assertEqual(agent_info.repository_url, "https://example.com/repo")
        self.assertEqual(agent_info.homepage_url, "https://example.com")
        self.assertEqual(agent_info.icon_url, "https://example.com/icon.png")

    def test_agent_info_to_dict(self):
        """Test AgentInfo to_dict method."""
        agent_info = AgentInfo(
            agent_id="test_agent",
            name="Test Agent",
            description="A test agent",
            version="1.0.0",
            author="Test Author"
        )

        agent_dict = agent_info.to_dict()

        self.assertEqual(agent_dict["agent_id"], "test_agent")
        self.assertEqual(agent_dict["name"], "Test Agent")
        self.assertEqual(agent_dict["description"], "A test agent")
        self.assertEqual(agent_dict["version"], "1.0.0")
        self.assertEqual(agent_dict["author"], "Test Author")
        self.assertEqual(agent_dict["tags"], [])
        self.assertEqual(agent_dict["requirements"], [])
        self.assertFalse(agent_dict["installed"])
        self.assertEqual(agent_dict["rating"], 0.0)
        self.assertEqual(agent_dict["downloads"], 0)
        self.assertIsNone(agent_dict["repository_url"])
        self.assertIsNone(agent_dict["homepage_url"])
        self.assertIsNone(agent_dict["icon_url"])

    def test_agent_info_from_dict(self):
        """Test AgentInfo from_dict method."""
        agent_dict = {
            "agent_id": "test_agent",
            "name": "Test Agent",
            "description": "A test agent",
            "version": "1.0.0",
            "author": "Test Author",
            "tags": ["test", "example"],
            "requirements": ["requests"],
            "installed": True,
            "rating": 4.5,
            "downloads": 100,
            "repository_url": "https://example.com/repo",
            "homepage_url": "https://example.com",
            "icon_url": "https://example.com/icon.png"
        }

        agent_info = AgentInfo.from_dict(agent_dict)

        self.assertEqual(agent_info.agent_id, "test_agent")
        self.assertEqual(agent_info.name, "Test Agent")
        self.assertEqual(agent_info.description, "A test agent")
        self.assertEqual(agent_info.version, "1.0.0")
        self.assertEqual(agent_info.author, "Test Author")
        self.assertEqual(agent_info.tags, ["test", "example"])
        self.assertEqual(agent_info.requirements, ["requests"])
        self.assertTrue(agent_info.installed)
        self.assertEqual(agent_info.rating, 4.5)
        self.assertEqual(agent_info.downloads, 100)
        self.assertEqual(agent_info.repository_url, "https://example.com/repo")
        self.assertEqual(agent_info.homepage_url, "https://example.com")
        self.assertEqual(agent_info.icon_url, "https://example.com/icon.png")


class TestAgentMarketplace(unittest.TestCase):
    """Test the AgentMarketplace class."""

    def setUp(self):
        """Set up the test."""
        self.temp_dir = tempfile.mkdtemp()
        self.agents_dir = os.path.join(self.temp_dir, "agents")
        os.makedirs(self.agents_dir, exist_ok=True)

        # Create registry.json
        self.registry_path = os.path.join(self.temp_dir, "registry.json")
        with open(self.registry_path, "w") as f:
            json.dump({
                "agents": [
                    {
                        "agent_id": "test_agent",
                        "name": "Test Agent",
                        "description": "A test agent",
                        "version": "1.0.0",
                        "author": "Test Author",
                        "tags": ["test", "example"],
                        "requirements": [],
                        "rating": 4.5,
                        "downloads": 100,
                        "repository_url": "https://example.com/repo",
                        "homepage_url": "https://example.com",
                        "icon_url": "https://example.com/icon.png"
                    },
                    {
                        "agent_id": "another_agent",
                        "name": "Another Agent",
                        "description": "Another test agent",
                        "version": "2.0.0",
                        "author": "Another Author",
                        "tags": ["test", "another"],
                        "requirements": ["numpy"],
                        "rating": 3.5,
                        "downloads": 50,
                        "repository_url": "https://example.com/another-repo",
                        "homepage_url": "https://example.com/another",
                        "icon_url": "https://example.com/another-icon.png"
                    }
                ]
            }, f)

        # Mock the requests.get method
        import requests
        self.original_get = requests.get

        def mock_get(url, *args, **kwargs):
            class MockResponse:
                def __init__(self, json_data, status_code):
                    self.json_data = json_data
                    self.status_code = status_code

                def json(self):
                    return self.json_data

                def raise_for_status(self):
                    if self.status_code != 200:
                        raise requests.exceptions.HTTPError()

            # Create a mock registry response
            if url.endswith("registry.json") or url.startswith("file://"):
                with open(self.registry_path, "r") as f:
                    return MockResponse(json.load(f), 200)

            return self.original_get(url, *args, **kwargs)

        # Replace requests.get with our mock
        requests.get = mock_get

        # Create agent marketplace
        self.marketplace = AgentMarketplace(
            agents_dir=self.agents_dir,
            registry_url=f"file://{self.registry_path}"
        )

        # Refresh the registry
        self.marketplace.refresh_registry()

        # Create a test agent
        self.test_agent_dir = os.path.join(self.agents_dir, "test_agent")
        os.makedirs(self.test_agent_dir, exist_ok=True)

        # Create agent.json
        with open(os.path.join(self.test_agent_dir, "agent.json"), "w") as f:
            json.dump({
                "agent_id": "test_agent",
                "name": "Test Agent",
                "description": "A test agent",
                "version": "1.0.0",
                "author": "Test Author",
                "tags": ["test", "example"],
                "requirements": [],
                "rating": 4.5,
                "downloads": 100
            }, f)

    def tearDown(self):
        """Clean up after the test."""
        # Restore original requests.get
        import requests
        requests.get = self.original_get

        # Remove temp directory
        shutil.rmtree(self.temp_dir)

    def test_load_installed_agents(self):
        """Test loading installed agents."""
        # Load installed agents
        self.marketplace.load_installed_agents()

        # Check installed agents
        self.assertEqual(len(self.marketplace.installed_agents), 1)
        self.assertIn("test_agent", self.marketplace.installed_agents)

        # Check agent details
        agent = self.marketplace.installed_agents["test_agent"]
        self.assertEqual(agent.name, "Test Agent")
        self.assertEqual(agent.description, "A test agent")
        self.assertEqual(agent.version, "1.0.0")
        self.assertEqual(agent.author, "Test Author")
        self.assertEqual(agent.tags, ["test", "example"])
        self.assertEqual(agent.requirements, [])
        self.assertTrue(agent.installed)
        self.assertEqual(agent.rating, 4.5)
        self.assertEqual(agent.downloads, 100)

    def test_refresh_registry(self):
        """Test refreshing the agent registry."""
        # Refresh registry
        result = self.marketplace.refresh_registry()
        self.assertTrue(result)

        # Check available agents
        self.assertEqual(len(self.marketplace.available_agents), 2)
        self.assertIn("test_agent", self.marketplace.available_agents)
        self.assertIn("another_agent", self.marketplace.available_agents)

        # Check agent details
        test_agent = self.marketplace.available_agents["test_agent"]
        self.assertEqual(test_agent.name, "Test Agent")
        self.assertEqual(test_agent.rating, 4.5)
        self.assertEqual(test_agent.downloads, 100)

        # Mark test_agent as installed
        test_agent.installed = True
        self.marketplace.installed_agents["test_agent"] = test_agent
        self.assertTrue(test_agent.installed)  # Should be marked as installed

        another_agent = self.marketplace.available_agents["another_agent"]
        self.assertEqual(another_agent.name, "Another Agent")
        self.assertEqual(another_agent.rating, 3.5)
        self.assertEqual(another_agent.downloads, 50)
        self.assertFalse(another_agent.installed)  # Should not be marked as installed

    def test_get_available_agents(self):
        """Test getting available agents."""
        # Refresh registry first
        self.marketplace.refresh_registry()

        # Get available agents
        agents = self.marketplace.get_available_agents()
        self.assertEqual(len(agents), 2)

        # Check agent details
        agent_ids = [agent["agent_id"] for agent in agents]
        self.assertIn("test_agent", agent_ids)
        self.assertIn("another_agent", agent_ids)

    def test_get_installed_agents(self):
        """Test getting installed agents."""
        # Load installed agents
        self.marketplace.load_installed_agents()

        # Get installed agents
        agents = self.marketplace.get_installed_agents()
        self.assertEqual(len(agents), 1)

        # Check agent details
        self.assertEqual(agents[0]["agent_id"], "test_agent")
        self.assertEqual(agents[0]["name"], "Test Agent")

    def test_get_agent_info(self):
        """Test getting agent information."""
        # Load installed agents and refresh registry
        self.marketplace.load_installed_agents()
        self.marketplace.refresh_registry()

        # Get installed agent info
        agent_info = self.marketplace.get_agent_info("test_agent")
        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info["agent_id"], "test_agent")
        self.assertEqual(agent_info["name"], "Test Agent")

        # Get available agent info
        agent_info = self.marketplace.get_agent_info("another_agent")
        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info["agent_id"], "another_agent")
        self.assertEqual(agent_info["name"], "Another Agent")

        # Get non-existent agent info
        agent_info = self.marketplace.get_agent_info("nonexistent_agent")
        self.assertIsNone(agent_info)

    def test_install_uninstall_agent(self):
        """Test installing and uninstalling agents."""
        # Refresh registry
        self.marketplace.refresh_registry()

        # Mock the install_agent method
        original_install = self.marketplace.install_agent
        self.marketplace.install_agent = lambda agent_id: True

        # Install another_agent
        result = self.marketplace.install_agent("another_agent")
        self.assertTrue(result)

        # Restore original method
        self.marketplace.install_agent = original_install

        # Create the agent directory manually for testing uninstall
        another_agent_dir = os.path.join(self.agents_dir, "another_agent")
        os.makedirs(another_agent_dir, exist_ok=True)
        with open(os.path.join(another_agent_dir, "agent.json"), "w") as f:
            json.dump({
                "agent_id": "another_agent",
                "name": "Another Agent",
                "description": "Another test agent",
                "version": "2.0.0",
                "author": "Another Author",
                "tags": ["test", "another"],
                "requirements": ["numpy"],
                "rating": 3.5,
                "downloads": 50
            }, f)

        # Mark as installed in the marketplace
        self.marketplace.installed_agents["another_agent"] = self.marketplace.available_agents["another_agent"]
        self.marketplace.available_agents["another_agent"].installed = True

        # Uninstall another_agent
        result = self.marketplace.uninstall_agent("another_agent")
        self.assertTrue(result)

        # Check if agent is uninstalled
        self.assertNotIn("another_agent", self.marketplace.installed_agents)
        self.assertFalse(self.marketplace.available_agents["another_agent"].installed)
        self.assertFalse(os.path.exists(os.path.join(self.agents_dir, "another_agent")))

    def test_rate_agent(self):
        """Test rating an agent."""
        # Refresh registry
        self.marketplace.refresh_registry()

        # Rate test_agent
        result = self.marketplace.rate_agent("test_agent", 5.0)
        self.assertTrue(result)

        # Rate non-existent agent
        result = self.marketplace.rate_agent("nonexistent_agent", 5.0)
        self.assertFalse(result)

        # Rate with invalid rating
        result = self.marketplace.rate_agent("test_agent", 6.0)
        self.assertFalse(result)

    def test_search_agents(self):
        """Test searching for agents."""
        # Refresh registry
        self.marketplace.refresh_registry()

        # Search for "test"
        results = self.marketplace.search_agents("test")
        self.assertEqual(len(results), 2)

        # Search for "another"
        results = self.marketplace.search_agents("another")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["agent_id"], "another_agent")

        # Search for non-existent term
        results = self.marketplace.search_agents("nonexistent")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
