"""
Plugin package for MultiAgentConsole.

This package provides a plugin system for extending the functionality of MultiAgentConsole.
"""

from .base import Plugin, PluginManager
from .registry import PluginInfo, PluginRegistry

__all__ = [
    'Plugin',
    'PluginManager',
    'PluginInfo',
    'PluginRegistry'
]
