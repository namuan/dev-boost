import random
import string
import sys
import time

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
    QSlider,
    QSpinBox,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style


class RandomStringProcessor:
    """Backend logic class for generating random strings."""

    def __init__(self):
        self.COLOR_UPPER = "#ac1c1c"
        self.COLOR_LOWER = "#000000"
        self.COLOR_DIGIT = "#5151d3"
        self.COLOR_SYMBOL = "#cc2222"
        self.COLOR_BINARY = "#006600"  # Green color for binary digits
        self.symbols_set = r"!@#$%^&*()_+-=[]{}|;:,.<>/?`~"
        self.binary_set = "01"
        self.hex_set = "0123456789ABCDEF"

    def set_seed(self, seed_value):
        """Sets the random seed for string generation."""
        try:
            if seed_value.isdigit():
                random.seed(int(seed_value))
            else:
                random.seed(seed_value)
        except (ValueError, TypeError):
            random.seed(int(time.time()))

    def generate_random_strings(
        self, num_upper, num_lower, num_digits, num_symbols, count, use_colors=True, preset=None
    ):
        """
        Generates random strings based on the specified parameters.

        Args:
            num_upper: Number of uppercase characters
            num_lower: Number of lowercase characters
            num_digits: Number of digits
            num_symbols: Number of symbols
            count: Number of strings to generate
            use_colors: Whether to use HTML color formatting
            preset: Optional preset name for special generation modes

        Returns:
            tuple: (output_text, is_html) where output_text is the generated text and is_html indicates if it's HTML formatted
        """
        output_lines = []

        for _ in range(count):
            char_list = []

            # Special handling for binary preset
            if preset == "Random Binary":
                char_list.extend(random.choices(self.binary_set, k=num_digits))  # noqa: S311
            # Special handling for hex preset
            elif preset == "Random Hex":
                char_list.extend(random.choices(self.hex_set, k=num_upper + num_digits))  # noqa: S311
            else:
                # Standard character generation
                char_list.extend(random.choices(string.ascii_uppercase, k=num_upper))  # noqa: S311
                char_list.extend(random.choices(string.ascii_lowercase, k=num_lower))  # noqa: S311
                char_list.extend(random.choices(string.digits, k=num_digits))  # noqa: S311
                char_list.extend(random.choices(self.symbols_set, k=num_symbols))  # noqa: S311

            random.shuffle(char_list)

            if use_colors:
                html_line = ""
                for char in char_list:
                    safe_char = char.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    if preset == "Random Binary":
                        html_line += f'<span style="color: {self.COLOR_BINARY};">{safe_char}</span>'
                    elif char in string.ascii_uppercase:
                        html_line += f'<span style="color: {self.COLOR_UPPER};">{safe_char}</span>'
                    elif char in string.ascii_lowercase:
                        html_line += f'<span style="color: {self.COLOR_LOWER};">{safe_char}</span>'
                    elif char in string.digits:
                        html_line += f'<span style="color: {self.COLOR_DIGIT};">{safe_char}</span>'
                    else:
                        html_line += f'<span style="color: {self.COLOR_SYMBOL};">{safe_char}</span>'
                output_lines.append(html_line)
            else:
                output_lines.append("".join(char_list))

        if use_colors:
            return "<br>".join(output_lines), True
        return "\n".join(output_lines), False

    def generate_new_seed(self):
        """Generates a new seed based on current time."""
        return str(int(time.time() * 1000))


