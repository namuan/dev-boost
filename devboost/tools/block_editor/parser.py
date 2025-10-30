import logging
import re
from collections.abc import Iterable
from datetime import datetime

from .storage import Block

logger = logging.getLogger(__name__)


_BLOCK_START_RE = re.compile(r"^###\s*(?P<title>.*?)\s*(?:\[(?P<lang>[\w\-]+)\])?\s*$")


def _new_block_id() -> str:
    return f"blk-{int(datetime.utcnow().timestamp() * 1000)}"


def parse_blocks_from_text(text: str) -> list[Block]:
    """
    Parse a plain text buffer into blocks using a simple delimiter syntax.

    Delimiter format:
        ### Block Title [language]

    Everything until the next delimiter or end-of-text is considered the content of that block.
    If no delimiter appears at the beginning, the text is treated as a single 'Untitled' block.
    """
    lines = text.splitlines()
    blocks: list[Block] = []
    current_title = None
    current_lang = "plain"
    current_lines: list[str] = []
    order = 0

    def _flush_block() -> None:
        nonlocal order, current_title, current_lang, current_lines
        if current_lines or current_title is not None:
            content = "\n".join(current_lines).rstrip()
            title = current_title or "Untitled"
            blocks.append(
                Block(
                    id=_new_block_id(),
                    title=title,
                    language=current_lang or "plain",
                    content=content,
                    order=order,
                )
            )
            logger.debug("Parsed block '%s' (lang=%s, order=%d, len=%d)", title, current_lang, order, len(content))
            order += 1
        current_title = None
        current_lang = "plain"
        current_lines = []

    found_delimiter = False
    for line in lines:
        m = _BLOCK_START_RE.match(line)
        if m:
            found_delimiter = True
            # Emit previous block
            _flush_block()
            current_title = (m.group("title") or "Untitled").strip()
            current_lang = (m.group("lang") or "plain").strip()
        else:
            current_lines.append(line)

    # Final flush
    _flush_block()

    if not blocks and not found_delimiter:
        # Entire text as single block
        blocks.append(
            Block(
                id=_new_block_id(),
                title="Untitled",
                language="plain",
                content=text.rstrip(),
                order=0,
            )
        )
        logger.debug("Parsed single Untitled block from text (len=%d)", len(text))

    return blocks


def serialize_blocks_to_text(blocks: Iterable[Block]) -> str:
    """Serialize blocks back into the delimiter-based plain text format."""
    parts: list[str] = []
    for b in sorted(blocks, key=lambda x: x.order):
        title = b.title.strip() or "Untitled"
        lang = b.language.strip() or "plain"
        header = f"### {title} [{lang}]"
        parts.append(header)
        if b.content:
            parts.append(b.content.rstrip())
    return "\n".join(parts).rstrip() + "\n"
