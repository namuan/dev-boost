import logging
import sys
import urllib.parse

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSplitter,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style

logger = logging.getLogger(__name__)


class URLCodecSettings:
    """Settings for URL encoding/decoding."""

    def __init__(self):
        self.encoding_type = "standard"  # "standard" or "component"
        self.safe_characters = ""
        self.plus_for_space = True
        self.custom_safe_chars = ""


class URLCodec:
    """Backend logic for URL encoding and decoding."""

    def __init__(self, settings: URLCodecSettings = None):
        self.settings = settings or URLCodecSettings()

    def encode_url(self, text: str) -> str:
        """Encode text for safe URL transmission.

        Args:
            text: Text to encode

        Returns:
            URL-encoded string
        """
        if not text:
            return ""

        try:
            safe_chars = self.settings.safe_characters + self.settings.custom_safe_chars

            if self.settings.encoding_type == "component":
                # Use quote for component encoding (spaces become %20)
                return urllib.parse.quote(text, safe=safe_chars)
            # Use quote_plus for standard URL encoding (spaces become +)
            if self.settings.plus_for_space:
                return urllib.parse.quote_plus(text, safe=safe_chars)
            return urllib.parse.quote(text, safe=safe_chars)
        except Exception as e:
            logger.exception("Error encoding URL")
            return f"Error: {e!s}"

    def decode_url(self, text: str) -> str:
        """Decode URL-encoded text.

        Args:
            text: URL-encoded text to decode

        Returns:
            Decoded string
        """
        if not text:
            return ""

        try:
            if self.settings.plus_for_space:
                # Use unquote_plus to handle both %20 and + for spaces
                return urllib.parse.unquote_plus(text)
            # Use unquote for standard decoding
            return urllib.parse.unquote(text)
        except Exception as e:
            logger.exception("Error decoding URL")
            return f"Error: {e!s}"

    @staticmethod
    def encode_url_component(text: str) -> str:
        """Encode text as URL component (spaces become %20).

        Args:
            text: Text to encode

        Returns:
            URL component encoded string
        """
        if not text:
            return ""

        try:
            # Use quote for component encoding (spaces become %20)
            return urllib.parse.quote(text, safe="")
        except Exception as e:
            logger.exception("Error encoding URL component")
            return f"Error: {e!s}"

    @staticmethod
    def decode_url_component(text: str) -> str:
        """Decode URL component encoded text.

        Args:
            text: URL component encoded text to decode

        Returns:
            Decoded string
        """
        if not text:
            return ""

        try:
            # Use unquote for component decoding
            return urllib.parse.unquote(text)
        except Exception as e:
            logger.exception("Error decoding URL component")
            return f"Error: {e!s}"


