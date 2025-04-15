"""
MCP (Multi-Agent Communication Protocol) Server for MultiAgentConsole.

This module provides a simple server for agent communication:
- Standardized message format
- Agent registration
- Message routing
- Plugin integration

Author: Sai Sunkara
Copyright 2025 Sai Sunkara
License: MIT
"""

import json
import logging
import threading
import time
from typing import Dict, List, Any, Callable, Optional
import uuid


class MCPMessage:
    """Represents a message in the MCP system."""

    def __init__(self, sender: str, receiver: str, message_type: str, content: Any,
                message_id: Optional[str] = None, reply_to: Optional[str] = None):
        """Initialize a new MCP message.

        Args:
            sender: ID of the sending agent
            receiver: ID of the receiving agent (or 'broadcast')
            message_type: Type of message
            content: Message content
            message_id: Unique message ID (generated if not provided)
            reply_to: ID of the message this is replying to
        """
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.content = content
        self.message_id = message_id or str(uuid.uuid4())
        self.reply_to = reply_to
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary.

        Returns:
            Dictionary representation of the message
        """
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "content": self.content,
            "message_id": self.message_id,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create a message from a dictionary.

        Args:
            data: Dictionary representation of the message

        Returns:
            MCPMessage instance
        """
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            message_type=data["message_type"],
            content=data["content"],
            message_id=data.get("message_id"),
            reply_to=data.get("reply_to")
        )


class MCPAgent:
    """Represents an agent in the MCP system."""

    def __init__(self, agent_id: str, name: str, capabilities: List[str] = None):
        """Initialize a new MCP agent.

        Args:
            agent_id: Unique agent ID
            name: Agent name
            capabilities: List of agent capabilities
        """
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities or []
        self.is_active = True
        self.last_seen = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent to a dictionary.

        Returns:
            Dictionary representation of the agent
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "is_active": self.is_active,
            "last_seen": self.last_seen
        }


class MCPServer:
    """Simple MCP server for agent communication."""

    def __init__(self):
        """Initialize the MCP server."""
        self.agents: Dict[str, MCPAgent] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.message_history: List[MCPMessage] = []
        self.max_history = 1000
        self.lock = threading.RLock()

        logging.info("MCP Server initialized")

    def register_agent(self, agent: MCPAgent) -> bool:
        """Register an agent with the server.

        Args:
            agent: Agent to register

        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            if agent.agent_id in self.agents:
                logging.warning(f"Agent {agent.agent_id} already registered")
                return False

            self.agents[agent.agent_id] = agent
            logging.info(f"Agent registered: {agent.name} ({agent.agent_id})")

            # Broadcast agent registration
            self.send_message(MCPMessage(
                sender="system",
                receiver="broadcast",
                message_type="agent_registered",
                content=agent.to_dict()
            ))

            return True

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the server.

        Args:
            agent_id: ID of the agent to unregister

        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            if agent_id not in self.agents:
                logging.warning(f"Agent {agent_id} not registered")
                return False

            agent = self.agents.pop(agent_id)
            logging.info(f"Agent unregistered: {agent.name} ({agent.agent_id})")

            # Broadcast agent unregistration
            self.send_message(MCPMessage(
                sender="system",
                receiver="broadcast",
                message_type="agent_unregistered",
                content={"agent_id": agent_id, "name": agent.name}
            ))

            return True

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler.

        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        with self.lock:
            if message_type not in self.message_handlers:
                self.message_handlers[message_type] = []

            self.message_handlers[message_type].append(handler)
            logging.debug(f"Handler registered for message type: {message_type}")

    def unregister_handler(self, message_type: str, handler: Callable) -> bool:
        """Unregister a message handler.

        Args:
            message_type: Type of message to handle
            handler: Handler function

        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            if message_type not in self.message_handlers:
                return False

            if handler not in self.message_handlers[message_type]:
                return False

            self.message_handlers[message_type].remove(handler)
            logging.debug(f"Handler unregistered for message type: {message_type}")
            return True

    def send_message(self, message: MCPMessage) -> bool:
        """Send a message through the server.

        Args:
            message: Message to send

        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            # Add to history
            self.message_history.append(message)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)

            # Handle broadcast messages
            if message.receiver == "broadcast":
                for agent_id in self.agents:
                    if agent_id != message.sender:
                        self._deliver_message(message, agent_id)
                return True

            # Handle direct messages
            if message.receiver in self.agents:
                return self._deliver_message(message, message.receiver)
            else:
                logging.warning(f"Unknown receiver: {message.receiver}")
                return False

    def _deliver_message(self, message: MCPMessage, receiver_id: str) -> bool:
        """Deliver a message to a specific receiver.

        Args:
            message: Message to deliver
            receiver_id: ID of the receiver

        Returns:
            True if successful, False otherwise
        """
        # Update agent's last seen time if they're the sender
        if message.sender in self.agents:
            self.agents[message.sender].last_seen = time.time()

        # Call handlers for this message type
        if message.message_type in self.message_handlers:
            for handler in self.message_handlers[message.message_type]:
                try:
                    handler(message)
                except Exception as e:
                    logging.error(f"Error in message handler: {e}")

        return True

    def get_agent(self, agent_id: str) -> Optional[MCPAgent]:
        """Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            MCPAgent instance or None if not found
        """
        return self.agents.get(agent_id)

    def list_agents(self) -> List[MCPAgent]:
        """List all registered agents.

        Returns:
            List of registered agents
        """
        return list(self.agents.values())

    def get_recent_messages(self, count: int = 10) -> List[MCPMessage]:
        """Get recent messages.

        Args:
            count: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        with self.lock:
            return self.message_history[-count:]


