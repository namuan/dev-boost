import logging

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

logger = logging.getLogger(__name__)


class MarkdownHighlighter(QSyntaxHighlighter):
    """A very lightweight Markdown syntax highlighter for QTextDocument.

    This covers common patterns: headings, inline code, emphasis, and links.
    It is intentionally simple to keep performance acceptable while providing
    visual cues.
    """

    def __init__(self, document):
        super().__init__(document)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._init_formats()

    def _init_formats(self) -> None:
        # Headings: #, ##, ..., ######
        heading_format = QTextCharFormat()
        heading_format.setFontWeight(QFont.Weight.Bold)
        heading_format.setForeground(QColor("#2e7d32"))  # greenish
        self._rules.append((QRegularExpression(r"^(#{1,6})\s.*"), heading_format))

        # Inline code: `code`
        code_format = QTextCharFormat()
        code_format.setFontFamily("monospace")
        code_format.setForeground(QColor("#6d4c41"))  # brownish
        self._rules.append((QRegularExpression(r"`[^`]+`"), code_format))

        # Emphasis: *italic* and **bold** (basic)
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        self._rules.append((QRegularExpression(r"\*[^*]+\*"), italic_format))

        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        self._rules.append((QRegularExpression(r"\*\*[^*]+\*\*"), bold_format))

        # Links: [text](url)
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#1565c0"))  # blue
        self._rules.append((QRegularExpression(r"\[[^\]]+\]\([^\)]+\)"), link_format))

    def highlightBlock(self, text: str) -> None:
        try:
            for regex, fmt in self._rules:
                i = regex.globalMatch(text)
                while i.hasNext():
                    match = i.next()
                    self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
        except Exception:
            logger.exception("MarkdownHighlighter encountered an error while highlighting")


__all__ = ["MarkdownHighlighter"]
