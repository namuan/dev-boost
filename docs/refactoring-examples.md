# Dev Boost Refactoring Examples

## Before and After Examples for Each Rule Violation

## Rule 1: Small and Concise Functions

### Before: Create Tool Widget - Too Long

```python
def create_tool_widget():
    # MAIN FUNCTION - 200+ lines
    main_widget = QWidget()
    main_widget.setWindowTitle("JSON Formatter & Validator")

    # Layout setup - 15 lines
    splitter = QSplitter(Qt.Orientation.Horizontal)
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)

    # Input section - 25 lines
    input_group = QGroupBox("Input JSON")
    input_layout = QVBoxLayout(input_group)
    self.input_text = QTextEdit()
    self.input_text.setFont(monospace_font)
    self.input_text.setMinimumHeight(200)
    input_layout.addWidget(self.input_text)

    # Complex toolbar with buttons - 30 lines
    input_toolbar = QHBoxLayout()
    self.format_button = QPushButton("Format JSON")
    self.format_button.clicked.connect(lambda: self._format_json_content())
    self.format_button.setEnabled(False)

    self.clear_input_button = QPushButton("Clear")
    self.clear_input_button.clicked.connect(lambda: self.input_text.clear())

    self.load_sample_button = QPushButton("Load Sample")
    def load_sample_json():
        sample = '{"name": "sample", "items": [1, 2, 3], "enabled": true}'
        self.input_text.setPlainText(sample)
        self._format_json_content()
    self.load_sample_button.clicked.connect(load_sample_json)

    # Output section - 25 lines (similar complexity)
    # Status bar - 15 lines
    # Signal connections - 20 lines
    # etc.
```

### After: Create Tool Widget - Decomposed

```python
def create_tool_widget():
    widget = BaseToolWidget("JSON Formatter")
    widget.setup_main_layout(
        input_panel=self._create_input_panel(),
        output_panel=self._create_output_panel(),
        status_bar=self._create_status_bar()
    )
    return widget

def _create_input_panel(self) -> QWidget:
    return self._create_json_panel(
        panel_title="Input JSON",
        text_widget_name="input_text",
        toolbar_config=[
            ToolbarButton("Format", self._handle_format_json, validation_key="input_text"),
            ToolbarButton("Clear", self._handle_clear_input),
            ToolbarButton("Load Sample", self._handle_load_sample)
        ]
    )

def _create_json_panel(self, panel_title: str, text_widget_name: str,
                      toolbar_config: List[ToolbarButton]) -> QWidget:
    panel = JsonPanel(panel_title)
    text_edit = panel.add_text_widget(text_widget_name, monospaced=True)

    for button_config in toolbar_config:
        panel.add_button(button_config)

    return panel
```

## Rule 2: Break Up Complex Chains

### Before: Complex if-elif Chain

```python
def _on_tool_selected(self, item):
    """60+ lines with 16+ elif statements - anti-pattern"""
    tool_name = item.data(Qt.ItemDataRole.UserRole)

    if tool_name == "Unix Time Converter":
        widget = create_unix_time_widget(self.scratch_pad)
        self.content_stack.addWidget(widget)
        self.content_stack.setCurrentWidget(widget)
    elif tool_name == "JSON Formatter":
        widget = create_json_tool_widget(self.scratch_pad)
        self.content_stack.addWidget(widget)
        self.content_stack.setCurrentWidget(widget)
    elif tool_name == "Base64 Encoder/Decoder":
        widget = create_base64_tool_widget(self.scratch_pad)
        self.content_stack.addWidget(widget)
        self.content_stack.setCurrentWidget(widget)
    # ... 13 more elif statements
    elif tool_name == "JWT Debugger":
        widget = create_jwt_tool_widget(self.scratch_pad)
        self.content_stack.addWidget(widget)
        self.content_stack.setCurrentWidget(widget)
    else:
        self.content_stack.setCurrentWidget(self.welcome_screen)
```

### After: Dictionary Dispatch Pattern

```python
def _on_tool_selected(self, item):
    """<25 lines - clean dispatch"""
    tool_name = item.data(Qt.ItemDataRole.UserRole)
    widget_factory = self.tool_registry.get(tool_name)

    if widget_factory:
        self._display_tool_widget(widget_factory)
    else:
        self._display_welcome_screen()

def _display_tool_widget(self, factory):
    """Separated display logic into helper method"""
    widget = factory(scratch_pad=self.scratch_pad)
    self.content_stack.addWidget(widget)
    self.content_stack.setCurrentWidget(widget)
```

