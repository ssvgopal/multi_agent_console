"""Test the workflow module."""

import unittest
import os
import tempfile
import shutil
import json
import time
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta

from multi_agent_console.workflow import (
    WorkflowStep, Workflow, WorkflowTemplate, 
    WorkflowManager, ScheduledTask, BatchProcessor
)


class TestWorkflowStep(unittest.TestCase):
    """Test the WorkflowStep class."""

    def test_init(self):
        """Test initializing a workflow step."""
        # Create a mock action
        action = MagicMock()
        
        # Create a workflow step
        step = WorkflowStep("test_step", "Test step", action, {"param1": "value1"})
        
        # Check that the step was initialized correctly
        self.assertEqual(step.name, "test_step")
        self.assertEqual(step.description, "Test step")
        self.assertEqual(step.action, action)
        self.assertEqual(step.params, {"param1": "value1"})
        self.assertEqual(step.status, "pending")
        self.assertIsNone(step.result)
        self.assertIsNone(step.error)
        self.assertIsNone(step.start_time)
        self.assertIsNone(step.end_time)

    def test_execute(self):
        """Test executing a workflow step."""
        # Create a mock action that returns a result
        action = MagicMock(return_value="test_result")
        
        # Create a workflow step
        step = WorkflowStep("test_step", "Test step", action, {"param1": "value1"})
        
        # Execute the step
        result = step.execute()
        
        # Check that the action was called with the correct parameters
        action.assert_called_once_with(param1="value1")
        
        # Check that the result was returned
        self.assertEqual(result, "test_result")
        
        # Check that the step status was updated
        self.assertEqual(step.status, "completed")
        self.assertEqual(step.result, "test_result")
        self.assertIsNotNone(step.start_time)
        self.assertIsNotNone(step.end_time)

    def test_execute_with_context(self):
        """Test executing a workflow step with context variables."""
        # Create a mock action that returns a result
        action = MagicMock(return_value="test_result")
        
        # Create a workflow step with a context variable reference
        step = WorkflowStep("test_step", "Test step", action, {"param1": "$context_var"})
        
        # Create a context with the variable
        context = {"context_var": "context_value"}
        
        # Execute the step with the context
        result = step.execute(context)
        
        # Check that the action was called with the context variable value
        action.assert_called_once_with(param1="context_value")
        
        # Check that the result was returned
        self.assertEqual(result, "test_result")

    def test_execute_with_missing_context_variable(self):
        """Test executing a workflow step with a missing context variable."""
        # Create a mock action
        action = MagicMock()
        
        # Create a workflow step with a context variable reference
        step = WorkflowStep("test_step", "Test step", action, {"param1": "$missing_var"})
        
        # Create a context without the variable
        context = {"other_var": "value"}
        
        # Execute the step with the context (should raise an exception)
        with self.assertRaises(ValueError):
            step.execute(context)
        
        # Check that the action was not called
        action.assert_not_called()
        
        # Check that the step status was updated
        self.assertEqual(step.status, "failed")
        self.assertIsNotNone(step.error)

    def test_execute_with_exception(self):
        """Test executing a workflow step that raises an exception."""
        # Create a mock action that raises an exception
        action = MagicMock(side_effect=Exception("Test exception"))
        
        # Create a workflow step
        step = WorkflowStep("test_step", "Test step", action)
        
        # Execute the step (should raise an exception)
        with self.assertRaises(Exception):
            step.execute()
        
        # Check that the step status was updated
        self.assertEqual(step.status, "failed")
        self.assertEqual(step.error, "Test exception")
        self.assertIsNotNone(step.start_time)
        self.assertIsNotNone(step.end_time)

    def test_get_duration(self):
        """Test getting the duration of a workflow step execution."""
        # Create a mock action
        action = MagicMock()
        
        # Create a workflow step
        step = WorkflowStep("test_step", "Test step", action)
        
        # Check that the duration is None before execution
        self.assertIsNone(step.get_duration())
        
        # Execute the step
        step.execute()
        
        # Check that the duration is not None after execution
        self.assertIsNotNone(step.get_duration())
        self.assertGreaterEqual(step.get_duration(), 0)

    def test_to_dict(self):
        """Test converting a workflow step to a dictionary."""
        # Create a mock action
        action = MagicMock(return_value="test_result")
        
        # Create a workflow step
        step = WorkflowStep("test_step", "Test step", action, {"param1": "value1"})
        
        # Execute the step
        step.execute()
        
        # Convert to dictionary
        step_dict = step.to_dict()
        
        # Check that the dictionary contains the expected keys
        self.assertIn("name", step_dict)
        self.assertIn("description", step_dict)
        self.assertIn("params", step_dict)
        self.assertIn("status", step_dict)
        self.assertIn("result", step_dict)
        self.assertIn("start_time", step_dict)
        self.assertIn("end_time", step_dict)
        self.assertIn("duration", step_dict)
        
        # Check that the values are correct
        self.assertEqual(step_dict["name"], "test_step")
        self.assertEqual(step_dict["description"], "Test step")
        self.assertEqual(step_dict["params"], {"param1": "value1"})
        self.assertEqual(step_dict["status"], "completed")
        self.assertEqual(step_dict["result"], "test_result")


