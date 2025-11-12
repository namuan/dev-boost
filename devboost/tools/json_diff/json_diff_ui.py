import json
import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_status_style, get_tool_style

from .json_diff import DiffEntry, JsonDiffEngine

logger = logging.getLogger(__name__)


class JSONDiffDashboard(QWidget):
    def __init__(self, scratch_pad_widget=None):
        super().__init__()
        self.scratch_pad_widget = scratch_pad_widget
        self.engine = JsonDiffEngine()
        self._diffs: list[DiffEntry] = []

        self._setup_ui()
        self.setStyleSheet(get_tool_style())

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        top_bar = QHBoxLayout()
        self.compare_btn = QPushButton("Compare")
        self.compare_btn.clicked.connect(self._run_compare)
        self.swap_btn = QPushButton("Swap A/B")
        self.swap_btn.clicked.connect(self._swap_inputs)
        self.save_btn = QPushButton("Save Report")
        self.save_btn.clicked.connect(self._save_report)
        self.send_to_scratch_btn = None
        if self.scratch_pad_widget:
            self.send_to_scratch_btn = QPushButton("Send to Scratch Pad")
            self.send_to_scratch_btn.clicked.connect(self._send_to_scratch_pad)
        top_bar.addStretch()
        top_bar.addWidget(self.compare_btn)
        top_bar.addWidget(self.swap_btn)
        if self.send_to_scratch_btn:
            top_bar.addWidget(self.send_to_scratch_btn)
        else:
            top_bar.addWidget(self.save_btn)
        root.addLayout(top_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_toolbar = QHBoxLayout()
        self.left_paste_btn = QPushButton("Paste")
        self.left_paste_btn.clicked.connect(lambda: self._load_from_clipboard(self.left_edit))
        self.left_load_btn = QPushButton("Load File...")
        self.left_load_btn.clicked.connect(lambda: self._load_from_file(self.left_edit))
        self.left_clear_btn = QPushButton("Clear")
        self.left_clear_btn.clicked.connect(lambda: self.left_edit.clear())
        left_toolbar.addWidget(self.left_paste_btn)
        left_toolbar.addWidget(self.left_load_btn)
        left_toolbar.addWidget(self.left_clear_btn)
        left_toolbar.addStretch()
        left_layout.addLayout(left_toolbar)
        self.left_edit = QTextEdit()
        self.left_edit.setFont(QFont("Courier", 11))
        left_layout.addWidget(self.left_edit)
        splitter.addWidget(left_pane)

        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_toolbar = QHBoxLayout()
        self.right_paste_btn = QPushButton("Paste")
        self.right_paste_btn.clicked.connect(lambda: self._load_from_clipboard(self.right_edit))
        self.right_load_btn = QPushButton("Load File...")
        self.right_load_btn.clicked.connect(lambda: self._load_from_file(self.right_edit))
        self.right_clear_btn = QPushButton("Clear")
        self.right_clear_btn.clicked.connect(lambda: self.right_edit.clear())
        right_toolbar.addWidget(self.right_paste_btn)
        right_toolbar.addWidget(self.right_load_btn)
        right_toolbar.addWidget(self.right_clear_btn)
        right_toolbar.addStretch()
        right_layout.addLayout(right_toolbar)
        self.right_edit = QTextEdit()
        self.right_edit.setFont(QFont("Courier", 11))
        right_layout.addWidget(self.right_edit)
        splitter.addWidget(right_pane)

        splitter.setSizes([400, 400])
        root.addWidget(splitter, 1)

        self.tabs = QTabWidget()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Path", "Change", "Left", "Right"])
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Courier", 11))
        self.tabs.addTab(self.tree, "Tree Diff")
        self.tabs.addTab(self.text, "Text Diff")
        root.addWidget(self.tabs, 1)

    def _load_from_clipboard(self, target: QTextEdit) -> None:
        try:
            text = QApplication.clipboard().text()
            if text:
                target.setPlainText(text)
                logger.info("Loaded JSON from clipboard into %s", "left" if target is self.left_edit else "right")
        except Exception:
            logger.exception("Failed to load JSON from clipboard")

    def _load_from_file(self, target: QTextEdit) -> None:
        try:
            fname, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)")
            if fname:
                content = Path(fname).read_text(encoding="utf-8")
                target.setPlainText(content)
                logger.info("Loaded file '%s' into %s", fname, "left" if target is self.left_edit else "right")
        except Exception:
            logger.exception("Failed to load JSON file")
            QMessageBox.warning(self, "Error", "Failed to load JSON file.")

    def _swap_inputs(self) -> None:
        l = self.left_edit.toPlainText()
        r = self.right_edit.toPlainText()
        self.left_edit.setPlainText(r)
        self.right_edit.setPlainText(l)
        logger.info("Swapped left/right inputs")

    def _parse_json(self, text: str) -> tuple[bool, Any, str]:
        t = text.strip()
        if not t:
            return False, None, "Input is empty"
        try:
            return True, json.loads(t), ""
        except json.JSONDecodeError as e:
            return False, None, f"JSON error at line {e.lineno}, column {e.colno}: {e.msg}"
        except Exception as e:
            return False, None, f"Unexpected error: {e!s}"

    def _run_compare(self) -> None:
        left_text = self.left_edit.toPlainText()
        right_text = self.right_edit.toPlainText()

        l_ok, l_json, l_err = self._parse_json(left_text)
        r_ok, r_json, r_err = self._parse_json(right_text)

        if not l_ok:
            QMessageBox.warning(self, "Invalid JSON (Left)", l_err)
            self.left_edit.setStyleSheet(get_status_style("error"))
            logger.warning("Left JSON parse failed: %s", l_err)
            return
        self.left_edit.setStyleSheet("")

        if not r_ok:
            QMessageBox.warning(self, "Invalid JSON (Right)", r_err)
            self.right_edit.setStyleSheet(get_status_style("error"))
            logger.warning("Right JSON parse failed: %s", r_err)
            return
        self.right_edit.setStyleSheet("")

        self._diffs = self.engine.compare(l_json, r_json)
        logger.info("Computed JSON diff entries=%d", len(self._diffs))
        self._populate_tree()
        self._populate_text()

    def _populate_tree(self) -> None:
        self.tree.clear()
        for d in self._diffs:
            item = QTreeWidgetItem([d.path, d.change, self._fmt(d.left), self._fmt(d.right)])
            self._apply_color(item, d.change)
            self.tree.addTopLevelItem(item)
        self.tree.resizeColumnToContents(0)

    def _populate_text(self) -> None:
        lines: list[str] = []
        for d in self._diffs:
            prefix = (
                "+" if d.change == "added" else "-" if d.change == "removed" else "~" if d.change == "modified" else "!"
            )
            lines.append(f"{prefix} {d.path}\n  left: {self._fmt(d.left)}\n  right: {self._fmt(d.right)}")
        summary = f"Diffs: {len(self._diffs)} (added={self._count('added')}, removed={self._count('removed')}, modified={self._count('modified')}, type_changed={self._count('type_changed')})\n\n"
        self.text.setPlainText(summary + "\n".join(lines))

    def _count(self, kind: str) -> int:
        return sum(1 for d in self._diffs if d.change == kind)

    def _fmt(self, v: Any) -> str:
        try:
            if isinstance(v, dict | list):
                return json.dumps(v, ensure_ascii=False)
            return "null" if v is None else str(v)
        except Exception:
            return "<unrepr>"

    def _apply_color(self, item: QTreeWidgetItem, change: str) -> None:
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

    def _save_report(self) -> None:
        try:
            if not self._diffs:
                QMessageBox.information(self, "No Differences", "No differences to save.")
                return
            fname, _ = QFileDialog.getSaveFileName(
                self, "Save Diff Report", "json_diff_report.txt", "Text Files (*.txt)"
            )
            if not fname:
                return
            Path(fname).write_text(self.text.toPlainText(), encoding="utf-8")
            logger.info("Saved diff report to %s", fname)
            QMessageBox.information(self, "Saved", f"Diff report saved to {fname}")
        except Exception:
            logger.exception("Failed to save diff report")
            QMessageBox.warning(self, "Error", "Failed to save diff report.")

    def _send_to_scratch_pad(self) -> None:
        try:
            if not self.scratch_pad_widget:
                return
            content = self.text.toPlainText()
            if not content:
                QMessageBox.information(self, "No Report", "Generate a diff report first.")
                return
            if hasattr(self.scratch_pad_widget, "append_text"):
                self.scratch_pad_widget.append_text(content)
            elif hasattr(self.scratch_pad_widget, "get_content") and hasattr(self.scratch_pad_widget, "set_content"):
                current = self.scratch_pad_widget.get_content()
                new_content = f"{current}\n\n---\n{content}" if current else content
                self.scratch_pad_widget.set_content(new_content)
            elif hasattr(self.scratch_pad_widget, "text_edit"):
                existing = self.scratch_pad_widget.text_edit.toPlainText()
                new_content = f"{existing}\n\n---\n{content}" if existing else content
                self.scratch_pad_widget.text_edit.setPlainText(new_content)
            logger.info("Sent diff report to scratch pad")
        except Exception:
            logger.exception("Failed to send to scratch pad")
            QMessageBox.warning(self, "Error", "Failed to send report to Scratch Pad.")
