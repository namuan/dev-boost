import unittest

from devdriver.tools.regex_tester import RegexTester


class TestRegexTester(unittest.TestCase):
    """Test cases for RegExp Tester backend logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.tester = RegexTester()

    def test_set_pattern_valid(self):
        """Test setting a valid regex pattern."""
        result = self.tester.set_pattern(r"\d+")
        self.assertTrue(result)
        self.assertEqual(self.tester.pattern, r"\d+")

    def test_set_pattern_invalid(self):
        """Test setting an invalid regex pattern."""
        result = self.tester.set_pattern(r"[invalid")
        self.assertFalse(result)
        self.assertEqual(self.tester.pattern, "")  # Should not update on invalid pattern

    def test_set_text(self):
        """Test setting text to test against."""
        test_text = "Hello 123 World 456"
        self.tester.set_text(test_text)
        self.assertEqual(self.tester.text, test_text)

    def test_find_matches_simple(self):
        """Test finding simple matches."""
        self.tester.set_pattern(r"\d+")
        self.tester.set_text("Hello 123 World 456")

        matches = self.tester.find_matches()
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0], ("123", 6, 9))
        self.assertEqual(matches[1], ("456", 16, 19))

    def test_find_matches_no_pattern(self):
        """Test finding matches with no pattern set."""
        self.tester.set_text("Hello 123 World 456")
        matches = self.tester.find_matches()
        self.assertEqual(matches, [])

    def test_find_matches_no_text(self):
        """Test finding matches with no text set."""
        self.tester.set_pattern(r"\d+")
        matches = self.tester.find_matches()
        self.assertEqual(matches, [])

    def test_find_matches_no_matches(self):
        """Test finding matches when pattern doesn't match text."""
        self.tester.set_pattern(r"\d+")
        self.tester.set_text("Hello World")

        matches = self.tester.find_matches()
        self.assertEqual(matches, [])

    def test_get_match_count(self):
        """Test getting match count."""
        self.tester.set_pattern(r"\w+")
        self.tester.set_text("Hello World Test")

        count = self.tester.get_match_count()
        self.assertEqual(count, 3)

    def test_get_match_count_no_matches(self):
        """Test getting match count when no matches."""
        self.tester.set_pattern(r"\d+")
        self.tester.set_text("Hello World")

        count = self.tester.get_match_count()
        self.assertEqual(count, 0)

    def test_replace_matches(self):
        """Test replacing matches."""
        self.tester.set_pattern(r"\d+")
        self.tester.set_text("Hello 123 World 456")

        result = self.tester.replace_matches("XXX")
        self.assertEqual(result, "Hello XXX World XXX")

    def test_replace_matches_no_pattern(self):
        """Test replacing matches with no pattern."""
        self.tester.set_text("Hello 123 World 456")

        result = self.tester.replace_matches("XXX")
        self.assertEqual(result, "Hello 123 World 456")

    def test_replace_matches_invalid_pattern(self):
        """Test replacing matches with invalid pattern."""
        self.tester.pattern = "[invalid"  # Set invalid pattern directly
        self.tester.set_text("Hello 123 World 456")

        result = self.tester.replace_matches("XXX")
        self.assertEqual(result, "Hello 123 World 456")

    def test_format_output_simple(self):
        """Test formatting output with simple format."""
        self.tester.set_pattern(r"\d+")
        self.tester.set_text("Hello 123 World 456")

        result = self.tester.format_output("$&\\n")
        self.assertEqual(result, "123\n456\n")

    def test_format_output_no_matches(self):
        """Test formatting output when no matches."""
        self.tester.set_pattern(r"\d+")
        self.tester.set_text("Hello World")

        result = self.tester.format_output("$&\\n")
        self.assertEqual(result, "")

    def test_format_output_with_tabs(self):
        """Test formatting output with tab characters."""
        self.tester.set_pattern(r"\w+")
        self.tester.set_text("Hello World")

        result = self.tester.format_output("$&\\t")
        self.assertEqual(result, "Hello\tWorld\t")

    def test_format_output_custom_format(self):
        """Test formatting output with custom format."""
        self.tester.set_pattern(r"\d+")
        self.tester.set_text("Hello 123 World 456")

        result = self.tester.format_output("Found: $&, ")
        self.assertEqual(result, "Found: 123, Found: 456, ")

    def test_get_sample_pattern(self):
        """Test getting sample pattern."""
        sample = self.tester.get_sample_pattern()
        self.assertIsInstance(sample, str)
        self.assertTrue(len(sample) > 0)

        # Test that sample pattern is valid
        result = self.tester.set_pattern(sample)
        self.assertTrue(result)

    def test_email_pattern_matching(self):
        """Test email pattern matching with sample."""
        email_pattern = self.tester.get_sample_pattern()
        self.tester.set_pattern(email_pattern)

        test_text = "Contact: john.doe@example.com and support@company.org"
        self.tester.set_text(test_text)

        matches = self.tester.find_matches()
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0][0], "john.doe@example.com")
        self.assertEqual(matches[1][0], "support@company.org")

    def test_complex_pattern(self):
        """Test complex regex pattern."""
        # Pattern for phone numbers - improved to handle spaces
        phone_pattern = r"\(?\d{3}\)?[-. ]?\d{3}[-.]?\d{4}"
        self.tester.set_pattern(phone_pattern)

        test_text = "Call us at (555) 123-4567 or 555.987.6543"
        self.tester.set_text(test_text)

        matches = self.tester.find_matches()
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0][0], "(555) 123-4567")
        self.assertEqual(matches[1][0], "555.987.6543")

    def test_case_sensitive_matching(self):
        """Test case sensitive pattern matching."""
        self.tester.set_pattern(r"Hello")
        self.tester.set_text("Hello world, hello again")

        matches = self.tester.find_matches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "Hello")

    def test_word_boundary_pattern(self):
        """Test word boundary pattern."""
        self.tester.set_pattern(r"\btest\b")
        self.tester.set_text("This is a test, testing, and contest")

        matches = self.tester.find_matches()
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "test")


if __name__ == "__main__":
    unittest.main()