class TestWorkflow(unittest.TestCase):
    """Test the Workflow class."""

    def setUp(self):
        """Set up the test environment."""
        # Create mock actions
        self.action1 = MagicMock(return_value="result1")
        self.action2 = MagicMock(return_value="result2")
        
        # Create a workflow
        self.workflow = Workflow("test_workflow", "Test workflow")
        
        # Add steps to the workflow
        self.step1 = WorkflowStep("step1", "Step 1", self.action1, {"param1": "value1"})
        self.step2 = WorkflowStep("step2", "Step 2", self.action2, {"param2": "$step1"})
        self.workflow.add_step(self.step1)
        self.workflow.add_step(self.step2)

    def test_init(self):
        """Test initializing a workflow."""
        # Create a workflow
        workflow = Workflow("test_workflow", "Test workflow")
        
        # Check that the workflow was initialized correctly
        self.assertEqual(workflow.name, "test_workflow")
        self.assertEqual(workflow.description, "Test workflow")
        self.assertEqual(workflow.steps, [])
        self.assertEqual(workflow.context, {})
        self.assertEqual(workflow.status, "pending")
        self.assertEqual(workflow.current_step_index, 0)
        self.assertIsNone(workflow.start_time)
        self.assertIsNone(workflow.end_time)

    def test_add_step(self):
        """Test adding a step to a workflow."""
        # Create a workflow
        workflow = Workflow("test_workflow", "Test workflow")
        
        # Create a step
        step = WorkflowStep("test_step", "Test step", MagicMock())
        
        # Add the step to the workflow
        workflow.add_step(step)
        
        # Check that the step was added
        self.assertEqual(len(workflow.steps), 1)
        self.assertEqual(workflow.steps[0], step)

    def test_execute(self):
        """Test executing a workflow."""
        # Execute the workflow
        results = self.workflow.execute()
        
        # Check that the actions were called with the correct parameters
        self.action1.assert_called_once_with(param1="value1")
        self.action2.assert_called_once_with(param2="result1")
        
        # Check that the workflow status was updated
        self.assertEqual(self.workflow.status, "completed")
        self.assertIsNotNone(self.workflow.start_time)
        self.assertIsNotNone(self.workflow.end_time)
        
        # Check that the context was updated
        self.assertEqual(self.workflow.context["step1"], "result1")
        self.assertEqual(self.workflow.context["step2"], "result2")
        
        # Check that the results contain the expected information
        self.assertEqual(results["name"], "test_workflow")
        self.assertEqual(results["status"], "completed")
        self.assertEqual(len(results["steps"]), 2)

    def test_execute_step(self):
        """Test executing a specific step in a workflow."""
        # Execute the first step
        result = self.workflow.execute_step(0)
        
        # Check that the first action was called with the correct parameters
        self.action1.assert_called_once_with(param1="value1")
        
        # Check that the second action was not called
        self.action2.assert_not_called()
        
        # Check that the result was returned
        self.assertEqual(result, "result1")
        
        # Check that the workflow status was updated
        self.assertEqual(self.workflow.status, "running")
        self.assertIsNotNone(self.workflow.start_time)
        self.assertIsNone(self.workflow.end_time)
        
        # Check that the context was updated
        self.assertEqual(self.workflow.context["step1"], "result1")
        self.assertNotIn("step2", self.workflow.context)

    def test_execute_step_out_of_range(self):
        """Test executing a step with an index out of range."""
        # Try to execute a step with an invalid index
        with self.assertRaises(ValueError):
            self.workflow.execute_step(2)

    def test_pause_and_resume(self):
        """Test pausing and resuming a workflow."""
        # Execute the first step
        self.workflow.execute_step(0)
        
        # Pause the workflow
        self.workflow.pause()
        
        # Check that the workflow status was updated
        self.assertEqual(self.workflow.status, "paused")
        
        # Resume the workflow
        results = self.workflow.resume()
        
        # Check that the second action was called with the correct parameters
        self.action2.assert_called_once_with(param2="result1")
        
        # Check that the workflow status was updated
        self.assertEqual(self.workflow.status, "completed")
        self.assertIsNotNone(self.workflow.end_time)
        
        # Check that the context was updated
        self.assertEqual(self.workflow.context["step1"], "result1")
        self.assertEqual(self.workflow.context["step2"], "result2")
        
        # Check that the results contain the expected information
        self.assertEqual(results["name"], "test_workflow")
        self.assertEqual(results["status"], "completed")
        self.assertEqual(len(results["steps"]), 2)

    def test_resume_not_paused(self):
        """Test resuming a workflow that is not paused."""
        # Try to resume a workflow that is not paused
        with self.assertRaises(ValueError):
            self.workflow.resume()

    def test_get_results(self):
        """Test getting the results of a workflow execution."""
        # Execute the workflow
        self.workflow.execute()
        
        # Get the results
        results = self.workflow.get_results()
        
        # Check that the results contain the expected information
        self.assertEqual(results["name"], "test_workflow")
        self.assertEqual(results["description"], "Test workflow")
        self.assertEqual(results["status"], "completed")
        self.assertEqual(len(results["steps"]), 2)
        self.assertIsNotNone(results["start_time"])
        self.assertIsNotNone(results["end_time"])
        self.assertIsNotNone(results["duration"])

    def test_get_duration(self):
        """Test getting the duration of a workflow execution."""
        # Check that the duration is None before execution
        self.assertIsNone(self.workflow.get_duration())
        
        # Execute the workflow
        self.workflow.execute()
        
        # Check that the duration is not None after execution
        self.assertIsNotNone(self.workflow.get_duration())
        self.assertGreaterEqual(self.workflow.get_duration(), 0)

    def test_to_dict(self):
        """Test converting a workflow to a dictionary."""
        # Convert to dictionary
        workflow_dict = self.workflow.to_dict()
        
        # Check that the dictionary contains the expected keys
        self.assertIn("name", workflow_dict)
        self.assertIn("description", workflow_dict)
        self.assertIn("steps", workflow_dict)
        
        # Check that the values are correct
        self.assertEqual(workflow_dict["name"], "test_workflow")
        self.assertEqual(workflow_dict["description"], "Test workflow")
        self.assertEqual(len(workflow_dict["steps"]), 2)
        
        # Check that the steps contain the expected information
        step1_dict = workflow_dict["steps"][0]
        self.assertEqual(step1_dict["name"], "step1")
        self.assertEqual(step1_dict["description"], "Step 1")
        self.assertEqual(step1_dict["params"], {"param1": "value1"})
        
        step2_dict = workflow_dict["steps"][1]
        self.assertEqual(step2_dict["name"], "step2")
        self.assertEqual(step2_dict["description"], "Step 2")
        self.assertEqual(step2_dict["params"], {"param2": "$step1"})

    def test_from_dict(self):
        """Test creating a workflow from a dictionary."""
        # Create a dictionary representation of a workflow
        workflow_dict = {
            "name": "test_workflow",
            "description": "Test workflow",
            "steps": [
                {
                    "name": "step1",
                    "description": "Step 1",
                    "action": "action1",
                    "params": {"param1": "value1"}
                },
                {
                    "name": "step2",
                    "description": "Step 2",
                    "action": "action2",
                    "params": {"param2": "$step1"}
                }
            ]
        }
        
        # Create an action registry
        action_registry = {
            "action1": self.action1,
            "action2": self.action2
        }
        
        # Create a workflow from the dictionary
        workflow = Workflow.from_dict(workflow_dict, action_registry)
        
        # Check that the workflow was created correctly
        self.assertEqual(workflow.name, "test_workflow")
        self.assertEqual(workflow.description, "Test workflow")
        self.assertEqual(len(workflow.steps), 2)
        
        # Check that the steps were created correctly
        step1 = workflow.steps[0]
        self.assertEqual(step1.name, "step1")
        self.assertEqual(step1.description, "Step 1")
        self.assertEqual(step1.action, self.action1)
        self.assertEqual(step1.params, {"param1": "value1"})
        
        step2 = workflow.steps[1]
        self.assertEqual(step2.name, "step2")
        self.assertEqual(step2.description, "Step 2")
        self.assertEqual(step2.action, self.action2)
        self.assertEqual(step2.params, {"param2": "$step1"})


