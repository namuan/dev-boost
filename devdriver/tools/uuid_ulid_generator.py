import logging
import sys
import uuid
import time
import random
import struct
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union

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
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QClipboard

logger = logging.getLogger(__name__)


class UUIDULIDProcessor:
    """Backend logic class for UUID/ULID generation and decoding."""
    
    # ULID encoding alphabet (Crockford's Base32)
    ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    
    @staticmethod
    def generate_uuid_v1() -> str:
        """Generate a UUID version 1 (time-based)."""
        return str(uuid.uuid1())
    
    @staticmethod
    def generate_uuid_v4() -> str:
        """Generate a UUID version 4 (random)."""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_ulid() -> str:
        """Generate a ULID (Universally Unique Lexicographically Sortable Identifier)."""
        # ULID format: 48-bit timestamp + 80-bit randomness
        timestamp = int(time.time() * 1000)  # milliseconds since epoch
        
        # Encode timestamp (48 bits)
        timestamp_part = UUIDULIDProcessor._encode_base32(timestamp, 10)
        
        # Generate random part (80 bits = 16 characters in base32)
        random_bytes = random.getrandbits(80)
        random_part = UUIDULIDProcessor._encode_base32(random_bytes, 16)
        
        return timestamp_part + random_part
    
    @staticmethod
    def _encode_base32(value: int, length: int) -> str:
        """Encode integer to Crockford's Base32 with specified length."""
        alphabet = UUIDULIDProcessor.ULID_ALPHABET
        result = ""
        
        for _ in range(length):
            result = alphabet[value % 32] + result
            value //= 32
        
        return result
    
    @staticmethod
    def _decode_base32(encoded: str) -> int:
        """Decode Crockford's Base32 string to integer."""
        alphabet = UUIDULIDProcessor.ULID_ALPHABET
        result = 0
        
        for char in encoded.upper():
            if char in alphabet:
                result = result * 32 + alphabet.index(char)
            else:
                raise ValueError(f"Invalid character in ULID: {char}")
        
        return result
    
    @staticmethod
    def decode_uuid(uuid_str: str) -> Dict[str, Any]:
        """Decode a UUID string and extract its components."""
        try:
            # Clean and validate UUID string
            uuid_str = uuid_str.strip().replace('-', '')
            if len(uuid_str) != 32:
                raise ValueError("Invalid UUID length")
            
            # Parse UUID
            uuid_obj = uuid.UUID(uuid_str)
            
            # Extract components
            result = {
                "standard_format": str(uuid_obj),
                "raw_contents": uuid_str.upper(),
                "version": uuid_obj.version,
                "variant": UUIDULIDProcessor._get_variant_name(uuid_obj.variant),
            }
            
            # Version-specific decoding
            if uuid_obj.version == 1:
                # Time-based UUID
                timestamp = uuid_obj.time
                # UUID timestamp is 100-nanosecond intervals since 1582-10-15
                unix_timestamp = (timestamp - 0x01b21dd213814000) / 10000000
                result["contents_time"] = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).isoformat()
                result["contents_clock_id"] = f"{uuid_obj.clock_seq:04x}"
                result["contents_node"] = f"{uuid_obj.node:012x}"
            else:
                result["contents_time"] = "N/A (not time-based)"
                result["contents_clock_id"] = "N/A"
                result["contents_node"] = "N/A"
            
            return result
            
        except Exception as e:
            logger.error(f"Error decoding UUID: {e}")
            return {
                "standard_format": "Invalid UUID",
                "raw_contents": "Invalid UUID",
                "version": "Unknown",
                "variant": "Unknown",
                "contents_time": "Invalid",
                "contents_clock_id": "Invalid",
                "contents_node": "Invalid",
            }
    
    @staticmethod
    def decode_ulid(ulid_str: str) -> Dict[str, Any]:
        """Decode a ULID string and extract its components."""
        try:
            ulid_str = ulid_str.strip().upper()
            if len(ulid_str) != 26:
                raise ValueError("Invalid ULID length")
            
            # Extract timestamp part (first 10 characters)
            timestamp_part = ulid_str[:10]
            random_part = ulid_str[10:]
            
            # Decode timestamp
            timestamp_ms = UUIDULIDProcessor._decode_base32(timestamp_part)
            timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            
            # Decode random part
            random_value = UUIDULIDProcessor._decode_base32(random_part)
            
            return {
                "standard_format": ulid_str,
                "raw_contents": ulid_str,
                "version": "ULID",
                "variant": "ULID",
                "contents_time": timestamp_dt.isoformat(),
                "contents_clock_id": "N/A (ULID)",
                "contents_node": f"{random_value:020x}",
            }
            
        except Exception as e:
            logger.error(f"Error decoding ULID: {e}")
            return {
                "standard_format": "Invalid ULID",
                "raw_contents": "Invalid ULID",
                "version": "Unknown",
                "variant": "Unknown",
                "contents_time": "Invalid",
                "contents_clock_id": "Invalid",
                "contents_node": "Invalid",
            }
    
    @staticmethod
    def _get_variant_name(variant: int) -> str:
        """Get human-readable variant name."""
        if variant == uuid.RFC_4122:
            return "RFC 4122"
        elif variant == uuid.RESERVED_NCS:
            return "Reserved NCS"
        elif variant == uuid.RESERVED_MICROSOFT:
            return "Reserved Microsoft"
        elif variant == uuid.RESERVED_FUTURE:
            return "Reserved Future"
        else:
            return f"Unknown ({variant})"
    
    @staticmethod
    def detect_and_decode(input_str: str) -> Dict[str, Any]:
        """Auto-detect whether input is UUID or ULID and decode accordingly."""
        input_str = input_str.strip()
        
        # Check if it looks like a ULID (26 characters, base32)
        if len(input_str) == 26 and all(c.upper() in UUIDULIDProcessor.ULID_ALPHABET for c in input_str):
            return UUIDULIDProcessor.decode_ulid(input_str)
        
        # Otherwise, try to decode as UUID
        return UUIDULIDProcessor.decode_uuid(input_str)


