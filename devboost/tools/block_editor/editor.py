import logging
import uuid

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_layout_margin, get_layout_spacing, get_tool_style

from .storage import Block, BlockStorage
from .widget import BlockWidget

logger = logging.getLogger(__name__)


class BlocksEditorWidget(QWidget):
    """Container widget managing a list of block editors with controls."""

    def __init__(self):
        super().__init__()
        self.storage = BlockStorage()
        self.blocks: list[Block] = []
        self.block_widgets: list[BlockWidget] = []
        # Search/replace removed per UX simplification
        self._init_ui()
        self._load_blocks()

    def _init_ui(self) -> None:
        self.setMinimumWidth(400)
        # Apply consistent app-wide tool style for background and controls
        try:
            self.setStyleSheet(get_tool_style())
            logger.info("Applied tool style to Block Editor for consistent background")
        except Exception:
            logger.exception("Failed to apply tool style to Block Editor")

        root = QVBoxLayout(self)
        # Harmonize margins and spacing with global layout constants
        m = get_layout_margin("small")
        s = get_layout_spacing("medium")
        logging.debug("BlocksEditorWidget: root margins=%s spacing=%s", m, s)
        root.setContentsMargins(m, m, m, m)
        root.setSpacing(s)

        # Top actions bar (row 1): Add/Save/Copy All
        top_actions_bar = QHBoxLayout()
        add_btn = QPushButton("+ Add Block")
        add_btn.setToolTip("Create a new empty block")
        add_btn.clicked.connect(self._add_block)
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Persist blocks to storage")
        save_btn.clicked.connect(self._save_blocks)
        copy_btn = QPushButton("Copy All")
        copy_btn.setToolTip("Copy all non-empty block contents to clipboard")
        copy_btn.clicked.connect(self._copy_all_blocks)
        top_actions_bar.addWidget(add_btn)
        top_actions_bar.addWidget(save_btn)
        top_actions_bar.addWidget(copy_btn)
        top_actions_bar.addStretch()
        logger.info("Top bar initialized: Add/Save/Copy All; Search/Replace removed per UX")

        # Second row removed entirely per UX

        # Scrollable area for blocks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Ensure scroll area fills remaining space and maintains consistent size
        try:
            self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            logger.debug("Scroll area size policy set to Expanding/Expanding")
        except Exception:
            logger.exception("Failed to set scroll area size policy")
        self.blocks_container = QWidget()
        self.blocks_layout = QVBoxLayout(self.blocks_container)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)
        # Inter-block spacing aligned to global 'small' spacing
        bs = get_layout_spacing("small")
        logging.debug("BlocksEditorWidget: inter-block spacing=%s", bs)
        self.blocks_layout.setSpacing(bs)
        self.scroll_area.setWidget(self.blocks_container)

        root.addLayout(top_actions_bar)
        root.addWidget(self.scroll_area, 1)
        self.setLayout(root)

    def _load_blocks(self) -> None:
        try:
            loaded = self.storage.load()
            if not loaded:
                # Attempt migration from plain scratch pad
                migrated = self.storage.migrate_from_plain_text()
                self.blocks = migrated or []
            else:
                self.blocks = loaded
            logger.info("Loaded %d blocks into editor", len(self.blocks))
            self._render_blocks()
        except Exception:
            logger.exception("Failed to load blocks into editor")

    def _render_blocks(self) -> None:
        # Clear existing layout items (widgets AND spacers) to avoid accumulation
        try:
            total_items = self.blocks_layout.count()
            cleared_widgets = 0
            while self.blocks_layout.count():
                item = self.blocks_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    cleared_widgets += 1
            self.block_widgets.clear()
            logger.debug(
                "Cleared blocks layout items=%d (widgets=%d, spacers=%d)",
                total_items,
                cleared_widgets,
                max(total_items - cleared_widgets, 0),
            )
        except Exception:
            logger.exception("Failed to clear existing block widgets and spacers")
        # Search/replace state removed; nothing to clear
        # Render blocks in order
        ordered = sorted(self.blocks, key=lambda b: b.order)
        for b in ordered:
            # Provide callback so controls live in the block header row (Delete only)
            bw = BlockWidget(
                b,
                # Bind delete to a slot that ignores signal args and deletes by id
                on_delete=self._make_delete_handler(b.id),
            )
            # Observe language changes to keep layout fresh and visible
            try:
                bw.languageChanged.connect(lambda lang, bw=bw: self._on_block_language_changed(bw, lang))
            except Exception:
                logger.exception("Failed to connect languageChanged for block %s", b.id)
            self.block_widgets.append(bw)
            self.blocks_layout.addWidget(bw)
            # Search/replace removed; no focus tracking needed
        self.blocks_layout.addStretch()

    # Per-block controls moved into BlockWidget header; no separate row

    def _add_block(self) -> None:
        try:
            new_block = Block(
                id=str(uuid.uuid4()),
                title="Untitled",
                language="plain",
                content="",
                order=len(self.blocks),
            )
            self.blocks.append(new_block)
            logger.info("Added new block id=%s", new_block.id)
            self._save_blocks()
            self._render_blocks()
        except Exception:
            logger.exception("Failed to add a new block")

    def _delete_block(self, index: int) -> None:
        try:
            if 0 <= index < len(self.blocks):
                # Map index from sorted view to actual block id to avoid off-by-one errors
                ordered = sorted(self.blocks, key=lambda b: b.order)
                target = ordered[index]
                logger.debug(
                    "Resolving deletion: requested index=%d -> block id=%s (order=%d)",
                    index,
                    target.id,
                    target.order,
                )
                # Delegate to id-based deletion
                self._delete_block_by_id(target.id)
        except Exception:
            logger.exception("Failed to delete block at index=%d", index)

    def _make_delete_handler(self, block_id: str):
        """Return a callable slot that ignores any signal args and deletes by id."""

        def _slot(*_args, **_kwargs):
            try:
                self._delete_block_by_id(block_id)
            except Exception:
                logger.exception("Delete slot failed for block id=%s", block_id)

        return _slot

    def _delete_block_by_id(self, block_id: str) -> None:
        """Delete a block by its id, then reorder and refresh UI."""
        try:
            before_count = len(self.blocks)
            # Use storage helper to delete by id for clarity
            self.blocks = self.storage.delete_block(self.blocks, block_id)
            after_count = len(self.blocks)
            logger.info(
                "Deleted block id=%s (before=%d, after=%d)",
                block_id,
                before_count,
                after_count,
            )
            # Reassign sequential order using storage helper and keep internal list consistent
            self.blocks = self.storage.reorder(self.blocks)
            self._save_blocks()
            self._render_blocks()
        except Exception:
            logger.exception("Failed to delete block id=%s", block_id)

    # Move Up/Down controls removed per UX; drag-and-drop reordering can be considered later.

    def _save_blocks(self) -> None:
        try:
            # Update content from widgets before saving
            for bw in self.block_widgets:
                bw.block.content = bw.get_content()
            self.storage.save(self.blocks)
        except Exception:
            logger.exception("Failed to save blocks from editor")

    # Search/Replace functionality removed per UX

    def _copy_all_blocks(self) -> None:
        try:
            contents: list[str] = []
            for idx, bw in enumerate(self.block_widgets):
                text = bw.get_content()
                if text and text.strip():
                    contents.append(text)
                    logger.debug(
                        "Collecting block idx=%d id=%s chars=%d",
                        idx,
                        getattr(bw.block, "id", "unknown"),
                        len(text),
                    )

            combined = "\n\n".join(contents)
            QApplication.clipboard().setText(combined)
            logger.info(
                "Copied %d non-empty blocks to clipboard (chars=%d)",
                len(contents),
                len(combined),
            )
        except Exception:
            logger.exception("Failed to copy all blocks to clipboard")

    def _on_block_language_changed(self, bw: BlockWidget, new_language: str) -> None:
        """React to per-block language changes by nudging layout and logging state."""
        try:
            idx = self.blocks_layout.indexOf(bw)
            count = self.blocks_layout.count()
            logger.debug(
                "Container observed language change: blockIdx=%d/%d lang=%s size=%s vis=%s",
                idx,
                count,
                new_language,
                (bw.width(), bw.height()),
                bw.isVisible(),
            )
            # Nudge layout and scroll area to recompute sizes
            self.blocks_layout.invalidate()
            self.blocks_layout.activate()
            self.blocks_layout.update()
            bw.show()
            self.blocks_container.adjustSize()
            self.blocks_container.updateGeometry()
            self.scroll_area.updateGeometry()
        except Exception:
            logger.exception("Failed to handle block language change in container")


