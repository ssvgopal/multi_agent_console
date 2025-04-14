"""
A2A Plugin for MCP Server.

This plugin adds A2A protocol support to the MCP server.
"""

import logging
import json
from typing import Dict, Any, List, Optional

from ..mcp_server import MCPPlugin, MCPMessage
from ..a2a_adapter import A2AAdapter, A2ATextArtifact


class A2APlugin(MCPPlugin):
    """Plugin that adds A2A protocol support to the MCP server."""
    
    def __init__(self):
        """Initialize the A2A plugin."""
        super().__init__(
            plugin_id="a2a_plugin",
            name="A2A Protocol Support",
            description="Adds support for the Agent-to-Agent (A2A) protocol"
        )
        self.adapter = None
    
    def register(self, server) -> bool:
        """Register the plugin with an MCP server.
        
        Args:
            server: MCP server
            
        Returns:
            True if successful, False otherwise
        """
        result = super().register(server)
        
        if result:
            # Create A2A adapter
            self.adapter = A2AAdapter(server)
            
            # Register A2A-compatible agent for the console
            self.adapter.register_a2a_agent(
                agent_id="console_a2a",
                name="MultiAgentConsole A2A",
                capabilities=["text", "file", "data"]
            )
            
            logging.info("A2A adapter created and console agent registered")
        
        return result
    
    def unregister(self) -> bool:
        """Unregister the plugin from its MCP server.
        
        Returns:
            True if successful, False otherwise
        """
        self.adapter = None
        return super().unregister()
    
    def on_message(self, message: MCPMessage) -> None:
        """Handle an incoming message.
        
        Args:
            message: Incoming message
        """
        # We only need to handle messages specifically for the A2A plugin
        if message.receiver != "a2a_plugin":
            return
        
        if message.message_type == "create_a2a_task":
            self._handle_create_task(message)
        elif message.message_type == "get_a2a_task":
            self._handle_get_task(message)
        elif message.message_type == "cancel_a2a_task":
            self._handle_cancel_task(message)
    
    def _handle_create_task(self, message: MCPMessage) -> None:
        """Handle a create task message.
        
        Args:
            message: Message containing task creation request
        """
        if not self.adapter:
            self._send_error(message.sender, "A2A adapter not initialized")
            return
        
        content = message.content
        agent_id = content.get("agent_id")
        input_text = content.get("input_text")
        
        if not agent_id or not input_text:
            self._send_error(message.sender, "Missing required parameters: agent_id, input_text")
            return
        
        # Create input artifact
        input_artifact = A2ATextArtifact.create(
            text=input_text,
            name="User Input",
            description="Text input from user"
        )
        
        # Create task
        task_id = self.adapter.create_task(agent_id, [input_artifact])
        
        # Send response
        self._send_response(
            receiver=message.sender,
            message_type="a2a_task_created",
            content={
                "task_id": task_id,
                "status": "Task created successfully"
            }
        )
    
    def _handle_get_task(self, message: MCPMessage) -> None:
        """Handle a get task message.
        
        Args:
            message: Message containing task query
        """
        if not self.adapter:
            self._send_error(message.sender, "A2A adapter not initialized")
            return
        
        content = message.content
        task_id = content.get("task_id")
        
        if not task_id:
            self._send_error(message.sender, "Missing required parameter: task_id")
            return
        
        # Get task
        task = self.adapter.get_task(task_id)
        
        if not task:
            self._send_error(message.sender, f"Task not found: {task_id}")
            return
        
        # Send response
        self._send_response(
            receiver=message.sender,
            message_type="a2a_task_info",
            content={
                "task": task
            }
        )
    
    def _handle_cancel_task(self, message: MCPMessage) -> None:
        """Handle a cancel task message.
        
        Args:
            message: Message containing task cancellation request
        """
        if not self.adapter:
            self._send_error(message.sender, "A2A adapter not initialized")
            return
        
        content = message.content
        task_id = content.get("task_id")
        
        if not task_id:
            self._send_error(message.sender, "Missing required parameter: task_id")
            return
        
        # Cancel task
        success = self.adapter.cancel_task(task_id)
        
        if not success:
            self._send_error(message.sender, f"Failed to cancel task: {task_id}")
            return
        
        # Send response
        self._send_response(
            receiver=message.sender,
            message_type="a2a_task_cancelled",
            content={
                "task_id": task_id,
                "status": "Task cancelled successfully"
            }
        )
    
    def _send_response(self, receiver: str, message_type: str, content: Dict[str, Any]) -> None:
        """Send a response message.
        
        Args:
            receiver: Message receiver
            message_type: Message type
            content: Message content
        """
        if not self.server:
            logging.error("Cannot send response: server not initialized")
            return
        
        message = MCPMessage(
            sender="a2a_plugin",
            receiver=receiver,
            message_type=message_type,
            content=content
        )
        
        self.server.send_message(message)
    
    def _send_error(self, receiver: str, error_message: str) -> None:
        """Send an error message.
        
        Args:
            receiver: Message receiver
            error_message: Error message
        """
        self._send_response(
            receiver=receiver,
            message_type="a2a_error",
            content={
                "error": error_message
            }
        )
