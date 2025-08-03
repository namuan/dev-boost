import json
import logging

from jsonpath_ng import parse
from PyQt6.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# It's good practice to have a logger
logger = logging.getLogger(__name__)


class JSONValidator(QObject):
    """
    Backend JSON validation logic with proper error handling.
    """

    validation_completed = pyqtSignal(str, bool, str)  # formatted_json, is_valid, error_message

    def __init__(self):
        super().__init__()

    def validate_and_format_json(self, input_text: str, indent_spaces: int = 2) -> tuple[bool, str, str]:
        """
        Validates and formats JSON string with proper error handling.

        Args:
            input_text: The input JSON string to validate
            indent_spaces: Number of spaces for indentation (2, 4, or 0 for tabs)

        Returns:
            Tuple of (is_valid, formatted_json, error_message)
        """
        if not input_text.strip():
            return False, "", "Input is empty"

        try:
            # Parse JSON to validate
            parsed_json = json.loads(input_text)

            # Format JSON with specified indentation
            if indent_spaces == 0:  # Use tabs
                formatted_json = json.dumps(parsed_json, indent="\t", ensure_ascii=False, sort_keys=True)
            else:
                formatted_json = json.dumps(parsed_json, indent=indent_spaces, ensure_ascii=False, sort_keys=True)

            return True, formatted_json, ""

        except json.JSONDecodeError as e:
            error_msg = f"JSON Decode Error at line {e.lineno}, column {e.colno}: {e.msg}"
            logger.exception(f"JSON validation failed: {error_msg}")
            return False, "", error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {e!s}"
            logger.exception(f"JSON validation failed: {error_msg}")
            return False, "", error_msg

    def minify_json(self, input_text: str) -> tuple[bool, str, str]:
        """
        Minifies JSON by removing whitespace.

        Args:
            input_text: The input JSON string to minify

        Returns:
            Tuple of (is_valid, minified_json, error_message)
        """
        if not input_text.strip():
            return False, "", "Input is empty"

        try:
            parsed_json = json.loads(input_text)
            minified_json = json.dumps(parsed_json, separators=(",", ":"), ensure_ascii=False)
            return True, minified_json, ""

        except json.JSONDecodeError as e:
            error_msg = f"JSON Decode Error at line {e.lineno}, column {e.colno}: {e.msg}"
            return False, "", error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {e!s}"
            return False, "", error_msg

    def get_sample_json(self) -> str:
        """
        Returns a sample JSON for testing purposes.
        """
        sample = {
            "name": "John Doe",
            "age": 30,
            "city": "New York",
            "hobbies": ["reading", "swimming", "coding"],
            "address": {"street": "123 Main St", "zipcode": "10001"},
            "active": True,
        }
        return json.dumps(sample, indent=2)

    def query_json_path(self, input_text: str, json_path: str) -> tuple[bool, str, str]:
        """
        Query JSON using JSONPath expression.

        Args:
            input_text: The input JSON string
            json_path: JSONPath expression (e.g., $.store.book[*].author)

        Returns:
            Tuple of (is_valid, result_json, error_message)
        """
        if not input_text.strip():
            return False, "", "Input is empty"

        if not json_path.strip():
            return False, "", "JSON Path is empty"

        try:
            # Parse JSON
            parsed_json = json.loads(input_text)

            # Parse JSONPath expression
            jsonpath_expr = parse(json_path)

            # Execute query
            matches = [match.value for match in jsonpath_expr.find(parsed_json)]

            if not matches:
                return True, "[]", "No matches found"

            # Format result
            result = matches[0] if len(matches) == 1 else matches

            result_json = json.dumps(result, indent=2, ensure_ascii=False)
            return True, result_json, ""

        except json.JSONDecodeError as e:
            error_msg = f"JSON Decode Error at line {e.lineno}, column {e.colno}: {e.msg}"
            return False, "", error_msg

        except Exception as e:
            error_msg = f"JSONPath Error: {e!s}"
            return False, "", error_msg


