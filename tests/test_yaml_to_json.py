import contextlib
import json

import pytest

from devboost.tools.yaml_to_json import YAMLToJSONConverter


class TestYAMLToJSONConverter:
    """Test cases for YAMLToJSONConverter class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.converter = YAMLToJSONConverter()

    def test_init(self):
        """Test converter initialization."""
        assert self.converter.last_error is None

    def test_convert_simple_yaml_to_json(self):
        """Test converting simple YAML to JSON."""
        yaml_input = "name: John\nage: 30"
        expected = {"name": "John", "age": 30}

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result == expected
        assert self.converter.last_error is None

    def test_convert_complex_yaml_to_json(self):
        """Test converting complex YAML with nested structures."""
        yaml_input = """person:
  name: John Doe
  age: 30
  skills:
    - Python
    - JavaScript
  address:
    street: 123 Main St
    city: Anytown"""

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result["person"]["name"] == "John Doe"
        assert parsed_result["person"]["age"] == 30
        assert "Python" in parsed_result["person"]["skills"]
        assert parsed_result["person"]["address"]["city"] == "Anytown"

    def test_convert_yaml_with_different_indentation(self):
        """Test JSON output with different indentation levels."""
        yaml_input = "name: John\nage: 30"

        # Test 2 spaces indentation
        result_2 = self.converter.convert_yaml_to_json(yaml_input, indent=2)
        assert '  "name"' in result_2

        # Test 4 spaces indentation
        result_4 = self.converter.convert_yaml_to_json(yaml_input, indent=4)
        assert '    "name"' in result_4

    def test_convert_empty_yaml(self):
        """Test converting empty YAML string."""
        result = self.converter.convert_yaml_to_json("")
        assert result == ""

        result = self.converter.convert_yaml_to_json("   ")
        assert result == ""

    def test_convert_yaml_with_null_values(self):
        """Test converting YAML with null values."""
        yaml_input = "name: John\nage: null\nempty: ~"

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result["name"] == "John"
        assert parsed_result["age"] is None
        assert parsed_result["empty"] is None

    def test_convert_yaml_with_boolean_values(self):
        """Test converting YAML with boolean values."""
        yaml_input = "active: true\ninactive: false\nyes_value: yes\nno_value: no"

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result["active"] is True
        assert parsed_result["inactive"] is False
        assert parsed_result["yes_value"] is True
        assert parsed_result["no_value"] is False

    def test_convert_yaml_with_numbers(self):
        """Test converting YAML with different number types."""
        yaml_input = "integer: 42\nfloat: 3.14\nscientific: 1.23e-4\noctal: 0o755"

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result["integer"] == 42
        assert parsed_result["float"] == 3.14
        assert parsed_result["scientific"] == 1.23e-4
        assert parsed_result["octal"] == "0o755"  # YAML treats this as string

    def test_convert_yaml_with_lists(self):
        """Test converting YAML with lists."""
        yaml_input = """fruits:
  - apple
  - banana
  - orange
