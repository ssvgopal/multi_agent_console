"""
Tests for the plugin system.
"""

import os
import unittest
import tempfile
import shutil
import json
from pathlib import Path

from multi_agent_console.plugin.base import Plugin, PluginManager
from multi_agent_console.plugin.registry import PluginInfo, PluginRegistry


class TestPlugin(Plugin):
    """Test plugin implementation."""

    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return "test_plugin"

    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "Test Plugin"

    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "A test plugin for unit tests"

    @property
    def author(self) -> str:
        """Get the plugin author."""
        return "Test Author"

    def initialize(self, context):
        """Initialize the plugin."""
        self.initialized = True
        self.context = context
        return True

    def shutdown(self):
        """Shutdown the plugin."""
        self.initialized = False
        return True

    def get_capabilities(self):
        """Get the plugin capabilities."""
        return ["test_capability"]

    def handle_event(self, event_type, event_data):
        """Handle an event."""
        if event_type == "test_capability":
            return {"result": "success", "data": event_data}
        return None


class DependentPlugin(Plugin):
    """Plugin that depends on TestPlugin."""

    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return "dependent_plugin"

    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "Dependent Plugin"

    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "A plugin that depends on TestPlugin"

    @property
    def dependencies(self) -> list:
        """Get the plugin dependencies."""
        return ["test_plugin"]

    def initialize(self, context):
        """Initialize the plugin."""
        self.initialized = True
        return True

    def shutdown(self):
        """Shutdown the plugin."""
        self.initialized = False
        return True


class TestPluginBase(unittest.TestCase):
    """Test the Plugin base class."""

    def setUp(self):
        """Set up the test."""
        self.plugin = TestPlugin()

    def test_plugin_properties(self):
        """Test plugin properties."""
        self.assertEqual(self.plugin.id, "test_plugin")
        self.assertEqual(self.plugin.name, "Test Plugin")
        self.assertEqual(self.plugin.version, "1.0.0")
        self.assertEqual(self.plugin.description, "A test plugin for unit tests")
        self.assertEqual(self.plugin.author, "Test Author")

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        context = {"test": "value"}
        result = self.plugin.initialize(context)
        self.assertTrue(result)
        self.assertTrue(hasattr(self.plugin, "initialized"))
        self.assertTrue(self.plugin.initialized)
        self.assertEqual(self.plugin.context, context)

    def test_plugin_shutdown(self):
        """Test plugin shutdown."""
        self.plugin.initialize({})
        result = self.plugin.shutdown()
        self.assertTrue(result)
        self.assertFalse(self.plugin.initialized)

    def test_plugin_capabilities(self):
        """Test plugin capabilities."""
        capabilities = self.plugin.get_capabilities()
        self.assertIsInstance(capabilities, list)
        self.assertIn("test_capability", capabilities)

    def test_plugin_handle_event(self):
        """Test plugin event handling."""
        event_data = {"param": "value"}
        result = self.plugin.handle_event("test_capability", event_data)
        self.assertIsNotNone(result)
        self.assertEqual(result["result"], "success")
        self.assertEqual(result["data"], event_data)

        # Test unknown event type
        result = self.plugin.handle_event("unknown", {})
        self.assertIsNone(result)


