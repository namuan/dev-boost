import logging

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# It's good practice to have a logger
logger = logging.getLogger(__name__)


def create_json_formatter_widget(style_func):
    """
    Creates the main widget for the JSON formatter tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.

    Returns:
        QWidget: The main widget for the tool.
    """
    widget = QWidget()
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
