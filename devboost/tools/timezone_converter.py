import json
import logging
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, ClassVar
from zoneinfo import ZoneInfo, available_timezones

import appdirs
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style

logger = logging.getLogger(__name__)


class TimeZoneConverter:
    """Backend logic for timezone conversion and management."""

    # Common city to timezone mappings
    CITY_TIMEZONE_MAP: ClassVar[dict[str, str]] = {
        # Major cities
        "new york": "America/New_York",
        "nyc": "America/New_York",
        "london": "Europe/London",
        "paris": "Europe/Paris",
        "tokyo": "Asia/Tokyo",
        "sydney": "Australia/Sydney",
        "los angeles": "America/Los_Angeles",
        "la": "America/Los_Angeles",
        "chicago": "America/Chicago",
        "toronto": "America/Toronto",
        "vancouver": "America/Vancouver",
        "berlin": "Europe/Berlin",
        "madrid": "Europe/Madrid",
        "rome": "Europe/Rome",
        "moscow": "Europe/Moscow",
        "dubai": "Asia/Dubai",
        "singapore": "Asia/Singapore",
        "hong kong": "Asia/Hong_Kong",
        "mumbai": "Asia/Kolkata",
        "delhi": "Asia/Kolkata",
        "beijing": "Asia/Shanghai",
        "shanghai": "Asia/Shanghai",
        "seoul": "Asia/Seoul",
        "bangkok": "Asia/Bangkok",
        "jakarta": "Asia/Jakarta",
        "manila": "Asia/Manila",
        "melbourne": "Australia/Melbourne",
        "perth": "Australia/Perth",
        "auckland": "Pacific/Auckland",
        "san francisco": "America/Los_Angeles",
        "sf": "America/Los_Angeles",
        "boston": "America/New_York",
        "washington": "America/New_York",
        "dc": "America/New_York",
        "miami": "America/New_York",
        "denver": "America/Denver",
        "phoenix": "America/Phoenix",
        "seattle": "America/Los_Angeles",
        "atlanta": "America/New_York",
        "dallas": "America/Chicago",
        "houston": "America/Chicago",
        "montreal": "America/Montreal",
        "mexico city": "America/Mexico_City",
        "sao paulo": "America/Sao_Paulo",
        "buenos aires": "America/Argentina/Buenos_Aires",
        "lima": "America/Lima",
        "bogota": "America/Bogota",
        "caracas": "America/Caracas",
        "santiago": "America/Santiago",
        "cairo": "Africa/Cairo",
        "johannesburg": "Africa/Johannesburg",
        "lagos": "Africa/Lagos",
        "nairobi": "Africa/Nairobi",
        "casablanca": "Africa/Casablanca",
        "istanbul": "Europe/Istanbul",
        "athens": "Europe/Athens",
        "helsinki": "Europe/Helsinki",
        "stockholm": "Europe/Stockholm",
        "oslo": "Europe/Oslo",
        "copenhagen": "Europe/Copenhagen",
        "amsterdam": "Europe/Amsterdam",
        "brussels": "Europe/Brussels",
        "zurich": "Europe/Zurich",
        "vienna": "Europe/Vienna",
        "prague": "Europe/Prague",
        "warsaw": "Europe/Warsaw",
        "budapest": "Europe/Budapest",
        "bucharest": "Europe/Bucharest",
        "sofia": "Europe/Sofia",
        "zagreb": "Europe/Zagreb",
        "belgrade": "Europe/Belgrade",
        "kiev": "Europe/Kiev",
        "minsk": "Europe/Minsk",
        "riga": "Europe/Riga",
        "tallinn": "Europe/Tallinn",
        "vilnius": "Europe/Vilnius",
    }

    @staticmethod
    def get_config_dir() -> Path:
        """Get the configuration directory for storing user data.

        Returns:
            Path: Configuration directory path
        """
        config_dir = Path(appdirs.user_data_dir("DevBoost", "DeskRiders"))
        config_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Configuration directory: %s", config_dir)
        return config_dir

    @staticmethod
    def _get_timezone_from_datetime() -> str | None:
        """Get timezone from datetime now."""
        try:
            local_dt = datetime.now().astimezone()
            local_tz = local_dt.tzinfo
            if hasattr(local_tz, "key"):
                logger.debug("Found timezone key: %s", local_tz.key)
                return local_tz.key
            if hasattr(local_tz, "zone"):
                logger.debug("Found timezone zone: %s", local_tz.zone)
                return local_tz.zone
        except Exception:
            logger.debug("Could not determine timezone from datetime.", exc_info=True)
        return None

    @staticmethod
    def _get_timezone_from_time_module() -> str | None:
        """Get timezone from time module."""
        try:
            import time as time_module

            tz_name = time_module.tzname[time_module.daylight]
            logger.debug("Time module timezone: %s", tz_name)
            return tz_name
        except Exception:
            logger.debug("Could not determine timezone from time module.", exc_info=True)
        return None

    @staticmethod
    def _get_timezone_from_offset(local_dt: datetime) -> str | None:
        """Get timezone from offset."""
        offset = local_dt.utcoffset()
        tz_str = str(local_dt.tzinfo)
        logger.debug("Local timezone string: %s, offset: %s", tz_str, offset)
        if not offset:
            return None

        total_seconds = int(offset.total_seconds())
        hours_offset = total_seconds // 3600

        if hours_offset == 0 and ("BST" in tz_str or "GMT" in tz_str):
            return "Europe/London"
        if hours_offset == 1:
            if "BST" in tz_str or any(x in tz_str.upper() for x in ["LONDON", "BRITAIN", "UK"]):
                return "Europe/London"
            return "Europe/London"  # Default to London for +1
        if hours_offset == -5:
            return "America/New_York"
        if hours_offset == -8:
            return "America/Los_Angeles"
        if hours_offset == 9:
            return "Asia/Tokyo"
        if hours_offset in [10, 11]:
            return "Australia/Sydney"
        return None

    @staticmethod
    def _get_timezone_from_locale() -> str | None:
        """Get timezone from locale."""
        try:
            import locale

            loc = locale.getdefaultlocale()
            if loc and loc[0]:
                if loc[0].startswith("en_GB") or "GB" in loc[0]:
                    return "Europe/London"
                if loc[0].startswith("en_US") or "US" in loc[0]:
                    return "America/New_York"
        except Exception:
            logger.warning("Could not determine timezone from locale.", exc_info=True)
        return None

    @staticmethod
    def _get_timezone_from_string(tz_str: str) -> str | None:
        """Get timezone from string patterns."""
        if any(x in tz_str.upper() for x in ["GMT", "BST", "LONDON", "BRITAIN"]):
            return "Europe/London"
        return None

    @staticmethod
    def get_local_timezone() -> str:
        """Get the local system timezone identifier.

        Returns:
            Local timezone identifier (e.g., 'Europe/London')
        """
        # Method 1: Try to get timezone from datetime
        tz = TimeZoneConverter._get_timezone_from_datetime()
        if tz:
            return tz

        # Method 2: Try using time module
        tz = TimeZoneConverter._get_timezone_from_time_module()
        if tz:
            return tz

        try:
            local_dt = datetime.now().astimezone()

            # Method 3: Check for common timezone patterns
            tz = TimeZoneConverter._get_timezone_from_offset(local_dt)
            if tz:
                return tz

            # Method 4: try to detect from system locale or other methods
            tz = TimeZoneConverter._get_timezone_from_locale()
            if tz:
                return tz

            # Final fallback based on timezone string patterns
            tz_str = str(local_dt.tzinfo)
            tz = TimeZoneConverter._get_timezone_from_string(tz_str)
            if tz:
                return tz

            logger.warning("Could not determine specific timezone from %s, defaulting to UTC", tz_str)
            return "UTC"

        except Exception:
            logger.warning("Could not determine local timezone", exc_info=True)
            return "UTC"

    @staticmethod
    def get_local_city_name() -> str:
        """Get a friendly name for the local timezone.

        Returns:
            Friendly city name for local timezone
        """
        local_tz = TimeZoneConverter.get_local_timezone()

        # Map timezone to friendly city name
        tz_to_city = {
            "Europe/London": "London (Local)",
            "America/New_York": "New York (Local)",
            "America/Los_Angeles": "Los Angeles (Local)",
            "America/Chicago": "Chicago (Local)",
            "Asia/Tokyo": "Tokyo (Local)",
            "Australia/Sydney": "Sydney (Local)",
            "Europe/Paris": "Paris (Local)",
            "Europe/Berlin": "Berlin (Local)",
            "UTC": "UTC (Local)",
        }

        if local_tz in tz_to_city:
            return tz_to_city[local_tz]

        # Extract city name from timezone identifier
        if "/" in local_tz:
            city = local_tz.split("/")[-1].replace("_", " ")
            return f"{city} (Local)"

        return f"{local_tz} (Local)"

    @staticmethod
    def load_saved_cities() -> list[dict[str, Any]]:
        """Load saved cities from configuration file.

        Returns:
            List of city dictionaries with name and timezone
        """
        config_file = TimeZoneConverter.get_config_dir() / "timezone_cities.json"
        logger.info("Loading saved cities from: %s", config_file)

        if not config_file.exists():
            logger.info("No saved cities file found, returning default cities")

            # Get local timezone and add it to defaults
            local_tz = TimeZoneConverter.get_local_timezone()
            local_city_name = TimeZoneConverter.get_local_city_name()

            # Return default cities with local timezone first
            default_cities = [
                {"name": local_city_name, "timezone": local_tz},
                {"name": "New York", "timezone": "America/New_York"},
                {"name": "London", "timezone": "Europe/London"},
                {"name": "Tokyo", "timezone": "Asia/Tokyo"},
                {"name": "Sydney", "timezone": "Australia/Sydney"},
            ]

            # Remove duplicates (if local timezone matches one of the defaults)
            seen_timezones = set()
            unique_cities = []
            for city in default_cities:
                if city["timezone"] not in seen_timezones:
                    unique_cities.append(city)
                    seen_timezones.add(city["timezone"])

            TimeZoneConverter.save_cities(unique_cities)
            return unique_cities

        try:
            with config_file.open("r", encoding="utf-8") as f:
                cities = json.load(f)
            logger.info("Loaded %d saved cities", len(cities))
            return cities
        except (json.JSONDecodeError, OSError):
            logger.exception("Error loading saved cities")
            return []

    @staticmethod
    def save_cities(cities: list[dict[str, Any]]) -> None:
        """Save cities to configuration file.

        Args:
            cities: List of city dictionaries to save
        """
        config_file = TimeZoneConverter.get_config_dir() / "timezone_cities.json"
        logger.info("Saving %d cities to: %s", len(cities), config_file)

        try:
            with config_file.open("w", encoding="utf-8") as f:
                json.dump(cities, f, indent=2, ensure_ascii=False)
            logger.info("Cities saved successfully")
        except OSError:
            logger.exception("Error saving cities")

    @staticmethod
    def get_current_time_in_timezone(timezone_name: str) -> datetime | None:
        """Get current time in specified timezone.

        Args:
            timezone_name: Timezone identifier (e.g., 'America/New_York')

        Returns:
            Current datetime in the specified timezone, or None if invalid
        """
        try:
            tz = ZoneInfo(timezone_name)
            current_time = datetime.now(tz)
            logger.debug("Current time in %s: %s", timezone_name, current_time)
            return current_time
        except Exception:
            logger.exception("Error getting current time for timezone %s", timezone_name)
            return None

    @staticmethod
    def convert_time_between_zones(
        time_str: str, from_tz: str, to_tz: str, date_str: str | None = None
    ) -> datetime | None:
        """Convert time from one timezone to another.

        Args:
            time_str: Time string (e.g., '14:30', '2:30 PM', '1430')
            from_tz: Source timezone identifier
            to_tz: Target timezone identifier
            date_str: Optional date string, defaults to today

        Returns:
            Converted datetime in target timezone, or None if invalid
        """
        try:
            # Parse the time input
            parsed_time = TimeZoneConverter.parse_time_input(time_str)
            if parsed_time is None:
                logger.error("Failed to parse time input: %s", time_str)
                return None

            # Parse date if provided, otherwise use today
            if date_str:
                parsed_date = TimeZoneConverter.parse_date_input(date_str)
                if parsed_date is None:
                    logger.error("Failed to parse date input: %s", date_str)
                    return None
            else:
                parsed_date = datetime.now().date()

            # Combine date and time
            dt_naive = datetime.combine(parsed_date, parsed_time)
            logger.debug("Combined datetime: %s", dt_naive)

            # Localize to source timezone
            from_zone = ZoneInfo(from_tz)
            dt_localized = dt_naive.replace(tzinfo=from_zone)
            logger.debug("Localized to %s: %s", from_tz, dt_localized)

            # Convert to target timezone
            to_zone = ZoneInfo(to_tz)
            dt_converted = dt_localized.astimezone(to_zone)
            logger.info(
                "CONVERSION: %s %s in %s -> %s in %s",
                time_str,
                date_str or "today",
                from_tz,
                dt_converted.strftime("%H:%M %Y-%m-%d"),
                to_tz,
            )

            return dt_converted

        except Exception:
            logger.exception("Error converting time from %s to %s", from_tz, to_tz)
            return None

    @staticmethod
    def _parse_time_ampm(time_str: str) -> time | None:
        """Parse time in AM/PM format."""
        is_pm = "PM" in time_str
        time_part = time_str.replace("AM", "").replace("PM", "").strip()

        if ":" in time_part:
            hour_str, minute_str = time_part.split(":")
            hour = int(hour_str)
            minute = int(minute_str)
        else:
            hour = int(time_part)
            minute = 0

        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0

        return time(hour, minute)

    @staticmethod
    def _parse_time_24h(time_str: str) -> time | None:
        """Parse time in 24h format."""
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])
                return time(hour, minute)
        else:
            if len(time_str) in [1, 2]:
                hour = int(time_str)
                return time(hour, 0)
            if len(time_str) in [3, 4]:
                if len(time_str) == 3:
                    hour = int(time_str[0])
                    minute = int(time_str[1:3])
                else:
                    hour = int(time_str[0:2])
                    minute = int(time_str[2:4])
                return time(hour, minute)
        return None

    @staticmethod
    def parse_time_input(time_str: str) -> time | None:
        """Parse various time input formats.

        Supports:
        - HH (e.g., '14' -> 14:00)
        - HHMM (e.g., '1430' -> 14:30)
        - HH:MM (e.g., '14:30')
        - H:MM AM/PM (e.g., '2:30 PM')
        - HH AM/PM (e.g., '2 PM')

        Args:
            time_str: Time string to parse

        Returns:
            Parsed time object, or None if invalid
        """
        if not time_str or not time_str.strip():
            return None

        time_str = time_str.strip().upper()
        logger.debug("Parsing time input: '%s'", time_str)

        try:
            if "AM" in time_str or "PM" in time_str:
                return TimeZoneConverter._parse_time_ampm(time_str)
            return TimeZoneConverter._parse_time_24h(time_str)

        except (ValueError, IndexError):
            logger.exception("Error parsing time '%s'", time_str)

        return None

    @staticmethod
    def _parse_date_relative(date_str: str, today: date) -> date | None:
        """Parse relative date formats."""
        if date_str in ["today", "t"]:
            return today
        if date_str in ["tomorrow", "tm"]:
            return today + timedelta(days=1)
        if date_str.startswith("+") and date_str.endswith("d"):
            days_str = date_str[1:-1]
            days = int(days_str)
            return today + timedelta(days=days)
        return None

    @staticmethod
    def _parse_date_absolute(date_str: str, today: date) -> date | None:
        """Parse absolute date formats."""
        if not date_str.isdigit():
            return None

        if len(date_str) == 2:
            day = int(date_str)
            return today.replace(day=day)
        if len(date_str) == 4:
            month = int(date_str[:2])
            day = int(date_str[2:])
            return today.replace(month=month, day=day)
        if len(date_str) == 6:
            year = 2000 + int(date_str[:2])
            month = int(date_str[2:4])
            day = int(date_str[4:])
            return date(year, month, day)
        if len(date_str) == 8:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:])
            return date(year, month, day)
        return None

    @staticmethod
    def parse_date_input(date_str: str) -> date | None:
        """Parse various date input formats.

        Supports:
        - 'today' or 't'
        - 'tomorrow' or 'tm'
        - '+Nd' (N days from now, e.g., '+3d')
        - 'dd' (day of current month)
        - 'mmdd' (month and day)
        - 'yymmdd' (year, month, day)
        - 'yyyymmdd' (full date)

        Args:
            date_str: Date string to parse

        Returns:
            Parsed date object, or None if invalid
        """
        if not date_str or not date_str.strip():
            return None

        date_str = date_str.strip().lower()
        logger.debug("Parsing date input: '%s'", date_str)
        today = datetime.now().date()

        try:
            parsed_date = TimeZoneConverter._parse_date_relative(date_str, today)
            if parsed_date:
                return parsed_date
            return TimeZoneConverter._parse_date_absolute(date_str, today)

        except (ValueError, IndexError):
            logger.exception("Error parsing date '%s'", date_str)

        return None

    @staticmethod
    def get_timezone_for_city(city_name: str) -> str | None:
        """Get timezone identifier for a city.

        Args:
            city_name: City name to look up

        Returns:
            Timezone identifier, or None if not found
        """
        if not city_name:
            return None

        city_lower = city_name.lower().strip()
        logger.debug("Looking up timezone for city: '%s'", city_lower)

        # Check direct mapping
        if city_lower in TimeZoneConverter.CITY_TIMEZONE_MAP:
            timezone = TimeZoneConverter.CITY_TIMEZONE_MAP[city_lower]
            logger.debug("Found timezone for '%s': %s", city_name, timezone)
            return timezone

        # Check partial matches (but avoid matching empty strings)
        if city_lower:  # Only check partial matches if city_lower is not empty
            for city_key, timezone in TimeZoneConverter.CITY_TIMEZONE_MAP.items():
                if city_lower in city_key or city_key in city_lower:
                    logger.debug("Found partial match for '%s': %s", city_name, timezone)
                    return timezone

        logger.warning("No timezone found for city: '%s'", city_name)
        return None

    @staticmethod
    def search_cities(query: str) -> list[dict[str, str]]:
        """Search for cities matching query.

        Args:
            query: Search query

        Returns:
            List of matching city dictionaries
        """
        if not query or not query.strip():
            return []

        query_lower = query.lower().strip()
        logger.debug("Searching cities for query: '%s'", query_lower)

        matches = []
        for city_name, timezone in TimeZoneConverter.CITY_TIMEZONE_MAP.items():
            if query_lower in city_name:
                matches.append({
                    "name": city_name.title(),
                    "timezone": timezone,
                    "display_name": f"{city_name.title()} ({timezone})",
                })

        logger.debug("Found %d matching cities", len(matches))
        return matches

    @staticmethod
    def get_available_timezones() -> list[str]:
        """Get list of all available timezone identifiers.

        Returns:
            Sorted list of timezone identifiers
        """
        timezones = sorted(available_timezones())
        logger.debug("Found %d available timezones", len(timezones))
        return timezones

    @staticmethod
    def format_time(dt: datetime, use_24h: bool = True) -> str:
        """Format datetime for display.

        Args:
            dt: Datetime to format
            use_24h: Whether to use 24-hour format

        Returns:
            Formatted time string
        """
        if use_24h:
            return dt.strftime("%H:%M")
        return dt.strftime("%I:%M %p")

    @staticmethod
    def format_date(dt: datetime) -> str:
        """Format date for display.

        Args:
            dt: Datetime to format

        Returns:
            Formatted date string
        """
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def get_timezone_abbreviation(dt: datetime) -> str:
        """Get timezone abbreviation for datetime.

        Args:
            dt: Datetime with timezone info

        Returns:
            Timezone abbreviation (e.g., 'EST', 'PST')
        """
        return dt.strftime("%Z")


