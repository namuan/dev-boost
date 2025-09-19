import logging

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style

logger = logging.getLogger(__name__)


class UnitConverter:
    """Backend class for unit conversion operations."""

    def __init__(self):
        """Initialize the UnitConverter."""
        logger.info("Initializing UnitConverter")

        # Define unit categories and their conversions to base units
        self.unit_categories = {
            "Length": {
                "base_unit": "m",
                "units": {
                    "m": 1.0,
                    "km": 1000.0,
                    "cm": 0.01,
                    "mm": 0.001,
                    "in": 0.0254,
                    "ft": 0.3048,
                    "yd": 0.9144,
                    "mi": 1609.344,
                },
            },
            "Mass": {
                "base_unit": "kg",
                "units": {
                    "kg": 1.0,
                    "g": 0.001,
                    "mg": 0.000001,
                    "lb": 0.453592,
                    "oz": 0.0283495,
                },
            },
            "Temperature": {
                "base_unit": "K",
                "units": {
                    "K": {"offset": 0, "scale": 1},
                    "°C": {"offset": 273.15, "scale": 1},
                    "°F": {"offset": 459.67, "scale": 5 / 9},
                },
            },
            "Time": {
                "base_unit": "s",
                "units": {
                    "s": 1.0,
                    "ms": 0.001,
                    "min": 60.0,
                    "h": 3600.0,
                    "day": 86400.0,
                },
            },
            "Data Rate": {
                "base_unit": "bps",
                "units": {
                    # Bits per second
                    "bps": 1.0,
                    "Kbps": 1000.0,
                    "Mbps": 1000000.0,
                    "Gbps": 1000000000.0,
                    # Bytes per second
                    "B/s": 8.0,
                    "KB/s": 8000.0,
                    "MB/s": 8000000.0,
                    "GB/s": 8000000000.0,
                },
            },
        }

    def convert_units(
        self, value: float, from_unit: str, to_unit: str, category: str, use_iec: bool = False
    ) -> float | None:
        """Convert between units in the same category."""
        try:
            logger.debug("Converting %s from %s to %s in category %s", value, from_unit, to_unit, category)

            if category not in self.unit_categories:
                logger.error("Unknown category: %s", category)
                return None

            category_data = self.unit_categories[category]

            # Handle temperature conversions specially
            if category == "Temperature":
                return self._convert_temperature(value, from_unit, to_unit)

            # Handle data rate with IEC option
            if category == "Data Rate":
                return self._convert_data_rate(value, from_unit, to_unit, use_iec)

            # Standard linear conversions
            if from_unit not in category_data["units"] or to_unit not in category_data["units"]:
                logger.error("Unknown units: %s or %s", from_unit, to_unit)
                return None

            # Convert to base unit, then to target unit
            base_value = value * category_data["units"][from_unit]
            result = base_value / category_data["units"][to_unit]

            logger.debug("Conversion result: %s", result)
            return result

        except Exception:
            logger.exception("Error converting units")
            return None

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float | None:
        """Convert temperature units with proper offset handling."""
        try:
            temp_units = self.unit_categories["Temperature"]["units"]

            if from_unit not in temp_units or to_unit not in temp_units:
                return None

            # Convert to Kelvin first
            if from_unit == "K":
                kelvin_value = value
            elif from_unit == "°C":
                kelvin_value = value + 273.15
            elif from_unit == "°F":
                kelvin_value = (value + 459.67) * 5 / 9
            else:
                return None

            # Validate Kelvin >= 0
            if kelvin_value < 0:
                logger.warning("Temperature below absolute zero: %sK", kelvin_value)
                return None

            # Convert from Kelvin to target
            if to_unit == "K":
                result = kelvin_value
            elif to_unit == "°C":
                result = kelvin_value - 273.15
            elif to_unit == "°F":
                result = kelvin_value * 9 / 5 - 459.67
            else:
                return None

            return result

        except Exception:
            logger.exception("Error converting temperature")
            return None

    def _convert_data_rate(self, value: float, from_unit: str, to_unit: str, use_iec: bool) -> float | None:
        """Convert data rate units with SI/IEC option."""
        try:
            # Define multipliers
            si_multipliers = {"K": 1000, "M": 1000000, "G": 1000000000}
            iec_multipliers = {"K": 1024, "M": 1048576, "G": 1073741824}

            multipliers = iec_multipliers if use_iec else si_multipliers

            # Parse units
            def parse_data_unit(unit):
                if unit == "bps":
                    return 1.0, "bits"
                if unit == "B/s":
                    return 8.0, "bits"
                if unit.endswith("bps"):
                    prefix = unit[:-3]
                    return multipliers.get(prefix, 1.0), "bits"
                if unit.endswith("B/s"):
                    prefix = unit[:-3]
                    return multipliers.get(prefix, 1.0) * 8.0, "bits"
                return 1.0, "bits"

            from_multiplier, _ = parse_data_unit(from_unit)
            to_multiplier, _ = parse_data_unit(to_unit)

            # Convert to bits per second, then to target
            bits_per_second = value * from_multiplier
            return bits_per_second / to_multiplier

        except Exception:
            logger.exception("Error converting data rate")
            return None


