# DevBoost Project Structure and Tool Integration Patterns

## Project Overview

DevBoost is a PyQt6-based desktop application that provides various developer productivity tools. The application follows a modular architecture where each tool is implemented as a separate module with consistent integration patterns.

## Project Structure

```
dev-boost/
├── devboost/                    # Main application package
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # Main application window and logic
│   ├── config.py               # Configuration management
│   ├── styles.py               # Application styling
│   ├── tools_search.py         # Tool search functionality
│   └── tools/                  # Individual tool implementations
│       ├── __init__.py         # Tool exports
│       ├── base64_string_encodec.py
│       ├── color_converter.py
│       ├── http_client.py
│       ├── image_optimizer.py
│       ├── json_format_validate.py
│       ├── jwt_debugger.py
│       ├── lorem_ipsum_generator.py
│       ├── markdown_viewer.py
│       ├── random_string_generator.py
│       ├── regex_tester.py
│       ├── scratch_pad.py
│       ├── string_case_converter.py
│       ├── unix_time_converter.py
│       ├── url_encode_decode.py
│       ├── uuid_ulid_generator.py
│       ├── uvx_runner.py
│       ├── xml_beautifier.py
│       └── yaml_to_json.py
├── tests/                      # Test suite
├── docs/                       # Documentation
├── assets/                     # Static assets
├── scripts/                    # Build and installation scripts
├── pyproject.toml             # Project configuration
├── Makefile                   # Build automation
└── README.md                  # Project documentation
```

## Tool Integration Pattern

### 1. Tool Implementation Structure

Each tool follows a consistent three-part structure:

#### A. Backend Logic Class

```python
class ToolNameConverter:
    """Backend logic for the tool functionality."""

    @staticmethod
    def method_name(input_param: str) -> str:
        """Core functionality method."""
        # Implementation logic
        return result
```

#### B. Widget Creation Function

```python
def create_tool_name_widget(style_func, scratch_pad=None):
    """Create and return the tool widget.

    Args:
        style_func: Function to get QStyle for standard icons
        scratch_pad: Optional scratch pad widget to send results to

    Returns:
        QWidget: The complete tool widget
    """
    # Widget creation logic
    return widget
```

#### C. Tool Registration

Tools must be registered in three locations:

1. **Export in `devboost/tools/__init__.py`**:

```python
from .tool_name import create_tool_name_widget

__all__ = [
    # ... other tools
    "create_tool_name_widget",
]
```

2. **Import in `devboost/main.py`**:

```python
from .tools import (
    # ... other imports
    create_tool_name_widget,
)
```

3. **Register in tools list in `devboost/main.py`**:

```python
self.tools = [
    # ... other tools
    ("🌍", "Tool Display Name", "search keywords for tool"),
]
```

### 2. Main Application Architecture

#### Core Components

1. **DevDriverWindow**: Main application window class
2. **Sidebar**: Tool navigation with search functionality
3. **Content Area**: Stacked widget container for tool views
4. **Scratch Pad**: Dockable widget for collecting results

#### Key Features

- **Tool Search**: Real-time search with keyword matching
- **Keyboard Shortcuts**:
  - `Ctrl+Shift+F` / `Cmd+Shift+F`: Focus search
  - `Ctrl+Shift+T` / `Cmd+Shift+T`: Focus tool list
  - `Ctrl+Shift+S` / `Cmd+Shift+S`: Toggle scratch pad
- **Scratch Pad Integration**: Tools can send results to scratch pad
- **Responsive Layout**: Sidebar + content area with dockable scratch pad

### 3. Widget Creation Pattern

#### Standard Widget Structure

```python
def create_tool_widget(style_func, scratch_pad=None):
    # 1. Create main widget and layout
    widget = QWidget()
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(10, 5, 5, 10)
    main_layout.setSpacing(5)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    # 2. Apply consistent styling
    widget.setStyleSheet(get_tool_style())

    # 3. Initialize backend logic
    converter = BackendClass()

    # 4. Create input section
    input_section = create_input_section()

    # 5. Create separator
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)

    # 6. Create results section
    results_section = create_results_section()

    # 7. Add scratch pad integration if available
    if scratch_pad:
        send_button = QPushButton("Send to Scratch Pad")
        # Connect to scratch pad functionality

    # 8. Assemble layout
    main_layout.addLayout(input_section)
    main_layout.addWidget(separator)
    main_layout.addLayout(results_section)

    return widget
```

