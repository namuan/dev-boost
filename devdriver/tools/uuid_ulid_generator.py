import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


def create_field_row(name: str, style_func) -> QWidget:
    """Helper function to create a labeled field row for the decoder."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)

    label = QLabel(name)
    layout.addWidget(label)

    field_layout = QHBoxLayout()
    field_layout.setSpacing(5)

    line_edit = QLineEdit()
    line_edit.setReadOnly(True)
    field_layout.addWidget(line_edit)

    copy_button = QPushButton()
    copy_button.setObjectName("iconButton")
    # Image description: A simple black icon representing two overlapping pages, for copying.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon))
    copy_button.setFixedSize(30, 30)
    field_layout.addWidget(copy_button)

    layout.addLayout(field_layout)
    return widget


def create_uuid_ulid_tool_widget(style_func) -> QWidget:
    """
    Creates the UUID/ULID Generate/Decode widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete UUID/ULID tool widget.
    """
    logger.info("Creating UUID/ULID Generate/Decode widget")
    main_widget = QWidget()
    main_widget.setStyleSheet("""
        QWidget {
            background-color: #ffffff;
            color: #333333;
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QLabel {
            font-size: 13px;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            padding: 5px 12px;
            border-radius: 3px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #e8e8e8;
        }
        QPushButton#iconButton {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 2px;
        }
        QPushButton#iconButton:hover {
            background-color: #f0f0f0;
        }
        QLineEdit, QComboBox, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 13px;
        }
        QComboBox {
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QTextEdit {
            color: #888888;
        }
        QCheckBox {
            font-size: 13px;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
        }
    """)

    main_layout = QHBoxLayout(main_widget)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(12)

    # --- LEFT PANE (DECODER) ---
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(8)

    # Top controls
    input_controls_layout = QHBoxLayout()
    input_controls_layout.setSpacing(6)

    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button_left = QPushButton("Clear")
    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A flat, gray gear icon for settings.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
    settings_button.setFixedSize(32, 32)

    input_controls_layout.addWidget(QPushButton("Input:"))  # This is styled as a button in the screenshot
    input_controls_layout.addWidget(clipboard_button)
    input_controls_layout.addWidget(sample_button)
    input_controls_layout.addWidget(clear_button_left)
    input_controls_layout.addSpacing(4)
    input_controls_layout.addWidget(settings_button)
    input_controls_layout.addStretch()

    # UUID Input field
    uuid_input = QLineEdit("00000000-0000-0000-0000-000000000000")

    left_layout.addLayout(input_controls_layout)
    left_layout.addWidget(uuid_input)
    left_layout.addSpacing(10)

    # Decoded Fields
    field_names = [
        "Standard String Format",
        "Raw Contents",
        "Version",
        "Variant",
        "Contents - Time",
        "Contents - Clock ID",
        "Contents - Node",
    ]
    for name in field_names:
        left_layout.addWidget(create_field_row(name, style_func))

    left_layout.addStretch()

    # --- RIGHT PANE (GENERATOR) ---
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(8)

    # Generator controls
    controls_layout = QHBoxLayout()
    controls_layout.setSpacing(6)

    generate_button = QPushButton("Generate")
    copy_button = QPushButton("Copy")
    clear_button_right = QPushButton("Clear")

    uuid_version_combo = QComboBox()
    uuid_version_combo.addItems(["UUID v1", "UUID v4", "ULID"])
    uuid_version_combo.setFixedWidth(100)

    count_label = QLabel("x")
    count_input = QLineEdit("100")
    count_input.setFixedWidth(50)
    count_input.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    lowercased_checkbox = QCheckBox("lowercased")

    controls_layout.addWidget(generate_button)
    controls_layout.addWidget(copy_button)
    controls_layout.addWidget(clear_button_right)
    controls_layout.addStretch()
    controls_layout.addWidget(uuid_version_combo)
    controls_layout.addWidget(count_label)
    controls_layout.addWidget(count_input)
    controls_layout.addWidget(lowercased_checkbox)

    generate_label = QLabel("Generate new IDs")

    output_text_edit = QTextEdit()
    output_text_edit.setPlaceholderText("- Right click > Save to file...")
    output_text_edit.setReadOnly(True)

    right_layout.addWidget(generate_label)
    right_layout.addLayout(controls_layout)
    right_layout.addWidget(output_text_edit)

    # Add panes to main layout
    main_layout.addWidget(left_pane, 5)  # Give more space to the left pane
    main_layout.addWidget(right_pane, 4)

    logger.info("UUID/ULID widget creation completed")
    return main_widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("UUID/ULID Generate/Decode Tool")
    main_window.setGeometry(100, 100, 1000, 600)

    uuid_tool_widget = create_uuid_ulid_tool_widget(app.style)
    main_window.setCentralWidget(uuid_tool_widget)

    main_window.show()
    sys.exit(app.exec())