class TimeZoneConverterUI:
    def __init__(self, converter_widget: QWidget, scratch_pad: QWidget | None):
        self.converter_widget = converter_widget
        self.scratch_pad = scratch_pad
        self.converter = TimeZoneConverter()
        self.saved_cities = self.converter.load_saved_cities()
        self.use_24h_format = True

        self.input_section, self.input_widgets = self._create_input_section()
        self.results_section, self.results_widgets = self._create_results_section()

        main_layout = QVBoxLayout(self.converter_widget)
        main_layout.setContentsMargins(10, 5, 5, 10)
        main_layout.setSpacing(5)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.converter_widget.setStyleSheet(get_tool_style())

        main_layout.addWidget(self.input_section)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.results_section)

        self._connect_signals()
        self.update_results()

    def _create_input_section(self) -> tuple[QWidget, dict[str, QWidget]]:
        """Create the input section of the timezone converter widget."""
        input_section = QWidget()
        input_section_layout = QVBoxLayout(input_section)
        input_section_layout.setSpacing(3)

        top_controls_layout = QHBoxLayout()
        top_controls_layout.setSpacing(5)

        now_button = QPushButton("Now")
        clipboard_button = QPushButton("Clipboard")
        clear_button = QPushButton("Clear")
        format_toggle_button = QPushButton("24h")
        format_toggle_button.setCheckable(True)
        format_toggle_button.setChecked(True)

        send_to_scratch_pad_button = None
        if self.scratch_pad:
            send_to_scratch_pad_button = QPushButton("Send to Scratch Pad")
            logger.info("Scratch pad integration enabled")

        top_controls_layout.addWidget(now_button)
        top_controls_layout.addWidget(clipboard_button)
        top_controls_layout.addWidget(clear_button)
        top_controls_layout.addWidget(format_toggle_button)
        if send_to_scratch_pad_button:
            top_controls_layout.addWidget(send_to_scratch_pad_button)
        top_controls_layout.addStretch()

        input_fields_layout = QHBoxLayout()
        input_fields_layout.setSpacing(5)

        time_input = QLineEdit()
        time_input.setPlaceholderText("Enter time (e.g., 14:30, 2:30 PM, 1430)")

        date_input = QLineEdit()
        date_input.setPlaceholderText("Date (optional: today, +1d, 0315)")
        date_input.setFixedWidth(200)

        source_city_combo = QComboBox()
        source_city_combo.setEditable(True)
        source_city_combo.setPlaceholderText("Source city (optional)")
        source_city_combo.setFixedWidth(200)

        for city in self.saved_cities:
            source_city_combo.addItem(city["name"], city["timezone"])

        input_fields_layout.addWidget(QLabel("Time:"))
        input_fields_layout.addWidget(time_input)
        input_fields_layout.addWidget(QLabel("Date:"))
        input_fields_layout.addWidget(date_input)
        input_fields_layout.addWidget(QLabel("From:"))
        input_fields_layout.addWidget(source_city_combo)

        tips_label = QLabel("Formats: 14:30, 2:30 PM | Dates: today, +3d")
        tips_label.setObjectName("tipsLabel")
        tips_label.setWordWrap(False)
        tips_label.setMaximumHeight(20)

        input_section_layout.addLayout(top_controls_layout)
        input_section_layout.addLayout(input_fields_layout)
        input_section_layout.addWidget(tips_label)

        widgets = {
            "now_button": now_button,
            "clipboard_button": clipboard_button,
            "clear_button": clear_button,
            "format_toggle_button": format_toggle_button,
            "send_to_scratch_pad_button": send_to_scratch_pad_button,
            "time_input": time_input,
            "date_input": date_input,
            "source_city_combo": source_city_combo,
        }
        return input_section, widgets

    def _create_results_section(self) -> tuple[QWidget, dict[str, QWidget]]:
        """Create the results section of the timezone converter widget."""
        results_section = QWidget()
        results_layout = QVBoxLayout(results_section)
        results_layout.setSpacing(5)

        results_header_layout = QHBoxLayout()
        results_label = QLabel("Time Conversions")
        results_label.setObjectName("sectionHeader")

        add_city_button = QPushButton("+ Add City")

        results_header_layout.addWidget(results_label)
        results_header_layout.addStretch()
        results_header_layout.addWidget(add_city_button)

        results_layout.addLayout(results_header_layout)

        results_list = QListWidget()
        results_list.setMinimumHeight(300)
        results_list.setMaximumHeight(600)
        results_list.setSpacing(10)
        results_list.setContentsMargins(0, 0, 0, 0)

        results_layout.addWidget(results_list)

        widgets = {"add_city_button": add_city_button, "results_list": results_list}
        return results_section, widgets

    def _connect_signals(self):
        """Connect widget signals to slots."""
        self.input_widgets["now_button"].clicked.connect(self.set_current_time)
        self.input_widgets["clipboard_button"].clicked.connect(self.paste_from_clipboard)
        self.input_widgets["clear_button"].clicked.connect(self.clear_inputs)
        self.input_widgets["format_toggle_button"].clicked.connect(self.toggle_format)

        self.input_widgets["time_input"].textChanged.connect(self.update_results)
        self.input_widgets["date_input"].textChanged.connect(self.update_results)
        self.input_widgets["source_city_combo"].currentTextChanged.connect(self.update_results)

        self.results_widgets["add_city_button"].clicked.connect(self.show_add_city_dialog)

        if self.input_widgets["send_to_scratch_pad_button"]:
            self.input_widgets["send_to_scratch_pad_button"].clicked.connect(self.send_to_scratch_pad_func)

    def create_city_item_widget(self, city, time_str, date_str, tz_abbr, converted_time=None):
        """Create a custom widget for a city list item."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 1, 5, 1)
        item_layout.setSpacing(8)

        city_label = QLabel(city["name"])
        city_label.setObjectName("cityName")
        city_label.setFixedWidth(100)

        time_label = QLabel(time_str)
        time_label.setObjectName("timeValue")
        time_label.setFixedWidth(60)

        date_label = QLabel(date_str)
        date_label.setObjectName("dateValue")
        date_label.setFixedWidth(80)

        tz_label = QLabel(f"({tz_abbr})")
        tz_label.setObjectName("timezoneAbbr")
        tz_label.setFixedWidth(50)

        copy_button = QPushButton("Copy")
        copy_button.setFixedSize(45, 16)
        copy_button.setStyleSheet("QPushButton { padding: 1px; font-size: 10px; }")

        delete_button = QPushButton("x")
        delete_button.setFixedSize(16, 16)
        delete_button.setStyleSheet("QPushButton { color: red; font-weight: bold; padding: 0px; font-size: 10px; }")
        delete_button.setToolTip(f"Remove {city['name']}")

        if len(self.saved_cities) <= 1:
            delete_button.setEnabled(False)
            delete_button.setToolTip("Cannot remove the last city")

        item_layout.addWidget(city_label)
        item_layout.addWidget(time_label)
        item_layout.addWidget(date_label)
        item_layout.addWidget(tz_label)
        item_layout.addStretch()
        item_layout.addWidget(copy_button)
        item_layout.addWidget(delete_button)

        item_widget.setFixedHeight(20)

        if converted_time or time_str != "Error":
            copy_text = f"{city['name']}: {time_str} {date_str} {tz_abbr}"
            copy_button.clicked.connect(lambda: QApplication.clipboard().setText(copy_text))
        else:
            copy_button.setEnabled(False)

        delete_button.clicked.connect(lambda: self.delete_city_from_row(city))

        return item_widget

    def update_results(self):
        """Update the results list with current time conversions."""
        logger.info("Updating timezone conversion results")
        results_list = self.results_widgets["results_list"]
        results_list.clear()

        time_text = self.input_widgets["time_input"].text().strip()
        date_text = self.input_widgets["date_input"].text().strip()
        source_city = self.input_widgets["source_city_combo"].currentText().strip()

        if not time_text:
            self._show_current_times()
        else:
            self._show_converted_times(time_text, date_text, source_city)

        logger.info("Results list updated successfully")

    def _show_current_times(self):
        """Display current times for all saved cities."""
        logger.debug("No time input, showing current times")
        for city in self.saved_cities:
            current_time = self.converter.get_current_time_in_timezone(city["timezone"])
            if current_time:
                time_str = self.converter.format_time(current_time, self.use_24h_format)
                date_str = self.converter.format_date(current_time)
                tz_abbr = self.converter.get_timezone_abbreviation(current_time)

                item_widget = self.create_city_item_widget(city, time_str, date_str, tz_abbr, current_time)
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                self.results_widgets["results_list"].addItem(list_item)
                self.results_widgets["results_list"].setItemWidget(list_item, item_widget)

                logger.debug(
                    "Current time in %s (%s): %s %s %s",
                    city["name"],
                    city["timezone"],
                    time_str,
                    date_str,
                    tz_abbr,
                )

    def _show_converted_times(self, time_text: str, date_text: str, source_city: str):
        """Display converted times for all saved cities."""
        logger.debug("Converting time: %s, date: %s, from: %s", time_text, date_text, source_city)
        source_tz = self._get_source_timezone(source_city)

        logger.info("Using source timezone: %s for conversion from time: %s", source_tz, time_text)

        for city in self.saved_cities:
            converted_time = self.converter.convert_time_between_zones(
                time_text, source_tz, city["timezone"], date_text
            )

            if converted_time:
                time_str = self.converter.format_time(converted_time, self.use_24h_format)
                date_str = self.converter.format_date(converted_time)
                tz_abbr = self.converter.get_timezone_abbreviation(converted_time)

                logger.debug(
                    "Converted %s from %s to %s: %s %s %s",
                    time_text,
                    source_tz,
                    city["timezone"],
                    time_str,
                    date_str,
                    tz_abbr,
                )
            else:
                time_str = "Error"
                date_str = "--"
                tz_abbr = "--"
                logger.error("Failed to convert %s from %s to %s", time_text, source_tz, city["timezone"])

            item_widget = self.create_city_item_widget(city, time_str, date_str, tz_abbr, converted_time)
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            self.results_widgets["results_list"].addItem(list_item)
            self.results_widgets["results_list"].setItemWidget(list_item, item_widget)

    def _get_source_timezone(self, source_city: str) -> str:
        """Determine the source timezone from the input."""
        if not source_city:
            logger.debug("No source city specified, using UTC")
            return "UTC"

        for city in self.saved_cities:
            if city["name"].lower() == source_city.lower():
                source_tz = city["timezone"]
                logger.debug("Found source timezone from saved cities: %s for %s", source_tz, source_city)
                return source_tz

        source_tz = self.converter.get_timezone_for_city(source_city)
        if source_tz:
            logger.debug("Found source timezone from city mapping: %s for %s", source_tz, source_city)
            return source_tz

        logger.warning("Could not find timezone for %s, using UTC as fallback", source_city)
        return "UTC"

    def delete_city_from_row(self, city_data: dict[str, Any]):
        """Delete a city from the saved cities list."""
        if len(self.saved_cities) <= 1:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(
                self.converter_widget, "Cannot Remove City", "You must have at least one city in the list."
            )
            return

        for i, city in enumerate(self.saved_cities):
            if city["name"] == city_data["name"] and city["timezone"] == city_data["timezone"]:
                removed_city = self.saved_cities.pop(i)
                self.converter.save_cities(self.saved_cities)

                source_city_combo = self.input_widgets["source_city_combo"]
                for j in range(source_city_combo.count()):
                    if source_city_combo.itemText(j) == removed_city["name"]:
                        source_city_combo.removeItem(j)
                        break

                logger.info("Removed city: %s", removed_city["name"])
                self.update_results()
                break

    def toggle_format(self):
        """Toggle between 12h and 24h time format."""
        self.use_24h_format = not self.use_24h_format
        self.input_widgets["format_toggle_button"].setText("24h" if self.use_24h_format else "12h")
        logger.info("Time format toggled to: %s", "24h" if self.use_24h_format else "12h")
        self.update_results()

    def clear_inputs(self):
        """Clear all input fields."""
        logger.info("Clearing all input fields")
        self.input_widgets["time_input"].clear()
        self.input_widgets["date_input"].clear()
        self.input_widgets["source_city_combo"].setCurrentIndex(-1)
        self.update_results()

    def set_current_time(self):
        """Set current time in the time input and detect local timezone."""
        current_time = datetime.now()
        time_str = self.converter.format_time(current_time, True)
        self.input_widgets["time_input"].setText(time_str)

        try:
            local_tz = self.converter.get_local_timezone()
            logger.debug("Detected local timezone: %s", local_tz)

            source_city_combo = self.input_widgets["source_city_combo"]
            local_city_found = False
            for i in range(source_city_combo.count()):
                city_tz = source_city_combo.itemData(i)
                city_name = source_city_combo.itemText(i)

                if city_tz == local_tz or "(Local)" in city_name:
                    source_city_combo.setCurrentIndex(i)
                    local_city_found = True
                    logger.debug("Set source city to: %s", city_name)
                    break

            if not local_city_found:
                logger.warning("Local timezone %s not found in saved cities", local_tz)

        except Exception:
            logger.warning("Could not detect local timezone", exc_info=True)

        logger.info("Set current time: %s with local timezone as source", time_str)
        self.update_results()

    def paste_from_clipboard(self):
        """Paste time from clipboard."""
        clipboard_text = QApplication.clipboard().text().strip()
        if clipboard_text:
            self.input_widgets["time_input"].setText(clipboard_text)
            logger.info("Pasted from clipboard: %s", clipboard_text)
            self.update_results()

    def show_add_city_dialog(self):
        """Show a simple dialog to add a city."""
        from PyQt6.QtWidgets import QInputDialog

        city_name, ok = QInputDialog.getText(
            self.converter_widget, "Add City", "Enter city name (e.g., Paris, Tokyo, Sydney):"
        )

        if ok and city_name.strip():
            city_name = city_name.strip()
            logger.info("User wants to add city: %s", city_name)

            timezone = self.converter.get_timezone_for_city(city_name)

            if timezone:
                for existing_city in self.saved_cities:
                    if existing_city["timezone"] == timezone:
                        logger.warning("City with timezone %s already exists", timezone)
                        return

                new_city = {"name": city_name.title(), "timezone": timezone}
                self.saved_cities.append(new_city)
                self.converter.save_cities(self.saved_cities)

                source_city_combo = self.input_widgets["source_city_combo"]
                source_city_combo.addItem(new_city["name"], new_city["timezone"])

                logger.info("Added city: %s (%s)", new_city["name"], timezone)
                self.update_results()
            else:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self.converter_widget,
                    "City Not Found",
                    f"Could not find timezone information for '{city_name}'.\n\n"
                    "Try using a major city name like:\n"
                    "• London, Paris, Berlin\n"
                    "• New York, Los Angeles, Chicago\n"
                    "• Tokyo, Sydney, Mumbai",
                )

    def send_to_scratch_pad_func(self):
        """Send current results to scratch pad."""
        if not self.scratch_pad:
            return

        logger.info("Sending timezone results to scratch pad")

        results_text = "TimeZone Conversion Results\n"
        results_text += "=" * 30 + "\n\n"

        time_text = self.input_widgets["time_input"].text().strip()
        date_text = self.input_widgets["date_input"].text().strip()
        source_city = self.input_widgets["source_city_combo"].currentText().strip()

        if time_text:
            results_text += f"Input Time: {time_text}\n"
            if date_text:
                results_text += f"Input Date: {date_text}\n"
            if source_city:
                results_text += f"Source City: {source_city}\n"
            results_text += "\n"
        else:
            results_text += "Current Times:\n\n"

        for city in self.saved_cities:
            if time_text:
                source_tz = self._get_source_timezone(source_city)
                converted_time = self.converter.convert_time_between_zones(
                    time_text, source_tz, city["timezone"], date_text
                )
            else:
                converted_time = self.converter.get_current_time_in_timezone(city["timezone"])

            if converted_time:
                time_str = self.converter.format_time(converted_time, self.use_24h_format)
                date_str = self.converter.format_date(converted_time)
                tz_abbr = self.converter.get_timezone_abbreviation(converted_time)
                results_text += f"{city['name']}: {time_str} {date_str} ({tz_abbr})\n"

        self.scratch_pad.set_content(
            self.scratch_pad.get_content() + "\n\n" + results_text if self.scratch_pad.get_content() else results_text
        )
        logger.info("Results sent to scratch pad successfully")


def create_timezone_converter_widget(style_func, scratch_pad=None):
    """Create and return the TimeZone Converter widget."""
    converter_widget = QWidget()
    TimeZoneConverterUI(converter_widget, scratch_pad)
    return converter_widget
