import sys

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def create_jwt_debugger_widget(style_func):
    """
    Creates the main JWT Debugger widget.

    This function constructs the entire UI seen in the screenshot, which consists
    of an encoded input pane on the left, a decoded output pane on the right,
    and a status bar at the bottom.

    Args:
        style_func: A function that returns a QStyle object, used for standard icons.

    Returns:
        QWidget: The fully constructed JWT Debugger widget.
    """
    main_widget = QWidget()
    main_widget.setObjectName("jwtDebugger")
    main_widget.setStyleSheet("""
        QWidget#jwtDebugger {
            background-color: #fdfdfd;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 14px;
        }
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            padding: 8px;
            color: #333333;
        }
        QTextEdit:read-only {
            background-color: #f8f8f8;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #dcdcdc;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton#iconButton {
            background-color: transparent;
            border: none;
            padding: 2px;
        }
        QLabel {
            font-size: 14px;
            color: #333333;
        }
        QFrame#rightPane {
            background-color: #f7f7f7;
            border-left: 1px solid #e0e0e0;
        }
        QTextEdit#signatureFormulaEdit {
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
            border-bottom: none;
            background-color: #ffffff;
        }
        QTextEdit#secretInput {
            border-top-left-radius: 0;
            border-top-right-radius: 0;
            background-color: #ffffff;
            font-style: italic;
        }
        QFrame#verificationFrame {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }
        QComboBox {
            padding: 4px 8px;
            border: 1px solid #dcdcdc;
            border-radius: 4px;
        }
        QWidget#statusBar {
            border-top: 1px solid #e0e0e0;
            background-color: #f7f7f7;
        }
        QLabel#statusLabel {
            font-size: 13px;
            color: #555555;
        }
    """)

    # --- Main Layout ---
    top_level_layout = QVBoxLayout(main_widget)
    top_level_layout.setContentsMargins(0, 0, 0, 0)
    top_level_layout.setSpacing(0)

    content_layout = QHBoxLayout()
    content_layout.setContentsMargins(0, 10, 0, 10)
    content_layout.setSpacing(0)

    # --- Left Pane (Encoded Input) ---
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(10, 0, 10, 0)
    left_layout.setSpacing(8)

    # Top controls
    left_controls_layout = QHBoxLayout()
    left_controls_layout.setSpacing(8)

    input_label = QLabel("Input:")
    input_label.setVisible(False)  # As per screenshot, no explicit "Input" label
    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")
    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A flat, gray gear icon for settings.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))

    left_controls_layout.addWidget(input_label)
    left_controls_layout.addWidget(clipboard_button)
    left_controls_layout.addWidget(sample_button)
    left_controls_layout.addWidget(clear_button)
    left_controls_layout.addStretch()
    left_controls_layout.addWidget(settings_button)

    # Input text area
    encoded_text_edit = QTextEdit()
    encoded_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    placeholder_text = (
        "- Enter Your Text\n"
        "- Drag/Drop Files\n"
        "- Right Click → Load From File...\n"
        "- ⌘ + F to Search\n"
        "- ⌘ + ⇧ + F to Replace"
    )
    encoded_text_edit.setPlaceholderText(placeholder_text)

    left_layout.addLayout(left_controls_layout)
    left_layout.addWidget(encoded_text_edit)

    # --- Right Pane (Decoded Output) ---
    right_pane = QWidget()
    right_pane.setObjectName("rightPane")
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(10, 0, 10, 0)
    right_layout.setSpacing(15)

    # Algorithm selector
    algo_layout = QHBoxLayout()
    algo_combo = QComboBox()
    algo_combo.addItems([
        "HS256",
        "HS384",
        "HS512",
        "RS256",
        "RS384",
        "RS512",
        "ES256",
        "ES384",
        "ES512",
        "PS256",
        "PS384",
        "PS512",
    ])
    algo_copy_button = QPushButton()
    algo_copy_button.setObjectName("iconButton")
    # Image description: A copy icon. Two overlapping pages.
    algo_copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
    algo_layout.addWidget(algo_combo)
    algo_layout.addStretch()
    algo_layout.addWidget(algo_copy_button)

    # Header section
    header_layout = QVBoxLayout()
    header_bar_layout = QHBoxLayout()
    header_bar_layout.addWidget(QLabel("Header:"))
    header_bar_layout.addStretch()
    header_copy_button = QPushButton("Copy")
    header_bar_layout.addWidget(header_copy_button)
    header_text_edit = QTextEdit()
    header_text_edit.setReadOnly(True)
    header_text_edit.setText("{\n}")
    header_text_edit.setFixedHeight(100)
    header_layout.addLayout(header_bar_layout)
    header_layout.addWidget(header_text_edit)

    # Payload section
    payload_layout = QVBoxLayout()
    payload_bar_layout = QHBoxLayout()
    payload_bar_layout.addWidget(QLabel("Payload:"))
    payload_bar_layout.addStretch()
    payload_copy_button = QPushButton("Copy")
    payload_bar_layout.addWidget(payload_copy_button)
    payload_text_edit = QTextEdit()
    payload_text_edit.setReadOnly(True)
    payload_text_edit.setText("{\n}")
    payload_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    payload_layout.addLayout(payload_bar_layout)
    payload_layout.addWidget(payload_text_edit)

    # Signature section
    signature_layout = QVBoxLayout()
    signature_layout.setSpacing(5)
    signature_bar_layout = QHBoxLayout()
    signature_bar_layout.addWidget(QLabel("Signature:"))
    signature_layout.addLayout(signature_bar_layout)

    # Verification formula and secret input
    verification_frame = QFrame()
    verification_frame.setObjectName("verificationFrame")
    verification_layout = QVBoxLayout(verification_frame)
    verification_layout.setContentsMargins(0, 0, 0, 0)
    verification_layout.setSpacing(0)

    signature_formula_edit = QTextEdit()
    signature_formula_edit.setObjectName("signatureFormulaEdit")
    signature_formula_edit.setReadOnly(True)
    signature_html = """
    <pre style="font-family: Consolas, Courier New, monospace; color: #333; margin: 8px;"><font color="#e14295">HMACSHA256</font>(
      <font color="#2484c1">base64UrlEncode</font>(header) + <font color="#d73a49">"."</font> +
      <font color="#2484c1">base64UrlEncode</font>(payload),
    </pre>
    """
    signature_formula_edit.setHtml(signature_html)
    signature_formula_edit.setFixedHeight(90)

    secret_input = QTextEdit()
    secret_input.setObjectName("secretInput")
    secret_input.setPlaceholderText("your-secret")
    secret_input.setFixedHeight(50)

    verification_layout.addWidget(signature_formula_edit)
    verification_layout.addWidget(secret_input)
    signature_layout.addWidget(verification_frame)

    right_layout.addLayout(algo_layout)
    right_layout.addLayout(header_layout)
    right_layout.addLayout(payload_layout, 1)  # Make payload stretchable
    right_layout.addLayout(signature_layout)
    right_layout.addStretch()

    content_layout.addWidget(left_pane, 1)
    content_layout.addWidget(right_pane, 1)

    # --- Status Bar ---
    status_bar = QWidget()
    status_bar.setObjectName("statusBar")
    status_bar.setFixedHeight(30)
    status_layout = QHBoxLayout(status_bar)
    status_layout.setContentsMargins(10, 0, 10, 0)
    status_label = QLabel("Verification Status: No Input")
    status_label.setObjectName("statusLabel")
    status_layout.addWidget(status_label)

    top_level_layout.addLayout(content_layout, 1)
    top_level_layout.addWidget(status_bar)

    return main_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Main window to host the widget
    main_window = QMainWindow()
    main_window.setWindowTitle("JWT Debugger")
    main_window.setGeometry(100, 100, 1200, 700)

    # The widget needs a function to get the application style for icons
    jwt_tool_widget = create_jwt_debugger_widget(app.style)

    # Set the created widget as the central widget of the main window.
    main_window.setCentralWidget(jwt_tool_widget)

    main_window.show()
    sys.exit(app.exec())
