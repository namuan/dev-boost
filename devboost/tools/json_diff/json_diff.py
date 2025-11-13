import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_status_style, get_tool_style

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


def create_json_diff_widget(style_func=None, scratch_pad_widget=None) -> QWidget:
    """
    Creates the main widget for the JSON diff tool, following the same pattern
    as create_json_formatter_widget (no QWidget subclass, pure factory).

    Args:
        style_func: Optional function returning a QStyle (for icons, if needed).
        scratch_pad_widget: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The main widget for the JSON diff tool.
    """
    engine = JsonDiffEngine()

    # Root widget and layout
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    root_layout = QVBoxLayout(widget)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    # --- Top bar ---
    top_bar = QHBoxLayout()
    top_bar.setContentsMargins(10, 5, 5, 5)
    top_bar.setSpacing(8)

    compare_btn = QPushButton("Compare")
    swap_btn = QPushButton("Swap A/B")
    send_to_scratch_btn = QPushButton("Send to Scratch Pad")

    top_bar.addStretch()
    top_bar.addWidget(compare_btn)
    top_bar.addWidget(swap_btn)
    top_bar.addWidget(send_to_scratch_btn)

    root_layout.addLayout(top_bar)

    # --- Splitter with left/right JSON inputs ---
    splitter = QSplitter(Qt.Orientation.Horizontal)

    # Left pane
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_toolbar = QHBoxLayout()

    left_paste_btn = QPushButton("Paste")
    left_load_btn = QPushButton("Load File...")
    left_clear_btn = QPushButton("Clear")

    left_toolbar.addWidget(left_paste_btn)
    left_toolbar.addWidget(left_load_btn)
    left_toolbar.addWidget(left_clear_btn)
    left_toolbar.addStretch()
    left_layout.addLayout(left_toolbar)

    left_edit = QTextEdit()
    left_edit.setFont(QFont("Courier", 11))
    left_edit.setAcceptRichText(False)
    left_layout.addWidget(left_edit)

    splitter.addWidget(left_pane)

    # Right pane
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_toolbar = QHBoxLayout()

    right_paste_btn = QPushButton("Paste")
    right_load_btn = QPushButton("Load File...")
    right_clear_btn = QPushButton("Clear")

    right_toolbar.addWidget(right_paste_btn)
    right_toolbar.addWidget(right_load_btn)
    right_toolbar.addWidget(right_clear_btn)
    right_toolbar.addStretch()
    right_layout.addLayout(right_toolbar)

    right_edit = QTextEdit()
    right_edit.setFont(QFont("Courier", 11))
    right_edit.setAcceptRichText(False)
    right_layout.addWidget(right_edit)

    splitter.addWidget(right_pane)

    splitter.setSizes([400, 400])
    root_layout.addWidget(splitter, 1)

    logger.info("Configured JSON Diff inputs to accept plain-text pasting")

    # --- Diff views (Tree + Text) ---
    # Use a QTabWidget for tree/text diff views (mirroring formatter pattern)
    from PyQt6.QtWidgets import QTabWidget as _QTabWidget

    tabs = _QTabWidget()

    tree = QTreeWidget()
    tree.setHeaderLabels(["Path", "Change", "Left", "Right"])

    text = QTextEdit()
    text.setReadOnly(True)
    text.setFont(QFont("Courier", 11))

    tabs.addTab(tree, "Tree Diff")
    tabs.addTab(text, "Text Diff")

    root_layout.addWidget(tabs, 1)

    # --- Helper functions (closure-based, no QWidget subclass) ---

    def _load_from_clipboard(target: QTextEdit) -> None:
        try:
            app = QApplication.instance()
            if not app:
                return
            clip_text = app.clipboard().text()
            if clip_text:
                target.setPlainText(clip_text)
                logger.info(
                    "Loaded JSON from clipboard into %s",
                    "left" if target is left_edit else "right",
                )
        except Exception:
            logger.exception("Failed to load JSON from clipboard")

    def _load_from_file(target: QTextEdit) -> None:
        try:
            fname, _ = QFileDialog.getOpenFileName(
                widget,
                "Open JSON File",
                "",
                "JSON Files (*.json);;All Files (*)",
            )
            if fname:
                from pathlib import Path

                content = Path(fname).read_text(encoding="utf-8")
                target.setPlainText(content)
                logger.info(
                    "Loaded file '%s' into %s",
                    fname,
                    "left" if target is left_edit else "right",
                )
        except Exception:
            logger.exception("Failed to load JSON file")
            QMessageBox.warning(widget, "Error", "Failed to load JSON file.")

    def _swap_inputs() -> None:
        l = left_edit.toPlainText()
        r = right_edit.toPlainText()
        left_edit.setPlainText(r)
        right_edit.setPlainText(l)
        logger.info("Swapped left/right inputs")

    def _parse_json(text: str) -> tuple[bool, Any, str]:
        t = text.strip()
        if not t:
            return False, None, "Input is empty"
        try:
            return True, json.loads(t), ""
        except json.JSONDecodeError as e:
            return False, None, f"JSON error at line {e.lineno}, column {e.colno}: {e.msg}"
        except Exception as e:
            return False, None, f"Unexpected error: {e!s}"

    diffs: list[DiffEntry] = []

    def _count(kind: str) -> int:
        return sum(1 for d in diffs if d.change == kind)

    def _fmt(v: Any) -> str:
        try:
            if isinstance(v, dict | list):
                return json.dumps(v, ensure_ascii=False)
            return "null" if v is None else str(v)
        except Exception:
            return "<unrepr>"

    def _apply_color(item: QTreeWidgetItem, change: str) -> None:
        from PyQt6.QtGui import QBrush, QColor

        if change == "added":
            brush = QBrush(QColor("#2ecc71"))
        elif change == "removed":
            brush = QBrush(QColor("#e74c3c"))
        elif change == "modified":
            brush = QBrush(QColor("#f1c40f"))
        else:
            brush = QBrush(QColor("#8e44ad"))
        for i in range(4):
            item.setForeground(i, brush)

    def _populate_tree() -> None:
        tree.clear()
        for d in diffs:
            item = QTreeWidgetItem([d.path, d.change, _fmt(d.left), _fmt(d.right)])
            _apply_color(item, d.change)
            tree.addTopLevelItem(item)
        tree.resizeColumnToContents(0)

    def _populate_text() -> None:
        lines: list[str] = []
        for d in diffs:
            prefix = (
                "+" if d.change == "added" else "-" if d.change == "removed" else "~" if d.change == "modified" else "!"
            )
            lines.append(f"{prefix} {d.path}\n  left: {_fmt(d.left)}\n  right: {_fmt(d.right)}")
        summary = (
            f"Diffs: {len(diffs)} "
            f"(added={_count('added')}, "
            f"removed={_count('removed')}, "
            f"modified={_count('modified')}, "
            f"type_changed={_count('type_changed')})\n\n"
        )
        text.setPlainText(summary + "\n".join(lines))
        text.setStyleSheet(get_status_style("info") if diffs else "")

    def _run_compare() -> None:
        nonlocal diffs
        left_text = left_edit.toPlainText()
        right_text = right_edit.toPlainText()

        l_ok, l_json, l_err = _parse_json(left_text)
        r_ok, r_json, r_err = _parse_json(right_text)

        if not l_ok:
            QMessageBox.warning(widget, "Invalid JSON (Left)", l_err)
            left_edit.setStyleSheet(get_status_style("error"))
            logger.warning("Left JSON parse failed: %s", l_err)
            return
        left_edit.setStyleSheet("")

        if not r_ok:
            QMessageBox.warning(widget, "Invalid JSON (Right)", r_err)
            right_edit.setStyleSheet(get_status_style("error"))
            logger.warning("Right JSON parse failed: %s", r_err)
            return
        right_edit.setStyleSheet("")

        diffs = engine.compare(l_json, r_json)
        logger.info("Computed JSON diff entries=%d", len(diffs))
        _populate_tree()
        _populate_text()

    def _send_to_scratch_pad() -> None:
        try:
            content = text.toPlainText()
            if not content:
                QMessageBox.information(widget, "No Report", "Generate a diff report first.")
                return
            sp = scratch_pad_widget
            if not sp:
                QMessageBox.information(widget, "No Scratch Pad", "Scratch Pad is not available.")
                return
            if hasattr(sp, "append_text"):
                sp.append_text(content)
            elif hasattr(sp, "get_content") and hasattr(sp, "set_content"):
                current = sp.get_content()
                new_content = f"{current}\n\n---\n{content}" if current else content
                sp.set_content(new_content)
            elif hasattr(sp, "text_edit"):
                existing = sp.text_edit.toPlainText()
                new_content = f"{existing}\n\n---\n{content}" if existing else content
                sp.text_edit.setPlainText(new_content)
            logger.info("Sent diff report to scratch pad")
        except Exception:
            logger.exception("Failed to send to scratch pad")
            QMessageBox.warning(widget, "Error", "Failed to send report to Scratch Pad.")

    # --- Wire up signals ---
    compare_btn.clicked.connect(_run_compare)
    swap_btn.clicked.connect(_swap_inputs)
    send_to_scratch_btn.clicked.connect(_send_to_scratch_pad)

    left_paste_btn.clicked.connect(lambda: _load_from_clipboard(left_edit))
    right_paste_btn.clicked.connect(lambda: _load_from_clipboard(right_edit))

    left_load_btn.clicked.connect(lambda: _load_from_file(left_edit))
    right_load_btn.clicked.connect(lambda: _load_from_file(right_edit))

    left_clear_btn.clicked.connect(lambda: left_edit.clear())
    right_clear_btn.clicked.connect(lambda: right_edit.clear())

    return widget
