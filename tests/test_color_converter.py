from devboost.tools.color_converter import ColorConverter


class TestColorConverter:
    """Test cases for ColorConverter backend class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.converter = ColorConverter()

    def test_initialization(self):
        """Test ColorConverter initialization."""
        converter = ColorConverter()
        assert converter is not None

    def test_parse_hex_3_digit(self):
        """Test parsing 3-digit hex colors."""
        result = self.converter.parse_color("#F0A")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 1.0) < 0.01  # FF
        assert abs(g - 0.0) < 0.01  # 00
        assert abs(b - 0.667) < 0.01  # AA
        assert a == 1.0

    def test_parse_hex_4_digit(self):
        """Test parsing 4-digit hex colors with alpha."""
        result = self.converter.parse_color("#F0A8")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 1.0) < 0.01  # FF
        assert abs(g - 0.0) < 0.01  # 00
        assert abs(b - 0.667) < 0.01  # AA
        assert abs(a - 0.533) < 0.01  # 88

    def test_parse_hex_6_digit(self):
        """Test parsing 6-digit hex colors."""
        result = self.converter.parse_color("#5CCC7F")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 0.361) < 0.01  # 5C
        assert abs(g - 0.8) < 0.01  # CC
        assert abs(b - 0.498) < 0.01  # 7F
        assert a == 1.0

    def test_parse_hex_8_digit(self):
        """Test parsing 8-digit hex colors with alpha."""
        result = self.converter.parse_color("#5CCC7F80")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 0.361) < 0.01  # 5C
        assert abs(g - 0.8) < 0.01  # CC
        assert abs(b - 0.498) < 0.01  # 7F
        assert abs(a - 0.502) < 0.01  # 80

    def test_parse_rgb(self):
        """Test parsing RGB colors."""
        result = self.converter.parse_color("rgb(92, 204, 127)")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 0.361) < 0.01
        assert abs(g - 0.8) < 0.01
        assert abs(b - 0.498) < 0.01
        assert a == 1.0

    def test_parse_rgba(self):
        """Test parsing RGBA colors."""
        result = self.converter.parse_color("rgba(92, 204, 127, 0.5)")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 0.361) < 0.01
        assert abs(g - 0.8) < 0.01
        assert abs(b - 0.498) < 0.01
        assert a == 0.5

    def test_parse_hsl(self):
        """Test parsing HSL colors."""
        result = self.converter.parse_color("hsl(139, 52%, 58%)")
        assert result is not None
        r, g, b, a = result
        # HSL conversion should be close to expected RGB values
        assert 0.3 < r < 0.4
        assert 0.7 < g < 0.9
        assert 0.4 < b < 0.6
        assert a == 1.0

    def test_parse_hsla(self):
        """Test parsing HSLA colors."""
        result = self.converter.parse_color("hsla(139, 52%, 58%, 0.8)")
        assert result is not None
        r, g, b, a = result
        assert 0.3 < r < 0.4
        assert 0.7 < g < 0.9
        assert 0.4 < b < 0.6
        assert a == 0.8

    def test_parse_hsb(self):
        """Test parsing HSB/HSV colors."""
        result = self.converter.parse_color("hsb(139, 55%, 80%)")
        assert result is not None
        r, g, b, a = result
        # HSB conversion should produce valid RGB values
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1
        assert a == 1.0

    def test_parse_hwb(self):
        """Test parsing HWB colors."""
        result = self.converter.parse_color("hwb(139, 36%, 20%)")
        assert result is not None
        r, g, b, a = result
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1
        assert a == 1.0

    def test_parse_cmyk(self):
        """Test parsing CMYK colors."""
        result = self.converter.parse_color("cmyk(55%, 0%, 38%, 20%)")
        assert result is not None
        r, g, b, a = result
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1
        assert a == 1.0

    def test_parse_invalid_color(self):
        """Test parsing invalid color formats."""
        assert self.converter.parse_color("") is None
        assert self.converter.parse_color("invalid") is None
        assert self.converter.parse_color("#GGG") is None
        assert self.converter.parse_color("rgb(300, 400, 500)") is not None  # Should clamp values

    def test_to_hex(self):
        """Test converting to hex format."""
        result = self.converter.to_hex(0.361, 0.8, 0.498)
        assert result == "#5CCC7F"

    def test_to_hex_with_alpha(self):
        """Test converting to hex format with alpha."""
        result = self.converter.to_hex(0.361, 0.8, 0.498, 0.5)
        assert result == "#5CCC7F80"

    def test_to_hex_force_alpha(self):
        """Test converting to hex format with forced alpha inclusion."""
        result = self.converter.to_hex(0.361, 0.8, 0.498, 1.0, include_alpha=True)
        assert result == "#5CCC7FFF"

    def test_to_hex_exclude_alpha(self):
        """Test converting to hex format with forced alpha exclusion."""
        result = self.converter.to_hex(0.361, 0.8, 0.498, 0.5, include_alpha=False)
        assert result == "#5CCC7F"

    def test_to_rgb(self):
        """Test converting to RGB format."""
        result = self.converter.to_rgb(0.361, 0.8, 0.498)
        assert result == "rgb(92, 204, 127)"

    def test_to_rgb_percentages(self):
        """Test converting to RGB format with percentages."""
        result = self.converter.to_rgb(0.5, 0.8, 0.2, use_percentages=True)
        assert result == "rgb(50.0%, 80.0%, 20.0%)"

    def test_to_rgb_clamping(self):
        """Test RGB conversion with value clamping."""
        result = self.converter.to_rgb(1.5, -0.2, 0.8)
        assert result == "rgb(255, 0, 204)"

    def test_to_rgba(self):
        """Test converting to RGBA format."""
        result = self.converter.to_rgba(0.361, 0.8, 0.498, 0.5)
        assert result == "rgba(92, 204, 127, 0.5)"

    def test_to_rgba_percentages(self):
        """Test converting to RGBA format with percentages."""
        result = self.converter.to_rgba(0.5, 0.8, 0.2, 0.6, use_percentages=True)
        assert result == "rgba(50.0%, 80.0%, 20.0%, 0.6)"

    def test_to_rgba_alpha_percentage(self):
        """Test converting to RGBA format with alpha as percentage."""
        result = self.converter.to_rgba(0.5, 0.8, 0.2, 0.6, alpha_as_percentage=True)
        assert result == "rgba(128, 204, 51, 60.0%)"

    def test_to_rgba_all_percentages(self):
        """Test converting to RGBA format with all percentages."""
        result = self.converter.to_rgba(0.5, 0.8, 0.2, 0.6, use_percentages=True, alpha_as_percentage=True)
        assert result == "rgba(50.0%, 80.0%, 20.0%, 60.0%)"

    def test_to_rgba_clamping(self):
        """Test RGBA conversion with value clamping."""
        result = self.converter.to_rgba(1.5, -0.2, 0.8, 1.2)
        assert result == "rgba(255, 0, 204, 1.0)"

    def test_to_hsl(self):
        """Test converting to HSL format."""
        result = self.converter.to_hsl(0.361, 0.8, 0.498)
        # HSL values should be reasonable
        assert "hsl(" in result
        assert "%" in result

    def test_to_hsl_precision(self):
        """Test converting to HSL format with precision."""
        result = self.converter.to_hsl(0.5, 0.8, 0.2, precision=1)
        assert "hsl(" in result
        assert "." in result  # Should have decimal places

    def test_to_hsl_with_deg(self):
        """Test converting to HSL format with deg suffix."""
        result = self.converter.to_hsl_with_deg(0.5, 0.8, 0.2)
        assert "hsl(" in result
        assert "deg" in result

    def test_to_hsl_clamping(self):
        """Test HSL conversion with value clamping."""
        result = self.converter.to_hsl(1.5, -0.2, 0.8)
        assert "hsl(" in result

    def test_to_hsla(self):
        """Test converting to HSLA format."""
        result = self.converter.to_hsla(0.361, 0.8, 0.498, 0.8)
        assert "hsla(" in result
        assert "%" in result
        assert "80%" in result  # Alpha as percentage

    def test_to_hsla_precision(self):
        """Test converting to HSLA format with precision."""
        result = self.converter.to_hsla(0.5, 0.8, 0.2, 0.6, precision=1)
        assert "hsla(" in result
        assert "." in result  # Should have decimal places

    def test_to_hsla_alpha_decimal(self):
        """Test converting to HSLA format with alpha as decimal."""
        result = self.converter.to_hsla(0.5, 0.8, 0.2, 0.6, alpha_as_percentage=False)
        assert "hsla(" in result
        assert "0.6)" in result  # Alpha as decimal

    def test_to_hsla_with_deg(self):
        """Test converting to HSLA format with deg suffix."""
        result = self.converter.to_hsla_with_deg(0.5, 0.8, 0.2, 0.6)
        assert "hsla(" in result
        assert "deg" in result

    def test_to_hsla_clamping(self):
        """Test HSLA conversion with value clamping."""
        result = self.converter.to_hsla(1.5, -0.2, 0.8, 1.2)
        assert "hsla(" in result

    def test_to_hsb(self):
        """Test converting to HSB format."""
        result = self.converter.to_hsb(0.361, 0.8, 0.498)
        assert "hsb(" in result
        assert "%" in result

    def test_to_hsb_precision(self):
        """Test converting to HSB format with precision."""
        result = self.converter.to_hsb(0.5, 0.8, 0.2, precision=1)
        assert "hsb(" in result
        assert "." in result  # Should have decimal places

    def test_to_hsb_with_deg(self):
        """Test converting to HSB format with deg suffix."""
        result = self.converter.to_hsb_with_deg(0.5, 0.8, 0.2)
        assert "hsb(" in result
        assert "deg" in result

    def test_to_hsv(self):
        """Test converting to HSV format."""
        result = self.converter.to_hsv(0.361, 0.8, 0.498)
        assert "hsv(" in result
        assert "%" in result

    def test_to_hsv_precision(self):
        """Test converting to HSV format with precision."""
        result = self.converter.to_hsv(0.5, 0.8, 0.2, precision=1)
        assert "hsv(" in result
        assert "." in result  # Should have decimal places

    def test_to_hsv_with_deg(self):
        """Test converting to HSV format with deg suffix."""
        result = self.converter.to_hsv_with_deg(0.5, 0.8, 0.2)
        assert "hsv(" in result
        assert "deg" in result

    def test_hsb_hsv_equivalence(self):
        """Test that HSB and HSV produce equivalent results."""
        hsb_result = self.converter.to_hsb(0.5, 0.8, 0.2)
        hsv_result = self.converter.to_hsv(0.5, 0.8, 0.2)

        # Extract numeric values (should be the same)
        hsb_values = hsb_result.replace("hsb(", "").replace(")", "").split(", ")
        hsv_values = hsv_result.replace("hsv(", "").replace(")", "").split(", ")

        assert hsb_values == hsv_values

    def test_to_hsb_clamping(self):
        """Test HSB conversion with value clamping."""
        result = self.converter.to_hsb(1.5, -0.2, 0.8)
        assert "hsb(" in result

    def test_to_hsv_clamping(self):
        """Test HSV conversion with value clamping."""
        result = self.converter.to_hsv(1.5, -0.2, 0.8)
        assert "hsv(" in result

    def test_to_hwb(self):
        """Test converting to HWB format."""
        result = self.converter.to_hwb(0.361, 0.8, 0.498)
        assert "hwb(" in result
        assert "%" in result

    def test_to_hwb_precision(self):
        """Test converting to HWB format with precision."""
        result = self.converter.to_hwb(0.5, 0.8, 0.2, precision=1)
        assert "hwb(" in result
        assert "." in result  # Should have decimal places

    def test_to_hwb_with_deg(self):
        """Test converting to HWB format with deg suffix."""
        result = self.converter.to_hwb_with_deg(0.5, 0.8, 0.2)
        assert "hwb(" in result
        assert "deg" in result

    def test_to_hwb_clamping(self):
        """Test HWB conversion with value clamping."""
        result = self.converter.to_hwb(1.5, -0.2, 0.8)
        assert "hwb(" in result

    def test_to_cmyk(self):
        """Test converting to CMYK format."""
        result = self.converter.to_cmyk(0.361, 0.8, 0.498)
        assert "cmyk(" in result
        assert "%" in result

    def test_to_cmyk_precision(self):
        """Test converting to CMYK format with precision."""
        result = self.converter.to_cmyk(0.5, 0.8, 0.2, precision=1)
        assert "cmyk(" in result
        assert "." in result  # Should have decimal places

    def test_to_cmyk_clamping(self):
        """Test CMYK conversion with value clamping."""
        result = self.converter.to_cmyk(1.5, -0.2, 0.8)
        assert "cmyk(" in result

    def test_to_cmyk_black(self):
        """Test CMYK conversion for pure black."""
        result = self.converter.to_cmyk(0, 0, 0)
        assert result == "cmyk(0%, 0%, 0%, 100%)"

    def test_to_cmyk_white(self):
        """Test CMYK conversion for pure white."""
        result = self.converter.to_cmyk(1, 1, 1)
        assert result == "cmyk(0%, 0%, 0%, 0%)"

    def test_convert_all_formats(self):
        """Test converting to all formats at once."""
        result = self.converter.convert_all_formats("#5CCC7F")
        assert len(result) == 10  # Updated count to include HSV
        assert "hex" in result
        assert "hex_alpha" in result
        assert "rgb" in result
        assert "rgba" in result
        assert "hsl" in result
        assert "hsla" in result
        assert "hsb" in result
        assert "hsv" in result
        assert "hwb" in result
        assert "cmyk" in result

        # Verify some specific values
        assert result["hex"] == "#5CCC7F"
        assert result["rgb"] == "rgb(92, 204, 127)"

        # Verify HSB and HSV are equivalent
        hsb_values = result["hsb"].replace("hsb(", "").replace(")", "").split(", ")
        hsv_values = result["hsv"].replace("hsv(", "").replace(")", "").split(", ")
        assert hsb_values == hsv_values

    def test_convert_all_formats_invalid(self):
        """Test converting invalid color returns empty dict."""
        result = self.converter.convert_all_formats("invalid")
        assert result == {}

    def test_round_trip_conversion(self):
        """Test that converting back and forth preserves color."""
        original = "#5CCC7F"
        rgba = self.converter.parse_color(original)
        assert rgba is not None

        r, g, b, a = rgba
        converted_back = self.converter.to_hex(r, g, b, a)
        assert converted_back == original

    def test_edge_cases(self):
        """Test edge cases and boundary values."""
        # Pure black
        result = self.converter.parse_color("#000000")
        assert result == (0.0, 0.0, 0.0, 1.0)

        # Pure white
        result = self.converter.parse_color("#FFFFFF")
        assert result == (1.0, 1.0, 1.0, 1.0)

        # Pure red
        result = self.converter.parse_color("#FF0000")
        assert result == (1.0, 0.0, 0.0, 1.0)

    def test_hex_validation(self):
        """Test hex color validation."""
        # Valid hex colors
        assert self.converter.is_valid_hex_color("#FFF")
        assert self.converter.is_valid_hex_color("#FFFF")
        assert self.converter.is_valid_hex_color("#FFFFFF")
        assert self.converter.is_valid_hex_color("#FFFFFFFF")
        assert self.converter.is_valid_hex_color("#abc")
        assert self.converter.is_valid_hex_color("#123456")

        # Invalid hex colors
        assert not self.converter.is_valid_hex_color("")
        assert not self.converter.is_valid_hex_color("FFF")
        assert not self.converter.is_valid_hex_color("#GGG")
        assert not self.converter.is_valid_hex_color("#FF")
        assert not self.converter.is_valid_hex_color("#FFFFF")
        assert not self.converter.is_valid_hex_color("#FFFFFFFFF")
        assert not self.converter.is_valid_hex_color("rgb(255,255,255)")

    def test_hex_normalization(self):
        """Test hex color normalization."""
        # 3-digit to 6-digit
        assert self.converter.normalize_hex_color("#abc") == "#AABBCC"
        assert self.converter.normalize_hex_color("#ABC") == "#AABBCC"

        # 4-digit to 8-digit
        assert self.converter.normalize_hex_color("#abcd") == "#AABBCCDD"

        # Already normalized
        assert self.converter.normalize_hex_color("#AABBCC") == "#AABBCC"
        assert self.converter.normalize_hex_color("#AABBCCDD") == "#AABBCCDD"

        # Invalid colors
        assert self.converter.normalize_hex_color("invalid") is None
        assert self.converter.normalize_hex_color("#GGG") is None

    def test_hex_short_format(self):
        """Test short hex format conversion."""
        # Colors that can be shortened
        result = self.converter.to_hex_short(1.0, 0.0, 0.667)  # #FF00AA -> #F0A
        assert result == "#F0A"

        result = self.converter.to_hex_short(0.0, 0.0, 0.0)  # #000000 -> #000
        assert result == "#000"

        result = self.converter.to_hex_short(1.0, 1.0, 1.0)  # #FFFFFF -> #FFF
        assert result == "#FFF"

        # Colors that cannot be shortened
        result = self.converter.to_hex_short(0.361, 0.8, 0.498)  # #5CCC7F
        assert result is None

        # With alpha that can be shortened
        result = self.converter.to_hex_short(1.0, 0.0, 0.667, 0.533)  # #FF00AA88 -> #F0A8
        assert result == "#F0A8"

        # With alpha that cannot be shortened
        result = self.converter.to_hex_short(1.0, 0.0, 0.667, 0.5)  # #FF00AA80
        assert result is None

    def test_hex_value_clamping(self):
        """Test that hex conversion clamps values to valid range."""
        # Values above 1.0 should be clamped
        result = self.converter.to_hex(1.5, 0.8, 0.498)
        assert result == "#FFCC7F"

        # Values below 0.0 should be clamped
        result = self.converter.to_hex(-0.5, 0.8, 0.498)
        assert result == "#00CC7F"

        # Alpha values should also be clamped
        result = self.converter.to_hex(0.5, 0.5, 0.5, 1.5, include_alpha=True)
        assert result == "#808080FF"

        result = self.converter.to_hex(0.5, 0.5, 0.5, -0.5, include_alpha=True)
        assert result == "#80808000"

    def test_case_insensitive_parsing(self):
        """Test that color parsing is case insensitive."""
        result1 = self.converter.parse_color("RGB(92, 204, 127)")
        result2 = self.converter.parse_color("rgb(92, 204, 127)")
        result3 = self.converter.parse_color("Rgb(92, 204, 127)")

        assert result1 == result2 == result3

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        result1 = self.converter.parse_color("rgb(92,204,127)")
        result2 = self.converter.parse_color("rgb( 92 , 204 , 127 )")
        result3 = self.converter.parse_color("  rgb(92, 204, 127)  ")

        assert result1 == result2 == result3

    def test_percentage_values(self):
        """Test parsing percentage values in RGB."""
        result = self.converter.parse_color("rgb(50%, 80%, 25%)")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 0.5) < 0.01
        assert abs(g - 0.8) < 0.01
        assert abs(b - 0.25) < 0.01
        assert a == 1.0

    def test_rgb_validation(self):
        """Test RGB color validation."""
        # Valid RGB colors
        assert self.converter.is_valid_rgb_color("rgb(255, 255, 255)")
        assert self.converter.is_valid_rgb_color("rgb(0, 0, 0)")
        assert self.converter.is_valid_rgb_color("rgb(50%, 80%, 25%)")
        assert self.converter.is_valid_rgb_color("RGB(255, 255, 255)")
        assert self.converter.is_valid_rgb_color("rgb( 255 , 255 , 255 )")

        # Invalid RGB colors
        assert not self.converter.is_valid_rgb_color("")
        assert not self.converter.is_valid_rgb_color("rgb(255, 255)")
        assert not self.converter.is_valid_rgb_color("rgb(255, 255, 255, 255)")
        assert not self.converter.is_valid_rgb_color("rgb(300, 255, 255)")
        assert not self.converter.is_valid_rgb_color("rgb(-10, 255, 255)")
        assert not self.converter.is_valid_rgb_color("rgb(255, 255, 255")
        assert not self.converter.is_valid_rgb_color("255, 255, 255")

    def test_rgba_validation(self):
        """Test RGBA color validation."""
        # Valid RGBA colors
        assert self.converter.is_valid_rgba_color("rgba(255, 255, 255, 1)")
        assert self.converter.is_valid_rgba_color("rgba(0, 0, 0, 0)")
        assert self.converter.is_valid_rgba_color("rgba(50%, 80%, 25%, 50%)")
        assert self.converter.is_valid_rgba_color("rgba(255, 255, 255, 0.5)")
        assert self.converter.is_valid_rgba_color("RGBA(255, 255, 255, 1)")

        # Invalid RGBA colors
        assert not self.converter.is_valid_rgba_color("")
        assert not self.converter.is_valid_rgba_color("rgba(255, 255, 255)")
        assert not self.converter.is_valid_rgba_color("rgba(255, 255, 255, 255, 255)")
        assert not self.converter.is_valid_rgba_color("rgba(300, 255, 255, 1)")
        assert not self.converter.is_valid_rgba_color("rgba(255, 255, 255, 2)")
        assert not self.converter.is_valid_rgba_color("rgba(255, 255, 255, -0.5)")

    def test_rgb_component_validation(self):
        """Test individual RGB component validation."""
        # Valid RGB components
        assert self.converter._is_valid_rgb_component("255")
        assert self.converter._is_valid_rgb_component("0")
        assert self.converter._is_valid_rgb_component("100%")
        assert self.converter._is_valid_rgb_component("0%")
        assert self.converter._is_valid_rgb_component("50.5")

        # Invalid RGB components
        assert not self.converter._is_valid_rgb_component("256")
        assert not self.converter._is_valid_rgb_component("-1")
        assert not self.converter._is_valid_rgb_component("101%")
        assert not self.converter._is_valid_rgb_component("-1%")
        assert not self.converter._is_valid_rgb_component("abc")

    def test_alpha_component_validation(self):
        """Test alpha component validation."""
        # Valid alpha components
        assert self.converter._is_valid_alpha_component("1")
        assert self.converter._is_valid_alpha_component("0")
        assert self.converter._is_valid_alpha_component("0.5")
        assert self.converter._is_valid_alpha_component("100%")
        assert self.converter._is_valid_alpha_component("0%")
        assert self.converter._is_valid_alpha_component("50%")

        # Invalid alpha components
        assert not self.converter._is_valid_alpha_component("2")
        assert not self.converter._is_valid_alpha_component("-0.5")
        assert not self.converter._is_valid_alpha_component("101%")
        assert not self.converter._is_valid_alpha_component("-1%")
        assert not self.converter._is_valid_alpha_component("abc")

    def test_rgb_parsing_edge_cases(self):
        """Test RGB parsing with edge cases."""
        # Values at boundaries
        result = self.converter.parse_color("rgb(0, 255, 128)")
        assert result is not None
        r, g, b, a = result
        assert r == 0.0
        assert g == 1.0
        assert abs(b - 0.502) < 0.01
        assert a == 1.0

        # Mixed percentage and numeric (should handle gracefully)
        result = self.converter.parse_color("rgb(50%, 128, 25%)")
        assert result is not None

        # Values that need clamping
        result = self.converter.parse_color("rgb(300, -50, 128)")
        assert result is not None
        r, g, b, a = result
        assert r == 1.0  # Clamped from 300/255
        assert g == 0.0  # Clamped from -50
        assert abs(b - 0.502) < 0.01

    def test_rgba_parsing_edge_cases(self):
        """Test RGBA parsing with edge cases."""
        # Alpha at boundaries
        result = self.converter.parse_color("rgba(128, 128, 128, 0)")
        assert result is not None
        r, g, b, a = result
        assert abs(r - 0.502) < 0.01
        assert abs(g - 0.502) < 0.01
        assert abs(b - 0.502) < 0.01
        assert a == 0.0

        result = self.converter.parse_color("rgba(128, 128, 128, 1)")
        assert result is not None
        r, g, b, a = result
        assert a == 1.0

        # Alpha as percentage
        result = self.converter.parse_color("rgba(128, 128, 128, 50%)")
        assert result is not None
        r, g, b, a = result
        assert a == 0.5

        # Alpha values that need clamping
        result = self.converter.parse_color("rgba(128, 128, 128, 2)")
        assert result is not None
        r, g, b, a = result
        assert a == 1.0  # Clamped from 2

        result = self.converter.parse_color("rgba(128, 128, 128, -0.5)")
        assert result is not None
        r, g, b, a = result
        assert a == 0.0  # Clamped from -0.5

    def test_hue_with_degrees(self):
        """Test parsing hue values with 'deg' suffix."""
        result1 = self.converter.parse_color("hsl(180deg, 50%, 50%)")
        result2 = self.converter.parse_color("hsl(180, 50%, 50%)")

        assert result1 is not None
        assert result2 is not None
        # Should be approximately equal
        r1, g1, b1, a1 = result1
        r2, g2, b2, a2 = result2
        assert abs(r1 - r2) < 0.01
        assert abs(g1 - g2) < 0.01
        assert abs(b1 - b2) < 0.01
        assert a1 == a2

    def test_hsl_validation(self):
        """Test HSL color validation."""
        # Valid HSL colors
        assert self.converter.is_valid_hsl_color("hsl(180, 50%, 50%)")
        assert self.converter.is_valid_hsl_color("hsl(180deg, 50%, 50%)")
        assert self.converter.is_valid_hsl_color("HSL(180, 50%, 50%)")
        assert self.converter.is_valid_hsl_color("hsl( 180 , 50% , 50% )")
        assert self.converter.is_valid_hsl_color("hsl(0, 0%, 0%)")
        assert self.converter.is_valid_hsl_color("hsl(360, 100%, 100%)")

        # Invalid HSL colors
        assert not self.converter.is_valid_hsl_color("")
        assert not self.converter.is_valid_hsl_color("hsl(180, 50%)")
        assert not self.converter.is_valid_hsl_color("hsl(180, 50%, 50%, 50%)")
        assert not self.converter.is_valid_hsl_color("hsl(180, 150%, 50%)")
        assert not self.converter.is_valid_hsl_color("hsl(180, -10%, 50%)")
        assert not self.converter.is_valid_hsl_color("hsl(180, 50%, 50%")
        assert not self.converter.is_valid_hsl_color("180, 50%, 50%")

    def test_hsla_validation(self):
        """Test HSLA color validation."""
        # Valid HSLA colors
        assert self.converter.is_valid_hsla_color("hsla(180, 50%, 50%, 1)")
        assert self.converter.is_valid_hsla_color("hsla(180deg, 50%, 50%, 0.5)")
        assert self.converter.is_valid_hsla_color("hsla(180, 50%, 50%, 50%)")
        assert self.converter.is_valid_hsla_color("HSLA(180, 50%, 50%, 1)")
        assert self.converter.is_valid_hsla_color("hsla( 180 , 50% , 50% , 0.5 )")

        # Invalid HSLA colors
        assert not self.converter.is_valid_hsla_color("")
        assert not self.converter.is_valid_hsla_color("hsla(180, 50%, 50%)")
        assert not self.converter.is_valid_hsla_color("hsla(180, 50%, 50%, 50%, 50%)")
        assert not self.converter.is_valid_hsla_color("hsla(180, 150%, 50%, 1)")
        assert not self.converter.is_valid_hsla_color("hsla(180, 50%, 50%, 2)")
        assert not self.converter.is_valid_hsla_color("hsla(180, 50%, 50%, -0.5)")

    def test_hue_component_validation(self):
        """Test hue component validation."""
        # Valid hue components
        assert self.converter._is_valid_hue_component("180")
        assert self.converter._is_valid_hue_component("180deg")
        assert self.converter._is_valid_hue_component("0")
        assert self.converter._is_valid_hue_component("360")
        assert self.converter._is_valid_hue_component("720")  # Wraps around
        assert self.converter._is_valid_hue_component("-90")  # Wraps around

        # Invalid hue components
        assert not self.converter._is_valid_hue_component("abc")
        assert not self.converter._is_valid_hue_component("180px")

    def test_percentage_component_validation(self):
        """Test percentage component validation."""
        # Valid percentage components
        assert self.converter._is_valid_percentage_component("50%")
        assert self.converter._is_valid_percentage_component("0%")
        assert self.converter._is_valid_percentage_component("100%")
        assert self.converter._is_valid_percentage_component("50")  # Without %
        assert self.converter._is_valid_percentage_component("0")
        assert self.converter._is_valid_percentage_component("100")

        # Invalid percentage components
        assert not self.converter._is_valid_percentage_component("101%")
        assert not self.converter._is_valid_percentage_component("-1%")
        assert not self.converter._is_valid_percentage_component("101")
        assert not self.converter._is_valid_percentage_component("-1")
        assert not self.converter._is_valid_percentage_component("abc")

    def test_hsl_parsing_edge_cases(self):
        """Test HSL parsing with edge cases."""
        # Hue wrapping
        result1 = self.converter.parse_color("hsl(0, 50%, 50%)")
        result2 = self.converter.parse_color("hsl(360, 50%, 50%)")
        result3 = self.converter.parse_color("hsl(720, 50%, 50%)")

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        # Should be approximately equal due to hue wrapping
        r1, _g1, _b1, _a1 = result1
        r2, _g2, _b2, _a2 = result2
        r3, _g3, _b3, _a3 = result3

        assert abs(r1 - r2) < 0.01
        assert abs(r1 - r3) < 0.01

        # Values that need clamping
        result = self.converter.parse_color("hsl(180, 150%, -10%)")
        assert result is not None
        r, g, b, _a = result
        # Should be clamped to valid ranges
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1

    def test_hsla_parsing_edge_cases(self):
        """Test HSLA parsing with edge cases."""
        # Alpha at boundaries
        result = self.converter.parse_color("hsla(180, 50%, 50%, 0)")
        assert result is not None
        r, g, b, a = result
        assert a == 0.0

        result = self.converter.parse_color("hsla(180, 50%, 50%, 1)")
        assert result is not None
        r, g, b, a = result
        assert a == 1.0

        # Alpha as percentage
        result = self.converter.parse_color("hsla(180, 50%, 50%, 50%)")
        assert result is not None
        r, g, b, a = result
        assert a == 0.5

        # Alpha values that need clamping
        result = self.converter.parse_color("hsla(180, 50%, 50%, 2)")
        assert result is not None
        r, g, b, a = result
        assert a == 1.0  # Clamped from 2

        result = self.converter.parse_color("hsla(180, 50%, 50%, -0.5)")
        assert result is not None
        _r, _g, _b, a = result
        assert a == 0.0  # Clamped from -0.5

    def test_hsb_validation(self):
        """Test HSB color validation."""
        # Valid HSB colors
        assert self.converter.is_valid_hsb_color("hsb(180, 50%, 50%)")
        assert self.converter.is_valid_hsb_color("hsb(180deg, 50%, 50%)")
        assert self.converter.is_valid_hsb_color("HSB(180, 50%, 50%)")
        assert self.converter.is_valid_hsb_color("hsb( 180 , 50% , 50% )")
        assert self.converter.is_valid_hsb_color("hsb(0, 0%, 0%)")
        assert self.converter.is_valid_hsb_color("hsb(360, 100%, 100%)")

        # Invalid HSB colors
        assert not self.converter.is_valid_hsb_color("")
        assert not self.converter.is_valid_hsb_color("hsb(180, 50%)")
        assert not self.converter.is_valid_hsb_color("hsb(180, 50%, 50%, 50%)")
        assert not self.converter.is_valid_hsb_color("hsb(180, 150%, 50%)")
        assert not self.converter.is_valid_hsb_color("hsb(180, -10%, 50%)")
        assert not self.converter.is_valid_hsb_color("hsb(180, 50%, 50%")
        assert not self.converter.is_valid_hsb_color("180, 50%, 50%")

    def test_hsv_validation(self):
        """Test HSV color validation."""
        # Valid HSV colors
        assert self.converter.is_valid_hsv_color("hsv(180, 50%, 50%)")
        assert self.converter.is_valid_hsv_color("hsv(180deg, 50%, 50%)")
        assert self.converter.is_valid_hsv_color("HSV(180, 50%, 50%)")
        assert self.converter.is_valid_hsv_color("hsv( 180 , 50% , 50% )")
        assert self.converter.is_valid_hsv_color("hsv(0, 0%, 0%)")
        assert self.converter.is_valid_hsv_color("hsv(360, 100%, 100%)")

        # Invalid HSV colors
        assert not self.converter.is_valid_hsv_color("")
        assert not self.converter.is_valid_hsv_color("hsv(180, 50%)")
        assert not self.converter.is_valid_hsv_color("hsv(180, 50%, 50%, 50%)")
        assert not self.converter.is_valid_hsv_color("hsv(180, 150%, 50%)")
        assert not self.converter.is_valid_hsv_color("hsv(180, -10%, 50%)")
        assert not self.converter.is_valid_hsv_color("hsv(180, 50%, 50%")
        assert not self.converter.is_valid_hsv_color("180, 50%, 50%")

    def test_hsb_parsing_edge_cases(self):
        """Test HSB parsing with edge cases."""
        # Hue wrapping
        result1 = self.converter.parse_color("hsb(0, 50%, 50%)")
        result2 = self.converter.parse_color("hsb(360, 50%, 50%)")
        result3 = self.converter.parse_color("hsb(720, 50%, 50%)")

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        # Should be approximately equal due to hue wrapping
        r1, _g1, _b1, _a1 = result1
        r2, _g2, _b2, _a2 = result2
        r3, _g3, _b3, _a3 = result3

        assert abs(r1 - r2) < 0.01
        assert abs(r1 - r3) < 0.01

        # Values that need clamping
        result = self.converter.parse_color("hsb(180, 150%, -10%)")
        assert result is not None
        r, g, b, _a = result
        # Should be clamped to valid ranges
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1

    def test_hsv_parsing_edge_cases(self):
        """Test HSV parsing with edge cases."""
        # HSV should behave identically to HSB
        hsb_result = self.converter.parse_color("hsb(180, 50%, 75%)")
        hsv_result = self.converter.parse_color("hsv(180, 50%, 75%)")

        assert hsb_result is not None
        assert hsv_result is not None

        # Should be identical
        r1, g1, b1, a1 = hsb_result
        r2, g2, b2, a2 = hsv_result

        assert abs(r1 - r2) < 0.001
        assert abs(g1 - g2) < 0.001
        assert abs(b1 - b2) < 0.001
        assert a1 == a2

        # Test with degrees
        result = self.converter.parse_color("hsv(180deg, 50%, 75%)")
        assert result is not None

        # Values that need clamping
        result = self.converter.parse_color("hsv(180, 150%, -10%)")
        assert result is not None
        r, g, b, _a = result
        # Should be clamped to valid ranges
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1

    def test_hwb_validation(self):
        """Test HWB color validation."""
        # Valid HWB colors
        assert self.converter.is_valid_hwb_color("hwb(180, 50%, 25%)")
        assert self.converter.is_valid_hwb_color("hwb(180deg, 50%, 25%)")
        assert self.converter.is_valid_hwb_color("HWB(180, 50%, 25%)")
        assert self.converter.is_valid_hwb_color("hwb( 180 , 50% , 25% )")
        assert self.converter.is_valid_hwb_color("hwb(0, 0%, 0%)")
        assert self.converter.is_valid_hwb_color("hwb(360, 100%, 100%)")

        # Invalid HWB colors
        assert not self.converter.is_valid_hwb_color("")
        assert not self.converter.is_valid_hwb_color("hwb(180, 50%)")
        assert not self.converter.is_valid_hwb_color("hwb(180, 50%, 25%, 50%)")
        assert not self.converter.is_valid_hwb_color("hwb(180, 150%, 25%)")
        assert not self.converter.is_valid_hwb_color("hwb(180, -10%, 25%)")
        assert not self.converter.is_valid_hwb_color("hwb(180, 50%, 25%")
        assert not self.converter.is_valid_hwb_color("180, 50%, 25%")

    def test_hwb_parsing_edge_cases(self):
        """Test HWB parsing with edge cases."""
        # Hue wrapping
        result1 = self.converter.parse_color("hwb(0, 20%, 30%)")
        result2 = self.converter.parse_color("hwb(360, 20%, 30%)")
        result3 = self.converter.parse_color("hwb(720, 20%, 30%)")

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        # Should be approximately equal due to hue wrapping
        r1, _g1, _b1, _a1 = result1
        r2, _g2, _b2, _a2 = result2
        r3, _g3, _b3, _a3 = result3

        assert abs(r1 - r2) < 0.01
        assert abs(r1 - r3) < 0.01

        # Test when whiteness + blackness >= 1 (should produce gray)
        result = self.converter.parse_color("hwb(180, 60%, 50%)")
        assert result is not None
        r, g, b, a = result
        # Should be a shade of gray (r ≈ g ≈ b)
        assert abs(r - g) < 0.01
        assert abs(g - b) < 0.01

        # Values that need clamping
        result = self.converter.parse_color("hwb(180, 150%, -10%)")
        assert result is not None
        r, g, b, _a = result
        # Should be clamped to valid ranges
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1

        # Test with degrees
        result = self.converter.parse_color("hwb(180deg, 20%, 30%)")
        assert result is not None

    def test_cmyk_validation(self):
        """Test CMYK color validation."""
        # Valid CMYK colors
        assert self.converter.is_valid_cmyk_color("cmyk(50%, 25%, 75%, 10%)")
        assert self.converter.is_valid_cmyk_color("CMYK(50%, 25%, 75%, 10%)")
        assert self.converter.is_valid_cmyk_color("cmyk( 50% , 25% , 75% , 10% )")
        assert self.converter.is_valid_cmyk_color("cmyk(0%, 0%, 0%, 0%)")
        assert self.converter.is_valid_cmyk_color("cmyk(100%, 100%, 100%, 100%)")

        # Invalid CMYK colors
        assert not self.converter.is_valid_cmyk_color("")
        assert not self.converter.is_valid_cmyk_color("cmyk(50%, 25%, 75%)")
        assert not self.converter.is_valid_cmyk_color("cmyk(50%, 25%, 75%, 10%, 5%)")
        assert not self.converter.is_valid_cmyk_color("cmyk(150%, 25%, 75%, 10%)")
        assert not self.converter.is_valid_cmyk_color("cmyk(-10%, 25%, 75%, 10%)")
        assert not self.converter.is_valid_cmyk_color("cmyk(50%, 25%, 75%, 10%")
        assert not self.converter.is_valid_cmyk_color("50%, 25%, 75%, 10%")
        assert not self.converter.is_valid_cmyk_color("cmyk(50, 25%, 75%, 10%)")

    def test_cmyk_parsing_edge_cases(self):
        """Test CMYK parsing with edge cases."""
        # Values that need clamping
        result = self.converter.parse_color("cmyk(150%, -10%, 75%, 200%)")
        assert result is not None
        r, g, b, a = result
        # Should be clamped to valid ranges
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1

        # Pure black (K=100%)
        result = self.converter.parse_color("cmyk(0%, 0%, 0%, 100%)")
        assert result is not None
        r, g, b, a = result
        assert r == 0 and g == 0 and b == 0

        # Pure white (all 0%)
        result = self.converter.parse_color("cmyk(0%, 0%, 0%, 0%)")
        assert result is not None
        r, g, b, a = result
        assert r == 1 and g == 1 and b == 1

        # Pure cyan
        result = self.converter.parse_color("cmyk(100%, 0%, 0%, 0%)")
        assert result is not None
        r, g, b, a = result
        assert r == 0 and g == 1 and b == 1

        # Pure magenta
        result = self.converter.parse_color("cmyk(0%, 100%, 0%, 0%)")
        assert result is not None
        r, g, b, a = result
        assert r == 1 and g == 0 and b == 1

        # Pure yellow
        result = self.converter.parse_color("cmyk(0%, 0%, 100%, 0%)")
        assert result is not None
        r, g, b, _a = result
        assert r == 1 and g == 1 and b == 0
