from devboost.tools.url_encode_decode import URLCodec


class TestURLCodec:
    """Test cases for URLCodec class."""

    def test_encode_url_basic(self):
        """Test basic URL encoding."""
        codec = URLCodec()
        result = codec.encode_url("hello world")
        assert result == "hello+world"

    def test_encode_url_special_characters(self):
        """Test URL encoding with special characters."""
        codec = URLCodec()
        result = codec.encode_url("hello@world.com")
        assert result == "hello%40world.com"

    def test_encode_url_symbols(self):
        """Test URL encoding with various symbols."""
        codec = URLCodec()
        result = codec.encode_url("test&param=value")
        assert result == "test%26param%3Dvalue"

    def test_encode_url_unicode(self):
        """Test URL encoding with Unicode characters."""
        codec = URLCodec()
        result = codec.encode_url("café")
        assert result == "caf%C3%A9"

    def test_encode_url_empty_string(self):
        """Test URL encoding with empty string."""
        codec = URLCodec()
        result = codec.encode_url("")
        assert result == ""

    def test_encode_url_none(self):
        """Test URL encoding with None input."""
        codec = URLCodec()
        result = codec.encode_url(None)
        assert result == ""

    def test_decode_url_basic(self):
        """Test basic URL decoding."""
        codec = URLCodec()
        result = codec.decode_url("hello+world")
        assert result == "hello world"

    def test_decode_url_percent_encoding(self):
        """Test URL decoding with percent encoding."""
        codec = URLCodec()
        result = codec.decode_url("hello%20world")
        assert result == "hello world"

    def test_decode_url_special_characters(self):
        """Test URL decoding with special characters."""
        codec = URLCodec()
        result = codec.decode_url("hello%40world.com")
        assert result == "hello@world.com"

    def test_decode_url_symbols(self):
        """Test URL decoding with various symbols."""
        codec = URLCodec()
        result = codec.decode_url("test%26param%3Dvalue")
        assert result == "test&param=value"

    def test_decode_url_unicode(self):
        """Test URL decoding with Unicode characters."""
        codec = URLCodec()
        result = codec.decode_url("caf%C3%A9")
        assert result == "café"

    def test_decode_url_empty_string(self):
        """Test URL decoding with empty string."""
        codec = URLCodec()
        result = codec.decode_url("")
        assert result == ""

    def test_decode_url_none(self):
        """Test URL decoding with None input."""
        codec = URLCodec()
        result = codec.decode_url(None)
        assert result == ""

    def test_encode_url_component_basic(self):
        """Test basic URL component encoding."""
        codec = URLCodec()
        result = codec.encode_url_component("hello world")
        assert result == "hello%20world"

    def test_encode_url_component_special_characters(self):
        """Test URL component encoding with special characters."""
        codec = URLCodec()
        result = codec.encode_url_component("hello@world.com")
        assert result == "hello%40world.com"

    def test_encode_url_component_symbols(self):
        """Test URL component encoding with various symbols."""
        codec = URLCodec()
        result = codec.encode_url_component("test&param=value")
        assert result == "test%26param%3Dvalue"

    def test_encode_url_component_unicode(self):
        """Test URL component encoding with Unicode characters."""
        codec = URLCodec()
        result = codec.encode_url_component("café")
        assert result == "caf%C3%A9"

    def test_encode_url_component_empty_string(self):
        """Test URL component encoding with empty string."""
        codec = URLCodec()
        result = codec.encode_url_component("")
        assert result == ""

    def test_encode_url_component_none(self):
        """Test URL component encoding with None input."""
        codec = URLCodec()
        result = codec.encode_url_component(None)
        assert result == ""

    def test_decode_url_component_basic(self):
        """Test basic URL component decoding."""
        codec = URLCodec()
        result = codec.decode_url_component("hello%20world")
        assert result == "hello world"

    def test_decode_url_component_special_characters(self):
        """Test URL component decoding with special characters."""
        codec = URLCodec()
        result = codec.decode_url_component("hello%40world.com")
        assert result == "hello@world.com"

    def test_decode_url_component_symbols(self):
        """Test URL component decoding with various symbols."""
        codec = URLCodec()
        result = codec.decode_url_component("test%26param%3Dvalue")
        assert result == "test&param=value"

    def test_decode_url_component_unicode(self):
        """Test URL component decoding with Unicode characters."""
        codec = URLCodec()
        result = codec.decode_url_component("caf%C3%A9")
        assert result == "café"

    def test_decode_url_component_empty_string(self):
        """Test URL component decoding with empty string."""
        codec = URLCodec()
        result = codec.decode_url_component("")
        assert result == ""

    def test_decode_url_component_none(self):
        """Test URL component decoding with None input."""
        codec = URLCodec()
        result = codec.decode_url_component(None)
        assert result == ""

    def test_encode_decode_roundtrip(self):
        """Test that encoding and then decoding returns original text."""
        codec = URLCodec()
        original = "Hello World! @#$%^&*()_+ café"
        encoded = codec.encode_url(original)
        decoded = codec.decode_url(encoded)
        assert decoded == original

    def test_encode_decode_component_roundtrip(self):
        """Test that component encoding and then decoding returns original text."""
        codec = URLCodec()
        original = "Hello World! @#$%^&*()_+ café"
        encoded = codec.encode_url_component(original)
        decoded = codec.decode_url_component(encoded)
        assert decoded == original

    def test_complex_url_encoding(self):
        """Test encoding of a complex URL with query parameters."""
        codec = URLCodec()
        url = "https://example.com/search?q=hello world&category=test"
        result = codec.encode_url(url)
        expected = "https%3A%2F%2Fexample.com%2Fsearch%3Fq%3Dhello+world%26category%3Dtest"
        assert result == expected

    def test_complex_url_decoding(self):
        """Test decoding of a complex encoded URL."""
        codec = URLCodec()
        encoded_url = "https%3A//example.com/search%3Fq%3Dhello+world%26category%3Dtest"
        result = codec.decode_url(encoded_url)
        expected = "https://example.com/search?q=hello world&category=test"
        assert result == expected

    def test_space_encoding_differences(self):
        """Test the difference between URL and component encoding for spaces."""
        codec = URLCodec()
        text = "hello world"

        url_encoded = codec.encode_url(text)
        component_encoded = codec.encode_url_component(text)

        assert url_encoded == "hello+world"
        assert component_encoded == "hello%20world"

    def test_malformed_input_handling(self):
        """Test handling of malformed encoded input."""
        codec = URLCodec()
        # Test with incomplete percent encoding
        result = codec.decode_url("hello%2")
        # Should handle gracefully and not crash
        assert isinstance(result, str)

    def test_edge_case_characters(self):
        """Test encoding/decoding of edge case characters."""
        codec = URLCodec()
        edge_cases = [
            "\n\r\t",  # Newlines and tabs
            "<>\"'",  # HTML special chars
            "{}[]|\\^`",  # Other special chars
        ]

        for text in edge_cases:
            encoded = codec.encode_url(text)
            decoded = codec.decode_url(encoded)
            assert decoded == text, f"Failed roundtrip for: {text!r}"
