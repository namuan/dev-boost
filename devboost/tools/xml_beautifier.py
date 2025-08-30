import sys
import xml.dom.minidom

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style


class XMLProcessor(QObject):
    """Backend XML processing logic."""

    def beautify_xml(self, xml_string: str, indent: int) -> tuple[bool, str, str]:
        """
        Beautifies an XML string.
        Args:
            xml_string: The input XML string.
            indent: Number of spaces for indentation.
        Returns:
            A tuple containing success status, the result, and an error message.
        """
        if not xml_string.strip():
            return True, "", ""
        try:
            dom = xml.dom.minidom.parseString(xml_string)  # noqa: S318
            pretty_xml = dom.toprettyxml(indent=" " * indent)
            lines = pretty_xml.split("\n")
            # Remove XML declaration and filter out empty lines
            result_lines = [line for line in lines if line.strip() and not line.startswith("<?xml")]
            return True, "\n".join(result_lines), ""
        except Exception as e:
            return False, "", str(e)

    def get_sample_xml(self) -> str:
        """Returns a sample XML string."""
        return """<data>
<item id="1">
    <name>Product A</name>
    <price currency="USD">19.99</price>
    <tags>
        <tag>electronics</tag>
        <tag>gadget</tag>
    </tags>
</item>
<item id="2">
    <name>Product B</name>
    <price currency="EUR">25.50</price>
    <tags>
        <tag>home</tag>
        <tag>kitchen</tag>
    </tags>
</item>
</data>"""


# ruff: noqa: C901
def create_xml_formatter_widget(style_func, scratch_pad=None):
    """Creates the main widget for the XML formatter tool."""
    xml_processor = XMLProcessor()

    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    splitter = QSplitter(Qt.Orientation.Horizontal)
    main_layout.addWidget(splitter, 1)

    # --- Left Pane (Input) ---
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(10, 5, 5, 10)
    left_layout.setSpacing(5)

    input_toolbar_layout = QHBoxLayout()
    input_toolbar_layout.setSpacing(8)

    clipboard_button = QPushButton("Clipboard")
    input_toolbar_layout.addWidget(clipboard_button)
    sample_button = QPushButton("Sample")
    input_toolbar_layout.addWidget(sample_button)
    clear_button = QPushButton("Clear")
    input_toolbar_layout.addWidget(clear_button)
    input_toolbar_layout.addStretch()

    left_layout.addLayout(input_toolbar_layout)

    input_text_edit = QTextEdit()
    left_layout.addWidget(input_text_edit)
    splitter.addWidget(left_pane)

    # --- Right Pane (Output) ---
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(10, 5, 5, 10)
    right_layout.setSpacing(5)

    output_toolbar_layout = QHBoxLayout()

    output_toolbar_layout.addStretch()

    spaces_combo = QComboBox()
    spaces_combo.addItem("2 spaces")
    spaces_combo.addItem("4 spaces")
    output_toolbar_layout.addWidget(spaces_combo)

    copy_button = QPushButton("Copy")
    output_toolbar_layout.addWidget(copy_button)

    # Add "Send to Scratch Pad" button if scratch_pad is provided
    if scratch_pad:
        send_to_scratch_pad_button = QPushButton("Send to Scratch Pad")
        send_to_scratch_pad_button.clicked.connect(
            lambda: send_to_scratch_pad(scratch_pad, output_text_edit.toPlainText())
        )
        output_toolbar_layout.addWidget(send_to_scratch_pad_button)

    right_layout.addLayout(output_toolbar_layout)

    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    right_layout.addWidget(output_text_edit)
    splitter.addWidget(right_pane)

    splitter.setSizes([300, 300])

    # --- Connect signals and slots ---
    def process_xml():
        input_text = input_text_edit.toPlainText()
        if not input_text.strip():
            output_text_edit.clear()
            return

        indent = 2 if spaces_combo.currentText() == "2 spaces" else 4
        success, result, error = xml_processor.beautify_xml(input_text, indent)

        if success:
            output_text_edit.setPlainText(result)
        else:
            output_text_edit.setPlainText(f"Error: {error}")

    def load_sample():
        sample_xml = xml_processor.get_sample_xml()
        input_text_edit.setPlainText(sample_xml)

    def clear_all():
        input_text_edit.clear()
        output_text_edit.clear()

    def copy_output():
        output_text = output_text_edit.toPlainText()
        if output_text.strip():
            QApplication.clipboard().setText(output_text)
            msg_box = QMessageBox(widget)
            msg_box.setText("Output copied to clipboard!")
            msg_box.setWindowTitle("Copied")
            msg_box.exec()

    def load_from_clipboard():
        clipboard_text = QApplication.clipboard().text()
        if clipboard_text:
            input_text_edit.setPlainText(clipboard_text)

    sample_button.clicked.connect(load_sample)
    clipboard_button.clicked.connect(load_from_clipboard)
    clear_button.clicked.connect(clear_all)
    copy_button.clicked.connect(copy_output)

    input_text_edit.textChanged.connect(process_xml)
    spaces_combo.currentIndexChanged.connect(process_xml)

    return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("XML Beautify/Minify Tool")
    main_window.setGeometry(100, 100, 800, 600)

    central_widget = create_xml_formatter_widget(app.style, None)
    main_window.setCentralWidget(central_widget)

    main_window.show()
    sys.exit(app.exec())


def send_to_scratch_pad(scratch_pad, content):
    """
    Send content to the scratch pad.

    Args:
        scratch_pad: The scratch pad widget.
        content (str): The content to send.
    """
    if scratch_pad and content:
        # Append content to the scratch pad with a separator
        current_content = scratch_pad.get_content()
        new_content = f"{current_content}\n\n---\n{content}" if current_content else content
        scratch_pad.set_content(new_content)
