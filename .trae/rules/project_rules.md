# Dev Boost - AI Coding Agent Instructions

## Project Overview

Dev Boost is a PyQt6-based desktop application providing developer productivity tools. It features a plugin-style architecture with a sidebar navigation and stacked widget content area.

## Architecture

### Core Structure

- **Main Application**: `devboost/main_cli.py` - Contains `DevDriverWindow` (QMainWindow) with sidebar + content area layout
- **Tool Plugins**: `devboost/tools/` - Each tool is a factory function returning a QWidget (e.g., `create_json_formatter_widget()`)
- **Search System**: `devboost/tools_search.py` - Handles tool discovery and keyboard navigation
- **Styling**: `devboost/styles.py` - Centralized QSS styles with `COLORS`, `FONTS`, `LAYOUT` constants

### Tool Plugin Pattern

Each tool follows this pattern:

```python
def create_tool_widget() -> QWidget:
    # Create main widget with tool-specific UI
    # Import and apply styles from ..styles
    # Return configured widget
```

Tools are registered in `devboost/tools/__init__.py` and imported in `main_cli.py`.

## Development Workflows

### Essential Commands

- `make run` - Launch the application (not `uv run devboost`)
- `make test` - Run pytest suite
- `make check` - Run pre-commit hooks (ruff linting)

### Testing

- Tests in `tests/` directory mirror `devboost/` structure
- Use pytest with PyQt6 fixtures: `QApplication.instance()` pattern
- Mock PyQt signals/slots for unit testing
- Example: `tests/test_json_format_validate.py` shows validator testing patterns

### Code Quality

- **Ruff** for linting (configured in `pyproject.toml`)
- **Pre-commit hooks** for automated checks
- **Type hints** encouraged but not fully implemented
- **Logging** via Python logging module (see `main_cli.py` setup)

## Key Conventions

### UI Patterns

- Use `QSplitter` for resizable layouts (see `json_format_validate.py`)
- Apply styles via `get_tool_style()` from `styles.py`
- Status indicators use `get_status_style()` with success/error colors
- Consistent button styling with `BUTTON_STYLE`

### Tool Implementation

- Separate business logic from UI (e.g., `JSONValidator` class)
- Use PyQt signals for async operations
- Implement keyboard shortcuts consistently
- Add help dialogs for complex tools (see `RegexCheatSheetDialog`)

## Dependencies & Environment

- **Python 3.11+** required
- **PyQt6** for UI framework
- **uv** for dependency management (preferred over pip)
- **Key deps**: faker, jsonpath-ng, markdown, pyyaml
- **Dev deps**: pytest, pre-commit, ruff

## Integration Points

### Tool Registration

1. Create tool module in `devboost/tools/`
2. Export factory function in `devboost/tools/__init__.py`
3. Import and add to tools list in `main_cli.py`
4. Add search keywords to tools tuple

### Search Integration

Tools are searchable via keywords defined in `main_cli.py` tools list:

```python
("🔧", "Tool Name", "keyword1 keyword2 description")
```

## Limitations

- This is a PyQt6 application so it is not possible to use Preview to check the application.

## File References

- **Entry point**: `devboost/main_cli.py:main()`
- **Tool examples**: `devboost/tools/json_format_validate.py`, `devboost/tools/regex_tester.py`
- **Test examples**: `tests/test_json_format_validate.py`
- **Style guide**: `devboost/styles.py`
