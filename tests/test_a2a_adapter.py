"""Test the A2A adapter module."""

import unittest
import json
import uuid
from unittest.mock import MagicMock, patch

from multi_agent_console.a2a_adapter import (
    A2AAdapter, A2ATextArtifact, A2AFileArtifact, A2ADataArtifact
)
from multi_agent_console.mcp_server import MCPServer, MCPMessage, MCPAgent


class TestA2AAdapter(unittest.TestCase):
    """Test the A2AAdapter class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a mock MCP server
        self.mcp_server = MagicMock(spec=MCPServer)
        
        # Create an A2A adapter with the mock server
        self.a2a_adapter = A2AAdapter(self.mcp_server)

    def test_init(self):
        """Test initializing an A2A adapter."""
        # Check that the MCP server was set
        self.assertEqual(self.a2a_adapter.mcp_server, self.mcp_server)
        
        # Check that the tasks dictionary was initialized
        self.assertEqual(self.a2a_adapter.tasks, {})
        
        # Check that the message handlers were registered
        self.mcp_server.register_handler.assert_any_call("a2a_request", self.a2a_adapter._handle_a2a_request)
        self.mcp_server.register_handler.assert_any_call("a2a_response", self.a2a_adapter._handle_a2a_response)

    def test_register_a2a_agent(self):
        """Test registering an A2A-compatible agent."""
        # Set up the mock server to return True for register_agent
        self.mcp_server.register_agent.return_value = True
        
        # Register an agent
        result = self.a2a_adapter.register_a2a_agent("test_agent", "Test Agent")
        
        # Check that the result is True
        self.assertTrue(result)
        
        # Check that register_agent was called with the correct parameters
        self.mcp_server.register_agent.assert_called_once()
        agent = self.mcp_server.register_agent.call_args[0][0]
        self.assertEqual(agent.agent_id, "test_agent")
        self.assertEqual(agent.name, "Test Agent")
        self.assertIn("a2a", agent.capabilities)

    def test_register_a2a_agent_with_capabilities(self):
        """Test registering an A2A-compatible agent with capabilities."""
        # Set up the mock server to return True for register_agent
        self.mcp_server.register_agent.return_value = True
        
        # Register an agent with capabilities
        result = self.a2a_adapter.register_a2a_agent(
            "test_agent", "Test Agent", ["text", "file"]
        )
        
        # Check that the result is True
        self.assertTrue(result)
        
        # Check that register_agent was called with the correct parameters
        self.mcp_server.register_agent.assert_called_once()
        agent = self.mcp_server.register_agent.call_args[0][0]
        self.assertEqual(agent.agent_id, "test_agent")
        self.assertEqual(agent.name, "Test Agent")
        self.assertIn("a2a", agent.capabilities)
        self.assertIn("text", agent.capabilities)
        self.assertIn("file", agent.capabilities)

    @patch('uuid.uuid4')
    def test_create_task(self, mock_uuid4):
        """Test creating a new A2A task."""
        # Set up the mock UUID
        mock_uuid = MagicMock()
        mock_uuid.hex = "test_task_id"
        mock_uuid.__str__.return_value = "test_task_id"
        mock_uuid4.return_value = mock_uuid
        
        # Create input artifacts
        input_artifacts = [
            {"name": "Test Artifact", "parts": [{"type": "text", "text": "Test content"}]}
        ]
        
        # Create a task
        task_id = self.a2a_adapter.create_task("test_agent", input_artifacts)
        
        # Check that the task ID was returned
        self.assertEqual(task_id, "test_task_id")
        
        # Check that the task was stored
        self.assertIn("test_task_id", self.a2a_adapter.tasks)
        task = self.a2a_adapter.tasks["test_task_id"]
        self.assertEqual(task["id"], "test_task_id")
        self.assertEqual(task["state"], "PENDING")
        self.assertEqual(task["agent_id"], "test_agent")
        self.assertEqual(task["input_artifacts"], input_artifacts)
        
        # Check that _send_a2a_message was called with the correct parameters
        self.mcp_server.send_message.assert_called_once()
        message = self.mcp_server.send_message.call_args[0][0]
        self.assertEqual(message.sender, "a2a_adapter")
        self.assertEqual(message.receiver, "test_agent")
        self.assertEqual(message.message_type, "a2a_request")
        self.assertEqual(message.content["jsonrpc"], "2.0")
        self.assertEqual(message.content["id"], "test_task_id")
        self.assertEqual(message.content["method"], "tasks/create")
        self.assertEqual(message.content["params"]["input"], input_artifacts)

    def test_get_task(self):
        """Test getting an A2A task by ID."""
        # Create a test task
        test_task = {
            "id": "test_task_id",
            "state": "PENDING",
            "agent_id": "test_agent",
            "input_artifacts": [],
            "output_artifacts": [],
            "created_at": None,
            "updated_at": None
        }
        self.a2a_adapter.tasks["test_task_id"] = test_task
        
        # Get the task
        task = self.a2a_adapter.get_task("test_task_id")
        
        # Check that the task was returned
        self.assertEqual(task, test_task)
        
        # Try to get a non-existent task
        task = self.a2a_adapter.get_task("non_existent_task")
        
        # Check that None was returned
        self.assertIsNone(task)

    def test_cancel_task(self):
        """Test canceling an A2A task."""
        # Create a test task
        test_task = {
            "id": "test_task_id",
            "state": "PENDING",
            "agent_id": "test_agent",
            "input_artifacts": [],
            "output_artifacts": [],
            "created_at": None,
            "updated_at": None
        }
        self.a2a_adapter.tasks["test_task_id"] = test_task
        
        # Cancel the task
        result = self.a2a_adapter.cancel_task("test_task_id")
        
        # Check that the result is True
        self.assertTrue(result)
        
        # Check that the task state was updated
        self.assertEqual(test_task["state"], "CANCELLING")
        
        # Check that _send_a2a_message was called with the correct parameters
        self.mcp_server.send_message.assert_called_once()
        message = self.mcp_server.send_message.call_args[0][0]
        self.assertEqual(message.sender, "a2a_adapter")
        self.assertEqual(message.receiver, "test_agent")
        self.assertEqual(message.message_type, "a2a_request")
        self.assertEqual(message.content["jsonrpc"], "2.0")
        self.assertEqual(message.content["method"], "tasks/cancel")
        self.assertEqual(message.content["params"]["taskId"], "test_task_id")
        
        # Try to cancel a non-existent task
        result = self.a2a_adapter.cancel_task("non_existent_task")
        
        # Check that the result is False
        self.assertFalse(result)

    def test_handle_a2a_request(self):
        """Test handling an A2A request message."""
        # Create a mock message
        message = MCPMessage(
            sender="test_agent",
            receiver="a2a_adapter",
            message_type="a2a_request",
            content={
                "jsonrpc": "2.0",
                "id": "test_request_id",
                "method": "tasks/create",
                "params": {
                    "input": [{"name": "Test Artifact", "parts": [{"type": "text", "text": "Test content"}]}]
                }
            }
        )
        
        # Mock the _handle_create_task method
        self.a2a_adapter._handle_create_task = MagicMock()
        
        # Handle the message
        self.a2a_adapter._handle_a2a_request(message)
        
        # Check that _handle_create_task was called with the correct parameters
        self.a2a_adapter._handle_create_task.assert_called_once_with(
            "test_agent", message.content
        )
        
        # Test with a different method
        message.content["method"] = "tasks/get"
        self.a2a_adapter._handle_get_task = MagicMock()
        
        # Handle the message
        self.a2a_adapter._handle_a2a_request(message)
        
        # Check that _handle_get_task was called with the correct parameters
        self.a2a_adapter._handle_get_task.assert_called_once_with(
            "test_agent", message.content
        )
        
        # Test with a different method
        message.content["method"] = "tasks/cancel"
        self.a2a_adapter._handle_cancel_task = MagicMock()
        
        # Handle the message
        self.a2a_adapter._handle_a2a_request(message)
        
        # Check that _handle_cancel_task was called with the correct parameters
        self.a2a_adapter._handle_cancel_task.assert_called_once_with(
            "test_agent", message.content
        )
        
        # Test with an unknown method
        message.content["method"] = "unknown_method"
        
        # Handle the message
        self.a2a_adapter._handle_a2a_request(message)
        
        # Check that no handler was called
        self.a2a_adapter._handle_create_task.assert_called_once()
        self.a2a_adapter._handle_get_task.assert_called_once()
        self.a2a_adapter._handle_cancel_task.assert_called_once()

    def test_handle_a2a_response(self):
        """Test handling an A2A response message."""
        # Create a test task
        test_task = {
            "id": "test_task_id",
            "state": "PENDING",
            "agent_id": "test_agent",
            "input_artifacts": [],
            "output_artifacts": [],
            "created_at": None,
            "updated_at": None
        }
        self.a2a_adapter.tasks["test_task_id"] = test_task
        
        # Create a mock message with a result
        message = MCPMessage(
            sender="test_agent",
            receiver="a2a_adapter",
            message_type="a2a_response",
            content={
                "jsonrpc": "2.0",
                "id": "test_task_id",
                "result": {
                    "state": "COMPLETED",
                    "output": [{"name": "Result", "parts": [{"type": "text", "text": "Result content"}]}]
                }
            }
        )
        
        # Handle the message
        self.a2a_adapter._handle_a2a_response(message)
        
        # Check that the task was updated
        self.assertEqual(test_task["state"], "COMPLETED")
        self.assertEqual(test_task["output_artifacts"], [{"name": "Result", "parts": [{"type": "text", "text": "Result content"}]}])
        
        # Create a mock message with an error
        message.content = {
            "jsonrpc": "2.0",
            "id": "test_task_id",
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        
        # Handle the message
        self.a2a_adapter._handle_a2a_response(message)
        
        # Check that the task was updated
        self.assertEqual(test_task["state"], "ERROR")
        self.assertEqual(test_task["error"], {"code": -32603, "message": "Internal error"})


class TestA2AArtifacts(unittest.TestCase):
    """Test the A2A artifact helper classes."""

    def test_text_artifact(self):
        """Test creating a text artifact."""
        # Create a text artifact
        artifact = A2ATextArtifact.create("Test content", "Test Name", "Test Description")
        
        # Check that the artifact was created correctly
        self.assertEqual(artifact["parts"][0]["type"], "text")
        self.assertEqual(artifact["parts"][0]["text"], "Test content")
        self.assertEqual(artifact["name"], "Test Name")
        self.assertEqual(artifact["description"], "Test Description")
        
        # Create a text artifact without name and description
        artifact = A2ATextArtifact.create("Test content")
        
        # Check that the artifact was created correctly
        self.assertEqual(artifact["parts"][0]["type"], "text")
        self.assertEqual(artifact["parts"][0]["text"], "Test content")
        self.assertNotIn("name", artifact)
        self.assertNotIn("description", artifact)

    @patch('base64.b64encode')
    def test_file_artifact(self, mock_b64encode):
        """Test creating a file artifact."""
        # Mock the base64 encoding
        mock_b64encode.return_value = b"encoded_content"
        
        # Create a file artifact
        file_content = b"Test file content"
        artifact = A2AFileArtifact.create(
            file_content, "text/plain", "Test Name", "Test Description", "test.txt"
        )
        
        # Check that the artifact was created correctly
        self.assertEqual(artifact["parts"][0]["type"], "file")
        self.assertEqual(artifact["parts"][0]["file"]["mimeType"], "text/plain")
        self.assertEqual(artifact["parts"][0]["file"]["bytes"], "encoded_content")
        self.assertEqual(artifact["parts"][0]["file"]["name"], "test.txt")
        self.assertEqual(artifact["name"], "Test Name")
        self.assertEqual(artifact["description"], "Test Description")
        
        # Create a file artifact without name, description, and file name
        artifact = A2AFileArtifact.create(file_content, "text/plain")
        
        # Check that the artifact was created correctly
        self.assertEqual(artifact["parts"][0]["type"], "file")
        self.assertEqual(artifact["parts"][0]["file"]["mimeType"], "text/plain")
        self.assertEqual(artifact["parts"][0]["file"]["bytes"], "encoded_content")
        self.assertNotIn("name", artifact["parts"][0]["file"])
        self.assertNotIn("name", artifact)
        self.assertNotIn("description", artifact)

    def test_data_artifact(self):
        """Test creating a data artifact."""
        # Create a data artifact
        data = {"key": "value", "nested": {"key": "value"}}
        artifact = A2ADataArtifact.create(data, "Test Name", "Test Description")
        
        # Check that the artifact was created correctly
        self.assertEqual(artifact["parts"][0]["type"], "data")
        self.assertEqual(artifact["parts"][0]["data"], data)
        self.assertEqual(artifact["name"], "Test Name")
        self.assertEqual(artifact["description"], "Test Description")
        
        # Create a data artifact without name and description
        artifact = A2ADataArtifact.create(data)
        
        # Check that the artifact was created correctly
        self.assertEqual(artifact["parts"][0]["type"], "data")
        self.assertEqual(artifact["parts"][0]["data"], data)
        self.assertNotIn("name", artifact)
        self.assertNotIn("description", artifact)


if __name__ == "__main__":
    unittest.main()
