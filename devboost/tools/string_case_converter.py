import logging
import re
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_tool_style

# It's good practice to have a logger
logger = logging.getLogger(__name__)


class StringCaseConverter:
    """Backend class for string case conversion operations."""

    def __init__(self):
        """Initialize the StringCaseConverter."""
        logger.info("Initializing StringCaseConverter")

    def to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        if not text:
            return ""

        # Split by common delimiters and spaces
        words = re.split(r"[\s_\-\.]+", text.strip())
        if not words:
            return ""

        # First word lowercase, rest title case
        result = words[0].lower()
        for word in words[1:]:
            if word:
                result += word.capitalize()

        return result

    def to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        if not text:
            return ""

        # Split by common delimiters and spaces
        words = re.split(r"[\s_\-\.]+", text.strip())
        if not words:
            return ""

        # All words title case
        result = ""
        for word in words:
            if word:
                result += word.capitalize()

        return result

    def to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        if not text:
            return ""

        # Handle camelCase and PascalCase
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)

        # Split by common delimiters and spaces
        words = re.split(r"[\s_\-\.]+", text.strip())

        # Join with underscores and lowercase
        return "_".join(word.lower() for word in words if word)

    def to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case."""
        if not text:
            return ""

        # Handle camelCase and PascalCase
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)

        # Split by common delimiters and spaces
        words = re.split(r"[\s_\-\.]+", text.strip())

        # Join with hyphens and lowercase
        return "-".join(word.lower() for word in words if word)

    def to_header_case(self, text: str) -> str:
        """Convert text to Header-Case."""
        if not text:
            return ""

        # Handle camelCase and PascalCase
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)

        # Split by common delimiters and spaces
        words = re.split(r"[\s_\-\.]+", text.strip())

        # Join with hyphens and title case
        return "-".join(word.capitalize() for word in words if word)

    def to_uppercase(self, text: str) -> str:
        """Convert text to UPPERCASE."""
        return text.upper()

    def to_lowercase(self, text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()

    def to_title_case(self, text: str) -> str:
        """Convert text to Title Case."""
        if not text:
            return ""

        # Handle camelCase and PascalCase by adding spaces
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)

        # Split by common delimiters
        words = re.split(r"[\s_\-\.]+", text.strip())

        # Join with spaces and title case
        return " ".join(word.capitalize() for word in words if word)

    def convert_case(self, text: str, case_type: str) -> str:
        """Convert text to the specified case type."""
        if not text:
            return ""

        case_methods = {
            "camelCase": self.to_camel_case,
            "PascalCase": self.to_pascal_case,
            "snake_case": self.to_snake_case,
            "kebab-case": self.to_kebab_case,
            "Header-Case": self.to_header_case,
            "UPPERCASE": self.to_uppercase,
            "lowercase": self.to_lowercase,
            "Title Case": self.to_title_case,
        }

        method = case_methods.get(case_type)
        if method:
            return method(text)
        else:
            logger.warning(f"Unknown case type: {case_type}")
            return text


# ruff: noqa: C901
def create_case_converter_widget(style_func):
    """
    Creates and returns the String Case Converter widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete case converter widget.
    """
    logger.info("Creating String Case Converter widget")
    widget = QWidget()

    # Create backend converter instance
    converter = StringCaseConverter()

    # Timer for debounced input processing
    update_timer = QTimer()
    update_timer.setSingleShot(True)
    update_timer.timeout.connect(lambda: update_output())
    widget.setStyleSheet(get_tool_style())

    # Main layout is vertical
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # --- Top Controls Bar ---
    top_bar = QWidget()
    top_bar.setObjectName("topBar")
    top_bar_layout = QHBoxLayout(top_bar)
    top_bar_layout.setContentsMargins(10, 8, 10, 8)
    top_bar_layout.setSpacing(8)

    # Left side of top bar
    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    top_bar_layout.addWidget(clipboard_button)
    top_bar_layout.addWidget(sample_button)
    top_bar_layout.addWidget(clear_button)
    top_bar_layout.addStretch()

    # Right side of top bar
    case_combo = QComboBox()
    case_combo.addItems([
        "camelCase",
        "PascalCase",
        "snake_case",
        "kebab-case",
        "Header-Case",
        "UPPERCASE",
        "lowercase",
        "Title Case",
    ])
    copy_button = QPushButton("Copy")
    # Image description: A standard copy icon, depicting two overlapping pages.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))

    top_bar_layout.addWidget(case_combo)
    top_bar_layout.addWidget(copy_button)
    main_layout.addWidget(top_bar)

    # --- Content Area (Input/Output Panes) ---
    content_splitter = QSplitter(Qt.Orientation.Horizontal)

    # Input Pane (Left)
    input_text_edit = QTextEdit()
    content_splitter.addWidget(input_text_edit)

    # Output Pane (Right)
    output_pane_widget = QWidget()
    output_layout = QVBoxLayout(output_pane_widget)
    output_layout.setContentsMargins(0, 0, 0, 0)
    output_layout.setSpacing(0)

    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    output_layout.addWidget(output_text_edit)

    content_splitter.addWidget(output_pane_widget)
    content_splitter.setSizes([400, 400])  # Equal split

    main_layout.addWidget(content_splitter, 1)

    # --- Backend Integration Functions ---
    def update_output():
        """Update the output based on current input and selected case."""
        try:
            input_text = input_text_edit.toPlainText()
            selected_case = case_combo.currentText()

            if input_text.strip():
                converted_text = converter.convert_case(input_text, selected_case)
                output_text_edit.setPlainText(converted_text)
            else:
                output_text_edit.clear()
        except Exception as e:
            logger.exception("Error during case conversion")
            output_text_edit.setPlainText(f"Error: {e!s}")

    def on_input_changed():
        """Handle input text changes with debouncing."""
        update_timer.stop()
        update_timer.start(300)  # 300ms delay

    def on_case_changed():
        """Handle case selection changes."""
        update_output()

    def on_clipboard_clicked():
        """Load text from clipboard."""
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                input_text_edit.setPlainText(text)
                update_output()
        except Exception:
            logger.exception("Error loading from clipboard")

    def on_sample_clicked():
        """Load sample text."""
        sample_text = "Hello World Example Text"
        input_text_edit.setPlainText(sample_text)
        update_output()

    def on_clear_clicked():
        """Clear input and output."""
        input_text_edit.clear()
        output_text_edit.clear()

    def on_copy_clicked():
        """Copy output to clipboard."""
        try:
            output_text = output_text_edit.toPlainText()
            if output_text:
                clipboard = QApplication.clipboard()
                clipboard.setText(output_text)
                logger.info("Output copied to clipboard")
        except Exception:
            logger.exception("Error copying to clipboard")

    def on_lightning_clicked():
        """Quick convert - automatically detect best case and convert."""
        try:
            input_text = input_text_edit.toPlainText().strip()
            if not input_text:
                return

            # Auto-detect current case and suggest next logical conversion
            if "_" in input_text:
                # snake_case -> camelCase
                case_combo.setCurrentText("camelCase")
            elif "-" in input_text:
                # kebab-case -> camelCase
                case_combo.setCurrentText("camelCase")
            elif input_text.islower():
                # lowercase -> Title Case
                case_combo.setCurrentText("Title Case")
            elif input_text.isupper():
                # UPPERCASE -> lowercase
                case_combo.setCurrentText("lowercase")
            elif any(c.isupper() for c in input_text[1:]):
                # camelCase or PascalCase -> snake_case
                case_combo.setCurrentText("snake_case")
            else:
                # Default to camelCase
                case_combo.setCurrentText("camelCase")

            update_output()
        except Exception:
            logger.exception("Error in lightning conversion")

    # --- Connect UI Events ---
    input_text_edit.textChanged.connect(on_input_changed)
    case_combo.currentTextChanged.connect(on_case_changed)
    clipboard_button.clicked.connect(on_clipboard_clicked)
    sample_button.clicked.connect(on_sample_clicked)
    clear_button.clicked.connect(on_clear_clicked)
    copy_button.clicked.connect(on_copy_clicked)

    # Set initial case selection
    case_combo.setCurrentText("camelCase")

    logger.info("Case Converter widget creation completed")
    return widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    # Create a main window to host the widget
    main_window = QMainWindow()
    main_window.setWindowTitle("Case Converter Tool")
    main_window.setGeometry(100, 100, 900, 600)

    # The widget needs a function to get the application style
    case_converter_tool_widget = create_case_converter_widget(app.style)

    # Set the created widget as the central widget of the main window.
    main_window.setCentralWidget(case_converter_tool_widget)

    main_window.show()
    sys.exit(app.exec())
