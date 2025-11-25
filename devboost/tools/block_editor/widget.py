import logging
import os
from collections.abc import Callable
from datetime import datetime

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QParallelAnimationGroup,
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

# Overlay debug toggle: set DEVBOOST_OVERLAY_DEBUG=1/true/yes/on to enable
OVERLAY_DEBUG = os.getenv("DEVBOOST_OVERLAY_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _overlay_debug(msg: str, *args, **kwargs) -> None:
    if OVERLAY_DEBUG:
        logger.debug(msg, *args, **kwargs)


LANGUAGE_OPTIONS = [
    "plain",
    "markdown",
    "json",
    "xml",
    "python",
    "javascript",
    "calc",
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
        _overlay_debug("BlockWidget: applying layout margins=%s spacing=%s", m, s)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(s)

        # Create editor according to language (no persistent header row)
        initial_language = self.block.language if self.block.language in LANGUAGE_OPTIONS else "plain"
        if initial_language != self.block.language:
            _overlay_debug(
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

        # Install event filter(s) to manage hover/focus overlay visibility and positioning
        self._install_event_filters_for_editor(self.editor)
        try:
            self._calc_updating = False
        except Exception:
            self._calc_updating = False

        # Create hover overlay with icon cluster (language, format, delete)
        self._create_overlay()
        # If the pointer is already inside the editor/viewport, reveal overlay immediately
        try:
            self._maybe_show_overlay_if_hovered()
        except Exception:
            logger.exception("Failed to force-show overlay on init for block %s", self.block.id)
        # Always show blocks; ignore any persisted 'collapsed' flags
        if getattr(self.block, "collapsed", False):
            _overlay_debug("Ignoring persisted collapsed state for block %s; blocks remain open.", self.block.id)
            self.block.collapsed = False
        self.setLayout(layout)
        # Ensure the BlockWidget itself participates in vertical growth so it remains visible
        try:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
            # Guard against zero-height render glitches by enforcing a reasonable minimum
            self.setMinimumHeight(max(160, self.editor.minimumHeight() + m + s))
            _overlay_debug(
                "BlockWidget sizing applied for %s: sizePolicy=(Expanding, MinimumExpanding), minHeight=%d",
                self.block.id,
                self.minimumHeight(),
            )
        except Exception:
            logger.exception("Failed to apply BlockWidget sizing for block %s", self.block.id)
        self._update_format_button_enabled()
        self._attach_calc_behavior_if_needed()

    def _apply_lexer(self, language: str) -> None:
        """Apply QScintilla lexer based on selected language to the current editor.

        Safely no-ops when the current editor is a QTextEdit (e.g., markdown/plain).
        """
        try:
            if not (QsciScintilla and isinstance(self.editor, QsciScintilla)):
                # Not a QScintilla editor; nothing to apply
                _overlay_debug("Skipping lexer apply: editor is not QsciScintilla for language=%s", language)
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
            old_editor = self.editor
            try:
                self.editor.hide()
            except Exception:
                logger.exception("Failed to hide previous editor for block %s", self.block.id)
            self.editor = target
            self.editor.show()
            try:
                self._animate_editor_switch(old_editor, self.editor)
            except Exception:
                logger.exception("Failed to start editor switch animation for block %s", self.block.id)
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
        # Reflect language change on the overlay button
        self._update_language_button_label()
        # If pointer is already hovering, reveal overlay immediately to avoid "missing" overlay perception
        try:
            self._maybe_show_overlay_if_hovered()
        except Exception:
            logger.exception("Failed to force-show overlay after language change for block %s", self.block.id)
        # Update format button enablement when overlay is valid
        self._update_format_button_enabled()
        self._attach_calc_behavior_if_needed()
        # Notify container for any follow-up layout nudges
        try:
            self.languageChanged.emit(new_language)
        except Exception:
            logger.exception("Failed to emit languageChanged for block %s", self.block.id)

    def _log_parent_chain(self) -> None:
        try:
            pw = self.parentWidget()
            gp = pw.parentWidget() if pw is not None else None
            _overlay_debug(
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
            _overlay_debug("Detached previous editor for block %s", self.block.id)
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
                _overlay_debug("Destroyed overlay prior to editor swap for block %s", self.block.id)
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
            _overlay_debug(
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
            if OVERLAY_DEBUG:
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

    def _ensure_opacity_effect(self, widget) -> QGraphicsOpacityEffect:
        try:
            effect = widget.graphicsEffect()
            if not isinstance(effect, QGraphicsOpacityEffect):
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)
            try:
                effect.setOpacity(1.0)
            except Exception:
                _overlay_debug("Opacity effect lacks setOpacity; continuing")
            return effect  # type: ignore[return-value]
        except Exception:
            logger.exception("Failed to ensure opacity effect; creating new")
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            try:
                effect.setOpacity(1.0)
            except Exception:
                _overlay_debug("Opacity effect lacks setOpacity; continuing")
            return effect

    def _animate_editor_switch(self, from_widget, to_widget) -> None:
        """Crossfade between editors for a smoother UX."""
        try:
            if from_widget is to_widget:
                _overlay_debug("Editor switch skipped: target equals current for block %s", self.block.id)
                return
            # Hide overlay during transition to avoid flicker
            try:
                if hasattr(self, "_overlay_hide_timer"):
                    self._overlay_hide_timer.stop()
                if hasattr(self, "overlay"):
                    self._hide_overlay()
            except Exception:
                logger.exception("Failed to hide overlay before animation for block %s", self.block.id)

            from_eff = self._ensure_opacity_effect(from_widget)
            to_eff = self._ensure_opacity_effect(to_widget)
            # Prepare target editor visibility
            try:
                to_widget.show()
            except Exception:
                logger.exception("Failed to show target editor for block %s", self.block.id)
            try:
                to_eff.setOpacity(0.0)
                from_eff.setOpacity(1.0)
            except Exception:
                _overlay_debug("Opacity effect missing setOpacity; animation may be noop")

            fade_out = QPropertyAnimation(from_eff, b"opacity", self)
            fade_out.setDuration(160)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

            fade_in = QPropertyAnimation(to_eff, b"opacity", self)
            fade_in.setDuration(160)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

            group = QParallelAnimationGroup(self)
            group.addAnimation(fade_out)
            group.addAnimation(fade_in)

            def _on_finished() -> None:
                try:
                    # Finalize visibility
                    from_widget.hide()
                    try:
                        from_eff.setOpacity(1.0)
                        to_eff.setOpacity(1.0)
                    except Exception:
                        _overlay_debug("Opacity effect lacks setOpacity during finalize; continuing")
                    # Reattach and position overlay to new editor
                    self._rebuild_overlay_for_editor()
                    self._position_overlay()
                    # Minor layout nudge after switch
                    self._refresh_layout_cascade(self.layout())
                    _overlay_debug(
                        "Completed editor crossfade for block %s (from=%s to=%s)",
                        self.block.id,
                        type(from_widget).__name__,
                        type(to_widget).__name__,
                    )
                except Exception:
                    logger.exception("Failed finishing editor switch for block %s", self.block.id)

            group.finished.connect(_on_finished)
            # Keep reference so GC doesn't stop animations
            self._editor_switch_group = group
            _overlay_debug(
                "Starting editor crossfade for block %s (from=%s to=%s)",
                self.block.id,
                type(from_widget).__name__,
                type(to_widget).__name__,
            )
            group.start()
        except Exception:
            logger.exception("Failed to animate editor switch for block %s", self.block.id)

    def get_content(self) -> str:
        if QsciScintilla and isinstance(self.editor, QsciScintilla):
            return self.editor.text()
        return self.editor.toPlainText()  # type: ignore[attr-defined]

    def set_content(self, content: str) -> None:
        if QsciScintilla and isinstance(self.editor, QsciScintilla):
            self.editor.setText(content)
        else:
            self.editor.setPlainText(content)  # type: ignore[attr-defined]

    def _create_qsci_editor(self, lang: str):
        """Create and configure a QsciScintilla editor for code-like languages."""
        _overlay_debug("Creating QsciScintilla editor for language=%s, block=%s", lang, self.block.id)
        editor = QsciScintilla()
        try:
            # Basic flags
            if hasattr(editor, "setUtf8"):
                editor.setUtf8(True)
            if hasattr(editor, "setAutoIndent"):
                editor.setAutoIndent(True)
            # Show whitespace and enable word wrap via SendScintilla
            try:
                editor.SendScintilla(editor.SCI_SETVIEWWS, 1)  # type: ignore[attr-defined]
                editor.SendScintilla(editor.SCI_SETWRAPMODE, 1)  # type: ignore[attr-defined]
            except Exception:
                logger.exception("Failed SendScintilla config for language=%s", lang)
            # Apply lexer
            lexer = None
            if lang == "python" and QsciLexerPython:
                lexer = QsciLexerPython()
            elif lang == "json" and QsciLexerJSON:
                lexer = QsciLexerJSON()
            elif lang in ("javascript", "js") and QsciLexerJavaScript:
                lexer = QsciLexerJavaScript()
            try:
                editor.setLexer(lexer)
            except Exception:
                logger.exception("Failed to set lexer on Qsci editor for language=%s", lang)
            # Content and hover
            editor.setText(self.block.content)
            try:
                editor.setMouseTracking(True)
            except Exception:
                logger.exception("Failed to enable mouse tracking on Qsci editor for block %s", self.block.id)
            try:
                editor.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            except Exception:
                logger.exception("Failed to enable WA_Hover on Qsci editor for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to configure QsciScintilla editor for language=%s", lang)
        return editor

    def _create_text_editor(self, lang: str):
        """Create and configure a QTextEdit editor for plain/markdown/xml/json fallback."""
        _overlay_debug("Creating QTextEdit editor for language=%s, block=%s", lang, self.block.id)
        text_edit = QTextEdit()
        try:
            text_edit.setAcceptRichText(False)
            text_edit.setPlainText(self.block.content)
            # Hover/mouse tracking
            try:
                text_edit.setMouseTracking(True)
                text_edit.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            except Exception:
                logger.exception("Failed to enable tracking/hover on QTextEdit for block %s", self.block.id)
            # For QAbstractScrollArea-based widgets, mouse events are on the viewport
            try:
                if hasattr(text_edit, "viewport") and callable(text_edit.viewport):
                    vp = text_edit.viewport()
                    if vp is not None:
                        vp.setMouseTracking(True)
                        try:
                            vp.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
                        except Exception:
                            logger.exception(
                                "Failed to enable WA_Hover on QTextEdit viewport for block %s", self.block.id
                            )
            except Exception:
                logger.exception("Failed to enable mouse tracking on QTextEdit viewport for block %s", self.block.id)
            # Lightweight markdown highlighter
            if lang == "markdown":
                try:
                    MarkdownHighlighter(text_edit.document())
                except Exception:
                    logger.exception("Failed to initialize Markdown highlighter")
            if lang == "calc":
                try:
                    text_edit.textChanged.connect(self._on_text_changed_calc)
                except Exception:
                    logger.exception("Failed to connect calc textChanged handler for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to configure QTextEdit for language=%s", lang)
        return text_edit

    def _create_editor_for_language(self, language: str):
        """Create an editor widget appropriate for the selected language."""
        lang = language.lower()
        if QsciScintilla and lang in {"python", "json", "javascript", "js"}:
            return self._create_qsci_editor(lang)
        return self._create_text_editor(lang)

    # Folding capability removed; blocks remain open in the UI

    # --- Hover overlay implementation ---
    def _create_overlay(self) -> None:
        """Create a tiny semi-transparent overlay anchored to the editor's top-right.

        Contains three icon buttons: language, auto-format, delete.
        Overlay fades in on hover/focus and fades out otherwise.
        """
        try:
            parent = self._overlay_parent_widget()
            self.overlay = QWidget(parent)
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

            # Language button opens a popover menu with options and shows current language
            self.lang_btn = QToolButton(self.overlay)
            try:
                lang_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
                # Keep icon optional; show text prominently
                self.lang_btn.setIcon(lang_icon)
            except Exception:
                logger.exception("Failed to set language icon; falling back to text")
            self.lang_btn.setText("Lang")
            self.lang_btn.setIconSize(QSize(16, 16))
            # Prefer text to make current language visible
            self.lang_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            self._update_language_button_label()
            self.lang_btn.setToolTip(f"Language: {self.block.language}")
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
            try:
                self.overlay.setVisible(True)
            except Exception:
                _overlay_debug("Failed to explicitly show overlay; relying on parent visibility")
            self._log_overlay_state("created")
            _overlay_debug("Created hover overlay for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to create hover overlay for block %s", self.block.id)

    def _overlay_parent_widget(self):
        try:
            # Prefer the viewport for scroll-area based editors like QTextEdit
            if hasattr(self.editor, "viewport") and callable(self.editor.viewport):
                vp = self.editor.viewport()
                if vp is not None:
                    _overlay_debug("Using viewport as overlay parent for block %s", self.block.id)
                    return vp
        except Exception:
            logger.exception("Failed to get viewport; falling back to editor for block %s", self.block.id)
        return self.editor

    def _install_event_filters_for_editor(self, editor) -> None:
        """Install event filters on the active editor and its viewport (if any).

        This ensures we receive hover/mouse events even for scroll-area based widgets
        like QTextEdit whose events are emitted on the viewport.
        """
        try:
            try:
                # Ensure editor itself emits hover/mouse move events
                try:
                    editor.setMouseTracking(True)
                except Exception:
                    _overlay_debug("Failed to enable mouseTracking on editor for block %s", self.block.id)
                try:
                    editor.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
                except Exception:
                    _overlay_debug("Failed to enable WA_Hover on editor for block %s", self.block.id)
                editor.installEventFilter(self)
                _overlay_debug("Installed event filter on editor for block %s", self.block.id)
            except Exception:
                logger.exception("Failed to install event filter on editor for block %s", self.block.id)
            # Also listen to viewport events if present
            try:
                if hasattr(editor, "viewport") and callable(editor.viewport):
                    vp = editor.viewport()
                    if vp is not None:
                        try:
                            vp.setMouseTracking(True)
                        except Exception:
                            _overlay_debug("Failed to enable mouseTracking on viewport for block %s", self.block.id)
                        try:
                            vp.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
                        except Exception:
                            _overlay_debug("Failed to enable WA_Hover on viewport for block %s", self.block.id)
                        vp.installEventFilter(self)
                        _overlay_debug("Installed event filter on editor viewport for block %s", self.block.id)
            except Exception:
                logger.exception("Failed to install event filter on editor viewport for block %s", self.block.id)
        except Exception:
            logger.exception("Unexpected error installing event filters for block %s", self.block.id)

    def _update_language_button_label(self) -> None:
        """Update the language button text to reflect the current language."""
        try:
            lang = (self.block.language or "plain").lower()
            label_map = {
                "plain": "Plain",
                "markdown": "MD",
                "json": "JSON",
                "xml": "XML",
                "python": "Py",
                "javascript": "JS",
                "calc": "Calc",
            }
            display = label_map.get(lang, lang.title())
            if hasattr(self, "lang_btn") and self.lang_btn is not None:
                self.lang_btn.setText(display)
                self.lang_btn.setToolTip(f"Language: {lang}")
            _overlay_debug("Language button label set to '%s' for block %s", display, self.block.id)
        except Exception:
            logger.exception("Failed to update language button label for block %s", self.block.id)

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
            _overlay_debug("Language menu opened for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to open language menu for block %s", self.block.id)

    def _position_overlay(self) -> None:
        try:
            if not hasattr(self, "overlay"):
                return
            # Anchor 6px from top-right inside editor
            ow = self.overlay.width()
            # Base width from overlay parent (viewport/editor) to ensure correct positioning
            parent_widget = self.overlay.parentWidget() if hasattr(self, "overlay") else None
            base_width = parent_widget.width() if parent_widget is not None else self.editor.width()
            ox = max(base_width - ow - 6, 2)
            oy = 6
            self.overlay.move(ox, oy)
            self._log_overlay_state("positioned")
            _overlay_debug("Overlay positioned for block %s at (%d,%d)", self.block.id, ox, oy)
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
            try:
                self.overlay.setVisible(True)
                self.overlay.raise_()
            except Exception:
                _overlay_debug("Overlay show/raise failed softly for block %s", self.block.id)
            try:
                # Log when animation finishes to confirm final opacity state
                self._overlay_anim.finished.connect(lambda: self._log_overlay_state("anim-finished-show"))
            except Exception:
                _overlay_debug("Failed to connect finished signal for overlay anim show on block %s", self.block.id)
            self._log_overlay_state("show")
            _overlay_debug("Overlay shown for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to show overlay for block %s", self.block.id)

    def _hide_overlay(self) -> None:
        try:
            # Keep overlay if mouse is still hovering over it
            if hasattr(self, "overlay") and self.overlay.underMouse():
                _overlay_debug("Overlay hide canceled due to hover for block %s", self.block.id)
                return
            self._overlay_anim.stop()
            self._overlay_anim.setStartValue(self._overlay_effect.opacity())
            self._overlay_anim.setEndValue(0.0)
            self._overlay_anim.start()
            try:
                self._overlay_anim.finished.connect(lambda: self._log_overlay_state("anim-finished-hide"))
            except Exception:
                _overlay_debug("Failed to connect finished signal for overlay anim hide on block %s", self.block.id)
            self._log_overlay_state("hide")
            _overlay_debug("Overlay hidden for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to hide overlay for block %s", self.block.id)

    def _rebuild_overlay_for_editor(self) -> None:
        """Reattach overlay to the current editor (after language change)."""
        try:
            # Recreate overlay to avoid stale parenting/filters during editor swap
            if hasattr(self, "overlay") and self.overlay is not None:
                try:
                    self.overlay.setParent(None)
                    self.overlay.deleteLater()
                except Exception:
                    logger.debug("Overlay deletion failed; continuing with recreation for block %s", self.block.id)
                finally:
                    self.overlay = None
            self._create_overlay()
            # Ensure event filters are installed on the active editor and viewport
            self._install_event_filters_for_editor(self.editor)
            self._log_overlay_state("recreated")
            logger.debug("Recreated overlay for current editor on block %s", self.block.id)
            # Proactively reveal overlay briefly after language change for user feedback
            try:
                self._show_overlay()
            except Exception:
                logger.debug("Soft failure in proactive overlay show post language change for block %s", self.block.id)
        except Exception:
            logger.exception("Failed to reattach overlay for block %s", self.block.id)

    def eventFilter(self, obj, event):  # type: ignore[override]
        try:
            # Consider both the editor and its viewport as sources of hover/mouse events
            is_editor = obj is self.editor
            is_viewport = False
            try:
                if hasattr(self.editor, "viewport") and callable(self.editor.viewport):
                    is_viewport = obj is self.editor.viewport()
            except Exception:
                # If viewport access fails, keep is_viewport as False
                logger.debug("Viewport check failed for block %s", self.block.id)

            if is_editor or is_viewport:
                et = event.type()
                if et in (
                    QEvent.Type.Enter,
                    QEvent.Type.FocusIn,
                    QEvent.Type.MouseMove,
                    QEvent.Type.HoverEnter,
                    QEvent.Type.HoverMove,
                ):
                    logger.debug(
                        "Overlay trigger(show) from %s event=%s for block %s",
                        "viewport" if is_viewport else "editor",
                        et.name if hasattr(et, "name") else int(et),
                        self.block.id,
                    )
                    self._show_overlay()
                    return False
                if et in (QEvent.Type.Leave, QEvent.Type.FocusOut, QEvent.Type.HoverLeave):
                    logger.debug(
                        "Overlay trigger(hide) from %s event=%s for block %s",
                        "viewport" if is_viewport else "editor",
                        et.name if hasattr(et, "name") else int(et),
                        self.block.id,
                    )
                    self._overlay_hide_timer.start()
                    return False
                if et == QEvent.Type.Resize:
                    self._position_overlay()
                    return False
            elif hasattr(self, "overlay") and obj is self.overlay:
                et = event.type()
                if et in (QEvent.Type.Enter, QEvent.Type.MouseMove, QEvent.Type.HoverEnter, QEvent.Type.HoverMove):
                    self._show_overlay()
                    return False
                if et in (QEvent.Type.Leave, QEvent.Type.HoverLeave):
                    self._overlay_hide_timer.start()
                    return False
        except Exception:
            logger.exception("eventFilter error in block %s", self.block.id)
        return super().eventFilter(obj, event)

    def _maybe_show_overlay_if_hovered(self) -> None:
        """Show overlay immediately if mouse is already hovering over active editor/viewport/overlay."""
        try:
            vp = None
            try:
                if hasattr(self.editor, "viewport") and callable(self.editor.viewport):
                    vp = self.editor.viewport()
            except Exception:
                vp = None
            if (
                (hasattr(self, "overlay") and self.overlay is not None and self.overlay.underMouse())
                or (self.editor is not None and self.editor.underMouse())
                or (vp is not None and vp.underMouse())
            ):
                self._show_overlay()
                self._log_overlay_state("force-show-hovered")
                logger.debug("Overlay force-shown due to hover state for block %s", self.block.id)
        except Exception:
            logger.exception("Failed hover check for overlay on block %s", self.block.id)

    def _log_overlay_state(self, tag: str) -> None:
        """Log overlay diagnostic state to validate visibility and positioning assumptions."""
        try:
            exists = hasattr(self, "overlay") and self.overlay is not None
            if not exists:
                _overlay_debug("[%s] overlay missing for block %s", tag, self.block.id)
                return
            parent = self.overlay.parentWidget()
            eff = getattr(self, "_overlay_effect", None)
            opacity = None
            try:
                if eff is not None:
                    opacity = eff.opacity()
            except Exception:
                opacity = None
            if OVERLAY_DEBUG:
                logger.info(
                    "[%s] overlay state: block=%s pos=(%d,%d) size=(%d,%d) parent=%s psize=(%d,%d) opacity=%s",
                    tag,
                    self.block.id,
                    self.overlay.x(),
                    self.overlay.y(),
                    self.overlay.width(),
                    self.overlay.height(),
                    type(parent).__name__ if parent is not None else None,
                    parent.width() if parent is not None else -1,
                    parent.height() if parent is not None else -1,
                    opacity,
                )
        except Exception:
            logger.exception("[%s] overlay state logging failed for block %s", tag, self.block.id)

    # --- Visibility diagnostics on the BlockWidget itself ---
    def showEvent(self, event):  # type: ignore[override]
        try:
            if OVERLAY_DEBUG:
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
            if OVERLAY_DEBUG:
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
            if OVERLAY_DEBUG:
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
            enabled = current_lang in {"json", "xml", "calc"}
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

    def _attach_calc_behavior_if_needed(self) -> None:
        try:
            lang = (self.block.language or "").lower()
            if lang == "calc" and hasattr(self, "editor"):
                try:
                    if hasattr(self.editor, "textChanged"):
                        self.editor.textChanged.connect(self._on_text_changed_calc)
                        logger.info("Calc auto-eval connected for block %s", self.block.id)
                except Exception:
                    logger.exception("Failed to attach calc behavior for block %s", self.block.id)
        except Exception:
            logger.exception("Unexpected error attaching calc behavior for block %s", self.block.id)

    def _on_text_changed_calc(self) -> None:
        try:
            if getattr(self, "_calc_updating", False):
                return
            lang = (self.block.language or "").lower()
            if lang != "calc":
                return
            content = self.get_content()
            lines = content.splitlines()
            if not any((l.strip().endswith("=") or ("→" in l)) for l in lines):
                return
            formatted, err = try_auto_format("calc", content)
            if err or formatted is None:
                if err:
                    logger.warning("Calc auto-eval failed for block %s: %s", self.block.id, err)
                return
            if formatted.strip() == content.strip():
                return
            self._calc_updating = True
            self.set_content(formatted)
            self.block.content = formatted
            logger.info("Calc auto-eval applied for block %s", self.block.id)
        except Exception:
            logger.exception("Calc auto-eval error for block %s", self.block.id)
        finally:
            try:
                self._calc_updating = False
            except Exception:
                self._calc_updating = False


def create_block_widget(block: Block) -> QWidget:
    return BlockWidget(block)
