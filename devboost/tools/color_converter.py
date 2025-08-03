import logging
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def create_color_converter_widget():
    """
    Creates the Color Converter widget.

    Returns:
        QWidget: The complete Color Converter widget.
    """
    widget = QWidget()
    widget.setObjectName("mainWidget")

    # Main horizontal layout
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # --- LEFT PANEL (INPUTS) ---
    left_panel = QWidget()
    left_panel.setObjectName("leftPanel")
    left_panel_layout = QVBoxLayout(left_panel)
    left_panel_layout.setContentsMargins(20, 20, 20, 20)
    left_panel_layout.setSpacing(15)
    left_panel.setFixedWidth(450)

    # Top input section
    input_section_layout = QVBoxLayout()
    input_section_layout.setSpacing(8)

    # Input header with buttons
    input_header_layout = QHBoxLayout()
    input_label = QLabel("Input:")
    input_header_layout.addWidget(input_label)
    input_header_layout.addStretch()
    input_header_layout.addWidget(QPushButton("Clipboard"))
    input_header_layout.addWidget(QPushButton("Sample"))
    input_header_layout.addWidget(QPushButton("Clear"))
    input_section_layout.addLayout(input_header_layout)

    # Input field and color preview
    input_field_layout = QHBoxLayout()
    input_field = QLineEdit()
    input_field.setPlaceholderText("(Enter any of the supported formats below)")
    input_field_layout.addWidget(input_field)

    color_preview = QLabel()
    color_preview.setObjectName("colorPreview")
    color_preview.setFixedSize(34, 34)
    input_field_layout.addWidget(color_preview)

    input_section_layout.addLayout(input_field_layout)
    left_panel_layout.addLayout(input_section_layout)

    # Grid for color formats
    formats_layout = QGridLayout()
    formats_layout.setHorizontalSpacing(10)
    formats_layout.setVerticalSpacing(12)

    # Data for the format rows
    formats_data = {
        "Hex": "#5CCC7F",
        "Hex with alpha": "#5CCC7FFF",
        "RGB": "rgb(92, 204, 127)",
        "RGBA": "rgba(92, 204, 127, 1)",
        "HSL": "hsl(139, 52%, 58%)",
        "HSLA": "hsla(139, 52%, 58%, 100%)",
        "HSB (HSV)": "hsb(139, 55%, 80%)",
        "HWB": "hwb(139, 36%, 20%)",
        "CMYK": "cmyk(55%, 0%, 38%, 20%)",
    }

    # Create and add format rows to the grid
    row = 0
    for label_text, value_text in formats_data.items():
        label = QLabel(f"{label_text}:")
        line_edit = QLineEdit(value_text)
        copy_button = QPushButton("Copy")
        copy_button.setFixedWidth(60)

        formats_layout.addWidget(label, row, 0)
        formats_layout.addWidget(line_edit, row, 1)
        formats_layout.addWidget(copy_button, row, 2)
        row += 1

    formats_layout.setColumnStretch(1, 1)  # Allow the QLineEdit column to stretch
    left_panel_layout.addLayout(formats_layout)
    left_panel_layout.addStretch()

    # --- RIGHT PANEL (CODE PRESETS) ---
    right_panel = QWidget()
    right_panel.setObjectName("rightPanel")
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)

    tabs = QTabWidget()
    tabs.setObjectName("presetsTab")

    # Code Presets Tab
    code_presets_tab = QWidget()
    code_presets_layout = QVBoxLayout(code_presets_tab)
    code_presets_layout.setContentsMargins(15, 15, 15, 15)

    code_presets_edit = QTextEdit()
    code_presets_edit.setObjectName("codePresetsEdit")
    code_presets_edit.setReadOnly(True)

    code_content = """# CSS Level 4 Color Module:

rgb({red-b} {green-b} {blue-b})
rgb({red-b} {green-b} {blue-b} / {alpha-p}%)
hsl({hue-d}deg {hsl-saturation-p}% {lightness-p}%)
hsl({hue-d}deg {hsl-saturation-p}% {lightness-p}% / {alpha-p}%)

# Swift:

NSColor(
    calibratedRed: {red},
    green: {green},
    blue: {blue},
    alpha: {alpha}
)

NSColor(
    calibratedHue: {hue},
    saturation: {hsb-saturation},
    brightness: {brightness},
    alpha: {alpha}
)

# .NET

Color.FromArgb({red-b}, {green-b}, {blue-b})
Color.FromRgb({red-b}, {green-b}, {blue-b}, {alpha-b})

# Java

new Color({red-b}, {green-b}, {blue-b})
new Color({red-b}, {green-b}, {blue-b}, {alpha-b})

# Android

Color.rgb({red-b}, {green-b}, {blue-b})
Color.argb({red-b}, {green-b}, {blue-b}, {alpha-b})

<color name="color_name">{hex}</color>
<color name="color_name">{hex-alpha}</color>

# OpenGL

glColor3f({red}, {green}, {blue})
glColor4f({red}, {green}, {blue}, {alpha})

# ObjC

[UIColor colorWithRed:{red} green:{green} blue:{blue} alpha:{alpha}]
[UIColor colorWithHue:{hue} saturation:{hsb-saturation} brightness:{brightness} alpha:{alpha}]"""

    code_presets_edit.setText(code_content)
    code_presets_layout.addWidget(code_presets_edit)

    tabs.addTab(code_presets_tab, "Code Presets")
    tabs.addTab(QWidget(), "View Source")
    tabs.addTab(QWidget(), "Variables")

    right_layout.addWidget(tabs)

    # Add panels to main layout
    main_layout.addWidget(left_panel)
    main_layout.addWidget(right_panel, 1)  # Make right panel stretch

    # Apply Stylesheet
    widget.setStyleSheet("""
        QWidget#mainWidget {
            background-color: #F8F9FA;
        }
        QWidget#leftPanel {
            background-color: #ffffff;
            border-right: 1px solid #E0E0E0;
        }
        QLabel {
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 13px;
            color: #212529;
        }
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 5px 8px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 13px;
            color: #495057;
        }
        QLineEdit:focus {
            border-color: #80bdff;
        }
        QPushButton {
            background-color: #f8f9fa;
            border: 1px solid #ced4da;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 13px;
            color: #212529;
        }
        QPushButton:hover {
            background-color: #e9ecef;
        }
        QPushButton:pressed {
            background-color: #dae0e5;
        }
        QLabel#colorPreview {
            background-color: #5CCC7F;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        QTabWidget#presetsTab::pane {
            border: none;
        }
        QTabBar::tab {
            background: #e9ecef;
            color: #495057;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QTabBar::tab:selected {
            background: #F8F9FA;
            color: #000000;
        }
        QTabBar::tab:!selected:hover {
            background: #dde2e7;
        }
        QTextEdit#codePresetsEdit {
            background-color: #F8F9FA;
            border: none;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            color: #343a40;
            line-height: 1.5;
        }
    """)

    return widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    # Create a main window to host the widget
    main_window = QMainWindow()
    main_window.setWindowTitle("Color Converter Tool")
    main_window.setGeometry(100, 100, 950, 650)

    # Create the color converter widget
    color_converter_widget = create_color_converter_widget()

    # Set the created widget as the central widget of the main window.
    main_window.setCentralWidget(color_converter_widget)

    main_window.show()
    sys.exit(app.exec())