numbers:
  - 1
  - 2
  - 3"""

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result["fruits"] == ["apple", "banana", "orange"]
        assert parsed_result["numbers"] == [1, 2, 3]

    def test_convert_yaml_with_unicode(self):
        """Test converting YAML with Unicode characters."""
        yaml_input = "name: José\ncity: São Paulo\nemoji: 🚀"

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result["name"] == "José"
        assert parsed_result["city"] == "São Paulo"
        assert parsed_result["emoji"] == "🚀"

    def test_convert_invalid_yaml(self):
        """Test converting invalid YAML raises ValueError."""
        invalid_yaml = "name: John\n  age: 30\n invalid_indentation"

        with pytest.raises(ValueError) as exc_info:
            self.converter.convert_yaml_to_json(invalid_yaml)

        assert "YAML parsing error" in str(exc_info.value)
        assert self.converter.last_error is not None
        assert "YAML parsing error" in self.converter.last_error

    def test_validate_yaml_valid_input(self):
        """Test validating valid YAML input."""
        valid_yaml = "name: John\nage: 30"

        assert self.converter.validate_yaml(valid_yaml) is True
        assert self.converter.last_error is None

    def test_validate_yaml_invalid_input(self):
        """Test validating invalid YAML input."""
        invalid_yaml = "name: John\n  age: 30\n invalid_indentation"

        assert self.converter.validate_yaml(invalid_yaml) is False
        assert self.converter.last_error is not None
        assert "YAML validation error" in self.converter.last_error

    def test_validate_yaml_empty_input(self):
        """Test validating empty YAML input."""
        assert self.converter.validate_yaml("") is True
        assert self.converter.validate_yaml("   ") is True
        assert self.converter.last_error is None

    def test_validate_yaml_complex_valid(self):
        """Test validating complex valid YAML."""
        complex_yaml = """database:
  host: localhost
  port: 5432
  credentials:
    username: admin
    password: secret
  pools:
    - name: read_pool
      size: 10
    - name: write_pool
      size: 5"""

        assert self.converter.validate_yaml(complex_yaml) is True
        assert self.converter.last_error is None

    def test_get_last_error_no_error(self):
        """Test getting last error when no error occurred."""
        self.converter.convert_yaml_to_json("name: John")
        assert self.converter.get_last_error() is None

    def test_get_last_error_after_error(self):
        """Test getting last error after an error occurred."""
        with contextlib.suppress(ValueError):
            self.converter.convert_yaml_to_json("invalid: yaml: content:")

        error = self.converter.get_last_error()
        assert error is not None
        assert "YAML parsing error" in error

    def test_get_sample_yaml(self):
        """Test getting sample YAML data."""
        sample = self.converter.get_sample_yaml()

        assert isinstance(sample, str)
        assert len(sample) > 0
        assert "name:" in sample
        assert "John Doe" in sample
        assert "skills:" in sample

        # Verify the sample is valid YAML
        assert self.converter.validate_yaml(sample) is True

    def test_sample_yaml_converts_successfully(self):
        """Test that the sample YAML converts to JSON successfully."""
        sample = self.converter.get_sample_yaml()

        result = self.converter.convert_yaml_to_json(sample)
        parsed_result = json.loads(result)

        assert parsed_result["name"] == "John Doe"
        assert parsed_result["age"] == 30
        assert "Python" in parsed_result["skills"]
        assert parsed_result["address"]["city"] == "Anytown"
        assert parsed_result["active"] is True
        assert parsed_result["salary"] == 75000.50

    def test_error_handling_preserves_state(self):
        """Test that error handling preserves converter state."""
        # First, successful conversion
        self.converter.convert_yaml_to_json("name: John")
        assert self.converter.last_error is None

        # Then, failed conversion
        with contextlib.suppress(ValueError):
            self.converter.convert_yaml_to_json("invalid: yaml: content:")

        assert self.converter.last_error is not None

        # Another successful conversion should clear the error
        self.converter.convert_yaml_to_json("name: Jane")
        assert self.converter.last_error is None

    def test_convert_yaml_with_multiline_strings(self):
        """Test converting YAML with multiline strings."""
        yaml_input = """description: |
  This is a multiline
  string that spans
  multiple lines.
summary: >
  This is a folded
  string that will be
  on one line."""

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert "\n" in parsed_result["description"]
        assert "This is a multiline" in parsed_result["description"]
        assert parsed_result["summary"].count("\n") == 0  # Folded string should be on one line

    def test_convert_yaml_with_comments(self):
        """Test converting YAML with comments (comments should be ignored)."""
        yaml_input = """# This is a comment
name: John  # Inline comment
age: 30
# Another comment
email: john@example.com"""

        result = self.converter.convert_yaml_to_json(yaml_input)
        parsed_result = json.loads(result)

        assert parsed_result["name"] == "John"
        assert parsed_result["age"] == 30
        assert parsed_result["email"] == "john@example.com"
        # Comments should not appear in JSON output
        assert "#" not in result
