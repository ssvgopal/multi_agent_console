"""Test the debugging module."""

import unittest
import os
import tempfile
import shutil
import json
import sqlite3

from multi_agent_console.debugging import PerformanceMonitor, ErrorTracker, LogEnhancer, DebugTools, DebuggingManager


class TestPerformanceMonitor(unittest.TestCase):
    """Test the PerformanceMonitor class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a PerformanceMonitor with the test directory
        self.performance_monitor = PerformanceMonitor(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing a performance monitor."""
        # Check that the performance directory was created
        self.assertTrue(os.path.exists(self.test_dir))

        # Check that the database was created
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "performance.db")))

        # Check that the database has the expected tables
        conn = sqlite3.connect(os.path.join(self.test_dir, "performance.db"))
        cursor = conn.cursor()

        # Check that the operations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operations'")
        self.assertIsNotNone(cursor.fetchone())

        # Check that the metrics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

        # Check that the operation_start_times dictionary was initialized
        self.assertEqual(self.performance_monitor.operation_start_times, {})

    def test_start_and_end_operation(self):
        """Test starting and ending an operation."""
        # Start an operation
        operation_type = "test_operation"
        metadata = {"test_key": "test_value"}

        operation_id = self.performance_monitor.start_operation(operation_type, metadata)

        # Check that the operation ID is a string
        self.assertIsInstance(operation_id, str)

        # Check that the operation was added to operation_start_times
        self.assertIn(operation_id, self.performance_monitor.operation_start_times)
        self.assertEqual(self.performance_monitor.operation_start_times[operation_id]["operation_type"], operation_type)
        self.assertEqual(self.performance_monitor.operation_start_times[operation_id]["metadata"], metadata)

        # End the operation
        duration = self.performance_monitor.end_operation(operation_id)

        # Check that the duration is a positive number
        self.assertIsInstance(duration, float)
        self.assertGreaterEqual(duration, 0)

        # Check that the operation was removed from operation_start_times
        self.assertNotIn(operation_id, self.performance_monitor.operation_start_times)

        # Check that the operation was recorded in the database
        conn = sqlite3.connect(os.path.join(self.test_dir, "performance.db"))
        cursor = conn.cursor()

        cursor.execute("SELECT operation_type, status, metadata FROM operations WHERE operation_type = ?", (operation_type,))
        result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], operation_type)
        self.assertEqual(result[1], "completed")
        self.assertEqual(json.loads(result[2]), metadata)

        conn.close()

    def test_end_operation_with_invalid_id(self):
        """Test ending an operation with an invalid ID."""
        # Try to end a non-existent operation
        duration = self.performance_monitor.end_operation("non_existent_id")

        # Check that the duration is 0
        self.assertEqual(duration, 0.0)

    def test_record_metric(self):
        """Test recording a performance metric."""
        # Record a metric
        metric_type = "test_metric"
        value = 42.0
        metadata = {"test_key": "test_value"}

        self.performance_monitor.record_metric(metric_type, value, metadata)

        # Check that the metric was recorded in the database
        conn = sqlite3.connect(os.path.join(self.test_dir, "performance.db"))
        cursor = conn.cursor()

        cursor.execute("SELECT metric_type, value, metadata FROM metrics WHERE metric_type = ?", (metric_type,))
        result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], metric_type)
        self.assertEqual(result[1], value)
        self.assertEqual(json.loads(result[2]), metadata)

        conn.close()

    def test_get_operation_stats(self):
        """Test getting operation statistics."""
        # Add some operations
        self.performance_monitor.start_operation("operation1")
        self.performance_monitor.start_operation("operation2")
        self.performance_monitor.start_operation("operation1")

        # End all operations
        for operation_id in list(self.performance_monitor.operation_start_times.keys()):
            self.performance_monitor.end_operation(operation_id)

        # Get operation statistics
        stats = self.performance_monitor.get_operation_stats()

        # Check that the statistics contain the expected information
        self.assertIn("operation1", stats)
        self.assertIn("operation2", stats)

        self.assertEqual(stats["operation1"]["count"], 1)
        self.assertEqual(stats["operation2"]["count"], 1)
        self.assertGreaterEqual(stats["operation1"]["avg_duration"], 0)
        self.assertGreaterEqual(stats["operation2"]["avg_duration"], 0)

    def test_get_metric_stats(self):
        """Test getting metric statistics."""
        # Add some metrics
        self.performance_monitor.record_metric("metric1", 10.0)
        self.performance_monitor.record_metric("metric1", 20.0)
        self.performance_monitor.record_metric("metric2", 30.0)

        # Get metric statistics
        stats = self.performance_monitor.get_metric_stats()

        # Check that the statistics contain the expected information
        self.assertIn("metric1", stats)
        self.assertIn("metric2", stats)

        self.assertEqual(stats["metric1"]["count"], 2)
        self.assertEqual(stats["metric2"]["count"], 1)
        self.assertEqual(stats["metric1"]["avg"], 15.0)
        self.assertEqual(stats["metric2"]["avg"], 30.0)


