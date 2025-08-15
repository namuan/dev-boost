# Dev Boost Function Complexity Report

## Analysis Summary

### Method Complexity Metrics

| Function Name                 | File                     | Lines | Nesting Depth | If/Else Count | Refactoring Priority |
| ----------------------------- | ------------------------ | ----- | ------------- | ------------- | -------------------- |
| \_create_sidebar              | main.py                  | 175   | 5 (deep)      | 3             | HIGH                 |
| \_on_tool_selected            | main.py                  | 60+   | 4             | 16            | HIGH                 |
| create_tool_widget            | json_format_validate.py  | 200+  | 6             | 8             | HIGH                 |
| create_color_converter_widget | color_converter.py       | 180+  | 5             | 12            | HIGH                 |
| create_regex_tester_widget    | regex_tester.py          | 160+  | 5             | 10            | MEDIUM               |
| \_navigate_visible_items      | tools_search.py          | 45    | 4             | 4             | MEDIUM               |
| get_valid                     | base64_string_encoder.py | 55    | 3             | 6             | MEDIUM               |
| create_uuid_ulid_widget       | uuid_ulid_generator.py   | 130   | 4             | 8             | MEDIUM               |
| create_xml_formatter_widget   | xml_formatter.py         | 140   | 4             | 7             | MEDIUM               |

## Detailed Analysis by File

### devboost/main.py

#### \_create_sidebar() - Analysis

```
Lines: 175 (lines 190-365)
Complex indicators:
- Creates 4+ different UI components
- Has 8+ local variables
- Contains nested layout creation
- Handles tool registration and display
- Includes complex list iteration

Refactor targets:
- Extract search widget creation: 30 lines
- Extract tool list setup: 25 lines
- Extract tool data definition: 20 lines
- Final decompositions: 100 lines → 4×25 lines
```

#### \_create_content_area() - Analysis

```
Lines: 120+ (lines 275-395)
Complexity indicators:
- Creates 15+ different widgets in sequence
- Long parameter chains
- Complex nested layout creation
- Tool instantiation scattered throughout

Refactor targets:
- Extract toolbar creation
- Extract widget instantiation into helper loop/factory
- Extract welcome screen creation
```

#### \_on_tool_selected() - Analysis

```
Lines: 60+ (incomplete visibility, but visible chain is long)
Complexity: 16 elif statements
Complexity type: Switch/if-else chain anti-pattern
Refactor: Dictionary dispatch with string mapping
Risk: Tool registration may need restructuring
```

### devboost/tools/json_format_validate.py

#### create_tool_widget() - Analysis

```
Lines: 200+ (estimated from file size and visible portions)
Complexity indicators:
- Creates entire UI in single function
- Layout creation deeply nested (6+ levels)
- Signal connections inline
- Button creation duplicated patterns

Refactoring needed:
- Extract _create_layout_structure(): 40 lines → 4×10 lines
- Extract _create_input_widgets(): 30 lines
- Extract _create_output_widgets(): 30 lines
- Extract _create_buttons(): 30 lines
- Extract _connect_signals(): 20 lines
- Main function: 200 → 50 lines
```

### devboost/tools/color_converter.py

#### create_color_converter_widget() - Analysis

```
Lines: 180+ (estimated)
Complexity focus: Color conversion logic
- Multiple nested color format detection
- Conditional chains for format switching
- Complex math operations intermixed with UI updates

Refactoring needed:
- Extract color format detection: _get_color_format()
- Extract conversion functions: _convert_to_hex(), _convert_to_rgb(), etc.
- Update UI from conversion results
```

### devboost/tools/regex_tester.py

#### create_regex_tester_widget() - Analysis

```
Lines: 160+ (estimated)
Complexity focus: Pattern validation and highlighting
- Complex regex compilation nested in validation logic
- Match highlighting with nested conditionals
- API calls mixed with UI updates

Refactoring needed:
- Extract _compile_regex_pattern()
- Extract _highlight_matches()
- Extract _display_validation_result()
```

### devboost/tools/uuid_ulid_generator.py

#### create_uuid_ulid_widget() - Analysis

```
Lines: 130+ (estimated)
Complexity focus: Generator type switching
Multiple UUID/ULID generation modes with conditional chains
Refactor: Extract generation methods per type
```

### devboost/tools/xml_formatter.py

#### create_xml_formatter_widget() - Analysis

```
Lines: 140+ (estimated)
Complexity focus: XML formatting options
Nested options handling for XML beautification
Refactor: Extract formatting configurations to separate methods
```

### devboost/tools_search.py

#### \_navigate_visible_items() - Analysis

```
Lines: 45 (estimated)
Complexity focus: Navigation through visible items
Multiple conditional checks for navigation
Refactor: Extract boundary checking and item validation
```

## Nesting Depth Analysis

### Deeply Nested Functions (>3 levels)

1. **create_tool_widget()** in json_format_validate.py

   - Issue: Layout creation has 6 levels of nesting
   - Solution: Flatten structure, extract methods

2. **\_create_sidebar()** in main
