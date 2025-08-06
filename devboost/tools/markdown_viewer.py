import logging
import os
import sys
import tempfile
import webbrowser

import markdown
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_tool_style

# Attempt to import QWebEngineView and handle potential ImportError
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    logging.info("PyQtWebEngine not found. Using lightweight QTextEdit for markdown preview.")

# It's good practice to have a logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MARKDOWN_SAMPLE_TEXT = """
# Markdown Preview

This is a sample text to demonstrate the capabilities of this Markdown preview tool.

## Features

- **Real-time preview:** See your rendered HTML as you type.
- **GitHub Flavored Markdown:** Includes support for tables, code blocks, etc.
- **Syntax Highlighting:** For code snippets.

### Example Code Block

```python
def hello_world():
    # Prints "Hello, World!" to the console
    print("Hello, World!")

hello_world()```

### Example List

1.  First item
2.  Second item
    - Nested item
3.  Third item

> This is a blockquote. It's great for quoting text from other sources.

---

[Visit the project on GitHub](https://github.com)
"""


# ruff: noqa: C901
def create_markdown_preview_widget():
    """
    Creates and returns the Markdown Preview widget.

    Returns:
        QWidget: The complete markdown preview widget.
    """
    logger.info("Creating Markdown Preview widget")
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    # Continue with the widget creation regardless of WebEngine availability
    # We'll handle the preview widget creation later based on availability

    # Timer for debounced input processing
    update_timer = QTimer()
    update_timer.setSingleShot(True)
    update_timer.timeout.connect(lambda: update_preview())

    # --- Main Layout ---
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    main_splitter = QSplitter(Qt.Orientation.Horizontal)
    main_layout.addWidget(main_splitter)

    # --- Left Pane (Input) ---
    input_pane = QWidget()
    input_layout = QVBoxLayout(input_pane)
    input_layout.setContentsMargins(10, 5, 5, 10)
    input_layout.setSpacing(5)

    input_buttons_layout = QHBoxLayout()
    input_buttons_layout.setSpacing(8)

    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    input_buttons_layout.addWidget(clipboard_button)
    input_buttons_layout.addWidget(sample_button)
    input_buttons_layout.addWidget(clear_button)
    input_buttons_layout.addStretch()

    input_layout.addLayout(input_buttons_layout)

    input_text_edit = QTextEdit()
    input_text_edit.setAcceptRichText(False)
    input_layout.addWidget(input_text_edit, 1)

    # --- Right Pane (Output) ---
    output_pane = QWidget()
    output_layout = QVBoxLayout(output_pane)
    output_layout.setContentsMargins(5, 5, 10, 10)
    output_layout.setSpacing(5)

    output_header_layout = QHBoxLayout()
    output_header_layout.setSpacing(8)

    open_browser_button = QPushButton("Open in Browser")

    output_header_layout.addStretch()
    output_header_layout.addWidget(open_browser_button)

    output_layout.addLayout(output_header_layout)

    if WEBENGINE_AVAILABLE:
        output_view = QWebEngineView()
        output_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
    else:
        # Use QTextEdit with native markdown support as lightweight alternative
        output_view = QTextEdit()
        output_view.setReadOnly(True)
        # Set some basic styling for better appearance
        output_view.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                padding: 10px;
            }
        """)
    output_layout.addWidget(output_view, 1)

    # --- Assemble Main Layout ---
    main_splitter.addWidget(input_pane)
    main_splitter.addWidget(output_pane)
    main_splitter.setSizes([450, 450])

    # --- Backend Functions ---
    def update_preview():
        try:
            text = input_text_edit.toPlainText()
            html = markdown.markdown(text, extensions=["fenced_code", "tables"])

            if WEBENGINE_AVAILABLE:
                full_html = f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            background-color: #FFFFFF;
                            padding: 10px;
                        }}
                        pre {{
                            background-color: #F5F5F5;
                            padding: 10px;
                            border-radius: 4px;
                            overflow-x: auto;
                        }}
                        code {{
                            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                        }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; }}
                        th {{ background-color: #f2f2f2; }}
                        blockquote {{ border-left: 4px solid #ddd; padding-left: 10px; color: #666; }}
                    </style>
                </head>
                <body>{html}</body>
                </html>
                """
                output_view.setHtml(full_html)
            else:
                # For QTextEdit, set the HTML directly (basic rendering)
                output_view.setHtml(html)
        except Exception as e:
            logger.exception("Error during Markdown conversion")
            if WEBENGINE_AVAILABLE:
                output_view.setHtml(f"<h1>Error</h1><p>Could not render Markdown: {e!s}</p>")
            else:
                output_view.setPlainText(f"Error: Could not render Markdown: {e!s}")

    def on_input_changed():
        update_timer.start(250)

    def on_clipboard_clicked():
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                input_text_edit.setPlainText(text)
        except Exception as e:
            logger.exception("Error loading from clipboard", exc_info=e)

    def on_sample_clicked():
        input_text_edit.setPlainText(MARKDOWN_SAMPLE_TEXT)

    def on_clear_clicked():
        input_text_edit.clear()
        if WEBENGINE_AVAILABLE:
            output_view.setHtml("")
        else:
            output_view.clear()

    def on_open_browser_clicked():
        def save_and_open(html):
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
                    f.write(html)
                    webbrowser.open("file://" + os.path.realpath(f.name))
                    logger.info(f"Opened preview in browser: {f.name}")
            except Exception as e:
                logger.exception("Failed to save or open temporary file", exc_info=e)

        try:
            if WEBENGINE_AVAILABLE:
                output_view.page().toHtml(save_and_open)
            else:
                # For QTextEdit, get the HTML content directly
                html_content = output_view.toHtml()
                save_and_open(html_content)
        except Exception as e:
            logger.exception("Error getting HTML from view", exc_info=e)

    def load_from_file():
        file_path, _ = QFileDialog.getOpenFileName(
            widget, "Load from File", "", "Markdown Files (*.md *.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, encoding="utf-8") as f:
                    input_text_edit.setPlainText(f.read())
                    update_preview()
            except Exception as e:
                logger.exception("Error loading file", exc_info=e)
                if WEBENGINE_AVAILABLE:
                    output_view.setHtml(f"<h1>Error</h1><p>Could not load file: {e!s}</p>")
                else:
                    output_view.setPlainText(f"Error: Could not load file: {e!s}")
                QMessageBox.critical(widget, "Error", f"Could not read file:\n{e}")

    def show_context_menu(position):
        context_menu = input_text_edit.createStandardContextMenu()
        context_menu.addSeparator()
        load_action = QAction("Load from File...", input_text_edit)
        load_action.triggered.connect(load_from_file)
        context_menu.addAction(load_action)
        context_menu.exec(input_text_edit.mapToGlobal(position))

    # --- Connect Events ---
    input_text_edit.textChanged.connect(on_input_changed)
    clipboard_button.clicked.connect(on_clipboard_clicked)
    sample_button.clicked.connect(on_sample_clicked)
    clear_button.clicked.connect(on_clear_clicked)
    open_browser_button.clicked.connect(on_open_browser_clicked)

    input_text_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    input_text_edit.customContextMenuRequested.connect(show_context_menu)

    logger.info("Markdown Preview widget creation completed")
    return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("Markdown Preview Tool")
    main_window.setGeometry(100, 100, 1000, 700)

    markdown_tool_widget = create_markdown_preview_widget()

    main_window.setCentralWidget(markdown_tool_widget)
    main_window.show()

    sys.exit(app.exec())
