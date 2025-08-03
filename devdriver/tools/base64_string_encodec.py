import logging
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


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
    widget.setStyleSheet("""
        QWidget {
            background-color: #ffffff;
            color: #333333;
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #dcdcdc;
            padding: 5px 12px;
            border-radius: 3px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton#iconButton {
            background-color: transparent;
            border: none;
            padding: 2px;
        }
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #dcdcdc;
            border-radius: 2px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            padding: 8px;
        }
        QFrame[frameShape="HLine"] {
            border: none;
            border-top: 1px solid #e5e5e5;
        }
        QRadioButton {
            font-size: 13px;
            spacing: 5px;
        }
        QRadioButton::indicator {
            width: 14px;
            height: 14px;
        }
        QTextEdit::placeholder {
            color: #a9a9a9;
        }
    """)

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

    input_icon_button = QPushButton()
    input_icon_button.setObjectName("iconButton")
    # Image description: A simple yellow lightning bolt icon.
    input_icon_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))  # Placeholder
    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A flat, gray gear icon for settings.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))

    top_bar_layout.addWidget(input_icon_button)
    top_bar_layout.addWidget(clipboard_button)
    top_bar_layout.addWidget(sample_button)
    top_bar_layout.addWidget(clear_button)
    top_bar_layout.addSpacing(4)
    top_bar_layout.addWidget(settings_button)
    top_bar_layout.addStretch()

    encode_radio = QRadioButton("Encode")
    decode_radio = QRadioButton("Decode")
    decode_radio.setChecked(True)

    radio_group = QButtonGroup(widget)
    radio_group.addButton(encode_radio)
    radio_group.addButton(decode_radio)

    top_bar_layout.addWidget(encode_radio)
    top_bar_layout.addWidget(decode_radio)

    input_label = QLabel("Input:")
    input_section_layout.addWidget(input_label)
    input_section_layout.addLayout(top_bar_layout)

    # Input Text Edit
    input_text_edit = QTextEdit()
    input_text_edit.setMinimumHeight(180)
    placeholder_text_input = (
        "– Enter Your Text\n"
        "– Drag/Drop Files\n"
        "– Right Click → Load from File...\n"
        "– ⌘ + F to Search\n"
        "– ⌘ + ⇧ + F to Replace"
    )
    # Using a QLabel for placeholder as QTextEdit placeholder is limited
    input_text_edit.setPlaceholderText(placeholder_text_input)
    input_section_layout.addWidget(input_text_edit, 1)

    # --- BOTTOM OUTPUT SECTION ---
    output_section_layout = QVBoxLayout()
    output_section_layout.setSpacing(8)
    output_section_layout.setContentsMargins(0, 12, 0, 0)

    # Output Controls Bar
    output_bar_layout = QHBoxLayout()

    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon))  # Placeholder

    use_as_input_button = QPushButton("Use as input")
    # Image description: An upward-pointing arrow icon.
    use_as_input_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))  # Placeholder

    output_bar_layout.addStretch()
    output_bar_layout.addWidget(copy_button)
    output_bar_layout.addWidget(use_as_input_button)

    output_label = QLabel("Output:")
    output_section_layout.addWidget(output_label)
    output_section_layout.addLayout(output_bar_layout)

    # Output Text Edit
    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    output_text_edit.setMinimumHeight(180)
    placeholder_text_output = "– Right click > Save to file..."
    output_text_edit.setPlaceholderText(placeholder_text_output)
    output_section_layout.addWidget(output_text_edit, 1)

    main_layout.addLayout(input_section_layout, 1)

    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    main_layout.addWidget(separator)

    main_layout.addLayout(output_section_layout, 1)

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
