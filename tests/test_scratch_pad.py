import pytest
from PyQt6.QtWidgets import QApplication

from devboost.tools.scratch_pad import ScratchPadWidget


class TestScratchPadWidget:
    """Test cases for ScratchPadWidget functionality."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def scratch_pad_widget(self, app):
        """Create ScratchPadWidget instance for testing."""
        return ScratchPadWidget()

    def test_plain_text_mode_by_default(self, scratch_pad_widget):
        """Test that the scratch pad is in plain text mode by default."""
        # Check that rich text is disabled by default
        assert not scratch_pad_widget.text_edit.acceptRichText(), "Scratch pad should be in plain text mode by default"

        # Try to set HTML content - it should be treated as plain text
        html_content = "<b>Bold text</b>"
        scratch_pad_widget.text_edit.setPlainText(html_content)

        # The content should remain as plain text (HTML tags visible)
        plain_text = scratch_pad_widget.text_edit.toPlainText()
        assert plain_text == html_content, "HTML should be treated as plain text"
