import calendar
import datetime
import logging
import re
import time
import zoneinfo

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style

logger = logging.getLogger(__name__)


class UnixTimeConverter:
    """Backend logic for Unix timestamp conversion."""

    @staticmethod
    def parse_input(input_text: str) -> float | None:
        """Parse input text and evaluate mathematical expressions.

        Args:
            input_text: Input string that may contain numbers and math operators

        Returns:
            Parsed number as float or None if invalid
        """
        if not input_text.strip():
            return None

        # Remove whitespace
        input_text = input_text.strip()

        # Check if it's a simple number
        try:
            return float(input_text)
        except ValueError:
            pass

        # Check for mathematical expressions (only allow safe operations)
        if re.match(r"^[0-9+\-*/().\s]+$", input_text):
            try:
                # Use eval with restricted globals for safety
                result = eval(input_text, {"__builtins__": {}}, {})  # noqa: S307
                return float(result)
            except (ValueError, SyntaxError, ZeroDivisionError):
                return None

        return None

    @staticmethod
    def unix_to_datetime(timestamp: float) -> datetime.datetime:
        """Convert Unix timestamp to datetime object.

        Args:
            timestamp: Unix timestamp (seconds since epoch)

        Returns:
            datetime object in UTC
        """
        return datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)

    @staticmethod
    def unix_to_local_datetime(timestamp: float) -> datetime.datetime:
        """Convert Unix timestamp to local datetime object.

        Args:
            timestamp: Unix timestamp (seconds since epoch)

        Returns:
            datetime object in local timezone
        """
        return datetime.datetime.fromtimestamp(timestamp)

    @staticmethod
    def format_local_time(dt: datetime.datetime) -> str:
        """Format datetime as local time string.

        Args:
            dt: datetime object

        Returns:
            Formatted local time string
        """
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

    @staticmethod
    def format_utc_iso(dt: datetime.datetime) -> str:
        """Format datetime as UTC ISO 8601 string.

        Args:
            dt: datetime object in UTC

        Returns:
            ISO 8601 formatted string
        """
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    @staticmethod
    def format_relative_time(timestamp: float) -> str:
        """Format timestamp as relative time (e.g., '2 hours ago').

        Args:
            timestamp: Unix timestamp

        Returns:
            Relative time string
        """
        now = time.time()
        diff = now - timestamp

        if abs(diff) < 60:
            return "Just now"
        elif abs(diff) < 3600:
            minutes = int(abs(diff) / 60)
            suffix = "ago" if diff > 0 else "from now"
            return f"{minutes} minute{'s' if minutes != 1 else ''} {suffix}"
        elif abs(diff) < 86400:
            hours = int(abs(diff) / 3600)
            suffix = "ago" if diff > 0 else "from now"
            return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"
        else:
            days = int(abs(diff) / 86400)
            suffix = "ago" if diff > 0 else "from now"
            return f"{days} day{'s' if days != 1 else ''} {suffix}"

    @staticmethod
    def get_day_of_year(dt: datetime.datetime) -> int:
        """Get day of year for given datetime.

        Args:
            dt: datetime object

        Returns:
            Day of year (1-366)
        """
        return dt.timetuple().tm_yday

    @staticmethod
    def get_week_of_year(dt: datetime.datetime) -> int:
        """Get week of year for given datetime.

        Args:
            dt: datetime object

        Returns:
            Week of year (1-53)
        """
        return dt.isocalendar()[1]

    @staticmethod
    def is_leap_year(dt: datetime.datetime) -> bool:
        """Check if the year is a leap year.

        Args:
            dt: datetime object

        Returns:
            True if leap year, False otherwise
        """
        return calendar.isleap(dt.year)

    @staticmethod
    def get_current_timestamp() -> float:
        """Get current Unix timestamp.

        Returns:
            Current Unix timestamp
        """
        return time.time()

    @staticmethod
    def unix_to_timezone_datetime(timestamp: float, timezone_name: str) -> datetime.datetime | None:
        """Convert Unix timestamp to datetime in specified timezone.

        Args:
            timestamp: Unix timestamp (seconds since epoch)
            timezone_name: Timezone name (e.g., 'America/New_York', 'Europe/London')

        Returns:
            datetime object in specified timezone or None if timezone is invalid
        """
        try:
            tz = zoneinfo.ZoneInfo(timezone_name)
            return datetime.datetime.fromtimestamp(timestamp, tz=tz)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError):
            return None

    @staticmethod
    def get_common_timezones() -> list[str]:
        """Get list of common timezone names.

        Returns:
            List of common timezone identifiers
        """
        return [
            "UTC",
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Kolkata",
            "Australia/Sydney",
            "Pacific/Auckland",
        ]