def create_blocks_editor_widget(style_func=None) -> QWidget:
    """
    Create and return the Block Editor widget using a factory pattern (no QWidget subclass),
    mirroring the approach used in json_diff and api_inspector tools.

    The legacy BlocksEditorWidget class remains for backward compatibility, but this
    factory assembles the UI directly.
    """

    # ---------- Core state ----------
    storage = BlockStorage()
    blocks: list[Block] = []
    block_widgets: list[BlockWidget] = []

    # ---------- Root and layout ----------
    root = QWidget()
    try:
        root.setStyleSheet(get_tool_style())
    except Exception:
        logger.exception("Failed to apply tool style to Block Editor")

    root.setMinimumWidth(400)
    root_layout = QVBoxLayout(root)
    # Use global layout constants
    m = get_layout_margin("small")
    s = get_layout_spacing("medium")
    root_layout.setContentsMargins(m, m, m, m)
    root_layout.setSpacing(s)

    # ---------- Top bar ----------
    top_bar = QHBoxLayout()
    add_btn = QPushButton("+ Add Block")
    add_btn.setToolTip("Create a new empty block")
    save_btn = QPushButton("\ud83d\udcbe Save")
    save_btn.setToolTip("Persist blocks to storage")
    copy_btn = QPushButton("Copy All")
    copy_btn.setToolTip("Copy all non-empty block contents to clipboard")
    top_bar.addWidget(add_btn)
    top_bar.addWidget(save_btn)
    top_bar.addWidget(copy_btn)
    top_bar.addStretch()

    # ---------- Scroll area with blocks container ----------
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    try:
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    except Exception:
        logger.exception("Failed to set scroll area size policy")

    blocks_container = QWidget()
    blocks_layout = QVBoxLayout(blocks_container)
    blocks_layout.setContentsMargins(0, 0, 0, 0)
    bs = get_layout_spacing("small")
    blocks_layout.setSpacing(bs)
    scroll_area.setWidget(blocks_container)

    root_layout.addLayout(top_bar)
    root_layout.addWidget(scroll_area, 1)

    # ---------- Helpers ----------
    def _save_blocks() -> None:
        try:
            for bw in block_widgets:
                bw.block.content = bw.get_content()
            storage.save(blocks)
        except Exception:
            logger.exception("Failed to save blocks from editor")

    def _clear_blocks_layout() -> None:
        try:
            while blocks_layout.count():
                item = blocks_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()
        except Exception:
            logger.exception("Failed clearing blocks layout")

    def _on_block_language_changed(bw: BlockWidget, new_language: str) -> None:
        try:
            idx = blocks_layout.indexOf(bw)
            count = blocks_layout.count()
            logger.debug(
                "Container observed language change: blockIdx=%d/%d lang=%s size=%s vis=%s",
                idx,
                count,
                new_language,
                (bw.width(), bw.height()),
                bw.isVisible(),
            )
            blocks_layout.invalidate()
            blocks_layout.activate()
            blocks_layout.update()
            bw.show()
            blocks_container.adjustSize()
            blocks_container.updateGeometry()
            scroll_area.updateGeometry()
        except Exception:
            logger.exception("Failed to handle block language change in container")

    def _delete_block_by_id(block_id: str) -> None:
        try:
            before = len(blocks)
            # Use helpers from storage
            new_list = storage.delete_block(blocks, block_id)
            new_list = storage.reorder(new_list)
            blocks.clear()
            blocks.extend(new_list)
            logger.info("Deleted block id=%s (before=%d, after=%d)", block_id, before, len(blocks))
            _save_blocks()
            _render_blocks()
        except Exception:
            logger.exception("Failed to delete block id=%s", block_id)

    def _make_delete_handler(block_id: str):
        def _slot(*_args, **_kwargs):
            try:
                _delete_block_by_id(block_id)
            except Exception:
                logger.exception("Delete slot failed for block id=%s", block_id)

        return _slot

    def _render_blocks() -> None:
        try:
            _clear_blocks_layout()
            block_widgets.clear()
            # Sort by order to have stable presentation
            ordered = sorted(blocks, key=lambda b: b.order)
            for b in ordered:
                bw = BlockWidget(b, on_delete=_make_delete_handler(b.id))
                try:
                    bw.languageChanged.connect(lambda lang, bw=bw: _on_block_language_changed(bw, lang))
                except Exception:
                    logger.exception("Failed to connect languageChanged for block %s", b.id)
                block_widgets.append(bw)
                blocks_layout.addWidget(bw)
            blocks_layout.addStretch()
        except Exception:
            logger.exception("Failed to render blocks")

    def _load_blocks() -> None:
        try:
            loaded = storage.load()
            if not loaded:
                migrated = storage.migrate_from_plain_text()
                blocks[:] = migrated or []
            else:
                blocks[:] = loaded
            logger.info("Loaded %d blocks into editor", len(blocks))
            _render_blocks()
        except Exception:
            logger.exception("Failed to load blocks into editor")

    def _add_block() -> None:
        try:
            new_block = Block(
                id=str(uuid.uuid4()),
                title="Untitled",
                language="plain",
                content="",
                order=len(blocks),
            )
            blocks.append(new_block)
            logger.info("Added new block id=%s", new_block.id)
            _save_blocks()
            _render_blocks()
        except Exception:
            logger.exception("Failed to add a new block")

    def _copy_all_blocks() -> None:
        try:
            contents: list[str] = []
            for idx, bw in enumerate(block_widgets):
                text = bw.get_content()
                if text and text.strip():
                    contents.append(text)
                    logger.debug(
                        "Collecting block idx=%d id=%s chars=%d",
                        idx,
                        getattr(bw.block, "id", "unknown"),
                        len(text),
                    )
            combined = "\n\n".join(contents)
            QApplication.clipboard().setText(combined)
            logger.info("Copied %d non-empty blocks to clipboard (chars=%d)", len(contents), len(combined))
        except Exception:
            logger.exception("Failed to copy all blocks to clipboard")

    # ---------- Wiring ----------
    add_btn.clicked.connect(_add_block)
    save_btn.clicked.connect(_save_blocks)
    copy_btn.clicked.connect(_copy_all_blocks)

    # ---------- Initial load ----------
    _load_blocks()

    return root