class TestWorkflowTemplate(unittest.TestCase):
    """Test the WorkflowTemplate class."""

    def setUp(self):
        """Set up the test environment."""
        # Create mock actions
        self.action1 = MagicMock(return_value="result1")
        self.action2 = MagicMock(return_value="result2")
        
        # Create a template
        self.template = WorkflowTemplate(
            "test_template",
            "Test template",
            [
                {
                    "name": "step1",
                    "description": "Step 1",
                    "action": "action1",
                    "params": {"param1": "$input1"}
                },
                {
                    "name": "step2",
                    "description": "Step 2",
                    "action": "action2",
                    "params": {"param2": "$step1"}
                }
            ]
        )
        
        # Create an action registry
        self.action_registry = {
            "action1": self.action1,
            "action2": self.action2
        }

    def test_init(self):
        """Test initializing a workflow template."""
        # Check that the template was initialized correctly
        self.assertEqual(self.template.name, "test_template")
        self.assertEqual(self.template.description, "Test template")
        self.assertEqual(len(self.template.steps), 2)

    def test_create_workflow(self):
        """Test creating a workflow from a template."""
        # Create a workflow from the template
        workflow = self.template.create_workflow(
            self.action_registry,
            {"input1": "template_value"}
        )
        
        # Check that the workflow was created correctly
        self.assertEqual(workflow.name, "test_template")
        self.assertEqual(workflow.description, "Test template")
        self.assertEqual(len(workflow.steps), 2)
        
        # Check that the steps were created correctly
        step1 = workflow.steps[0]
        self.assertEqual(step1.name, "step1")
        self.assertEqual(step1.description, "Step 1")
        self.assertEqual(step1.action, self.action1)
        self.assertEqual(step1.params, {"param1": "template_value"})
        
        step2 = workflow.steps[1]
        self.assertEqual(step2.name, "step2")
        self.assertEqual(step2.description, "Step 2")
        self.assertEqual(step2.action, self.action2)
        self.assertEqual(step2.params, {"param2": "$step1"})

    def test_to_dict(self):
        """Test converting a template to a dictionary."""
        # Convert to dictionary
        template_dict = self.template.to_dict()
        
        # Check that the dictionary contains the expected keys
        self.assertIn("name", template_dict)
        self.assertIn("description", template_dict)
        self.assertIn("steps", template_dict)
        
        # Check that the values are correct
        self.assertEqual(template_dict["name"], "test_template")
        self.assertEqual(template_dict["description"], "Test template")
        self.assertEqual(len(template_dict["steps"]), 2)

    def test_from_dict(self):
        """Test creating a template from a dictionary."""
        # Create a dictionary representation of a template
        template_dict = {
            "name": "test_template",
            "description": "Test template",
            "steps": [
                {
                    "name": "step1",
                    "description": "Step 1",
                    "action": "action1",
                    "params": {"param1": "$input1"}
                },
                {
                    "name": "step2",
                    "description": "Step 2",
                    "action": "action2",
                    "params": {"param2": "$step1"}
                }
            ]
        }
        
        # Create a template from the dictionary
        template = WorkflowTemplate.from_dict(template_dict)
        
        # Check that the template was created correctly
        self.assertEqual(template.name, "test_template")
        self.assertEqual(template.description, "Test template")
        self.assertEqual(len(template.steps), 2)
        
        # Check that the steps were created correctly
        step1 = template.steps[0]
        self.assertEqual(step1["name"], "step1")
        self.assertEqual(step1["description"], "Step 1")
        self.assertEqual(step1["action"], "action1")
        self.assertEqual(step1["params"], {"param1": "$input1"})
        
        step2 = template.steps[1]
        self.assertEqual(step2["name"], "step2")
        self.assertEqual(step2["description"], "Step 2")
        self.assertEqual(step2["action"], "action2")
        self.assertEqual(step2["params"], {"param2": "$step1"})


# Add more test classes for ScheduledTask, BatchProcessor, and WorkflowManager as needed

if __name__ == "__main__":
    unittest.main()
