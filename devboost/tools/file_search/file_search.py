import logging
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.config import get_config, set_config
from devboost.styles import get_status_style, get_tool_style

logger = logging.getLogger(__name__)


def create_file_search_widget(style_func=None, scratch_pad_widget=None) -> QWidget:
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    root_layout = QVBoxLayout(widget)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    top_panel = QVBoxLayout()
    top_panel.setContentsMargins(0, 0, 0, 0)
    top_panel.setSpacing(0)
    search_row = QHBoxLayout()
    search_row.setContentsMargins(10, 8, 10, 8)
    search_row.setSpacing(8)
    options_row = QHBoxLayout()
    options_row.setContentsMargins(10, 0, 10, 8)
    options_row.setSpacing(8)

    last_dir = get_config("file_search.last_base_dir", str(Path.cwd()))
    dir_edit = QLineEdit(last_dir)
    dir_edit.setPlaceholderText("Base directory")
    browse_btn = QPushButton("Browse")
    rg_path = get_config("file_search.ripgrep_path", "")
    rg_edit = QLineEdit(rg_path)
    rg_edit.setPlaceholderText("ripgrep path (rg)")
    choose_rg_btn = QPushButton("Choose rg")
    search_edit = QLineEdit()
    search_edit.setPlaceholderText("Search files (ripgrep)")
    search_btn = QPushButton("Search")

    search_row.addWidget(search_edit, 1)
    search_row.addWidget(search_btn)
    options_row.addWidget(dir_edit, 1)
    options_row.addWidget(browse_btn)
    options_row.addWidget(choose_rg_btn)

    top_panel.addLayout(search_row, 0)
    top_panel.addLayout(options_row, 0)
    root_layout.addLayout(top_panel, 1)

    splitter = QSplitter(Qt.Orientation.Horizontal)

    files_list = QListWidget()
    content_view = QTextEdit()
    content_view.setReadOnly(True)
    content_view.setFont(QFont("Courier", 11))

    splitter.addWidget(files_list)
    splitter.addWidget(content_view)
    splitter.setSizes([500, 500])

    root_layout.addWidget(splitter, 9)

    def _highlight_search_items() -> None:
        query = search_edit.text().strip()
        if not query:
            content_view.setExtraSelections([])
            return
        doc = content_view.document()
        if doc.isEmpty():
            content_view.setExtraSelections([])
            return
        case_sensitive = any(ch.isupper() for ch in query)
        rx = QRegularExpression(query)
        if not case_sensitive:
            rx.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
        selections = []
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 235, 59))
        cursor = QTextCursor(doc)
        cursor.setPosition(0)
        count = 0
        while True:
            found = doc.find(rx, cursor)
            if found.isNull():
                break
            sel = QTextEdit.ExtraSelection()
            sel.cursor = found
            sel.format = fmt
            selections.append(sel)
            cursor.setPosition(found.selectionEnd())
            count += 1
        content_view.setExtraSelections(selections)
        logger.info("Highlight applied: query=%r matches=%d", query, count)

    def _update_rg_status() -> None:
        explicit_rg = rg_edit.text().strip()
        which_rg = shutil.which("rg")
        rg_bin = explicit_rg or which_rg
        if rg_bin and explicit_rg:
            choose_rg_btn.setText("rg ✓")
            choose_rg_btn.setStyleSheet(get_status_style("success"))
            logger.info("ripgrep status: explicit path set")
        elif rg_bin and not explicit_rg:
            choose_rg_btn.setText("rg ✓")
            choose_rg_btn.setStyleSheet(get_status_style("info"))
            logger.info("ripgrep status: found via PATH")
        else:
            choose_rg_btn.setText("rg ✕")
            choose_rg_btn.setStyleSheet(get_status_style("warning"))
            logger.warning("ripgrep status: not set")
        rg_edit.setVisible(False)

    _update_rg_status()

    def _run_search() -> None:
        query = search_edit.text().strip()
        if not query:
            content_view.setPlainText("Enter a search query above.")
            content_view.setStyleSheet(get_status_style("warning"))
            logger.warning("No search query provided")
            return
        chosen = dir_edit.text().strip()
        search_root = Path(chosen) if chosen else Path.cwd()
        if not search_root.exists() or not search_root.is_dir():
            content_view.setPlainText(f"Invalid base directory:\n{search_root}")
            content_view.setStyleSheet(get_status_style("error"))
            logger.warning("Invalid base directory: %s", search_root)
            return
        rg_bin = rg_edit.text().strip() or shutil.which("rg")
        if rg_bin is None or not Path(rg_bin).exists():
            msg = "ripgrep (rg) not found. Set path above or install: brew install ripgrep"
            content_view.setPlainText(msg)
            content_view.setStyleSheet(get_status_style("error"))
            logger.warning("ripgrep CLI not found or invalid path: %s", rg_edit.text().strip())
            return
        try:
            cmd = [
                rg_bin,
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
            set_config("file_search.last_base_dir", str(search_root))
            if rg_edit.text().strip():
                set_config("file_search.ripgrep_path", rg_edit.text().strip())
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
            _highlight_search_items()
        except Exception:
            logger.exception("Failed to read file: %s", path_str)
            content_view.setPlainText(f"Failed to read file:\n{path_str}")
            content_view.setStyleSheet(get_status_style("error"))

    def _choose_dir() -> None:
        start_dir = dir_edit.text().strip() or str(Path.cwd())
        selected = QFileDialog.getExistingDirectory(widget, "Select Base Directory", start_dir)
        if selected:
            dir_edit.setText(selected)
            logger.info("Base directory set: %s", selected)
            set_config("file_search.last_base_dir", selected)

    def _choose_rg() -> None:
        start_path = rg_edit.text().strip() or "/opt/homebrew/bin"
        selected, _ = QFileDialog.getOpenFileName(widget, "Select ripgrep (rg) binary", start_path)
        if selected:
            rg_edit.setText(selected)
            set_config("file_search.ripgrep_path", selected)
            logger.info("ripgrep path set: %s", selected)
            _update_rg_status()

    def _on_selection_changed() -> None:
        item = files_list.currentItem()
        if item:
            _load_file(item.text())

    browse_btn.clicked.connect(_choose_dir)
    choose_rg_btn.clicked.connect(_choose_rg)
    search_btn.clicked.connect(_run_search)
    search_edit.returnPressed.connect(_run_search)
    search_edit.textChanged.connect(_highlight_search_items)
    files_list.currentItemChanged.connect(lambda current, prev: _on_selection_changed())

    return widget
