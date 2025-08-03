import json
import pytest
import sys
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add the parent directory to the path to import the module
sys.path.insert(0, '/Users/nnn/workspace/devdriver')

from devdriver.tools.json_format_validate import JSONValidator, create_json_formatter_widget


class TestJSONValidator:
    """Test cases for JSONValidator class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.validator = JSONValidator()
    
    def test_validate_and_format_json_valid_input(self):
        """Test validation and formatting with valid JSON input."""
        input_json = '{"name": "John", "age": 30}'
        is_valid, formatted_json, error_message = self.validator.validate_and_format_json(input_json, 2)
        
        assert is_valid is True
        assert error_message == ""
        assert "name" in formatted_json
        assert "age" in formatted_json
        # Check if it's properly formatted with indentation
        assert "\n" in formatted_json
    
    def test_validate_and_format_json_invalid_input(self):
        """Test validation with invalid JSON input."""
        input_json = '{"name": "John", "age":}'
        is_valid, formatted_json, error_message = self.validator.validate_and_format_json(input_json, 2)
        
        assert is_valid is False
        assert formatted_json == ""
        assert "JSON Decode Error" in error_message
    
    def test_validate_and_format_json_empty_input(self):
        """Test validation with empty input."""
        input_json = ""
        is_valid, formatted_json, error_message = self.validator.validate_and_format_json(input_json, 2)
        
        assert is_valid is False
        assert formatted_json == ""
        assert error_message == "Input is empty"
    
    def test_validate_and_format_json_whitespace_input(self):
        """Test validation with whitespace-only input."""
        input_json = "   \n\t   "
        is_valid, formatted_json, error_message = self.validator.validate_and_format_json(input_json, 2)
        
        assert is_valid is False
        assert formatted_json == ""
        assert error_message == "Input is empty"
    
    def test_validate_and_format_json_different_indentations(self):
        """Test formatting with different indentation options."""
        input_json = '{"name": "John", "age": 30}'
        
        # Test 2 spaces
        is_valid, formatted_2, _ = self.validator.validate_and_format_json(input_json, 2)
        assert is_valid is True
        assert "  " in formatted_2  # 2 spaces
        
        # Test 4 spaces
        is_valid, formatted_4, _ = self.validator.validate_and_format_json(input_json, 4)
        assert is_valid is True
        assert "    " in formatted_4  # 4 spaces
        
        # Test tabs
        is_valid, formatted_tabs, _ = self.validator.validate_and_format_json(input_json, 0)
        assert is_valid is True
        assert "\t" in formatted_tabs  # tabs
    
    def test_minify_json_valid_input(self):
        """Test JSON minification with valid input."""
        input_json = '{\n  "name": "John",\n  "age": 30\n}'
        is_valid, minified_json, error_message = self.validator.minify_json(input_json)
        
        assert is_valid is True
        assert error_message == ""
        assert "\n" not in minified_json
        assert " " not in minified_json.replace('"name"', '').replace('"John"', '').replace('"age"', '')
    
    def test_minify_json_invalid_input(self):
        """Test JSON minification with invalid input."""
        input_json = '{"name": "John", "age":}'
        is_valid, minified_json, error_message = self.validator.minify_json(input_json)
        
        assert is_valid is False
        assert minified_json == ""
        assert "JSON Decode Error" in error_message
    
    def test_minify_json_empty_input(self):
        """Test JSON minification with empty input."""
        input_json = ""
        is_valid, minified_json, error_message = self.validator.minify_json(input_json)
        
        assert is_valid is False
        assert minified_json == ""
        assert error_message == "Input is empty"
    
    def test_get_sample_json(self):
        """Test sample JSON generation."""
        sample_json = self.validator.get_sample_json()
        
        assert sample_json is not None
        assert len(sample_json) > 0
        
        # Verify it's valid JSON
        try:
            parsed = json.loads(sample_json)
            assert "name" in parsed
            assert "age" in parsed
            assert "hobbies" in parsed
            assert isinstance(parsed["hobbies"], list)
        except json.JSONDecodeError:
            pytest.fail("Sample JSON is not valid JSON")
    
    def test_complex_json_validation(self):
        """Test validation with complex nested JSON."""
        complex_json = '''
        {
            "users": [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "preferences": {
                        "theme": "dark",
                        "notifications": true,
                        "languages": ["en", "es"]
                    }
                },
                {
                    "id": 2,
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "preferences": {
                        "theme": "light",
                        "notifications": false,
                        "languages": ["en", "fr", "de"]
                    }
                }
            ],
            "metadata": {
                "total": 2,
                "page": 1,
                "timestamp": "2023-12-01T10:00:00Z"
            }
        }
        '''
        
        is_valid, formatted_json, error_message = self.validator.validate_and_format_json(complex_json, 2)
        
        assert is_valid is True
        assert error_message == ""
        assert "users" in formatted_json
        assert "metadata" in formatted_json
        
        # Verify the formatted JSON is still valid
        try:
            json.loads(formatted_json)
        except json.JSONDecodeError:
            pytest.fail("Formatted JSON is not valid JSON")
    
    def test_unicode_json_validation(self):
        """Test validation with Unicode characters."""
        unicode_json = '{"name": "José", "city": "São Paulo", "emoji": "😀"}'
        is_valid, formatted_json, error_message = self.validator.validate_and_format_json(unicode_json, 2)
        
        assert is_valid is True
        assert error_message == ""
        assert "José" in formatted_json
        assert "São Paulo" in formatted_json
        assert "😀" in formatted_json
    
    def test_json_path_query_valid(self):
        """Test JSON Path querying with valid input."""
        test_json = '''
        {
            "store": {
                "book": [
                    {"title": "Book 1", "author": "Author 1", "price": 10.99},
                    {"title": "Book 2", "author": "Author 2", "price": 15.99}
                ]
            }
        }
        '''
        
        # Test querying book titles
        is_valid, result, error_message = self.validator.query_json_path(test_json, "$.store.book[*].title")
        
        if hasattr(self.validator, 'query_json_path'):
            # Only test if JSONPath is available
            try:
                import jsonpath_ng
                assert is_valid is True
                assert "Book 1" in result
                assert "Book 2" in result
                assert error_message == ""
            except ImportError:
                # JSONPath not available, should return error
                assert is_valid is False
                assert "JSONPath library not available" in error_message
    
    def test_json_path_query_no_matches(self):
        """Test JSON Path querying with no matches."""
        test_json = '{"name": "John", "age": 30}'
        
        if hasattr(self.validator, 'query_json_path'):
            try:
                import jsonpath_ng
                is_valid, result, error_message = self.validator.query_json_path(test_json, "$.nonexistent")
                assert is_valid is True
                assert result == "[]"
                assert "No matches found" in error_message
            except ImportError:
                # JSONPath not available, skip test
                pass
    
    def test_json_path_query_invalid_json(self):
        """Test JSON Path querying with invalid JSON."""
        invalid_json = '{"name": "John", "age":}'
        
        if hasattr(self.validator, 'query_json_path'):
            is_valid, result, error_message = self.validator.query_json_path(invalid_json, "$.name")
            assert is_valid is False
            assert result == ""
            assert "JSON Decode Error" in error_message
    
    def test_json_path_query_empty_inputs(self):
        """Test JSON Path querying with empty inputs."""
        if hasattr(self.validator, 'query_json_path'):
            # Empty JSON
            is_valid, result, error_message = self.validator.query_json_path("", "$.name")
            assert is_valid is False
            assert error_message == "Input is empty"
            
            # Empty JSON Path
            is_valid, result, error_message = self.validator.query_json_path('{"name": "John"}', "")
            assert is_valid is False
            assert error_message == "JSON Path is empty"


@pytest.fixture
def qapp():
    """Create QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it might be used by other tests