def create_field_row(name: str, style_func) -> tuple[QWidget, QLineEdit, QPushButton]:
    """Helper function to create a labeled field row for the decoder.
    
    Returns:
        tuple: (widget, line_edit, copy_button) for external access
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)

    label = QLabel(name)
    layout.addWidget(label)

    field_layout = QHBoxLayout()
    field_layout.setSpacing(5)

    line_edit = QLineEdit()
    line_edit.setReadOnly(True)
    field_layout.addWidget(line_edit)

    copy_button = QPushButton()
    copy_button.setObjectName("iconButton")
    # Image description: A simple black icon representing two overlapping pages, for copying.
    copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon))
    copy_button.setFixedSize(30, 30)
    field_layout.addWidget(copy_button)

    layout.addLayout(field_layout)
    return widget, line_edit, copy_button


def create_uuid_ulid_tool_widget(style_func) -> QWidget:
    """
    Creates the UUID/ULID Generate/Decode widget.

    Args:
        style_func: Function to get QStyle for standard icons.

    Returns:
        QWidget: The complete UUID/ULID tool widget.
    """
    logger.info("Creating UUID/ULID Generate/Decode widget")
    main_widget = QWidget()
    main_widget.setStyleSheet("""
        QWidget {
            background-color: #ffffff;
            color: #333333;
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QLabel {
            font-size: 13px;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            padding: 5px 12px;
            border-radius: 3px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #e8e8e8;
        }
        QPushButton#iconButton {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 2px;
        }
        QPushButton#iconButton:hover {
            background-color: #f0f0f0;
        }
        QLineEdit, QComboBox, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 13px;
        }
        QComboBox {
            font-family: "Segoe UI", Arial, sans-serif;
        }
        QTextEdit {
            color: #888888;
        }
        QCheckBox {
            font-size: 13px;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
        }
    """)

    main_layout = QHBoxLayout(main_widget)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(12)

    # --- LEFT PANE (DECODER) ---
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(8)

    # Top controls
    input_controls_layout = QHBoxLayout()
    input_controls_layout.setSpacing(6)

    clipboard_button = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button_left = QPushButton("Clear")
    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A flat, gray gear icon for settings.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
    settings_button.setFixedSize(32, 32)

    input_controls_layout.addWidget(QPushButton("Input:"))  # This is styled as a button in the screenshot
    input_controls_layout.addWidget(clipboard_button)
    input_controls_layout.addWidget(sample_button)
    input_controls_layout.addWidget(clear_button_left)
    input_controls_layout.addSpacing(4)
    input_controls_layout.addWidget(settings_button)
    input_controls_layout.addStretch()

    # UUID Input field
    uuid_input = QLineEdit("00000000-0000-0000-0000-000000000000")

    left_layout.addLayout(input_controls_layout)
    left_layout.addWidget(uuid_input)
    left_layout.addSpacing(10)

    # Decoded Fields
    field_names = [
        "Standard String Format",
        "Raw Contents",
        "Version",
        "Variant",
        "Contents - Time",
        "Contents - Clock ID",
        "Contents - Node",
    ]
    
    # Store field references for updating
    field_widgets = {}
    field_line_edits = {}
    field_copy_buttons = {}
    
    for name in field_names:
        widget, line_edit, copy_button = create_field_row(name, style_func)
        left_layout.addWidget(widget)
        field_widgets[name] = widget
        field_line_edits[name] = line_edit
        field_copy_buttons[name] = copy_button
    
    # Initialize processor
    processor = UUIDULIDProcessor()
    
    def validate_input(input_text: str) -> bool:
        """Validate if input is a valid UUID or ULID."""
        if not input_text:
            return True  # Empty input is valid (neutral state)
        
        input_text = input_text.strip()
        
        # Check ULID format (26 characters, base32)
        if len(input_text) == 26:
            return all(c.upper() in processor.ULID_ALPHABET for c in input_text)
        
        # Check UUID format
        try:
            # Remove hyphens and check length
            clean_uuid = input_text.replace('-', '')
            if len(clean_uuid) != 32:
                return False
            # Try to parse as UUID
            uuid.UUID(clean_uuid)
            return True
        except (ValueError, AttributeError):
            return False
    
    def update_decoded_fields():
        """Update all decoded fields based on current input."""
        input_text = uuid_input.text().strip()
        
        # Validate input and apply styling
        is_valid = validate_input(input_text)
        if not input_text:
            # Empty input - neutral styling
            uuid_input.setStyleSheet("")
        elif is_valid:
            # Valid input - green border
            uuid_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #4CAF50;
                    background-color: #f8fff8;
                }
            """)
        else:
            # Invalid input - red border
            uuid_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #f44336;
                    background-color: #fff8f8;
                }
            """)
        
        if not input_text:
            # Clear all fields
            for line_edit in field_line_edits.values():
                line_edit.clear()
            return
        
        if not is_valid:
            # Show error in fields
            for line_edit in field_line_edits.values():
                line_edit.setText("Invalid input")
            return
        
        # Decode the input
        decoded = processor.detect_and_decode(input_text)
        
        # Update fields
        field_line_edits["Standard String Format"].setText(decoded.get("standard_format", ""))
        field_line_edits["Raw Contents"].setText(decoded.get("raw_contents", ""))
        field_line_edits["Version"].setText(str(decoded.get("version", "")))
        field_line_edits["Variant"].setText(decoded.get("variant", ""))
        field_line_edits["Contents - Time"].setText(decoded.get("contents_time", ""))
        field_line_edits["Contents - Clock ID"].setText(decoded.get("contents_clock_id", ""))
        field_line_edits["Contents - Node"].setText(decoded.get("contents_node", ""))
    
    def on_clipboard_clicked():
        """Load UUID/ULID from clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            uuid_input.setText(text)
            update_decoded_fields()
    
    def on_sample_clicked():
        """Load a sample UUID for demonstration."""
        sample_uuid = processor.generate_uuid_v4()
        uuid_input.setText(sample_uuid)
        update_decoded_fields()
    
    def on_clear_clicked():
        """Clear the input and all decoded fields."""
        uuid_input.clear()
        update_decoded_fields()
    
    # Connect left pane buttons
    clipboard_button.clicked.connect(on_clipboard_clicked)
    sample_button.clicked.connect(on_sample_clicked)
    clear_button_left.clicked.connect(on_clear_clicked)
    
    # Connect input field to auto-update
    uuid_input.textChanged.connect(update_decoded_fields)
    
    # Connect copy buttons for each field
    for name, copy_button in field_copy_buttons.items():
        line_edit = field_line_edits[name]
        copy_button.clicked.connect(lambda checked, le=line_edit: QApplication.clipboard().setText(le.text()))
    
    # Initial decode
    update_decoded_fields()

    left_layout.addStretch()

    # --- RIGHT PANE (GENERATOR) ---
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(8)

    # Generator controls
    controls_layout = QHBoxLayout()
    controls_layout.setSpacing(6)

    generate_button = QPushButton("Generate")
    copy_button = QPushButton("Copy")
    clear_button_right = QPushButton("Clear")

    uuid_version_combo = QComboBox()
    uuid_version_combo.addItems(["UUID v1", "UUID v4", "ULID"])
    uuid_version_combo.setFixedWidth(100)

    count_label = QLabel("x")
    count_input = QLineEdit("100")
    count_input.setFixedWidth(50)
    count_input.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    lowercased_checkbox = QCheckBox("lowercased")

    controls_layout.addWidget(generate_button)
    controls_layout.addWidget(copy_button)
    controls_layout.addWidget(clear_button_right)
    controls_layout.addStretch()
    controls_layout.addWidget(uuid_version_combo)
    controls_layout.addWidget(count_label)
    controls_layout.addWidget(count_input)
    controls_layout.addWidget(lowercased_checkbox)

    generate_label = QLabel("Generate new IDs")

    output_text_edit = QTextEdit()
    output_text_edit.setPlaceholderText("- Right click > Save to file...")
    output_text_edit.setReadOnly(True)

    right_layout.addWidget(generate_label)
    right_layout.addLayout(controls_layout)
    right_layout.addWidget(output_text_edit)
    
    # Right pane functionality
    def on_generate_clicked():
        """Generate UUIDs/ULIDs based on selected type and count."""
        try:
            # Get generation parameters
            selected_type = uuid_version_combo.currentText()
            count = int(count_input.text() or "1")
            lowercase = lowercased_checkbox.isChecked()
            
            # Limit count to reasonable number
            count = min(count, 10000)
            
            generated_ids = []
            
            # Generate based on selected type
            for _ in range(count):
                if selected_type == "UUID v1":
                    new_id = processor.generate_uuid_v1()
                elif selected_type == "UUID v4":
                    new_id = processor.generate_uuid_v4()
                elif selected_type == "ULID":
                    new_id = processor.generate_ulid()
                else:
                    new_id = processor.generate_uuid_v4()  # Default
                
                if lowercase:
                    new_id = new_id.lower()
                
                generated_ids.append(new_id)
            
            # Display generated IDs
            output_text_edit.setPlainText("\n".join(generated_ids))
            
        except ValueError:
            # Invalid count input
            output_text_edit.setPlainText("Error: Invalid count value")
        except Exception as e:
            logger.error(f"Error generating IDs: {e}")
            output_text_edit.setPlainText(f"Error: {str(e)}")
    
    def on_copy_generated_clicked():
        """Copy generated IDs to clipboard."""
        text = output_text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
    
    def on_clear_generated_clicked():
        """Clear the generated output."""
        output_text_edit.clear()
    
    # Connect right pane buttons
    generate_button.clicked.connect(on_generate_clicked)
    copy_button.clicked.connect(on_copy_generated_clicked)
    clear_button_right.clicked.connect(on_clear_generated_clicked)
    
    # Validate count input
    def validate_count_input():
        """Validate count input and apply styling."""
        text = count_input.text()
        try:
            if text:
                count = int(text)
                if 1 <= count <= 10000:
                    count_input.setStyleSheet("")
                else:
                    count_input.setStyleSheet("border: 1px solid #ff9800;")
            else:
                count_input.setStyleSheet("")
        except ValueError:
            count_input.setStyleSheet("border: 1px solid #f44336;")
    
    count_input.textChanged.connect(validate_count_input)

    # Add panes to main layout
    main_layout.addWidget(left_pane, 5)  # Give more space to the left pane
    main_layout.addWidget(right_pane, 4)

    logger.info("UUID/ULID widget creation completed")
    return main_widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("UUID/ULID Generate/Decode Tool")
    main_window.setGeometry(100, 100, 1000, 600)

    uuid_tool_widget = create_uuid_ulid_tool_widget(app.style)
    main_window.setCentralWidget(uuid_tool_widget)

    main_window.show()
    sys.exit(app.exec())
