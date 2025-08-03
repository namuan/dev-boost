import datetime
import unittest
from unittest.mock import patch

from devboost.tools.unix_time_converter import UnixTimeConverter


class TestUnixTimeConverter(unittest.TestCase):
    """Test cases for Unix Time Converter backend logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = UnixTimeConverter()
        # Known timestamp: 2024-01-01 00:00:00 UTC
        self.test_timestamp = 1704067200.0

    def test_parse_input_simple_number(self):
        """Test parsing simple numeric input."""
        result = self.converter.parse_input("1704067200")
        self.assertEqual(result, 1704067200.0)

        result = self.converter.parse_input("1704067200.5")
        self.assertEqual(result, 1704067200.5)

    def test_parse_input_mathematical_expressions(self):
        """Test parsing mathematical expressions."""
        result = self.converter.parse_input("1704067200 + 3600")
        self.assertEqual(result, 1704070800.0)

        result = self.converter.parse_input("1704067200 * 2")
        self.assertEqual(result, 3408134400.0)

        result = self.converter.parse_input("(1704067200 + 3600) / 2")
        self.assertEqual(result, 852035400.0)

    def test_parse_input_invalid(self):
        """Test parsing invalid input."""
        result = self.converter.parse_input("")
        self.assertIsNone(result)

        result = self.converter.parse_input("invalid")
        self.assertIsNone(result)

        result = self.converter.parse_input("1704067200 + abc")
        self.assertIsNone(result)

    def test_unix_to_datetime(self):
        """Test Unix timestamp to UTC datetime conversion."""
        dt = self.converter.unix_to_datetime(self.test_timestamp)
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 0)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.tzinfo, datetime.UTC)

    def test_unix_to_local_datetime(self):
        """Test Unix timestamp to local datetime conversion."""
        dt = self.converter.unix_to_local_datetime(self.test_timestamp)
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)
        # Note: hour may vary based on local timezone

    def test_format_utc_iso(self):
        """Test UTC ISO 8601 formatting."""
        dt = self.converter.unix_to_datetime(self.test_timestamp)
        formatted = self.converter.format_utc_iso(dt)
        self.assertTrue(formatted.startswith("2024-01-01T00:00:00"))
        self.assertTrue(formatted.endswith("Z"))

    def test_format_relative_time(self):
        """Test relative time formatting."""
        with patch("time.time", return_value=self.test_timestamp + 3600):
            # 1 hour ago
            result = self.converter.format_relative_time(self.test_timestamp)
            self.assertEqual(result, "1 hour ago")

        with patch("time.time", return_value=self.test_timestamp + 7200):
            # 2 hours ago
            result = self.converter.format_relative_time(self.test_timestamp)
            self.assertEqual(result, "2 hours ago")

        with patch("time.time", return_value=self.test_timestamp + 30):
            # Just now
            result = self.converter.format_relative_time(self.test_timestamp)
            self.assertEqual(result, "Just now")

        with patch("time.time", return_value=self.test_timestamp - 3600):
            # 1 hour from now
            result = self.converter.format_relative_time(self.test_timestamp)
            self.assertEqual(result, "1 hour from now")

    def test_get_day_of_year(self):
        """Test day of year calculation."""
        dt = self.converter.unix_to_datetime(self.test_timestamp)
        day_of_year = self.converter.get_day_of_year(dt)
        self.assertEqual(day_of_year, 1)  # January 1st is day 1

    def test_get_week_of_year(self):
        """Test week of year calculation."""
        dt = self.converter.unix_to_datetime(self.test_timestamp)
        week_of_year = self.converter.get_week_of_year(dt)
        self.assertEqual(week_of_year, 1)  # First week of 2024

    def test_is_leap_year(self):
        """Test leap year detection."""
        dt_2024 = self.converter.unix_to_datetime(self.test_timestamp)
        self.assertTrue(self.converter.is_leap_year(dt_2024))  # 2024 is a leap year

        # Test non-leap year (2023)
        dt_2023 = datetime.datetime(2023, 1, 1, tzinfo=datetime.UTC)
        self.assertFalse(self.converter.is_leap_year(dt_2023))

    def test_get_current_timestamp(self):
        """Test current timestamp retrieval."""
        with patch("time.time", return_value=self.test_timestamp):
            result = self.converter.get_current_timestamp()
            self.assertEqual(result, self.test_timestamp)

    def test_format_local_time(self):
        """Test local time formatting."""
        dt = self.converter.unix_to_local_datetime(self.test_timestamp)
        formatted = self.converter.format_local_time(dt)
        self.assertTrue("2024-01-01" in formatted)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test epoch (1970-01-01 00:00:00 UTC)
        epoch_dt = self.converter.unix_to_datetime(0)
        self.assertEqual(epoch_dt.year, 1970)
        self.assertEqual(epoch_dt.month, 1)
        self.assertEqual(epoch_dt.day, 1)

        # Test negative timestamp (before epoch)
        negative_dt = self.converter.unix_to_datetime(-86400)  # 1969-12-31
        self.assertEqual(negative_dt.year, 1969)
        self.assertEqual(negative_dt.month, 12)
        self.assertEqual(negative_dt.day, 31)

        # Test very large timestamp
        large_timestamp = 2147483647  # 2038-01-19 (32-bit limit)
        large_dt = self.converter.unix_to_datetime(large_timestamp)
        self.assertEqual(large_dt.year, 2038)

    def test_mathematical_operators_security(self):
        """Test that only safe mathematical operations are allowed."""
        # Test that dangerous operations are rejected
        result = self.converter.parse_input("__import__('os').system('ls')")
        self.assertIsNone(result)

        result = self.converter.parse_input("exec('print(1)')")
        self.assertIsNone(result)

        # Test that only numbers and basic operators work
        result = self.converter.parse_input("1 + 2 * 3")
        self.assertEqual(result, 7.0)

    def test_timezone_conversion(self):
        """Test timezone conversion functionality."""
        # Test valid timezone conversion
        dt = self.converter.unix_to_timezone_datetime(self.test_timestamp, "UTC")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)

        # Test invalid timezone
        dt = self.converter.unix_to_timezone_datetime(self.test_timestamp, "Invalid/Timezone")
        self.assertIsNone(dt)

        # Test New York timezone (EST/EDT)
        dt_ny = self.converter.unix_to_timezone_datetime(self.test_timestamp, "America/New_York")
        self.assertIsNotNone(dt_ny)
        self.assertEqual(dt_ny.year, 2023)  # Should be Dec 31, 2023 in EST
        self.assertEqual(dt_ny.month, 12)
        self.assertEqual(dt_ny.day, 31)

    def test_get_common_timezones(self):
        """Test getting common timezones list."""
        timezones = self.converter.get_common_timezones()
        self.assertIsInstance(timezones, list)
        self.assertIn("UTC", timezones)
        self.assertIn("America/New_York", timezones)
        self.assertIn("Europe/London", timezones)
        self.assertGreater(len(timezones), 5)  # Should have multiple timezones


if __name__ == "__main__":
    unittest.main()
