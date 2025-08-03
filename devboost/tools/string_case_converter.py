import logging
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# It's good practice to have a logger
logger = logging.getLogger(__name__)


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
            border-radius: 4px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #e6e6e6;
        }
        QPushButton#iconButton {
            background-color: transparent;
            border: none;
            padding: 4px;
        }
        QTextEdit {
            background-color: #ffffff;
            border: none;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            padding: 8px;
            color: #212121;
        }
        QTextEdit::placeholder {
            color: #a9a9a9;
        }
        QLabel#outputLabel {
            font-size: 13px;
            font-weight: 500;
            padding: 8px 8px 0 8px;
        }
        QFrame#separator {
            background-color: #e0e0e0;
        }
        QComboBox {
            background-color: #f0f0f0;
            border: 1px solid #dcdcdc;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 13px;
            min-width: 80px;
        }
        QComboBox::drop-down {
            border: none;
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
        }
        QComboBox::down-arrow {
            image: url(down_arrow.png); /* Placeholder for a custom arrow if needed */
        }
        QWidget#topBar {
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
        }
    """)

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
    lightning_button = QPushButton()
    lightning_button.setObjectName("iconButton")
    # Image description: A simple yellow lightning bolt icon.
    lightning_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A flat, gray gear icon for settings.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))

    top_bar_layout.addWidget(lightning_button)
    top_bar_layout.addWidget(clipboard_button)
    top_bar_layout.addWidget(sample_button)
    top_bar_layout.addWidget(clear_button)
    top_bar_layout.addSpacing(4)
    top_bar_layout.addWidget(settings_button)
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
    content_layout = QHBoxLayout()
    content_layout.setSpacing(0)
    content_layout.setContentsMargins(0, 0, 0, 0)

    # Input Pane (Left)
    input_text_edit = QTextEdit()
    input_placeholder = (
        "- Enter Your Text\n"
        "- Drag/Drop Files\n"
        "- Right Click \u2192 Load from File...\n"
        "- \u2318 + F to Search\n"
        "- \u2318 + \u21e7 + F to Replace"
    )
    input_text_edit.setPlaceholderText(input_placeholder)
    content_layout.addWidget(input_text_edit, 1)

    # Separator
    separator = QFrame()
    separator.setObjectName("separator")
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    content_layout.addWidget(separator)

    # Output Pane (Right)
    output_pane_widget = QWidget()
    output_layout = QVBoxLayout(output_pane_widget)
    output_layout.setContentsMargins(0, 0, 0, 0)
    output_layout.setSpacing(0)

    output_label = QLabel("Output:")
    output_label.setObjectName("outputLabel")
    output_layout.addWidget(output_label)

    output_text_edit = QTextEdit()
    output_placeholder = (
        "Tips:\n"
        "\u2014 Right Click \u2192 Save to File...\n"
        "\u2014 Right Click \u2192 Show Line Numbers\n"
        "\u2014 Right Click \u2192 Line Wrapping"
    )
    output_text_edit.setPlaceholderText(output_placeholder)
    output_text_edit.setReadOnly(True)
    output_layout.addWidget(output_text_edit)

    content_layout.addWidget(output_pane_widget, 1)

    main_layout.addLayout(content_layout, 1)

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
