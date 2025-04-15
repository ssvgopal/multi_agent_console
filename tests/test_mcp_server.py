"""Test the MCP server module."""

import unittest
import json
import time
from unittest.mock import MagicMock, patch

from multi_agent_console.mcp_server import (
    MCPServer, MCPMessage, MCPAgent, MCPPlugin, MCPPluginManager
)


class TestMCPMessage(unittest.TestCase):
    """Test the MCPMessage class."""

    def test_init(self):
        """Test initializing a message."""
        # Create a message
        message = MCPMessage(
            sender="test_sender",
            receiver="test_receiver",
            message_type="test_type",
            content={"key": "value"},
            message_id="test_id",
            reply_to="reply_id"
        )

        # Check that the attributes were set correctly
        self.assertEqual(message.sender, "test_sender")
        self.assertEqual(message.receiver, "test_receiver")
        self.assertEqual(message.message_type, "test_type")
        self.assertEqual(message.content, {"key": "value"})
        self.assertEqual(message.message_id, "test_id")
        self.assertEqual(message.reply_to, "reply_id")
        self.assertIsNotNone(message.timestamp)

    def test_init_with_defaults(self):
        """Test initializing a message with default values."""
        # Create a message with default values
        message = MCPMessage(
            sender="test_sender",
            receiver="test_receiver",
            message_type="test_type",
            content={"key": "value"}
        )

        # Check that the attributes were set correctly
        self.assertEqual(message.sender, "test_sender")
        self.assertEqual(message.receiver, "test_receiver")
        self.assertEqual(message.message_type, "test_type")
        self.assertEqual(message.content, {"key": "value"})
        self.assertIsNotNone(message.message_id)
        self.assertIsNone(message.reply_to)
        self.assertIsNotNone(message.timestamp)

    def test_to_dict(self):
        """Test converting a message to a dictionary."""
        # Create a message
        message = MCPMessage(
            sender="test_sender",
            receiver="test_receiver",
            message_type="test_type",
            content={"key": "value"},
            message_id="test_id",
            reply_to="reply_id"
        )

        # Convert to dictionary
        message_dict = message.to_dict()

        # Check that the dictionary contains the correct values
        self.assertEqual(message_dict["sender"], "test_sender")
        self.assertEqual(message_dict["receiver"], "test_receiver")
        self.assertEqual(message_dict["message_type"], "test_type")
        self.assertEqual(message_dict["content"], {"key": "value"})
        self.assertEqual(message_dict["message_id"], "test_id")
        self.assertEqual(message_dict["reply_to"], "reply_id")
        self.assertEqual(message_dict["timestamp"], message.timestamp)

    def test_from_dict(self):
        """Test creating a message from a dictionary."""
        # Create a dictionary
        message_dict = {
            "sender": "test_sender",
            "receiver": "test_receiver",
            "message_type": "test_type",
            "content": {"key": "value"},
            "message_id": "test_id",
            "reply_to": "reply_id"
        }

        # Create a message from the dictionary
        message = MCPMessage.from_dict(message_dict)

        # Check that the attributes were set correctly
        self.assertEqual(message.sender, "test_sender")
        self.assertEqual(message.receiver, "test_receiver")
        self.assertEqual(message.message_type, "test_type")
        self.assertEqual(message.content, {"key": "value"})
        self.assertEqual(message.message_id, "test_id")
        self.assertEqual(message.reply_to, "reply_id")


class TestMCPAgent(unittest.TestCase):
    """Test the MCPAgent class."""

    def test_init(self):
        """Test initializing an agent."""
        # Create an agent
        agent = MCPAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["capability1", "capability2"]
        )

        # Check that the attributes were set correctly
        self.assertEqual(agent.agent_id, "test_agent")
        self.assertEqual(agent.name, "Test Agent")
        self.assertEqual(agent.capabilities, ["capability1", "capability2"])
        self.assertTrue(agent.is_active)
        self.assertIsNotNone(agent.last_seen)

    def test_init_with_defaults(self):
        """Test initializing an agent with default values."""
        # Create an agent with default values
        agent = MCPAgent(
            agent_id="test_agent",
            name="Test Agent"
        )

        # Check that the attributes were set correctly
        self.assertEqual(agent.agent_id, "test_agent")
        self.assertEqual(agent.name, "Test Agent")
        self.assertEqual(agent.capabilities, [])
        self.assertTrue(agent.is_active)
        self.assertIsNotNone(agent.last_seen)

    def test_to_dict(self):
        """Test converting an agent to a dictionary."""
        # Create an agent
        agent = MCPAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["capability1", "capability2"]
        )

        # Convert to dictionary
        agent_dict = agent.to_dict()

        # Check that the dictionary contains the correct values
        self.assertEqual(agent_dict["agent_id"], "test_agent")
        self.assertEqual(agent_dict["name"], "Test Agent")
        self.assertEqual(agent_dict["capabilities"], ["capability1", "capability2"])
        self.assertTrue(agent_dict["is_active"])
        self.assertEqual(agent_dict["last_seen"], agent.last_seen)


