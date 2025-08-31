# TimeZone Tool Requirements Analysis

## Overview

This document analyzes the requirements for implementing a comprehensive TimeZone conversion tool for DevBoost, inspired by Alfred's timezone workflow. The tool will provide timezone conversions, city time lookups, and time calculations across different timezones.

## Current DevBoost Architecture Analysis

### Tool Integration Pattern

1. **Backend Logic Class**: Each tool has a backend class with static methods (e.g., `UnixTimeConverter`)
2. **Widget Creation Function**: Each tool exports a `create_*_widget(style_func, scratch_pad=None)` function
3. **Tool Registration**: Tools are registered in three places:
   - `devboost/tools/__init__.py` - Import and export the create function
   - `devboost/main.py` - Add to tools list with icon, name, and keywords
   - `devboost/main.py` - Add screen creation and navigation logic

### Existing Dependencies

- `PyQt6` - GUI framework
- `requests` - HTTP requests (already available)
- `appdirs` - User data directory management
- `zoneinfo` - Python 3.9+ built-in timezone functionality

## Core Features Required (Based on Alfred Workflow)

### 1. Current Time Display

- Show current time for saved cities
- Support for hotkey/search access
- Display multiple cities simultaneously

### 2. Time Conversion

- Convert specific times (HH, HHMM, HH:MM formats)
- Convert to all saved cities
- Support for AM/PM and 24-hour formats

### 3. City Search and Management

- Search for cities in saved list
- Show current time for searched cities
- Add/remove cities from saved list
- Persistent city configuration

### 4. Date/Time Parsing

- Support relative dates:
  - `today` or `t`
  - `tomorrow` or `tm`
  - `+Nd` (N days from now)
- Support absolute dates:
  - `dd` (day of current month)
  - `mmdd` (month and day)
  - `yymmdd` (year, month, day)
  - `yyyymmdd` (full date)

### 5. Source City Conversion

- Convert time from specific source city to other cities
- Support "time in [city]" queries

### 6. Format Options

- Toggle between 12h/24h time formats
- Configurable date formats
- Time zone abbreviation display

### 7. Configuration Management

- Cities file management in user data directory
- JSON-based configuration
- Import/export capabilities

## Technical Architecture

### Backend Logic (`TimeZoneConverter` class)

```python
class TimeZoneConverter:
    @staticmethod
    def get_current_time_in_timezone(timezone_name: str) -> datetime:
        """Get current time in specified timezone."""

    @staticmethod
    def convert_time_between_zones(time_str: str, from_tz: str, to_tz: str) -> datetime:
        """Convert time from one timezone to another."""

    @staticmethod
    def parse_time_input(input_str: str) -> tuple[datetime, str]:
        """Parse various time input formats."""

    @staticmethod
    def get_timezone_for_city(city_name: str) -> str:
        """Get timezone identifier for a city."""

    @staticmethod
    def search_cities(query: str) -> list[dict]:
        """Search for cities matching query."""
```

### UI Components (PyQt6)

1. **Input Section**:

   - Time/date input field with format hints
   - Source city selection dropdown
   - Format toggle (12h/24h)

2. **Results Section**:

   - Grid display of converted times for saved cities
   - City name, local time, timezone abbreviation
   - Visual indicators for different days

3. **City Management**:

   - Add/remove cities interface
   - Search functionality
   - Drag-and-drop reordering

4. **Settings Panel**:
   - Format preferences
   - Default cities configuration
   - Import/export options

### File Structure

```
devboost/tools/timezone_converter.py  # Main implementation
tests/test_timezone_converter.py      # Test suite
```

### Data Management

- **Cities Configuration**: JSON file in user data directory
- **City Database**: Built-in city-to-timezone mappings
- **Timezone Data**: Python's `zoneinfo` module

### Integration Points

1. Add import in `devboost/tools/__init__.py`
2. Register in main application tools list with icon 🌍
3. Add screen creation in `main.py`
4. Add navigation logic in `_on_tool_selected`
5. Create comprehensive test coverage

## Implementation Approach

### Phase 1: Core Backend Logic

- Implement `TimeZoneConverter` class
- Basic timezone conversion functionality
- Time parsing utilities
- City-timezone mapping

### Phase 2: Basic UI

- Create widget with input/output sections
- Implement time conversion display
- Basic city management

### Phase 3: Advanced Features

- Relative date parsing
- Configuration persistence
- Advanced city search
- Format customization

### Phase 4: Polish and Integration

- Scratch pad integration
- Comprehensive error handling
- Performance optimization
- User experience enhancements

## Dependencies to Add

- No additional dependencies required (using built-in `zoneinfo`)
- Optional: `geoip2` for enhanced location services (future enhancement)

## Data Sources

- **Timezone Database**: Python's built-in `zoneinfo` module
- **City Mappings**: Built-in city-to-timezone database
- **User Configuration**: JSON file in user data directory

## Success Criteria

1. ✅ Accurate timezone conversions using `zoneinfo`
2. ✅ Intuitive UI following DevBoost patterns
3. ✅ Persistent city configuration
4. ✅ Support for various time input formats
5. ✅ Integration with scratch pad functionality
6. ✅ Comprehensive error handling and logging
7. ✅ Performance suitable for real-time use

## Next Steps

1. Implement core `TimeZoneConverter` backend class
2. Create basic UI widget structure
3. Add timezone conversion functionality
4. Implement city management features
5. Add configuration persistence
6. Create comprehensive tests
7. Integrate with main application

This analysis provides a comprehensive foundation for implementing the TimeZone tool while maintaining consistency with DevBoost's architecture and user experience patterns.
