"""JSON Diff tool for comparing two JSON documents."""

from .json_diff import (
    DiffEntry,
    JsonDiffEngine,
    create_json_diff_widget,
)
from .json_diff_ui import JSONDiffDashboard

__all__ = [
    "JSONDiffDashboard",
    "DiffEntry",
    "JsonDiffEngine",
    "create_json_diff_widget",
]
