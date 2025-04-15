"""
Advanced logging module for MultiAgentConsole.

This module provides enhanced logging capabilities with structured logging,
log rotation, and different log levels.
"""

import os
import sys
import json
import logging
import logging.handlers
import traceback
import time
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Define log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class StructuredLogRecord(logging.LogRecord):
    """Extended LogRecord with additional structured data."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.structured_data = {}


class StructuredLogger(logging.Logger):
    """Logger that supports structured logging."""
    
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        """Create a LogRecord with structured data support."""
        record = StructuredLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra is not None:
            for key in extra:
                if key == "structured_data" and isinstance(extra[key], dict):
                    record.structured_data = extra[key]
                elif key in ["message", "asctime", "levelname", "levelno"]:
                    pass  # Skip reserved keys
                else:
                    setattr(record, key, extra[key])
        return record


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON strings."""
    
    def __init__(self, include_timestamp=True):
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record):
        """Format the record as JSON."""
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z" if self.include_timestamp else None,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add structured data if available
        if hasattr(record, "structured_data") and record.structured_data:
            log_data["data"] = record.structured_data
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        return json.dumps(log_data)


class LogManager:
    """Manager for advanced logging capabilities."""
    
    def __init__(
        self,
        log_dir: str = None,
        console_level: str = "INFO",
        file_level: str = "DEBUG",
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        json_format: bool = True,
        capture_stdout: bool = False,
        capture_stderr: bool = True,
        system_info: bool = True
    ):
        """Initialize the log manager.
        
        Args:
            log_dir: Directory for log files (default: ./logs)
            console_level: Log level for console output
            file_level: Log level for file output
            max_file_size: Maximum size of log files before rotation
            backup_count: Number of backup files to keep
            json_format: Whether to use JSON format for logs
            capture_stdout: Whether to capture stdout
            capture_stderr: Whether to capture stderr
            system_info: Whether to log system information on startup
        """
        # Register the custom logger class
        logging.setLoggerClass(StructuredLogger)
        
        # Set up log directory
        self.log_dir = log_dir or os.path.join(os.getcwd(), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up log levels
        self.console_level = LOG_LEVELS.get(console_level.upper(), logging.INFO)
        self.file_level = LOG_LEVELS.get(file_level.upper(), logging.DEBUG)
        
        # Set up root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)  # Capture all logs
        
        # Remove existing handlers
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
        
        # Set up console handler
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(self.console_level)
        
        # Set up file handler
        log_file = os.path.join(self.log_dir, "multi_agent_console.log")
        self.file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        self.file_handler.setLevel(self.file_level)
        
        # Set up error file handler
        error_log_file = os.path.join(self.log_dir, "errors.log")
        self.error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        self.error_file_handler.setLevel(logging.ERROR)
        
        # Set up formatters
        if json_format:
            self.console_formatter = JSONFormatter(include_timestamp=False)
            self.file_formatter = JSONFormatter()
        else:
            self.console_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S"
            )
            self.file_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
            )
        
        self.console_handler.setFormatter(self.console_formatter)
        self.file_handler.setFormatter(self.file_formatter)
        self.error_file_handler.setFormatter(self.file_formatter)
        
        # Add handlers to root logger
        self.root_logger.addHandler(self.console_handler)
        self.root_logger.addHandler(self.file_handler)
        self.root_logger.addHandler(self.error_file_handler)
        
        # Capture stdout and stderr if requested
        self.stdout_capture = None
        self.stderr_capture = None
        
        if capture_stdout:
            self.stdout_capture = StdoutCapture(self.get_logger("stdout"))
        
        if capture_stderr:
            self.stderr_capture = StderrCapture(self.get_logger("stderr"))
        
        # Log system information
        if system_info:
            self.log_system_info()
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    def log_system_info(self):
        """Log system information."""
        logger = self.get_logger("system")
        
        try:
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "hostname": socket.gethostname(),
                "cpu_count": os.cpu_count(),
                "time": datetime.now().isoformat(),
                "pid": os.getpid()
            }
            
            # Add environment variables (excluding sensitive ones)
            env_vars = {}
            for key, value in os.environ.items():
                if not any(sensitive in key.lower() for sensitive in ["key", "secret", "token", "password", "credential"]):
                    env_vars[key] = value
            
            system_info["environment"] = env_vars
            
            logger.info(
                "System information",
                extra={"structured_data": system_info}
            )
        except Exception as e:
            logger.error(f"Failed to log system information: {e}")
    
    def log_metrics(self, metrics: Dict[str, Any], logger_name: str = "metrics"):
        """Log metrics data.
        
        Args:
            metrics: Dictionary of metrics to log
            logger_name: Name of the logger to use
        """
        logger = self.get_logger(logger_name)
        logger.info(
            f"Metrics: {', '.join(f'{k}={v}' for k, v in metrics.items())}",
            extra={"structured_data": metrics}
        )
    
    def shutdown(self):
        """Shutdown logging and release resources."""
        # Restore stdout and stderr
        if self.stdout_capture:
            self.stdout_capture.close()
        
        if self.stderr_capture:
            self.stderr_capture.close()
        
        # Shutdown logging
        logging.shutdown()


