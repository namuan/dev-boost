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


def create_blocks_editor_widget(style_func=None) -> QWidget:
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
