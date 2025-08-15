# Dev Boost – Comprehensive Project Rules and Guide

## Project Overview

Dev Boost is a PyQt6-based desktop application providing a collection of developer tools to boost productivity. It features a sidebar navigation and a stacked widget content area, with 14+ tools such as JSON Formatter/Validator, RegExp Tester, URL Encode/Decode, UUID/ULID Generator, YAML→JSON, XML Beautifier, Unix Time Converter, Color Converter, Markdown Viewer, Lorem Ipsum Generator, Random String Generator, Base64 Encoder/Decoder, JWT Debugger, and a persistent Scratch Pad.

## Architecture

### Core Structure

- Main Application: devboost/main_cli.py – contains DevDriverWindow (QMainWindow) with sidebar + content layout
- Tool Plugins: devboost/tools/ – each tool provides a factory function that returns a QWidget
- Search System: devboost/tools_search.py – tool discovery and keyboard navigation
- Styling: devboost/styles.py – centralized QSS styles with COLORS, FONTS, LAYOUT

### Tool Plugin Pattern

Each tool follows this pattern:

```python
def create_tool_widget() -> QWidget:
    # Create main widget with tool-specific UI
    # Import and apply styles from ..styles
    # Return configured widget
```

Tools are registered in devboost/tools/**init**.py and imported in main_cli.py.

### Project Structure (high level)

```
dev-boost/
├── devboost/                 # Main package
│   ├── __init__.py
│   ├── main.py               # Main window and startup logic
│   ├── styles.py             # Shared UI styling and themes
│   ├── tools/                # Individual tools and exports
│   └── tools_search.py       # Search and navigation
├── tests/                    # Unit tests for tools and systems
├── assets/                   # Images and static assets
├── docs/                     # Documentation
└── build/dist                # Build artifacts and distributions
```

## Development Workflows

### Essential Commands

- make run – launch the application (dev mode)
- make test – run pytest suite
- make check – run pre-commit hooks (ruff linting/formatting, etc.)
- make build – build distributables (PyInstaller)
- make install-macosx – install as a macOS app

### Installation

```bash
# From repository root
make install
```

### Development Utilities

```bash
# Run specific tests
uv run pytest tests/test_regex_tester.py -v

# Lint and format
uv run ruff check .
uv run ruff format .
```

## Testing

- Tests mirror the devboost/ structure under tests/.
- Use pytest with the QApplication.instance() pattern for PyQt6 widgets.
- Mock PyQt signals/slots where helpful for isolation.
- See tests/test_json_format_validate.py for validator testing patterns.

## Code Quality

- Ruff for linting and formatting (configured in pyproject.toml).
- Pre-commit hooks enforce: case/merge conflict checks, TOML/YAML validation, EOF, trailing whitespace, pyupgrade, ruff, ruff-format, prettier.
- Type hints encouraged but not mandatory.
- Logging via Python logging module (see main_cli.py setup).

## Dependencies & Environment

- Python 3.11+ (project) / Python 3.12+ (development guidance in QWEN)
- PyQt6 for UI
- uv for dependency management
- Key deps: faker, jsonpath-ng, markdown, pyyaml
- Dev deps: pytest, pre-commit, ruff

## Key Conventions

### UI Patterns

- Use QSplitter for resizable layouts (see json_format_validate.py).
- Apply styles via get_tool_style() from styles.py.
- Status indicators should use get_status_style() with success/error colors.
- Consistent button styling with BUTTON_STYLE.

### Tool Implementation

- Separate business logic from UI (e.g., JSONValidator class).
- Use PyQt signals for async operations.
- Implement keyboard shortcuts consistently.
- Add help dialogs for complex tools (e.g., RegexCheatSheetDialog).

### Scratch Pad Integration

When a tool supports output to the shared Scratch Pad:

1. Add a parameter scratch_pad=None to the widget creation function.
2. Add a "Send to Scratch Pad" button.
3. Implement context-specific formatting for the content.
4. Connect the button to send formatted content to the scratch pad.

## Integration Points

### Tool Registration

1. Create the tool module under devboost/tools/.
2. Export the factory function in devboost/tools/**init**.py.
3. Import and add to the tools list in main_cli.py.
4. Provide search keywords in the tools list, e.g.:

```python
("🔧", "Tool Name", "keyword1 keyword2 description")
```

### Search Integration

- Tools are searchable via keywords defined in main_cli.py tools list.
- Search functionality implemented in tools_search.py handles filtering and keyboard navigation.

## Key Components

### Main Application (devboost/main.py)

- DevDriverWindow main window class
- Sidebar navigation with tool listing
- Search for tools (+ keyboard shortcuts, e.g., Cmd+Shift+F for search, Cmd+Shift+T for tool list)
- Scratch Pad dock widget

### Tools System

- Tools organized in devboost/tools/ with one file per tool.
- **init**.py exports tool creation functions.

### Styles (devboost/styles.py)

- Centralized QSS styling using a common color palette and component styles.

### Search (devboost/tools_search.py)

- Filters tools in the sidebar and supports keyboard navigation.

## Recent Development Activities (Patterns to Follow)

- "Send to Scratch Pad" implemented across several tools with contextual formatting:
  - RegExp Tester: includes pattern, matches, and input text.
  - URL Encode/Decode: includes mode and input/output context.
  - Base64 String Encode/Decode: includes mode and input/output context.

Follow this pattern when extending to other tools.

## Limitations

- PyQt6 desktop app: online preview tools cannot render or interact with the UI.

## File References

- Entry point: devboost/main_cli.py:main()
- Tool examples: devboost/tools/json_format_validate.py, devboost/tools/regex_tester.py
- Test examples: tests/test_json_format_validate.py
- Style guide: devboost/styles.py

## License

This project is licensed under the MIT License. See the LICENSE file for details.