class TestMCPServer(unittest.TestCase):
    """Test the MCPServer class."""

    def setUp(self):
        """Set up the test environment."""
        # Create an MCP server
        self.server = MCPServer()

    def test_init(self):
        """Test initializing a server."""
        # Check that the attributes were initialized correctly
        self.assertEqual(self.server.agents, {})
        self.assertEqual(self.server.message_handlers, {})
        self.assertEqual(self.server.message_history, [])
        self.assertEqual(self.server.max_history, 1000)

    def test_register_agent(self):
        """Test registering an agent."""
        # Create an agent
        agent = MCPAgent(
            agent_id="test_agent",
            name="Test Agent",
            capabilities=["capability1", "capability2"]
        )

        # Register the agent
        result = self.server.register_agent(agent)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the agent was added to the agents dictionary
        self.assertIn("test_agent", self.server.agents)
        self.assertEqual(self.server.agents["test_agent"], agent)

        # Check that a message was added to the history
        self.assertEqual(len(self.server.message_history), 1)
        message = self.server.message_history[0]
        self.assertEqual(message.sender, "system")
        self.assertEqual(message.receiver, "broadcast")
        self.assertEqual(message.message_type, "agent_registered")
        self.assertEqual(message.content, agent.to_dict())

        # Try to register the same agent again
        result = self.server.register_agent(agent)

        # Check that the result is False
        self.assertFalse(result)

    def test_unregister_agent(self):
        """Test unregistering an agent."""
        # Create and register an agent
        agent = MCPAgent(
            agent_id="test_agent",
            name="Test Agent"
        )
        self.server.register_agent(agent)

        # Unregister the agent
        result = self.server.unregister_agent("test_agent")

        # Check that the result is True
        self.assertTrue(result)

        # Check that the agent was removed from the agents dictionary
        self.assertNotIn("test_agent", self.server.agents)

        # Check that a message was added to the history
        self.assertEqual(len(self.server.message_history), 2)
        message = self.server.message_history[1]
        self.assertEqual(message.sender, "system")
        self.assertEqual(message.receiver, "broadcast")
        self.assertEqual(message.message_type, "agent_unregistered")
        self.assertEqual(message.content["agent_id"], "test_agent")

        # Try to unregister a non-existent agent
        result = self.server.unregister_agent("non_existent_agent")

        # Check that the result is False
        self.assertFalse(result)

    def test_register_handler(self):
        """Test registering a message handler."""
        # Create a handler function
        handler = MagicMock()

        # Register the handler
        self.server.register_handler("test_type", handler)

        # Check that the handler was added to the handlers dictionary
        self.assertIn("test_type", self.server.message_handlers)
        self.assertIn(handler, self.server.message_handlers["test_type"])

        # Register another handler for the same type
        handler2 = MagicMock()
        self.server.register_handler("test_type", handler2)

        # Check that both handlers are in the list
        self.assertEqual(len(self.server.message_handlers["test_type"]), 2)
        self.assertIn(handler, self.server.message_handlers["test_type"])
        self.assertIn(handler2, self.server.message_handlers["test_type"])

    def test_unregister_handler(self):
        """Test unregistering a message handler."""
        # Create and register a handler
        handler = MagicMock()
        self.server.register_handler("test_type", handler)

        # Unregister the handler
        result = self.server.unregister_handler("test_type", handler)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the handler was removed from the handlers dictionary
        self.assertEqual(len(self.server.message_handlers["test_type"]), 0)

        # Try to unregister a non-existent handler
        result = self.server.unregister_handler("test_type", handler)

        # Check that the result is False
        self.assertFalse(result)

        # Try to unregister a handler for a non-existent type
        result = self.server.unregister_handler("non_existent_type", handler)

        # Check that the result is False
        self.assertFalse(result)

    def test_send_message_direct(self):
        """Test sending a direct message."""
        # Create and register agents
        agent1 = MCPAgent(agent_id="agent1", name="Agent 1")
        agent2 = MCPAgent(agent_id="agent2", name="Agent 2")
        self.server.register_agent(agent1)
        self.server.register_agent(agent2)

        # Create a handler
        handler = MagicMock()
        self.server.register_handler("test_type", handler)

        # Create a message
        message = MCPMessage(
            sender="agent1",
            receiver="agent2",
            message_type="test_type",
            content={"key": "value"}
        )

        # Send the message
        result = self.server.send_message(message)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the message was added to the history
        self.assertIn(message, self.server.message_history)

        # Check that the handler was called
        handler.assert_called_once_with(message)

        # Check that the sender's last_seen time was updated
        self.assertAlmostEqual(agent1.last_seen, time.time(), delta=1)

    def test_send_message_broadcast(self):
        """Test sending a broadcast message."""
        # Create and register agents
        agent1 = MCPAgent(agent_id="agent1", name="Agent 1")
        agent2 = MCPAgent(agent_id="agent2", name="Agent 2")
        agent3 = MCPAgent(agent_id="agent3", name="Agent 3")
        self.server.register_agent(agent1)
        self.server.register_agent(agent2)
        self.server.register_agent(agent3)

        # Create a handler
        handler = MagicMock()
        self.server.register_handler("test_type", handler)

        # Create a broadcast message
        message = MCPMessage(
            sender="agent1",
            receiver="broadcast",
            message_type="test_type",
            content={"key": "value"}
        )

        # Send the message
        result = self.server.send_message(message)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the message was added to the history
        self.assertIn(message, self.server.message_history)

        # Check that the handler was called for each recipient
        self.assertEqual(handler.call_count, 2)  # agent2 and agent3, not agent1

        # Check that the sender's last_seen time was updated
        self.assertAlmostEqual(agent1.last_seen, time.time(), delta=1)

    def test_send_message_unknown_receiver(self):
        """Test sending a message to an unknown receiver."""
        # Create and register an agent
        agent = MCPAgent(agent_id="agent1", name="Agent 1")
        self.server.register_agent(agent)

        # Create a message with an unknown receiver
        message = MCPMessage(
            sender="agent1",
            receiver="unknown_agent",
            message_type="test_type",
            content={"key": "value"}
        )

        # Send the message
        result = self.server.send_message(message)

        # Check that the result is False
        self.assertFalse(result)

        # Check that the message was still added to the history
        self.assertIn(message, self.server.message_history)

    def test_get_agent(self):
        """Test getting an agent by ID."""
        # Create and register an agent
        agent = MCPAgent(agent_id="test_agent", name="Test Agent")
        self.server.register_agent(agent)

        # Get the agent
        result = self.server.get_agent("test_agent")

        # Check that the correct agent was returned
        self.assertEqual(result, agent)

        # Try to get a non-existent agent
        result = self.server.get_agent("non_existent_agent")

        # Check that None was returned
        self.assertIsNone(result)

    def test_list_agents(self):
        """Test listing all registered agents."""
        # Create and register some agents
        agent1 = MCPAgent(agent_id="agent1", name="Agent 1")
        agent2 = MCPAgent(agent_id="agent2", name="Agent 2")
        self.server.register_agent(agent1)
        self.server.register_agent(agent2)

        # List the agents
        agents = self.server.list_agents()

        # Check that the correct agents were returned
        self.assertEqual(len(agents), 2)
        self.assertIn(agent1, agents)
        self.assertIn(agent2, agents)

    def test_get_recent_messages(self):
        """Test getting recent messages."""
        # Create and send some messages
        for i in range(5):
            message = MCPMessage(
                sender=f"sender{i}",
                receiver=f"receiver{i}",
                message_type="test_type",
                content={"index": i}
            )
            self.server.message_history.append(message)

        # Get the recent messages
        messages = self.server.get_recent_messages(3)

        # Check that the correct messages were returned
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].content["index"], 2)
        self.assertEqual(messages[1].content["index"], 3)
        self.assertEqual(messages[2].content["index"], 4)


