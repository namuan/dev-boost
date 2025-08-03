import base64
import unittest
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from devdriver.tools.base64_string_encodec import create_base64_string_encodec_widget


class TestBase64StringEncodec(unittest.TestCase):
    """Test cases for Base64 String Encode/Decode functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures."""
        self.widget = create_base64_string_encodec_widget(self.app.style)
        # Find the input and output text edits
        self.input_text_edit = None
        self.output_text_edit = None
        self.encode_radio = None
        self.decode_radio = None
        
        # Find widgets by traversing the widget tree
        for child in self.widget.findChildren(type(self.widget)):
            if hasattr(child, 'toPlainText') and hasattr(child, 'setPlainText'):
                if not hasattr(child, 'setReadOnly') or not child.isReadOnly():
                    self.input_text_edit = child
                else:
                    self.output_text_edit = child
        
        # Find radio buttons
        from PyQt6.QtWidgets import QRadioButton
        radio_buttons = self.widget.findChildren(QRadioButton)
        for radio in radio_buttons:
            if radio.text() == "Encode":
                self.encode_radio = radio
            elif radio.text() == "Decode":
                self.decode_radio = radio

    def test_widget_creation(self):
        """Test that the widget is created successfully."""
        self.assertIsNotNone(self.widget)
        self.assertIsNotNone(self.input_text_edit)
        self.assertIsNotNone(self.output_text_edit)
        self.assertIsNotNone(self.encode_radio)
        self.assertIsNotNone(self.decode_radio)

    def test_base64_encoding(self):
        """Test base64 encoding functionality."""
        # Set encode mode
        self.encode_radio.setChecked(True)
        
        # Test encoding
        test_text = "Hello, World!"
        expected_encoded = base64.b64encode(test_text.encode('utf-8')).decode('ascii')
        
        self.input_text_edit.setPlainText(test_text)
        # Process events to trigger the encoding
        self.app.processEvents()
        
        output_text = self.output_text_edit.toPlainText()
        self.assertEqual(output_text, expected_encoded)

    def test_base64_decoding(self):
        """Test base64 decoding functionality."""
        # Set decode mode (should be default)
        self.decode_radio.setChecked(True)
        
        # Test decoding
        test_text = "Hello, World!"
        encoded_text = base64.b64encode(test_text.encode('utf-8')).decode('ascii')
        
        self.input_text_edit.setPlainText(encoded_text)
        # Process events to trigger the decoding
        self.app.processEvents()
        
        output_text = self.output_text_edit.toPlainText()
        self.assertEqual(output_text, test_text)

    def test_empty_input(self):
        """Test behavior with empty input."""
        self.input_text_edit.setPlainText("")
        self.app.processEvents()
        
        output_text = self.output_text_edit.toPlainText()
        self.assertEqual(output_text, "")

    def test_invalid_base64_decoding(self):
        """Test error handling for invalid base64 input."""
        # Set decode mode
        self.decode_radio.setChecked(True)
        
        # Test with invalid base64
        invalid_base64 = "This is not valid base64!"
        self.input_text_edit.setPlainText(invalid_base64)
        self.app.processEvents()
        
        output_text = self.output_text_edit.toPlainText()
        self.assertTrue(output_text.startswith("Error:"))

    def test_mode_switching(self):
        """Test switching between encode and decode modes."""
        test_text = "Hello, World!"
        
        # Start with encoding
        self.encode_radio.setChecked(True)
        self.input_text_edit.setPlainText(test_text)
        self.app.processEvents()
        
        encoded_output = self.output_text_edit.toPlainText()
        expected_encoded = base64.b64encode(test_text.encode('utf-8')).decode('ascii')
        self.assertEqual(encoded_output, expected_encoded)
        
        # Switch to decoding with the same input
        self.decode_radio.setChecked(True)
        self.app.processEvents()
        
        # The output should show an error since the input is not valid base64
        decoded_output = self.output_text_edit.toPlainText()
        self.assertTrue(decoded_output.startswith("Error:"))

    def test_unicode_handling(self):
        """Test encoding and decoding of unicode characters."""
        # Test with unicode characters
        unicode_text = "Hello, 世界! 🌍"
        
        # Encode
        self.encode_radio.setChecked(True)
        self.input_text_edit.setPlainText(unicode_text)
        self.app.processEvents()
        
        encoded_output = self.output_text_edit.toPlainText()
        expected_encoded = base64.b64encode(unicode_text.encode('utf-8')).decode('ascii')
        self.assertEqual(encoded_output, expected_encoded)
        
        # Decode back
        self.decode_radio.setChecked(True)
        self.input_text_edit.setPlainText(encoded_output)
        self.app.processEvents()
        
        decoded_output = self.output_text_edit.toPlainText()
        self.assertEqual(decoded_output, unicode_text)


if __name__ == '__main__':
    unittest.main()