#### Common UI Elements

1. **Input Section**:

   - Input fields with clear labels
   - Action buttons (Now, Clipboard, Clear)
   - Format selection dropdowns
   - Tips/help text

2. **Results Section**:

   - Grid or list layout for results
   - Copy buttons for individual results
   - Clear formatting and labels

3. **Control Buttons**:
   - "Send to Scratch Pad" (if scratch_pad provided)
   - "Copy" buttons for results
   - "Clear" for resetting state

### 4. Styling and Theming

#### Style Functions

- `get_main_app_style()`: Main application styling
- `get_tool_style()`: Individual tool styling

#### Consistent Visual Elements

- Sidebar with tool icons and names
- Top bar with tool title
- Separators between sections
- Consistent button styling
- Proper spacing and margins

### 5. Tool Navigation Logic

#### Tool Selection Handler

```python
def _on_tool_selected(self, item):
    tool_name = item.data(Qt.ItemDataRole.UserRole)

    if tool_name == "Tool Display Name":
        self.top_bar_title.setText("Tool Display Name")
        self.stacked_widget.setCurrentWidget(self.tool_screen)
    # ... other tools
```

#### Screen Creation

```python
# In __init__ method
self.tool_screen = create_tool_widget(self.style, self.scratch_pad_widget)
self.stacked_widget.addWidget(self.tool_screen)
```

### 6. Dependencies and Build System

#### Core Dependencies

- **PyQt6**: GUI framework
- **Python 3.11+**: Minimum Python version
- **Standard Library**: Extensive use of built-in modules

#### Development Dependencies

- **pytest**: Testing framework
- **ruff**: Linting and formatting
- **pre-commit**: Git hooks
- **pyinstaller**: Application packaging

#### Build Commands

- `make install`: Setup development environment
- `make check`: Run linting and tests
- `make run`: Run application
- `make test`: Run test suite
- `make package`: Build executable

### 7. Testing Patterns

#### Test Structure

```python
# tests/test_tool_name.py
import pytest
from devboost.tools.tool_name import ToolNameConverter

class TestToolNameConverter:
    def test_method_name(self):
        # Test implementation
        pass
```

#### Test Coverage

- Backend logic unit tests
- Input validation tests
- Error handling tests
- Integration tests for widget creation

### 8. Configuration Management

#### User Data Directory

- Uses `appdirs` for cross-platform user data directory
- JSON-based configuration files
- Persistent settings and preferences

#### Configuration Pattern

```python
import appdirs
import json
from pathlib import Path

def get_config_dir():
    return Path(appdirs.user_data_dir("DevBoost", "DeskRiders"))

def load_config(filename):
    config_path = get_config_dir() / filename
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}
```

## Integration Checklist for New Tools

### Implementation Steps

1. ✅ **Create tool module** in `devboost/tools/`
2. ✅ **Implement backend logic class** with static methods
3. ✅ **Create widget creation function** following standard pattern
4. ✅ **Add tool export** in `devboost/tools/__init__.py`
5. ✅ **Import in main.py** and add to tools list
6. ✅ **Create screen instance** in `DevDriverWindow.__init__`
7. ✅ **Add navigation logic** in `_on_tool_selected`
8. ✅ **Add to stacked widget** in content area
9. ✅ **Create test file** in `tests/` directory
10. ✅ **Add comprehensive logging** for debugging
11. ✅ **Implement scratch pad integration** if applicable
12. ✅ **Follow consistent styling** using `get_tool_style()`

### Quality Standards

- **Logging**: Extensive logging for GUI debugging
- **Error Handling**: Graceful error handling with user feedback
- **Performance**: Responsive UI with background processing if needed
- **Accessibility**: Clear labels and keyboard navigation
- **Consistency**: Follow established patterns and styling

This documentation provides a comprehensive guide for understanding and extending the DevBoost application architecture.