class ProgrammerConverter:
    """Backend class for programmer mode conversions."""

    def __init__(self):
        """Initialize the ProgrammerConverter."""
        logger.info("Initializing ProgrammerConverter")

    def parse_input(self, input_str: str, bit_width: int = 32) -> int | None:
        """Parse input string and return integer value."""
        try:
            input_str = input_str.strip()
            if not input_str:
                return None

            # Detect base and convert
            if input_str.startswith("0b"):
                value = int(input_str, 2)
            elif input_str.startswith("0o"):
                value = int(input_str, 8)
            elif input_str.startswith("0x"):
                value = int(input_str, 16)
            else:
                value = int(input_str, 10)

            # Clamp to bit width
            max_value = (1 << bit_width) - 1
            value = value & max_value

            logger.debug("Parsed %s as %s (bit width: %s)", input_str, value, bit_width)
            return value

        except ValueError:
            logger.exception("Error parsing input %s", input_str)
            return None

    def format_value(
        self, value: int, base: str, bit_width: int = 32, nibble_group: bool = False, byte_group: bool = False
    ) -> str:
        """Format value in specified base with optional grouping."""
        try:
            if value is None:
                return ""

            # Clamp to bit width
            max_value = (1 << bit_width) - 1
            value = value & max_value

            if base == "bin":
                result = format(value, f"0{bit_width}b")
                if nibble_group:
                    result = " ".join(result[i : i + 4] for i in range(0, len(result), 4))
                elif byte_group:
                    result = " ".join(result[i : i + 8] for i in range(0, len(result), 8))
                return f"0b{result}"
            if base == "oct":
                return f"0o{value:o}"
            if base == "dec":
                return str(value)
            if base == "hex":
                result = f"{value:0{bit_width // 4}x}"
                if nibble_group:
                    result = " ".join(result[i : i + 1] for i in range(0, len(result), 1))
                elif byte_group:
                    result = " ".join(result[i : i + 2] for i in range(0, len(result), 2))
                return f"0x{result}"

            return str(value)

        except Exception:
            logger.exception("Error formatting value in base")
            return ""

    def bitwise_operation(self, a: int, b: int, operation: str, bit_width: int = 32) -> int | None:
        """Perform bitwise operation."""
        try:
            max_value = (1 << bit_width) - 1
            a = a & max_value
            b = b & max_value

            if operation == "AND":
                result = a & b
            elif operation == "OR":
                result = a | b
            elif operation == "XOR":
                result = a ^ b
            elif operation == "NOT":
                result = (~a) & max_value
            elif operation == "<<":
                result = (a << b) & max_value
            elif operation == ">>":
                result = a >> b
            else:
                logger.error("Unknown operation: %s", operation)
                return None

            logger.debug("Bitwise operation: %s %s %s = %s", a, operation, b, result)
            return result

        except Exception:
            logger.exception("Error performing bitwise operation")
            return None