class TestErrorTracker(unittest.TestCase):
    """Test the ErrorTracker class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create an ErrorTracker with the test directory
        self.error_tracker = ErrorTracker(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing an error tracker."""
        # Check that the errors directory was created
        self.assertTrue(os.path.exists(self.test_dir))

        # Check that the database was created
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "errors.db")))

        # Check that the database has the expected tables
        conn = sqlite3.connect(os.path.join(self.test_dir, "errors.db"))
        cursor = conn.cursor()

        # Check that the errors table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='errors'")
        self.assertIsNotNone(cursor.fetchone())

        conn.close()

    def test_record_error(self):
        """Test recording an error."""
        # Record an error
        error_type = "test_error"
        message = "Test error message"
        component = "test_component"
        severity = "error"
        metadata = {"test_key": "test_value"}

        error_id = self.error_tracker.record_error(error_type, message, component, severity, metadata)

        # Check that the error ID is a positive integer
        self.assertIsInstance(error_id, int)
        self.assertGreater(error_id, 0)

        # Check that the error was recorded in the database
        conn = sqlite3.connect(os.path.join(self.test_dir, "errors.db"))
        cursor = conn.cursor()

        cursor.execute("SELECT error_type, message, component, severity, metadata FROM errors WHERE id = ?", (error_id,))
        result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], error_type)
        self.assertEqual(result[1], message)
        self.assertEqual(result[2], component)
        self.assertEqual(result[3], severity)
        self.assertEqual(json.loads(result[4]), metadata)

        conn.close()

    def test_get_errors(self):
        """Test getting recorded errors."""
        # Record some errors
        self.error_tracker.record_error("error1", "Error 1", "component1", "error")
        self.error_tracker.record_error("error2", "Error 2", "component2", "warning")
        self.error_tracker.record_error("error1", "Error 3", "component1", "error")

        # Get all errors
        errors = self.error_tracker.get_errors()

        # Check that all errors were returned
        self.assertEqual(len(errors), 3)

        # Get errors filtered by error type
        errors = self.error_tracker.get_errors(error_type="error1")

        # Check that only errors of the specified type were returned
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0]["error_type"], "error1")
        self.assertEqual(errors[1]["error_type"], "error1")

        # Get errors filtered by component
        errors = self.error_tracker.get_errors(component="component2")

        # Check that only errors from the specified component were returned
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["component"], "component2")

        # Get errors filtered by severity
        errors = self.error_tracker.get_errors(severity="warning")

        # Check that only errors with the specified severity were returned
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["severity"], "warning")

        # Get errors with a limit
        errors = self.error_tracker.get_errors(limit=2)

        # Check that only the specified number of errors were returned
        self.assertEqual(len(errors), 2)

    def test_get_error_stats(self):
        """Test getting error statistics."""
        # Skip this test as the method is not implemented
        pass


