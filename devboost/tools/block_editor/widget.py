import logging
from collections.abc import Callable
from datetime import datetime

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.Qsci import QsciLexerJavaScript, QsciLexerJSON, QsciLexerPython, QsciScintilla
except Exception:  # pragma: no cover - optional
    QsciScintilla = None  # type: ignore[assignment]
    QsciLexerPython = None  # type: ignore[assignment]
    QsciLexerJSON = None  # type: ignore[assignment]
    QsciLexerJavaScript = None  # type: ignore[assignment]

from devboost.styles import get_layout_margin, get_layout_spacing

from .formatters import try_auto_format
from .highlighters import MarkdownHighlighter
from .storage import Block

logger = logging.getLogger(__name__)


LANGUAGE_OPTIONS = [
    "plain",
    "markdown",
    "json",
    "xml",
    "python",
    "javascript",
]


class BlockWidget(QWidget):
    """A basic block editor widget with language selector and controls in a single header row."""

    def __init__(
        self,
        block: Block,
        on_delete: Callable[[], None] | None = None,
    ):
        super().__init__()
        self.block = block
        self._on_delete = on_delete
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        # Harmonize margins and spacing with global layout constants
        m = get_layout_margin("small")
        s = get_layout_spacing("small")
        logging.debug("BlockWidget: applying layout margins=%s spacing=%s", m, s)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(s)

        # Header with language and controls
        header = QHBoxLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGE_OPTIONS)
        # Ensure language is valid
        if self.block.language in LANGUAGE_OPTIONS:
            self.language_combo.setCurrentText(self.block.language)
        else:
            self.language_combo.setCurrentText("plain")
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        # Blocks are always open; folding control removed per UX feedback
        # Title removed per UX feedback; reclaim space in header
        # Align controls to right: add stretch first, then widgets
        header.addStretch()
        header.addWidget(self.language_combo)
        # Auto-format button (enabled for JSON/XML)
        self.format_btn = QPushButton("Auto-Format")
        self.format_btn.setToolTip("Pretty format structured data")
        self.format_btn.clicked.connect(self._on_format_clicked)
        header.addWidget(self.format_btn)
        # Per-block management control on the same row (Delete only)
        # Icon-only delete button for tighter header appearance
        self.del_btn = QPushButton("🗑")
        self.del_btn.setObjectName("iconButton")
        self.del_btn.setToolTip("Delete block")
        try:
            # Keep a compact footprint consistent with toolbar/icon sizing
            self.del_btn.setFixedSize(28, 24)
        except Exception as exc:
            # Fallback: continue without fixed sizing
            logging.debug("BlockWidget: setFixedSize not supported, proceeding without fixed size: %s", exc)
        if self._on_delete:
            self.del_btn.clicked.connect(self._on_delete)
        header.addWidget(self.del_btn)
        logger.info(
            "Block %s header prepared: Language selector, Auto-Format, and Delete control; Multi-Cursor removed",
            self.block.id,
        )

        layout.addLayout(header)
        # Create editor according to language
        self.editor = self._create_editor_for_language(self.language_combo.currentText())
        # Apply consistent sizing constraints to prevent layout-induced resizing
        self._apply_editor_sizing(self.editor)
        layout.addWidget(self.editor)
        # Always show blocks; ignore any persisted 'collapsed' flags
        if getattr(self.block, "collapsed", False):
            logger.debug("Ignoring persisted collapsed state for block %s; blocks remain open.", self.block.id)
            self.block.collapsed = False
        self.setLayout(layout)
        self._update_format_button_enabled()

    def _apply_lexer(self, language: str) -> None:
        """Apply QScintilla lexer based on selected language to the current editor.

        Safely no-ops when the current editor is a QTextEdit (e.g., markdown/plain).
        """
        try:
            if not (QsciScintilla and isinstance(self.editor, QsciScintilla)):
                # Not a QScintilla editor; nothing to apply
                logger.debug("Skipping lexer apply: editor is not QsciScintilla for language=%s", language)
                return

            lexer = None
            lang = language.lower()
            if lang == "python" and QsciLexerPython:
                lexer = QsciLexerPython()
            elif lang == "json" and QsciLexerJSON:
                lexer = QsciLexerJSON()
            elif lang in ("javascript", "js") and QsciLexerJavaScript:
                lexer = QsciLexerJavaScript()

            self.editor.setLexer(lexer)
            logger.info(
                "Applied lexer=%s for language=%s on block %s",
                type(lexer).__name__ if lexer else None,
                lang,
                self.block.id,
            )
        except Exception:
            logger.exception("Failed to apply lexer for language=%s on block %s", language, self.block.id)

    def _on_language_changed(self, new_language: str) -> None:
        """Handle language selection change."""
        logger.info("Block %s language changed to %s", self.block.id, new_language)
        # Preserve content while switching editor implementation if required
        prior_content = self.get_content()
        # Replace editor widget when switching between QScintilla and QTextEdit (e.g., markdown)
        parent_layout = self.layout()
        if parent_layout:
            parent_layout.removeWidget(self.editor)
            self.editor.hide()
        self.editor = self._create_editor_for_language(new_language)
        # Re-apply sizing constraints on the newly created editor
        self._apply_editor_sizing(self.editor)
        self.set_content(prior_content)
        if parent_layout:
            parent_layout.addWidget(self.editor)
        self.block.language = new_language
        # Update timestamp when language changes
        try:
            self.block.updated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        except Exception:
            logger.exception("Failed to update timestamp on language change for block %s", self.block.id)
        self._apply_lexer(new_language)
        self._update_format_button_enabled()

    def _apply_editor_sizing(self, editor_widget) -> None:
        """Apply sizing constraints to the editor to keep blocks from resizing when layout changes.

        - Minimum height: 150 px
        - Horizontal policy: Expanding (fills available width)
        - Vertical policy: Fixed (prevents auto-resizing when other blocks are added/removed)
        """
        try:
            editor_widget.setMinimumHeight(150)
            editor_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            logger.debug(
                "Applied editor sizing for block %s: minHeight=150, sizePolicy=(Expanding, Fixed)",
                self.block.id,
            )
        except Exception:
            logger.exception("Failed to apply sizing policy to editor for block %s", self.block.id)

    def get_content(self) -> str:
        if QsciScintilla and isinstance(self.editor, QsciScintilla):
            return self.editor.text()
        return self.editor.toPlainText()  # type: ignore[attr-defined]

    def set_content(self, content: str) -> None:
        if QsciScintilla and isinstance(self.editor, QsciScintilla):
            self.editor.setText(content)
        else:
            self.editor.setPlainText(content)  # type: ignore[attr-defined]

    def _create_editor_for_language(self, language: str):
        """Create an editor widget appropriate for the selected language."""
        lang = language.lower()
        # Prefer QScintilla for code-like languages
        if QsciScintilla and lang in {"python", "json", "javascript", "js"}:
            logger.debug("Creating QsciScintilla editor for language=%s, block=%s", lang, self.block.id)
            editor = QsciScintilla()
            # Some QScintilla builds on PyQt6 may not expose certain convenience APIs.
            # Guard these calls to avoid AttributeError across environments.
            try:
                if hasattr(editor, "setUtf8"):
                    editor.setUtf8(True)
                if hasattr(editor, "setAutoIndent"):
                    editor.setAutoIndent(True)
            except Exception:
                logger.exception("Failed to set basic QsciScintilla flags for language=%s", lang)
            # Configure visible whitespace and word wrap using SendScintilla to avoid API differences
            try:
                # 1 = SCWS_VISIBLEALWAYS
                editor.SendScintilla(editor.SCI_SETVIEWWS, 1)  # type: ignore[attr-defined]
                # 1 = SC_WRAP_WORD
                editor.SendScintilla(editor.SCI_SETWRAPMODE, 1)  # type: ignore[attr-defined]
            except Exception:
                logger.exception("Failed to configure whitespace/wrap via SendScintilla for language=%s", lang)
            # Apply lexer directly to the new editor instance
            try:
                lexer = None
                if lang == "python" and QsciLexerPython:
                    lexer = QsciLexerPython()
                elif lang == "json" and QsciLexerJSON:
                    lexer = QsciLexerJSON()
                elif lang in ("javascript", "js") and QsciLexerJavaScript:
                    lexer = QsciLexerJavaScript()
                editor.setLexer(lexer)
            except Exception:
                logger.exception("Failed to set lexer on new QsciScintilla editor for language=%s", lang)
            editor.setText(self.block.content)
            return editor

        # Fallback to QTextEdit; attach lightweight Markdown highlighter when needed
        text_edit = QTextEdit()
        text_edit.setAcceptRichText(False)
        text_edit.setPlainText(self.block.content)
        if lang == "markdown":
            try:
                MarkdownHighlighter(text_edit.document())
            except Exception:
                logger.exception("Failed to initialize Markdown highlighter")
        return text_edit

    # Folding capability removed; blocks remain open in the UI

    def _update_format_button_enabled(self) -> None:
        enabled = self.language_combo.currentText().lower() in {"json", "xml"}
        self.format_btn.setEnabled(enabled)

    def _on_format_clicked(self) -> None:
        try:
            lang = self.language_combo.currentText().lower()
            content = self.get_content()
            formatted, err = try_auto_format(lang, content)
            if formatted is not None:
                self.set_content(formatted)
                self.block.content = formatted
                logger.info("Auto-formatted block %s as %s", self.block.id, lang)
            else:
                # Unsupported or error
                if err:
                    logger.warning("Auto-format failed for block %s: %s", self.block.id, err)
                else:
                    logger.info("Auto-format not applicable for language: %s", lang)
        except Exception:
            logger.exception("Unexpected error during auto-format for block %s", self.block.id)

    # Multi-cursor functionality removed per UX feedback


def create_block_widget(block: Block) -> QWidget:
    return BlockWidget(block)