# ruff: noqa: C901
def create_json_formatter_widget(style_func):
    """
    Creates the main widget for the JSON formatter tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.

    Returns:
        QWidget: The main widget for the tool.
    """
    widget = QWidget()

    # Create JSON validator instance
    json_validator = JSONValidator()
    widget.setStyleSheet("""
        QWidget {
            background-color: #F8F9FA;
            color: #212529;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        QTextEdit, QLineEdit {
            background-color: #FFFFFF;
            border: 1px solid #DEE2E6;
            border-radius: 4px;
            padding: 8px;
            font-family: "Menlo", "Monaco", "Consolas", "Courier New", monospace;
            font-size: 13px;
        }
        QTextEdit {
            color: #6c757d;
        }
        QPushButton {
            background-color: #F8F9FA;
            border: 1px solid #CED4DA;
            border-radius: 4px;
            padding: 5px 10px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #E9ECEF;
        }
        QPushButton#iconButton {
            border: none;
            padding: 5px;
        }
        QPushButton#iconButton:hover {
            background-color: #E9ECEF;
        }
        QPushButton#jsonToggleButton {
             border: none;
             padding: 0px;
        }
        QSplitter::handle {
            background-color: #DEE2E6;
        }
        QSplitter::handle:horizontal {
            width: 1px;
        }
        QLabel {
            font-size: 14px;
            font-weight: 500;
        }
        QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #CED4DA;
            border-radius: 4px;
            padding: 4px;
            min-width: 6em;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            /* Using a standard icon for the dropdown arrow */
        }
        QLineEdit#jsonPathInput {
            border: none;
            background-color: #F8F9FA;
            padding: 6px;
        }
    """)

    # Main layout
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Splitter
    splitter = QSplitter(Qt.Orientation.Horizontal)
    main_layout.addWidget(splitter, 1)

    # --- Left Pane (Input) ---
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(10, 5, 5, 10)
    left_layout.setSpacing(5)

    # Input Toolbar
    input_toolbar_layout = QHBoxLayout()
    input_toolbar_layout.setSpacing(8)

    input_toolbar_layout.addWidget(QLabel("Input:"))

    run_button = QPushButton()
    run_button.setObjectName("iconButton")
    # Image description: A simple, black, solid lightning bolt icon.
    run_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))  # Placeholder
    input_toolbar_layout.addWidget(run_button)

    input_toolbar_layout.addWidget(QPushButton("Clipboard"))
    input_toolbar_layout.addWidget(QPushButton("Sample"))
    input_toolbar_layout.addWidget(QPushButton("Clear"))
    input_toolbar_layout.addStretch()

    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A black gear icon for settings, classic cogwheel shape.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
    input_toolbar_layout.addWidget(settings_button)

    input_toolbar_layout.addWidget(QPushButton("JSON"))

    json_toggle_button = QPushButton()
    json_toggle_button.setObjectName("jsonToggleButton")
    # Image description: A blue rectangular icon with two white vertical arrows inside. One arrow points up, the other points down.
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(6, 4, 20, 24, QColor("#4285F4"))
    painter.setPen(Qt.GlobalColor.white)
    # Up arrow
    painter.drawLine(16, 8, 12, 14)
    painter.drawLine(16, 8, 20, 14)
    # Down arrow
    painter.drawLine(16, 24, 12, 18)
    painter.drawLine(16, 24, 20, 18)
    painter.end()
    json_toggle_button.setIcon(QIcon(pixmap))
    json_toggle_button.setIconSize(QSize(20, 20))
    input_toolbar_layout.addWidget(json_toggle_button)

    left_layout.addLayout(input_toolbar_layout)

    # Input Text Area
    input_text_edit = QTextEdit()
    input_text_edit.setPlaceholderText(
        "— Enter Your Text\n"
        "— Drag/Drop Files\n"
        "— Right Click → Load from File...\n"
        "— ⌘ + F to Search\n"
        "— ⌘ + ⇧ + F to Replace"
    )
    left_layout.addWidget(input_text_edit)
    splitter.addWidget(left_pane)

    # --- Right Pane (Output) ---
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(5, 5, 10, 10)
    right_layout.setSpacing(5)

    # Output Toolbar
    output_toolbar_layout = QHBoxLayout()
    output_toolbar_layout.setSpacing(8)

    output_toolbar_layout.addWidget(QLabel("Output:"))
    output_toolbar_layout.addStretch()

    spaces_combo = QComboBox()
    spaces_combo.addItem("2 spaces")
    spaces_combo.addItem("4 spaces")
    spaces_combo.addItem("Tabs")
    output_toolbar_layout.addWidget(spaces_combo)

    copy_button = QPushButton("Copy")
    # Image description: A simple black icon of two overlapping squares, representing 'copy'.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon))  # Placeholder
    output_toolbar_layout.addWidget(copy_button)

    right_layout.addLayout(output_toolbar_layout)

    # Output Text Area
    output_text_edit = QTextEdit()
    output_text_edit.setPlaceholderText("Right click → Save to file...")
    right_layout.addWidget(output_text_edit)
    splitter.addWidget(right_pane)

    splitter.setSizes([300, 300])

    # --- Bottom Bar ---
    bottom_bar = QFrame()
    bottom_bar.setFrameShape(QFrame.Shape.NoFrame)
    bottom_bar.setFixedHeight(35)
    bottom_bar.setStyleSheet("background-color: #F8F9FA; border-top: 1px solid #DEE2E6;")

    bottom_layout = QHBoxLayout(bottom_bar)
    bottom_layout.setContentsMargins(10, 0, 10, 0)
    bottom_layout.setSpacing(5)

    json_path_input = QLineEdit()
    json_path_input.setObjectName("jsonPathInput")
    json_path_input.setPlaceholderText("JSON Path: (e.g., $.store.book[*].author)")
    bottom_layout.addWidget(json_path_input)

    help_button = QPushButton()
    help_button.setObjectName("iconButton")
    # Image description: A simple, black question mark icon.
    help_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))
    bottom_layout.addWidget(help_button)

    main_layout.addWidget(bottom_bar)

    # Connect button functionality
    def format_json():
        """Format and validate JSON from input text."""
        input_text = input_text_edit.toPlainText()

        # Get indentation preference
        spaces_text = spaces_combo.currentText()
        if "2 spaces" in spaces_text:
            indent = 2
        elif "4 spaces" in spaces_text:
            indent = 4
        else:  # Tabs
            indent = 0

        is_valid, formatted_json, error_message = json_validator.validate_and_format_json(input_text, indent)

        if is_valid:
            output_text_edit.setPlainText(formatted_json)
            output_text_edit.setStyleSheet("QTextEdit { color: #212529; }")
        else:
            output_text_edit.setPlainText(f"Error: {error_message}")
            output_text_edit.setStyleSheet("QTextEdit { color: #dc3545; }")

    def load_sample():
        """Load sample JSON into input area."""
        sample_json = json_validator.get_sample_json()
        input_text_edit.setPlainText(sample_json)

    def clear_input():
        """Clear input text area."""
        input_text_edit.clear()
        output_text_edit.clear()
        output_text_edit.setStyleSheet("QTextEdit { color: #6c757d; }")

    def copy_output():
        """Copy output to clipboard."""
        output_text = output_text_edit.toPlainText()
        if output_text:
            app = QApplication.instance()
            if app:
                app.clipboard().setText(output_text)
                # Show brief confirmation
                QMessageBox.information(widget, "Copied", "Output copied to clipboard!")

    def load_from_clipboard():
        """Load JSON from clipboard."""
        app = QApplication.instance()
        if app:
            clipboard_text = app.clipboard().text()
            if clipboard_text:
                input_text_edit.setPlainText(clipboard_text)

    def execute_json_path():
        """Execute JSON Path query on input JSON."""
        input_text = input_text_edit.toPlainText()
        json_path = json_path_input.text()

        if not json_path.strip():
            # If no JSON Path, just format the JSON normally
            format_json()
            return

        is_valid, result_json, error_message = json_validator.query_json_path(input_text, json_path)

        if is_valid:
            output_text_edit.setPlainText(result_json)
            output_text_edit.setStyleSheet("QTextEdit { color: #212529; }")
            if error_message:  # "No matches found" case
                output_text_edit.setPlainText(f"Result: {result_json}\n\nNote: {error_message}")
        else:
            output_text_edit.setPlainText(f"Error: {error_message}")
            output_text_edit.setStyleSheet("QTextEdit { color: #dc3545; }")

    # Connect buttons to functions
    def on_run_button_clicked():
        """Handle run button click - check if JSON Path is present."""
        if json_path_input.text().strip():
            execute_json_path()
        else:
            format_json()

    run_button.clicked.connect(on_run_button_clicked)
    json_path_input.returnPressed.connect(execute_json_path)
    sample_button = None
    clipboard_button = None
    clear_button = None

    # Find buttons by iterating through toolbar
    for i in range(input_toolbar_layout.count()):
        item = input_toolbar_layout.itemAt(i)
        if item and item.widget():
            widget_item = item.widget()
            if isinstance(widget_item, QPushButton):
                if widget_item.text() == "Sample":
                    sample_button = widget_item
                elif widget_item.text() == "Clipboard":
                    clipboard_button = widget_item
                elif widget_item.text() == "Clear":
                    clear_button = widget_item

    if sample_button:
        sample_button.clicked.connect(load_sample)
    if clipboard_button:
        clipboard_button.clicked.connect(load_from_clipboard)
    if clear_button:
        clear_button.clicked.connect(clear_input)

    copy_button.clicked.connect(copy_output)

    return widget


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # In a real app, style_func would be a method of the main window,
    # but for a standalone test, we can just use the app's style.
    main_window = QMainWindow()
    main_window.setWindowTitle("JSON-YAML Converter")
    main_window.setGeometry(100, 100, 800, 600)

    central_widget = create_json_formatter_widget(app.style)
    main_window.setCentralWidget(central_widget)

    main_window.show()
    sys.exit(app.exec())
