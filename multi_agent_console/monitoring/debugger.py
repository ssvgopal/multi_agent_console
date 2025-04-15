"""
Debugging module for MultiAgentConsole.

This module provides tools for debugging and troubleshooting.
"""

import os
import sys
import inspect
import traceback
import threading
import time
import json
import pdb
import functools
from typing import Dict, Any, List, Callable, Optional, Union, Set
from datetime import datetime

from .logger import get_logger

# Get logger
logger = get_logger("debugger")


class Debugger:
    """Advanced debugger for MultiAgentConsole."""

    def __init__(self):
        """Initialize the debugger."""
        self.breakpoints: Dict[str, Set[int]] = {}
        self.watches: Dict[str, List[str]] = {}
        self.tracing_enabled = False
        self.trace_depth = 0
        self.trace_filter = None
        self.trace_output = None
        self.trace_history: List[Dict[str, Any]] = []
        self.max_trace_history = 1000
        self.debug_mode = False

    def enable_debug_mode(self):
        """Enable debug mode."""
        self.debug_mode = True
        logger.info("Debug mode enabled")

    def disable_debug_mode(self):
        """Disable debug mode."""
        self.debug_mode = False
        logger.info("Debug mode disabled")

    def set_breakpoint(self, filename: str, line: int):
        """Set a breakpoint at the specified location.

        Args:
            filename: Source file name
            line: Line number
        """
        if filename not in self.breakpoints:
            self.breakpoints[filename] = set()

        self.breakpoints[filename].add(line)
        logger.info(f"Breakpoint set at {filename}:{line}")

    def clear_breakpoint(self, filename: str, line: int):
        """Clear a breakpoint at the specified location.

        Args:
            filename: Source file name
            line: Line number
        """
        if filename in self.breakpoints and line in self.breakpoints[filename]:
            self.breakpoints[filename].remove(line)
            logger.info(f"Breakpoint cleared at {filename}:{line}")

            # Remove empty entries
            if not self.breakpoints[filename]:
                del self.breakpoints[filename]

    def clear_all_breakpoints(self):
        """Clear all breakpoints."""
        self.breakpoints = {}
        logger.info("All breakpoints cleared")

    def add_watch(self, variable_name: str, context: str = "global"):
        """Add a watch for a variable.

        Args:
            variable_name: Name of the variable to watch
            context: Context for the watch (e.g., function name, module)
        """
        if context not in self.watches:
            self.watches[context] = []

        if variable_name not in self.watches[context]:
            self.watches[context].append(variable_name)
            logger.info(f"Watch added for {variable_name} in context {context}")

    def remove_watch(self, variable_name: str, context: str = "global"):
        """Remove a watch for a variable.

        Args:
            variable_name: Name of the variable to watch
            context: Context for the watch
        """
        if context in self.watches and variable_name in self.watches[context]:
            self.watches[context].remove(variable_name)
            logger.info(f"Watch removed for {variable_name} in context {context}")

            # Remove empty entries
            if not self.watches[context]:
                del self.watches[context]

    def clear_all_watches(self):
        """Clear all watches."""
        self.watches = {}
        logger.info("All watches cleared")

    def start_tracing(self, filter_func: Optional[Callable] = None, output_file: Optional[str] = None):
        """Start function call tracing.

        Args:
            filter_func: Optional function to filter trace events
            output_file: Optional file to write trace output
        """
        if self.tracing_enabled:
            logger.warning("Tracing is already enabled")
            return

        self.tracing_enabled = True
        self.trace_depth = 0
        self.trace_filter = filter_func
        self.trace_history = []

        if output_file:
            self.trace_output = open(output_file, 'w')
        else:
            self.trace_output = None

        # Set the trace function
        sys.settrace(self._trace_calls)
        threading.settrace(self._trace_calls)

        logger.info("Tracing started")

    def stop_tracing(self):
        """Stop function call tracing."""
        if not self.tracing_enabled:
            logger.warning("Tracing is not enabled")
            return

        self.tracing_enabled = False
        sys.settrace(None)
        threading.settrace(None)

        if self.trace_output:
            self.trace_output.close()
            self.trace_output = None

        logger.info(f"Tracing stopped, {len(self.trace_history)} events recorded")

    def _trace_calls(self, frame, event, arg):
        """Trace function calls.

        Args:
            frame: Current frame
            event: Event type
            arg: Event-specific argument

        Returns:
            Trace function for local events or None
        """
        if not self.tracing_enabled:
            return None

        # Get frame info
        code = frame.f_code
        filename = os.path.basename(code.co_filename)
        function_name = code.co_name
        line_no = frame.f_lineno

        # Check if we should filter this event
        if self.trace_filter and not self.trace_filter(filename, function_name, event):
            return None

        # Handle different events
        if event == 'call':
            self.trace_depth += 1
            trace_info = {
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'filename': filename,
                'function': function_name,
                'line': line_no,
                'depth': self.trace_depth,
                'thread': threading.current_thread().name
            }

            # Add to history
            self._add_to_trace_history(trace_info)

            # Check for watches
            self._check_watches(frame, function_name)

            # Return local trace function
            return self._trace_locals

        elif event == 'return':
            trace_info = {
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'filename': filename,
                'function': function_name,
                'line': line_no,
                'depth': self.trace_depth,
                'thread': threading.current_thread().name,
                'return_value': str(arg)
            }

            # Add to history
            self._add_to_trace_history(trace_info)

            self.trace_depth -= 1

        return None

    def _trace_locals(self, frame, event, arg):
        """Trace local events within a function.

        Args:
            frame: Current frame
            event: Event type
            arg: Event-specific argument

        Returns:
            Self for continued tracing
        """
        if not self.tracing_enabled:
            return None

        # Get frame info
        code = frame.f_code
        filename = os.path.basename(code.co_filename)
        function_name = code.co_name
        line_no = frame.f_lineno

        # Check for breakpoints
        if event == 'line' and filename in self.breakpoints and line_no in self.breakpoints[filename]:
            # We hit a breakpoint
            logger.info(f"Breakpoint hit at {filename}:{line_no} in {function_name}")

            if self.debug_mode:
                # Start interactive debugger
                print(f"\n>>> Breakpoint hit at {filename}:{line_no} in {function_name}")
                pdb.set_trace()

        # Check for watches on line events
        if event == 'line':
            self._check_watches(frame, function_name)

        # Handle exceptions
        if event == 'exception':
            exc_type, exc_value, exc_traceback = arg
            trace_info = {
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'filename': filename,
                'function': function_name,
                'line': line_no,
                'depth': self.trace_depth,
                'thread': threading.current_thread().name,
                'exception_type': exc_type.__name__,
                'exception_value': str(exc_value)
            }

            # Add to history
            self._add_to_trace_history(trace_info)

        return self._trace_locals

    def _check_watches(self, frame, function_name):
        """Check watched variables in the current frame.

        Args:
            frame: Current frame
            function_name: Name of the current function
        """
        # Check global watches
        if "global" in self.watches:
            for var_name in self.watches["global"]:
                if var_name in frame.f_globals:
                    value = frame.f_globals[var_name]
                    logger.info(f"Watch (global): {var_name} = {value}")

        # Check function-specific watches
        if function_name in self.watches:
            for var_name in self.watches[function_name]:
                if var_name in frame.f_locals:
                    value = frame.f_locals[var_name]
                    logger.info(f"Watch ({function_name}): {var_name} = {value}")

    def _add_to_trace_history(self, trace_info):
        """Add an event to the trace history.

        Args:
            trace_info: Trace event information
        """
        self.trace_history.append(trace_info)

        # Trim history if needed
        if len(self.trace_history) > self.max_trace_history:
            self.trace_history = self.trace_history[-self.max_trace_history:]

        # Write to output file if specified
        if self.trace_output:
            self.trace_output.write(json.dumps(trace_info) + '\n')
            self.trace_output.flush()

    def get_trace_history(self) -> List[Dict[str, Any]]:
        """Get the trace history.

        Returns:
            List of trace events
        """
        return self.trace_history

    def save_trace_history(self, filename: str):
        """Save the trace history to a file.

        Args:
            filename: Output file name
        """
        with open(filename, 'w') as f:
            json.dump(self.trace_history, f, indent=2)

        logger.info(f"Trace history saved to {filename}")

    def inspect_object(self, obj: Any) -> Dict[str, Any]:
        """Inspect an object and return its details.

        Args:
            obj: Object to inspect

        Returns:
            Dictionary with object details
        """
        result = {
            'type': type(obj).__name__,
            'module': getattr(type(obj), '__module__', None),
            'id': id(obj),
            'dir': dir(obj)
        }

        # Add docstring if available
        if hasattr(obj, '__doc__') and obj.__doc__:
            result['docstring'] = obj.__doc__.strip()

        # Add source code for functions and methods
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            try:
                result['source'] = inspect.getsource(obj)
            except Exception:
                result['source'] = 'Source code not available'

        # Add attributes for classes and instances
        if inspect.isclass(obj) or hasattr(obj, '__dict__'):
            attrs = {}
            for attr in dir(obj):
                if not attr.startswith('__'):
                    try:
                        value = getattr(obj, attr)
                        attrs[attr] = str(value)
                    except Exception as e:
                        attrs[attr] = f'Error: {str(e)}'
            result['attributes'] = attrs

        return result

    def get_current_stack(self) -> List[Dict[str, Any]]:
        """Get the current call stack.

        Returns:
            List of frame information dictionaries
        """
        stack = []
        frame = inspect.currentframe()

        try:
            while frame:
                info = inspect.getframeinfo(frame)
                stack.append({
                    'filename': info.filename,
                    'function': info.function,
                    'line': info.lineno,
                    'code': info.code_context[0].strip() if info.code_context else None,
                    'locals': {k: str(v) for k, v in frame.f_locals.items()}
                })
                frame = frame.f_back
        finally:
            del frame  # Avoid reference cycles

        return stack

    def memory_dump(self, obj: Any, max_depth: int = 2) -> Dict[str, Any]:
        """Create a memory dump of an object.

        Args:
            obj: Object to dump
            max_depth: Maximum recursion depth

        Returns:
            Dictionary representation of the object
        """
        visited = set()

        def _dump(o, depth):
            if depth > max_depth:
                return str(o)

            obj_id = id(o)
            if obj_id in visited:
                return f"<reference to object at 0x{obj_id:x}>"

            visited.add(obj_id)

            if isinstance(o, (str, int, float, bool, type(None))):
                return o
            elif isinstance(o, (list, tuple)):
                return [_dump(x, depth + 1) for x in o]
            elif isinstance(o, dict):
                return {str(k): _dump(v, depth + 1) for k, v in o.items()}
            elif hasattr(o, '__dict__'):
                return {
                    '__type__': type(o).__name__,
                    '__module__': getattr(type(o), '__module__', None),
                    '__id__': obj_id,
                    **{k: _dump(v, depth + 1) for k, v in o.__dict__.items()}
                }
            else:
                return str(o)

        return _dump(obj, 0)


# Global debugger instance
_debugger = None


def get_debugger() -> Debugger:
    """Get the global debugger instance.

    Returns:
        Debugger instance
    """
    global _debugger

    if _debugger is None:
        _debugger = Debugger()

    return _debugger


def debug(func=None, *, breakpoint: bool = False):
    """Decorator to enable debugging for a function.

    Args:
        func: Function to decorate
        breakpoint: Whether to set a breakpoint at the start of the function

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            debugger = get_debugger()

            if breakpoint and debugger.debug_mode:
                # Set breakpoint at function entry
                frame = inspect.currentframe()
                filename = os.path.basename(frame.f_code.co_filename)
                line_no = frame.f_lineno
                debugger.set_breakpoint(filename, line_no)

                # Start debugger
                pdb.set_trace()

            return func(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def setup_debugging(debug_mode: bool = False) -> Debugger:
    """Set up debugging with the specified configuration.

    Args:
        debug_mode: Whether to enable debug mode

    Returns:
        Debugger instance
    """
    global _debugger

    if _debugger is None:
        _debugger = Debugger()

    if debug_mode:
        _debugger.enable_debug_mode()
    else:
        _debugger.disable_debug_mode()

    return _debugger
