import sys

# Add the parent directory to the path to import the module
sys.path.insert(0, "/Users/nnn/workspace/dev-boost")

from devboost.tools.string_case_converter import StringCaseConverter


class TestStringCaseConverter:
    """Test cases for StringCaseConverter class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.converter = StringCaseConverter()

    def test_to_camel_case(self):
        """Test camelCase conversion."""
        # Basic conversion
        assert self.converter.to_camel_case("hello world") == "helloWorld"
        assert self.converter.to_camel_case("hello_world") == "helloWorld"
        assert self.converter.to_camel_case("hello-world") == "helloWorld"
        assert self.converter.to_camel_case("hello.world") == "helloWorld"

        # Multiple words
        assert self.converter.to_camel_case("hello world example text") == "helloWorldExampleText"
        assert self.converter.to_camel_case("hello_world_example_text") == "helloWorldExampleText"

        # Edge cases
        assert self.converter.to_camel_case("") == ""
        assert self.converter.to_camel_case("   ") == ""
        assert self.converter.to_camel_case("hello") == "hello"
        assert self.converter.to_camel_case("HELLO") == "hello"

    def test_to_pascal_case(self):
        """Test PascalCase conversion."""
        # Basic conversion
        assert self.converter.to_pascal_case("hello world") == "HelloWorld"
        assert self.converter.to_pascal_case("hello_world") == "HelloWorld"
        assert self.converter.to_pascal_case("hello-world") == "HelloWorld"
        assert self.converter.to_pascal_case("hello.world") == "HelloWorld"

        # Multiple words
        assert self.converter.to_pascal_case("hello world example text") == "HelloWorldExampleText"
        assert self.converter.to_pascal_case("hello_world_example_text") == "HelloWorldExampleText"

        # Edge cases
        assert self.converter.to_pascal_case("") == ""
        assert self.converter.to_pascal_case("   ") == ""
        assert self.converter.to_pascal_case("hello") == "Hello"
        assert self.converter.to_pascal_case("HELLO") == "Hello"

    def test_to_snake_case(self):
        """Test snake_case conversion."""
        # Basic conversion
        assert self.converter.to_snake_case("hello world") == "hello_world"
        assert self.converter.to_snake_case("helloWorld") == "hello_world"
        assert self.converter.to_snake_case("HelloWorld") == "hello_world"
        assert self.converter.to_snake_case("hello-world") == "hello_world"
        assert self.converter.to_snake_case("hello.world") == "hello_world"

        # Multiple words
        assert self.converter.to_snake_case("hello world example text") == "hello_world_example_text"
        assert self.converter.to_snake_case("helloWorldExampleText") == "hello_world_example_text"

        # Edge cases
        assert self.converter.to_snake_case("") == ""
        assert self.converter.to_snake_case("   ") == ""
        assert self.converter.to_snake_case("hello") == "hello"
        assert self.converter.to_snake_case("HELLO") == "hello"

    def test_to_kebab_case(self):
        """Test kebab-case conversion."""
        # Basic conversion
        assert self.converter.to_kebab_case("hello world") == "hello-world"
        assert self.converter.to_kebab_case("helloWorld") == "hello-world"
        assert self.converter.to_kebab_case("HelloWorld") == "hello-world"
        assert self.converter.to_kebab_case("hello_world") == "hello-world"
        assert self.converter.to_kebab_case("hello.world") == "hello-world"

        # Multiple words
        assert self.converter.to_kebab_case("hello world example text") == "hello-world-example-text"
        assert self.converter.to_kebab_case("helloWorldExampleText") == "hello-world-example-text"

        # Edge cases
        assert self.converter.to_kebab_case("") == ""
        assert self.converter.to_kebab_case("   ") == ""
        assert self.converter.to_kebab_case("hello") == "hello"
        assert self.converter.to_kebab_case("HELLO") == "hello"

    def test_to_header_case(self):
        """Test Header-Case conversion."""
        # Basic conversion
        assert self.converter.to_header_case("hello world") == "Hello-World"
        assert self.converter.to_header_case("helloWorld") == "Hello-World"
        assert self.converter.to_header_case("HelloWorld") == "Hello-World"
        assert self.converter.to_header_case("hello_world") == "Hello-World"
        assert self.converter.to_header_case("hello.world") == "Hello-World"

        # Multiple words
        assert self.converter.to_header_case("hello world example text") == "Hello-World-Example-Text"
        assert self.converter.to_header_case("helloWorldExampleText") == "Hello-World-Example-Text"

        # Edge cases
        assert self.converter.to_header_case("") == ""
        assert self.converter.to_header_case("   ") == ""
        assert self.converter.to_header_case("hello") == "Hello"
        assert self.converter.to_header_case("HELLO") == "Hello"

    def test_to_uppercase(self):
        """Test UPPERCASE conversion."""
        assert self.converter.to_uppercase("hello world") == "HELLO WORLD"
        assert self.converter.to_uppercase("helloWorld") == "HELLOWORLD"
        assert self.converter.to_uppercase("Hello-World") == "HELLO-WORLD"
        assert self.converter.to_uppercase("") == ""
        assert self.converter.to_uppercase("123abc") == "123ABC"

    def test_to_lowercase(self):
        """Test lowercase conversion."""
        assert self.converter.to_lowercase("HELLO WORLD") == "hello world"
        assert self.converter.to_lowercase("HelloWorld") == "helloworld"
        assert self.converter.to_lowercase("Hello-World") == "hello-world"
        assert self.converter.to_lowercase("") == ""
        assert self.converter.to_lowercase("123ABC") == "123abc"

    def test_to_title_case(self):
        """Test Title Case conversion."""
        # Basic conversion
        assert self.converter.to_title_case("hello world") == "Hello World"
        assert self.converter.to_title_case("helloWorld") == "Hello World"
        assert self.converter.to_title_case("HelloWorld") == "Hello World"
        assert self.converter.to_title_case("hello_world") == "Hello World"
        assert self.converter.to_title_case("hello-world") == "Hello World"
        assert self.converter.to_title_case("hello.world") == "Hello World"

        # Multiple words
        assert self.converter.to_title_case("hello world example text") == "Hello World Example Text"
        assert self.converter.to_title_case("helloWorldExampleText") == "Hello World Example Text"

        # Edge cases
        assert self.converter.to_title_case("") == ""
        assert self.converter.to_title_case("   ") == ""
        assert self.converter.to_title_case("hello") == "Hello"
        assert self.converter.to_title_case("HELLO") == "Hello"

    def test_convert_case(self):
        """Test the main convert_case method."""
        test_text = "hello world"

        # Test all case types
        assert self.converter.convert_case(test_text, "camelCase") == "helloWorld"
        assert self.converter.convert_case(test_text, "PascalCase") == "HelloWorld"
        assert self.converter.convert_case(test_text, "snake_case") == "hello_world"
        assert self.converter.convert_case(test_text, "kebab-case") == "hello-world"
        assert self.converter.convert_case(test_text, "Header-Case") == "Hello-World"
        assert self.converter.convert_case(test_text, "UPPERCASE") == "HELLO WORLD"
        assert self.converter.convert_case(test_text, "lowercase") == "hello world"
        assert self.converter.convert_case(test_text, "Title Case") == "Hello World"

        # Test unknown case type
        assert self.converter.convert_case(test_text, "unknown") == test_text

        # Test empty text
        assert self.converter.convert_case("", "camelCase") == ""

    def test_complex_conversions(self):
        """Test complex text conversions."""
        complex_text = "XMLHttpRequest_API-Handler.processData"

        # Test various conversions
        assert self.converter.to_camel_case(complex_text) == "xmlhttprequestApiHandlerProcessdata"
        assert self.converter.to_pascal_case(complex_text) == "XmlhttprequestApiHandlerProcessdata"
        assert self.converter.to_snake_case(complex_text) == "xmlhttp_request_api_handler_process_data"
        assert self.converter.to_kebab_case(complex_text) == "xmlhttp-request-api-handler-process-data"
        assert self.converter.to_header_case(complex_text) == "Xmlhttp-Request-Api-Handler-Process-Data"
        assert self.converter.to_title_case(complex_text) == "Xmlhttp Request Api Handler Process Data"

    def test_numbers_and_special_chars(self):
        """Test handling of numbers and special characters."""
        text_with_numbers = "hello123world456"

        # Numbers should be preserved
        assert self.converter.to_snake_case(text_with_numbers) == "hello123world456"
        assert self.converter.to_kebab_case(text_with_numbers) == "hello123world456"
        assert self.converter.to_camel_case(text_with_numbers) == "hello123world456"

        # Test with mixed content
        mixed_text = "API_v2.1-beta"
        assert self.converter.to_camel_case(mixed_text) == "apiV21Beta"
        assert self.converter.to_snake_case(mixed_text) == "api_v2_1_beta"

    def test_whitespace_handling(self):
        """Test handling of various whitespace scenarios."""
        # Multiple spaces
        assert self.converter.to_camel_case("hello    world") == "helloWorld"

        # Leading/trailing spaces
        assert self.converter.to_camel_case("  hello world  ") == "helloWorld"

        # Tabs and newlines
        assert self.converter.to_camel_case("hello\tworld\ntest") == "helloWorldTest"

    def test_single_word_handling(self):
        """Test handling of single words."""
        single_word = "hello"

        assert self.converter.to_camel_case(single_word) == "hello"
        assert self.converter.to_pascal_case(single_word) == "Hello"
        assert self.converter.to_snake_case(single_word) == "hello"
        assert self.converter.to_kebab_case(single_word) == "hello"
        assert self.converter.to_header_case(single_word) == "Hello"
        assert self.converter.to_title_case(single_word) == "Hello"
