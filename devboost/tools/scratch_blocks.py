import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import appdirs

# Logger for this module
logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


@dataclass
class Block:
    """
    Represents a scratch block of text with optional language binding.

    Attributes:
        id: Stable identifier for the block (UUID-like string recommended).
        title: Short human-friendly title for the block.
        language: Language key for syntax highlighting (e.g., 'python', 'json', 'markdown').
        content: The raw text content.
        order: Integer used to sort blocks in the editor.
        collapsed: Whether the block is currently collapsed in the UI.
        created_at: ISO8601 timestamp when the block was created (UTC).
        updated_at: ISO8601 timestamp when the block was last updated (UTC).
    """

    id: str
    title: str
    language: str
    content: str
    order: int
    collapsed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Do not persist fields that are only used by UI: 'collapsed' and optional 'title'
        data.pop("collapsed", None)
        data.pop("title", None)
        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Block":
        # Provide safe defaults and type normalization
        return Block(
            id=str(data.get("id", "")),
            title=str(data.get("title", "Untitled")),
            language=str(data.get("language", "plain")),
            content=str(data.get("content", "")),
            order=int(data.get("order", 0)),
            collapsed=bool(data.get("collapsed", False)),
            created_at=str(data.get("created_at", _utc_now_iso())),
            updated_at=str(data.get("updated_at", _utc_now_iso())),
        )


class BlockStorage:
    """
    Persistent storage manager for scratch pad blocks.

    Data is stored in a JSON file at:
        <appdata>/DevBoost/scratch_blocks.json

    The JSON structure:
    {
      "version": 1,
      "blocks": [ Block, ... ]
    }
    """

    def __init__(self, app_name: str = "DevBoost", app_author: str = "DeskRiders") -> None:
        self.app_name = app_name
        self.app_author = app_author
        self.data_dir = Path(appdirs.user_data_dir(self.app_name, self.app_author))
        self.storage_file = self.data_dir / "scratch_blocks.json"
        self.version = 1
        logger.debug("Initialized BlockStorage at %s", self.storage_file)

    def load(self) -> list[Block]:
        """Load blocks from storage. Returns empty list if none exist."""
        try:
            if not self.storage_file.exists():
                logger.info("No block storage file found at %s; returning empty list", self.storage_file)
                return []
            with self.storage_file.open(encoding="utf-8") as f:
                raw = json.load(f)
            blocks_data = raw.get("blocks", [])
            blocks = [Block.from_dict(b) for b in blocks_data]
            logger.debug("Loaded %d blocks from storage", len(blocks))
            return blocks
        except Exception:
            logger.exception("Failed to load blocks from storage")
            return []

    def save(self, blocks: list[Block]) -> None:
        """Persist blocks to storage."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": self.version,
                "blocks": [b.to_dict() for b in blocks],
                "saved_at": _utc_now_iso(),
            }
            with self.storage_file.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info("Saved %d blocks to %s", len(blocks), self.storage_file)
        except Exception:
            logger.exception("Failed to save blocks to storage")

    def add_block(self, blocks: list[Block], block: Block) -> list[Block]:
        """Add a new block and return updated block list."""
        blocks.append(block)
        logger.debug("Added block %s with order %d", block.id, block.order)
        return blocks

    def get_block(self, blocks: list[Block], block_id: str) -> Block | None:
        """Retrieve a block by id, None if not found."""
        for b in blocks:
            if b.id == block_id:
                return b
        return None

    def update_block(self, blocks: list[Block], updated: Block) -> list[Block]:
        """Replace a block with same id and update updated_at."""
        for i, b in enumerate(blocks):
            if b.id == updated.id:
                updated.updated_at = _utc_now_iso()
                blocks[i] = updated
                logger.debug("Updated block %s", updated.id)
                break
        return blocks

    def delete_block(self, blocks: list[Block], block_id: str) -> list[Block]:
        """Delete a block by id and return updated list."""
        new_blocks = [b for b in blocks if b.id != block_id]
        logger.debug("Deleted block %s (before=%d, after=%d)", block_id, len(blocks), len(new_blocks))
        return new_blocks

    def reorder(self, blocks: list[Block]) -> list[Block]:
        """Sort blocks by order and reassign sequential order values (0..n-1)."""
        sorted_blocks = sorted(blocks, key=lambda b: b.order)
        for i, b in enumerate(sorted_blocks):
            b.order = i
        logger.debug("Reordered %d blocks", len(sorted_blocks))
        return sorted_blocks

    def migrate_from_plain_text(self) -> list[Block] | None:
        """
        Migrate existing plain text scratch pad content into a single block if present.

        The plain text file is located at: <appdata>/DevBoost/scratch_pad.txt
        Returns the migrated blocks list if migration occurred, otherwise None.
        """
        try:
            plain_file = self.data_dir / "scratch_pad.txt"
            if not plain_file.exists():
                logger.info("No plain scratch pad file found; skipping migration")
                return None
            content = plain_file.read_text(encoding="utf-8")
            if not content.strip():
                logger.info("Plain scratch pad file is empty; skipping migration")
                return None

            # Create a single block from the existing content
            block = Block(
                id=f"blk-{int(datetime.utcnow().timestamp())}",
                title="Migrated Scratch",
                language="plain",
                content=content,
                order=0,
            )
            self.save([block])
            logger.info("Migrated plain text scratch pad content into block storage")
            return [block]
        except Exception:
            logger.exception("Failed during migration from plain text scratch pad")
            return None


__all__ = [
    "Block",
    "BlockStorage",
]
