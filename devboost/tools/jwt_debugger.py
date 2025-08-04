import base64
import hashlib
import hmac
import json
import sys
import time

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_status_style, get_tool_style


class JWTDebugger:
    """
    Backend class for JWT parsing, validation, and debugging.
    """

    SUPPORTED_ALGORITHMS = {  # noqa: RUF012
        "HS256": hashlib.sha256,
        "HS384": hashlib.sha384,
        "HS512": hashlib.sha512,
    }

    def __init__(self):
        self.header = {}
        self.payload = {}
        self.signature = ""
        self.algorithm = "HS256"
        self.secret = ""
        self.is_valid = False
        self.error_message = ""

    def _base64_url_decode(self, data: str) -> bytes:
        """Decode base64url encoded data."""
        # Add padding if necessary
        missing_padding = len(data) % 4
        if missing_padding:
            data += "=" * (4 - missing_padding)

        # Replace URL-safe characters
        data = data.replace("-", "+").replace("_", "/")

        try:
            return base64.b64decode(data)
        except Exception as e:
            raise ValueError(f"Invalid base64url encoding: {e}") from e

    def _base64_url_encode(self, data: bytes) -> str:
        """Encode data to base64url format."""
        encoded = base64.b64encode(data).decode("utf-8")
        return encoded.replace("+", "-").replace("/", "_").rstrip("=")

    def parse_jwt(self, token: str) -> tuple[bool, str]:
        """
        Parse a JWT token into its components.

        Args:
            token: The JWT token string

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Reset state
            self.header = {}
            self.payload = {}
            self.signature = ""
            self.is_valid = False
            self.error_message = ""

            # Split token into parts
            parts = token.strip().split(".")
            if len(parts) != 3:
                self.error_message = "Invalid JWT format. Expected 3 parts separated by dots."
                return False, self.error_message

            header_b64, payload_b64, signature_b64 = parts

            # Decode header
            try:
                header_bytes = self._base64_url_decode(header_b64)
                self.header = json.loads(header_bytes.decode("utf-8"))
            except Exception as e:
                self.error_message = f"Invalid header: {e}"
                return False, self.error_message

            # Decode payload
            try:
                payload_bytes = self._base64_url_decode(payload_b64)
                self.payload = json.loads(payload_bytes.decode("utf-8"))
            except Exception as e:
                self.error_message = f"Invalid payload: {e}"
                return False, self.error_message

            # Store signature
            self.signature = signature_b64

            # Extract algorithm from header
            self.algorithm = self.header.get("alg", "HS256")

            return True, ""

        except Exception as e:
            self.error_message = f"Failed to parse JWT: {e}"
            return False, self.error_message

    def verify_signature(self, token: str, secret: str) -> tuple[bool, str]:
        """
        Verify the JWT signature.

        Args:
            token: The JWT token string
            secret: The secret key for verification

        Returns:
            Tuple of (is_valid, status_message)
        """
        try:
            if not token or not secret:
                return False, "Token and secret are required for verification"

            parts = token.strip().split(".")
            if len(parts) != 3:
                return False, "Invalid JWT format"

            header_b64, payload_b64, signature_b64 = parts

            # Check if algorithm is supported
            if self.algorithm not in self.SUPPORTED_ALGORITHMS:
                return False, f"Unsupported algorithm: {self.algorithm}"

            # Create the signing input
            signing_input = f"{header_b64}.{payload_b64}"

            # Generate expected signature
            hash_func = self.SUPPORTED_ALGORITHMS[self.algorithm]
            expected_signature = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hash_func).digest()

            expected_signature_b64 = self._base64_url_encode(expected_signature)

            # Compare signatures
            if hmac.compare_digest(signature_b64, expected_signature_b64):
                self.is_valid = True
                return True, "Signature verified successfully"
            else:
                self.is_valid = False
                return False, "Invalid signature"

        except Exception as e:
            self.is_valid = False
            return False, f"Verification failed: {e}"

    def get_header_json(self) -> str:
        """Get formatted header JSON."""
        if not self.header:
            return "{\n}"
        return json.dumps(self.header, indent=2)

    def get_payload_json(self) -> str:
        """Get formatted payload JSON."""
        if not self.payload:
            return "{\n}"
        return json.dumps(self.payload, indent=2)

    def get_signature_formula(self) -> str:
        """Get the signature formula HTML."""
        algo_name = self.algorithm.replace("HS", "HMACSHA")
        return f"""
        <pre style="font-family: Consolas, Courier New, monospace; color: #333; margin: 8px;"><font color="#e14295">{algo_name}</font>(
          <font color="#2484c1">base64UrlEncode</font>(header) + <font color="#d73a49">"."
          <font color="#2484c1">base64UrlEncode</font>(payload),
        </pre>
        """

    def check_expiration(self) -> tuple[bool, str]:
        """Check if the JWT token is expired.

        Returns:
            Tuple of (is_expired, message)
        """
        if not self.payload:
            return False, "No payload to check"

        exp_claim = self.payload.get("exp")
        if exp_claim is None:
            return False, "No expiration claim found"

        try:
            # Convert exp claim to timestamp
            exp_timestamp = int(exp_claim)
            current_timestamp = int(time.time())

            if current_timestamp > exp_timestamp:
                exp_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(exp_timestamp))
                return True, f"Token expired on {exp_time}"
            else:
                exp_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(exp_timestamp))
                return False, f"Token valid until {exp_time}"

        except (ValueError, TypeError):
            return False, "Invalid expiration claim format"


# ruff: noqa: C901
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
    # Create JWT backend instance
    jwt_backend = JWTDebugger()

    main_widget = QWidget()
    main_widget.setObjectName("jwtDebugger")
    main_widget.setStyleSheet(get_tool_style())

    # --- Main Layout ---
    top_level_layout = QVBoxLayout(main_widget)
    top_level_layout.setContentsMargins(0, 0, 0, 0)
    top_level_layout.setSpacing(0)

    # Create horizontal splitter for main content
    main_splitter = QSplitter(Qt.Orientation.Horizontal)
    main_splitter.setContentsMargins(0, 0, 0, 0)

    # --- Left Pane (Encoded Input) ---
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(10, 5, 5, 10)
    left_layout.setSpacing(5)

    # Top controls
    left_controls_layout = QHBoxLayout()
    left_controls_layout.setSpacing(8)

    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    left_controls_layout.addWidget(clipboard_button)
    left_controls_layout.addWidget(sample_button)
    left_controls_layout.addWidget(clear_button)
    left_controls_layout.addStretch()

    # Input text area
    encoded_text_edit = QTextEdit()
    encoded_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    left_layout.addLayout(left_controls_layout)
    left_layout.addWidget(encoded_text_edit)

    # --- Right Pane (Decoded Output) ---
    right_pane = QWidget()
    right_pane.setObjectName("rightPane")
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(10, 5, 5, 10)
    right_layout.setSpacing(5)

    # Algorithm selector
    algo_layout = QHBoxLayout()
    algo_combo = QComboBox()
    algo_combo.addItems([
        "HS256",
    ])
    algo_layout.addWidget(algo_combo)
    algo_layout.addStretch()

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
    verification_layout.setSpacing(5)

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

    main_splitter.addWidget(left_pane)
    main_splitter.addWidget(right_pane)
    main_splitter.setSizes([500, 500])  # Give more space to right pane for decoded content

    # --- Status Bar ---
    status_bar = QWidget()
    status_bar.setObjectName("statusBar")
    status_bar.setFixedHeight(30)
    status_layout = QHBoxLayout(status_bar)
    status_layout.setContentsMargins(10, 0, 10, 0)
    status_label = QLabel("Verification Status: No Input")
    status_label.setObjectName("statusLabel")
    status_layout.addWidget(status_label)

    top_level_layout.addWidget(main_splitter, 1)
    top_level_layout.addWidget(status_bar)

    # --- Backend Integration ---
    def update_jwt_display():
        """Update the JWT display based on current input."""
        token = encoded_text_edit.toPlainText().strip()
        secret = secret_input.toPlainText().strip()

        if not token:
            # Clear all fields when no input
            header_text_edit.setText("{\n}")
            payload_text_edit.setText("{\n}")
            signature_formula_edit.setHtml(jwt_backend.get_signature_formula())
            status_label.setText("Verification Status: No Input")
            return

        # Parse JWT
        success, error_msg = jwt_backend.parse_jwt(token)

        if success:
            # Update header and payload displays
            header_text_edit.setText(jwt_backend.get_header_json())
            payload_text_edit.setText(jwt_backend.get_payload_json())

            # Update algorithm combo box
            algo_index = algo_combo.findText(jwt_backend.algorithm)
            if algo_index >= 0:
                algo_combo.setCurrentIndex(algo_index)

            # Update signature formula
            signature_formula_edit.setHtml(jwt_backend.get_signature_formula())

            # Check for expiration
            is_expired, exp_msg = jwt_backend.check_expiration()

            # Verify signature if secret is provided
            if secret:
                is_valid, status_msg = jwt_backend.verify_signature(token, secret)
                if is_valid:
                    if is_expired:
                        status_label.setText(f"Verification Status: ⚠️ Valid signature but {exp_msg}")
                        status_label.setStyleSheet("color: #ff8c00;")
                    else:
                        status_label.setText(f"Verification Status: ✓ {status_msg}. {exp_msg}")
                        status_label.setStyleSheet("color: #28a745;")
                else:
                    status_label.setText(f"Verification Status: ✗ {status_msg}")
                    status_label.setStyleSheet(get_status_style("error"))
            else:
                if is_expired:
                    status_label.setText(f"Verification Status: ⚠️ Parsed successfully but {exp_msg}")
                    status_label.setStyleSheet("color: #ff8c00;")
                else:
                    exp_info = f". {exp_msg}" if "valid until" in exp_msg else ""
                    status_label.setText(f"Verification Status: Parsed successfully (no secret provided){exp_info}")
                    status_label.setStyleSheet("color: #ffc107;")
        else:
            # Show error
            header_text_edit.setText("{\n}")
            payload_text_edit.setText("{\n}")
            status_label.setText(f"Verification Status: ✗ {error_msg}")
            status_label.setStyleSheet(get_status_style("error"))

    def on_algorithm_changed():
        """Handle algorithm selection change."""
        jwt_backend.algorithm = algo_combo.currentText()
        signature_formula_edit.setHtml(jwt_backend.get_signature_formula())
        update_jwt_display()

    def copy_to_clipboard(text):
        """Copy text to clipboard."""
        app = QApplication.instance()
        if app:
            app.clipboard().setText(text)

    def load_sample_jwt():
        """Load a sample JWT for testing."""
        sample_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        encoded_text_edit.setText(sample_jwt)
        secret_input.setText("your-256-bit-secret")
        update_jwt_display()

    def clear_input():
        """Clear all input fields."""
        encoded_text_edit.clear()
        secret_input.clear()
        update_jwt_display()

    def paste_from_clipboard():
        """Paste content from clipboard."""
        app = QApplication.instance()
        if app:
            clipboard_text = app.clipboard().text()
            if clipboard_text:
                encoded_text_edit.setText(clipboard_text)
                update_jwt_display()

    # Connect UI events
    encoded_text_edit.textChanged.connect(update_jwt_display)
    secret_input.textChanged.connect(update_jwt_display)
    algo_combo.currentTextChanged.connect(on_algorithm_changed)

    # Connect buttons
    sample_button.clicked.connect(load_sample_jwt)
    clear_button.clicked.connect(clear_input)
    clipboard_button.clicked.connect(paste_from_clipboard)

    # Copy buttons
    header_copy_button.clicked.connect(lambda: copy_to_clipboard(header_text_edit.toPlainText()))
    payload_copy_button.clicked.connect(lambda: copy_to_clipboard(payload_text_edit.toPlainText()))

    # Initialize display
    update_jwt_display()

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
