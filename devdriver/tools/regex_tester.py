import logging
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
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


def create_regexp_tester_widget(style_func):
    """
    Creates and returns the RegExp Tester widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete RegExp Tester widget.
    """
    logger.info("Creating RegExp Tester widget")
    widget = QWidget()
    widget.setStyleSheet("""
        QWidget {
            background-color: #f0f2f5;
            color: #333333;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 13px;
        }
        QFrame#mainContainer {
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 6px;
        }
        QLabel {
            font-weight: 500;
        }
        QPushButton {
            background-color: #f9fafb;
            border: 1px solid #d1d5db;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #f3f4f6;
        }
        QPushButton#iconButton {
            background-color: transparent;
            border: none;
            padding: 4px;
        }
        QPushButton#cheatSheetButton {
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            padding: 5px 10px;
        }
        QLineEdit, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-radius: 4px;
            padding: 6px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            color: #111827;
        }
        QLineEdit#barInput {
             border: none;
             padding: 4px;
             background-color: #f3f4f6;
        }
        QLineEdit {
            padding-left: 10px;
        }
        QLineEdit[has-leading-action=true] {
            padding-left: 30px;
        }
        QTextEdit {
            padding: 8px;
        }
        QLineEdit::placeholder, QTextEdit::placeholder {
            color: #9ca3af;
        }
    """)

    # --- MAIN LAYOUT ---
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(12)

    # --- REGEXP SECTION ---
    regexp_section_frame = QFrame()
    regexp_section_frame.setObjectName("mainContainer")
    regexp_section_layout = QVBoxLayout(regexp_section_frame)
    regexp_section_layout.setContentsMargins(1, 1, 1, 1)  # Thin margins for inner layout
    regexp_top_bar_layout = QHBoxLayout()
    regexp_top_bar_layout.setContentsMargins(10, 10, 10, 10)
    regexp_top_bar_layout.setSpacing(8)

    regexp_label = QLabel("RegExp:")
    regexp_input = QLineEdit()
    regexp_input.setPlaceholderText("Enter a regular expression")
    regexp_input.setObjectName("barInput")

    clipboard_button_1 = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A flat, gray gear icon for settings.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))

    cheat_sheet_button = QPushButton("Cheat Sheet")
    # Image description: A document or book icon, for a cheat sheet.
    cheat_sheet_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))
    cheat_sheet_button.setObjectName("cheatSheetButton")

    regexp_top_bar_layout.addWidget(regexp_label)
    regexp_top_bar_layout.addSpacing(5)
    regexp_top_bar_layout.addWidget(regexp_input, 1)
    regexp_top_bar_layout.addWidget(clipboard_button_1)
    regexp_top_bar_layout.addWidget(sample_button)
    regexp_top_bar_layout.addWidget(clear_button)
    regexp_top_bar_layout.addWidget(settings_button)
    regexp_top_bar_layout.addStretch()
    regexp_top_bar_layout.addWidget(cheat_sheet_button)
    regexp_section_layout.addLayout(regexp_top_bar_layout)
    regexp_section_layout.setStretchFactor(regexp_top_bar_layout, 0)

    # --- TEXT INPUT SECTION ---
    text_section_frame = QFrame()
    text_section_frame.setObjectName("mainContainer")
    text_section_layout = QVBoxLayout(text_section_frame)
    text_section_layout.setContentsMargins(10, 10, 10, 10)
    text_section_layout.setSpacing(8)

    text_top_bar_layout = QHBoxLayout()
    text_top_bar_layout.setSpacing(8)
    text_label = QLabel("Text:")
    clipboard_button_2 = QPushButton("Clipboard")
    matches_label = QLabel("0 matches")
    matches_label.setAlignment(Qt.AlignmentFlag.AlignRight)

    text_top_bar_layout.addWidget(text_label)
    text_top_bar_layout.addWidget(clipboard_button_2)
    text_top_bar_layout.addStretch()
    text_top_bar_layout.addWidget(matches_label)
    text_section_layout.addLayout(text_top_bar_layout)

    text_input_edit = QTextEdit()
    placeholder_text_input = (
        "- Enter Your Text\n"
        "- Drag/Drop Files\n"
        "- Right Click → Load from File...\n"
        "- ⌘ + F to Search\n"
        "- ⌘ + ⇧ + F to Replace"
    )
    text_input_edit.setPlaceholderText(placeholder_text_input)
    text_section_layout.addWidget(text_input_edit)

    # --- BOTTOM SECTION (OUTPUT & MATCHES) ---
    bottom_layout = QHBoxLayout()
    bottom_layout.setSpacing(12)

    # --- OUTPUT (Left Side) ---
    output_section_frame = QFrame()
    output_section_frame.setObjectName("mainContainer")
    output_section_layout = QVBoxLayout(output_section_frame)
    output_section_layout.setContentsMargins(10, 10, 10, 10)
    output_section_layout.setSpacing(8)

    output_top_bar_layout = QHBoxLayout()
    output_top_bar_layout.setSpacing(8)
    output_label = QLabel("Output:")
    output_input = QLineEdit("$&\\n")
    output_input.setObjectName("barInput")
    help_button = QPushButton()
    help_button.setObjectName("iconButton")
    # Image description: A question mark icon inside a circle.
    help_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))
    output_top_bar_layout.addWidget(output_label)
    output_top_bar_layout.addSpacing(5)
    output_top_bar_layout.addWidget(output_input, 1)
    output_top_bar_layout.addWidget(help_button)
    output_top_bar_layout.addStretch()

    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    output_text_edit.setPlaceholderText("- Right Click > Save to file...")
    output_section_layout.addLayout(output_top_bar_layout)
    output_section_layout.addWidget(output_text_edit, 1)
    bottom_layout.addWidget(output_section_frame, 1)

    # --- MATCHES (Right Side) ---
    matches_section_frame = QFrame()
    matches_section_frame.setObjectName("mainContainer")
    matches_section_layout = QVBoxLayout(matches_section_frame)
    matches_section_layout.setContentsMargins(10, 10, 10, 10)
    matches_section_layout.setSpacing(8)

    matches_top_bar_layout = QHBoxLayout()
    matches_top_bar_layout.setSpacing(8)
    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon))
    search_matches_input = QLineEdit()
    search_matches_input.setPlaceholderText("Search matches...")
    # Image description: Placeholder for a magnifying glass search icon.
    search_icon = style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)
    search_action = QAction(search_icon, "Search", search_matches_input)
    search_matches_input.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)
    search_matches_input.setProperty("has-leading-action", True)  # For styling

    matches_top_bar_layout.addStretch()
    matches_top_bar_layout.addWidget(copy_button)
    matches_top_bar_layout.addWidget(search_matches_input, 1)

    matches_text_edit = QTextEdit()
    matches_text_edit.setReadOnly(True)
    matches_section_layout.addLayout(matches_top_bar_layout)
    matches_section_layout.addWidget(matches_text_edit, 1)
    bottom_layout.addWidget(matches_section_frame, 1)

    # --- Add all sections to the main layout ---
    main_layout.addWidget(regexp_section_frame)
    main_layout.addWidget(text_section_frame, 4)
    main_layout.addLayout(bottom_layout, 3)

    logger.info("RegExp Tester widget creation completed")
    return widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("RegExp Tester")
    main_window.setGeometry(100, 100, 1100, 750)

    regexp_tool_widget = create_regexp_tester_widget(app.style)
    main_window.setCentralWidget(regexp_tool_widget)

    main_window.show()
    sys.exit(app.exec())
