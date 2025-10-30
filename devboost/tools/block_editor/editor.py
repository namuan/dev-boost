import logging
import uuid

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
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

        # Top actions bar (row 1): Add/Save
        top_actions_bar = QHBoxLayout()
        add_btn = QPushButton("+ Add Block")
        add_btn.setToolTip("Create a new empty block")
        add_btn.clicked.connect(self._add_block)
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Persist blocks to storage")
        save_btn.clicked.connect(self._save_blocks)
        top_actions_bar.addWidget(add_btn)
        top_actions_bar.addWidget(save_btn)
        top_actions_bar.addStretch()
        logger.info("Top bar initialized: Add/Save only; Search/Replace removed per UX")

        # Second row removed entirely per UX

        # Scrollable area for blocks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.blocks_container = QWidget()
        self.blocks_layout = QVBoxLayout(self.blocks_container)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)
        # Inter-block spacing aligned to global 'small' spacing
        bs = get_layout_spacing("small")
        logging.debug("BlocksEditorWidget: inter-block spacing=%s", bs)
        self.blocks_layout.setSpacing(bs)
        self.scroll_area.setWidget(self.blocks_container)

        root.addLayout(top_actions_bar)
        root.addWidget(self.scroll_area)
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
        # Clear existing widgets
        while self.block_widgets:
            w = self.block_widgets.pop()
            w.setParent(None)
        # Search/replace state removed; nothing to clear
        # Render blocks in order
        ordered = sorted(self.blocks, key=lambda b: b.order)
        for idx, b in enumerate(ordered):
            # Provide callback so controls live in the block header row (Delete only)
            bw = BlockWidget(
                b,
                on_delete=lambda idx=idx: self._delete_block(idx),
            )
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
                b = self.blocks.pop(index)
                logger.info("Deleted block id=%s at index=%d", b.id, index)
                # Reassign order sequentially
                for i, blk in enumerate(self.blocks):
                    blk.order = i
                self._save_blocks()
                self._render_blocks()
        except Exception:
            logger.exception("Failed to delete block at index=%d", index)

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


def create_blocks_editor_widget(style_func=None) -> QWidget:
    return BlocksEditorWidget()
