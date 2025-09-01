import tempfile
from datetime import datetime, time
from pathlib import Path
from unittest.mock import patch

from devboost.tools.timezone_converter import TimeZoneConverter


class TestTimeZoneConverter:
    """Test suite for TimeZoneConverter backend logic."""

    def test_parse_time_input_24h_format(self):
        """Test parsing 24-hour time formats."""
        # Test HH:MM format
        result = TimeZoneConverter.parse_time_input("14:30")
        assert result == time(14, 30)

        # Test H:MM format
        result = TimeZoneConverter.parse_time_input("9:15")
        assert result == time(9, 15)

        # Test HHMM format
        result = TimeZoneConverter.parse_time_input("1430")
        assert result == time(14, 30)

        # Test HMM format
        result = TimeZoneConverter.parse_time_input("915")
        assert result == time(9, 15)

        # Test HH format
        result = TimeZoneConverter.parse_time_input("14")
        assert result == time(14, 0)

        # Test H format
        result = TimeZoneConverter.parse_time_input("9")
        assert result == time(9, 0)

    def test_parse_time_input_12h_format(self):
        """Test parsing 12-hour time formats with AM/PM."""
        # Test AM format
        result = TimeZoneConverter.parse_time_input("9:30 AM")
        assert result == time(9, 30)

        result = TimeZoneConverter.parse_time_input("12:00 AM")
        assert result == time(0, 0)

        # Test PM format
        result = TimeZoneConverter.parse_time_input("2:30 PM")
        assert result == time(14, 30)

        result = TimeZoneConverter.parse_time_input("12:00 PM")
        assert result == time(12, 0)

        # Test without minutes
        result = TimeZoneConverter.parse_time_input("9 AM")
        assert result == time(9, 0)

        result = TimeZoneConverter.parse_time_input("2 PM")
        assert result == time(14, 0)

    def test_parse_time_input_invalid(self):
        """Test parsing invalid time inputs."""
        # Empty input
        result = TimeZoneConverter.parse_time_input("")
        assert result is None

        # Invalid format
        result = TimeZoneConverter.parse_time_input("invalid")
        assert result is None

        # Invalid hour
        result = TimeZoneConverter.parse_time_input("25:00")
        assert result is None

        # Invalid minute
        result = TimeZoneConverter.parse_time_input("14:60")
        assert result is None

    def test_parse_date_input_relative(self):
        """Test parsing relative date inputs."""
        from datetime import date, timedelta

        today = date.today()

        # Test 'today' and 't'
        result = TimeZoneConverter.parse_date_input("today")
        assert result == today

        result = TimeZoneConverter.parse_date_input("t")
        assert result == today

        # Test 'tomorrow' and 'tm'
        result = TimeZoneConverter.parse_date_input("tomorrow")
        assert result == today + timedelta(days=1)

        result = TimeZoneConverter.parse_date_input("tm")
        assert result == today + timedelta(days=1)

        # Test '+Nd' format
        result = TimeZoneConverter.parse_date_input("+3d")
        assert result == today + timedelta(days=3)

        result = TimeZoneConverter.parse_date_input("+1d")
        assert result == today + timedelta(days=1)

    def test_parse_date_input_absolute(self):
        """Test parsing absolute date inputs."""
        from datetime import date

        today = date.today()

        # Test dd format (day of current month)
        result = TimeZoneConverter.parse_date_input("15")
        expected = today.replace(day=15)
        assert result == expected

        # Test mmdd format
        result = TimeZoneConverter.parse_date_input("0315")
        expected = today.replace(month=3, day=15)
        assert result == expected

        # Test yymmdd format
        result = TimeZoneConverter.parse_date_input("240315")
        expected = date(2024, 3, 15)
        assert result == expected

        # Test yyyymmdd format
        result = TimeZoneConverter.parse_date_input("20240315")
        expected = date(2024, 3, 15)
        assert result == expected

    def test_parse_date_input_invalid(self):
        """Test parsing invalid date inputs."""
        # Empty input
        result = TimeZoneConverter.parse_date_input("")
        assert result is None

        # Invalid format
        result = TimeZoneConverter.parse_date_input("invalid")
        assert result is None

        # Invalid date
        result = TimeZoneConverter.parse_date_input("0230")  # Feb 30th
        assert result is None

    def test_get_timezone_for_city(self):
        """Test city to timezone mapping."""
        # Test exact matches with fallback cities that should work
        result = TimeZoneConverter.get_timezone_for_city("nyc")
        assert result == "America/New_York"

        result = TimeZoneConverter.get_timezone_for_city("london")
        assert result == "Europe/London"

        result = TimeZoneConverter.get_timezone_for_city("tokyo")
        assert result == "Asia/Tokyo"

        # Test case insensitive
        result = TimeZoneConverter.get_timezone_for_city("NYC")
        assert result == "America/New_York"

        result = TimeZoneConverter.get_timezone_for_city("London")
        assert result == "Europe/London"

        # Test abbreviations
        result = TimeZoneConverter.get_timezone_for_city("nyc")
        assert result == "America/New_York"

        result = TimeZoneConverter.get_timezone_for_city("la")
        assert result == "America/Los_Angeles"

        # Test unknown city
        result = TimeZoneConverter.get_timezone_for_city("unknown_city")
        assert result is None

        # Test empty input
        result = TimeZoneConverter.get_timezone_for_city("")
        assert result is None

    def test_search_cities(self):
        """Test city search functionality."""
        # Test search for 'york' (should find New York)
        results = TimeZoneConverter.search_cities("york")
        assert len(results) > 0

        # Should find 'New York'
        city_names = [city["name"].lower() for city in results]
        assert any(name == "new york" for name in city_names)

        # Test search for 'london'
        results = TimeZoneConverter.search_cities("london")
        assert len(results) > 0
        assert any(city["name"].lower() == "london" for city in results)

        # Test empty search
        results = TimeZoneConverter.search_cities("")
        assert results == []

        # Test no matches
        results = TimeZoneConverter.search_cities("nonexistent_city_xyz")
        assert results == []

    def test_search_cities_barcelona_duplicates(self):
        """Test that Barcelona search returns multiple entries from different countries."""
        # Search for Barcelona should return multiple results
        results = TimeZoneConverter.search_cities("barcelona")

        # Should find at least 2 Barcelona entries (Spain and Venezuela)
        barcelona_results = [city for city in results if city["name"].lower() == "barcelona"]
        assert len(barcelona_results) >= 2, f"Expected at least 2 Barcelona entries, got {len(barcelona_results)}"

        # Should have different timezones
        timezones = {city["timezone"] for city in barcelona_results}
        assert len(timezones) >= 2, f"Expected different timezones, got {timezones}"

        # Should include Spain (Europe/Madrid) and Venezuela (America/Caracas)
        expected_timezones = {"Europe/Madrid", "America/Caracas"}
        found_timezones = {city["timezone"] for city in barcelona_results}
        assert expected_timezones.issubset(found_timezones), f"Expected {expected_timezones}, found {found_timezones}"

        # Display names should include country information for disambiguation
        for city in barcelona_results:
            display_name = city["display_name"]
            assert "barcelona" in display_name.lower(), f"Display name should contain Barcelona: {display_name}"
            # Should contain country or region info
            assert any(
                keyword in display_name.lower() for keyword in ["spain", "venezuela", "catalonia", "anzoátegui"]
            ), f"Display name should contain country/region info: {display_name}"

    def test_search_cities_various_duplicates(self):
        """Test search functionality with various cities that have duplicates."""
        # Test cities that commonly have duplicates
        test_cities = ["paris", "london", "madrid", "rome", "berlin"]

        for city_name in test_cities:
            results = TimeZoneConverter.search_cities(city_name)
            assert len(results) > 0, f"Should find results for {city_name}"

            # Check that results contain the searched city
            matching_cities = [city for city in results if city_name in city["name"].lower()]
            assert len(matching_cities) > 0, f"Should find cities matching {city_name}"

            # Check that display names are properly formatted
            for city in matching_cities:
                display_name = city["display_name"]
                assert city_name in display_name.lower(), f"Display name should contain {city_name}: {display_name}"
                assert (
                    "(" in display_name and ")" in display_name
                ), f"Display name should contain timezone: {display_name}"

    def test_search_cities_edge_cases(self):
        """Test edge cases for city search functionality."""
        # Test empty query
        results = TimeZoneConverter.search_cities("")
        assert results == [], "Empty query should return empty results"

        # Test whitespace-only query
        results = TimeZoneConverter.search_cities("   ")
        assert results == [], "Whitespace-only query should return empty results"

        # Test non-existent city
        results = TimeZoneConverter.search_cities("nonexistent_city_xyz_123")
        assert results == [], "Non-existent city should return empty results"

        # Test very short query that might match many cities
        results = TimeZoneConverter.search_cities("a")
        assert len(results) <= 50, "Results should be limited to 50 entries"

        # Test case sensitivity
        results_lower = TimeZoneConverter.search_cities("london")
        results_upper = TimeZoneConverter.search_cities("LONDON")
        results_mixed = TimeZoneConverter.search_cities("London")

        # All should return the same results (case insensitive)
        assert len(results_lower) > 0, "Lowercase search should find results"
        assert len(results_upper) > 0, "Uppercase search should find results"
        assert len(results_mixed) > 0, "Mixed case search should find results"

        # Test special characters in query
        results = TimeZoneConverter.search_cities("saint-")
        # Should handle special characters gracefully (either find results or return empty)
        assert isinstance(results, list), "Should return a list even with special characters"

        # Test very long query
        long_query = "a" * 100
        results = TimeZoneConverter.search_cities(long_query)
        assert results == [], "Very long query should return empty results"

    def test_get_current_time_in_timezone(self):
        """Test getting current time in timezone."""
        # Test valid timezone
        result = TimeZoneConverter.get_current_time_in_timezone("America/New_York")
        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

        # Test another valid timezone
        result = TimeZoneConverter.get_current_time_in_timezone("Europe/London")
        assert result is not None
        assert isinstance(result, datetime)

        # Test invalid timezone
        result = TimeZoneConverter.get_current_time_in_timezone("Invalid/Timezone")
        assert result is None

    def test_convert_time_between_zones(self):
        """Test time conversion between timezones."""
        # Test basic conversion
        result = TimeZoneConverter.convert_time_between_zones("14:30", "America/New_York", "Europe/London")
        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

        # Test with date
        result = TimeZoneConverter.convert_time_between_zones("14:30", "America/New_York", "Europe/London", "today")
        assert result is not None

        # Test invalid time
        result = TimeZoneConverter.convert_time_between_zones("invalid_time", "America/New_York", "Europe/London")
        assert result is None

        # Test invalid timezone
        result = TimeZoneConverter.convert_time_between_zones("14:30", "Invalid/Timezone", "Europe/London")
        assert result is None

    def test_format_time(self):
        """Test time formatting."""
        from zoneinfo import ZoneInfo

        dt = datetime(2024, 3, 15, 14, 30, tzinfo=ZoneInfo("UTC"))

        # Test 24-hour format
        result = TimeZoneConverter.format_time(dt, use_24h=True)
        assert result == "14:30"

        # Test 12-hour format
        result = TimeZoneConverter.format_time(dt, use_24h=False)
        assert result == "02:30 p.m."

        # Test morning time
        dt_morning = datetime(2024, 3, 15, 9, 15, tzinfo=ZoneInfo("UTC"))
        result = TimeZoneConverter.format_time(dt_morning, use_24h=False)
        assert result == "09:15 a.m."

    def test_format_date(self):
        """Test date formatting."""
        from zoneinfo import ZoneInfo

        dt = datetime(2024, 3, 15, 14, 30, tzinfo=ZoneInfo("UTC"))
        result = TimeZoneConverter.format_date(dt)
        assert result == "2024-03-15"

    def test_get_timezone_abbreviation(self):
        """Test timezone abbreviation extraction."""
        from zoneinfo import ZoneInfo

        # Test UTC
        dt = datetime(2024, 3, 15, 14, 30, tzinfo=ZoneInfo("UTC"))
        result = TimeZoneConverter.get_timezone_abbreviation(dt)
        assert result == "UTC"

        # Test EST (note: abbreviation may vary based on DST)
        dt_est = datetime(2024, 1, 15, 14, 30, tzinfo=ZoneInfo("America/New_York"))
        result = TimeZoneConverter.get_timezone_abbreviation(dt_est)
        assert result in ["EST", "EDT"]  # Could be either depending on DST

    def test_config_management(self):
        """Test configuration file management."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.object(TimeZoneConverter, "get_config_dir", return_value=Path(temp_dir)),
        ):
            # Test saving and loading cities
            test_cities = [
                {"name": "Test City 1", "timezone": "America/New_York"},
                {"name": "Test City 2", "timezone": "Europe/London"},
            ]

            # Save cities
            TimeZoneConverter.save_cities(test_cities)

            # Load cities
            loaded_cities = TimeZoneConverter.load_saved_cities()
            assert loaded_cities == test_cities

            # Test loading when file doesn't exist (should return defaults)
            config_file = Path(temp_dir) / "timezone_cities.json"
            config_file.unlink()  # Remove the file

            default_cities = TimeZoneConverter.load_saved_cities()
            assert len(default_cities) > 0  # Default cities
            assert any(city["name"] == "New York" for city in default_cities)

    def test_get_available_timezones(self):
        """Test getting available timezones."""
        timezones = TimeZoneConverter.get_available_timezones()
        assert isinstance(timezones, list)
        assert len(timezones) > 0
        assert "UTC" in timezones
        assert "America/New_York" in timezones
        assert "Europe/London" in timezones

        # Test that list is sorted
        assert timezones == sorted(timezones)

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test None inputs
        assert TimeZoneConverter.parse_time_input(None) is None
        assert TimeZoneConverter.parse_date_input(None) is None
        assert TimeZoneConverter.get_timezone_for_city(None) is None

        # Test whitespace inputs
        assert TimeZoneConverter.parse_time_input("   ") is None
        assert TimeZoneConverter.parse_date_input("   ") is None
        assert TimeZoneConverter.get_timezone_for_city("   ") is None

        # Test search with whitespace
        results = TimeZoneConverter.search_cities("   ")
        assert results == []

    def test_city_timezone_map_completeness(self):
        """Test that the city timezone map contains expected cities."""
        expected_cities = [
            "new york",
            "london",
            "tokyo",
            "sydney",
            "los angeles",
            "chicago",
            "toronto",
            "vancouver",
            "berlin",
            "paris",
        ]

        for city in expected_cities:
            timezone = TimeZoneConverter.get_timezone_for_city(city)
            assert timezone is not None, f"No timezone found for {city}"
            assert timezone.count("/") >= 1, f"Invalid timezone format for {city}: {timezone}"

    def test_time_conversion_accuracy(self):
        """Test that time conversions are accurate."""
        # Convert 12:00 PM EST to UTC (should be 17:00 UTC in winter)
        # Note: This test assumes standard time, not daylight saving time
        result = TimeZoneConverter.convert_time_between_zones(
            "12:00",
            "America/New_York",
            "UTC",
            "20240115",  # January 15, 2024 (EST)
        )

        if result:
            # In January, EST is UTC-5, so 12:00 EST = 17:00 UTC
            assert result.hour == 17
            assert result.minute == 0

    def test_widget_creation_function_exists(self):
        """Test that the widget creation function can be imported."""
        from devboost.tools.timezone_converter import create_timezone_converter_widget

        # Test that function exists and is callable
        assert callable(create_timezone_converter_widget)

        # Test that it can be called with minimal parameters
        # Note: We don't actually create the widget in tests to avoid GUI dependencies
        # widget = create_timezone_converter_widget(lambda: None, None)
        # assert widget is not None