def create_unit_converter_widget(style_func, scratch_pad=None):
    """Create the unit converter widget."""
    logger.info("Creating unit converter widget")

    # Create main widget
    main_widget = QWidget()
    main_layout = QVBoxLayout(main_widget)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(10)

    # Set widget properties
    main_widget.setObjectName("mainWidget")
    main_widget.setStyleSheet(get_tool_style())

    # Initialize converters
    unit_converter = UnitConverter()
    programmer_converter = ProgrammerConverter()

    # Tab widget for modes
    tabs = QTabWidget()
    main_layout.addWidget(tabs)

    # Create tabs
    units_tab = _create_units_tab(unit_converter)
    programmer_tab = _create_programmer_tab(programmer_converter)

    tabs.addTab(units_tab, "Units")
    tabs.addTab(programmer_tab, "Programmer")

    return main_widget


def _create_units_tab(unit_converter):
    """Create the units conversion tab."""
    units_tab = QWidget()
    units_layout = QVBoxLayout(units_tab)
    units_layout.setContentsMargins(10, 10, 10, 10)
    units_layout.setSpacing(10)

    # Create UI components
    category_combo, from_unit_combo = _create_category_selection(units_layout, unit_converter)
    input_field, precision_spin = _create_input_section(units_layout)
    iec_checkbox, bits_bytes_checkbox = _create_data_rate_controls(units_layout)
    results_scroll, results_layout = _create_results_area(units_layout)

    # Set up event handlers and initialize
    units_event_handlers = _setup_units_event_handlers(
        category_combo,
        from_unit_combo,
        input_field,
        precision_spin,
        iec_checkbox,
        bits_bytes_checkbox,
        results_layout,
        unit_converter,
    )

    # Initialize the units display
    units_event_handlers["update_from_units"]()

    return units_tab


def _create_programmer_tab(programmer_converter):
    """Create the programmer mode tab."""
    programmer_tab = QWidget()
    programmer_layout = QVBoxLayout(programmer_tab)
    programmer_layout.setContentsMargins(10, 10, 10, 10)
    programmer_layout.setSpacing(10)

    # Create UI components
    prog_input_field, base_combo, width_combo = _create_programmer_input_section(programmer_layout)
    nibble_checkbox, byte_checkbox = _create_grouping_options(programmer_layout)
    base_fields = _create_base_representations(programmer_layout)
    operation_widgets = _create_bitwise_operations(programmer_layout)

    # Set up event handlers
    _setup_programmer_event_handlers(
        prog_input_field,
        base_combo,
        width_combo,
        nibble_checkbox,
        byte_checkbox,
        base_fields,
        operation_widgets,
        programmer_converter,
    )

    return programmer_tab


def get_error_input_style():
    """Get error styling for input fields."""
    return "border: 2px solid #d32f2f; background-color: #ffebee;"


def _create_category_selection(layout, unit_converter):
    """Create category selection UI components."""
    category_layout = QHBoxLayout()
    category_label = QLabel("Category:")
    category_combo = QComboBox()
    category_combo.addItems(list(unit_converter.unit_categories.keys()))
    from_unit_combo = QComboBox()

    category_layout.addWidget(category_label)
    category_layout.addWidget(category_combo)
    category_layout.addStretch()
    layout.addLayout(category_layout)

    return category_combo, from_unit_combo


def _create_input_section(layout):
    """Create input section UI components."""
    input_layout = QHBoxLayout()
    input_label = QLabel("Value:")
    input_field = QLineEdit()
    input_field.setPlaceholderText("Enter value to convert")
    from_unit_combo = QComboBox()

    input_layout.addWidget(input_label)
    input_layout.addWidget(input_field)
    input_layout.addWidget(QLabel("From:"))
    input_layout.addWidget(from_unit_combo)
    layout.addLayout(input_layout)

    # Precision control
    precision_layout = QHBoxLayout()
    precision_label = QLabel("Decimal places:")
    precision_spin = QSpinBox()
    precision_spin.setRange(0, 8)
    precision_spin.setValue(3)
    precision_layout.addWidget(precision_label)
    precision_layout.addWidget(precision_spin)
    precision_layout.addStretch()
    layout.addLayout(precision_layout)

    return input_field, precision_spin


