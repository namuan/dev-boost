"""
Unit tests for the Cron Expression Editor tool.
"""

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from devboost.tools.cron_expression_editor import CronExpressionParser


class TestCronExpressionParser(unittest.TestCase):
    """Test cases for CronExpressionParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = CronExpressionParser()

    def test_validate_valid_expressions(self):
        """Test validation of valid cron expressions."""
        valid_expressions = [
            "0 0 * * *",  # Daily at midnight
            "0 12 * * *",  # Daily at noon
            "0 0 * * 0",  # Weekly on Sunday
            "0 0 1 * *",  # Monthly on 1st
            "*/5 * * * *",  # Every 5 minutes
            "0 9-17 * * 1-5",  # Business hours
            "30 2 * * 1",  # Weekly on Monday at 2:30 AM
        ]

        for expr in valid_expressions:
            with self.subTest(expression=expr):
                is_valid, error = self.parser.validate(expr)
                self.assertTrue(is_valid, f"Expression '{expr}' should be valid, but got error: {error}")
                self.assertIsNone(error)

    def test_validate_invalid_expressions(self):
        """Test validation of invalid cron expressions."""
        invalid_expressions = [
            "",  # Empty string
            "* * * *",  # Too few fields
            "* * * * * *",  # Too many fields
            "60 * * * *",  # Invalid minute (60)
            "* 24 * * *",  # Invalid hour (24)
            "* * 32 * *",  # Invalid day (32)
            "* * * 13 *",  # Invalid month (13)
            "* * * * 8",  # Invalid day of week (8)
            "invalid",  # Non-numeric
        ]

        for expr in invalid_expressions:
            with self.subTest(expression=expr):
                is_valid, error = self.parser.validate(expr)
                self.assertFalse(is_valid, f"Expression '{expr}' should be invalid")
                self.assertIsNotNone(error)

    @patch("devboost.tools.cron_expression_editor.datetime")
    def test_get_next_run_times(self, mock_datetime):
        """Test calculation of next run times."""
        # Mock current time to 2024-01-15 10:30:00 UTC (Monday)
        mock_now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        test_cases = [
            {
                "expression": "0 12 * * *",  # Daily at noon
                "expected_count": 5,
                "description": "Daily at noon should have 5 future runs",
            },
            {
                "expression": "0 0 * * 0",  # Weekly on Sunday
                "expected_count": 5,
                "description": "Weekly on Sunday should have 5 future runs",
            },
            {
                "expression": "*/15 * * * *",  # Every 15 minutes
                "expected_count": 5,
                "description": "Every 15 minutes should have 5 future runs",
            },
        ]

        for case in test_cases:
            with self.subTest(expression=case["expression"]):
                next_runs = self.parser.get_next_run_times(case["expression"], count=5)
                self.assertEqual(len(next_runs), case["expected_count"], case["description"])

                # Verify all times are in the future
                for run_time in next_runs:
                    self.assertGreater(run_time, mock_now, "All run times should be in the future")

                # Verify times are in ascending order
                for i in range(1, len(next_runs)):
                    self.assertGreater(next_runs[i], next_runs[i - 1], "Run times should be in ascending order")

    def test_get_next_run_times_invalid_expression(self):
        """Test get_next_run_times with invalid expression."""
        next_runs = self.parser.get_next_run_times("invalid expression")
        self.assertEqual(next_runs, [], "Invalid expression should return empty list")

    def test_get_human_readable_description(self):
        """Test human-readable description generation."""
        test_cases = [
            {"expression": "0 0 * * *", "expected_keywords": ["daily", "midnight", "00:00"]},
            {"expression": "0 12 * * *", "expected_keywords": ["daily", "noon", "12:00"]},
            {"expression": "0 0 * * 0", "expected_keywords": ["weekly", "sunday"]},
            {"expression": "0 0 1 * *", "expected_keywords": ["monthly", "first"]},
            {"expression": "*/5 * * * *", "expected_keywords": ["every", "5", "minute"]},
            {"expression": "0 9-17 * * 1-5", "expected_keywords": ["business", "weekday", "monday", "friday"]},
        ]

        for case in test_cases:
            with self.subTest(expression=case["expression"]):
                description = self.parser.get_human_readable_description(case["expression"])
                self.assertIsInstance(description, str, "Description should be a string")
                self.assertGreater(len(description), 0, "Description should not be empty")

                # Check for expected keywords (case-insensitive)
                description_lower = description.lower()
                for keyword in case["expected_keywords"]:
                    self.assertIn(
                        keyword.lower(),
                        description_lower,
                        f"Description should contain '{keyword}' for expression '{case['expression']}'",
                    )

    def test_get_human_readable_description_invalid_expression(self):
        """Test human-readable description with invalid expression."""
        description = self.parser.get_human_readable_description("invalid expression")
        self.assertIn("invalid", description.lower(), "Should indicate invalid expression")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with None input
        is_valid, error = self.parser.validate(None)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

        # Test with whitespace
        is_valid, error = self.parser.validate("   ")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

        # Test boundary values
        boundary_cases = [
            "0 0 1 1 0",  # January 1st, Sunday
            "59 23 31 12 6",  # December 31st, Saturday, 23:59
            "0 0 29 2 *",  # February 29th (leap year consideration)
        ]

        for expr in boundary_cases:
            with self.subTest(expression=expr):
                is_valid, error = self.parser.validate(expr)
                self.assertTrue(is_valid, f"Boundary case '{expr}' should be valid, but got error: {error}")


class TestCronExpressionEditorIntegration(unittest.TestCase):
    """Integration tests for the complete cron expression editor."""

    def test_create_widget_function_exists(self):
        """Test that the create widget function exists and is callable."""
        from devboost.tools.cron_expression_editor import create_cron_expression_editor_widget

        self.assertTrue(
            callable(create_cron_expression_editor_widget), "create_cron_expression_editor_widget should be callable"
        )

    @patch("devboost.tools.cron_expression_editor.QWidget")
    def test_widget_creation(self, mock_qwidget):
        """Test widget creation without actually creating PyQt widgets."""
        from devboost.tools.cron_expression_editor import create_cron_expression_editor_widget

        # Mock the QWidget to avoid PyQt dependencies in tests
        mock_widget = MagicMock()
        mock_qwidget.return_value = mock_widget

        try:
            widget = create_cron_expression_editor_widget()
            # If we get here without exception, the function works
            self.assertIsNotNone(widget, "Widget creation should return a widget")
        except ImportError:
            # If PyQt6 is not available in test environment, skip this test
            self.skipTest("PyQt6 not available in test environment")


if __name__ == "__main__":
    unittest.main()
