import json
import sys

import yaml
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import clear_input_style, get_error_input_style, get_tool_style


class YAMLToJSONConverter:
    """Backend class for converting YAML to JSON with proper validation."""

    def __init__(self):
        self.last_error = None

    def convert_yaml_to_json(self, yaml_text: str, indent: int = 2) -> str:
        """
        Convert YAML text to JSON format.

        Args:
            yaml_text: The YAML string to convert
            indent: Number of spaces for JSON indentation (default: 2)

        Returns:
            JSON string representation of the YAML data

        Raises:
            ValueError: If YAML parsing fails
        """
        try:
            self.last_error = None

            # Handle empty input
            if not yaml_text.strip():
                return ""

            # Parse YAML
            yaml_data = yaml.safe_load(yaml_text)

            # Convert to JSON with specified indentation
            return json.dumps(yaml_data, indent=indent, ensure_ascii=False)

        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error: {e!s}"
            self.last_error = error_msg
            raise ValueError(error_msg) from e
        except json.JSONEncodeError as e:
            error_msg = f"JSON encoding error: {e!s}"
            self.last_error = error_msg
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Conversion error: {e!s}"
            self.last_error = error_msg
            raise ValueError(error_msg) from e

    def validate_yaml(self, yaml_text: str) -> bool:
        """
        Validate if the given text is valid YAML.

        Args:
            yaml_text: The YAML string to validate

        Returns:
            True if valid YAML, False otherwise
        """
        try:
            self.last_error = None

            if not yaml_text.strip():
                return True  # Empty string is valid

            yaml.safe_load(yaml_text)
            return True

        except yaml.YAMLError as e:
            self.last_error = f"YAML validation error: {e!s}"
            return False
        except Exception as e:
            self.last_error = f"Validation error: {e!s}"
            return False

    def get_last_error(self) -> str:
        """
        Get the last error message.

        Returns:
            The last error message or None if no error occurred
        """
        return self.last_error

    def get_sample_yaml(self) -> str:
        """
        Get a sample YAML string for demonstration.

        Returns:
            A sample YAML string
        """
        return """# Sample YAML data
name: John Doe
age: 30
email: john.doe@example.com
address:
  street: 123 Main St
  city: Anytown
  state: CA
  zip: 12345
skills:
  - Python
  - JavaScript
  - Docker
  - Kubernetes
active: true
salary: 75000.50"""