def _create_data_rate_controls(layout):
    """Create data rate specific controls."""
    data_rate_layout = QHBoxLayout()
    iec_checkbox = QCheckBox("Use IEC (1Ki = 1024)")
    bits_bytes_checkbox = QCheckBox("Show bits/bytes toggle")
    data_rate_layout.addWidget(iec_checkbox)
    data_rate_layout.addWidget(bits_bytes_checkbox)
    data_rate_layout.addStretch()
    layout.addLayout(data_rate_layout)

    # Initially hide data rate controls
    iec_checkbox.hide()
    bits_bytes_checkbox.hide()

    return iec_checkbox, bits_bytes_checkbox


def _create_results_area(layout):
    """Create results display area."""
    results_scroll = QScrollArea()
    results_widget = QWidget()
    results_layout = QVBoxLayout(results_widget)
    results_scroll.setWidget(results_widget)
    results_scroll.setWidgetResizable(True)
    results_scroll.setMinimumHeight(300)
    layout.addWidget(results_scroll)

    return results_scroll, results_layout


def _create_programmer_input_section(layout):
    """Create programmer mode input section."""
    prog_input_layout = QHBoxLayout()
    prog_input_label = QLabel("Input:")
    prog_input_field = QLineEdit()
    prog_input_field.setPlaceholderText("Enter value (0x, 0b, 0o prefixes supported)")
    base_combo = QComboBox()
    base_combo.addItems(["Auto-detect", "Binary", "Octal", "Decimal", "Hexadecimal"])

    prog_input_layout.addWidget(prog_input_label)
    prog_input_layout.addWidget(prog_input_field)
    prog_input_layout.addWidget(QLabel("Base:"))
    prog_input_layout.addWidget(base_combo)
    layout.addLayout(prog_input_layout)

    # Bit width selection
    width_layout = QHBoxLayout()
    width_label = QLabel("Bit width:")
    width_combo = QComboBox()
    width_combo.addItems(["8", "16", "32", "64"])
    width_combo.setCurrentText("32")
    width_layout.addWidget(width_label)
    width_layout.addWidget(width_combo)
    width_layout.addStretch()
    layout.addLayout(width_layout)

    return prog_input_field, base_combo, width_combo


def _create_grouping_options(layout):
    """Create grouping options for programmer mode."""
    grouping_layout = QHBoxLayout()
    nibble_checkbox = QCheckBox("Nibble grouping (4-bit)")
    byte_checkbox = QCheckBox("Byte grouping (8-bit)")
    grouping_layout.addWidget(nibble_checkbox)
    grouping_layout.addWidget(byte_checkbox)
    grouping_layout.addStretch()
    layout.addLayout(grouping_layout)

    return nibble_checkbox, byte_checkbox


def _create_base_representations(layout):
    """Create base representation fields."""
    bases_widget = QWidget()
    bases_layout = QGridLayout(bases_widget)

    # Create fields for each base
    bin_label = QLabel("Binary:")
    bin_field = QLineEdit()
    bin_field.setReadOnly(True)
    bin_copy_btn = QPushButton("Copy")

    oct_label = QLabel("Octal:")
    oct_field = QLineEdit()
    oct_field.setReadOnly(True)
    oct_copy_btn = QPushButton("Copy")

    dec_label = QLabel("Decimal:")
    dec_field = QLineEdit()
    dec_field.setReadOnly(True)
    dec_copy_btn = QPushButton("Copy")

    hex_label = QLabel("Hexadecimal:")
    hex_field = QLineEdit()
    hex_field.setReadOnly(True)
    hex_copy_btn = QPushButton("Copy")

    bases_layout.addWidget(bin_label, 0, 0)
    bases_layout.addWidget(bin_field, 0, 1)
    bases_layout.addWidget(bin_copy_btn, 0, 2)
    bases_layout.addWidget(oct_label, 1, 0)
    bases_layout.addWidget(oct_field, 1, 1)
    bases_layout.addWidget(oct_copy_btn, 1, 2)
    bases_layout.addWidget(dec_label, 2, 0)
    bases_layout.addWidget(dec_field, 2, 1)
    bases_layout.addWidget(dec_copy_btn, 2, 2)
    bases_layout.addWidget(hex_label, 3, 0)
    bases_layout.addWidget(hex_field, 3, 1)
    bases_layout.addWidget(hex_copy_btn, 3, 2)

    layout.addWidget(bases_widget)

    return {
        "bin": (bin_field, bin_copy_btn),
        "oct": (oct_field, oct_copy_btn),
        "dec": (dec_field, dec_copy_btn),
        "hex": (hex_field, hex_copy_btn),
    }


