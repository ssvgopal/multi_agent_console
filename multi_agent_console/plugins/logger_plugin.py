"""
Logger Plugin for MCP Server.

This plugin logs all messages passing through the MCP server.
"""

import logging
import time
from typing import Dict, Any

from ..mcp_server import MCPPlugin, MCPMessage


class LoggerPlugin(MCPPlugin):
    """Plugin that logs all MCP messages."""
    
    def __init__(self):
        """Initialize the logger plugin."""
        super().__init__(
            plugin_id="logger_plugin",
            name="Message Logger",
            description="Logs all messages passing through the MCP server"
        )
        self.log_count = 0
        self.start_time = time.time()
    
    def on_message(self, message: MCPMessage) -> None:
        """Handle an incoming message.
        
        Args:
            message: Incoming message
        """
        self.log_count += 1
        logging.info(f"MCP Message: {message.sender} -> {message.receiver} [{message.message_type}]")
        
        # Log detailed message content at debug level
        logging.debug(f"Message content: {message.content}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin statistics.
        
        Returns:
            Dictionary with statistics
        """
        uptime = time.time() - self.start_time
        return {
            "log_count": self.log_count,
            "uptime": uptime,
            "messages_per_second": self.log_count / uptime if uptime > 0 else 0
        }