## Rule 3: Simplify Complex Conditionals

### Before: Nested Color Format Detection

```python
def _parse_color_value(self, text):
    """Mixed logic with deeply nested ifs"""
    if text.startswith('#'):
        if len(text) == 4:
            return self._handle_short_hex(text)
        elif len(text) == 7:
            return self._handle_regular_hex(text)
        else:
            self._show_error("Invalid hex length")
            return None
    elif text.startswith('rgb'):
        if text.startswith('rgba('):
            values = text[5:-1].split(',')
            if len(values) == 4:
                try:
                    return self._parse_rgba(values)
                except ValueError:
                    self._show_error("Invalid RGBA values")
                    return None
        elif text.startswith('rgb('):
            values = text[4:-1].split(',')
            if len(values) == 3:
                # ... continued nested logic
        else:
            return None
```

### After: Strategy Pattern

```python
def _parse_color_value(self, text: str) -> Optional[Color]:
    """Clean strategy dispatch"""
    strategy = self._detect_format_strategy(text)
    return strategy.parse(text) if strategy else None

def _detect_format_strategy(self, text: str) -> Optional[ColorParserStrategy]:
    """Clean detection - 0 nesting"""
    for strategy in self.parsers:
        if strategy.can_parse(text):
            return strategy
    return None

# Separate strategies for each format
class HexColorStrategy(ColorParserStrategy):
    def can_parse(self, text: str) -> bool:
        return bool(re.match(r'^#[0-9a-fA-F]{3,8}$', text))

    def parse(self, text: str) -> Color:
        # Single responsibility, no nested conditionals
        return Color.from_hex(text)
```

## Rule 4: Reduce Nesting

### Before: Deeply Nested XML Processing

```python
def format_xml(self, xml_text):
    """6 levels of nesting - complex"""
    try:
        tree = ET.fromstring(xml_text)
        if self.prettify_checkbox.isChecked():
            if self.indent_tabs_checkbox.isChecked():
                indent_str = '\t' * int(self.indent_spinbox.value())
            else:
                indent_str = ' ' * int(self.indent_spinbox.value() * 4)

            if self.sort_attributes.isChecked():
                self._sort_attributes_recursive(tree)

            if self.namespace_checkbox.isChecked():
                self._handle_namespace_formatting(tree)

            formatted_xml = ET.tostring(tree, encoding='unicode', method='xml')
            lines = formatted_xml.split('\n')
            formatted_lines = []

            for i, line in enumerate(lines):
                if line.strip():
                    if i > 0:
                        formatted_lines.append(indent_str + line)
                    else:
                        formatted_lines.append(line)

            return '\n'.join(formatted_lines)
    except ET.ParseError as e:
        # ... 4 more nested layers
```

### After: Flat Structure

```python
def format_xml(self, xml_text: str) -> str:
    """3 levels max, flat logic"""
    if not xml_text.strip():
        return xml_text

    try:
        tree = self._parse_xml(xml_text)
        tree = self._apply_formatting_options(tree)
        return self._format_xml_output(tree)
    except ET.ParseError as e:
        raise XMLFormattingError(f"Invalid XML: {e}")

def _apply_formatting_options(self, tree: ET.Element) -> ET.Element:
    # Each method handles specific option, flat chain
    if self.sort_attributes.isChecked():
        tree = self._sort_attributes(tree)

    if self.namespace_checkbox.isChecked():
        tree = self._format_namespaces(tree)

    return tree

def _format_xml_output(self, tree: ET.Element) -> str:
    formatted = ET.tostring(tree, encoding='unicode', method='xml')
    return self._apply_indentation(formatted)
```

## Rule 5: Use Descriptive Names

### Before: Generic Variable Names

```python
def format_html(self):
    """Hard to understand variable purposes"""
    t = self.tb.toPlainText()
    if t:
        result = str(t)
        try:
            formatted = BeautifulSoup(result, 'html.parser').prettify()
            self.tb_2.setPlainText(formatted)
            msg = f"Formatted HTML: {len(formatted)} characters"
            self.status_label.setText(msg)
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
    else:
        self.status_label.setText("No data to format")
```

### After: Descriptive Names

