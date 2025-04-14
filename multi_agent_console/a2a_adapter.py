"""
A2A (Agent-to-Agent) Protocol Adapter for MultiAgentConsole.

This module provides an adapter between the MCP server and the A2A protocol,
allowing the MultiAgentConsole to communicate with A2A-compatible agents.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple

from .mcp_server import MCPMessage, MCPAgent


class A2AAdapter:
    """Adapter between MCP server and A2A protocol."""
    
    def __init__(self, mcp_server):
        """Initialize the A2A adapter.
        
        Args:
            mcp_server: The MCP server instance
        """
        self.mcp_server = mcp_server
        self.tasks = {}  # Store A2A tasks
        
        # Register message handlers
        self.mcp_server.register_handler("a2a_request", self._handle_a2a_request)
        self.mcp_server.register_handler("a2a_response", self._handle_a2a_response)
        
        logging.info("A2A adapter initialized")
    
    def register_a2a_agent(self, agent_id: str, name: str, capabilities: List[str] = None) -> bool:
        """Register an A2A-compatible agent with the MCP server.
        
        Args:
            agent_id: Unique agent ID
            name: Agent name
            capabilities: List of agent capabilities
            
        Returns:
            True if successful, False otherwise
        """
        # Create an MCP agent with A2A capability
        if not capabilities:
            capabilities = []
        
        if "a2a" not in capabilities:
            capabilities.append("a2a")
        
        agent = MCPAgent(
            agent_id=agent_id,
            name=name,
            capabilities=capabilities
        )
        
        # Register the agent with the MCP server
        return self.mcp_server.register_agent(agent)
    
    def create_task(self, agent_id: str, input_artifacts: List[Dict[str, Any]]) -> str:
        """Create a new A2A task.
        
        Args:
            agent_id: ID of the agent to execute the task
            input_artifacts: List of input artifacts for the task
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        # Create A2A task
        task = {
            "id": task_id,
            "state": "PENDING",
            "agent_id": agent_id,
            "input_artifacts": input_artifacts,
            "output_artifacts": [],
            "created_at": None,
            "updated_at": None
        }
        
        # Store the task
        self.tasks[task_id] = task
        
        # Create A2A request message
        a2a_request = {
            "jsonrpc": "2.0",
            "id": task_id,
            "method": "tasks/create",
            "params": {
                "input": input_artifacts
            }
        }
        
        # Send the request to the agent
        self._send_a2a_message(agent_id, a2a_request)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get an A2A task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dictionary or None if not found
        """
        return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel an A2A task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if successful, False otherwise
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        agent_id = task["agent_id"]
        
        # Create A2A cancel request
        a2a_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tasks/cancel",
            "params": {
                "taskId": task_id
            }
        }
        
        # Send the request to the agent
        self._send_a2a_message(agent_id, a2a_request)
        
        # Update task state
        task["state"] = "CANCELLING"
        
        return True
    
    def _send_a2a_message(self, agent_id: str, a2a_message: Dict[str, Any]) -> bool:
        """Send an A2A message to an agent.
        
        Args:
            agent_id: ID of the agent to send the message to
            a2a_message: A2A message to send
            
        Returns:
            True if successful, False otherwise
        """
        # Convert A2A message to MCP message
        mcp_message = MCPMessage(
            sender="a2a_adapter",
            receiver=agent_id,
            message_type="a2a_request",
            content=a2a_message
        )
        
        # Send the message
        return self.mcp_server.send_message(mcp_message)
    
    def _handle_a2a_request(self, message: MCPMessage) -> None:
        """Handle an A2A request message.
        
        Args:
            message: MCP message containing an A2A request
        """
        if message.receiver != "a2a_adapter":
            return
        
        a2a_request = message.content
        
        # Process the A2A request based on method
        method = a2a_request.get("method")
        
        if method == "tasks/create":
            self._handle_create_task(message.sender, a2a_request)
        elif method == "tasks/get":
            self._handle_get_task(message.sender, a2a_request)
        elif method == "tasks/cancel":
            self._handle_cancel_task(message.sender, a2a_request)
        else:
            logging.warning(f"Unknown A2A method: {method}")
    
    def _handle_a2a_response(self, message: MCPMessage) -> None:
        """Handle an A2A response message.
        
        Args:
            message: MCP message containing an A2A response
        """
        if message.receiver != "a2a_adapter":
            return
        
        a2a_response = message.content
        
        # Update task based on response
        task_id = a2a_response.get("id")
        
        if task_id in self.tasks:
            task = self.tasks[task_id]
            
            # Check for error
            if "error" in a2a_response and a2a_response["error"]:
                task["state"] = "ERROR"
                task["error"] = a2a_response["error"]
            
            # Check for result
            if "result" in a2a_response and a2a_response["result"]:
                result = a2a_response["result"]
                
                # Update task state
                if "state" in result:
                    task["state"] = result["state"]
                
                # Update output artifacts
                if "output" in result:
                    task["output_artifacts"] = result["output"]
    
    def _handle_create_task(self, sender: str, a2a_request: Dict[str, Any]) -> None:
        """Handle a tasks/create request.
        
        Args:
            sender: ID of the sender agent
            a2a_request: A2A request message
        """
        task_id = a2a_request.get("id", str(uuid.uuid4()))
        input_artifacts = a2a_request.get("params", {}).get("input", [])
        
        # Create task
        task = {
            "id": task_id,
            "state": "PENDING",
            "agent_id": sender,
            "input_artifacts": input_artifacts,
            "output_artifacts": [],
            "created_at": None,
            "updated_at": None
        }
        
        # Store the task
        self.tasks[task_id] = task
        
        # Create response
        a2a_response = {
            "jsonrpc": "2.0",
            "id": task_id,
            "result": {
                "id": task_id,
                "state": "PENDING"
            }
        }
        
        # Send response
        self._send_a2a_response(sender, a2a_response)
    
    def _handle_get_task(self, sender: str, a2a_request: Dict[str, Any]) -> None:
        """Handle a tasks/get request.
        
        Args:
            sender: ID of the sender agent
            a2a_request: A2A request message
        """
        task_id = a2a_request.get("params", {}).get("taskId")
        
        if not task_id or task_id not in self.tasks:
            # Task not found
            a2a_response = {
                "jsonrpc": "2.0",
                "id": a2a_request.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Invalid parameters",
                    "data": {
                        "reason": "Task not found"
                    }
                }
            }
        else:
            # Return task
            task = self.tasks[task_id]
            
            a2a_response = {
                "jsonrpc": "2.0",
                "id": a2a_request.get("id"),
                "result": {
                    "id": task["id"],
                    "state": task["state"],
                    "input": task["input_artifacts"],
                    "output": task["output_artifacts"]
                }
            }
        
        # Send response
        self._send_a2a_response(sender, a2a_response)
    
    def _handle_cancel_task(self, sender: str, a2a_request: Dict[str, Any]) -> None:
        """Handle a tasks/cancel request.
        
        Args:
            sender: ID of the sender agent
            a2a_request: A2A request message
        """
        task_id = a2a_request.get("params", {}).get("taskId")
        
        if not task_id or task_id not in self.tasks:
            # Task not found
            a2a_response = {
                "jsonrpc": "2.0",
                "id": a2a_request.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Invalid parameters",
                    "data": {
                        "reason": "Task not found"
                    }
                }
            }
        else:
            # Cancel task
            task = self.tasks[task_id]
            task["state"] = "CANCELLED"
            
            a2a_response = {
                "jsonrpc": "2.0",
                "id": a2a_request.get("id"),
                "result": {
                    "id": task["id"],
                    "state": task["state"]
                }
            }
        
        # Send response
        self._send_a2a_response(sender, a2a_response)
    
    def _send_a2a_response(self, receiver: str, a2a_response: Dict[str, Any]) -> bool:
        """Send an A2A response to an agent.
        
        Args:
            receiver: ID of the agent to send the response to
            a2a_response: A2A response to send
            
        Returns:
            True if successful, False otherwise
        """
        # Convert A2A response to MCP message
        mcp_message = MCPMessage(
            sender="a2a_adapter",
            receiver=receiver,
            message_type="a2a_response",
            content=a2a_response
        )
        
        # Send the message
        return self.mcp_server.send_message(mcp_message)


class A2ATextArtifact:
    """Helper class for creating A2A text artifacts."""
    
    @staticmethod
    def create(text: str, name: str = None, description: str = None) -> Dict[str, Any]:
        """Create an A2A text artifact.
        
        Args:
            text: Text content
            name: Artifact name (optional)
            description: Artifact description (optional)
            
        Returns:
            A2A artifact dictionary
        """
        artifact = {
            "parts": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
        
        if name:
            artifact["name"] = name
        
        if description:
            artifact["description"] = description
        
        return artifact


class A2AFileArtifact:
    """Helper class for creating A2A file artifacts."""
    
    @staticmethod
    def create(file_content: bytes, mime_type: str, name: str = None, 
              description: str = None, file_name: str = None) -> Dict[str, Any]:
        """Create an A2A file artifact.
        
        Args:
            file_content: File content as bytes
            mime_type: MIME type of the file
            name: Artifact name (optional)
            description: Artifact description (optional)
            file_name: File name (optional)
            
        Returns:
            A2A artifact dictionary
        """
        import base64
        
        # Encode file content as base64
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        
        file_part = {
            "type": "file",
            "file": {
                "mimeType": mime_type,
                "bytes": encoded_content
            }
        }
        
        if file_name:
            file_part["file"]["name"] = file_name
        
        artifact = {
            "parts": [file_part]
        }
        
        if name:
            artifact["name"] = name
        
        if description:
            artifact["description"] = description
        
        return artifact


class A2ADataArtifact:
    """Helper class for creating A2A data artifacts."""
    
    @staticmethod
    def create(data: Dict[str, Any], name: str = None, description: str = None) -> Dict[str, Any]:
        """Create an A2A data artifact.
        
        Args:
            data: Data content as a dictionary
            name: Artifact name (optional)
            description: Artifact description (optional)
            
        Returns:
            A2A artifact dictionary
        """
        artifact = {
            "parts": [
                {
                    "type": "data",
                    "data": data
                }
            ]
        }
        
        if name:
            artifact["name"] = name
        
        if description:
            artifact["description"] = description
        
        return artifact
