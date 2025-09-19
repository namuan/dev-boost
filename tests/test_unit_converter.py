import sys

# Add the parent directory to the path to import the module
sys.path.insert(0, "/Users/nnn/workspace/dev-boost")


from devboost.tools.unit_converter import ProgrammerConverter, UnitConverter


class TestUnitConverter:
    """Test cases for UnitConverter backend class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.converter = UnitConverter()

    def test_initialization(self):
        """Test UnitConverter initialization."""
        converter = UnitConverter()
        assert converter is not None
        assert "Length" in converter.unit_categories
        assert "Mass" in converter.unit_categories
        assert "Temperature" in converter.unit_categories
        assert "Time" in converter.unit_categories
        assert "Data Rate" in converter.unit_categories

    # Length conversions
    def test_length_conversions_basic(self):
        """Test basic length conversions."""
        # Meter to kilometer
        result = self.converter.convert_units(1000, "m", "km", "Length")
        assert result == 1.0

        # Kilometer to meter
        result = self.converter.convert_units(1, "km", "m", "Length")
        assert result == 1000.0

        # Meter to centimeter
        result = self.converter.convert_units(1, "m", "cm", "Length")
        assert result == 100.0

        # Centimeter to meter
        result = self.converter.convert_units(100, "cm", "m", "Length")
        assert result == 1.0

    def test_length_conversions_imperial(self):
        """Test imperial length conversions."""
        # Feet to inches
        result = self.converter.convert_units(1, "ft", "in", "Length")
        assert abs(result - 12.0) < 0.001

        # Miles to feet
        result = self.converter.convert_units(1, "mi", "ft", "Length")
        assert abs(result - 5280.0) < 0.1

        # Inches to centimeters
        result = self.converter.convert_units(1, "in", "cm", "Length")
        assert abs(result - 2.54) < 0.001

    def test_length_conversions_edge_cases(self):
        """Test edge cases for length conversions."""
        # Zero value
        result = self.converter.convert_units(0, "m", "km", "Length")
        assert result == 0.0

        # Negative value
        result = self.converter.convert_units(-100, "m", "cm", "Length")
        assert result == -10000.0

        # Same unit conversion
        result = self.converter.convert_units(42, "m", "m", "Length")
        assert result == 42.0

    # Mass conversions
    def test_mass_conversions_basic(self):
        """Test basic mass conversions."""
        # Kilogram to gram
        result = self.converter.convert_units(1, "kg", "g", "Mass")
        assert result == 1000.0

        # Gram to kilogram
        result = self.converter.convert_units(1000, "g", "kg", "Mass")
        assert result == 1.0

        # Pound to kilogram
        result = self.converter.convert_units(1, "lb", "kg", "Mass")
        assert abs(result - 0.453592) < 0.000001

    def test_mass_conversions_imperial(self):
        """Test imperial mass conversions."""
        # Pound to ounce
        result = self.converter.convert_units(1, "lb", "oz", "Mass")
        assert abs(result - 16.0) < 0.01

        # Ounce to gram
        result = self.converter.convert_units(1, "oz", "g", "Mass")
        assert abs(result - 28.3495) < 0.001

    # Temperature conversions
    def test_temperature_conversions_celsius_kelvin(self):
        """Test Celsius to Kelvin conversions."""
        # Water freezing point
        result = self.converter.convert_units(0, "°C", "K", "Temperature")
        assert abs(result - 273.15) < 0.001

        # Water boiling point
        result = self.converter.convert_units(100, "°C", "K", "Temperature")
        assert abs(result - 373.15) < 0.001

        # Kelvin to Celsius
        result = self.converter.convert_units(273.15, "K", "°C", "Temperature")
        assert abs(result - 0.0) < 0.001

    def test_temperature_conversions_fahrenheit(self):
        """Test Fahrenheit conversions."""
        # Water freezing point
        result = self.converter.convert_units(32, "°F", "°C", "Temperature")
        assert abs(result - 0.0) < 0.001

        # Water boiling point
        result = self.converter.convert_units(212, "°F", "°C", "Temperature")
        assert abs(result - 100.0) < 0.001

        # Celsius to Fahrenheit
        result = self.converter.convert_units(0, "°C", "°F", "Temperature")
        assert abs(result - 32.0) < 0.001

        # Fahrenheit to Kelvin
        result = self.converter.convert_units(32, "°F", "K", "Temperature")
        assert abs(result - 273.15) < 0.001

    def test_temperature_conversions_edge_cases(self):
        """Test temperature conversion edge cases."""
        # Absolute zero in Celsius
        result = self.converter.convert_units(-273.15, "°C", "K", "Temperature")
        assert abs(result - 0.0) < 0.001

        # Absolute zero in Fahrenheit
        result = self.converter.convert_units(-459.67, "°F", "K", "Temperature")
        assert abs(result - 0.0) < 0.001

        # Below absolute zero should return None
        result = self.converter.convert_units(-300, "°C", "K", "Temperature")
        assert result is None

    # Time conversions
    def test_time_conversions_basic(self):
        """Test basic time conversions."""
        # Minutes to seconds
        result = self.converter.convert_units(1, "min", "s", "Time")
        assert result == 60.0

        # Hours to minutes
        result = self.converter.convert_units(1, "h", "min", "Time")
        assert result == 60.0

        # Days to hours
        result = self.converter.convert_units(1, "day", "h", "Time")
        assert result == 24.0

        # Milliseconds to seconds
        result = self.converter.convert_units(1000, "ms", "s", "Time")
        assert result == 1.0

    # Data rate conversions
    def test_data_rate_conversions_si(self):
        """Test data rate conversions with SI units."""
        # Kbps to bps
        result = self.converter.convert_units(1, "Kbps", "bps", "Data Rate", use_iec=False)
        assert result == 1000.0

        # Mbps to Kbps
        result = self.converter.convert_units(1, "Mbps", "Kbps", "Data Rate", use_iec=False)
        assert result == 1000.0

        # Bits to bytes
        result = self.converter.convert_units(8, "bps", "B/s", "Data Rate", use_iec=False)
        assert result == 1.0

        # KB/s to B/s
        result = self.converter.convert_units(1, "KB/s", "B/s", "Data Rate", use_iec=False)
        assert result == 1000.0

    def test_data_rate_conversions_iec(self):
        """Test data rate conversions with IEC units."""
        # Kbps to bps with IEC
        result = self.converter.convert_units(1, "Kbps", "bps", "Data Rate", use_iec=True)
        assert result == 1024.0

        # Mbps to Kbps with IEC
        result = self.converter.convert_units(1, "Mbps", "Kbps", "Data Rate", use_iec=True)
        assert result == 1024.0

    # Error handling tests
    def test_invalid_category(self):
        """Test handling of invalid category."""
        result = self.converter.convert_units(100, "m", "km", "InvalidCategory")
        assert result is None

    def test_invalid_units(self):
        """Test handling of invalid units."""
        result = self.converter.convert_units(100, "invalid_unit", "km", "Length")
        assert result is None

        result = self.converter.convert_units(100, "m", "invalid_unit", "Length")
        assert result is None

    def test_invalid_temperature_units(self):
        """Test handling of invalid temperature units."""
        result = self.converter.convert_units(100, "invalid_temp", "°C", "Temperature")
        assert result is None

    def test_conversion_with_invalid_value(self):
        """Test conversion with invalid numeric values."""
        # This should be handled by the calling code, but test robustness
        result = self.converter.convert_units(float("inf"), "m", "km", "Length")
        assert result == float("inf")

        result = self.converter.convert_units(float("-inf"), "m", "km", "Length")
        assert result == float("-inf")


class TestProgrammerConverter:
    """Test cases for ProgrammerConverter backend class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.converter = ProgrammerConverter()

    def test_initialization(self):
        """Test ProgrammerConverter initialization."""
        converter = ProgrammerConverter()
        assert converter is not None

    # Input parsing tests
    def test_parse_decimal_input(self):
        """Test parsing decimal input."""
        result = self.converter.parse_input("42")
        assert result == 42

        result = self.converter.parse_input("0")
        assert result == 0

        result = self.converter.parse_input("255")
        assert result == 255

    def test_parse_binary_input(self):
        """Test parsing binary input."""
        result = self.converter.parse_input("0b1010")
        assert result == 10

        result = self.converter.parse_input("0b11111111")
        assert result == 255

        result = self.converter.parse_input("0b0")
        assert result == 0

    def test_parse_octal_input(self):
        """Test parsing octal input."""
        result = self.converter.parse_input("0o12")
        assert result == 10

        result = self.converter.parse_input("0o377")
        assert result == 255

        result = self.converter.parse_input("0o0")
        assert result == 0

    def test_parse_hexadecimal_input(self):
        """Test parsing hexadecimal input."""
        result = self.converter.parse_input("0xA")
        assert result == 10

        result = self.converter.parse_input("0xFF")
        assert result == 255

        result = self.converter.parse_input("0x0")
        assert result == 0

        result = self.converter.parse_input("0xDEADBEEF")
        assert result == 3735928559

    def test_parse_input_edge_cases(self):
        """Test parsing input edge cases."""
        # Empty string
        result = self.converter.parse_input("")
        assert result is None

        # Whitespace only
        result = self.converter.parse_input("   ")
        assert result is None

        # Invalid format
        result = self.converter.parse_input("invalid")
        assert result is None

        # Invalid binary
        result = self.converter.parse_input("0b2")
        assert result is None

        # Invalid hex
        result = self.converter.parse_input("0xG")
        assert result is None

    def test_parse_input_bit_width_clamping(self):
        """Test bit width clamping during parsing."""
        # 32-bit max value + 1 should be clamped
        result = self.converter.parse_input("4294967296", bit_width=32)  # 2^32
        assert result == 0  # Wrapped around

        # 8-bit clamping
        result = self.converter.parse_input("256", bit_width=8)
        assert result == 0  # 256 & 0xFF = 0

        result = self.converter.parse_input("257", bit_width=8)
        assert result == 1  # 257 & 0xFF = 1

    # Value formatting tests
    def test_format_binary(self):
        """Test binary formatting."""
        result = self.converter.format_value(10, "bin", bit_width=8)
        assert result == "0b00001010"

        result = self.converter.format_value(255, "bin", bit_width=8)
        assert result == "0b11111111"

        result = self.converter.format_value(0, "bin", bit_width=8)
        assert result == "0b00000000"

    def test_format_binary_with_grouping(self):
        """Test binary formatting with grouping."""
        # Nibble grouping
        result = self.converter.format_value(255, "bin", bit_width=8, nibble_group=True)
        assert result == "0b1111 1111"

        # Byte grouping
        result = self.converter.format_value(65535, "bin", bit_width=16, byte_group=True)
        assert result == "0b11111111 11111111"

    def test_format_octal(self):
        """Test octal formatting."""
        result = self.converter.format_value(10, "oct")
        assert result == "0o12"

        result = self.converter.format_value(255, "oct")
        assert result == "0o377"

        result = self.converter.format_value(0, "oct")
        assert result == "0o0"

    def test_format_decimal(self):
        """Test decimal formatting."""
        result = self.converter.format_value(10, "dec")
        assert result == "10"

        result = self.converter.format_value(255, "dec")
        assert result == "255"

        result = self.converter.format_value(0, "dec")
        assert result == "0"

    def test_format_hexadecimal(self):
        """Test hexadecimal formatting."""
        result = self.converter.format_value(10, "hex", bit_width=8)
        assert result == "0x0a"

        result = self.converter.format_value(255, "hex", bit_width=8)
        assert result == "0xff"

        result = self.converter.format_value(0, "hex", bit_width=8)
        assert result == "0x00"

    def test_format_hexadecimal_with_grouping(self):
        """Test hexadecimal formatting with grouping."""
        # Nibble grouping (each hex digit)
        result = self.converter.format_value(255, "hex", bit_width=8, nibble_group=True)
        assert result == "0xf f"

        # Byte grouping
        result = self.converter.format_value(65535, "hex", bit_width=16, byte_group=True)
        assert result == "0xff ff"

    def test_format_value_edge_cases(self):
        """Test value formatting edge cases."""
        # None value
        result = self.converter.format_value(None, "dec")
        assert result == ""

        # Invalid base
        result = self.converter.format_value(10, "invalid")
        assert result == "10"  # Falls back to string conversion

    # Bitwise operation tests
    def test_bitwise_and(self):
        """Test bitwise AND operation."""
        result = self.converter.bitwise_operation(0b1010, 0b1100, "AND")
        assert result == 0b1000  # 8

        result = self.converter.bitwise_operation(255, 15, "AND")
        assert result == 15

        result = self.converter.bitwise_operation(0, 255, "AND")
        assert result == 0

    def test_bitwise_or(self):
        """Test bitwise OR operation."""
        result = self.converter.bitwise_operation(0b1010, 0b1100, "OR")
        assert result == 0b1110  # 14

        result = self.converter.bitwise_operation(240, 15, "OR")
        assert result == 255

        result = self.converter.bitwise_operation(0, 255, "OR")
        assert result == 255

    def test_bitwise_xor(self):
        """Test bitwise XOR operation."""
        result = self.converter.bitwise_operation(0b1010, 0b1100, "XOR")
        assert result == 0b0110  # 6

        result = self.converter.bitwise_operation(255, 255, "XOR")
        assert result == 0

        result = self.converter.bitwise_operation(170, 85, "XOR")  # 0xAA ^ 0x55
        assert result == 255

    def test_bitwise_not(self):
        """Test bitwise NOT operation."""
        result = self.converter.bitwise_operation(0, 0, "NOT", bit_width=8)
        assert result == 255  # All bits flipped in 8-bit

        result = self.converter.bitwise_operation(255, 0, "NOT", bit_width=8)
        assert result == 0

        result = self.converter.bitwise_operation(0b10101010, 0, "NOT", bit_width=8)
        assert result == 0b01010101

    def test_bitwise_left_shift(self):
        """Test bitwise left shift operation."""
        result = self.converter.bitwise_operation(1, 1, "<<")
        assert result == 2

        result = self.converter.bitwise_operation(1, 8, "<<")
        assert result == 256

        # Test overflow with bit width
        result = self.converter.bitwise_operation(255, 1, "<<", bit_width=8)
        assert result == 254  # 0xFF << 1 = 0x1FE, clamped to 8-bit = 0xFE

    def test_bitwise_right_shift(self):
        """Test bitwise right shift operation."""
        result = self.converter.bitwise_operation(8, 1, ">>")
        assert result == 4

        result = self.converter.bitwise_operation(256, 8, ">>")
        assert result == 1

        result = self.converter.bitwise_operation(1, 1, ">>")
        assert result == 0

    def test_bitwise_operation_bit_width_clamping(self):
        """Test bit width clamping in bitwise operations."""
        # 8-bit operations
        result = self.converter.bitwise_operation(256, 256, "AND", bit_width=8)
        assert result == 0  # Both values clamped to 0

        result = self.converter.bitwise_operation(300, 200, "OR", bit_width=8)
        # 300 & 0xFF = 44, 200 & 0xFF = 200, 44 | 200 = 236
        assert result == 236

    def test_bitwise_operation_edge_cases(self):
        """Test bitwise operation edge cases."""
        # Invalid operation
        result = self.converter.bitwise_operation(10, 5, "INVALID")
        assert result is None

        # Large shift values
        result = self.converter.bitwise_operation(1, 100, "<<", bit_width=32)
        assert result == 0  # Shifted out of range

        result = self.converter.bitwise_operation(0xFFFFFFFF, 100, ">>", bit_width=32)
        assert result == 0

    def test_bitwise_operation_different_bit_widths(self):
        """Test bitwise operations with different bit widths."""
        # 16-bit operations
        result = self.converter.bitwise_operation(0xFFFF, 0x0000, "NOT", bit_width=16)
        assert result == 0x0000

        result = self.converter.bitwise_operation(0x0000, 0x0000, "NOT", bit_width=16)
        assert result == 0xFFFF

        # 64-bit operations (if supported)
        result = self.converter.bitwise_operation(1, 1, "<<", bit_width=64)
        assert result == 2