```python
def format_html(self):
    """Clear variable purposes"""
    raw_html_content = self.input_html_text.toPlainText()
    if not raw_html_content.strip():
        self.status_label.setText("No HTML content to format")
        return

    try:
        cleaned_html = str(raw_html_content)
        formatted_html = BeautifulSoup(cleaned_html, 'html.parser').prettify()

        self.formatted_html_display.setPlainText(formatted_html)

        content_length = len(formatted_html)
        self.status_label.setText(f"HTML formatted successfully ({content_length} characters)")

    except ParsedHTMLException as formatting_error:
        self.status_label.setText(f"HTML formatting failed: {formatting_error}")
```

## Rule 6: Minimize Variable Lifespan

### Before: Long-Lived Variables

```python
class ColorConverter(QMainWindow):
    def __init__(self):
        # Problem: All variables global to instance
        self.hex_value = ""
        self.rgb_value = tuple()
        self.hsl_value = tuple()
        self.color_state = {}
        self.last_conversion_results = {}

    def convert_color(self, input_text):
        self.hex_value = self._to_hex(input_text)
        self.rgb_value = self._hex_to_rgb(self.hex_value)
        self.hsl_value = self._rgb_to_hsl(self.rgb_value)
        # These persist across conversions unnecessarily
```

### After: Local Context Objects

```python
class ColorConverter(QMainWindow):
    def convert_color(self, input_text: str) -> ColorConversionResult:
        # All variables scoped to operation only
        conversion_context = ColorConversionContext(input_text)

        if conversion_context.is_valid_color():
            result = conversion_context.perform_conversion()
            self._update_ui(result)
        else:
            self._show_invalid_format_error()
        # All intermediary values garbage-collected

class ColorConversionContext:
    def __init__(self, input_text: str):
        self.input_text = input_text
        self._cached_intermediates = {}  # Local to operation
```

## Composite Refactoring Example

### Before: Monolithic Tool Creation

```python
def create_complex_tool():
    """Example showing multiple rule violations combined"""
    # Rule 1: 200+ lines
    # Rule 3: Deep nesting (5+ levels)
    # Rule 5: Generic naming

    w = QWidget()
    l = QVBoxLayout(w)

    if True:  # Always true, just adds nesting
        h_layout = QHBoxLayout()
        if True:
            b1 = QPushButton("A")
            b2 = QPushButton("B")
            h_layout.addWidget(b1)
            h_layout.addWidget(b2)
            l.addLayout(h_layout)

    if True:
        grid = QGridLayout()
        for i in range(10):
            for j in range(10):
                btn = QPushButton(f"{i},{j}")
                btn.clicked.connect(
                    lambda checked, x=i, y=j: self.handle_click(x, y)
                )
                grid.addWidget(btn, i, j)
    # Much more code...
```

### After: Compliant Refactored Structure

```python
def create_complex_tool() -> QWidget:
    """Completely refactored - all rules addressed"""
    main_widget = QWidget()
    layout = self._create_main_layout()
    main_widget.setLayout(layout)
    return main_widget

def _create_main_layout(self) -> QVBoxLayout:
    layout = QVBoxLayout()
    layout.addLayout(self._create_action_buttons())
    layout.addWidget(self._create_interactive_grid())
    return layout

def _create_action_buttons(self) -> QHBoxLayout:
    button_row = QHBoxLayout()
    button_row.addWidget(self._create_button("Action A"))
    button_row.addWidget(self._create_button("Action B"))
    return button_row

def _create_interactive_grid(self) -> QWidget:
    grid_container = QWidget()
    grid_layout = QGridLayout(grid_container)

    for row in range(self.GRID_ROWS):
        for column in range(self.GRID_COLUMNS):
            grid_button = self._create_grid_button(row, column)
            grid_layout.addWidget(grid_button, row, column)

    return grid_container

def _create_grid_button(self, row: int, column: int) -> PositionalButton:
    button = PositionalButton(row, column)
    button.position_clicked.connect(self.handle_grid_position_click)
    return button
```

## Refactoring Implementation Stages

### Stage 1: Identify and Document Existing Issues

- [ ] Add @ todo comments to each method exceeding 50 lines
- [ ] Add @ todo comments for nesting depth > 3
- [ ] Add @ todo comments for naming violations

### Stage 2: Extraction Functions

- [ ] Create helper methods following naming patterns
- [ ] Extract validation logic to separate classes
- [ ] Extract UI creation to factory classes

### Stage 3: Pattern Application

- [ ] Apply consistent patterns across all tools
- [ ] Update variable names for clarity
- [ ] Minimize variable scope throughout codebase

### Stage 4: Testing and Verification

- [ ] Ensure existing functionality preserved
- [ ] Verify reduced complexity metrics
- [ ] Update documentation with new patterns
