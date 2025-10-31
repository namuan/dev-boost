import logging
from collections.abc import Callable
from datetime import datetime

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QMenu,
    QSizePolicy,
    QStyle,
    QTextEdit,
    QToolButton,
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
    """Block editor with hover overlay controls (language, format, delete).

    Removes the persistent header row to save vertical space and shows a compact
    semi-transparent overlay in the editor's top-right on hover/focus.
    """

    languageChanged = pyqtSignal(str)

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

        # Create editor according to language (no persistent header row)
        initial_language = self.block.language if self.block.language in LANGUAGE_OPTIONS else "plain"
        if initial_language != self.block.language:
            logger.debug(
                "Normalizing block %s language from %s to %s",
                self.block.id,
                self.block.language,
                initial_language,
            )
            self.block.language = initial_language

        # Build a stacked layout with code/text editors to avoid reparent churn
        self._editor_stack = QVBoxLayout()
        # Create shared editors lazily and set initial selection
        self._code_editor = None
        if QsciScintilla:
            try:
                self._code_editor = self._create_editor_for_language("python")
            except Exception:
                logger.exception("Failed to pre-create code editor; will fallback to text editor")
        try:
            self._text_editor = self._create_editor_for_language("plain")
        except Exception:
            logger.exception("Failed to create text editor; using fallback QTextEdit")
            self._text_editor = QTextEdit()
            self._text_editor.setAcceptRichText(False)
        # Apply sizing to both editors
        if self._code_editor is not None:
            self._apply_editor_sizing(self._code_editor)
        self._apply_editor_sizing(self._text_editor)
        # Host editors in a simple container to mimic stacked behavior
        self._editor_host = QWidget()
        self._editor_host_layout = QVBoxLayout(self._editor_host)
        self._editor_host_layout.setContentsMargins(0, 0, 0, 0)
        self._editor_host_layout.setSpacing(0)
        if self._code_editor is not None:
            self._editor_host_layout.addWidget(self._code_editor)
            self._code_editor.hide()
        self._editor_host_layout.addWidget(self._text_editor)
        self._text_editor.hide()
        # Select initial editor based on language without removing widgets
        self.editor = self._select_editor_for_language(initial_language)
        self.editor.show()
        layout.addWidget(self._editor_host)

        # Install event filter to manage hover/focus overlay visibility and positioning
        try:
            self.editor.installEventFilter(self)
            logger.debug("Installed event filter on editor for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to install event filter on editor for block %s", self.block.id)

        # Create hover overlay with icon cluster (language, format, delete)
        self._create_overlay()
        # Always show blocks; ignore any persisted 'collapsed' flags
        if getattr(self.block, "collapsed", False):
            logger.debug("Ignoring persisted collapsed state for block %s; blocks remain open.", self.block.id)
            self.block.collapsed = False
        self.setLayout(layout)
        # Ensure the BlockWidget itself participates in vertical growth so it remains visible
        try:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
            # Guard against zero-height render glitches by enforcing a reasonable minimum
            self.setMinimumHeight(max(160, self.editor.minimumHeight() + m + s))
            logger.debug(
                "BlockWidget sizing applied for %s: sizePolicy=(Expanding, MinimumExpanding), minHeight=%d",
                self.block.id,
                self.minimumHeight(),
            )
        except Exception:
            logger.exception("Failed to apply BlockWidget sizing for block %s", self.block.id)
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
        self._log_parent_chain()
        self._snapshot_state("before_swap")
        # Preserve content and switch visible editor without reparenting
        prior_content = self.get_content()
        target = self._select_editor_for_language(new_language)
        if target is not self.editor:
            try:
                self.editor.hide()
            except Exception:
                logger.exception("Failed to hide previous editor for block %s", self.block.id)
            self.editor = target
            self.editor.show()
        # Update content on the active editor
        self.set_content(prior_content)
        # Refresh layout minimally
        self._snapshot_state("after_attach")
        self._refresh_layout_cascade(self.layout())
        self._snapshot_state("after_refresh")
        self.block.language = new_language
        # Update timestamp when language changes
        try:
            self.block.updated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        except Exception:
            logger.exception("Failed to update timestamp on language change for block %s", self.block.id)
        self._apply_lexer(new_language)
        # Reattach overlay to the current editor
        self._rebuild_overlay_for_editor()
        # Update format button enablement when overlay is valid
        self._update_format_button_enabled()
        # Notify container for any follow-up layout nudges
        try:
            self.languageChanged.emit(new_language)
        except Exception:
            logger.exception("Failed to emit languageChanged for block %s", self.block.id)

    def _log_parent_chain(self) -> None:
        try:
            pw = self.parentWidget()
            gp = pw.parentWidget() if pw is not None else None
            logger.debug(
                "Parent chain on language change for %s: self=%s pw=%s gp=%s",
                self.block.id,
                type(self).__name__,
                type(pw).__name__ if pw else None,
                type(gp).__name__ if gp else None,
            )
        except Exception:
            logger.exception("Failed to log parent chain for block %s", self.block.id)

    def _detach_old_editor(self, parent_layout) -> None:
        try:
            old_editor = self.editor
            parent_layout.removeWidget(old_editor)
            old_editor.hide()
            # Fully detach and delete the previous editor to avoid layout quirks
            old_editor.setParent(None)
            old_editor.deleteLater()
            logger.debug("Detached previous editor for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to detach previous editor for block %s", self.block.id)

    def _destroy_overlay_safely(self) -> None:
        try:
            if hasattr(self, "overlay") and self.overlay is not None:
                self.overlay.deleteLater()
                self.overlay = None
                if hasattr(self, "lang_btn"):
                    self.lang_btn = None  # type: ignore[assignment]
                if hasattr(self, "format_btn"):
                    self.format_btn = None  # type: ignore[assignment]
                if hasattr(self, "del_btn"):
                    self.del_btn = None  # type: ignore[assignment]
                logger.debug("Destroyed overlay prior to editor swap for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to destroy previous overlay for block %s")

    def _refresh_layout_cascade(self, parent_layout) -> None:
        try:
            # Ensure visibility and aggressively refresh layout graph
            self.editor.show()
            self.setVisible(True)
            parent_layout.invalidate()
            parent_layout.activate()
            parent_layout.update()
            self.adjustSize()
            self.updateGeometry()
            # Nudge parent chain to recompute sizes if any lingering zero-height occurs
            container = self.parentWidget()
            if container is not None:
                cl = container.layout()
                if cl is not None:
                    cl.invalidate()
                    cl.activate()
                    cl.update()
                container.adjustSize()
                container.updateGeometry()
                container.repaint()
            grand = self.parentWidget().parentWidget() if self.parentWidget() is not None else None
            if grand is not None:
                gl = grand.layout()
                if gl is not None:
                    gl.invalidate()
                    gl.activate()
                    gl.update()
                grand.adjustSize()
                grand.updateGeometry()
                grand.repaint()
            logger.debug(
                "Refreshed layout after editor swap for block %s: visible=%s, size=%s",
                self.block.id,
                self.isVisible(),
                (self.width(), self.height()),
            )
        except Exception:
            logger.exception("Failed to refresh layout after editor swap for block %s", self.block.id)

    def _snapshot_state(self, tag: str) -> None:
        """Log a detailed snapshot of widget/editor/parent state to diagnose visibility issues."""
        try:
            container = self.parentWidget()
            cont_layout = container.layout() if container is not None else None
            idx = cont_layout.indexOf(self) if cont_layout is not None else -1
            count = cont_layout.count() if cont_layout is not None else -1
            editor_parent = self.editor.parentWidget() if hasattr(self, "editor") else None
            logger.info(
                "[%s] block=%s self(vis=%s hidden=%s size=%s min=%s idx=%s/%s) editor(size=%s min=%s vis=%s parent=%s)",
                tag,
                self.block.id,
                self.isVisible(),
                self.isHidden(),
                (self.width(), self.height()),
                (self.minimumWidth(), self.minimumHeight()),
                idx,
                count,
                (self.editor.width(), self.editor.height()) if hasattr(self, "editor") else None,
                (
                    getattr(self.editor, "minimumWidth", lambda: None)(),
                    getattr(self.editor, "minimumHeight", lambda: None)(),
                )
                if hasattr(self, "editor")
                else None,
                getattr(self.editor, "isVisible", lambda: None)() if hasattr(self, "editor") else None,
                type(editor_parent).__name__ if editor_parent is not None else None,
            )
        except Exception:
            logger.exception("Failed to snapshot state for block %s", self.block.id)

    def _apply_editor_sizing(self, editor_widget) -> None:
        """Apply sizing constraints to the editor to keep blocks from resizing when layout changes.

        - Minimum height: 150 px
        - Horizontal policy: Expanding (fills available width)
        - Vertical policy: MinimumExpanding (ensures visibility and allows layout to grow)
        """
        try:
            editor_widget.setMinimumHeight(150)
            editor_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
            logger.debug(
                "Applied editor sizing for block %s: minHeight=150, sizePolicy=(Expanding, MinimumExpanding)",
                self.block.id,
            )
        except Exception:
            logger.exception("Failed to apply sizing policy to editor for block %s", self.block.id)

    def _select_editor_for_language(self, language: str):
        """Return the appropriate editor for a language without recreating widgets."""
        lang = (language or "").lower()
        use_code = QsciScintilla is not None and lang in {"python", "json", "javascript", "js"}
        if use_code and self._code_editor is not None:
            # Apply lexer on the shared code editor
            try:
                lexer = None
                if lang == "python" and QsciLexerPython:
                    lexer = QsciLexerPython()
                elif lang == "json" and QsciLexerJSON:
                    lexer = QsciLexerJSON()
                elif lang in ("javascript", "js") and QsciLexerJavaScript:
                    lexer = QsciLexerJavaScript()
                self._code_editor.setLexer(lexer)
            except Exception:
                logger.exception("Failed to set lexer on shared code editor for language=%s", lang)
            return self._code_editor
        return self._text_editor

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
            # Ensure hover events are emitted for overlay visibility
            try:
                editor.setMouseTracking(True)
            except Exception:
                logger.exception("Failed to enable mouse tracking on QsciScintilla editor for block %s", self.block.id)
            return editor

        # Fallback to QTextEdit; attach lightweight Markdown highlighter when needed
        text_edit = QTextEdit()
        text_edit.setAcceptRichText(False)
        text_edit.setPlainText(self.block.content)
        # Ensure hover events are emitted for overlay visibility
        try:
            text_edit.setMouseTracking(True)
        except Exception:
            logger.exception("Failed to enable mouse tracking on QTextEdit for block %s", self.block.id)
        if lang == "markdown":
            try:
                MarkdownHighlighter(text_edit.document())
            except Exception:
                logger.exception("Failed to initialize Markdown highlighter")
        return text_edit

    # Folding capability removed; blocks remain open in the UI

    # --- Hover overlay implementation ---
    def _create_overlay(self) -> None:
        """Create a tiny semi-transparent overlay anchored to the editor's top-right.

        Contains three icon buttons: language, auto-format, delete.
        Overlay fades in on hover/focus and fades out otherwise.
        """
        try:
            self.overlay = QWidget(self.editor)
            self.overlay.setObjectName("blockOverlay")
            self.overlay.setStyleSheet(
                "#blockOverlay {"
                "  background-color: rgba(20, 20, 20, 120);"
                "  border-radius: 6px;"
                "}"
                "#blockOverlay QToolButton {"
                "  border: none;"
                "  background: transparent;"
                "  color: #e0e0e0;"
                "}"
                "#blockOverlay QToolButton:hover {"
                "  color: #ffffff;"
                "}"
            )
            hl = QHBoxLayout(self.overlay)
            hl.setContentsMargins(6, 4, 6, 4)
            hl.setSpacing(2)

            # Language button opens a popover menu with options
            self.lang_btn = QToolButton(self.overlay)
            try:
                lang_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
                self.lang_btn.setIcon(lang_icon)
            except Exception:
                logger.exception("Failed to set language icon; falling back to text")
            self.lang_btn.setText("Lang")
            self.lang_btn.setIconSize(QSize(16, 16))
            self.lang_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            if self.lang_btn.icon().isNull():
                self.lang_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            self.lang_btn.setToolTip("Set language")
            self.lang_btn.setFixedSize(26, 24)
            self.lang_btn.clicked.connect(self._open_language_menu)
            hl.addWidget(self.lang_btn)

            # Auto-format button
            self.format_btn = QToolButton(self.overlay)
            try:
                fmt_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
                self.format_btn.setIcon(fmt_icon)
            except Exception:
                logger.exception("Failed to set format icon; falling back to text")
            self.format_btn.setText("Fmt")
            self.format_btn.setIconSize(QSize(16, 16))
            self.format_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            if self.format_btn.icon().isNull():
                self.format_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            self.format_btn.setToolTip("Auto-format (JSON/XML)")
            self.format_btn.setFixedSize(26, 24)
            self.format_btn.clicked.connect(self._on_format_clicked)
            hl.addWidget(self.format_btn)

            # Delete button
            self.del_btn = QToolButton(self.overlay)
            try:
                del_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
                self.del_btn.setIcon(del_icon)
            except Exception:
                logger.exception("Failed to set delete icon; falling back to text")
            self.del_btn.setText("Del")
            self.del_btn.setIconSize(QSize(16, 16))
            self.del_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            if self.del_btn.icon().isNull():
                self.del_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            self.del_btn.setToolTip("Delete block")
            self.del_btn.setFixedSize(26, 24)
            if self._on_delete:
                self.del_btn.clicked.connect(self._on_delete)
            hl.addWidget(self.del_btn)

            # Opacity effect and animation for fade in/out
            self._overlay_effect = QGraphicsOpacityEffect(self.overlay)
            self.overlay.setGraphicsEffect(self._overlay_effect)
            self._overlay_effect.setOpacity(0.0)

            self._overlay_anim = QPropertyAnimation(self._overlay_effect, b"opacity", self.overlay)
            self._overlay_anim.setDuration(160)
            self._overlay_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

            # Timer to delay hiding the overlay after mouse leaves
            self._overlay_hide_timer = QTimer(self)
            self._overlay_hide_timer.setSingleShot(True)
            self._overlay_hide_timer.setInterval(600)
            self._overlay_hide_timer.timeout.connect(self._hide_overlay)

            # Position initially and keep hidden
            try:
                self.overlay.setMouseTracking(True)
                self.overlay.installEventFilter(self)
            except Exception:
                logger.exception("Failed to set mouse tracking/event filter on overlay for block %s", self.block.id)
            # Size based on layout hint to avoid zero-size rendering
            try:
                size_hint = hl.sizeHint()
                self.overlay.resize(max(90, size_hint.width()), max(28, size_hint.height()))
            except Exception:
                logger.exception("Failed to compute overlay size; falling back to default")
                self.overlay.resize(90, 28)
            self._position_overlay()
            self.overlay.raise_()
            logger.info("Created hover overlay for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to create hover overlay for block %s", self.block.id)

    def _open_language_menu(self) -> None:
        try:
            # Keep overlay visible while the menu is open
            self._overlay_hide_timer.stop()
            menu = QMenu(self.overlay)
            for lang in LANGUAGE_OPTIONS:
                act = menu.addAction(lang)
                act.triggered.connect(lambda checked=False, l=lang: self._on_language_changed(l))
            # Position the menu just below the language button
            pos_below_btn = self.lang_btn.mapToGlobal(QPoint(0, self.lang_btn.height()))
            menu.exec(pos_below_btn)
            logger.debug("Language menu opened for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to open language menu for block %s", self.block.id)

    def _position_overlay(self) -> None:
        try:
            if not hasattr(self, "overlay"):
                return
            # Anchor 6px from top-right inside editor
            ow = self.overlay.width()
            ox = max(self.editor.width() - ow - 6, 2)
            oy = 6
            self.overlay.move(ox, oy)
            logger.debug("Overlay positioned for block %s at (%d,%d)", self.block.id, ox, oy)
        except Exception:
            logger.exception("Failed to position overlay for block %s", self.block.id)

    def _show_overlay(self) -> None:
        try:
            self._overlay_hide_timer.stop()
            self._position_overlay()
            self._overlay_anim.stop()
            self._overlay_anim.setStartValue(self._overlay_effect.opacity())
            self._overlay_anim.setEndValue(1.0)
            self._overlay_anim.start()
            logger.debug("Overlay shown for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to show overlay for block %s", self.block.id)

    def _hide_overlay(self) -> None:
        try:
            # Keep overlay if mouse is still hovering over it
            if hasattr(self, "overlay") and self.overlay.underMouse():
                logger.debug("Overlay hide canceled due to hover for block %s", self.block.id)
                return
            self._overlay_anim.stop()
            self._overlay_anim.setStartValue(self._overlay_effect.opacity())
            self._overlay_anim.setEndValue(0.0)
            self._overlay_anim.start()
            logger.debug("Overlay hidden for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to hide overlay for block %s", self.block.id)

    def _rebuild_overlay_for_editor(self) -> None:
        """Reattach overlay to the current editor (after language change)."""
        try:
            if hasattr(self, "overlay") and self.overlay is not None:
                try:
                    self.overlay.setParent(self.editor)
                    self.overlay.raise_()
                    self._position_overlay()
                    logger.debug("Reattached overlay to new editor for block %s", self.block.id)
                except RuntimeError:
                    # Underlying C++ QWidget was already deleted; recreate overlay
                    logger.warning("Overlay pointer invalid; recreating for block %s", self.block.id)
                    self.overlay = None
                    self._create_overlay()
        except Exception:
            logger.exception("Failed to reattach overlay for block %s", self.block.id)

    def eventFilter(self, obj, event):  # type: ignore[override]
        try:
            if obj is self.editor:
                et = event.type()
                if et in (QEvent.Type.Enter, QEvent.Type.FocusIn, QEvent.Type.MouseMove):
                    self._show_overlay()
                    return False
                if et in (QEvent.Type.Leave, QEvent.Type.FocusOut):
                    self._overlay_hide_timer.start()
                    return False
                if et == QEvent.Type.Resize:
                    self._position_overlay()
                    return False
            elif hasattr(self, "overlay") and obj is self.overlay:
                et = event.type()
                if et in (QEvent.Type.Enter, QEvent.Type.MouseMove):
                    self._show_overlay()
                    return False
                if et == QEvent.Type.Leave:
                    self._overlay_hide_timer.start()
                    return False
        except Exception:
            logger.exception("eventFilter error in block %s", self.block.id)
        return super().eventFilter(obj, event)

    # --- Visibility diagnostics on the BlockWidget itself ---
    def showEvent(self, event):  # type: ignore[override]
        try:
            logger.info(
                "Block %s showEvent: size=%s min=%s visible=%s",
                self.block.id,
                (self.width(), self.height()),
                (self.minimumWidth(), self.minimumHeight()),
                self.isVisible(),
            )
        except Exception:
            logger.exception("Error logging showEvent for block %s", self.block.id)
        super().showEvent(event)

    def hideEvent(self, event):  # type: ignore[override]
        try:
            logger.info(
                "Block %s hideEvent: size=%s min=%s hidden=%s",
                self.block.id,
                (self.width(), self.height()),
                (self.minimumWidth(), self.minimumHeight()),
                self.isHidden(),
            )
        except Exception:
            logger.exception("Error logging hideEvent for block %s", self.block.id)
        super().hideEvent(event)

    def resizeEvent(self, event):  # type: ignore[override]
        try:
            logger.info(
                "Block %s resizeEvent: newSize=%s",
                self.block.id,
                (event.size().width(), event.size().height()),
            )
        except Exception:
            logger.exception("Error logging resizeEvent for block %s", self.block.id)
        super().resizeEvent(event)

    def _update_format_button_enabled(self) -> None:
        """Enable format button only for supported languages (json/xml)."""
        try:
            current_lang = (self.block.language or "").lower()
            enabled = current_lang in {"json", "xml"}
            if hasattr(self, "format_btn"):
                self.format_btn.setEnabled(enabled)
            logger.debug(
                "Format button enabled=%s for language=%s on block %s",
                enabled,
                current_lang,
                self.block.id,
            )
        except Exception:
            logger.exception("Failed to update format button state for block %s", self.block.id)

    def _on_format_clicked(self) -> None:
        try:
            lang = (self.block.language or "").lower()
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
