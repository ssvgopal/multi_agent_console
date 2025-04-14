"""
Advanced Debugging and Monitoring for MultiAgentConsole.

This module provides debugging and monitoring capabilities:
- Performance monitoring
- Error tracking
- Logging enhancements
- Debugging tools
"""

import os
import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import threading
import queue
import sqlite3


class PerformanceMonitor:
    """Monitors performance metrics."""
    
    def __init__(self, data_dir: str = "data/performance"):
        """Initialize the performance monitor.
        
        Args:
            data_dir: Directory for storing performance data
        """
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "performance.db")
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Start time for current operation
        self.operation_start_times = {}
        
        logging.info(f"Performance Monitor initialized at {self.db_path}")
    
    def _init_db(self) -> None:
        """Initialize the performance database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT,
            start_time DATETIME,
            end_time DATETIME,
            duration REAL,
            status TEXT,
            metadata TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            metric_type TEXT,
            value REAL,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_operation(self, operation_type: str, metadata: Dict[str, Any] = None) -> str:
        """Start timing an operation.
        
        Args:
            operation_type: Type of operation
            metadata: Additional metadata
            
        Returns:
            Operation ID
        """
        operation_id = f"{operation_type}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.operation_start_times[operation_id] = {
            "start_time": datetime.now(),
            "operation_type": operation_type,
            "metadata": metadata or {}
        }
        return operation_id
    
    def end_operation(self, operation_id: str, status: str = "completed") -> float:
        """End timing an operation and record it.
        
        Args:
            operation_id: Operation ID returned by start_operation
            status: Operation status (completed, failed, etc.)
            
        Returns:
            Duration in seconds
        """
        if operation_id not in self.operation_start_times:
            logging.warning(f"Operation {operation_id} not found")
            return 0.0
        
        end_time = datetime.now()
        start_data = self.operation_start_times.pop(operation_id)
        start_time = start_data["start_time"]
        operation_type = start_data["operation_type"]
        metadata = start_data["metadata"]
        
        duration = (end_time - start_time).total_seconds()
        
        # Record in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO operations (operation_type, start_time, end_time, duration, status, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (
                operation_type,
                start_time.isoformat(),
                end_time.isoformat(),
                duration,
                status,
                json.dumps(metadata)
            )
        )
        
        conn.commit()
        conn.close()
        
        return duration
    
    def record_metric(self, metric_type: str, value: float, metadata: Dict[str, Any] = None) -> None:
        """Record a performance metric.
        
        Args:
            metric_type: Type of metric
            value: Metric value
            metadata: Additional metadata
        """
        timestamp = datetime.now()
        
        # Record in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO metrics (timestamp, metric_type, value, metadata) VALUES (?, ?, ?, ?)",
            (
                timestamp.isoformat(),
                metric_type,
                value,
                json.dumps(metadata or {})
            )
        )
        
        conn.commit()
        conn.close()
    
    def get_operation_stats(self, operation_type: Optional[str] = None, 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics for operations.
        
        Args:
            operation_type: Filter by operation type
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Dictionary with operation statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT operation_type, duration, status FROM operations WHERE 1=1"
        params = []
        
        if operation_type:
            query += " AND operation_type = ?"
            params.append(operation_type)
        
        if start_time:
            query += " AND start_time >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND end_time <= ?"
            params.append(end_time.isoformat())
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Calculate statistics
        stats = {}
        for row in rows:
            op_type, duration, status = row
            
            if op_type not in stats:
                stats[op_type] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "min_duration": float('inf'),
                    "max_duration": 0.0,
                    "status_counts": {}
                }
            
            stats[op_type]["count"] += 1
            stats[op_type]["total_duration"] += duration
            stats[op_type]["min_duration"] = min(stats[op_type]["min_duration"], duration)
            stats[op_type]["max_duration"] = max(stats[op_type]["max_duration"], duration)
            
            if status not in stats[op_type]["status_counts"]:
                stats[op_type]["status_counts"][status] = 0
            stats[op_type]["status_counts"][status] += 1
        
        # Calculate averages
        for op_type in stats:
            if stats[op_type]["count"] > 0:
                stats[op_type]["avg_duration"] = stats[op_type]["total_duration"] / stats[op_type]["count"]
            
            # Fix min_duration if no operations were recorded
            if stats[op_type]["min_duration"] == float('inf'):
                stats[op_type]["min_duration"] = 0.0
        
        conn.close()
        
        return stats
    
    def get_metric_stats(self, metric_type: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics for metrics.
        
        Args:
            metric_type: Filter by metric type
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Dictionary with metric statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT metric_type, value FROM metrics WHERE 1=1"
        params = []
        
        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Calculate statistics
        stats = {}
        for row in rows:
            m_type, value = row
            
            if m_type not in stats:
                stats[m_type] = {
                    "count": 0,
                    "total": 0.0,
                    "min": float('inf'),
                    "max": 0.0
                }
            
            stats[m_type]["count"] += 1
            stats[m_type]["total"] += value
            stats[m_type]["min"] = min(stats[m_type]["min"], value)
            stats[m_type]["max"] = max(stats[m_type]["max"], value)
        
        # Calculate averages
        for m_type in stats:
            if stats[m_type]["count"] > 0:
                stats[m_type]["avg"] = stats[m_type]["total"] / stats[m_type]["count"]
            
            # Fix min if no metrics were recorded
            if stats[m_type]["min"] == float('inf'):
                stats[m_type]["min"] = 0.0
        
        conn.close()
        
        return stats


class ErrorTracker:
    """Tracks and analyzes errors."""
    
    def __init__(self, data_dir: str = "data/errors"):
        """Initialize the error tracker.
        
        Args:
            data_dir: Directory for storing error data
        """
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "errors.db")
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        logging.info(f"Error Tracker initialized at {self.db_path}")
    
    def _init_db(self) -> None:
        """Initialize the error database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            error_type TEXT,
            message TEXT,
            traceback TEXT,
            component TEXT,
            severity TEXT,
            metadata TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_error(self, error_type: str, message: str, component: str = None,
                    severity: str = "error", metadata: Dict[str, Any] = None) -> int:
        """Record an error.
        
        Args:
            error_type: Type of error
            message: Error message
            component: Component where the error occurred
            severity: Error severity (debug, info, warning, error, critical)
            metadata: Additional metadata
            
        Returns:
            Error ID
        """
        timestamp = datetime.now()
        tb = traceback.format_exc() if traceback.format_exc() != "NoneType: None\n" else None
        
        # Record in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO errors (timestamp, error_type, message, traceback, component, severity, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                timestamp.isoformat(),
                error_type,
                message,
                tb,
                component,
                severity,
                json.dumps(metadata or {})
            )
        )
        
        error_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return error_id
    
    def get_errors(self, error_type: Optional[str] = None, component: Optional[str] = None,
                 severity: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recorded errors.
        
        Args:
            error_type: Filter by error type
            component: Filter by component
            severity: Filter by severity
            limit: Maximum number of errors to return
            
        Returns:
            List of errors
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, timestamp, error_type, message, traceback, component, severity, metadata FROM errors WHERE 1=1"
        params = []
        
        if error_type:
            query += " AND error_type = ?"
            params.append(error_type)
        
        if component:
            query += " AND component = ?"
            params.append(component)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        errors = []
        for row in rows:
            error_id, timestamp, error_type, message, traceback, component, severity, metadata = row
            errors.append({
                "id": error_id,
                "timestamp": timestamp,
                "error_type": error_type,
                "message": message,
                "traceback": traceback,
                "component": component,
                "severity": severity,
                "metadata": json.loads(metadata) if metadata else {}
            })
        
        conn.close()
        
        return errors
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM errors")
        total_count = cursor.fetchone()[0]
        
        # Get counts by type
        cursor.execute("SELECT error_type, COUNT(*) FROM errors GROUP BY error_type")
        type_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get counts by component
        cursor.execute("SELECT component, COUNT(*) FROM errors GROUP BY component")
        component_counts = {row[0] or "Unknown": row[1] for row in cursor.fetchall()}
        
        # Get counts by severity
        cursor.execute("SELECT severity, COUNT(*) FROM errors GROUP BY severity")
        severity_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get recent errors
        cursor.execute(
            "SELECT id, timestamp, error_type, message, component, severity FROM errors ORDER BY timestamp DESC LIMIT 5"
        )
        recent_errors = []
        for row in cursor.fetchall():
            error_id, timestamp, error_type, message, component, severity = row
            recent_errors.append({
                "id": error_id,
                "timestamp": timestamp,
                "error_type": error_type,
                "message": message,
                "component": component or "Unknown",
                "severity": severity
            })
        
        conn.close()
        
        return {
            "total_count": total_count,
            "type_counts": type_counts,
            "component_counts": component_counts,
            "severity_counts": severity_counts,
            "recent_errors": recent_errors
        }


class LogEnhancer:
    """Enhances logging capabilities."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the log enhancer.
        
        Args:
            log_dir: Directory for storing logs
        """
        self.log_dir = log_dir
        
        # Create directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        self._configure_logging()
        
        logging.info("Log Enhancer initialized")
    
    def _configure_logging(self) -> None:
        """Configure enhanced logging."""
        # Create a formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create a file handler for each log level
        levels = [
            (logging.DEBUG, "debug.log"),
            (logging.INFO, "info.log"),
            (logging.WARNING, "warning.log"),
            (logging.ERROR, "error.log"),
            (logging.CRITICAL, "critical.log")
        ]
        
        for level, filename in levels:
            handler = logging.FileHandler(os.path.join(self.log_dir, filename))
            handler.setLevel(level)
            handler.setFormatter(formatter)
            
            # Add a filter to only include records at this level
            def filter_level(record, level=level):
                return record.levelno == level
            
            handler.addFilter(filter_level)
            logging.getLogger().addHandler(handler)
    
    def get_logs(self, level: str = "info", limit: int = 100) -> List[str]:
        """Get logs from a specific log file.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            limit: Maximum number of log lines to return
            
        Returns:
            List of log lines
        """
        level_map = {
            "debug": "debug.log",
            "info": "info.log",
            "warning": "warning.log",
            "error": "error.log",
            "critical": "critical.log"
        }
        
        if level not in level_map:
            return [f"Invalid log level: {level}"]
        
        log_file = os.path.join(self.log_dir, level_map[level])
        
        if not os.path.exists(log_file):
            return [f"Log file not found: {log_file}"]
        
        # Read the last 'limit' lines from the log file
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                return lines[-limit:]
        except Exception as e:
            return [f"Error reading log file: {str(e)}"]
    
    def clear_logs(self) -> None:
        """Clear all log files."""
        for filename in os.listdir(self.log_dir):
            if filename.endswith(".log"):
                try:
                    os.remove(os.path.join(self.log_dir, filename))
                except Exception as e:
                    logging.error(f"Error clearing log file {filename}: {e}")


class DebugTools:
    """Provides debugging tools."""
    
    def __init__(self):
        """Initialize the debug tools."""
        self.debug_mode = False
        self.breakpoints = {}
        self.watches = {}
        
        logging.info("Debug Tools initialized")
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Set debug mode.
        
        Args:
            enabled: Whether debug mode is enabled
        """
        self.debug_mode = enabled
        logging.info(f"Debug mode {'enabled' if enabled else 'disabled'}")
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled.
        
        Returns:
            True if debug mode is enabled, False otherwise
        """
        return self.debug_mode
    
    def add_breakpoint(self, component: str, condition: str = None) -> str:
        """Add a breakpoint.
        
        Args:
            component: Component to break on
            condition: Optional condition for the breakpoint
            
        Returns:
            Breakpoint ID
        """
        breakpoint_id = f"bp_{len(self.breakpoints) + 1}"
        self.breakpoints[breakpoint_id] = {
            "component": component,
            "condition": condition,
            "enabled": True
        }
        logging.info(f"Added breakpoint {breakpoint_id} for component {component}")
        return breakpoint_id
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """Remove a breakpoint.
        
        Args:
            breakpoint_id: Breakpoint ID
            
        Returns:
            True if successful, False otherwise
        """
        if breakpoint_id in self.breakpoints:
            del self.breakpoints[breakpoint_id]
            logging.info(f"Removed breakpoint {breakpoint_id}")
            return True
        return False
    
    def list_breakpoints(self) -> Dict[str, Dict[str, Any]]:
        """List all breakpoints.
        
        Returns:
            Dictionary of breakpoints
        """
        return self.breakpoints
    
    def add_watch(self, variable: str, component: str = None) -> str:
        """Add a watch for a variable.
        
        Args:
            variable: Variable to watch
            component: Optional component to restrict the watch
            
        Returns:
            Watch ID
        """
        watch_id = f"watch_{len(self.watches) + 1}"
        self.watches[watch_id] = {
            "variable": variable,
            "component": component,
            "enabled": True,
            "values": []
        }
        logging.info(f"Added watch {watch_id} for variable {variable}")
        return watch_id
    
    def remove_watch(self, watch_id: str) -> bool:
        """Remove a watch.
        
        Args:
            watch_id: Watch ID
            
        Returns:
            True if successful, False otherwise
        """
        if watch_id in self.watches:
            del self.watches[watch_id]
            logging.info(f"Removed watch {watch_id}")
            return True
        return False
    
    def list_watches(self) -> Dict[str, Dict[str, Any]]:
        """List all watches.
        
        Returns:
            Dictionary of watches
        """
        return self.watches
    
    def update_watch(self, watch_id: str, value: Any, timestamp: datetime = None) -> None:
        """Update a watch with a new value.
        
        Args:
            watch_id: Watch ID
            value: New value
            timestamp: Optional timestamp (default: now)
        """
        if watch_id in self.watches and self.watches[watch_id]["enabled"]:
            if timestamp is None:
                timestamp = datetime.now()
            
            self.watches[watch_id]["values"].append({
                "timestamp": timestamp.isoformat(),
                "value": str(value)
            })
    
    def get_watch_values(self, watch_id: str) -> List[Dict[str, Any]]:
        """Get values for a watch.
        
        Args:
            watch_id: Watch ID
            
        Returns:
            List of values
        """
        if watch_id in self.watches:
            return self.watches[watch_id]["values"]
        return []
    
    def check_breakpoint(self, component: str, locals_dict: Dict[str, Any] = None) -> Optional[str]:
        """Check if a breakpoint should be triggered.
        
        Args:
            component: Current component
            locals_dict: Local variables
            
        Returns:
            Breakpoint ID if triggered, None otherwise
        """
        if not self.debug_mode:
            return None
        
        for bp_id, bp in self.breakpoints.items():
            if not bp["enabled"]:
                continue
            
            if bp["component"] != component:
                continue
            
            if bp["condition"] and locals_dict:
                try:
                    # Evaluate the condition in the context of locals_dict
                    if not eval(bp["condition"], {"__builtins__": {}}, locals_dict):
                        continue
                except Exception:
                    # If condition evaluation fails, skip this breakpoint
                    continue
            
            return bp_id
        
        return None


class DebuggingManager:
    """Manages debugging and monitoring capabilities."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the debugging manager.
        
        Args:
            data_dir: Base directory for debugging data
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize components
        self.performance_monitor = PerformanceMonitor(os.path.join(data_dir, "performance"))
        self.error_tracker = ErrorTracker(os.path.join(data_dir, "errors"))
        self.log_enhancer = LogEnhancer(os.path.join(data_dir, "logs"))
        self.debug_tools = DebugTools()
        
        logging.info("Debugging Manager initialized")
    
    def start_operation_timer(self, operation_type: str, metadata: Dict[str, Any] = None) -> str:
        """Start timing an operation.
        
        Args:
            operation_type: Type of operation
            metadata: Additional metadata
            
        Returns:
            Operation ID
        """
        return self.performance_monitor.start_operation(operation_type, metadata)
    
    def end_operation_timer(self, operation_id: str, status: str = "completed") -> float:
        """End timing an operation.
        
        Args:
            operation_id: Operation ID
            status: Operation status
            
        Returns:
            Duration in seconds
        """
        return self.performance_monitor.end_operation(operation_id, status)
    
    def record_error(self, error_type: str, message: str, component: str = None,
                    severity: str = "error", metadata: Dict[str, Any] = None) -> int:
        """Record an error.
        
        Args:
            error_type: Type of error
            message: Error message
            component: Component where the error occurred
            severity: Error severity
            metadata: Additional metadata
            
        Returns:
            Error ID
        """
        return self.error_tracker.record_error(error_type, message, component, severity, metadata)
    
    def get_performance_stats(self, operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics.
        
        Args:
            operation_type: Filter by operation type
            
        Returns:
            Dictionary with performance statistics
        """
        return self.performance_monitor.get_operation_stats(operation_type)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        return self.error_tracker.get_error_stats()
    
    def get_logs(self, level: str = "info", limit: int = 100) -> List[str]:
        """Get logs.
        
        Args:
            level: Log level
            limit: Maximum number of log lines
            
        Returns:
            List of log lines
        """
        return self.log_enhancer.get_logs(level, limit)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Set debug mode.
        
        Args:
            enabled: Whether debug mode is enabled
        """
        self.debug_tools.set_debug_mode(enabled)
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled.
        
        Returns:
            True if debug mode is enabled, False otherwise
        """
        return self.debug_tools.is_debug_mode()
    
    def add_breakpoint(self, component: str, condition: str = None) -> str:
        """Add a breakpoint.
        
        Args:
            component: Component to break on
            condition: Optional condition
            
        Returns:
            Breakpoint ID
        """
        return self.debug_tools.add_breakpoint(component, condition)
    
    def list_breakpoints(self) -> Dict[str, Dict[str, Any]]:
        """List all breakpoints.
        
        Returns:
            Dictionary of breakpoints
        """
        return self.debug_tools.list_breakpoints()
    
    def add_watch(self, variable: str, component: str = None) -> str:
        """Add a watch.
        
        Args:
            variable: Variable to watch
            component: Optional component
            
        Returns:
            Watch ID
        """
        return self.debug_tools.add_watch(variable, component)
    
    def list_watches(self) -> Dict[str, Dict[str, Any]]:
        """List all watches.
        
        Returns:
            Dictionary of watches
        """
        return self.debug_tools.list_watches()
    
    def get_debug_status(self) -> Dict[str, Any]:
        """Get the status of debugging tools.
        
        Returns:
            Dictionary with status information
        """
        return {
            "debug_mode": self.debug_tools.is_debug_mode(),
            "breakpoints": len(self.debug_tools.list_breakpoints()),
            "watches": len(self.debug_tools.list_watches()),
            "error_count": self.error_tracker.get_error_stats()["total_count"],
            "performance_metrics": len(self.performance_monitor.get_operation_stats())
        }
