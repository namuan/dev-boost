import logging
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_status_style, get_tool_style

logger = logging.getLogger(__name__)


def create_ripgrep_search_widget(style_func=None, scratch_pad_widget=None) -> QWidget:
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    root_layout = QVBoxLayout(widget)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    top_bar = QHBoxLayout()
    top_bar.setContentsMargins(10, 8, 10, 8)
    top_bar.setSpacing(8)

    search_edit = QLineEdit()
    search_edit.setPlaceholderText("Search query (ripgrep)")
    search_btn = QPushButton("Search")

    top_bar.addWidget(search_edit, 1)
    top_bar.addWidget(search_btn)

    root_layout.addLayout(top_bar, 1)

    splitter = QSplitter(Qt.Orientation.Horizontal)

    files_list = QListWidget()
    content_view = QTextEdit()
    content_view.setReadOnly(True)
    content_view.setFont(QFont("Courier", 11))

    splitter.addWidget(files_list)
    splitter.addWidget(content_view)
    splitter.setSizes([500, 500])

    root_layout.addWidget(splitter, 9)

    search_root = Path.cwd()

    def _run_search() -> None:
        query = search_edit.text().strip()
        if not query:
            content_view.setPlainText("Enter a search query above.")
            content_view.setStyleSheet(get_status_style("warning"))
            logger.warning("No search query provided")
            return
        if shutil.which("rg") is None:
            msg = "ripgrep (rg) not found. Install via Homebrew: brew install ripgrep"
            content_view.setPlainText(msg)
            content_view.setStyleSheet(get_status_style("error"))
            logger.warning("ripgrep CLI not found on PATH")
            return
        try:
            cmd = [
                "rg",
                "--smart-case",
                "--no-messages",
                "-n",
                "-l",
                "--color",
                "never",
                query,
                str(search_root),
            ]
            logger.info("Running ripgrep: %s", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode not in (0, 1):
                logger.warning("ripgrep returned code=%d stderr=%s", result.returncode, result.stderr.strip())
            paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            files_list.clear()
            for p in paths:
                files_list.addItem(p)
            logger.info("ripgrep matches=%d", len(paths))
            if paths:
                files_list.setCurrentRow(0)
                content_view.setStyleSheet(get_status_style("info"))
            else:
                content_view.setPlainText("No matches found.")
                content_view.setStyleSheet(get_status_style("warning"))
        except Exception:
            logger.exception("Failed to run ripgrep search")
            content_view.setPlainText("Error running ripgrep.")
            content_view.setStyleSheet(get_status_style("error"))

    def _load_file(path_str: str) -> None:
        try:
            content = Path(path_str).read_text(encoding="utf-8", errors="replace")
            content_view.setPlainText(content)
            content_view.setStyleSheet("")
            logger.info("Loaded file: %s", path_str)
        except Exception:
            logger.exception("Failed to read file: %s", path_str)
            content_view.setPlainText(f"Failed to read file:\n{path_str}")
            content_view.setStyleSheet(get_status_style("error"))

    def _on_selection_changed() -> None:
        item = files_list.currentItem()
        if item:
            _load_file(item.text())

    search_btn.clicked.connect(_run_search)
    search_edit.returnPressed.connect(_run_search)
    files_list.currentItemChanged.connect(lambda current, prev: _on_selection_changed())

    return widget
