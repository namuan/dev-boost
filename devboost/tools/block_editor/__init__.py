"""Block Editor package.

This package groups all modules related to the Block Editor:
 - editor: main widget container and factory
 - widget: per-block editor widget
 - storage: block dataclass and persistence manager
 - parser: plain text <-> blocks converter
 - formatters: helpers for auto-formatting structured content
 - highlighters: syntax/markdown highlighters used in the editor

External modules should import the factory via:
    from devboost.tools.block_editor import create_blocks_editor_widget
"""

from .editor import create_blocks_editor_widget

__all__ = ["create_blocks_editor_widget"]