# ruff: noqa: C901
def create_unix_time_converter_widget(style_func):
    """Create and return the Unix Time Converter widget.

    Args:
        style_func: Function to get QStyle for standard icons

    Returns:
        QWidget: The complete Unix Time Converter widget
    """
    logger.info("Starting Unix Time Converter widget creation")
    converter_widget = QWidget()
    main_layout = QVBoxLayout(converter_widget)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(15)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    converter_widget.setStyleSheet(get_tool_style())
    logger.info("Main layout configured for Unix Time Converter")

    # Initialize converter backend
    converter = UnixTimeConverter()

    # --- Input Section ---
    input_section_layout = QVBoxLayout()
    input_section_layout.setSpacing(8)

    top_controls_layout = QHBoxLayout()
    top_controls_layout.setSpacing(8)

    # Create buttons with functionality
    now_button = QPushButton("Now")
    clipboard_button = QPushButton("Clipboard")
    clear_button = QPushButton("Clear")

    top_controls_layout.addWidget(now_button)
    top_controls_layout.addWidget(clipboard_button)
    top_controls_layout.addWidget(clear_button)
    top_controls_layout.addStretch()

    input_fields_layout = QHBoxLayout()
    input_fields_layout.setSpacing(8)

    input_line_edit = QLineEdit()

    time_unit_combo = QComboBox()
    time_unit_combo.addItem("Unix time (seconds since epoch)")
    time_unit_combo.setFixedWidth(250)

    input_fields_layout.addWidget(input_line_edit)
    input_fields_layout.addWidget(time_unit_combo)

    tips_label = QLabel("Tips: Mathematical operators + - * / are supported")
    tips_label.setObjectName("tipsLabel")

    input_section_layout.addLayout(top_controls_layout)
    input_section_layout.addLayout(input_fields_layout)
    input_section_layout.addWidget(tips_label)

    main_layout.addLayout(input_section_layout)

    # --- Separator ---
    separator1 = QFrame()
    separator1.setFrameShape(QFrame.Shape.HLine)
    separator1.setFrameShadow(QFrame.Shadow.Sunken)
    main_layout.addWidget(separator1)

    # --- Results Section ---
    results_grid = QGridLayout()
    results_grid.setSpacing(15)

    # Helper to create an output field with a copy button
    def create_output_field():
        field_widget = QWidget()
        field_layout = QHBoxLayout(field_widget)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(4)
        line_edit = QLineEdit()
        line_edit.setReadOnly(True)
        field_layout.addWidget(line_edit)
        copy_button = QPushButton()
        copy_button.setObjectName("iconButton")
        # Image description: A copy icon. Two overlapping squares. Black outlines.
        copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))  # Placeholder

        # Connect copy button to copy text to clipboard
        def copy_to_clipboard():
            clipboard = QApplication.clipboard()
            clipboard.setText(line_edit.text())

        copy_button.clicked.connect(copy_to_clipboard)

        field_layout.addWidget(copy_button)
        return field_widget, line_edit

    # Create output fields and store references
    local_field, local_output = create_output_field()
    day_of_year_field, day_of_year_output = create_output_field()
    other_formats_1_field, other_formats_1_output = create_output_field()

    utc_field, utc_output = create_output_field()
    week_of_year_field, week_of_year_output = create_output_field()
    other_formats_2_field, other_formats_2_output = create_output_field()

    relative_field, relative_output = create_output_field()
    leap_year_field, leap_year_output = create_output_field()
    other_formats_3_field, other_formats_3_output = create_output_field()

    unix_time_field, unix_time_output = create_output_field()
    other_formats_4_field, other_formats_4_output = create_output_field()

    # Grid items
    results_grid.addWidget(QLabel("Local:"), 0, 0)
    results_grid.addWidget(local_field, 0, 1)
    results_grid.addWidget(QLabel("Day of year"), 0, 2)
    results_grid.addWidget(day_of_year_field, 0, 3)
    results_grid.addWidget(QLabel("Other formats (local)"), 0, 4)
    results_grid.addWidget(other_formats_1_field, 0, 5)

    results_grid.addWidget(QLabel("UTC (ISO 8601):"), 1, 0)
    results_grid.addWidget(utc_field, 1, 1)
    results_grid.addWidget(QLabel("Week of year"), 1, 2)
    results_grid.addWidget(week_of_year_field, 1, 3)
    results_grid.addWidget(other_formats_2_field, 1, 5)

    results_grid.addWidget(QLabel("Relative:"), 2, 0)
    results_grid.addWidget(relative_field, 2, 1)
    results_grid.addWidget(QLabel("Is leap year?"), 2, 2)
    results_grid.addWidget(leap_year_field, 2, 3)
    results_grid.addWidget(other_formats_3_field, 2, 5)

    results_grid.addWidget(QLabel("Unix time:"), 3, 0)
    results_grid.addWidget(unix_time_field, 3, 1)
    results_grid.addWidget(other_formats_4_field, 3, 5)

    results_grid.setColumnStretch(1, 1)
    results_grid.setColumnStretch(3, 1)
    results_grid.setColumnStretch(5, 1)

    main_layout.addLayout(results_grid)

    # --- Separator ---
    separator2 = QFrame()
    separator2.setFrameShape(QFrame.Shape.HLine)
    separator2.setFrameShadow(QFrame.Shadow.Sunken)
    main_layout.addWidget(separator2)

    # --- Timezone Section ---
    timezone_section_layout = QVBoxLayout()
    timezone_section_layout.setSpacing(8)

    timezone_controls_layout = QHBoxLayout()
    timezone_controls_layout.setSpacing(8)

    timezone_controls_layout.addWidget(QLabel("Other timezones:"))
    tz_combo = QComboBox()
    tz_combo.setEditable(True)
    tz_combo.lineEdit().setPlaceholderText("Add timezone...")

    # Populate with common timezones
    common_timezones = converter.get_common_timezones()
    for tz in common_timezones:
        tz_combo.addItem(tz)

    timezone_controls_layout.addWidget(tz_combo, 1)
    add_tz_button = QPushButton("Add")
    timezone_controls_layout.addWidget(add_tz_button)

    timezone_section_layout.addLayout(timezone_controls_layout)

    # Container for timezone displays
    timezone_displays_layout = QVBoxLayout()
    timezone_displays = []  # Store timezone display widgets

    tz_info_label = QLabel("(Pick a timezone to get started...)")
    tz_info_label.setObjectName("tipsLabel")
    timezone_section_layout.addWidget(tz_info_label)
    timezone_section_layout.addLayout(timezone_displays_layout)

    main_layout.addLayout(timezone_section_layout)

    main_layout.addStretch()  # Push everything up

    # --- Conversion Logic ---
    def update_conversion():
        """Update all conversion fields based on input."""
        input_text = input_line_edit.text()
        timestamp = converter.parse_input(input_text)

        if timestamp is None:
            # Clear all fields if input is invalid
            local_output.setText("")
            utc_output.setText("")
            relative_output.setText("")
            unix_time_output.setText("")
            day_of_year_output.setText("")
            week_of_year_output.setText("")
            leap_year_output.setText("")
            other_formats_1_output.setText("")
            other_formats_2_output.setText("")
            other_formats_3_output.setText("")
            other_formats_4_output.setText("")
            return

        try:
            # Convert timestamp to datetime objects
            utc_dt = converter.unix_to_datetime(timestamp)
            local_dt = converter.unix_to_local_datetime(timestamp)

            # Update all fields
            local_output.setText(converter.format_local_time(local_dt))
            utc_output.setText(converter.format_utc_iso(utc_dt))
            relative_output.setText(converter.format_relative_time(timestamp))
            unix_time_output.setText(str(int(timestamp)))

            day_of_year_output.setText(str(converter.get_day_of_year(local_dt)))
            week_of_year_output.setText(str(converter.get_week_of_year(local_dt)))
            leap_year_output.setText("Yes" if converter.is_leap_year(local_dt) else "No")

            # Additional formats
            other_formats_1_output.setText(local_dt.strftime("%A, %B %d, %Y"))
            other_formats_2_output.setText(utc_dt.strftime("%Y-%m-%d %H:%M:%S UTC"))
            other_formats_3_output.setText(local_dt.strftime("%I:%M %p"))
            other_formats_4_output.setText(f"{timestamp:.3f}")

            # Update timezone displays
            update_timezone_displays(timestamp)

        except (ValueError, OSError):
            logger.exception(f"Error converting timestamp {timestamp}")
            # Clear fields on error
            for output in [
                local_output,
                utc_output,
                relative_output,
                unix_time_output,
                day_of_year_output,
                week_of_year_output,
                leap_year_output,
                other_formats_1_output,
                other_formats_2_output,
                other_formats_3_output,
                other_formats_4_output,
            ]:
                output.setText("Invalid timestamp")
            # Clear timezone displays
            for tz_data in timezone_displays:
                tz_data["output"].setText("Invalid timestamp")

    # --- Timezone Functions ---
    def add_timezone_display(timezone_name: str):
        """Add a new timezone display widget."""
        if timezone_name in [tz_data["name"] for tz_data in timezone_displays]:
            return  # Already exists

        # Create timezone display widget
        tz_widget = QWidget()
        tz_layout = QHBoxLayout(tz_widget)
        tz_layout.setContentsMargins(0, 0, 0, 0)
        tz_layout.setSpacing(8)

        tz_label = QLabel(f"{timezone_name}:")
        tz_label.setMinimumWidth(150)
        tz_output = QLineEdit()
        tz_output.setReadOnly(True)

        copy_button = QPushButton()
        copy_button.setObjectName("iconButton")
        copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))

        remove_button = QPushButton()
        remove_button.setObjectName("iconButton")
        remove_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))

        # Connect copy button
        def copy_tz_to_clipboard():
            clipboard = QApplication.clipboard()
            clipboard.setText(tz_output.text())

        copy_button.clicked.connect(copy_tz_to_clipboard)

        # Connect remove button
        def remove_timezone():
            timezone_displays_layout.removeWidget(tz_widget)
            tz_widget.deleteLater()
            # Remove from timezone_displays list
            timezone_displays[:] = [tz for tz in timezone_displays if tz["name"] != timezone_name]
            if not timezone_displays:
                tz_info_label.setText("(Pick a timezone to get started...)")
                tz_info_label.show()

        remove_button.clicked.connect(remove_timezone)

        tz_layout.addWidget(tz_label)
        tz_layout.addWidget(tz_output, 1)
        tz_layout.addWidget(copy_button)
        tz_layout.addWidget(remove_button)

        timezone_displays_layout.addWidget(tz_widget)
        timezone_displays.append({"name": timezone_name, "widget": tz_widget, "output": tz_output})

        # Hide the info label when we have timezones
        tz_info_label.hide()

    def update_timezone_displays(timestamp: float):
        """Update all timezone displays with the given timestamp."""
        for tz_data in timezone_displays:
            tz_dt = converter.unix_to_timezone_datetime(timestamp, tz_data["name"])
            if tz_dt:
                formatted_time = tz_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
                tz_data["output"].setText(formatted_time)
            else:
                tz_data["output"].setText("Invalid timezone")

    # --- Event Handlers ---
    def on_now_clicked():
        """Set input to current timestamp."""
        current_timestamp = converter.get_current_timestamp()
        input_line_edit.setText(str(int(current_timestamp)))
        update_conversion()

    def on_clipboard_clicked():
        """Set input from clipboard."""
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text().strip()
        if clipboard_text:
            input_line_edit.setText(clipboard_text)
            update_conversion()

    def on_clear_clicked():
        """Clear input and all outputs."""
        input_line_edit.clear()
        update_conversion()

    def on_add_timezone_clicked():
        """Add selected timezone to displays."""
        timezone_name = tz_combo.currentText().strip()
        if timezone_name:
            add_timezone_display(timezone_name)
            # Update with current timestamp if available
            input_text = input_line_edit.text()
            timestamp = converter.parse_input(input_text)
            if timestamp is not None:
                update_timezone_displays(timestamp)

    # Connect event handlers
    now_button.clicked.connect(on_now_clicked)
    clipboard_button.clicked.connect(on_clipboard_clicked)
    clear_button.clicked.connect(on_clear_clicked)
    add_tz_button.clicked.connect(on_add_timezone_clicked)
    input_line_edit.textChanged.connect(update_conversion)

    # Initialize with current time
    on_now_clicked()

    logger.info("Unix Time Converter widget creation completed successfully")
    return converter_widget