def _create_bitwise_operations(layout):
    """Create bitwise operations section."""
    ops_widget = QWidget()
    ops_layout = QVBoxLayout(ops_widget)

    ops_title = QLabel("Bitwise Operations:")
    ops_layout.addWidget(ops_title)

    # Two operand operations
    two_op_layout = QHBoxLayout()
    operand_a_field = QLineEdit()
    operand_a_field.setPlaceholderText("Operand A")
    operation_combo = QComboBox()
    operation_combo.addItems(["AND", "OR", "XOR", "<<", ">>"])
    operand_b_field = QLineEdit()
    operand_b_field.setPlaceholderText("Operand B")
    calc_btn = QPushButton("Calculate")

    two_op_layout.addWidget(operand_a_field)
    two_op_layout.addWidget(operation_combo)
    two_op_layout.addWidget(operand_b_field)
    two_op_layout.addWidget(calc_btn)
    ops_layout.addLayout(two_op_layout)

    # NOT operation
    not_layout = QHBoxLayout()
    not_operand_field = QLineEdit()
    not_operand_field.setPlaceholderText("Operand for NOT")
    not_btn = QPushButton("NOT")
    not_layout.addWidget(not_operand_field)
    not_layout.addWidget(not_btn)
    not_layout.addStretch()
    ops_layout.addLayout(not_layout)

    # Result
    result_layout = QHBoxLayout()
    result_label = QLabel("Result:")
    result_field = QLineEdit()
    result_field.setReadOnly(True)
    result_copy_btn = QPushButton("Copy")
    result_layout.addWidget(result_label)
    result_layout.addWidget(result_field)
    result_layout.addWidget(result_copy_btn)
    ops_layout.addLayout(result_layout)

    layout.addWidget(ops_widget)

    return {
        "operand_a": operand_a_field,
        "operation": operation_combo,
        "operand_b": operand_b_field,
        "calc_btn": calc_btn,
        "not_operand": not_operand_field,
        "not_btn": not_btn,
        "result": result_field,
        "result_copy": result_copy_btn,
    }