class TestPluginManager(unittest.TestCase):
    """Test the PluginManager class."""

    def setUp(self):
        """Set up the test."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = os.path.join(self.temp_dir, "plugins")
        os.makedirs(self.plugin_dir, exist_ok=True)

        # Create test plugin directory
        self.test_plugin_dir = os.path.join(self.plugin_dir, "test_plugin")
        os.makedirs(self.test_plugin_dir, exist_ok=True)

        # Create plugin.json
        with open(os.path.join(self.test_plugin_dir, "plugin.json"), "w") as f:
            json.dump({
                "id": "test_plugin",
                "name": "Test Plugin",
                "description": "A test plugin for unit tests",
                "version": "1.0.0",
                "author": "Test Author"
            }, f)

        # Create __init__.py
        with open(os.path.join(self.test_plugin_dir, "__init__.py"), "w") as f:
            f.write('"""Test plugin."""\n')

        # Create plugin.py
        with open(os.path.join(self.test_plugin_dir, "plugin.py"), "w") as f:
            f.write('''"""Test plugin implementation."""

from multi_agent_console.plugin.base import Plugin

class TestPlugin(Plugin):
    """Test plugin implementation."""

    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return "test_plugin"

    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "Test Plugin"

    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "A test plugin for unit tests"

    @property
    def author(self) -> str:
        """Get the plugin author."""
        return "Test Author"

    def initialize(self, context):
        """Initialize the plugin."""
        self.initialized = True
        self.context = context
        return True

    def shutdown(self):
        """Shutdown the plugin."""
        self.initialized = False
        return True

    def get_capabilities(self):
        """Get the plugin capabilities."""
        return ["test_capability"]

    def handle_event(self, event_type, event_data):
        """Handle an event."""
        if event_type == "test_capability":
            return {"result": "success", "data": event_data}
        return None
''')

        # Create dependent plugin directory
        self.dependent_plugin_dir = os.path.join(self.plugin_dir, "dependent_plugin")
        os.makedirs(self.dependent_plugin_dir, exist_ok=True)

        # Create plugin.json
        with open(os.path.join(self.dependent_plugin_dir, "plugin.json"), "w") as f:
            json.dump({
                "id": "dependent_plugin",
                "name": "Dependent Plugin",
                "description": "A plugin that depends on TestPlugin",
                "version": "1.0.0",
                "author": "Test Author"
            }, f)

        # Create __init__.py
        with open(os.path.join(self.dependent_plugin_dir, "__init__.py"), "w") as f:
            f.write('"""Dependent plugin."""\n')

        # Create plugin.py
        with open(os.path.join(self.dependent_plugin_dir, "plugin.py"), "w") as f:
            f.write('''"""Dependent plugin implementation."""

from multi_agent_console.plugin.base import Plugin

class DependentPlugin(Plugin):
    """Plugin that depends on TestPlugin."""

    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return "dependent_plugin"

    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "Dependent Plugin"

    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "A plugin that depends on TestPlugin"

    @property
    def dependencies(self) -> list:
        """Get the plugin dependencies."""
        return ["test_plugin"]

    def initialize(self, context):
        """Initialize the plugin."""
        self.initialized = True
        return True

    def shutdown(self):
        """Shutdown the plugin."""
        self.initialized = False
        return True
''')

        # Create plugin manager
        self.plugin_manager = PluginManager([self.plugin_dir])

    def tearDown(self):
        """Clean up after the test."""
        shutil.rmtree(self.temp_dir)

    def test_discover_plugins(self):
        """Test plugin discovery."""
        plugins = self.plugin_manager.discover_plugins()
        self.assertGreaterEqual(len(plugins), 2)

        # Check if test_plugin is in the discovered plugins
        test_plugin_found = False
        dependent_plugin_found = False

        for plugin_info in plugins:
            if plugin_info.get("id") == "test_plugin":
                test_plugin_found = True
            elif plugin_info.get("id") == "dependent_plugin":
                dependent_plugin_found = True

        self.assertTrue(test_plugin_found)
        self.assertTrue(dependent_plugin_found)

    def test_load_plugin(self):
        """Test loading a plugin."""
        plugin = self.plugin_manager.load_plugin(self.test_plugin_dir)
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, "test_plugin")
        self.assertEqual(plugin.name, "Test Plugin")

    def test_load_plugins(self):
        """Test loading all plugins."""
        plugins = self.plugin_manager.load_plugins()
        self.assertGreaterEqual(len(plugins), 2)
        self.assertIn("test_plugin", plugins)
        self.assertIn("dependent_plugin", plugins)

    def test_initialize_plugins(self):
        """Test initializing plugins."""
        self.plugin_manager.load_plugins()
        context = {"test": "value"}
        results = self.plugin_manager.initialize_plugins(context)

        self.assertIn("test_plugin", results)
        self.assertTrue(results["test_plugin"])
        self.assertIn("dependent_plugin", results)
        self.assertTrue(results["dependent_plugin"])

    def test_shutdown_plugins(self):
        """Test shutting down plugins."""
        self.plugin_manager.load_plugins()
        self.plugin_manager.initialize_plugins({})
        results = self.plugin_manager.shutdown_plugins()

        self.assertIn("test_plugin", results)
        self.assertTrue(results["test_plugin"])
        self.assertIn("dependent_plugin", results)
        self.assertTrue(results["dependent_plugin"])

    def test_get_plugin(self):
        """Test getting a plugin by ID."""
        self.plugin_manager.load_plugins()
        plugin = self.plugin_manager.get_plugin("test_plugin")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.id, "test_plugin")

    def test_get_plugins_by_capability(self):
        """Test getting plugins by capability."""
        self.plugin_manager.load_plugins()
        self.plugin_manager.initialize_plugins({})
        plugins = self.plugin_manager.get_plugins_by_capability("test_capability")
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].id, "test_plugin")

    def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins."""
        self.plugin_manager.load_plugins()
        self.plugin_manager.initialize_plugins({})

        # Disable test_plugin
        result = self.plugin_manager.disable_plugin("test_plugin")
        self.assertFalse(result)  # Should fail because dependent_plugin depends on it

        # Disable dependent_plugin first
        result = self.plugin_manager.disable_plugin("dependent_plugin")
        self.assertTrue(result)
        self.assertIn("dependent_plugin", self.plugin_manager.disabled_plugins)

        # Now disable test_plugin
        result = self.plugin_manager.disable_plugin("test_plugin")
        self.assertTrue(result)
        self.assertIn("test_plugin", self.plugin_manager.disabled_plugins)

        # Enable test_plugin
        result = self.plugin_manager.enable_plugin("test_plugin")
        self.assertTrue(result)
        self.assertNotIn("test_plugin", self.plugin_manager.disabled_plugins)

        # Enable dependent_plugin
        result = self.plugin_manager.enable_plugin("dependent_plugin")
        self.assertTrue(result)
        self.assertNotIn("dependent_plugin", self.plugin_manager.disabled_plugins)

    def test_broadcast_event(self):
        """Test broadcasting an event to plugins."""
        self.plugin_manager.load_plugins()
        self.plugin_manager.initialize_plugins({})

        event_data = {"param": "value"}
        responses = self.plugin_manager.broadcast_event("test_capability", event_data)

        self.assertIn("test_plugin", responses)
        self.assertEqual(responses["test_plugin"]["result"], "success")
        self.assertEqual(responses["test_plugin"]["data"], event_data)


