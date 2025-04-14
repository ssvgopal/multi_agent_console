"""
Advanced Workflow Features for MultiAgentConsole.

This module provides workflow capabilities:
- Workflow templates for common tasks
- Task scheduling and automation
- Batch processing capabilities
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import threading
import queue


class WorkflowStep:
    """Represents a single step in a workflow."""
    
    def __init__(self, name: str, description: str, action: Callable, params: Dict[str, Any] = None):
        """Initialize a workflow step.
        
        Args:
            name: Name of the step
            description: Description of the step
            action: Function to execute for this step
            params: Parameters for the action
        """
        self.name = name
        self.description = description
        self.action = action
        self.params = params or {}
        self.result = None
        self.status = "pending"  # pending, running, completed, failed
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def execute(self, context: Dict[str, Any] = None) -> Any:
        """Execute the step.
        
        Args:
            context: Execution context with variables from previous steps
            
        Returns:
            Result of the step execution
        """
        context = context or {}
        self.status = "running"
        self.start_time = datetime.now()
        
        try:
            # Prepare parameters with context variables
            params = {}
            for key, value in self.params.items():
                if isinstance(value, str) and value.startswith("$"):
                    var_name = value[1:]
                    if var_name in context:
                        params[key] = context[var_name]
                    else:
                        raise ValueError(f"Context variable '{var_name}' not found")
                else:
                    params[key] = value
            
            # Execute the action
            self.result = self.action(**params)
            self.status = "completed"
            return self.result
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            logging.error(f"Error executing step '{self.name}': {e}")
            raise
        finally:
            self.end_time = datetime.now()
    
    def get_duration(self) -> Optional[float]:
        """Get the duration of the step execution in seconds.
        
        Returns:
            Duration in seconds or None if the step hasn't been executed
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the step to a dictionary.
        
        Returns:
            Dictionary representation of the step
        """
        return {
            "name": self.name,
            "description": self.description,
            "params": self.params,
            "status": self.status,
            "result": str(self.result) if self.result is not None else None,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration()
        }


class Workflow:
    """Represents a workflow with multiple steps."""
    
    def __init__(self, name: str, description: str):
        """Initialize a workflow.
        
        Args:
            name: Name of the workflow
            description: Description of the workflow
        """
        self.name = name
        self.description = description
        self.steps = []
        self.context = {}
        self.status = "pending"  # pending, running, completed, failed, paused
        self.current_step_index = 0
        self.start_time = None
        self.end_time = None
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow.
        
        Args:
            step: Workflow step to add
        """
        self.steps.append(step)
    
    def execute(self) -> Dict[str, Any]:
        """Execute all steps in the workflow.
        
        Returns:
            Execution results
        """
        self.status = "running"
        self.start_time = datetime.now()
        self.current_step_index = 0
        
        try:
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                result = step.execute(self.context)
                self.context[step.name] = result
            
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            logging.error(f"Error executing workflow '{self.name}': {e}")
        finally:
            self.end_time = datetime.now()
        
        return self.get_results()
    
    def execute_step(self, step_index: int) -> Any:
        """Execute a specific step in the workflow.
        
        Args:
            step_index: Index of the step to execute
            
        Returns:
            Result of the step execution
        """
        if step_index < 0 or step_index >= len(self.steps):
            raise ValueError(f"Step index {step_index} out of range")
        
        if self.status not in ["pending", "running", "paused"]:
            raise ValueError(f"Cannot execute step in {self.status} state")
        
        self.status = "running"
        if not self.start_time:
            self.start_time = datetime.now()
        
        step = self.steps[step_index]
        self.current_step_index = step_index
        
        try:
            result = step.execute(self.context)
            self.context[step.name] = result
            
            # If this is the last step, mark the workflow as completed
            if step_index == len(self.steps) - 1:
                self.status = "completed"
                self.end_time = datetime.now()
            
            return result
        except Exception as e:
            self.status = "failed"
            logging.error(f"Error executing step {step_index} in workflow '{self.name}': {e}")
            raise
    
    def pause(self) -> None:
        """Pause the workflow execution."""
        if self.status == "running":
            self.status = "paused"
    
    def resume(self) -> Dict[str, Any]:
        """Resume the workflow execution.
        
        Returns:
            Execution results
        """
        if self.status != "paused":
            raise ValueError(f"Cannot resume workflow in {self.status} state")
        
        self.status = "running"
        
        try:
            for i in range(self.current_step_index + 1, len(self.steps)):
                self.current_step_index = i
                step = self.steps[i]
                result = step.execute(self.context)
                self.context[step.name] = result
            
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            logging.error(f"Error resuming workflow '{self.name}': {e}")
        finally:
            self.end_time = datetime.now()
        
        return self.get_results()
    
    def get_results(self) -> Dict[str, Any]:
        """Get the results of the workflow execution.
        
        Returns:
            Dictionary with execution results
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration()
        }
    
    def get_duration(self) -> Optional[float]:
        """Get the duration of the workflow execution in seconds.
        
        Returns:
            Duration in seconds or None if the workflow hasn't been executed
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the workflow to a dictionary.
        
        Returns:
            Dictionary representation of the workflow
        """
        return {
            "name": self.name,
            "description": self.description,
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "params": step.params
                }
                for step in self.steps
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], action_registry: Dict[str, Callable]) -> 'Workflow':
        """Create a workflow from a dictionary.
        
        Args:
            data: Dictionary representation of the workflow
            action_registry: Registry of available actions
            
        Returns:
            Workflow instance
        """
        workflow = cls(data["name"], data["description"])
        
        for step_data in data["steps"]:
            action_name = step_data.get("action", step_data["name"])
            if action_name not in action_registry:
                raise ValueError(f"Action '{action_name}' not found in registry")
            
            step = WorkflowStep(
                name=step_data["name"],
                description=step_data["description"],
                action=action_registry[action_name],
                params=step_data.get("params", {})
            )
            workflow.add_step(step)
        
        return workflow


class ScheduledTask:
    """Represents a scheduled task."""
    
    def __init__(self, workflow: Workflow, schedule_time: datetime, repeat_interval: Optional[timedelta] = None):
        """Initialize a scheduled task.
        
        Args:
            workflow: Workflow to execute
            schedule_time: Time to execute the workflow
            repeat_interval: Interval to repeat the workflow execution
        """
        self.workflow = workflow
        self.schedule_time = schedule_time
        self.repeat_interval = repeat_interval
        self.last_execution_time = None
        self.next_execution_time = schedule_time
        self.status = "pending"  # pending, running, completed, failed, cancelled
    
    def is_due(self) -> bool:
        """Check if the task is due for execution.
        
        Returns:
            True if the task is due, False otherwise
        """
        return datetime.now() >= self.next_execution_time
    
    def execute(self) -> Dict[str, Any]:
        """Execute the task.
        
        Returns:
            Execution results
        """
        self.status = "running"
        self.last_execution_time = datetime.now()
        
        try:
            results = self.workflow.execute()
            self.status = "completed"
            
            # Update next execution time if repeating
            if self.repeat_interval:
                self.next_execution_time = self.last_execution_time + self.repeat_interval
                self.status = "pending"
            
            return results
        except Exception as e:
            self.status = "failed"
            logging.error(f"Error executing scheduled task for workflow '{self.workflow.name}': {e}")
            raise
    
    def cancel(self) -> None:
        """Cancel the scheduled task."""
        self.status = "cancelled"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the scheduled task to a dictionary.
        
        Returns:
            Dictionary representation of the scheduled task
        """
        return {
            "workflow": self.workflow.to_dict(),
            "schedule_time": self.schedule_time.isoformat(),
            "repeat_interval": self.repeat_interval.total_seconds() if self.repeat_interval else None,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "next_execution_time": self.next_execution_time.isoformat() if self.next_execution_time else None,
            "status": self.status
        }