class TestMCPPlugin(unittest.TestCase):
    """Test the MCPPlugin class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a plugin
        self.plugin = MCPPlugin(
            plugin_id="test_plugin",
            name="Test Plugin",
            description="A test plugin"
        )

        # Create a mock server
        self.server = MagicMock(spec=MCPServer)

    def test_init(self):
        """Test initializing a plugin."""
        # Check that the attributes were set correctly
        self.assertEqual(self.plugin.plugin_id, "test_plugin")
        self.assertEqual(self.plugin.name, "Test Plugin")
        self.assertEqual(self.plugin.description, "A test plugin")
        self.assertFalse(self.plugin.is_enabled)
        self.assertIsNone(self.plugin.server)

    def test_register(self):
        """Test registering a plugin with a server."""
        # Register the plugin
        result = self.plugin.register(self.server)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the server was set
        self.assertEqual(self.plugin.server, self.server)

        # Check that the plugin is enabled
        self.assertTrue(self.plugin.is_enabled)

    def test_unregister(self):
        """Test unregistering a plugin."""
        # Register the plugin first
        self.plugin.register(self.server)

        # Unregister the plugin
        result = self.plugin.unregister()

        # Check that the result is True
        self.assertTrue(result)

        # Check that the server was cleared
        self.assertIsNone(self.plugin.server)

        # Check that the plugin is disabled
        self.assertFalse(self.plugin.is_enabled)

        # Try to unregister an unregistered plugin
        result = self.plugin.unregister()

        # Check that the result is False
        self.assertFalse(result)

    def test_on_message(self):
        """Test the on_message method."""
        # Create a message
        message = MCPMessage(
            sender="test_sender",
            receiver="test_plugin",
            message_type="test_type",
            content={"key": "value"}
        )

        # Call on_message
        # This should not raise an exception
        self.plugin.on_message(message)

    def test_to_dict(self):
        """Test converting a plugin to a dictionary."""
        # Convert to dictionary
        plugin_dict = self.plugin.to_dict()

        # Check that the dictionary contains the correct values
        self.assertEqual(plugin_dict["plugin_id"], "test_plugin")
        self.assertEqual(plugin_dict["name"], "Test Plugin")
        self.assertEqual(plugin_dict["description"], "A test plugin")
        self.assertFalse(plugin_dict["is_enabled"])


class TestMCPPluginManager(unittest.TestCase):
    """Test the MCPPluginManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a mock server
        self.server = MagicMock(spec=MCPServer)

        # Create a plugin manager
        self.plugin_manager = MCPPluginManager(self.server)

    def test_init(self):
        """Test initializing a plugin manager."""
        # Check that the attributes were set correctly
        self.assertEqual(self.plugin_manager.server, self.server)
        self.assertEqual(self.plugin_manager.plugins, {})

    def test_register_plugin(self):
        """Test registering a plugin."""
        # Create a mock plugin
        plugin = MagicMock(spec=MCPPlugin)
        plugin.plugin_id = "test_plugin"
        plugin.name = "Test Plugin"
        plugin.description = "A test plugin"
        plugin.register.return_value = True
        plugin.to_dict.return_value = {
            "plugin_id": "test_plugin",
            "name": "Test Plugin",
            "description": "A test plugin",
            "is_enabled": True
        }

        # Register the plugin
        result = self.plugin_manager.register_plugin(plugin)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the plugin was added to the plugins dictionary
        self.assertIn("test_plugin", self.plugin_manager.plugins)
        self.assertEqual(self.plugin_manager.plugins["test_plugin"], plugin)

        # Check that the plugin was registered with the server
        plugin.register.assert_called_once_with(self.server)

        # Check that a message handler was registered
        self.server.register_handler.assert_called_once_with("broadcast", plugin.on_message)

        # Check that a message was sent
        self.server.send_message.assert_called_once()
        message = self.server.send_message.call_args[0][0]
        self.assertEqual(message.sender, "system")
        self.assertEqual(message.receiver, "broadcast")
        self.assertEqual(message.message_type, "plugin_registered")
        self.assertEqual(message.content, plugin.to_dict())

        # Try to register the same plugin again
        result = self.plugin_manager.register_plugin(plugin)

        # Check that the result is False
        self.assertFalse(result)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        # Create and register a plugin
        plugin = MagicMock(spec=MCPPlugin)
        plugin.plugin_id = "test_plugin"
        plugin.name = "Test Plugin"
        plugin.unregister.return_value = True
        self.plugin_manager.plugins["test_plugin"] = plugin

        # Unregister the plugin
        result = self.plugin_manager.unregister_plugin("test_plugin")

        # Check that the result is True
        self.assertTrue(result)

        # Check that the plugin was removed from the plugins dictionary
        self.assertNotIn("test_plugin", self.plugin_manager.plugins)

        # Check that the plugin was unregistered
        plugin.unregister.assert_called_once()

        # Check that a message was sent
        self.server.send_message.assert_called_once()
        message = self.server.send_message.call_args[0][0]
        self.assertEqual(message.sender, "system")
        self.assertEqual(message.receiver, "broadcast")
        self.assertEqual(message.message_type, "plugin_unregistered")
        self.assertEqual(message.content["plugin_id"], "test_plugin")
        self.assertEqual(message.content["name"], "Test Plugin")

        # Try to unregister a non-existent plugin
        result = self.plugin_manager.unregister_plugin("non_existent_plugin")

        # Check that the result is False
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