def create_random_string_tool_widget(style=None, scratch_pad=None) -> QWidget:
    """
    Creates the Random String Generator tool widget.

    Args:
        style: Optional style parameter (not used but included for consistency with other tools)

    Returns:
        QWidget: The complete tool widget.
    """
    # Create the processor instance
    processor = RandomStringProcessor()

    # --- MAIN WIDGET & LAYOUT ---
    main_widget = QWidget()
    main_layout = QHBoxLayout(main_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # --- LEFT PANE (CONTROLS) ---
    left_pane = QWidget()
    left_pane.setObjectName("leftPane")
    left_pane.setFixedWidth(320)
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(15, 10, 15, 15)
    left_layout.setSpacing(12)

    # --- RIGHT PANE (OUTPUT) ---
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)

    # --- LEFT PANE WIDGETS ---

    # Presets
    presets_layout = QHBoxLayout()
    presets_combo = QComboBox()
    presets_combo.addItem("(Click to Select)")
    presets_combo.addItem("Strong Password")
    presets_combo.addItem("Long Password")
    presets_combo.addItem("License Key")
    presets_combo.addItem("Passphrase")
    presets_combo.addItem("PIN Code")
    presets_combo.addItem("Long PIN Code")
    presets_combo.addItem("Random Number")
    presets_combo.addItem("Random String")
    presets_combo.addItem("Random Hex")
    presets_combo.addItem("Random Binary")
    presets_combo.addItem("Random Everything")
    sample_button = QPushButton("Sample")
    sample_button.setFixedWidth(80)
    presets_layout.addWidget(presets_combo)
    presets_layout.addWidget(sample_button)
    left_layout.addLayout(presets_layout)

    # Seed
    seed_layout = QHBoxLayout()
    seed_label = QLabel("Seed")
    seed_input = QLineEdit("15092506351219123587")
    # Description for image generation AI: A flat, circular, anti-clockwise arrow icon (a refresh or reload symbol).
    reload_icon = main_widget.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
    seed_reload_button = QPushButton()
    seed_reload_button.setObjectName("iconButton")
    seed_reload_button.setIcon(reload_icon)
    seed_reload_button.setFixedSize(32, 32)
    seed_layout.addWidget(seed_label)
    seed_layout.addSpacing(10)
    seed_layout.addWidget(seed_input, 1)
    seed_layout.addWidget(seed_reload_button)
    left_layout.addLayout(seed_layout)

    # Character Type Controls
    control_rows = {}

    def create_char_control(label_text, default_value):
        layout = QVBoxLayout()
        layout.setSpacing(4)

        top_layout = QHBoxLayout()
        label = QLabel(label_text)

        spinbox = QSpinBox()
        spinbox.setRange(0, 100)
        spinbox.setFixedSize(55, 28)
        spinbox.setValue(default_value)

        top_layout.addWidget(label)
        top_layout.addStretch()
        top_layout.addWidget(spinbox)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(default_value)

        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)

        layout.addLayout(top_layout)
        layout.addWidget(slider)

        control_rows[label_text] = (slider, spinbox)
        return layout

    left_layout.addLayout(create_char_control("Uppercased Characters:", 6))
    left_layout.addLayout(create_char_control("Lowercased Characters:", 6))
    left_layout.addLayout(create_char_control("Symbols:", 2))
    left_layout.addLayout(create_char_control("Digits:", 3))
    left_layout.addSpacing(10)

    left_layout.addStretch()

    # --- RIGHT PANE WIDGETS ---

    # Top Controls Bar
    controls_widget = QWidget()
    controls_widget.setObjectName("controlsWidget")
    controls_widget.setFixedHeight(45)
    controls_layout = QHBoxLayout(controls_widget)
    controls_layout.setContentsMargins(10, 5, 10, 5)
    controls_layout.setSpacing(10)

    colors_checkbox = QCheckBox("Colors")
    colors_checkbox.setChecked(True)
    colors_checkbox.setStyleSheet("font-size: 14px;")

    count_spinbox = QSpinBox()
    count_spinbox.setPrefix("x")
    count_spinbox.setRange(1, 100)
    count_spinbox.setValue(1)
    count_spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
    count_spinbox.setFixedWidth(40)

    copy_button = QPushButton("Copy")

    # Add "Send to Scratch Pad" button if scratch_pad is provided
    if scratch_pad:
        send_to_scratch_pad_button = QPushButton("Send to Scratch Pad")
        send_to_scratch_pad_button.clicked.connect(
            lambda: send_to_scratch_pad(scratch_pad, output_text_edit.toPlainText())
        )
        controls_layout.addWidget(send_to_scratch_pad_button)

    controls_layout.addStretch()
    controls_layout.addWidget(colors_checkbox)
    controls_layout.addWidget(count_spinbox)
    controls_layout.addWidget(copy_button)

    # Output text area
    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    output_text_edit.setFontFamily("Menlo, Courier New, monospace")

    right_layout.addWidget(controls_widget)
    right_layout.addWidget(output_text_edit, 1)

    # --- LOGIC AND HANDLERS ---
    def generate_and_display():
        # Set the seed
        processor.set_seed(seed_input.text())

        # Get parameters from UI
        num_upper = control_rows["Uppercased Characters:"][1].value()
        num_lower = control_rows["Lowercased Characters:"][1].value()
        num_digits = control_rows["Digits:"][1].value()
        num_symbols = control_rows["Symbols:"][1].value()
        total_lines = count_spinbox.value()
        use_colors = colors_checkbox.isChecked()

        # Get current preset if any
        current_preset = presets_combo.currentText()
        if current_preset == "(Click to Select)":
            current_preset = None

        # Generate the strings
        output_text, is_html = processor.generate_random_strings(
            num_upper, num_lower, num_digits, num_symbols, total_lines, use_colors, preset=current_preset
        )

        # Display the result
        if is_html:
            output_text_edit.setHtml(output_text)
        else:
            output_text_edit.setPlainText(output_text)

    def copy_to_clipboard():
        QApplication.clipboard().setText(output_text_edit.toPlainText())

    def reset_seed():
        new_seed = processor.generate_new_seed()
        seed_input.setText(new_seed)
        generate_and_display()

    def apply_preset(preset_name):
        if preset_name == "(Click to Select)":
            return

        # Reset all controls to default values
        for control_name, (_slider, spinbox) in control_rows.items():
            if control_name == "Uppercased Characters:" or control_name == "Lowercased Characters:":
                spinbox.setValue(6)
            elif control_name == "Symbols:":
                spinbox.setValue(2)
            elif control_name == "Digits:":
                spinbox.setValue(3)
            elif control_name == "Words:" or control_name == "Separating Group Size:":
                spinbox.setValue(0)

        # Apply specific preset configurations
        if preset_name == "Strong Password":
            control_rows["Uppercased Characters:"][1].setValue(4)
            control_rows["Lowercased Characters:"][1].setValue(6)
            control_rows["Symbols:"][1].setValue(2)
            control_rows["Digits:"][1].setValue(2)
            count_spinbox.setValue(5)

        elif preset_name == "Long Password":
            control_rows["Uppercased Characters:"][1].setValue(8)
            control_rows["Lowercased Characters:"][1].setValue(12)
            control_rows["Symbols:"][1].setValue(4)
            control_rows["Digits:"][1].setValue(4)
            count_spinbox.setValue(3)

        elif preset_name == "License Key":
            control_rows["Uppercased Characters:"][1].setValue(16)
            control_rows["Lowercased Characters:"][1].setValue(0)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(4)
            count_spinbox.setValue(5)

        elif preset_name == "Passphrase":
            control_rows["Uppercased Characters:"][1].setValue(0)
            control_rows["Lowercased Characters:"][1].setValue(20)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(0)
            count_spinbox.setValue(4)

        elif preset_name == "PIN Code":
            control_rows["Uppercased Characters:"][1].setValue(0)
            control_rows["Lowercased Characters:"][1].setValue(0)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(4)
            count_spinbox.setValue(10)

        elif preset_name == "Long PIN Code":
            control_rows["Uppercased Characters:"][1].setValue(0)
            control_rows["Lowercased Characters:"][1].setValue(0)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(8)
            count_spinbox.setValue(5)

        elif preset_name == "Random Number":
            control_rows["Uppercased Characters:"][1].setValue(0)
            control_rows["Lowercased Characters:"][1].setValue(0)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(10)
            count_spinbox.setValue(8)

        elif preset_name == "Random String":
            control_rows["Uppercased Characters:"][1].setValue(5)
            control_rows["Lowercased Characters:"][1].setValue(5)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(0)
            count_spinbox.setValue(10)

        elif preset_name == "Random Hex":
            control_rows["Uppercased Characters:"][1].setValue(8)  # A-F
            control_rows["Lowercased Characters:"][1].setValue(0)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(8)  # 0-9
            count_spinbox.setValue(8)

        elif preset_name == "Random Binary":
            control_rows["Uppercased Characters:"][1].setValue(0)
            control_rows["Lowercased Characters:"][1].setValue(0)
            control_rows["Symbols:"][1].setValue(0)
            control_rows["Digits:"][1].setValue(16)  # Only 0-1 will be used
            count_spinbox.setValue(5)

        elif preset_name == "Random Everything":
            control_rows["Uppercased Characters:"][1].setValue(10)
            control_rows["Lowercased Characters:"][1].setValue(10)
            control_rows["Symbols:"][1].setValue(10)
            control_rows["Digits:"][1].setValue(10)
            count_spinbox.setValue(5)

        # Generate new strings with the preset configuration
        generate_and_display()

    # --- CONNECTIONS ---
    sample_button.clicked.connect(generate_and_display)
    copy_button.clicked.connect(copy_to_clipboard)
    seed_reload_button.clicked.connect(reset_seed)
    colors_checkbox.toggled.connect(generate_and_display)
    presets_combo.currentTextChanged.connect(apply_preset)

    for _, (slider, _spinbox) in control_rows.items():
        slider.valueChanged.connect(generate_and_display)
    count_spinbox.valueChanged.connect(generate_and_display)

    main_widget.setStyleSheet(get_tool_style())

    main_layout.addWidget(left_pane)
    main_layout.addWidget(right_pane, 1)

    generate_and_display()
    return main_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Random String Generator")
    main_window.setGeometry(100, 100, 900, 600)
    random_string_widget = create_random_string_tool_widget(scratch_pad=None)
    main_window.setCentralWidget(random_string_widget)
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