class BatchProcessor:
    """Processes items in batch."""
    
    def __init__(self, workflow: Workflow, batch_size: int = 10, max_workers: int = 5):
        """Initialize a batch processor.
        
        Args:
            workflow: Workflow to execute for each item
            batch_size: Number of items to process in a batch
            max_workers: Maximum number of worker threads
        """
        self.workflow = workflow
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.results = []
        self.errors = []
        self.status = "pending"  # pending, running, completed, failed, cancelled
    
    def process(self, items: List[Any]) -> Dict[str, Any]:
        """Process items in batch.
        
        Args:
            items: Items to process
            
        Returns:
            Processing results
        """
        self.status = "running"
        self.results = []
        self.errors = []
        
        try:
            # Process items in batches
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i+self.batch_size]
                batch_results = self._process_batch(batch)
                self.results.extend(batch_results)
            
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            logging.error(f"Error processing batch for workflow '{self.workflow.name}': {e}")
            raise
        
        return self.get_results()
    
    def _process_batch(self, batch: List[Any]) -> List[Dict[str, Any]]:
        """Process a batch of items.
        
        Args:
            batch: Batch of items to process
            
        Returns:
            Batch processing results
        """
        results = []
        
        # Create a thread pool
        threads = []
        result_queue = queue.Queue()
        
        # Process items in parallel
        for item in batch:
            if len(threads) >= self.max_workers:
                # Wait for a thread to finish
                thread = threads.pop(0)
                thread.join()
            
            # Create a new thread
            thread = threading.Thread(
                target=self._process_item,
                args=(item, result_queue)
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        
        # Collect results
        while not result_queue.empty():
            results.append(result_queue.get())
        
        return results
    
    def _process_item(self, item: Any, result_queue: queue.Queue) -> None:
        """Process a single item.
        
        Args:
            item: Item to process
            result_queue: Queue to store the result
        """
        try:
            # Create a copy of the workflow
            workflow_copy = Workflow(self.workflow.name, self.workflow.description)
            for step in self.workflow.steps:
                workflow_copy.add_step(WorkflowStep(
                    name=step.name,
                    description=step.description,
                    action=step.action,
                    params=step.params
                ))
            
            # Add the item to the context
            workflow_copy.context["item"] = item
            
            # Execute the workflow
            result = workflow_copy.execute()
            result["item"] = item
            result_queue.put(result)
        except Exception as e:
            error = {
                "item": item,
                "error": str(e)
            }
            self.errors.append(error)
            logging.error(f"Error processing item {item}: {e}")
    
    def get_results(self) -> Dict[str, Any]:
        """Get the results of the batch processing.
        
        Returns:
            Dictionary with processing results
        """
        return {
            "workflow": self.workflow.name,
            "status": self.status,
            "total_items": len(self.results) + len(self.errors),
            "successful_items": len(self.results),
            "failed_items": len(self.errors),
            "results": self.results,
            "errors": self.errors
        }


class WorkflowTemplate:
    """Represents a workflow template."""
    
    def __init__(self, name: str, description: str, steps: List[Dict[str, Any]]):
        """Initialize a workflow template.
        
        Args:
            name: Name of the template
            description: Description of the template
            steps: List of step definitions
        """
        self.name = name
        self.description = description
        self.steps = steps
    
    def create_workflow(self, action_registry: Dict[str, Callable], params: Dict[str, Any] = None) -> Workflow:
        """Create a workflow from the template.
        
        Args:
            action_registry: Registry of available actions
            params: Parameters to customize the workflow
            
        Returns:
            Workflow instance
        """
        params = params or {}
        workflow = Workflow(self.name, self.description)
        
        for step_def in self.steps:
            # Apply parameters
            step_params = step_def.get("params", {}).copy()
            for key, value in step_params.items():
                if isinstance(value, str) and value.startswith("$"):
                    param_name = value[1:]
                    if param_name in params:
                        step_params[key] = params[param_name]
            
            # Create the step
            action_name = step_def.get("action", step_def["name"])
            if action_name not in action_registry:
                raise ValueError(f"Action '{action_name}' not found in registry")
            
            step = WorkflowStep(
                name=step_def["name"],
                description=step_def["description"],
                action=action_registry[action_name],
                params=step_params
            )
            workflow.add_step(step)
        
        return workflow
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the template to a dictionary.
        
        Returns:
            Dictionary representation of the template
        """
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowTemplate':
        """Create a template from a dictionary.
        
        Args:
            data: Dictionary representation of the template
            
        Returns:
            WorkflowTemplate instance
        """
        return cls(
            name=data["name"],
            description=data["description"],
            steps=data["steps"]
        )


class WorkflowManager:
    """Manages workflows, templates, and scheduled tasks."""
    
    def __init__(self, data_dir: str = "data/workflows"):
        """Initialize the workflow manager.
        
        Args:
            data_dir: Directory for storing workflow data
        """
        self.data_dir = data_dir
        self.templates_dir = os.path.join(data_dir, "templates")
        self.workflows_dir = os.path.join(data_dir, "workflows")
        self.scheduled_tasks = []
        self.action_registry = {}
        
        # Create directories if they don't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.workflows_dir, exist_ok=True)
        
        # Start the scheduler thread
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logging.info("Workflow Manager initialized")
    
    def register_action(self, name: str, action: Callable) -> None:
        """Register an action.
        
        Args:
            name: Name of the action
            action: Function to execute
        """
        self.action_registry[name] = action
    
    def create_workflow(self, name: str, description: str) -> Workflow:
        """Create a new workflow.
        
        Args:
            name: Name of the workflow
            description: Description of the workflow
            
        Returns:
            Workflow instance
        """
        return Workflow(name, description)
    
    def save_workflow(self, workflow: Workflow) -> str:
        """Save a workflow.
        
        Args:
            workflow: Workflow to save
            
        Returns:
            Path to the saved workflow
        """
        workflow_data = workflow.to_dict()
        file_path = os.path.join(self.workflows_dir, f"{workflow.name}.json")
        
        with open(file_path, 'w') as f:
            json.dump(workflow_data, f, indent=2)
        
        return file_path
    
    def load_workflow(self, name: str) -> Workflow:
        """Load a workflow.
        
        Args:
            name: Name of the workflow
            
        Returns:
            Workflow instance
        """
        file_path = os.path.join(self.workflows_dir, f"{name}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Workflow '{name}' not found")
        
        with open(file_path, 'r') as f:
            workflow_data = json.load(f)
        
        return Workflow.from_dict(workflow_data, self.action_registry)
    
    def list_workflows(self) -> List[str]:
        """List available workflows.
        
        Returns:
            List of workflow names
        """
        workflows = []
        
        for file_name in os.listdir(self.workflows_dir):
            if file_name.endswith(".json"):
                workflows.append(file_name[:-5])
        
        return workflows
    
    def create_template(self, name: str, description: str, steps: List[Dict[str, Any]]) -> WorkflowTemplate:
        """Create a new workflow template.
        
        Args:
            name: Name of the template
            description: Description of the template
            steps: List of step definitions
            
        Returns:
            WorkflowTemplate instance
        """
        return WorkflowTemplate(name, description, steps)
    
    def save_template(self, template: WorkflowTemplate) -> str:
        """Save a workflow template.
        
        Args:
            template: Template to save
            
        Returns:
            Path to the saved template
        """
        template_data = template.to_dict()
        file_path = os.path.join(self.templates_dir, f"{template.name}.json")
        
        with open(file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        return file_path
    
    def load_template(self, name: str) -> WorkflowTemplate:
        """Load a workflow template.
        
        Args:
            name: Name of the template
            
        Returns:
            WorkflowTemplate instance
        """
        file_path = os.path.join(self.templates_dir, f"{name}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Template '{name}' not found")
        
        with open(file_path, 'r') as f:
            template_data = json.load(f)
        
        return WorkflowTemplate.from_dict(template_data)
    
    def list_templates(self) -> List[str]:
        """List available templates.
        
        Returns:
            List of template names
        """
        templates = []
        
        for file_name in os.listdir(self.templates_dir):
            if file_name.endswith(".json"):
                templates.append(file_name[:-5])
        
        return templates
    
    def schedule_workflow(self, workflow: Workflow, schedule_time: datetime, 
                         repeat_interval: Optional[timedelta] = None) -> ScheduledTask:
        """Schedule a workflow for execution.
        
        Args:
            workflow: Workflow to execute
            schedule_time: Time to execute the workflow
            repeat_interval: Interval to repeat the workflow execution
            
        Returns:
            ScheduledTask instance
        """
        task = ScheduledTask(workflow, schedule_time, repeat_interval)
        self.scheduled_tasks.append(task)
        return task
    
    def cancel_scheduled_task(self, task: ScheduledTask) -> None:
        """Cancel a scheduled task.
        
        Args:
            task: Task to cancel
        """
        task.cancel()
        self.scheduled_tasks.remove(task)
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """List scheduled tasks.
        
        Returns:
            List of scheduled tasks
        """
        return [
            {
                "workflow": task.workflow.name,
                "schedule_time": task.schedule_time.isoformat(),
                "next_execution_time": task.next_execution_time.isoformat() if task.next_execution_time else None,
                "status": task.status
            }
            for task in self.scheduled_tasks
        ]
    
    def create_batch_processor(self, workflow: Workflow, batch_size: int = 10, 
                              max_workers: int = 5) -> BatchProcessor:
        """Create a batch processor.
        
        Args:
            workflow: Workflow to execute for each item
            batch_size: Number of items to process in a batch
            max_workers: Maximum number of worker threads
            
        Returns:
            BatchProcessor instance
        """
        return BatchProcessor(workflow, batch_size, max_workers)
    
    def _scheduler_loop(self) -> None:
        """Scheduler loop to execute scheduled tasks."""
        while self.scheduler_running:
            # Check for due tasks
            for task in self.scheduled_tasks:
                if task.status == "pending" and task.is_due():
                    try:
                        task.execute()
                    except Exception as e:
                        logging.error(f"Error executing scheduled task: {e}")
            
            # Sleep for a short time
            time.sleep(1)
    
    def shutdown(self) -> None:
        """Shut down the workflow manager."""
        self.scheduler_running = False
        if self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        logging.info("Workflow Manager shut down")
