"""
Tests for the monitoring module.
"""

import os
import unittest
import tempfile
import shutil
import json
import time
import logging
import threading
from pathlib import Path

from multi_agent_console.monitoring import (
    setup_logging,
    get_logger,
    log_metrics,
    shutdown_logging,
    setup_performance_monitoring,
    get_performance_metrics,
    monitor,
    setup_debugging,
    get_debugger,
    debug,
    setup_error_tracking,
    get_error_tracker,
    track_error
)


class TestLogging(unittest.TestCase):
    """Test the logging module."""

    def setUp(self):
        """Set up the test."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "logs")

        # Set up logging
        self.log_manager = setup_logging(
            log_dir=self.log_dir,
            console_level="DEBUG",
            file_level="DEBUG",
            json_format=False,
            capture_stdout=False,
            capture_stderr=False,
            system_info=False
        )

    def tearDown(self):
        """Clean up after the test."""
        shutdown_logging()
        shutil.rmtree(self.temp_dir)

    def test_get_logger(self):
        """Test getting a logger."""
        logger = get_logger("test")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test")

    def test_log_messages(self):
        """Test logging messages."""
        logger = get_logger("test")

        # Log messages
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Check log files
        log_file = os.path.join(self.log_dir, "multi_agent_console.log")
        self.assertTrue(os.path.exists(log_file))

        error_log_file = os.path.join(self.log_dir, "errors.log")
        self.assertTrue(os.path.exists(error_log_file))

        # Check log content
        with open(log_file, "r") as f:
            content = f.read()
            self.assertIn("Debug message", content)
            self.assertIn("Info message", content)
            self.assertIn("Warning message", content)
            self.assertIn("Error message", content)
            self.assertIn("Critical message", content)

        with open(error_log_file, "r") as f:
            content = f.read()
            self.assertIn("Error message", content)
            self.assertIn("Critical message", content)
            self.assertNotIn("Debug message", content)
            self.assertNotIn("Info message", content)

    def test_log_metrics(self):
        """Test logging metrics."""
        metrics = {
            "cpu_usage": 10.5,
            "memory_usage": 256.0,
            "requests_per_second": 42
        }

        log_metrics(metrics, "performance")

        # Check log file
        log_file = os.path.join(self.log_dir, "multi_agent_console.log")
        with open(log_file, "r") as f:
            content = f.read()
            self.assertIn("performance", content)
            self.assertIn("cpu_usage=10.5", content)
            self.assertIn("memory_usage=256.0", content)
            self.assertIn("requests_per_second=42", content)


class TestPerformanceMonitoring(unittest.TestCase):
    """Test the performance monitoring module."""

    def setUp(self):
        """Set up the test."""
        # Set up performance monitoring
        self.performance_metrics = setup_performance_monitoring(
            collect_interval=1,
            history_size=10,
            auto_start=False
        )

    def tearDown(self):
        """Clean up after the test."""
        if self.performance_metrics.running:
            self.performance_metrics.stop()

    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        metrics = get_performance_metrics()
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics, self.performance_metrics)

    def test_collect_metrics(self):
        """Test collecting metrics."""
        metrics = self.performance_metrics.collect_metrics()
        self.assertIsNotNone(metrics)
        self.assertIn("timestamp", metrics)
        self.assertIn("uptime_seconds", metrics)
        self.assertIn("process", metrics)
        self.assertIn("system", metrics)

        # Check process metrics
        self.assertIn("cpu_percent", metrics["process"])
        self.assertIn("memory_percent", metrics["process"])
        self.assertIn("num_threads", metrics["process"])

        # Check system metrics
        self.assertIn("cpu_percent", metrics["system"])
        self.assertIn("memory_percent", metrics["system"])
        self.assertIn("memory_available_mb", metrics["system"])
        self.assertIn("disk_percent", metrics["system"])
        self.assertIn("disk_free_gb", metrics["system"])

    def test_start_stop_collection(self):
        """Test starting and stopping metrics collection."""
        # Start collection
        self.performance_metrics.start()
        self.assertTrue(self.performance_metrics.running)

        # Wait for metrics to be collected
        time.sleep(1.5)

        # Check metrics history
        self.assertGreater(len(self.performance_metrics.metrics_history), 0)

        # Stop collection
        self.performance_metrics.stop()
        self.assertFalse(self.performance_metrics.running)

        # Check that collection has stopped
        history_length = len(self.performance_metrics.metrics_history)
        time.sleep(1.5)
        self.assertEqual(len(self.performance_metrics.metrics_history), history_length)

    def test_monitor_decorator(self):
        """Test the monitor decorator."""
        @monitor
        def test_function():
            time.sleep(0.1)
            return "result"

        @monitor(name="custom_name")
        def test_function_with_custom_name():
            time.sleep(0.1)
            return "result"

        # Call the functions
        result1 = test_function()
        result2 = test_function_with_custom_name()

        # Check results
        self.assertEqual(result1, "result")
        self.assertEqual(result2, "result")

        # Check function metrics
        function_metrics = self.performance_metrics.get_function_metrics()
        # Get the key that contains 'test_function'
        test_function_key = next((k for k in function_metrics.keys() if 'test_function' in k), None)
        self.assertIsNotNone(test_function_key)
        self.assertIn("custom_name", function_metrics)

        # Check metrics details
        metrics1 = function_metrics[test_function_key]
        self.assertEqual(metrics1["calls"], 1)
        self.assertGreaterEqual(metrics1["total_time"], 0.1)
        self.assertEqual(metrics1["success_count"], 1)
        self.assertEqual(metrics1["error_count"], 0)

        metrics2 = function_metrics["custom_name"]
        self.assertEqual(metrics2["calls"], 1)
        self.assertGreaterEqual(metrics2["total_time"], 0.1)
        self.assertEqual(metrics2["success_count"], 1)
        self.assertEqual(metrics2["error_count"], 0)

    def test_monitor_decorator_with_exception(self):
        """Test the monitor decorator with an exception."""
        @monitor
        def test_function_with_exception():
            time.sleep(0.1)
            raise ValueError("Test exception")

        # Call the function
        try:
            test_function_with_exception()
        except ValueError:
            pass

        # Check function metrics
        function_metrics = self.performance_metrics.get_function_metrics()
        # Get the key that contains 'test_function_with_exception'
        exception_function_key = next((k for k in function_metrics.keys() if 'test_function_with_exception' in k), None)
        self.assertIsNotNone(exception_function_key)

        # Check metrics details
        metrics = function_metrics[exception_function_key]
        self.assertEqual(metrics["calls"], 1)
        self.assertGreaterEqual(metrics["total_time"], 0.1)
        self.assertEqual(metrics["success_count"], 0)
        self.assertEqual(metrics["error_count"], 1)


class TestDebugging(unittest.TestCase):
    """Test the debugging module."""

    def setUp(self):
        """Set up the test."""
        # Set up debugging
        self.debugger = setup_debugging(debug_mode=False)

    def test_get_debugger(self):
        """Test getting the debugger."""
        debugger = get_debugger()
        self.assertIsNotNone(debugger)
        self.assertEqual(debugger, self.debugger)

    def test_breakpoints(self):
        """Test setting and clearing breakpoints."""
        # Set breakpoints
        self.debugger.set_breakpoint("test_file.py", 10)
        self.debugger.set_breakpoint("test_file.py", 20)
        self.debugger.set_breakpoint("another_file.py", 30)

        # Check breakpoints
        self.assertIn("test_file.py", self.debugger.breakpoints)
        self.assertIn("another_file.py", self.debugger.breakpoints)
        self.assertIn(10, self.debugger.breakpoints["test_file.py"])
        self.assertIn(20, self.debugger.breakpoints["test_file.py"])
        self.assertIn(30, self.debugger.breakpoints["another_file.py"])

        # Clear a breakpoint
        self.debugger.clear_breakpoint("test_file.py", 10)
        self.assertNotIn(10, self.debugger.breakpoints["test_file.py"])
        self.assertIn(20, self.debugger.breakpoints["test_file.py"])

        # Clear all breakpoints
        self.debugger.clear_all_breakpoints()
        self.assertEqual(self.debugger.breakpoints, {})

    def test_watches(self):
        """Test adding and removing watches."""
        # Add watches
        self.debugger.add_watch("variable1", "global")
        self.debugger.add_watch("variable2", "global")
        self.debugger.add_watch("variable3", "function1")

        # Check watches
        self.assertIn("global", self.debugger.watches)
        self.assertIn("function1", self.debugger.watches)
        self.assertIn("variable1", self.debugger.watches["global"])
        self.assertIn("variable2", self.debugger.watches["global"])
        self.assertIn("variable3", self.debugger.watches["function1"])

        # Remove a watch
        self.debugger.remove_watch("variable1", "global")
        self.assertNotIn("variable1", self.debugger.watches["global"])
        self.assertIn("variable2", self.debugger.watches["global"])

        # Clear all watches
        self.debugger.clear_all_watches()
        self.assertEqual(self.debugger.watches, {})

    def test_debug_mode(self):
        """Test enabling and disabling debug mode."""
        # Check initial state
        self.assertFalse(self.debugger.debug_mode)

        # Enable debug mode
        self.debugger.enable_debug_mode()
        self.assertTrue(self.debugger.debug_mode)

        # Disable debug mode
        self.debugger.disable_debug_mode()
        self.assertFalse(self.debugger.debug_mode)

    def test_debug_decorator(self):
        """Test the debug decorator."""
        # Define a function with the debug decorator
        @debug
        def test_function():
            return "result"

        # Call the function
        result = test_function()

        # Check result
        self.assertEqual(result, "result")


class TestErrorTracking(unittest.TestCase):
    """Test the error tracking module."""

    def setUp(self):
        """Set up the test."""
        # Set up error tracking
        self.error_tracker = setup_error_tracking(
            max_errors=10,
            group_similar=True,
            notify_threshold=2,
            notify_interval=1
        )

    def tearDown(self):
        """Clean up after the test."""
        self.error_tracker.restore()

    def test_get_error_tracker(self):
        """Test getting the error tracker."""
        tracker = get_error_tracker()
        self.assertIsNotNone(tracker)
        self.assertEqual(tracker, self.error_tracker)

    def test_track_error(self):
        """Test tracking an error."""
        # Create an exception
        try:
            raise ValueError("Test error")
        except ValueError as e:
            # Track the error
            self.error_tracker.track_error(
                type(e),
                e,
                e.__traceback__,
                context={"test": "value"}
            )

        # Check errors
        errors = self.error_tracker.get_errors()
        self.assertEqual(len(errors), 1)

        # Check error details
        error = errors[0]
        self.assertEqual(error["type"], "ValueError")
        self.assertEqual(error["message"], "Test error")
        self.assertIn("traceback", error)
        self.assertIn("thread", error)
        self.assertEqual(error["context"], {"test": "value"})

    def test_error_groups(self):
        """Test error grouping."""
        # Create and track similar errors
        for i in range(3):
            try:
                raise ValueError(f"Test error {i}")
            except ValueError as e:
                self.error_tracker.track_error(type(e), e, e.__traceback__)

        # Check error groups
        groups = self.error_tracker.get_error_groups()
        self.assertEqual(len(groups), 1)

        # Check group details
        group_id = list(groups.keys())[0]
        group = groups[group_id]
        self.assertEqual(group["type"], "ValueError")
        self.assertEqual(group["count"], 3)
        self.assertEqual(len(group["occurrences"]), 3)

    def test_error_summary(self):
        """Test error summary."""
        # Create and track different types of errors
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.error_tracker.track_error(type(e), e, e.__traceback__)

        try:
            raise TypeError("Test error")
        except TypeError as e:
            self.error_tracker.track_error(type(e), e, e.__traceback__)

        try:
            raise ValueError("Another test error")
        except ValueError as e:
            self.error_tracker.track_error(type(e), e, e.__traceback__)

        # Get error summary
        summary = self.error_tracker.get_error_summary()

        # Check summary details
        self.assertEqual(summary["total_errors"], 3)
        self.assertEqual(summary["error_types"]["ValueError"], 2)
        self.assertEqual(summary["error_types"]["TypeError"], 1)
        self.assertEqual(summary["error_groups"], 3)

    def test_clear_errors(self):
        """Test clearing errors."""
        # Create and track an error
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.error_tracker.track_error(type(e), e, e.__traceback__)

        # Check that error was tracked
        self.assertEqual(len(self.error_tracker.get_errors()), 1)

        # Clear errors
        self.error_tracker.clear_errors()

        # Check that errors were cleared
        self.assertEqual(len(self.error_tracker.get_errors()), 0)
        self.assertEqual(len(self.error_tracker.get_error_groups()), 0)

    def test_error_handler(self):
        """Test error handlers."""
        # Create a handler
        handler_called = False
        handler_error = None

        def error_handler(error):
            nonlocal handler_called, handler_error
            handler_called = True
            handler_error = error

        # Add the handler
        self.error_tracker.add_error_handler(error_handler)

        # Create and track an error
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.error_tracker.track_error(type(e), e, e.__traceback__)

        # Check that handler was called
        self.assertTrue(handler_called)
        self.assertIsNotNone(handler_error)
        self.assertEqual(handler_error["type"], "ValueError")
        self.assertEqual(handler_error["message"], "Test error")

        # Remove the handler
        self.error_tracker.remove_error_handler(error_handler)

        # Reset handler state
        handler_called = False
        handler_error = None

        # Create and track another error
        try:
            raise ValueError("Another test error")
        except ValueError as e:
            self.error_tracker.track_error(type(e), e, e.__traceback__)

        # Check that handler was not called
        self.assertFalse(handler_called)
        self.assertIsNone(handler_error)


if __name__ == "__main__":
    unittest.main()
