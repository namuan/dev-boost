import logging
import os

import appdirs
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_tool_style

# It's good practice to have a logger
logger = logging.getLogger(__name__)


class ScratchPadWidget(QWidget):
    """
    A simple scratch pad widget for taking notes and drafts.
    """

    def __init__(self):
        super().__init__()
        self.app_name = "DevBoost"
        self.app_author = "DeskRiders"
        self.data_dir = appdirs.user_data_dir(self.app_name, self.app_author)
        self.scratch_pad_file = os.path.join(self.data_dir, "scratch_pad.txt")
        self.init_ui()
        self.load_content()

    def init_ui(self):
        """
        Initialize the user interface for the scratch pad.
        """
        self.setStyleSheet(get_tool_style())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Create a text edit for the scratch pad
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Start typing your notes here...")
        # Set to plain text mode by default
        self.text_edit.setAcceptRichText(False)

        # Create a button to clear the scratch pad
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_scratch_pad)

        # Create a button to copy the scratch pad content
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self.copy_scratch_pad)

        # Layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(clear_button)
        button_layout.addWidget(copy_button)
        button_layout.addStretch()

        # Add widgets to the main layout
        layout.addWidget(self.text_edit)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect text change signal to save content
        self.text_edit.textChanged.connect(self.save_content)

    def clear_scratch_pad(self):
        """
        Clear the content of the scratch pad.
        """
        self.text_edit.clear()

    def copy_scratch_pad(self):
        """
        Copy the content of the scratch pad to the clipboard.
        """
        content = self.text_edit.toPlainText()
        if content:
            self.text_edit.textCursor().document().setPlainText(content)
            self.text_edit.copy()
            # TODO: Add some kind of hint that the content is copied (maybe via Status Bar?)

    def get_content(self):
        """
        Get the content of the scratch pad.

        Returns:
            str: The content of the scratch pad.
        """
        return self.text_edit.toPlainText()

    def set_content(self, content):
        """
        Set the content of the scratch pad.

        Args:
            content (str): The content to set.
        """
        self.text_edit.setPlainText(content)

    def save_content(self):
        """
        Save the content of the scratch pad to a file.
        """
        try:
            # Ensure the data directory exists
            os.makedirs(self.data_dir, exist_ok=True)

            # Save content to file
            with open(self.scratch_pad_file, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
        except Exception:
            logger.exception("Failed to save scratch pad content")

    def load_content(self):
        """
        Load the content of the scratch pad from a file.
        """
        try:
            # Check if the file exists
            if os.path.exists(self.scratch_pad_file):
                with open(self.scratch_pad_file, encoding="utf-8") as f:
                    content = f.read()
                    self.text_edit.setPlainText(content)
        except Exception:
            logger.exception("Failed to load scratch pad content")


def create_scratch_pad_widget(style_func):
    """
    Creates the main widget for the scratch pad tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.

    Returns:
        QWidget: The main widget for the tool.
    """
    widget = ScratchPadWidget()
    return widget


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("Scratch Pad")
    main_window.setGeometry(100, 100, 400, 300)

    central_widget = create_scratch_pad_widget(app.style)
    main_window.setCentralWidget(central_widget)

    main_window.show()
    sys.exit(app.exec())
