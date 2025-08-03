import colorsys
import logging
import random
import re
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# It's good practice to have a logger
logger = logging.getLogger(__name__)


class ColorConverter:
    """Backend class for color format conversion operations."""

    def __init__(self):
        """Initialize the ColorConverter."""
        logger.info("Initializing ColorConverter")

    # ruff: noqa: C901
    def parse_color(self, color_input: str) -> tuple[float, float, float, float] | None:
        """Parse color input and return RGBA values (0-1 range).

        Args:
            color_input: Color string in various formats

        Returns:
            Tuple of (r, g, b, a) values in 0-1 range, or None if invalid
        """
        if not color_input:
            return None

        color_input = color_input.strip()

        # Hex format (#RGB, #RGBA, #RRGGBB, #RRGGBBAA)
        hex_match = re.match(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$", color_input)
        if hex_match:
            hex_value = hex_match.group(1)
            return self._parse_hex(hex_value)

        # RGB format
        rgb_match = re.match(r"^rgb\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if rgb_match:
            return self._parse_rgb(rgb_match.group(1))

        # RGBA format
        rgba_match = re.match(r"^rgba\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if rgba_match:
            return self._parse_rgba(rgba_match.group(1))

        # HSL format
        hsl_match = re.match(r"^hsl\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if hsl_match:
            return self._parse_hsl(hsl_match.group(1))

        # HSLA format
        hsla_match = re.match(r"^hsla\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if hsla_match:
            return self._parse_hsla(hsla_match.group(1))

        # HSB/HSV format
        hsb_match = re.match(r"^hsb\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if hsb_match:
            return self._parse_hsb(hsb_match.group(1))

        # HSV format (alias for HSB)
        hsv_match = re.match(r"^hsv\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if hsv_match:
            return self._parse_hsv(hsv_match.group(1))

        # HWB format
        hwb_match = re.match(r"^hwb\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if hwb_match:
            return self._parse_hwb(hwb_match.group(1))

        # CMYK format
        cmyk_match = re.match(r"^cmyk\s*\(\s*([^)]+)\s*\)$", color_input, re.IGNORECASE)
        if cmyk_match:
            return self._parse_cmyk(cmyk_match.group(1))

        return None

    def is_valid_hex_color(self, hex_input: str) -> bool:
        """Validate if input is a valid hex color format.

        Args:
            hex_input: Color string to validate

        Returns:
            True if valid hex color, False otherwise
        """
        if not hex_input:
            return False

        hex_input = hex_input.strip()

        # Check for # prefix and valid hex characters
        hex_match = re.match(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$", hex_input)
        return hex_match is not None

    def normalize_hex_color(self, hex_input: str) -> str | None:
        """Normalize hex color to standard format.

        Args:
            hex_input: Hex color string

        Returns:
            Normalized hex color string or None if invalid
        """
        if not self.is_valid_hex_color(hex_input):
            return None

        hex_input = hex_input.strip().upper()
        hex_value = hex_input[1:]  # Remove #

        if len(hex_value) == 3:  # #RGB -> #RRGGBB
            return f"#{hex_value[0] * 2}{hex_value[1] * 2}{hex_value[2] * 2}"
        elif len(hex_value) == 4:  # #RGBA -> #RRGGBBAA
            return f"#{hex_value[0] * 2}{hex_value[1] * 2}{hex_value[2] * 2}{hex_value[3] * 2}"
        elif len(hex_value) == 6 or len(hex_value) == 8:  # #RRGGBB
            return hex_input

        return None

    def _parse_hex(self, hex_value: str) -> tuple[float, float, float, float] | None:
        """Parse hex color value with enhanced validation.

        Args:
            hex_value: Hex color value without # prefix

        Returns:
            RGBA tuple or None if invalid
        """
        try:
            # Validate hex characters
            if not re.match(r"^[0-9A-Fa-f]+$", hex_value):
                return None

            if len(hex_value) == 3:  # #RGB
                r = int(hex_value[0] * 2, 16) / 255.0
                g = int(hex_value[1] * 2, 16) / 255.0
                b = int(hex_value[2] * 2, 16) / 255.0
                a = 1.0
            elif len(hex_value) == 4:  # #RGBA
                r = int(hex_value[0] * 2, 16) / 255.0
                g = int(hex_value[1] * 2, 16) / 255.0
                b = int(hex_value[2] * 2, 16) / 255.0
                a = int(hex_value[3] * 2, 16) / 255.0
            elif len(hex_value) == 6:  # #RRGGBB
                r = int(hex_value[0:2], 16) / 255.0
                g = int(hex_value[2:4], 16) / 255.0
                b = int(hex_value[4:6], 16) / 255.0
                a = 1.0
            elif len(hex_value) == 8:  # #RRGGBBAA
                r = int(hex_value[0:2], 16) / 255.0
                g = int(hex_value[2:4], 16) / 255.0
                b = int(hex_value[4:6], 16) / 255.0
                a = int(hex_value[6:8], 16) / 255.0
            else:
                return None

            # Ensure values are in valid range
            r = max(0.0, min(1.0, r))
            g = max(0.0, min(1.0, g))
            b = max(0.0, min(1.0, b))
            a = max(0.0, min(1.0, a))

            return (r, g, b, a)
        except (ValueError, IndexError):
            return None

    def is_valid_rgb_color(self, rgb_input: str) -> bool:
        """Validate if input is a valid RGB color format.

        Args:
            rgb_input: Color string to validate

        Returns:
            True if valid RGB color, False otherwise
        """
        if not rgb_input:
            return False

        rgb_input = rgb_input.strip()

        # Check RGB format
        rgb_match = re.match(r"^rgb\s*\(\s*([^)]+)\s*\)$", rgb_input, re.IGNORECASE)
        if rgb_match:
            return self._validate_rgb_components(rgb_match.group(1), 3)

        return False

    def is_valid_rgba_color(self, rgba_input: str) -> bool:
        """Validate if input is a valid RGBA color format.

        Args:
            rgba_input: Color string to validate

        Returns:
            True if valid RGBA color, False otherwise
        """
        if not rgba_input:
            return False

        rgba_input = rgba_input.strip()

        # Check RGBA format
        rgba_match = re.match(r"^rgba\s*\(\s*([^)]+)\s*\)$", rgba_input, re.IGNORECASE)
        if rgba_match:
            return self._validate_rgb_components(rgba_match.group(1), 4)

        return False

    def _validate_rgb_components(self, components: str, expected_count: int) -> bool:
        """Validate RGB/RGBA component values.

        Args:
            components: Comma-separated component values
            expected_count: Expected number of components (3 for RGB, 4 for RGBA)

        Returns:
            True if valid components, False otherwise
        """
        try:
            parts = [p.strip() for p in components.split(",")]
            if len(parts) != expected_count:
                return False

            # Validate RGB components (0-255 or 0-100%)
            for i in range(3):
                if not self._is_valid_rgb_component(parts[i]):
                    return False

            # Validate alpha component if present (0-1 or 0-100%)
            return not (expected_count == 4 and not self._is_valid_alpha_component(parts[3]))
        except (ValueError, IndexError):
            return False

    def _is_valid_rgb_component(self, component: str) -> bool:
        """Check if RGB component is valid (0-255 or 0-100%)."""
        try:
            component = component.strip()
            if component.endswith("%"):
                value = float(component[:-1])
                return 0 <= value <= 100
            else:
                value = float(component)
                return 0 <= value <= 255
        except ValueError:
            return False

    def _is_valid_alpha_component(self, component: str) -> bool:
        """Check if alpha component is valid (0-1 or 0-100%)."""
        try:
            component = component.strip()
            if component.endswith("%"):
                value = float(component[:-1])
                return 0 <= value <= 100
            else:
                value = float(component)
                return 0 <= value <= 1
        except ValueError:
            return False

    def _parse_rgb(self, rgb_values: str) -> tuple[float, float, float, float] | None:
        """Parse RGB color values with enhanced validation.

        Args:
            rgb_values: Comma-separated RGB values

        Returns:
            RGBA tuple or None if invalid
        """
        try:
            parts = [p.strip() for p in rgb_values.split(",")]
            if len(parts) != 3:
                return None

            r = self._parse_color_component(parts[0], 255)
            g = self._parse_color_component(parts[1], 255)
            b = self._parse_color_component(parts[2], 255)

            if r is None or g is None or b is None:
                return None

            # Clamp values to valid range
            r = max(0.0, min(1.0, r))
            g = max(0.0, min(1.0, g))
            b = max(0.0, min(1.0, b))

            return (r, g, b, 1.0)
        except (ValueError, IndexError):
            return None

    def _parse_rgba(self, rgba_values: str) -> tuple[float, float, float, float] | None:
        """Parse RGBA color values with enhanced validation.

        Args:
            rgba_values: Comma-separated RGBA values

        Returns:
            RGBA tuple or None if invalid
        """
        try:
            parts = [p.strip() for p in rgba_values.split(",")]
            if len(parts) != 4:
                return None

            r = self._parse_color_component(parts[0], 255)
            g = self._parse_color_component(parts[1], 255)
            b = self._parse_color_component(parts[2], 255)
            a = self._parse_color_component(parts[3], 1)

            if r is None or g is None or b is None or a is None:
                return None

            # Clamp values to valid range
            r = max(0.0, min(1.0, r))
            g = max(0.0, min(1.0, g))
            b = max(0.0, min(1.0, b))
            a = max(0.0, min(1.0, a))

            return (r, g, b, a)
        except (ValueError, IndexError):
            return None

    def is_valid_hsl_color(self, hsl_input: str) -> bool:
        """Validate if input is a valid HSL color format.

        Args:
            hsl_input: Color string to validate

        Returns:
            True if valid HSL color, False otherwise
        """
        if not hsl_input:
            return False

        hsl_input = hsl_input.strip()

        # Check HSL format
        hsl_match = re.match(r"^hsl\s*\(\s*([^)]+)\s*\)$", hsl_input, re.IGNORECASE)
        if hsl_match:
            return self._validate_hsl_components(hsl_match.group(1), 3)

        return False

    def is_valid_hsla_color(self, hsla_input: str) -> bool:
        """Validate if input is a valid HSLA color format.

        Args:
            hsla_input: Color string to validate

        Returns:
            True if valid HSLA color, False otherwise
        """
        if not hsla_input:
            return False

        hsla_input = hsla_input.strip()

        # Check HSLA format
        hsla_match = re.match(r"^hsla\s*\(\s*([^)]+)\s*\)$", hsla_input, re.IGNORECASE)
        if hsla_match:
            return self._validate_hsl_components(hsla_match.group(1), 4)

        return False

    def _validate_hsl_components(self, components: str, expected_count: int) -> bool:
        """Validate HSL/HSLA component values.

        Args:
            components: Comma-separated component values
            expected_count: Expected number of components (3 for HSL, 4 for HSLA)

        Returns:
            True if valid components, False otherwise
        """
        try:
            parts = [p.strip() for p in components.split(",")]
            if len(parts) != expected_count:
                return False

            # Validate hue component (0-360 degrees or 0-360)
            if not self._is_valid_hue_component(parts[0]):
                return False

            # Validate saturation and lightness components (0-100%)
            for i in range(1, 3):
                if not self._is_valid_percentage_component(parts[i]):
                    return False

            # Validate alpha component if present (0-1 or 0-100%)
            return not (expected_count == 4 and not self._is_valid_alpha_component(parts[3]))
        except (ValueError, IndexError):
            return False

    def _is_valid_hue_component(self, component: str) -> bool:
        """Check if hue component is valid (0-360 or 0-360deg)."""
        try:
            component = component.strip()
            float(component[:-3]) if component.endswith("deg") else float(component)
            # Hue can be any value, it wraps around
            return True
        except ValueError:
            return False

    def _is_valid_percentage_component(self, component: str) -> bool:
        """Check if percentage component is valid (0-100%)."""
        try:
            component = component.strip()
            if component.endswith("%"):
                value = float(component[:-1])
                return 0 <= value <= 100
            else:
                # Allow numeric values that will be treated as percentages
                value = float(component)
                return 0 <= value <= 100
        except ValueError:
            return False

    def _parse_hsl(self, hsl_values: str) -> tuple[float, float, float, float] | None:
        """Parse HSL color values with enhanced validation.

        Args:
            hsl_values: Comma-separated HSL values

        Returns:
            RGBA tuple or None if invalid
        """
        try:
            parts = [p.strip() for p in hsl_values.split(",")]
            if len(parts) != 3:
                return None

            h = self._parse_hue(parts[0])
            s = self._parse_percentage(parts[1])
            l = self._parse_percentage(parts[2])

            if h is None or s is None or l is None:
                return None

            # Clamp values to valid range
            h = h % 1.0  # Hue wraps around
            s = max(0.0, min(1.0, s))
            l = max(0.0, min(1.0, l))

            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return (r, g, b, 1.0)
        except (ValueError, IndexError):
            return None

    def _parse_hsla(self, hsla_values: str) -> tuple[float, float, float, float] | None:
        """Parse HSLA color values with enhanced validation.

        Args:
            hsla_values: Comma-separated HSLA values

        Returns:
            RGBA tuple or None if invalid
        """
        try:
            parts = [p.strip() for p in hsla_values.split(",")]
            if len(parts) != 4:
                return None

            h = self._parse_hue(parts[0])
            s = self._parse_percentage(parts[1])
            l = self._parse_percentage(parts[2])
            a = self._parse_color_component(parts[3], 1)

            if h is None or s is None or l is None or a is None:
                return None

            # Clamp values to valid range
            h = h % 1.0  # Hue wraps around
            s = max(0.0, min(1.0, s))
            l = max(0.0, min(1.0, l))
            a = max(0.0, min(1.0, a))

            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return (r, g, b, a)
        except (ValueError, IndexError):
            return None

    def is_valid_hsb_color(self, hsb_input: str) -> bool:
        """Validate if input is a valid HSB/HSV color format.

        Args:
            hsb_input: Color string to validate

        Returns:
            True if valid HSB color, False otherwise
        """
        if not hsb_input:
            return False

        hsb_input = hsb_input.strip()

        # Check HSB format
        hsb_match = re.match(r"^hsb\s*\(\s*([^)]+)\s*\)$", hsb_input, re.IGNORECASE)
        if hsb_match:
            return self._validate_hsl_components(hsb_match.group(1), 3)  # Same validation as HSL

        return False

    def is_valid_hsv_color(self, hsv_input: str) -> bool:
        """Validate if input is a valid HSV color format.

        Args:
            hsv_input: Color string to validate

        Returns:
            True if valid HSV color, False otherwise
        """
        if not hsv_input:
            return False

        hsv_input = hsv_input.strip()

        # Check HSV format
        hsv_match = re.match(r"^hsv\s*\(\s*([^)]+)\s*\)$", hsv_input, re.IGNORECASE)
        if hsv_match:
            return self._validate_hsl_components(hsv_match.group(1), 3)  # Same validation as HSL

        return False

    def _parse_hsb(self, hsb_values: str) -> tuple[float, float, float, float] | None:
        """Parse HSB/HSV color values with enhanced validation.

        Args:
            hsb_values: Comma-separated HSB values

        Returns:
            RGBA tuple or None if invalid
        """
        try:
            parts = [p.strip() for p in hsb_values.split(",")]
            if len(parts) != 3:
                return None

            h = self._parse_hue(parts[0])
            s = self._parse_percentage(parts[1])
            b = self._parse_percentage(parts[2])

            if h is None or s is None or b is None:
                return None

            # Clamp values to valid range
            h = h % 1.0  # Hue wraps around
            s = max(0.0, min(1.0, s))
            b = max(0.0, min(1.0, b))

            r, g, b_rgb = colorsys.hsv_to_rgb(h, s, b)
            return (r, g, b_rgb, 1.0)
        except (ValueError, IndexError):
            return None

    def _parse_hsv(self, hsv_values: str) -> tuple[float, float, float, float] | None:
        """Parse HSV color values (alias for HSB).

        Args:
            hsv_values: Comma-separated HSV values

        Returns:
            RGBA tuple or None if invalid
        """
        return self._parse_hsb(hsv_values)

    def is_valid_hwb_color(self, color_str: str) -> bool:
        """Check if a string is a valid HWB color format.

        Args:
            color_str: Color string to validate

        Returns:
            True if valid HWB format, False otherwise
        """
        if not color_str or not isinstance(color_str, str):
            return False

        color_str = color_str.strip().lower()
        if not color_str.startswith("hwb(") or not color_str.endswith(")"):
            return False

        try:
            values = color_str[4:-1].strip()
            parts = [p.strip() for p in values.split(",")]

            if len(parts) != 3:
                return False

            # Validate hue component
            if not self._is_valid_hue_component(parts[0]):
                return False

            # Validate whiteness and blackness components (percentages)
            if not self._is_valid_percentage_component(parts[1]):
                return False
            return self._is_valid_percentage_component(parts[2])
        except:  # noqa: E722
            return False

    def _parse_hwb(self, hwb_values: str) -> tuple[float, float, float, float] | None:
        """Parse HWB color values with enhanced validation and clamping."""
        try:
            parts = [p.strip() for p in hwb_values.split(",")]
            if len(parts) != 3:
                return None

            h = self._parse_hue(parts[0])
            w = self._parse_percentage(parts[1])
            b = self._parse_percentage(parts[2])

            if h is None or w is None or b is None:
                return None

            # Clamp values to valid ranges
            h = max(0, min(1, h))
            w = max(0, min(1, w))
            b = max(0, min(1, b))

            # Convert HWB to RGB
            if w + b >= 1:
                # When w + b >= 1, the color becomes a shade of gray
                gray = w / (w + b) if (w + b) > 0 else 0
                gray = max(0, min(1, gray))
                return (gray, gray, gray, 1.0)

            # Standard HWB to RGB conversion
            r, g, b_rgb = colorsys.hsv_to_rgb(h, 1 - w / (1 - b), 1 - b)

            # Clamp final RGB values
            r = max(0, min(1, r))
            g = max(0, min(1, g))
            b_rgb = max(0, min(1, b_rgb))

            return (r, g, b_rgb, 1.0)
        except (ValueError, IndexError, ZeroDivisionError):
            return None

    def is_valid_cmyk_color(self, color_str: str) -> bool:
        """Check if a string is a valid CMYK color format.

        Args:
            color_str: Color string to validate

        Returns:
            True if valid CMYK format, False otherwise
        """
        if not color_str or not isinstance(color_str, str):
            return False

        color_str = color_str.strip().lower()
        if not color_str.startswith("cmyk(") or not color_str.endswith(")"):
            return False

        try:
            values = color_str[5:-1].strip()
            parts = [p.strip() for p in values.split(",")]

            if len(parts) != 4:
                return False

            # Validate all components as percentages (must have % sign)
            for part in parts:
                part = part.strip()
                if not part.endswith("%"):
                    return False
                try:
                    value = float(part[:-1])
                    if not (0 <= value <= 100):
                        return False
                except ValueError:
                    return False

            return True
        except:  # noqa: E722
            return False

    def _parse_cmyk(self, cmyk_values: str) -> tuple[float, float, float, float] | None:
        """Parse CMYK color values with enhanced validation and clamping."""
        try:
            parts = [p.strip() for p in cmyk_values.split(",")]
            if len(parts) != 4:
                return None

            c = self._parse_percentage(parts[0])
            m = self._parse_percentage(parts[1])
            y = self._parse_percentage(parts[2])
            k = self._parse_percentage(parts[3])

            if c is None or m is None or y is None or k is None:
                return None

            # Clamp values to valid ranges
            c = max(0, min(1, c))
            m = max(0, min(1, m))
            y = max(0, min(1, y))
            k = max(0, min(1, k))

            # Convert CMYK to RGB
            r = (1 - c) * (1 - k)
            g = (1 - m) * (1 - k)
            b = (1 - y) * (1 - k)

            # Clamp final RGB values
            r = max(0, min(1, r))
            g = max(0, min(1, g))
            b = max(0, min(1, b))

            return (r, g, b, 1.0)
        except (ValueError, IndexError, ZeroDivisionError):
            return None

    def _parse_color_component(self, value: str, max_value: int | float) -> float | None:
        """Parse a color component value with enhanced validation.

        Args:
            value: Component value string
            max_value: Maximum value for non-percentage values

        Returns:
            Normalized component value (0-1) or None if invalid
        """
        try:
            value = value.strip()
            if value.endswith("%"):
                percent_value = float(value[:-1])
                # Clamp percentage values
                percent_value = max(0.0, min(100.0, percent_value))
                return percent_value / 100.0
            else:
                numeric_value = float(value)
                # Clamp numeric values
                numeric_value = max(0.0, min(max_value, numeric_value))
                return numeric_value / max_value
        except ValueError:
            return None

    def _parse_percentage(self, value: str) -> float | None:
        """Parse a percentage value with enhanced validation.

        Args:
            value: Percentage value string

        Returns:
            Normalized percentage value (0-1) or None if invalid
        """
        try:
            value = value.strip()
            if value.endswith("%"):
                percent_value = float(value[:-1])
                # Clamp percentage values
                percent_value = max(0.0, min(100.0, percent_value))
                return percent_value / 100.0
            else:
                # Treat as percentage value without % sign
                percent_value = float(value)
                percent_value = max(0.0, min(100.0, percent_value))
                return percent_value / 100.0
        except ValueError:
            return None

    def _parse_hue(self, value: str) -> float | None:
        """Parse a hue value with enhanced validation.

        Args:
            value: Hue value string

        Returns:
            Normalized hue value (0-1) or None if invalid
        """
        try:
            value = value.strip()
            hue = float(value[:-3]) if value.endswith("deg") else float(value)
            # Hue wraps around, so normalize to 0-1 range
            return (hue % 360) / 360.0
        except ValueError:
            return None

    def to_hex(self, r: float, g: float, b: float, a: float = 1.0, include_alpha: bool | None = None) -> str:
        """Convert RGBA to hex format with enhanced options.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1)
            include_alpha: Force include/exclude alpha. If None, auto-decide based on alpha value

        Returns:
            Hex color string
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))
        a = max(0.0, min(1.0, a))

        r_int = round(r * 255)
        g_int = round(g * 255)
        b_int = round(b * 255)

        # Decide whether to include alpha
        if include_alpha is None:
            include_alpha = a < 1.0

        if include_alpha:
            a_int = round(a * 255)
            return f"#{r_int:02X}{g_int:02X}{b_int:02X}{a_int:02X}"
        else:
            return f"#{r_int:02X}{g_int:02X}{b_int:02X}"

    def to_hex_short(self, r: float, g: float, b: float, a: float = 1.0) -> str | None:
        """Convert RGBA to short hex format if possible (e.g., #F0A instead of #FF00AA).

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1)

        Returns:
            Short hex color string if possible, None if not representable in short form
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))
        a = max(0.0, min(1.0, a))

        r_int = round(r * 255)
        g_int = round(g * 255)
        b_int = round(b * 255)
        a_int = round(a * 255)

        # Check if values can be represented in short form (each component is 0x00, 0x11, 0x22, ..., 0xFF)
        def can_be_short(value):
            return value % 17 == 0  # 0x11 = 17 in decimal

        if not (can_be_short(r_int) and can_be_short(g_int) and can_be_short(b_int)):
            return None

        r_short = r_int // 17
        g_short = g_int // 17
        b_short = b_int // 17

        if a < 1.0:
            if not can_be_short(a_int):
                return None
            a_short = a_int // 17
            return f"#{r_short:X}{g_short:X}{b_short:X}{a_short:X}"
        else:
            return f"#{r_short:X}{g_short:X}{b_short:X}"

    def to_rgb(self, r: float, g: float, b: float, a: float = 1.0, use_percentages: bool = False) -> str:
        """Convert RGBA to RGB format with enhanced options.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1) - ignored for RGB output
            use_percentages: If True, use percentage values instead of 0-255

        Returns:
            RGB color string
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))

        if use_percentages:
            r_val = round(r * 100, 1)
            g_val = round(g * 100, 1)
            b_val = round(b * 100, 1)
            return f"rgb({r_val}%, {g_val}%, {b_val}%)"
        else:
            r_int = round(r * 255)
            g_int = round(g * 255)
            b_int = round(b * 255)
            return f"rgb({r_int}, {g_int}, {b_int})"

    def to_rgba(
        self,
        r: float,
        g: float,
        b: float,
        a: float = 1.0,
        use_percentages: bool = False,
        alpha_as_percentage: bool = False,
    ) -> str:
        """Convert RGBA to RGBA format with enhanced options.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1)
            use_percentages: If True, use percentage values for RGB components
            alpha_as_percentage: If True, use percentage for alpha component

        Returns:
            RGBA color string
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))
        a = max(0.0, min(1.0, a))

        if use_percentages:
            r_val = round(r * 100, 1)
            g_val = round(g * 100, 1)
            b_val = round(b * 100, 1)
            rgb_part = f"{r_val}%, {g_val}%, {b_val}%"
        else:
            r_int = round(r * 255)
            g_int = round(g * 255)
            b_int = round(b * 255)
            rgb_part = f"{r_int}, {g_int}, {b_int}"

        if alpha_as_percentage:
            a_val = round(a * 100, 1)
            return f"rgba({rgb_part}, {a_val}%)"
        else:
            return f"rgba({rgb_part}, {a})"

    def to_hsl(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HSL format with enhanced options.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1) - ignored for HSL output
            precision: Decimal precision for percentage values

        Returns:
            HSL color string
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))

        h, l, s = colorsys.rgb_to_hls(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        l_pct = round(l * 100, precision)

        if precision == 0:
            return f"hsl({int(h_deg)}, {int(s_pct)}%, {int(l_pct)}%)"
        else:
            return f"hsl({h_deg}, {s_pct}%, {l_pct}%)"

    def to_hsl_with_deg(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HSL format with explicit 'deg' suffix for hue.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1) - ignored for HSL output
            precision: Decimal precision for values

        Returns:
            HSL color string with 'deg' suffix
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))

        h, l, s = colorsys.rgb_to_hls(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        l_pct = round(l * 100, precision)

        if precision == 0:
            return f"hsl({int(h_deg)}deg, {int(s_pct)}%, {int(l_pct)}%)"
        else:
            return f"hsl({h_deg}deg, {s_pct}%, {l_pct}%)"

    def to_hsla(
        self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0, alpha_as_percentage: bool = True
    ) -> str:
        """Convert RGBA to HSLA format with enhanced options.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1)
            precision: Decimal precision for values
            alpha_as_percentage: If True, use percentage for alpha component

        Returns:
            HSLA color string
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))
        a = max(0.0, min(1.0, a))

        h, l, s = colorsys.rgb_to_hls(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        l_pct = round(l * 100, precision)

        if alpha_as_percentage:
            a_val = round(a * 100, precision)
            if precision == 0:
                return f"hsla({int(h_deg)}, {int(s_pct)}%, {int(l_pct)}%, {int(a_val)}%)"
            else:
                return f"hsla({h_deg}, {s_pct}%, {l_pct}%, {a_val}%)"
        else:
            a_val = round(a, max(1, precision))
            if precision == 0:
                return f"hsla({int(h_deg)}, {int(s_pct)}%, {int(l_pct)}%, {a_val})"
            else:
                return f"hsla({h_deg}, {s_pct}%, {l_pct}%, {a_val})"

    def to_hsla_with_deg(
        self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0, alpha_as_percentage: bool = True
    ) -> str:
        """Convert RGBA to HSLA format with explicit 'deg' suffix for hue.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1)
            precision: Decimal precision for values
            alpha_as_percentage: If True, use percentage for alpha component

        Returns:
            HSLA color string with 'deg' suffix
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))
        a = max(0.0, min(1.0, a))

        h, l, s = colorsys.rgb_to_hls(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        l_pct = round(l * 100, precision)

        if alpha_as_percentage:
            a_val = round(a * 100, precision)
            if precision == 0:
                return f"hsla({int(h_deg)}deg, {int(s_pct)}%, {int(l_pct)}%, {int(a_val)}%)"
            else:
                return f"hsla({h_deg}deg, {s_pct}%, {l_pct}%, {a_val}%)"
        else:
            a_val = round(a, max(1, precision))
            if precision == 0:
                return f"hsla({int(h_deg)}deg, {int(s_pct)}%, {int(l_pct)}%, {a_val})"
            else:
                return f"hsla({h_deg}deg, {s_pct}%, {l_pct}%, {a_val})"

    def to_hsb(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HSB format with enhanced options.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1) - ignored for HSB output
            precision: Decimal precision for percentage values

        Returns:
            HSB color string
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))

        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        v_pct = round(v * 100, precision)

        if precision == 0:
            return f"hsb({int(h_deg)}, {int(s_pct)}%, {int(v_pct)}%)"
        else:
            return f"hsb({h_deg}, {s_pct}%, {v_pct}%)"

    def to_hsv(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HSV format (alias for HSB).

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1) - ignored for HSV output
            precision: Decimal precision for percentage values

        Returns:
            HSV color string
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))

        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        v_pct = round(v * 100, precision)

        if precision == 0:
            return f"hsv({int(h_deg)}, {int(s_pct)}%, {int(v_pct)}%)"
        else:
            return f"hsv({h_deg}, {s_pct}%, {v_pct}%)"

    def to_hsb_with_deg(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HSB format with explicit 'deg' suffix for hue.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1) - ignored for HSB output
            precision: Decimal precision for values

        Returns:
            HSB color string with 'deg' suffix
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))

        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        v_pct = round(v * 100, precision)

        if precision == 0:
            return f"hsb({int(h_deg)}deg, {int(s_pct)}%, {int(v_pct)}%)"
        else:
            return f"hsb({h_deg}deg, {s_pct}%, {v_pct}%)"

    def to_hsv_with_deg(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HSV format with explicit 'deg' suffix for hue.

        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1) - ignored for HSV output
            precision: Decimal precision for values

        Returns:
            HSV color string with 'deg' suffix
        """
        # Clamp values to valid range
        r = max(0.0, min(1.0, r))
        g = max(0.0, min(1.0, g))
        b = max(0.0, min(1.0, b))

        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h_deg = round(h * 360, precision)
        s_pct = round(s * 100, precision)
        v_pct = round(v * 100, precision)

        if precision == 0:
            return f"hsv({int(h_deg)}deg, {int(s_pct)}%, {int(v_pct)}%)"
        else:
            return f"hsv({h_deg}deg, {s_pct}%, {v_pct}%)"

    def to_hwb(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HWB format.

        Args:
            r, g, b: RGB values (0-1)
            a: Alpha value (0-1, not used in HWB output)
            precision: Number of decimal places for percentages

        Returns:
            HWB color string
        """
        # Clamp input values
        r = max(0, min(1, r))
        g = max(0, min(1, g))
        b = max(0, min(1, b))

        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        w = (1 - s) * v
        b_val = 1 - v

        h_deg = round(h * 360, precision)
        w_pct = round(w * 100, precision)
        b_pct = round(b_val * 100, precision)

        if precision == 0:
            return f"hwb({int(h_deg)}, {int(w_pct)}%, {int(b_pct)}%)"
        else:
            return f"hwb({h_deg:.{precision}f}, {w_pct:.{precision}f}%, {b_pct:.{precision}f}%)"

    def to_hwb_with_deg(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to HWB format with explicit 'deg' suffix for hue.

        Args:
            r, g, b: RGB values (0-1)
            a: Alpha value (0-1, not used in HWB output)
            precision: Number of decimal places

        Returns:
            HWB color string with 'deg' suffix
        """
        # Clamp input values
        r = max(0, min(1, r))
        g = max(0, min(1, g))
        b = max(0, min(1, b))

        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        w = (1 - s) * v
        b_val = 1 - v

        h_deg = round(h * 360, precision)
        w_pct = round(w * 100, precision)
        b_pct = round(b_val * 100, precision)

        if precision == 0:
            return f"hwb({int(h_deg)}deg, {int(w_pct)}%, {int(b_pct)}%)"
        else:
            return f"hwb({h_deg:.{precision}f}deg, {w_pct:.{precision}f}%, {b_pct:.{precision}f}%)"

    def to_cmyk(self, r: float, g: float, b: float, a: float = 1.0, precision: int = 0) -> str:
        """Convert RGBA to CMYK format.

        Args:
            r, g, b: RGB values (0-1)
            a: Alpha value (0-1, not used in CMYK output)
            precision: Number of decimal places for percentages

        Returns:
            CMYK color string
        """
        # Clamp input values
        r = max(0, min(1, r))
        g = max(0, min(1, g))
        b = max(0, min(1, b))

        k = 1 - max(r, g, b)
        if k == 1:
            c = m = y = 0
        else:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)

        # Clamp CMYK values
        c = max(0, min(1, c))
        m = max(0, min(1, m))
        y = max(0, min(1, y))
        k = max(0, min(1, k))

        c_pct = round(c * 100, precision)
        m_pct = round(m * 100, precision)
        y_pct = round(y * 100, precision)
        k_pct = round(k * 100, precision)

        if precision == 0:
            return f"cmyk({int(c_pct)}%, {int(m_pct)}%, {int(y_pct)}%, {int(k_pct)}%)"
        else:
            return (
                f"cmyk({c_pct:.{precision}f}%, {m_pct:.{precision}f}%, {y_pct:.{precision}f}%, {k_pct:.{precision}f}%)"
            )

    def convert_all_formats(self, color_input: str) -> dict[str, str]:
        """Convert input color to all supported formats.

        Args:
            color_input: Color string in any supported format

        Returns:
            Dictionary with all color formats, or empty dict if invalid
        """
        rgba = self.parse_color(color_input)
        if rgba is None:
            return {}

        r, g, b, a = rgba

        return {
            "hex": self.to_hex(r, g, b),
            "hex_alpha": self.to_hex(r, g, b, a),
            "rgb": self.to_rgb(r, g, b),
            "rgba": self.to_rgba(r, g, b, a),
            "hsl": self.to_hsl(r, g, b),
            "hsla": self.to_hsla(r, g, b, a),
            "hsb": self.to_hsb(r, g, b),
            "hsv": self.to_hsv(r, g, b),
            "hwb": self.to_hwb(r, g, b),
            "cmyk": self.to_cmyk(r, g, b),
        }


# ruff: noqa: C901
def create_color_converter_widget():
    """
    Creates the Color Converter widget.

    Returns:
        QWidget: The complete Color Converter widget.
    """
    widget = QWidget()
    widget.setObjectName("mainWidget")

    # Initialize the color converter backend
    converter = ColorConverter()

    # Main horizontal layout
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # --- LEFT PANEL (INPUTS) ---
    left_panel = QWidget()
    left_panel.setObjectName("leftPanel")
    left_panel_layout = QVBoxLayout(left_panel)
    left_panel_layout.setContentsMargins(20, 20, 20, 20)
    left_panel_layout.setSpacing(15)
    left_panel.setFixedWidth(450)

    # Top input section
    input_section_layout = QVBoxLayout()
    input_section_layout.setSpacing(8)

    # Input header with buttons
    input_header_layout = QHBoxLayout()
    input_label = QLabel("Input:")
    input_header_layout.addWidget(input_label)
    input_header_layout.addStretch()

    # Create header buttons
    clipboard_btn = QPushButton("Clipboard")
    sample_btn = QPushButton("Sample")
    clear_btn = QPushButton("Clear")

    input_header_layout.addWidget(clipboard_btn)
    input_header_layout.addWidget(sample_btn)
    input_header_layout.addWidget(clear_btn)
    input_section_layout.addLayout(input_header_layout)

    # Input field and color preview
    input_field_layout = QHBoxLayout()
    input_field = QLineEdit()
    input_field.setPlaceholderText("(Enter any of the supported formats below)")
    input_field_layout.addWidget(input_field)

    color_preview = QLabel()
    color_preview.setObjectName("colorPreview")
    color_preview.setFixedSize(34, 34)
    color_preview.setCursor(Qt.CursorShape.PointingHandCursor)  # Show pointer cursor on hover
    input_field_layout.addWidget(color_preview)

    input_section_layout.addLayout(input_field_layout)
    left_panel_layout.addLayout(input_section_layout)

    # Grid for color formats
    formats_layout = QGridLayout()
    formats_layout.setHorizontalSpacing(10)
    formats_layout.setVerticalSpacing(12)

    # Data for the format rows
    formats_data = {
        "Hex": "#5CCC7F",
        "Hex with alpha": "#5CCC7FFF",
        "RGB": "rgb(92, 204, 127)",
        "RGBA": "rgba(92, 204, 127, 1)",
        "HSL": "hsl(139, 52%, 58%)",
        "HSLA": "hsla(139, 52%, 58%, 100%)",
        "HSB (HSV)": "hsb(139, 55%, 80%)",
        "HWB": "hwb(139, 36%, 20%)",
        "CMYK": "cmyk(55%, 0%, 38%, 20%)",
    }

    # Store format line edits for updating
    format_line_edits = {}

    # Create and add format rows to the grid
    for index, (label_text, value_text) in enumerate(formats_data.items()):
        label = QLabel(f"{label_text}:")
        line_edit = QLineEdit(value_text)
        line_edit.setReadOnly(True)  # Make output fields read-only
        copy_button = QPushButton("Copy")
        copy_button.setFixedWidth(60)

        # Store reference to line edit
        format_key = label_text.lower().replace(" ", "_").replace("(", "").replace(")", "")
        format_line_edits[format_key] = line_edit

        # Connect copy button
        copy_button.clicked.connect(lambda checked, text=line_edit: widget.copy_to_clipboard(text.text()))

        formats_layout.addWidget(label, index, 0)
        formats_layout.addWidget(line_edit, index, 1)
        formats_layout.addWidget(copy_button, index, 2)

    formats_layout.setColumnStretch(1, 1)  # Allow the QLineEdit column to stretch
    left_panel_layout.addLayout(formats_layout)
    left_panel_layout.addStretch()

    # --- FUNCTIONALITY ---

    def update_color_formats(color_input: str):
        """Update all color format fields based on input."""
        if not color_input.strip():
            # Clear all fields if input is empty
            for line_edit in format_line_edits.values():
                line_edit.clear()
            color_preview.setStyleSheet(
                "QLabel#colorPreview { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 4px; }"
            )
            return

        # Parse the color
        rgba = converter.parse_color(color_input)
        if rgba is None:
            # Invalid color - show error state
            for line_edit in format_line_edits.values():
                line_edit.setText("Invalid color format")
                line_edit.setStyleSheet("QLineEdit { color: #dc3545; }")
            color_preview.setStyleSheet(
                "QLabel#colorPreview { background-color: #ffffff; border: 2px solid #dc3545; border-radius: 4px; }"
            )
            return

        # Valid color - update all formats
        r, g, b, a = rgba

        try:
            # Convert to all formats
            formats = converter.convert_all_formats(color_input)

            # Update format fields
            format_line_edits["hex"].setText(formats.get("hex", ""))
            format_line_edits["hex_with_alpha"].setText(formats.get("hex_alpha", ""))
            format_line_edits["rgb"].setText(formats.get("rgb", ""))
            format_line_edits["rgba"].setText(formats.get("rgba", ""))
            format_line_edits["hsl"].setText(formats.get("hsl", ""))
            format_line_edits["hsla"].setText(formats.get("hsla", ""))
            format_line_edits["hsb_hsv"].setText(formats.get("hsb", ""))
            format_line_edits["hwb"].setText(formats.get("hwb", ""))
            format_line_edits["cmyk"].setText(formats.get("cmyk", ""))

            # Reset styling for valid color
            for line_edit in format_line_edits.values():
                line_edit.setStyleSheet("")

            # Update color preview
            hex_color = formats.get("hex", "#ffffff")
            color_preview.setStyleSheet(
                f"QLabel#colorPreview {{ background-color: {hex_color}; border: 1px solid #ced4da; border-radius: 4px; }}"
            )

        except Exception:
            # Handle any conversion errors
            for line_edit in format_line_edits.values():
                line_edit.setText("Conversion error")
                line_edit.setStyleSheet("QLineEdit { color: #dc3545; }")

    def copy_to_clipboard(text: str):
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def load_sample_color():
        """Load a sample color into the input field."""
        sample_colors = [
            "#5CCC7F",
            "rgb(255, 128, 0)",
            "hsl(240, 100%, 50%)",
            "rgba(255, 0, 128, 0.8)",
            "hsb(180, 50%, 75%)",
            "hwb(300, 20%, 30%)",
            "cmyk(50%, 25%, 0%, 10%)",
        ]

        sample = random.choice(sample_colors)  # noqa: S311
        input_field.setText(sample)

    def load_from_clipboard():
        """Load color from clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            input_field.setText(text)

    def clear_input():
        """Clear the input field."""
        input_field.clear()

    def open_color_picker():
        """Open color picker dialog and update input field with selected color."""
        # Get current color from input field if valid
        current_color = QColor(255, 255, 255)  # Default to white
        current_input = input_field.text().strip()
        if current_input:
            rgba = converter.parse_color(current_input)
            if rgba is not None:
                r, g, b, a = rgba
                current_color = QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))

        # Open color dialog
        color = QColorDialog.getColor(current_color, widget, "Select Color")

        # If user selected a color (didn't cancel)
        if color.isValid():
            # Convert to hex format and update input field
            hex_color = color.name()  # Returns #RRGGBB format
            input_field.setText(hex_color)

    # Store methods on widget for external access
    widget.copy_to_clipboard = copy_to_clipboard

    # Make color preview clickable
    def on_color_preview_click(event):
        """Handle color preview click event."""
        open_color_picker()

    color_preview.mousePressEvent = on_color_preview_click

    # Connect signals
    input_field.textChanged.connect(update_color_formats)
    clipboard_btn.clicked.connect(load_from_clipboard)
    sample_btn.clicked.connect(load_sample_color)
    clear_btn.clicked.connect(clear_input)

    # Initialize with default color
    input_field.setText("#5CCC7F")

    # --- RIGHT PANEL (CODE PRESETS) ---
    right_panel = QWidget()
    right_panel.setObjectName("rightPanel")
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)

    tabs = QTabWidget()
    tabs.setObjectName("presetsTab")

    # Code Presets Tab
    code_presets_tab = QWidget()
    code_presets_layout = QVBoxLayout(code_presets_tab)
    code_presets_layout.setContentsMargins(15, 15, 15, 15)

    code_presets_edit = QTextEdit()
    code_presets_edit.setObjectName("codePresetsEdit")
    code_presets_edit.setReadOnly(True)

    def update_code_presets(rgba_values=None):
        """Update code presets with current color values."""
        if rgba_values is None:
            # Default values
            r, g, b, a = 0.361, 0.8, 0.498, 1.0
        else:
            r, g, b, a = rgba_values

        # Convert to different representations
        red_b = round(r * 255)
        green_b = round(g * 255)
        blue_b = round(b * 255)
        alpha_b = round(a * 255)
        round(a * 100)

        h, l, s = colorsys.rgb_to_hls(r, g, b)
        hue_d = round(h * 360)
        hsl_saturation_p = round(s * 100)
        lightness_p = round(l * 100)

        # HSB values (same as HSV)
        h_hsb, s_hsb, v_hsb = colorsys.rgb_to_hsv(r, g, b)
        round(h_hsb * 360)
        round(s_hsb * 100)
        round(v_hsb * 100)

        # Hex values
        hex_color = f"#{red_b:02x}{green_b:02x}{blue_b:02x}"

        code_content = f"""CSS
.color {{
    color: {hex_color};
    color: rgb({red_b}, {green_b}, {blue_b});
    color: rgba({red_b}, {green_b}, {blue_b}, {a:.2f});
    color: hsl({hue_d}, {hsl_saturation_p}%, {lightness_p}%);
    color: hsla({hue_d}, {hsl_saturation_p}%, {lightness_p}%, {a:.2f});
}}

Swift
let color = UIColor(red: {r:.3f}, green: {g:.3f}, blue: {b:.3f}, alpha: {a:.2f})
let color = UIColor(displayP3Red: {r:.3f}, green: {g:.3f}, blue: {b:.3f}, alpha: {a:.2f})

.NET
Color.FromArgb({alpha_b}, {red_b}, {green_b}, {blue_b})
Color.FromArgb({red_b}, {green_b}, {blue_b})

Java
new Color({red_b}, {green_b}, {blue_b})
new Color({red_b}, {green_b}, {blue_b}, {alpha_b})

Android
Color.rgb({red_b}, {green_b}, {blue_b})
Color.argb({alpha_b}, {red_b}, {green_b}, {blue_b})

OpenGL
glColor3f({r:.3f}f, {g:.3f}f, {b:.3f}f)
glColor4f({r:.3f}f, {g:.3f}f, {b:.3f}f, {a:.2f}f)

Objective-C
[UIColor colorWithRed:{r:.3f} green:{g:.3f} blue:{b:.3f} alpha:{a:.2f}]
[NSColor colorWithRed:{r:.3f} green:{g:.3f} blue:{b:.3f} alpha:{a:.2f}]

Python
# RGB tuple
color = ({red_b}, {green_b}, {blue_b})
# RGBA tuple
color = ({red_b}, {green_b}, {blue_b}, {alpha_b})
# Hex string
color = \"{hex_color}\"

JavaScript
// RGB
const color = `rgb({red_b}, {green_b}, {blue_b})`;
// RGBA
const color = `rgba({red_b}, {green_b}, {blue_b}, {a:.2f})`;
// Hex
const color = \"{hex_color}\";

Unity C#
new Color({r:.3f}f, {g:.3f}f, {b:.3f}f, {a:.2f}f)
new Color32({red_b}, {green_b}, {blue_b}, {alpha_b})"""

        code_presets_edit.setPlainText(code_content)

    # Initialize with default values
    update_code_presets()
    code_presets_layout.addWidget(code_presets_edit)

    tabs.addTab(code_presets_tab, "Code Presets")

    # Update the update_color_formats function to include code presets updates
    original_update_color_formats = update_color_formats

    def enhanced_update_color_formats(color_input: str):
        original_update_color_formats(color_input)

        # Update code presets if color is valid
        if color_input.strip():
            rgba = converter.parse_color(color_input)
            if rgba is not None:
                try:
                    r, g, b, a = rgba
                    update_code_presets((r, g, b, a))
                except Exception:
                    update_code_presets()
            else:
                update_code_presets()

    # Replace the function reference
    update_color_formats = enhanced_update_color_formats

    right_layout.addWidget(tabs)

    # Add panels to main layout
    main_layout.addWidget(left_panel)
    main_layout.addWidget(right_panel, 1)  # Make right panel stretch

    # Apply Stylesheet
    widget.setStyleSheet("""
        QWidget#mainWidget {
            background-color: #F8F9FA;
        }
        QWidget#leftPanel {
            background-color: #ffffff;
            border-right: 1px solid #E0E0E0;
        }
        QLabel {
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 13px;
            color: #212529;
        }
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 5px 8px;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 13px;
            color: #495057;
        }
        QLineEdit:focus {
            border-color: #80bdff;
        }
        QPushButton {
            background-color: #f8f9fa;
            border: 1px solid #ced4da;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 13px;
            color: #212529;
        }
        QPushButton:hover {
            background-color: #e9ecef;
        }
        QPushButton:pressed {
            background-color: #dae0e5;
        }
        QLabel#colorPreview {
            background-color: #5CCC7F;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        QTabWidget#presetsTab::pane {
            border: none;
        }
        QTabBar::tab {
            background: #e9ecef;
            color: #495057;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QTabBar::tab:selected {
            background: #F8F9FA;
            color: #000000;
        }
        QTabBar::tab:!selected:hover {
            background: #dde2e7;
        }
        QTextEdit#codePresetsEdit {
            background-color: #F8F9FA;
            border: none;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 14px;
            color: #343a40;
            line-height: 1.5;
        }
    """)

    return widget


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    # Create a main window to host the widget
    main_window = QMainWindow()
    main_window.setWindowTitle("Color Converter Tool")
    main_window.setGeometry(100, 100, 950, 650)

    # Create the color converter widget
    color_converter_widget = create_color_converter_widget()

    # Set the created widget as the central widget of the main window.
    main_window.setCentralWidget(color_converter_widget)

    main_window.show()
    sys.exit(app.exec())
