import json
import logging

from defusedxml.minidom import parseString

logger = logging.getLogger(__name__)


def format_json(text: str) -> tuple[str | None, str | None]:
    """Attempt to pretty-format JSON.

    Returns (formatted_text, error_message). If formatting fails, formatted_text is None and error_message contains context.
    """
    try:
        parsed = json.loads(text)
        formatted = json.dumps(parsed, indent=2, sort_keys=True, ensure_ascii=False)
        return formatted, None
    except Exception as exc:
        msg = f"JSON format error: {exc}"
        logger.warning(msg)
        return None, msg


def format_xml(text: str) -> tuple[str | None, str | None]:
    """Attempt to pretty-format XML using minidom.

    Returns (formatted_text, error_message). Note: minidom may add whitespace/newlines.
    """
    try:
        dom = parseString(text)
        formatted = dom.toprettyxml(indent="  ")
        return formatted, None
    except Exception as exc:
        msg = f"XML format error: {exc}"
        logger.warning(msg)
        return None, msg


def try_auto_format(language: str, text: str) -> tuple[str | None, str | None]:
    """Auto-format content if language is supported.

    Supports: json, xml. Returns (formatted, error). Unsupported languages return (None, None).
    """
    lang = (language or "").lower()
    if lang == "json":
        return format_json(text)
    if lang == "xml":
        return format_xml(text)
    return None, None