class TestPluginRegistry(unittest.TestCase):
    """Test the PluginRegistry class."""

    def setUp(self):
        """Set up the test."""
        self.temp_dir = tempfile.mkdtemp()
        self.plugins_dir = os.path.join(self.temp_dir, "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)

        # Create registry.json
        self.registry_path = os.path.join(self.temp_dir, "registry.json")
        with open(self.registry_path, "w") as f:
            json.dump({
                "plugins": [
                    {
                        "plugin_id": "test_plugin",
                        "name": "Test Plugin",
                        "description": "A test plugin for unit tests",
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
                        "plugin_id": "another_plugin",
                        "name": "Another Plugin",
                        "description": "Another test plugin",
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

        # Create plugin registry
        self.plugin_registry = PluginRegistry(
            plugins_dir=self.plugins_dir,
            registry_url=f"file://{self.registry_path}"
        )

        # Refresh the registry
        self.plugin_registry.refresh_registry()

    def tearDown(self):
        """Clean up after the test."""
        # Restore original requests.get
        import requests
        requests.get = self.original_get

        # Remove temp directory
        shutil.rmtree(self.temp_dir)

    def test_plugin_info(self):
        """Test PluginInfo class."""
        plugin_info = PluginInfo(
            plugin_id="test_plugin",
            name="Test Plugin",
            description="A test plugin",
            version="1.0.0",
            author="Test Author",
            tags=["test"],
            requirements=[],
            installed=True,
            rating=4.5,
            downloads=100
        )

        self.assertEqual(plugin_info.plugin_id, "test_plugin")
        self.assertEqual(plugin_info.name, "Test Plugin")
        self.assertEqual(plugin_info.description, "A test plugin")
        self.assertEqual(plugin_info.version, "1.0.0")
        self.assertEqual(plugin_info.author, "Test Author")
        self.assertEqual(plugin_info.tags, ["test"])
        self.assertEqual(plugin_info.requirements, [])
        self.assertTrue(plugin_info.installed)
        self.assertEqual(plugin_info.rating, 4.5)
        self.assertEqual(plugin_info.downloads, 100)

        # Test to_dict and from_dict
        plugin_dict = plugin_info.to_dict()
        plugin_info2 = PluginInfo.from_dict(plugin_dict)

        self.assertEqual(plugin_info.plugin_id, plugin_info2.plugin_id)
        self.assertEqual(plugin_info.name, plugin_info2.name)
        self.assertEqual(plugin_info.description, plugin_info2.description)
        self.assertEqual(plugin_info.version, plugin_info2.version)
        self.assertEqual(plugin_info.author, plugin_info2.author)
        self.assertEqual(plugin_info.tags, plugin_info2.tags)
        self.assertEqual(plugin_info.requirements, plugin_info2.requirements)
        self.assertEqual(plugin_info.installed, plugin_info2.installed)
        self.assertEqual(plugin_info.rating, plugin_info2.rating)
        self.assertEqual(plugin_info.downloads, plugin_info2.downloads)

    def test_refresh_registry(self):
        """Test refreshing the plugin registry."""
        # Refresh registry
        result = self.plugin_registry.refresh_registry()
        self.assertTrue(result)

        # Check available plugins
        self.assertEqual(len(self.plugin_registry.available_plugins), 2)
        self.assertIn("test_plugin", self.plugin_registry.available_plugins)
        self.assertIn("another_plugin", self.plugin_registry.available_plugins)

        # Check plugin details
        test_plugin = self.plugin_registry.available_plugins["test_plugin"]
        self.assertEqual(test_plugin.name, "Test Plugin")
        self.assertEqual(test_plugin.rating, 4.5)
        self.assertEqual(test_plugin.downloads, 100)

    def test_get_available_plugins(self):
        """Test getting available plugins."""
        # Refresh registry first
        self.plugin_registry.refresh_registry()

        # Get available plugins
        plugins = self.plugin_registry.get_available_plugins()
        self.assertEqual(len(plugins), 2)

        # Check plugin details
        plugin_ids = [plugin["plugin_id"] for plugin in plugins]
        self.assertIn("test_plugin", plugin_ids)
        self.assertIn("another_plugin", plugin_ids)

    def test_search_plugins(self):
        """Test searching for plugins."""
        # Refresh registry first
        self.plugin_registry.refresh_registry()

        # Search for "test"
        results = self.plugin_registry.search_plugins("test")
        self.assertEqual(len(results), 2)

        # Search for "another"
        results = self.plugin_registry.search_plugins("another")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["plugin_id"], "another_plugin")

        # Search for non-existent term
        results = self.plugin_registry.search_plugins("nonexistent")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
