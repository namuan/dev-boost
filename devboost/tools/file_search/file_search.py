import logging
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QColor, QFont, QKeySequence, QShortcut, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplitter,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.config import get_config, set_config
from devboost.styles import get_dialog_style, get_status_style, get_tool_style

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
    patterns_text = get_config("file_search.file_globs", "")
    patterns_edit = QLineEdit(patterns_text)
    patterns_edit.setPlaceholderText("File patterns (*.pdf *.zip *.py)")
    search_edit = QLineEdit()
    search_edit.setPlaceholderText("Search files (ripgrep)")
    search_btn = QPushButton("Search")
    cheat_sheet_btn = QPushButton("Cheat Sheet")
    if style_func:
        cheat_sheet_btn.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))

    search_row.addWidget(search_edit, 1)
    search_row.addWidget(search_btn)
    search_row.addWidget(cheat_sheet_btn)
    options_row.addWidget(dir_edit, 1)
    options_row.addWidget(browse_btn)
    options_row.addWidget(patterns_edit, 1)
    options_row.addWidget(choose_rg_btn)

    top_panel.addLayout(search_row, 0)
    top_panel.addLayout(options_row, 0)
    root_layout.addLayout(top_panel, 1)

    splitter = QSplitter(Qt.Orientation.Horizontal)

    files_list = QListWidget()
    content_view = QTextEdit()
    content_view.setReadOnly(True)
    content_view.setFont(QFont("Courier", 11))

    content_panel = QWidget()
    content_layout = QVBoxLayout(content_panel)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(0)
    content_layout.addWidget(content_view)

    splitter.addWidget(files_list)
    splitter.addWidget(content_panel)
    splitter.setSizes([500, 500])

    root_layout.addWidget(splitter, 9)

    match_cursors: list[QTextCursor] = []
    current_idx: int = -1
    count_label = QLabel("0/0")
    prev_btn = QPushButton("<")
    next_btn = QPushButton(">")
    count_label.setStyleSheet(get_status_style("info"))
    prev_btn.setEnabled(False)
    next_btn.setEnabled(False)
    nav_row = QHBoxLayout()
    nav_row.setContentsMargins(10, 4, 10, 8)
    nav_row.setSpacing(8)
    nav_row.addStretch(1)
    nav_row.addWidget(prev_btn)
    nav_row.addWidget(next_btn)
    nav_row.addWidget(count_label)
    content_layout.addLayout(nav_row)

    def _update_nav_state() -> None:
        has = bool(match_cursors)
        prev_btn.setEnabled(has)
        next_btn.setEnabled(has)
        total = len(match_cursors)
        current = current_idx + 1 if current_idx >= 0 else 0
        count_label.setText(f"{current}/{total}")

    def _goto_match(index: int) -> None:
        nonlocal current_idx
        if not match_cursors:
            current_idx = -1
            _update_nav_state()
            return
        n = len(match_cursors)
        current_idx = max(0, min(index, n - 1))
        cur = match_cursors[current_idx]
        content_view.setTextCursor(cur)
        content_view.ensureCursorVisible()
        _update_nav_state()

    def _next_match() -> None:
        if not match_cursors:
            _update_nav_state()
            return
        n = len(match_cursors)
        target = 0 if current_idx < 0 else (current_idx + 1) % n
        _goto_match(target)

    def _prev_match() -> None:
        if not match_cursors:
            _update_nav_state()
            return
        n = len(match_cursors)
        target = n - 1 if current_idx < 0 else (current_idx - 1 + n) % n
        _goto_match(target)

    def _goto_next_global() -> None:
        nonlocal current_idx
        if match_cursors:
            if current_idx < 0:
                _goto_match(0)
                return
            if current_idx + 1 < len(match_cursors):
                _goto_match(current_idx + 1)
                return
        row = files_list.currentRow()
        if row < 0:
            row = 0
        nfiles = files_list.count()
        if nfiles == 0:
            return
        for step in range(1, nfiles + 1):
            next_index = (row + step) % nfiles
            files_list.setCurrentRow(next_index)
            if match_cursors:
                _goto_match(0)
                return

    def _goto_prev_global() -> None:
        nonlocal current_idx
        if match_cursors and current_idx > 0:
            _goto_match(current_idx - 1)
            return
        row = files_list.currentRow()
        if row < 0:
            row = 0
        nfiles = files_list.count()
        if nfiles == 0:
            return
        for step in range(1, nfiles + 1):
            prev_index = (row - step + nfiles) % nfiles
            files_list.setCurrentRow(prev_index)
            if match_cursors:
                _goto_match(len(match_cursors) - 1)
                return

    def _highlight_search_items() -> None:
        nonlocal current_idx, match_cursors
        query = search_edit.text().strip()
        if not query:
            content_view.setExtraSelections([])
            match_cursors.clear()
            current_idx = -1
            _update_nav_state()
            return
        doc = content_view.document()
        if doc.isEmpty():
            content_view.setExtraSelections([])
            match_cursors.clear()
            current_idx = -1
            _update_nav_state()
            return
        case_sensitive = any(ch.isupper() for ch in query)
        rx = QRegularExpression(query)
        if not rx.isValid():
            logger.warning("Invalid regex for highlighting: %r error=%s", query, rx.errorString())
            content_view.setExtraSelections([])
            match_cursors.clear()
            current_idx = -1
            _update_nav_state()
            return
        has_inline_case_flag = "(?i)" in query or "(?-i)" in query
        if not case_sensitive and not has_inline_case_flag:
            rx.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
        selections = []
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(255, 235, 59))
        cursor = QTextCursor(doc)
        cursor.setPosition(0)
        count = 0
        match_cursors.clear()
        while True:
            found = doc.find(rx, cursor)
            if found.isNull():
                break
            sel = QTextEdit.ExtraSelection()
            sel.cursor = found
            sel.format = fmt
            selections.append(sel)
            match_cursors.append(QTextCursor(found))
            cursor.setPosition(found.selectionEnd())
            count += 1
        content_view.setExtraSelections(selections)
        if match_cursors:
            current_idx = 0
            content_view.setTextCursor(match_cursors[0])
            content_view.ensureCursorVisible()
        else:
            current_idx = -1
        _update_nav_state()
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

    def _open_rg_cheat_sheet() -> None:
        try:
            dialog = RipgrepCheatSheetDialog(widget)
            logger.info("Opening ripgrep cheat sheet dialog")
            dialog.exec()
        except Exception:
            logger.exception("Failed to open ripgrep cheat sheet dialog")

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
            ]
            globs_raw = patterns_edit.text().strip()
            globs: list[str] = globs_raw.split() if globs_raw else []
            need_text = any((".pdf" in g.lower()) or (".zip" in g.lower()) for g in globs)
            if need_text:
                cmd.append("--text")
            for g in globs:
                cmd.extend(["--glob", g])
            cmd.append(query)
            cmd.append(str(search_root))
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
            set_config("file_search.file_globs", globs_raw)
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
            suffix = Path(path_str).suffix.lower()
            if suffix in {".pdf", ".zip"}:
                content_view.setPlainText("Binary file preview not supported for PDF/ZIP.")
                content_view.setStyleSheet(get_status_style("warning"))
                logger.info("Binary preview skipped: %s", path_str)
                match_cursors.clear()
                _update_nav_state()
            else:
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
    next_btn.clicked.connect(_next_match)
    prev_btn.clicked.connect(_prev_match)
    files_list.currentItemChanged.connect(lambda current, prev: _on_selection_changed())
    widget._fs_next_sc = QShortcut(QKeySequence("F2"), widget)
    widget._fs_prev_sc = QShortcut(QKeySequence("Shift+F2"), widget)
    widget._fs_next_sc.activated.connect(_goto_next_global)
    widget._fs_prev_sc.activated.connect(_goto_prev_global)
    cheat_sheet_btn.clicked.connect(_open_rg_cheat_sheet)

    return widget


class RipgrepCheatSheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ripgrep Cheat Sheet")
        self.setModal(True)
        self.setFixedSize(700, 560)
        self.setStyleSheet(get_dialog_style())
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(_rg_cheat_sheet_text())
        layout.addWidget(text)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


def _rg_cheat_sheet_text() -> str:
    return (
        "RIPGREP CHEAT SHEET\n\n"
        "=== PATTERNS (Rust regex) ===\n"
        ".          Any char except newline\n"
        "\\d         Digit\n"
        "\\w         Word char\n"
        "\\s         Whitespace\n"
        "^          Start of line\n"
        "$          End of line\n"
        "\\b         Word boundary\n"
        "\\B         Non-word boundary\n"
        "* + ? {n} {n,} {n,m} Quantifiers\n"
        "(...)      Capturing group\n"
        "(?:...)    Non-capturing group\n\n"
        "=== INLINE FLAGS ===\n"
        "(?i)       Case insensitive\n"
        "(?-i)      Turn off case-insensitive\n"
        "(?m)       Multiline (^/$ match lines)\n"
        "(?s)       Dot matches newline\n"
        "(?x)       Ignore whitespace and allow comments\n\n"
        "=== SMART CASE ===\n"
        "--smart-case: lowercase pattern → case-insensitive; contains uppercase → case-sensitive\n\n"
        "=== COMMON CLI FLAGS ===\n"
        "-n         Show line numbers\n"
        "-l         Print only file paths with matches\n"
        "-F         Fixed-string search (no regex)\n"
        "-P         Use PCRE2 engine (enables look-around, backreferences)\n"
        "--color never  Disable colored output\n\n"
        "=== EXAMPLES ===\n"
        "foo|bar                 Either 'foo' or 'bar'\n"
        "\\bTODO\\b               Word 'TODO'\n"
        "(?i)error               Case-insensitive 'error'\n"
        "(?m)^class\\s+\\w+       Class declarations at line start\n"
        "(?s)BEGIN.*END          Span across lines\n"
        "[A-Za-z_][A-Za-z0-9_]*  Identifier\n\n"
        "Tip: In this tool, patterns use ripgrep regex semantics with smart-case.\n"
    )
