"""JSON Diff tool for comparing two JSON documents."""

from .json_diff import (
    DiffEntry,
    JsonDiffEngine,
    create_json_diff_widget,
)

__all__ = [
    "DiffEntry",
    "JsonDiffEngine",
    "create_json_diff_widget",
]
