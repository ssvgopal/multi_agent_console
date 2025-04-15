"""
Error tracking module for MultiAgentConsole.

This module provides tools for tracking and analyzing errors.
"""

import os
import sys
import traceback
import threading
import time
import json
import hashlib
from typing import Dict, Any, List, Callable, Optional, Union, Set
from datetime import datetime, timedelta
from collections import defaultdict

from .logger import get_logger

# Get logger
logger = get_logger("error_tracking")


class ErrorTracker:
    """Error tracker for monitoring and analyzing errors."""
    
    def __init__(
        self,
        max_errors: int = 1000,
        group_similar: bool = True,
        notify_threshold: int = 5,  # Number of similar errors to trigger notification
        notify_interval: int = 3600,  # Seconds between notifications for the same error
        error_handlers: Optional[List[Callable]] = None
    ):
        """Initialize the error tracker.
        
        Args:
            max_errors: Maximum number of errors to store
            group_similar: Whether to group similar errors
            notify_threshold: Number of similar errors to trigger notification
            notify_interval: Seconds between notifications for the same error
            error_handlers: List of error handler functions
        """
        self.max_errors = max_errors
        self.group_similar = group_similar
        self.notify_threshold = notify_threshold
        self.notify_interval = notify_interval
        self.error_handlers = error_handlers or []
        
        self.errors: List[Dict[str, Any]] = []
        self.error_groups: Dict[str, Dict[str, Any]] = {}
        self.last_notifications: Dict[str, datetime] = {}
        
        # Install exception hook
        self.original_excepthook = sys.excepthook
        sys.excepthook = self._exception_hook
        
        # Thread exception hook
        self.original_thread_excepthook = threading.excepthook
        threading.excepthook = self._thread_exception_hook
    
    def _exception_hook(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        # Track the error
        self.track_error(exc_type, exc_value, exc_traceback)
        
        # Call the original exception hook
        self.original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _thread_exception_hook(self, args):
        """Handle uncaught thread exceptions.
        
        Args:
            args: Thread exception arguments
        """
        # Track the error
        self.track_error(args.exc_type, args.exc_value, args.exc_traceback, thread=args.thread)
        
        # Call the original thread exception hook
        self.original_thread_excepthook(args)
    
    def track_error(
        self,
        exc_type: type,
        exc_value: BaseException,
        exc_traceback: traceback,
        thread: Optional[threading.Thread] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Track an error.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
            thread: Thread where the exception occurred
            context: Additional context information
        """
        # Get traceback as string
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Create error record
        error = {
            'timestamp': datetime.now().isoformat(),
            'type': exc_type.__name__,
            'message': str(exc_value),
            'traceback': tb_str,
            'thread': thread.name if thread else threading.current_thread().name,
            'context': context or {}
        }
        
        # Add to errors list
        self.errors.append(error)
        
        # Trim errors list if needed
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Group similar errors if enabled
        if self.group_similar:
            self._group_error(error)
        
        # Log the error
        logger.error(
            f"Error tracked: {error['type']}: {error['message']}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Call error handlers
        for handler in self.error_handlers:
            try:
                handler(error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
    
    def _group_error(self, error: Dict[str, Any]):
        """Group similar errors.
        
        Args:
            error: Error record
        """
        # Create a fingerprint for the error
        fingerprint = self._create_error_fingerprint(error)
        
        # Check if we've seen this error before
        if fingerprint in self.error_groups:
            group = self.error_groups[fingerprint]
            group['count'] += 1
            group['last_seen'] = error['timestamp']
            group['occurrences'].append(error)
            
            # Trim occurrences if needed
            if len(group['occurrences']) > 10:
                group['occurrences'] = group['occurrences'][-10:]
            
            # Check if we should notify
            if (group['count'] >= self.notify_threshold and
                (fingerprint not in self.last_notifications or
                 datetime.now() - self.last_notifications[fingerprint] > timedelta(seconds=self.notify_interval))):
                self._notify_error_group(fingerprint, group)
        else:
            # Create a new group
            self.error_groups[fingerprint] = {
                'fingerprint': fingerprint,
                'type': error['type'],
                'message': error['message'],
                'first_seen': error['timestamp'],
                'last_seen': error['timestamp'],
                'count': 1,
                'occurrences': [error]
            }
    
    def _create_error_fingerprint(self, error: Dict[str, Any]) -> str:
        """Create a fingerprint for an error.
        
        Args:
            error: Error record
            
        Returns:
            Error fingerprint
        """
        # Extract the most relevant parts of the traceback
        tb_lines = error['traceback'].split('\n')
        relevant_lines = []
        
        for line in tb_lines:
            if line.strip().startswith('File "'):
                # Include only files from our codebase
                if 'site-packages' not in line and '<frozen' not in line:
                    relevant_lines.append(line)
        
        # Create a string to hash
        fingerprint_str = f"{error['type']}:{relevant_lines}"
        
        # Hash the string
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    def _notify_error_group(self, fingerprint: str, group: Dict[str, Any]):
        """Notify about an error group.
        
        Args:
            fingerprint: Error fingerprint
            group: Error group
        """
        # Update last notification time
        self.last_notifications[fingerprint] = datetime.now()
        
        # Log notification
        logger.warning(
            f"Error threshold reached: {group['type']}: {group['message']} "
            f"({group['count']} occurrences since {group['first_seen']})"
        )
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Get all tracked errors.
        
        Returns:
            List of error records
        """
        return self.errors
    
    def get_error_groups(self) -> Dict[str, Dict[str, Any]]:
        """Get error groups.
        
        Returns:
            Dictionary of error groups
        """
        return self.error_groups
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of tracked errors.
        
        Returns:
            Error summary
        """
        # Count errors by type
        error_types = defaultdict(int)
        for error in self.errors:
            error_types[error['type']] += 1
        
        # Get time range
        if self.errors:
            first_error = datetime.fromisoformat(self.errors[0]['timestamp'])
            last_error = datetime.fromisoformat(self.errors[-1]['timestamp'])
            time_range = (last_error - first_error).total_seconds()
        else:
            time_range = 0
        
        return {
            'total_errors': len(self.errors),
            'error_types': dict(error_types),
            'error_groups': len(self.error_groups),
            'time_range_seconds': time_range
        }
    
    def clear_errors(self):
        """Clear all tracked errors."""
        self.errors = []
        self.error_groups = {}
        self.last_notifications = {}
        logger.info("Error tracking data cleared")
    
    def add_error_handler(self, handler: Callable):
        """Add an error handler function.
        
        Args:
            handler: Error handler function
        """
        if handler not in self.error_handlers:
            self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable):
        """Remove an error handler function.
        
        Args:
            handler: Error handler function
        """
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)
    
    def save_errors(self, filename: str):
        """Save tracked errors to a file.
        
        Args:
            filename: Output file name
        """
        with open(filename, 'w') as f:
            json.dump(self.errors, f, indent=2)
        
        logger.info(f"Errors saved to {filename}")
    
    def save_error_groups(self, filename: str):
        """Save error groups to a file.
        
        Args:
            filename: Output file name
        """
        with open(filename, 'w') as f:
            json.dump(self.error_groups, f, indent=2)
        
        logger.info(f"Error groups saved to {filename}")
    
    def restore(self):
        """Restore original exception hooks."""
        sys.excepthook = self.original_excepthook
        threading.excepthook = self.original_thread_excepthook
        logger.info("Original exception hooks restored")


# Global error tracker instance
_error_tracker = None


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance.
    
    Returns:
        ErrorTracker instance
    """
    global _error_tracker
    
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    
    return _error_tracker


def track_error(
    exc_type: type,
    exc_value: BaseException,
    exc_traceback: traceback,
    context: Optional[Dict[str, Any]] = None
):
    """Track an error.
    
    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
        context: Additional context information
    """
    tracker = get_error_tracker()
    tracker.track_error(exc_type, exc_value, exc_traceback, context=context)


def setup_error_tracking(
    max_errors: int = 1000,
    group_similar: bool = True,
    notify_threshold: int = 5,
    notify_interval: int = 3600,
    error_handlers: Optional[List[Callable]] = None
) -> ErrorTracker:
    """Set up error tracking with the specified configuration.
    
    Args:
        max_errors: Maximum number of errors to store
        group_similar: Whether to group similar errors
        notify_threshold: Number of similar errors to trigger notification
        notify_interval: Seconds between notifications for the same error
        error_handlers: List of error handler functions
        
    Returns:
        ErrorTracker instance
    """
    global _error_tracker
    
    if _error_tracker is not None:
        _error_tracker.restore()
    
    _error_tracker = ErrorTracker(
        max_errors=max_errors,
        group_similar=group_similar,
        notify_threshold=notify_threshold,
        notify_interval=notify_interval,
        error_handlers=error_handlers
    )
    
    return _error_tracker
