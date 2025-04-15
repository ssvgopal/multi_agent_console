"""
Monitoring package for MultiAgentConsole.

This package provides tools for monitoring, debugging, and error tracking.
"""

from .logger import (
    setup_logging,
    get_logger,
    log_metrics,
    shutdown_logging
)

from .performance import (
    setup_performance_monitoring,
    get_performance_metrics,
    monitor
)

from .debugger import (
    setup_debugging,
    get_debugger,
    debug
)

from .error_tracking import (
    setup_error_tracking,
    get_error_tracker,
    track_error
)

__all__ = [
    # Logger
    'setup_logging',
    'get_logger',
    'log_metrics',
    'shutdown_logging',
    
    # Performance
    'setup_performance_monitoring',
    'get_performance_metrics',
    'monitor',
    
    # Debugger
    'setup_debugging',
    'get_debugger',
    'debug',
    
    # Error tracking
    'setup_error_tracking',
    'get_error_tracker',
    'track_error'
]