# ruff: noqa: C901
def create_yaml_to_json_widget(style_func, scratch_pad=None):
    """
    Creates and returns the YAML to JSON converter widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete YAML to JSON converter widget.
    """
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    # Main horizontal layout with splitter
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    main_splitter = QSplitter(Qt.Orientation.Horizontal)
    main_layout.addWidget(main_splitter, 1)

    # --- Left Pane (Input) ---
    input_pane = QWidget()
    input_layout = QVBoxLayout(input_pane)
    input_layout.setContentsMargins(10, 5, 5, 10)
    input_layout.setSpacing(5)

    input_buttons_layout = QHBoxLayout()
    input_buttons_layout.setContentsMargins(0, 0, 0, 0)
    input_buttons_layout.setSpacing(8)

    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    input_buttons_layout.addWidget(clipboard_button)
    input_buttons_layout.addWidget(sample_button)
    input_buttons_layout.addWidget(clear_button)
    input_buttons_layout.addStretch()

    input_layout.addLayout(input_buttons_layout)

    input_text_edit = QTextEdit()
    input_layout.addWidget(input_text_edit, 1)

    # --- Right Pane (Output) ---
    output_pane = QWidget()
    output_pane.setObjectName("pane")
    output_layout = QVBoxLayout(output_pane)
    output_layout.setContentsMargins(10, 5, 5, 10)
    output_layout.setSpacing(5)

    output_header_layout = QHBoxLayout()
    output_header_layout.setSpacing(8)
    output_header_layout.setContentsMargins(0, 0, 0, 0)

    spaces_combo = QComboBox()
    spaces_combo.addItem("2 spaces")
    spaces_combo.addItem("4 spaces")

    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages.

    # Add "Send to Scratch Pad" button if scratch_pad is provided
    if scratch_pad:
        send_to_scratch_pad_button = QPushButton("Send to Scratch Pad")
        send_to_scratch_pad_button.clicked.connect(
            lambda: send_to_scratch_pad(scratch_pad, output_text_edit.toPlainText())
        )
        output_header_layout.addWidget(send_to_scratch_pad_button)

    output_header_layout.addStretch()
    output_header_layout.addWidget(spaces_combo)
    output_header_layout.addWidget(copy_button)
    output_layout.addLayout(output_header_layout)

    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    placeholder_text_output = "Tips:\n- Right Click → Show Line Numbers\n- Right Click → Line Wrapping"
    output_text_edit.setPlaceholderText(placeholder_text_output)

    # Enable custom context menu for output text edit
    output_text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    # State variables for context menu options
    show_line_numbers = False
    line_wrapping_enabled = True

    def create_output_context_menu(position):
        """Create and show context menu for output text edit."""
        nonlocal show_line_numbers, line_wrapping_enabled

        menu = output_text_edit.createStandardContextMenu()
        menu.addSeparator()

        # Line numbers toggle
        line_numbers_action = QAction("Hide Line Numbers" if show_line_numbers else "Show Line Numbers", menu)
        line_numbers_action.triggered.connect(toggle_line_numbers)
        menu.addAction(line_numbers_action)

        # Line wrapping toggle
        line_wrap_action = QAction("Disable Line Wrapping" if line_wrapping_enabled else "Enable Line Wrapping", menu)
        line_wrap_action.triggered.connect(toggle_line_wrapping)
        menu.addAction(line_wrap_action)

        menu.exec(output_text_edit.mapToGlobal(position))

    def toggle_line_numbers():
        """Toggle line numbers display in output."""
        nonlocal show_line_numbers
        show_line_numbers = not show_line_numbers

        if show_line_numbers:
            # Add line numbers to current content
            current_text = output_text_edit.toPlainText()
            if current_text:
                lines = current_text.split("\n")
                numbered_lines = [f"{i + 1:3d}: {line}" for i, line in enumerate(lines)]
                output_text_edit.setPlainText("\n".join(numbered_lines))
        else:
            # Remove line numbers from current content
            current_text = output_text_edit.toPlainText()
            if current_text and current_text.strip():
                lines = current_text.split("\n")
                # Remove line numbers (format: "  1: content")
                clean_lines = []
                for line in lines:
                    if len(line) > 4 and line[3:5] == ": ":
                        clean_lines.append(line[5:])
                    else:
                        clean_lines.append(line)
                output_text_edit.setPlainText("\n".join(clean_lines))

    def toggle_line_wrapping():
        """Toggle line wrapping in output."""
        nonlocal line_wrapping_enabled
        line_wrapping_enabled = not line_wrapping_enabled

        if line_wrapping_enabled:
            output_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            output_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    # Connect context menu
    output_text_edit.customContextMenuRequested.connect(create_output_context_menu)

    output_layout.addWidget(output_text_edit, 1)

    # --- Assemble Main Layout ---
    main_splitter.addWidget(input_pane)
    main_splitter.addWidget(output_pane)
    main_splitter.setSizes([400, 400])  # Equal split

    # --- Backend Integration ---
    converter = YAMLToJSONConverter()

    # Timer for debounced real-time processing
    conversion_timer = QTimer()
    conversion_timer.setSingleShot(True)
    conversion_timer.timeout.connect(lambda: process_yaml_input())

    def get_indent_from_combo():
        """Get indentation value from combo box."""
        text = spaces_combo.currentText()
        return 4 if "4" in text else 2

    def process_yaml_input():
        """Process YAML input and update output with debouncing."""
        yaml_text = input_text_edit.toPlainText()

        if not yaml_text.strip():
            output_text_edit.clear()
            return

        try:
            indent = get_indent_from_combo()
            json_output = converter.convert_yaml_to_json(yaml_text, indent)
            output_text_edit.setPlainText(json_output)

            # Reset input styling on successful conversion
            input_text_edit.setStyleSheet(clear_input_style())

        except ValueError as e:
            # Show error in output and highlight input with red border
            error_msg = f"Error: {e!s}"
            output_text_edit.setPlainText(error_msg)

            # Add red border to input to indicate error
            input_text_edit.setStyleSheet(get_error_input_style())

    def on_input_changed():
        """Handle input text changes with debouncing."""
        conversion_timer.stop()
        conversion_timer.start(300)  # 300ms debounce

    def on_spaces_changed():
        """Handle spaces combo box changes."""
        if input_text_edit.toPlainText().strip():
            process_yaml_input()

    def on_clipboard_clicked():
        """Handle clipboard button click to paste YAML content."""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()

        if clipboard_text:
            input_text_edit.setPlainText(clipboard_text)
            # The textChanged signal will automatically trigger conversion

    def on_sample_clicked():
        """Handle sample button click to load sample YAML data."""
        sample_yaml = converter.get_sample_yaml()
        input_text_edit.setPlainText(sample_yaml)
        # The textChanged signal will automatically trigger conversion

    def on_clear_clicked():
        """Handle clear button click to clear input text area."""
        input_text_edit.clear()
        output_text_edit.clear()
        # Reset input styling to normal
        input_text_edit.setStyleSheet(clear_input_style())

    def on_copy_clicked():
        """Handle copy button click to copy JSON output to clipboard."""
        from PyQt6.QtWidgets import QApplication

        output_text = output_text_edit.toPlainText()

        if output_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(output_text)

    # Connect signals
    input_text_edit.textChanged.connect(on_input_changed)
    spaces_combo.currentTextChanged.connect(on_spaces_changed)
    clipboard_button.clicked.connect(on_clipboard_clicked)
    sample_button.clicked.connect(on_sample_clicked)
    clear_button.clicked.connect(on_clear_clicked)
    copy_button.clicked.connect(on_copy_clicked)

    return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("YAML to JSON Converter")
    main_window.setGeometry(100, 100, 900, 600)

    # The create function needs a style function/object
    tool_widget = create_yaml_to_json_widget(app.style, None)

    main_window.setCentralWidget(tool_widget)
    main_window.show()
    sys.exit(app.exec())


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
