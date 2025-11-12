import logging
from dataclasses import dataclass
from typing import Any, Literal

from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiffEntry:
    path: str
    change: Literal["added", "removed", "modified", "type_changed"]
    left: Any | None
    right: Any | None


class JsonDiffEngine:
    def compare(self, left: Any, right: Any, base_path: str = "root") -> list[DiffEntry]:
        diffs: list[DiffEntry] = []
        try:
            if self._type_name(left) != self._type_name(right):
                diffs.append(DiffEntry(base_path, "type_changed", left, right))
                return diffs

            if isinstance(left, dict) and isinstance(right, dict):
                self._diff_dicts(left, right, base_path, diffs)
                return diffs

            if isinstance(left, list) and isinstance(right, list):
                self._diff_lists(left, right, base_path, diffs)
                return diffs

            if left != right:
                diffs.append(DiffEntry(base_path, "modified", left, right))
            return diffs
        finally:
            logger.debug("JsonDiffEngine.compare done path=%s diffs=%d", base_path, len(diffs))

    def _diff_dicts(self, left: dict, right: dict, base_path: str, diffs: list[DiffEntry]) -> None:
        left_keys = set(left.keys())
        right_keys = set(right.keys())

        for k in sorted(left_keys - right_keys):
            path = f"{base_path}.{k}"
            diffs.append(DiffEntry(path, "removed", left.get(k), None))

        for k in sorted(right_keys - left_keys):
            path = f"{base_path}.{k}"
            diffs.append(DiffEntry(path, "added", None, right.get(k)))

        for k in sorted(left_keys & right_keys):
            path = f"{base_path}.{k}"
            lval = left.get(k)
            rval = right.get(k)
            if self._type_name(lval) != self._type_name(rval):
                diffs.append(DiffEntry(path, "type_changed", lval, rval))
                continue
            if isinstance(lval, dict) and isinstance(rval, dict):
                self._diff_dicts(lval, rval, path, diffs)
                continue
            if isinstance(lval, list) and isinstance(rval, list):
                self._diff_lists(lval, rval, path, diffs)
                continue
            if lval != rval:
                diffs.append(DiffEntry(path, "modified", lval, rval))

    def _diff_lists(self, left: list, right: list, base_path: str, diffs: list[DiffEntry]) -> None:
        max_len = max(len(left), len(right))
        for i in range(max_len):
            path = f"{base_path}[{i}]"
            if i >= len(left):
                diffs.append(DiffEntry(path, "added", None, right[i]))
                continue
            if i >= len(right):
                diffs.append(DiffEntry(path, "removed", left[i], None))
                continue
            lval = left[i]
            rval = right[i]
            if self._type_name(lval) != self._type_name(rval):
                diffs.append(DiffEntry(path, "type_changed", lval, rval))
                continue
            if isinstance(lval, dict) and isinstance(rval, dict):
                self._diff_dicts(lval, rval, path, diffs)
                continue
            if isinstance(lval, list) and isinstance(rval, list):
                self._diff_lists(lval, rval, path, diffs)
                continue
            if lval != rval:
                diffs.append(DiffEntry(path, "modified", lval, rval))

    def _type_name(self, v: Any) -> str:
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "bool"
        if isinstance(v, int | float):
            return "number"
        if isinstance(v, str):
            return "string"
        if isinstance(v, dict):
            return "object"
        if isinstance(v, list):
            return "array"
        return type(v).__name__


def create_json_diff_widget(style=None, scratch_pad_widget=None) -> QWidget:
    from .json_diff_ui import JSONDiffDashboard

    return JSONDiffDashboard(scratch_pad_widget)