def _setup_units_event_handlers(
    category_combo,
    from_unit_combo,
    input_field,
    precision_spin,
    iec_checkbox,
    bits_bytes_checkbox,
    results_layout,
    unit_converter,
):
    """Set up event handlers for units tab."""

    def update_from_units():
        """Update the from unit combo based on selected category."""
        category = category_combo.currentText()
        from_unit_combo.clear()
        if category in unit_converter.unit_categories:
            units = list(unit_converter.unit_categories[category]["units"].keys())
            from_unit_combo.addItems(units)

        # Show/hide data rate specific controls
        if category == "Data Rate":
            iec_checkbox.show()
            bits_bytes_checkbox.show()
        else:
            iec_checkbox.hide()
            bits_bytes_checkbox.hide()

        logger.info("Updated units for category: %s", category)
        update_unit_results()

    def update_unit_results():
        """Update the conversion results."""
        try:
            # Clear previous results
            for i in reversed(range(results_layout.count())):
                child = results_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            input_text = input_field.text().strip()
            if not input_text:
                logger.debug("Input field is empty, clearing results")
                input_field.setStyleSheet("")  # Clear error state
                return

            try:
                input_value = float(input_text)
                input_field.setStyleSheet("")  # Clear error state
                logger.debug("Parsed input value: %s", input_value)
            except ValueError:
                logger.warning("Invalid input value: %s", input_text)
                input_field.setStyleSheet(get_error_input_style())

                # Show error message in results area
                error_widget = QWidget()
                error_layout = QHBoxLayout(error_widget)
                error_layout.setContentsMargins(5, 2, 5, 2)

                error_label = QLabel("⚠️ Invalid number format")
                error_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                error_layout.addWidget(error_label)
                error_layout.addStretch()

                results_layout.addWidget(error_widget)
                return

            category = category_combo.currentText()
            from_unit = from_unit_combo.currentText()
            precision = precision_spin.value()
            use_iec = iec_checkbox.isChecked()

            logger.debug("Converting %s %s in category %s", input_value, from_unit, category)

            if category not in unit_converter.unit_categories:
                logger.error("Unknown category: %s", category)
                return

            target_units = list(unit_converter.unit_categories[category]["units"].keys())
            conversion_count = 0

            for to_unit in target_units:
                if to_unit == from_unit:
                    continue

                result = unit_converter.convert_units(input_value, from_unit, to_unit, category, use_iec)

                if result is not None:
                    conversion_count += 1
                    # Create result row
                    row_widget = QWidget()
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(5, 2, 5, 2)

                    unit_label = QLabel(f"{to_unit}:")
                    unit_label.setMinimumWidth(60)

                    value_label = QLabel(f"{result:.{precision}f}")
                    value_label.setMinimumWidth(150)

                    copy_btn = QPushButton("Copy")
                    copy_btn.setMaximumWidth(60)

                    # Connect copy button
                    def make_copy_handler(value):
                        return lambda: QApplication.clipboard().setText(str(value))

                    copy_btn.clicked.connect(make_copy_handler(f"{result:.{precision}f}"))

                    row_layout.addWidget(unit_label)
                    row_layout.addWidget(value_label)
                    row_layout.addWidget(copy_btn)
                    row_layout.addStretch()

                    results_layout.addWidget(row_widget)
                else:
                    logger.warning("Failed to convert %s %s to %s", input_value, from_unit, to_unit)

            logger.info(
                "Updated conversion results for %s %s - %s conversions", input_value, from_unit, conversion_count
            )

        except Exception:
            logger.exception("Error updating unit results")
            input_field.setStyleSheet(get_error_input_style())

    # Connect event handlers
    category_combo.currentTextChanged.connect(update_from_units)
    from_unit_combo.currentTextChanged.connect(update_unit_results)
    input_field.textChanged.connect(update_unit_results)
    precision_spin.valueChanged.connect(update_unit_results)
    iec_checkbox.toggled.connect(update_unit_results)
    bits_bytes_checkbox.toggled.connect(update_unit_results)

    # Return event handlers for external access
    return {"update_from_units": update_from_units, "update_unit_results": update_unit_results}


