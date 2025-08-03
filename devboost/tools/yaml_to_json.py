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


def create_yaml_to_json_widget(style_func):
    """
    Creates and returns the YAML to JSON converter widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete YAML to JSON converter widget.
    """
    widget = QWidget()
    widget.setStyleSheet("""
        QWidget {
            background-color: #f7f7f9;
            color: #333333;
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QWidget#pane {
            background-color: transparent;
        }
        QLabel {
            font-size: 14px;
            font-weight: 500;
            color: #212529;
        }
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            padding: 8px;
            color: #212529;
        }
        QTextEdit::placeholder {
            color: #a9a9a9;
        }
        QPushButton, QComboBox {
            background-color: #ffffff;
            border: 1px solid #dcdcdc;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 13px;
            color: #212529;
        }
        QPushButton:hover, QComboBox:hover {
            background-color: #f0f0f0;
        }
        QPushButton#iconButton {
            background-color: transparent;
            border: none;
            padding: 4px;
        }
        QPushButton#iconButton:hover {
            background-color: #e9ecef;
            border-radius: 4px;
        }
        QComboBox {
            padding-top: 4px;
            padding-bottom: 4px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QFrame#separator {
            background-color: #e0e0e0;
            max-width: 1px;
        }
    """)

    # Main horizontal layout
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # --- Left Pane (Input) ---
    input_pane = QWidget()
    input_pane.setObjectName("pane")
    input_layout = QVBoxLayout(input_pane)
    input_layout.setContentsMargins(10, 10, 5, 10)
    input_layout.setSpacing(8)

    input_layout.addWidget(QLabel("Input:"))

    input_buttons_layout = QHBoxLayout()
    input_buttons_layout.setSpacing(8)
    input_buttons_layout.setContentsMargins(0, 0, 0, 0)

    input_icon_button = QPushButton()
    input_icon_button.setObjectName("iconButton")
    # Image description: A simple yellow lightning bolt icon.
    input_icon_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))

    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    input_buttons_layout.addWidget(input_icon_button)
    input_buttons_layout.addWidget(clipboard_button)
    input_buttons_layout.addWidget(sample_button)
    input_buttons_layout.addWidget(clear_button)
    input_buttons_layout.addStretch()

    input_layout.addLayout(input_buttons_layout)

    input_text_edit = QTextEdit()
    placeholder_text_input = (
        "- Enter Your Text\n"
        "- Drag/Drop Files\n"
        "- Right Click → Load from File...\n"
        "- ⌘ + F to Search\n"
        "- ⌘ + ⇧ + F to Replace"
    )
    input_text_edit.setPlaceholderText(placeholder_text_input)
    input_layout.addWidget(input_text_edit, 1)

    # --- Separator ---
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setObjectName("separator")

    # --- Right Pane (Output) ---
    output_pane = QWidget()
    output_pane.setObjectName("pane")
    output_layout = QVBoxLayout(output_pane)
    output_layout.setContentsMargins(5, 10, 10, 10)
    output_layout.setSpacing(8)

    output_header_layout = QHBoxLayout()
    output_header_layout.setSpacing(8)
    output_header_layout.setContentsMargins(0, 0, 0, 0)
    output_label = QLabel("Output:")

    spaces_combo = QComboBox()
    spaces_combo.addItem("2 spaces")
    spaces_combo.addItem("4 spaces")
    spaces_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))

    output_header_layout.addWidget(output_label)
    output_header_layout.addStretch()
    output_header_layout.addWidget(spaces_combo)
    output_header_layout.addWidget(copy_button)
    output_layout.addLayout(output_header_layout)

    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    placeholder_text_output = (
        "Tips:\n"
        "- Right Click → Save to File...\n"
        "- Right Click → Show Line Numbers\n"
        "- Right Click → Line Wrapping"
    )
    output_text_edit.setPlaceholderText(placeholder_text_output)
    output_layout.addWidget(output_text_edit, 1)

    # --- Assemble Main Layout ---
    main_layout.addWidget(input_pane, 1)
    main_layout.addWidget(separator)
    main_layout.addWidget(output_pane, 1)

    return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("YAML to JSON Converter")
    main_window.setGeometry(100, 100, 900, 600)

    # The create function needs a style function/object
    tool_widget = create_yaml_to_json_widget(app.style)

    main_window.setCentralWidget(tool_widget)
    main_window.show()
    sys.exit(app.exec())
