"""
Performance monitoring module for MultiAgentConsole.

This module provides tools for monitoring system and application performance.
"""

import os
import time
import threading
import psutil
import functools
from typing import Dict, Any, List, Callable, Optional, Union
from datetime import datetime

from .logger import get_logger, log_metrics

# Get logger
logger = get_logger("performance")


class PerformanceMetrics:
    """Class for collecting and reporting performance metrics."""
    
    def __init__(
        self,
        collect_interval: int = 60,  # seconds
        history_size: int = 60,  # number of data points to keep
        auto_start: bool = True
    ):
        """Initialize performance metrics collection.
        
        Args:
            collect_interval: Interval in seconds between metrics collection
            history_size: Number of historical data points to keep
            auto_start: Whether to automatically start collection
        """
        self.collect_interval = collect_interval
        self.history_size = history_size
        self.metrics_history: List[Dict[str, Any]] = []
        self.running = False
        self.collection_thread = None
        self.start_time = time.time()
        
        # Function execution metrics
        self.function_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Initialize process
        self.process = psutil.Process(os.getpid())
        
        if auto_start:
            self.start()
    
    def start(self):
        """Start metrics collection."""
        if self.running:
            return
        
        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collect_metrics_loop,
            daemon=True
        )
        self.collection_thread.start()
        logger.info("Performance metrics collection started")
    
    def stop(self):
        """Stop metrics collection."""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
            self.collection_thread = None
        logger.info("Performance metrics collection stopped")
    
    def _collect_metrics_loop(self):
        """Continuously collect metrics at the specified interval."""
        while self.running:
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Trim history if needed
                if len(self.metrics_history) > self.history_size:
                    self.metrics_history = self.metrics_history[-self.history_size:]
                
                # Log metrics
                log_metrics(metrics)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            # Sleep until next collection
            time.sleep(self.collect_interval)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics.
        
        Returns:
            Dictionary of metrics
        """
        # Get process info
        process_info = self.process.as_dict(
            attrs=['cpu_percent', 'memory_percent', 'num_threads', 'io_counters']
        )
        
        # Get system info
        system_cpu = psutil.cpu_percent(interval=0.1)
        system_memory = psutil.virtual_memory()
        system_disk = psutil.disk_usage('/')
        
        # Collect metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "process": {
                "cpu_percent": process_info['cpu_percent'],
                "memory_percent": process_info['memory_percent'],
                "num_threads": process_info['num_threads'],
            },
            "system": {
                "cpu_percent": system_cpu,
                "memory_percent": system_memory.percent,
                "memory_available_mb": system_memory.available / (1024 * 1024),
                "disk_percent": system_disk.percent,
                "disk_free_gb": system_disk.free / (1024 * 1024 * 1024),
            }
        }
        
        # Add IO counters if available
        if process_info['io_counters']:
            metrics["process"]["io_read_mb"] = process_info['io_counters'].read_bytes / (1024 * 1024)
            metrics["process"]["io_write_mb"] = process_info['io_counters'].write_bytes / (1024 * 1024)
        
        # Add network info
        try:
            net_io = psutil.net_io_counters()
            metrics["system"]["net_sent_mb"] = net_io.bytes_sent / (1024 * 1024)
            metrics["system"]["net_recv_mb"] = net_io.bytes_recv / (1024 * 1024)
        except Exception:
            pass  # Network info not available
        
        return metrics
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the most recent metrics.
        
        Returns:
            Dictionary of metrics or empty dict if no metrics collected
        """
        if not self.metrics_history:
            return {}
        return self.metrics_history[-1]
    
    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """Get the full metrics history.
        
        Returns:
            List of metric dictionaries
        """
        return self.metrics_history
    
    def get_function_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for monitored functions.
        
        Returns:
            Dictionary mapping function names to their metrics
        """
        return self.function_metrics
    
    def record_function_call(self, func_name: str, execution_time: float, success: bool):
        """Record metrics for a function call.
        
        Args:
            func_name: Name of the function
            execution_time: Execution time in seconds
            success: Whether the function executed successfully
        """
        if func_name not in self.function_metrics:
            self.function_metrics[func_name] = {
                "calls": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "success_count": 0,
                "error_count": 0,
                "last_call_time": None,
                "last_execution_time": None
            }
        
        metrics = self.function_metrics[func_name]
        metrics["calls"] += 1
        metrics["total_time"] += execution_time
        metrics["avg_time"] = metrics["total_time"] / metrics["calls"]
        metrics["min_time"] = min(metrics["min_time"], execution_time)
        metrics["max_time"] = max(metrics["max_time"], execution_time)
        
        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1
        
        metrics["last_call_time"] = datetime.now().isoformat()
        metrics["last_execution_time"] = execution_time
    
    def reset_function_metrics(self, func_name: Optional[str] = None):
        """Reset function metrics.
        
        Args:
            func_name: Name of function to reset, or None to reset all
        """
        if func_name:
            if func_name in self.function_metrics:
                del self.function_metrics[func_name]
        else:
            self.function_metrics = {}


# Global performance metrics instance
_performance_metrics = None


def get_performance_metrics() -> PerformanceMetrics:
    """Get the global performance metrics instance.
    
    Returns:
        PerformanceMetrics instance
    """
    global _performance_metrics
    
    if _performance_metrics is None:
        _performance_metrics = PerformanceMetrics()
    
    return _performance_metrics


def monitor(func=None, *, name: str = None):
    """Decorator to monitor function performance.
    
    Args:
        func: Function to decorate
        name: Custom name for the function in metrics
        
    Returns:
        Decorated function
    """
    def decorator(func):
        func_name = name or f"{func.__module__}.{func.__qualname__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = get_performance_metrics()
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                execution_time = time.time() - start_time
                metrics.record_function_call(func_name, execution_time, success)
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)


def setup_performance_monitoring(
    collect_interval: int = 60,
    history_size: int = 60,
    auto_start: bool = True
) -> PerformanceMetrics:
    """Set up performance monitoring with the specified configuration.
    
    Args:
        collect_interval: Interval in seconds between metrics collection
        history_size: Number of historical data points to keep
        auto_start: Whether to automatically start collection
        
    Returns:
        PerformanceMetrics instance
    """
    global _performance_metrics
    
    if _performance_metrics is not None:
        _performance_metrics.stop()
    
    _performance_metrics = PerformanceMetrics(
        collect_interval=collect_interval,
        history_size=history_size,
        auto_start=auto_start
    )
    
    return _performance_metrics
