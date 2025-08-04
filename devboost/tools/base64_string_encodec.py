import base64
import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QPushButton,
    QRadioButton,
    QSplitter,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_tool_style

logger = logging.getLogger(__name__)


# ruff: noqa: C901
def create_base64_string_encodec_widget(style_func):
    """
    Creates and returns the Base64 String Encode/Decode widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete Base64 encoder/decoder widget.
    """
    logger.info("Creating Base64 String Encode/Decode widget")
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(0)

    main_splitter = QSplitter(Qt.Orientation.Vertical)
    main_layout.addWidget(main_splitter)

    # --- TOP INPUT SECTION ---
    input_section_widget = QWidget()
    input_section_layout = QVBoxLayout(input_section_widget)
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
    input_text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    input_section_layout.addWidget(input_text_edit, 1)

    # --- BOTTOM OUTPUT SECTION ---
    output_section_widget = QWidget()
    output_section_layout = QVBoxLayout(output_section_widget)
    output_section_layout.setSpacing(8)
    output_section_layout.setContentsMargins(0, 12, 0, 0)

    # Output Controls Bar
    output_bar_layout = QHBoxLayout()

    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages.

    use_as_input_button = QPushButton("Use as input")
    # Image description: An upward-pointing arrow icon.
    use_as_input_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))  # Placeholder

    output_bar_layout.addStretch()
    output_bar_layout.addWidget(copy_button)
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

    # Connect functionality
    def perform_encoding_decoding():
        """Perform base64 encoding or decoding based on selected mode."""
        input_text = input_text_edit.toPlainText()
        if not input_text.strip():
            output_text_edit.clear()
            return

        try:
            if encode_radio.isChecked():
                # Encode to base64
                encoded_bytes = base64.b64encode(input_text.encode("utf-8"))
                result = encoded_bytes.decode("ascii")
            else:
                # Decode from base64
                decoded_bytes = base64.b64decode(input_text.encode("ascii"))
                result = decoded_bytes.decode("utf-8")

            output_text_edit.setPlainText(result)
        except Exception as e:
            output_text_edit.setPlainText(f"Error: {e!s}")
            logger.exception("Base64 operation failed")

    def copy_to_clipboard():
        """Copy output text to clipboard."""
        output_text = output_text_edit.toPlainText()
        if output_text:
            QApplication.clipboard().setText(output_text)
            logger.info("Output copied to clipboard")

    def use_output_as_input():
        """Move output text to input field."""
        output_text = output_text_edit.toPlainText()
        if output_text:
            input_text_edit.setPlainText(output_text)
            logger.info("Output moved to input")

    def clear_input():
        """Clear the input text field."""
        input_text_edit.clear()
        output_text_edit.clear()

    def load_sample():
        """Load sample text for testing."""
        sample_text = "Hello, World! This is a sample text for Base64 encoding/decoding."
        input_text_edit.setPlainText(sample_text)

    def paste_from_clipboard():
        """Paste text from clipboard to input."""
        clipboard_text = QApplication.clipboard().text()
        if clipboard_text:
            input_text_edit.setPlainText(clipboard_text)
            logger.info("Text pasted from clipboard")

    def load_from_file():
        """Load text from a file."""
        file_path, _ = QFileDialog.getOpenFileName(widget, "Load from File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, encoding="utf-8") as file:
                    content = file.read()
                    input_text_edit.setPlainText(content)
                    logger.info(f"File loaded: {file_path}")
            except Exception as e:
                logger.exception(f"Failed to load file {file_path}")
                input_text_edit.setPlainText(f"Error loading file: {e!s}")

    def show_input_context_menu(position):
        """Show context menu for input text area."""
        context_menu = QMenu(input_text_edit)

        # Add standard actions
        undo_action = context_menu.addAction("Undo")
        undo_action.triggered.connect(input_text_edit.undo)
        undo_action.setEnabled(input_text_edit.document().isUndoAvailable())

        redo_action = context_menu.addAction("Redo")
        redo_action.triggered.connect(input_text_edit.redo)
        redo_action.setEnabled(input_text_edit.document().isRedoAvailable())

        context_menu.addSeparator()

        cut_action = context_menu.addAction("Cut")
        cut_action.triggered.connect(input_text_edit.cut)
        cut_action.setEnabled(input_text_edit.textCursor().hasSelection())

        copy_action = context_menu.addAction("Copy")
        copy_action.triggered.connect(input_text_edit.copy)
        copy_action.setEnabled(input_text_edit.textCursor().hasSelection())

        paste_action = context_menu.addAction("Paste")
        paste_action.triggered.connect(input_text_edit.paste)

        context_menu.addSeparator()

        select_all_action = context_menu.addAction("Select All")
        select_all_action.triggered.connect(input_text_edit.selectAll)

        context_menu.addSeparator()

        # Add custom action
        load_file_action = context_menu.addAction("Load from File...")
        load_file_action.triggered.connect(load_from_file)

        context_menu.exec(input_text_edit.mapToGlobal(position))

    # Connect signals
    input_text_edit.textChanged.connect(perform_encoding_decoding)
    input_text_edit.customContextMenuRequested.connect(show_input_context_menu)
    encode_radio.toggled.connect(perform_encoding_decoding)
    decode_radio.toggled.connect(perform_encoding_decoding)
    copy_button.clicked.connect(copy_to_clipboard)
    use_as_input_button.clicked.connect(use_output_as_input)
    clear_button.clicked.connect(clear_input)
    sample_button.clicked.connect(load_sample)
    clipboard_button.clicked.connect(paste_from_clipboard)

    logger.info("Base64 widget creation completed")
    return widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    # Create a main window to host the widget
    main_window = QMainWindow()
    main_window.setWindowTitle("Base64 Encoder/Decoder Test")
    main_window.setGeometry(100, 100, 800, 600)

    # The widget needs a function to get the application style
    base64_tool_widget = create_base64_string_encodec_widget(app.style)

    # Set the created widget as the central widget of the main window. [1, 2, 3]
    main_window.setCentralWidget(base64_tool_widget)

    main_window.show()
    sys.exit(app.exec())
