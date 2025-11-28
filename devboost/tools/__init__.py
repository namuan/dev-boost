"""
DevBoost Tools Package.

This package provides various developer tools. Tool modules are loaded lazily
via the lazy_loader module to improve application startup time.

Note: Do NOT import tool modules directly from this __init__.py.
Use devboost.tools.lazy_loader.create_tool_widget() instead.
"""

# Only export the lazy loader for on-demand tool loading
from .lazy_loader import create_tool_widget, get_tool_factory, preload_tool

__all__ = [
    "create_tool_widget",
    "get_tool_factory",
    "preload_tool",
]