def _setup_programmer_event_handlers(
    prog_input_field,
    base_combo,
    width_combo,
    nibble_checkbox,
    byte_checkbox,
    base_fields,
    operation_widgets,
    programmer_converter,
):
    """Set up event handlers for programmer tab."""

    def update_programmer_display():
        """Update the programmer mode display."""
        try:
            input_text = prog_input_field.text().strip()
            bit_width = int(width_combo.currentText())

            if not input_text:
                logger.debug("Programmer input field is empty, clearing displays")
                prog_input_field.setStyleSheet("")
                for field, _ in base_fields.values():
                    field.clear()
                return

            # Parse input
            value = programmer_converter.parse_input(input_text)
            if value is None:
                logger.warning("Could not parse programmer input: %s", input_text)
                prog_input_field.setStyleSheet(get_error_input_style())
                for field, _ in base_fields.values():
                    field.setText("Invalid input")
                return

            prog_input_field.setStyleSheet("")  # Clear error state
            logger.debug("Parsed programmer input: %s", value)

            # Update base representations
            nibble_group = nibble_checkbox.isChecked()
            byte_group = byte_checkbox.isChecked()

            base_fields["bin"][0].setText(
                programmer_converter.format_value(value, 2, bit_width, nibble_group, byte_group)
            )
            base_fields["oct"][0].setText(
                programmer_converter.format_value(value, 8, bit_width, nibble_group, byte_group)
            )
            base_fields["dec"][0].setText(
                programmer_converter.format_value(value, 10, bit_width, nibble_group, byte_group)
            )
            base_fields["hex"][0].setText(
                programmer_converter.format_value(value, 16, bit_width, nibble_group, byte_group)
            )

        except Exception:
            logger.exception("Error updating programmer display")
            prog_input_field.setStyleSheet(get_error_input_style())

    def perform_bitwise_operation():
        """Perform bitwise operation."""
        try:
            operand_a_text = operation_widgets["operand_a"].text().strip()
            operand_b_text = operation_widgets["operand_b"].text().strip()
            operation = operation_widgets["operation"].currentText()

            if not operand_a_text or not operand_b_text:
                logger.debug("Missing operands for bitwise operation")
                return

            operand_a = programmer_converter.parse_input(operand_a_text)
            operand_b = programmer_converter.parse_input(operand_b_text)

            if operand_a is None or operand_b is None:
                logger.warning("Could not parse operands for bitwise operation")
                operation_widgets["result"].setText("Invalid operands")
                return

            result = programmer_converter.bitwise_operation(operand_a, operand_b, operation)
            if result is not None:
                bit_width = int(width_combo.currentText())
                nibble_group = nibble_checkbox.isChecked()
                byte_group = byte_checkbox.isChecked()
                formatted_result = programmer_converter.format_value(result, 10, bit_width, nibble_group, byte_group)
                operation_widgets["result"].setText(formatted_result)
                logger.info("Bitwise operation result: %s", formatted_result)
            else:
                operation_widgets["result"].setText("Error: Operation failed")

        except Exception:
            logger.exception("Error performing bitwise operation")
            operation_widgets["result"].setText("Error: Operation failed")

    def perform_not_operation():
        """Perform NOT operation."""
        try:
            operand_text = operation_widgets["not_operand"].text().strip()
            if not operand_text:
                logger.debug("Missing operand for NOT operation")
                return

            operand = programmer_converter.parse_input(operand_text)
            if operand is None:
                logger.warning("Could not parse operand for NOT operation")
                operation_widgets["result"].setText("Invalid operand")
                return

            bit_width = int(width_combo.currentText())
            mask = (1 << bit_width) - 1
            result = (~operand) & mask

            nibble_group = nibble_checkbox.isChecked()
            byte_group = byte_checkbox.isChecked()
            formatted_result = programmer_converter.format_value(result, 10, bit_width, nibble_group, byte_group)
            operation_widgets["result"].setText(formatted_result)
            logger.info("NOT operation result: %s", formatted_result)

        except Exception:
            logger.exception("Error performing NOT operation")
            operation_widgets["result"].setText("Error: Operation failed")

    # Connect event handlers
    prog_input_field.textChanged.connect(update_programmer_display)
    base_combo.currentTextChanged.connect(update_programmer_display)
    width_combo.currentTextChanged.connect(update_programmer_display)
    nibble_checkbox.toggled.connect(update_programmer_display)
    byte_checkbox.toggled.connect(update_programmer_display)

    operation_widgets["calc_btn"].clicked.connect(perform_bitwise_operation)
    operation_widgets["not_btn"].clicked.connect(perform_not_operation)

    # Connect copy buttons
    for _base_name, (field, copy_btn) in base_fields.items():
        copy_btn.clicked.connect(lambda checked, f=field: QApplication.clipboard().setText(f.text()))

    operation_widgets["result_copy"].clicked.connect(
        lambda: QApplication.clipboard().setText(operation_widgets["result"].text())
    )


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    # Create a main window to host the widget
    from PyQt6.QtWidgets import QMainWindow

    main_window = QMainWindow()
    main_window.setWindowTitle("Unit Converter Tool")
    main_window.setGeometry(100, 100, 800, 600)

    # Create the unit converter widget
    unit_converter_widget = create_unit_converter_widget(app.style)

    # Set the created widget as the central widget of the main window.
    main_window.setCentralWidget(unit_converter_widget)

    main_window.show()
    sys.exit(app.exec())