# ruff: noqa: C901
def create_url_codec_widget(style_func, scratch_pad=None):
    """
    Creates and returns the URL Encode/Decode widget.

    Args:
        style_func: Function to get QStyle for standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The complete URL encoder/decoder widget.
    """
    logger.info("Creating URL Encode/Decode widget")
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    main_splitter = QSplitter(Qt.Orientation.Vertical)
    main_layout.addWidget(main_splitter)

    # --- TOP INPUT SECTION ---
    input_section_widget = QWidget()
    input_section_layout = QVBoxLayout(input_section_widget)
    input_section_layout.setContentsMargins(10, 5, 5, 10)
    input_section_layout.setSpacing(5)

    # Top Bar: Controls and Mode Selection
    top_bar_layout = QHBoxLayout()
    top_bar_layout.setSpacing(8)

    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    top_bar_layout.addWidget(clipboard_button)
    top_bar_layout.addWidget(sample_button)
    top_bar_layout.addWidget(clear_button)
    top_bar_layout.addSpacing(4)
    top_bar_layout.addStretch()

    encode_radio = QRadioButton("Encode")
    encode_radio.setChecked(True)
    decode_radio = QRadioButton("Decode")

    radio_group = QButtonGroup(widget)
    radio_group.addButton(encode_radio)
    radio_group.addButton(decode_radio)

    top_bar_layout.addWidget(encode_radio)
    top_bar_layout.addWidget(decode_radio)
    input_section_layout.addLayout(top_bar_layout)

    # Input Text Edit
    input_text_edit = QTextEdit()
    input_text_edit.setMinimumHeight(180)
    input_section_layout.addWidget(input_text_edit, 1)

    # --- BOTTOM OUTPUT SECTION ---
    output_section_widget = QWidget()
    output_section_layout = QVBoxLayout(output_section_widget)
    output_section_layout.setSpacing(5)
    output_section_layout.setContentsMargins(10, 5, 5, 10)

    # Output Controls Bar
    output_bar_layout = QHBoxLayout()
    output_bar_layout.setSpacing(8)

    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages.

    # Add "Send to Scratch Pad" button if scratch_pad is provided
    send_to_scratch_pad_button = None
    if scratch_pad:
        send_to_scratch_pad_button = QPushButton("Send to Scratch Pad")

    use_as_input_button = QPushButton("Use as input")
    # Image description: An upward-pointing arrow icon, simple and bold.
    use_as_input_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))  # Placeholder

    output_bar_layout.addStretch()
    output_bar_layout.addWidget(copy_button)
    if send_to_scratch_pad_button:
        output_bar_layout.addWidget(send_to_scratch_pad_button)
    output_bar_layout.addWidget(use_as_input_button)
    output_section_layout.addLayout(output_bar_layout)

    # Output Text Edit
    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    output_text_edit.setMinimumHeight(180)
    output_section_layout.addWidget(output_text_edit, 1)

    main_splitter.addWidget(input_section_widget)
    main_splitter.addWidget(output_section_widget)
    main_splitter.setSizes([300, 300])  # Equal split

    # --- BACKEND FUNCTIONALITY CONNECTIONS ---
    settings = URLCodecSettings()
    codec = URLCodec(settings)

    def process_text():
        """Process input text based on selected mode (encode/decode)."""
        input_text = input_text_edit.toPlainText()

        result = codec.encode_url(input_text) if encode_radio.isChecked() else codec.decode_url(input_text)

        output_text_edit.setPlainText(result)

    def on_input_changed():
        """Handle input text changes with debouncing."""
        # Use a timer to debounce rapid text changes
        if hasattr(widget, "_timer"):
            widget._timer.stop()

        widget._timer = QTimer()
        widget._timer.setSingleShot(True)
        widget._timer.timeout.connect(process_text)
        widget._timer.start(300)  # 300ms delay

    def load_sample():
        """Load sample text for demonstration."""
        sample_text = "Hello World! This is a test URL: https://example.com/search?q=test query&category=demo"
        input_text_edit.setPlainText(sample_text)

    def clear_input():
        """Clear input text."""
        input_text_edit.clear()
        output_text_edit.clear()

    def copy_to_clipboard():
        """Copy output text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(output_text_edit.toPlainText())

    def paste_from_clipboard():
        """Paste text from clipboard to input."""
        clipboard = QApplication.clipboard()
        input_text_edit.setPlainText(clipboard.text())

    def use_output_as_input():
        """Use output text as new input."""
        output_text = output_text_edit.toPlainText()
        input_text_edit.setPlainText(output_text)

    def send_to_scratch_pad(scratch_pad, content):
        """
        Send content to the scratch pad.

        Args:
            scratch_pad: The scratch pad widget.
            content (str): The content to send.
        """
        if scratch_pad and content:
            # Append content to the scratch pad with a separator
            current_content = scratch_pad.get_content()
            new_content = f"{current_content}\n\n---\n{content}" if current_content else content
            scratch_pad.set_content(new_content)

    def format_url_codec_output_for_scratch_pad(input_text, output_text, mode):
        """
        Format URL Codec output for sending to scratch pad with context.

        Args:
            input_text (str): The input text
            output_text (str): The output text
            mode (str): The mode ("Encode" or "Decode")

        Returns:
            str: Formatted content for scratch pad
        """
        # Create a header with context
        header = f"URL Codec Results\nMode: {mode}\n" + "=" * 50

        # Add input and output sections
        input_section = f"INPUT:\n{input_text}"
        output_section = f"\n\nOUTPUT:\n{output_text}"

        return f"{header}\n{input_section}{output_section}"

    # Connect signals
    input_text_edit.textChanged.connect(on_input_changed)
    encode_radio.toggled.connect(process_text)
    decode_radio.toggled.connect(process_text)
    sample_button.clicked.connect(load_sample)
    clear_button.clicked.connect(clear_input)
    copy_button.clicked.connect(copy_to_clipboard)
    clipboard_button.clicked.connect(paste_from_clipboard)
    use_as_input_button.clicked.connect(use_output_as_input)

    # Connect "Send to Scratch Pad" button if it exists
    if send_to_scratch_pad_button:

        def on_send_to_scratch_pad():
            # Get current state for formatting
            input_text = input_text_edit.toPlainText()
            output_text = output_text_edit.toPlainText()
            mode = "Encode" if encode_radio.isChecked() else "Decode"

            # Format with context
            formatted_content = format_url_codec_output_for_scratch_pad(input_text, output_text, mode)
            send_to_scratch_pad(scratch_pad, formatted_content)

        send_to_scratch_pad_button.clicked.connect(on_send_to_scratch_pad)

    logger.info("URL Codec widget creation completed")
    return widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("URL Encoder/Decoder Tool")
    main_window.setGeometry(100, 100, 800, 600)

    url_tool_widget = create_url_codec_widget(app.style)

    main_window.setCentralWidget(url_tool_widget)

    main_window.show()
    sys.exit(app.exec())