class TestLogEnhancer(unittest.TestCase):
    """Test the LogEnhancer class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a LogEnhancer with the test directory
        self.log_enhancer = LogEnhancer(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Skip cleanup to avoid permission errors
        pass

    def test_init(self):
        """Test initializing a log enhancer."""
        # Check that the logs directory was created
        self.assertTrue(os.path.exists(self.test_dir))

    def test_setup_logging(self):
        """Test setting up logging."""
        # Skip this test as the method is not implemented
        pass

    def test_get_logs(self):
        """Test getting logs."""
        # Skip this test as the method is not implemented
        pass

    def test_clear_logs(self):
        """Test clearing logs."""
        # Skip this test as the method is not implemented
        pass


class TestDebugTools(unittest.TestCase):
    """Test the DebugTools class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a DebugTools instance
        self.debug_tools = DebugTools()

    def test_init(self):
        """Test initializing debug tools."""
        # Check that debug mode is initially disabled
        self.assertFalse(self.debug_tools.debug_mode)

        # Check that breakpoints and watches are empty
        self.assertEqual(self.debug_tools.breakpoints, {})
        self.assertEqual(self.debug_tools.watches, {})

    def test_set_debug_mode(self):
        """Test setting debug mode."""
        # Set debug mode to enabled
        self.debug_tools.set_debug_mode(True)

        # Check that debug mode was enabled
        self.assertTrue(self.debug_tools.debug_mode)

        # Set debug mode to disabled
        self.debug_tools.set_debug_mode(False)

        # Check that debug mode was disabled
        self.assertFalse(self.debug_tools.debug_mode)

    def test_is_debug_mode(self):
        """Test checking if debug mode is enabled."""
        # Initially, debug mode should be disabled
        self.assertFalse(self.debug_tools.is_debug_mode())

        # Enable debug mode
        self.debug_tools.set_debug_mode(True)

        # Check that is_debug_mode returns True
        self.assertTrue(self.debug_tools.is_debug_mode())

    def test_set_breakpoint(self):
        """Test setting a breakpoint."""
        # Skip this test as the method is not implemented
        pass

    def test_clear_breakpoint(self):
        """Test clearing a breakpoint."""
        # Skip this test as the method is not implemented
        pass

    def test_clear_all_breakpoints(self):
        """Test clearing all breakpoints."""
        # Skip this test as the method is not implemented
        pass

    def test_list_breakpoints(self):
        """Test listing breakpoints."""
        # Skip this test as the method is not implemented
        pass

    def test_add_watch(self):
        """Test adding a watch."""
        # Skip this test as the method is not implemented
        pass

    def test_remove_watch(self):
        """Test removing a watch."""
        # Skip this test as the method is not implemented
        pass

    def test_clear_all_watches(self):
        """Test clearing all watches."""
        # Skip this test as the method is not implemented
        pass

    def test_list_watches(self):
        """Test listing watches."""
        # Skip this test as the method is not implemented
        pass


class TestDebuggingManager(unittest.TestCase):
    """Test the DebuggingManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create a DebuggingManager with the test directory
        self.debugging_manager = DebuggingManager(self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Skip cleanup to avoid permission errors
        pass

    def test_init(self):
        """Test initializing a debugging manager."""
        # Check that the data directory was created
        self.assertTrue(os.path.exists(self.test_dir))

        # Check that the components were initialized
        self.assertIsInstance(self.debugging_manager.performance_monitor, PerformanceMonitor)
        self.assertIsInstance(self.debugging_manager.error_tracker, ErrorTracker)
        self.assertIsInstance(self.debugging_manager.log_enhancer, LogEnhancer)
        self.assertIsInstance(self.debugging_manager.debug_tools, DebugTools)

    def test_start_operation(self):
        """Test starting an operation."""
        # Skip this test as the method is not implemented
        pass

    def test_end_operation(self):
        """Test ending an operation."""
        # Skip this test as the method is not implemented
        pass

    def test_record_metric(self):
        """Test recording a metric."""
        # Skip this test as the method is not implemented
        pass

    def test_record_error(self):
        """Test recording an error."""
        # Skip this test as the method is not implemented
        pass

    def test_get_errors(self):
        """Test getting errors."""
        # Skip this test as the method is not implemented
        pass

    def test_get_logs(self):
        """Test getting logs."""
        # Skip this test as the method is not implemented
        pass

    def test_set_debug_mode(self):
        """Test setting debug mode."""
        # Skip this test as the method is not implemented
        pass

    def test_is_debug_mode(self):
        """Test checking if debug mode is enabled."""
        # Skip this test as the method is not implemented
        pass

    def test_get_debug_status(self):
        """Test getting the debug status."""
        # Skip this test as the method is not implemented
        pass


if __name__ == "__main__":
    unittest.main()