class TestJSONFormatterWidget:
    """Test cases for the JSON formatter widget UI."""
    
    def test_create_json_formatter_widget(self, qapp):
        """Test widget creation."""
        widget = create_json_formatter_widget(qapp.style)
        
        assert widget is not None
        assert widget.isVisible() is False  # Widget is created but not shown
    
    @patch('devdriver.tools.json_format_validate.QMessageBox')
    def test_widget_functionality_integration(self, mock_messagebox, qapp):
        """Test basic widget functionality integration."""
        widget = create_json_formatter_widget(qapp.style)
        
        # Find input and output text areas
        input_text_edit = None
        output_text_edit = None
        run_button = None
        
        # Search for text edit widgets
        for child in widget.findChildren(object):
            if hasattr(child, 'toPlainText'):
                if input_text_edit is None:
                    input_text_edit = child
                else:
                    output_text_edit = child
            elif hasattr(child, 'clicked') and hasattr(child, 'objectName'):
                if child.objectName() == 'iconButton':
                    run_button = child
                    break
        
        assert input_text_edit is not None
        assert output_text_edit is not None
        
        # Test with valid JSON
        test_json = '{"test": "value"}'
        input_text_edit.setPlainText(test_json)
        
        # The widget should be functional (this is more of a smoke test)
        assert input_text_edit.toPlainText() == test_json


if __name__ == '__main__':
    pytest.main([__file__])