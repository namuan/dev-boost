# Dev Boost Refactoring Checklist

## File-Level Refactoring Tasks

### Completed Analysis ✓

- [x] Identified all functions exceeding 50 lines
- [x] Mapped nesting depth issues
- [x] Located inconsistent patterns

## devboost/main.py Refactoring

### \_create_sidebar() [Lines ~190-365]

- [ ] Extract method: `_create_search_widget()` (30 lines)
- [ ] Extract method: `_create_tools_list_widget()` (25 lines)
- [ ] Extract method: `_create_search_results_label()` (15 lines)
- [ ] Extract method: `_populate_tools_list()` (25 lines)
- [ ] Extract method: `_style_sidebar_components()` (20 lines)
- [ ] Update main function to compose from extracted methods

### \_create_content_area() [Lines ~275-395]

- [ ] Extract method: `_setup_stacked_widget()` (30 lines)
- [ ] Extract method: `_create_tool_widgets()` (using factory pattern)
- [ ] Extract method: `_create_welcome_screen_widget()` (25 lines)
- [ ] Extract method: `_setup_main_widget_layout()` (20 lines)

### \_on_tool_selected() [Lines ~395-455]

- [ ] Create `tool_registry.py` module with registry dictionary
- [ ] Extract all tool widget creation functions to registry
- [ ] Replace if-elif chain with dictionary dispatch
- [ ] Add error handling for missing tools
- [ ] Update initialization to load registry

### Navigation Methods

- [ ] Extract method: `_focus_search_input()` (refactor existing)
- [ ] Extract method: `_focus_tool_list()` (refactor existing)
- [ ] Unify keyboard handling into `_handle_global_key_events()`

## Tool Files Refactoring

### json_format_validate.py

#### create_tool_widget() [>200 lines]

- [ ] Extract `_create_splitter_layout()` (25 lines)
- [ ] Extract `_create_input_panel()` (30 lines)
- [ ] Extract `_create_output_panel()` (30 lines)
- [ ] Extract `_create_input_toolbar()` (20 lines)
- [ ] Extract `_create_output_toolbar()` (20 lines)
- [ ] Extract `_create_status_bar()` (15 lines)
- [ ] Extract `_setup_button_connections()` (15 lines)
- [ ] Main function should compose sub-methods (final: ~40 lines total)

#### Inline Functions to Extract

- [ ] Extract \_format_and_validate_json() from format_json() lambda
- [ ] Extract \_load_sample_json() from load_sample() lambda
- [ ] Extract \_clear_ui_state() from clear_input() lambda
- [ ] Extract \_copy_to_clipboard() from copy_output() lambda
- [ ] Extract \_copy_formatted() function with proper validation

### uuid_ulid_generator.py

#### create_uuid_ulid_widget() [~130 lines]

- [ ] Extract `_create_generation_panel()` (25 lines)
- [ ] Extract `_create_display_panel()` (20 lines)
- [ ] Extract `_setup_radio_button_group()` (15 lines)
- [ ] Extract `_create_button_row()` (12 lines)
- [ ] Extract `_connect_generation_signals()` (18 lines)

### color_converter.py

#### create_color_converter_widget() [~180 lines]

- [ ] Create ColorConverter class with conversion methods
- [ ] Extract ColorFormat validation utility
- [ ] Extract color value parsing functions
- [ ] Extract color space conversion methods
- [ ] Refactor color preview updates
- [ ] Extract validation result handlers

### regex_tester.py

#### create_regex_tester_widget() [~160 lines]

- [ ] Extract RegexValidator class with validation methods
- [ ] Extract highlighting utilities
- [ ] Extract match result formatting
- [ ] Extract pattern compilation with caching

### xml_formatter.py

#### create_xml_formatter_widget() [~140 lines]

- [ ] Extract XMLFormatter utility class
- [ ] Extract formatting configuration (indent, attributes)
- [ ] Extract validation methods (well-formedness, schema)
- [ ] Refactor format application methods

### base64_string_encoder.py

#### Validators

- [ ] Extract Base64Validator class (file: base64_validator.py)
- [ ] Extract encoding/decoding methods as free functions
- [ ] Refactor input validation logic
- [ ] Refactor file handling methods

## Pattern Standardization Checklist

### Core Patterns

- [ ] Create `devboost/base` module with base classes
- [ ] Define `ToolWidgetBase` abstract base class
- [ ] Define `ValidatorBase` abstract base class
- [ ] Create `WidgetFactory` utility classes
- [ ] Create `TouchableValidator` decorator/factory for UI widgets

### Variable Naming Improvements

- [ ] Rename generic variables like "input", "output" to descriptive names
- [ ] Standardize format names (e.g., "hex_value", "rgb_tuple")
- [ ] Rename button variables with action verbs
- [ ] Extract magic numbers to constants

### Layout Pattern Compliance

- [ ] Standardize widget spacing (margins, gaps)
- [ ] Create LayoutFactory for QVBoxLayout, QHBoxLayout creation
- [ ] Extract common styling patterns to helper methods
- [ ] Create consistent widget creation factories

### Signal/Slot Pattern

- [ ] Extract all lambda functions to named methods
- [ ] Create consistent signal naming conventions
- [ ] Standardize error handling across signal connections
- [ ] Extract validation/update logic from button callbacks

## File-by-File Progress Tracker

### Phase 1: Core Application

- [ ] main.py: \_create_sidebar() refactoring
- [ ] main.py: \_create_content_area() refactoring
- [ ] main.py: tool registration system
- [ ] main.py: signal handling extraction

### Phase 2: Tool Standardization

- [ ] json_format_validate.py: full refactoring
- [ ] uuid_ulid_generator.py: widget extraction
- [ ] base64_string_encoder.py: validator extraction
- [ ] color_converter.py: conversion methods
- [ ] regex_tester.py: validator extraction
- [ ] xml_formatter.py: formatting extraction

### Phase 3: General Tools

- [ ] unix_time_converter.py: refactoring
- [ ] url_encoder_decoder.py: refactoring
- [ ] jwt_debugger.py: refactoring
- [ ] lorem_ipsum_generator.py: refactoring
- [ ] markdown_viewer.py: refactoring
- [ ] yaml_json_converter.py: refactoring

### Phase 4: Remaining Tools

- [ ] random_string_generator.py: refactoring
- [ ] xml_formatter.py: complete refactoring
- [ ] Any new tools following standards

## Testing Supplement

### Before Each Refactor

- [ ] Document current test coverage for target function
- [ ] Create integration test to verify UI behavior unchanged
- [ ] Create unit test for extracted methods

### After Each Refactor

- [ ] Ensure all tests pass
- [ ] Verify no behavioral changes introduced
- [ ] Update documentation with new method signatures

## Validation Steps

### Method Size Validation

- [ ] Ensure no extracted method exceeds 35 lines
- [ ] Ensure main method calls are <25 lines
- [ ] Verify nesting depth ≤3 in all methods

### Pattern Consistency Validation

- [ ] Verifysignal connection patterns consistent
- [ ] Ensure validator classes used uniformly
- [ ] Check naming conventions applied consistently
- [ ] Verify factory usage across similar widgets

### Integration Validation

- [ ] Run full test suite after each file
- [ ] Test toolbar creation flows work identically
- [ ] Verify Scratch Pad integration unchanged
- [ ] Test keyboard shortcuts preserved
- [ ] Validate tool selection flows work correctly
