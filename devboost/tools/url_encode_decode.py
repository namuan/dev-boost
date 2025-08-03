import logging
import sys
import urllib.parse

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_dialog_style, get_tool_style

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
            else:
                # Use quote_plus for standard URL encoding (spaces become +)
                if self.settings.plus_for_space:
                    return urllib.parse.quote_plus(text, safe=safe_chars)
                else:
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
            else:
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


class URLCodecSettingsDialog(QDialog):
    """Settings dialog for URL encoding options."""

    def __init__(self, settings: URLCodecSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("URL Encoding Settings")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the settings dialog UI."""
        self.setStyleSheet(get_dialog_style())

        layout = QVBoxLayout(self)

        # Encoding Type Group
        encoding_group = QGroupBox("Encoding Type")
        encoding_layout = QVBoxLayout(encoding_group)

        self.standard_radio = QRadioButton("Standard URL Encoding (+ for spaces)")
        self.component_radio = QRadioButton("Component Encoding (%20 for spaces)")

        encoding_layout.addWidget(self.standard_radio)
        encoding_layout.addWidget(self.component_radio)

        # Space Handling Group
        space_group = QGroupBox("Space Handling")
        space_layout = QVBoxLayout(space_group)

        self.plus_space_checkbox = QCheckBox("Use + for spaces (when applicable)")
        space_layout.addWidget(self.plus_space_checkbox)

        # Safe Characters Group
        safe_group = QGroupBox("Safe Characters")
        safe_layout = QGridLayout(safe_group)

        safe_layout.addWidget(QLabel("Preset Safe Characters:"), 0, 0)
        self.safe_preset_combo = QComboBox()
        self.safe_preset_combo.addItems([
            "None",
            "Alphanumeric only",
            "URL safe: -_.~",
            "Extended: -_.~:/?#[]@!$&'()*+,;=",
        ])
        safe_layout.addWidget(self.safe_preset_combo, 0, 1)

        safe_layout.addWidget(QLabel("Custom Safe Characters:"), 1, 0)
        self.custom_safe_edit = QLineEdit()
        self.custom_safe_edit.setPlaceholderText("Enter additional safe characters")
        safe_layout.addWidget(self.custom_safe_edit, 1, 1)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Add to main layout
        layout.addWidget(encoding_group)
        layout.addWidget(space_group)
        layout.addWidget(safe_group)
        layout.addStretch()
        layout.addWidget(button_box)

        # Connect signals
        self.safe_preset_combo.currentTextChanged.connect(self.update_safe_characters)

    def load_settings(self):
        """Load current settings into the dialog."""
        if self.settings.encoding_type == "component":
            self.component_radio.setChecked(True)
        else:
            self.standard_radio.setChecked(True)

        self.plus_space_checkbox.setChecked(self.settings.plus_for_space)
        self.custom_safe_edit.setText(self.settings.custom_safe_chars)

        # Set preset based on current safe characters
        if self.settings.safe_characters == "":
            self.safe_preset_combo.setCurrentText("None")
        elif self.settings.safe_characters == "-_.~":
            self.safe_preset_combo.setCurrentText("URL safe: -_.~")
        elif self.settings.safe_characters == "-_.~:/?#[]@!$&'()*+,;=":
            self.safe_preset_combo.setCurrentText("Extended: -_.~:/?#[]@!$&'()*+,;=")

    def update_safe_characters(self, preset_text: str):
        """Update safe characters based on preset selection."""
        preset_map = {
            "None": "",
            "Alphanumeric only": "",
            "URL safe: -_.~": "-_.~",
            "Extended: -_.~:/?#[]@!$&'()*+,;=": "-_.~:/?#[]@!$&'()*+,;=",
        }
        self.settings.safe_characters = preset_map.get(preset_text, "")

    def accept(self):
        """Save settings when dialog is accepted."""
        self.settings.encoding_type = "component" if self.component_radio.isChecked() else "standard"
        self.settings.plus_for_space = self.plus_space_checkbox.isChecked()
        self.settings.custom_safe_chars = self.custom_safe_edit.text()

        # Update safe characters from preset
        self.update_safe_characters(self.safe_preset_combo.currentText())

        super().accept()


# ruff: noqa: C901
def create_url_codec_widget(style_func):
    """
    Creates and returns the URL Encode/Decode widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete URL encoder/decoder widget.
    """
    logger.info("Creating URL Encode/Decode widget")
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(0)

    # --- TOP INPUT SECTION ---
    input_section_layout = QVBoxLayout()
    input_section_layout.setSpacing(8)
    input_section_layout.setContentsMargins(0, 0, 0, 12)

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
    output_section_layout = QVBoxLayout()
    output_section_layout.setSpacing(8)
    output_section_layout.setContentsMargins(0, 12, 0, 0)

    # Output Controls Bar
    output_bar_layout = QHBoxLayout()
    output_bar_layout.setSpacing(8)

    output_label = QLabel("Output:")

    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages, one slightly offset.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))  # Placeholder

    use_as_input_button = QPushButton("Use as input")
    # Image description: An upward-pointing arrow icon, simple and bold.
    use_as_input_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))  # Placeholder

    output_bar_layout.addWidget(output_label)
    output_bar_layout.addStretch()
    output_bar_layout.addWidget(copy_button)
    output_bar_layout.addWidget(use_as_input_button)
    output_section_layout.addLayout(output_bar_layout)

    # Output Text Edit
    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    output_text_edit.setMinimumHeight(180)
    output_section_layout.addWidget(output_text_edit, 1)

    main_layout.addLayout(input_section_layout, 1)

    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    main_layout.addWidget(separator)

    main_layout.addLayout(output_section_layout, 1)

    # --- BACKEND FUNCTIONALITY CONNECTIONS ---
    settings = URLCodecSettings()
    codec = URLCodec(settings)

    def process_text():
        """Process input text based on selected mode (encode/decode)."""
        input_text = input_text_edit.toPlainText()

        result = codec.encode_url(input_text) if encode_radio.isChecked() else codec.decode_url(input_text)

        output_text_edit.setPlainText(result)

    def open_settings():
        """Open settings dialog."""
        dialog = URLCodecSettingsDialog(settings, widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Settings were updated, reprocess current text
            process_text()

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

    # Connect signals
    input_text_edit.textChanged.connect(on_input_changed)
    encode_radio.toggled.connect(process_text)
    decode_radio.toggled.connect(process_text)
    sample_button.clicked.connect(load_sample)
    clear_button.clicked.connect(clear_input)
    copy_button.clicked.connect(copy_to_clipboard)
    clipboard_button.clicked.connect(paste_from_clipboard)
    use_as_input_button.clicked.connect(use_output_as_input)

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
