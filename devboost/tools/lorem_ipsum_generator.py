import random
import sys

from faker import Faker  # pip install Faker
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style


class LoremIpsumProcessor:
    """Backend logic class for generating placeholder text."""

    def __init__(self):
        self.fake = Faker()

    def generate(self, text_type: str, count: int) -> str:
        """Generates the specified type of text."""
        results = []
        for _ in range(count):
            if text_type == "Paragraph":
                results.append(self.fake.paragraph(nb_sentences=5))
            elif text_type == "Sentence":
                results.append(self.fake.sentence())
            elif text_type == "Word":
                results.append(self.fake.word())
            elif text_type == "Title":
                results.append(self.fake.sentence(nb_words=4).rstrip(".").title())
            elif text_type == "First name":
                results.append(self.fake.first_name())
            elif text_type == "Last name":
                results.append(self.fake.last_name())
            elif text_type == "Full name":
                results.append(self.fake.name())
            elif text_type == "Email":
                results.append(self.fake.email())
            elif text_type == "URL":
                results.append(self.fake.url())
            elif text_type == "Short tweet":
                text = self.fake.sentence(nb_words=random.randint(8, 15))  # noqa: S311
                hashtag = f"#{self.fake.word().lower()}"
                results.append(f"{text} {hashtag}")
            elif text_type == "Long tweet":
                text = self.fake.paragraph(nb_sentences=random.randint(2, 3))  # noqa: S311
                hashtags = f"#{self.fake.word().lower()} #{self.fake.word().lower()}"
                results.append(f"{text} {hashtags}")
            else:
                results.append("Unsupported type")

        return "\n\n".join(results) if text_type == "Paragraph" else "\n".join(results)


def create_lorem_ipsum_tool_widget(style_func, scratch_pad=None) -> QWidget:
    """
    Creates the Lorem Ipsum Generator tool widget.

    Args:
        style_func: Function to get QStyle for standard icons
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The complete tool widget.
    """
    main_widget = QWidget()
    main_widget.setStyleSheet(get_tool_style())

    main_layout = QHBoxLayout(main_widget)
    main_layout.setContentsMargins(10, 5, 5, 10)
    main_layout.setSpacing(5)

    processor = LoremIpsumProcessor()

    # --- LEFT PANE (CONTROLS) ---
    left_pane = QWidget()
    left_pane.setFixedWidth(150)
    left_pane.setObjectName("leftPane")
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(5, 10, 5, 10)
    left_layout.setSpacing(5)

    # --- RIGHT PANE (OUTPUT) ---
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)

    # Top Controls Bar
    controls_widget = QWidget()
    controls_widget.setObjectName("controlsWidget")
    controls_widget.setFixedHeight(45)
    controls_layout = QHBoxLayout(controls_widget)
    controls_layout.setContentsMargins(10, 5, 10, 5)
    controls_layout.setSpacing(10)

    count_spinbox = QSpinBox()
    count_spinbox.setPrefix("x")
    count_spinbox.setRange(1, 1000)
    count_spinbox.setValue(1)

    mode_combo = QComboBox()
    mode_combo.addItems(["Append", "Replace"])

    clear_button = QPushButton("Clear")
    copy_button = QPushButton("Copy")

    # Optionally add "Send to Scratch Pad" button
    send_to_scratch_pad_button = None
    if scratch_pad:
        send_to_scratch_pad_button = QPushButton("Send to Scratch Pad")

    controls_layout.addWidget(count_spinbox)
    controls_layout.addWidget(mode_combo)
    controls_layout.addStretch()
    controls_layout.addWidget(clear_button)
    controls_layout.addWidget(copy_button)
    if send_to_scratch_pad_button:
        controls_layout.addWidget(send_to_scratch_pad_button)

    # Output text area
    output_text_edit = QTextEdit()
    output_text_edit.setPlaceholderText("Lorem ipsum...")

    right_layout.addWidget(controls_widget)
    right_layout.addWidget(output_text_edit)

    # --- HANDLERS ---
    last_generated_type = None

    def handle_generation(text_type):
        nonlocal last_generated_type
        count = count_spinbox.value()
        mode = mode_combo.currentText()

        generated_text = processor.generate(text_type, count)

        # Remove placeholder text if it's the only thing present
        if output_text_edit.toPlainText() == "Lorem ipsum...":
            output_text_edit.clear()

        if mode == "Append":
            current_text = output_text_edit.toPlainText()
            if current_text:
                output_text_edit.append("\n" + generated_text)
            else:
                output_text_edit.setPlainText(generated_text)
        else:  # Replace
            output_text_edit.setPlainText(generated_text)

        # Track the last generated type for context
        last_generated_type = text_type

    def copy_to_clipboard():
        QApplication.clipboard().setText(output_text_edit.toPlainText())

    # --- ADD BUTTONS and CONNECT ---
    button_types = [
        "Paragraph",
        "Sentence",
        "Word",
        "Title",
        "First name",
        "Last name",
        "Full name",
        "Email",
        "URL",
        "Short tweet",
        "Long tweet",
    ]

    for btn_type in button_types:
        button = QPushButton(btn_type)
        button.clicked.connect(lambda checked, t=btn_type: handle_generation(t))
        left_layout.addWidget(button)

    left_layout.addStretch()

    clear_button.clicked.connect(output_text_edit.clear)
    copy_button.clicked.connect(copy_to_clipboard)

    # Connect "Send to Scratch Pad" button if available
    if send_to_scratch_pad_button:

        def format_lorem_ipsum_output_for_scratch_pad(text_type, count, mode, output_text):
            header = f"Lorem Ipsum Results\nType: {text_type}\nCount: {count}\nMode: {mode}\n" + "=" * 50
            output_section = f"\nOUTPUT:\n{output_text}"
            return f"{header}{output_section}"

        def on_send_to_scratch_pad():
            output_text = output_text_edit.toPlainText()
            if not output_text.strip():
                return
            text_type = last_generated_type or "Unknown"
            count = count_spinbox.value()
            mode = mode_combo.currentText()
            formatted_content = format_lorem_ipsum_output_for_scratch_pad(text_type, count, mode, output_text)
            send_to_scratch_pad(scratch_pad, formatted_content)

        send_to_scratch_pad_button.clicked.connect(on_send_to_scratch_pad)

    # --- FINAL ASSEMBLY ---
    main_layout.addWidget(left_pane)
    main_layout.addWidget(right_pane, 1)  # Give right pane more weight

    return main_widget


def send_to_scratch_pad(scratch_pad, content):
    """
    Send content to the scratch pad.

    Args:
        scratch_pad: The scratch pad widget.
        content (str): The content to send.
    """
    if scratch_pad and content:
        current_content = scratch_pad.get_content()
        new_content = f"{current_content}\n\n---\n{content}" if current_content else content
        scratch_pad.set_content(new_content)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("Lorem Ipsum Generator")
    main_window.setGeometry(100, 100, 800, 600)

    lorem_ipsum_widget = create_lorem_ipsum_tool_widget(app.style)
    main_window.setCentralWidget(lorem_ipsum_widget)

    main_window.show()
    sys.exit(app.exec())