class MCPPlugin:
    """Base class for MCP plugins."""

    def __init__(self, plugin_id: str, name: str, description: str = ""):
        """Initialize a new MCP plugin.

        Args:
            plugin_id: Unique plugin ID
            name: Plugin name
            description: Plugin description
        """
        self.plugin_id = plugin_id
        self.name = name
        self.description = description
        self.is_enabled = False
        self.server = None

    def register(self, server: MCPServer) -> bool:
        """Register the plugin with an MCP server.

        Args:
            server: MCP server

        Returns:
            True if successful, False otherwise
        """
        self.server = server
        self.is_enabled = True
        logging.info(f"Plugin registered: {self.name} ({self.plugin_id})")
        return True

    def unregister(self) -> bool:
        """Unregister the plugin from its MCP server.

        Returns:
            True if successful, False otherwise
        """
        if self.server:
            self.is_enabled = False
            self.server = None
            logging.info(f"Plugin unregistered: {self.name} ({self.plugin_id})")
            return True
        return False

    def on_message(self, message: MCPMessage) -> None:
        """Handle an incoming message.

        Args:
            message: Incoming message
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert the plugin to a dictionary.

        Returns:
            Dictionary representation of the plugin
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "description": self.description,
            "is_enabled": self.is_enabled
        }


class MCPPluginManager:
    """Manages MCP plugins."""

    def __init__(self, server: MCPServer):
        """Initialize the plugin manager.

        Args:
            server: MCP server
        """
        self.server = server
        self.plugins: Dict[str, MCPPlugin] = {}

        logging.info("MCP Plugin Manager initialized")

    def register_plugin(self, plugin: MCPPlugin) -> bool:
        """Register a plugin.

        Args:
            plugin: Plugin to register

        Returns:
            True if successful, False otherwise
        """
        if plugin.plugin_id in self.plugins:
            logging.warning(f"Plugin {plugin.plugin_id} already registered")
            return False

        if plugin.register(self.server):
            self.plugins[plugin.plugin_id] = plugin

            # Register message handler
            self.server.register_handler("broadcast", plugin.on_message)

            # Broadcast plugin registration
            self.server.send_message(MCPMessage(
                sender="system",
                receiver="broadcast",
                message_type="plugin_registered",
                content=plugin.to_dict()
            ))

            return True

        return False

    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin.

        Args:
            plugin_id: ID of the plugin to unregister

        Returns:
            True if successful, False otherwise
        """
        if plugin_id not in self.plugins:
            logging.warning(f"Plugin {plugin_id} not registered")
            return False

        plugin = self.plugins[plugin_id]
        if plugin.unregister():
            del self.plugins[plugin_id]

            # Broadcast plugin unregistration
            self.server.send_message(MCPMessage(
                sender="system",
                receiver="broadcast",
                message_type="plugin_unregistered",
                content={"plugin_id": plugin_id, "name": plugin.name}
            ))

            return True

        return False

    def get_plugin(self, plugin_id: str) -> Optional[MCPPlugin]:
        """Get a plugin by ID.

        Args:
            plugin_id: Plugin ID

        Returns:
            MCPPlugin instance or None if not found
        """
        return self.plugins.get(plugin_id)

    def list_plugins(self) -> List[MCPPlugin]:
        """List all registered plugins.

        Returns:
            List of registered plugins
        """
        return list(self.plugins.values())