class StdoutCapture:
    """Capture stdout and redirect to a logger."""
    
    def __init__(self, logger):
        """Initialize stdout capture.
        
        Args:
            logger: Logger to use for captured output
        """
        self.logger = logger
        self.original_stdout = sys.stdout
        sys.stdout = self
    
    def write(self, message):
        """Write message to original stdout and logger.
        
        Args:
            message: Message to write
        """
        if message.strip():
            self.logger.info(message.rstrip())
        self.original_stdout.write(message)
    
    def flush(self):
        """Flush the original stdout."""
        self.original_stdout.flush()
    
    def close(self):
        """Restore original stdout."""
        sys.stdout = self.original_stdout


class StderrCapture:
    """Capture stderr and redirect to a logger."""
    
    def __init__(self, logger):
        """Initialize stderr capture.
        
        Args:
            logger: Logger to use for captured output
        """
        self.logger = logger
        self.original_stderr = sys.stderr
        sys.stderr = self
    
    def write(self, message):
        """Write message to original stderr and logger.
        
        Args:
            message: Message to write
        """
        if message.strip():
            self.logger.error(message.rstrip())
        self.original_stderr.write(message)
    
    def flush(self):
        """Flush the original stderr."""
        self.original_stderr.flush()
    
    def close(self):
        """Restore original stderr."""
        sys.stderr = self.original_stderr


# Global log manager instance
_log_manager = None


def setup_logging(
    log_dir: str = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    json_format: bool = True,
    capture_stdout: bool = False,
    capture_stderr: bool = True,
    system_info: bool = True
) -> LogManager:
    """Set up logging with the specified configuration.
    
    Args:
        log_dir: Directory for log files (default: ./logs)
        console_level: Log level for console output
        file_level: Log level for file output
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup files to keep
        json_format: Whether to use JSON format for logs
        capture_stdout: Whether to capture stdout
        capture_stderr: Whether to capture stderr
        system_info: Whether to log system information on startup
        
    Returns:
        LogManager instance
    """
    global _log_manager
    
    if _log_manager is not None:
        # Shutdown existing log manager
        _log_manager.shutdown()
    
    _log_manager = LogManager(
        log_dir=log_dir,
        console_level=console_level,
        file_level=file_level,
        max_file_size=max_file_size,
        backup_count=backup_count,
        json_format=json_format,
        capture_stdout=capture_stdout,
        capture_stderr=capture_stderr,
        system_info=system_info
    )
    
    return _log_manager


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    global _log_manager
    
    if _log_manager is None:
        # Set up default logging if not already set up
        setup_logging()
    
    return _log_manager.get_logger(name)


def log_metrics(metrics: Dict[str, Any], logger_name: str = "metrics"):
    """Log metrics data.
    
    Args:
        metrics: Dictionary of metrics to log
        logger_name: Name of the logger to use
    """
    global _log_manager
    
    if _log_manager is None:
        # Set up default logging if not already set up
        setup_logging()
    
    _log_manager.log_metrics(metrics, logger_name)


def shutdown_logging():
    """Shutdown logging and release resources."""
    global _log_manager
    
    if _log_manager is not None:
        _log_manager.shutdown()
        _log_manager = None
