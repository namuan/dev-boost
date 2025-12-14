# Adding a New Tool

## Overview

- DevBoost tools are implemented as Python packages under `devboost.tools.<tool_name>` and are lazily loaded to keep startup fast.
- Each tool exposes a single factory function `create_<tool_name>_widget(...)` that returns a `PyQt6` `QWidget` for the UI.
- Tools must be registered in `devboost.tools.lazy_loader` and listed in `main.spec` so the build includes them.

## Features

- Lazy-loaded modules via dynamic import; only loaded when the user selects the tool.
- Consistent factory pattern: returns a ready-to-use `QWidget`, no subclass required.
- Optional Scratch Pad integration for sending output/results.
- Centralized registration for display names and factory locations.
- PyInstaller integration via `hiddenimports` to package dynamically imported tools.

## Usage

1. Create the package
   - Add a new directory `devboost/tools/my_tool/` with `__init__.py` and `my_tool.py`.
2. Implement the widget factory
   - Follow the `JSON Diff` pattern (`devboost/tools/json_diff/json_diff.py:125`). Keep the same signature and return a `QWidget`.
3. Export from `__init__.py`
   - Re-export the factory (and any public classes) so `importlib.import_module('devboost.tools.my_tool')` can find it.
4. Register the tool in the lazy loader
   - Add a new entry to `TOOL_REGISTRY` with the UI display name, module path, and factory name.
5. Add the tool to the build spec
   - Append the package path to `hidden_tool_imports` in `main.spec` so PyInstaller includes it.
6. Verify
   - Run `make check` to lint and test, then `make run` to launch the app and open your tool.

## API References

- Registry: `devboost/tools/lazy_loader.py:16` defines `TOOL_REGISTRY` mapping display names to `(module_path, factory_name)`.
- Lazy import: `devboost/tools/lazy_loader.py:52` `get_tool_factory(tool_name)` dynamically imports and caches the factory.
- Widget creation: `devboost/tools/lazy_loader.py:97` `create_tool_widget(tool_name, style_func, scratch_pad)` calls the factory; it passes `scratch_pad` to most tools.
- Build hidden imports: `main.spec:9`–`main.spec:39` lists dynamic tool packages under `hidden_tool_imports`.
- Example factory in an existing tool: `devboost/tools/json_diff/json_diff.py:125` implements `create_json_diff_widget`.
- Public exports: `devboost/tools/json_diff/__init__.py:3`–`devboost/tools/json_diff/__init__.py:12` re-exports the factory and classes.

## Parameters

- `create_<tool_name>_widget(style_func=None, scratch_pad_widget=None) -> QWidget`
  - `style_func`: Optional style function injected by the app. If unused, keep the parameter for consistency.
  - `scratch_pad_widget`: Optional Scratch Pad component. If provided, tools can append or set text on it (see JSON Diff usage in `devboost/tools/json_diff/json_diff.py:369`–`devboost/tools/json_diff/json_diff.py:392`).
  - Returns: A fully composed `QWidget` to be placed in the main UI.

## Examples

### Minimal tool implementation

```python
# devboost/tools/my_tool/my_tool.py
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from devboost.styles import get_tool_style, get_status_style

logger = logging.getLogger(__name__)


def create_my_tool_widget(style_func=None, scratch_pad_widget=None) -> QWidget:
    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel("Hello from My Tool"))

    def _send_to_scratch_pad() -> None:
        try:
            if not scratch_pad_widget:
                return
            content = "My Tool output"
            if hasattr(scratch_pad_widget, "append_text"):
                scratch_pad_widget.append_text(content)
            elif hasattr(scratch_pad_widget, "text_edit"):
                existing = scratch_pad_widget.text_edit.toPlainText()
                scratch_pad_widget.text_edit.setPlainText(f"{existing}\n\n---\n{content}" if existing else content)
            logger.info("Sent output to scratch pad")
        except Exception:
            logger.exception("Failed to send output to scratch pad")

    btn = QPushButton("Send to Scratch Pad")
    btn.setStyleSheet(get_status_style("info"))
    btn.clicked.connect(_send_to_scratch_pad)
    layout.addWidget(btn)

    return widget
```

### Public exports

```python
# devboost/tools/my_tool/__init__.py
from .my_tool import create_my_tool_widget

__all__ = ["create_my_tool_widget"]
```

### Register in the lazy loader

```python
# devboost/tools/lazy_loader.py
TOOL_REGISTRY = {
    # ... existing entries ...
    "My Tool": ("devboost.tools.my_tool", "create_my_tool_widget"),
}
```

- Reference: `devboost/tools/lazy_loader.py:16` shows how existing tools (e.g., "JSON Diff") are mapped to their module paths and factory names.

### Add to the build spec

```python
# main.spec
hidden_tool_imports = [
    # ... existing tool packages ...
    'devboost.tools.my_tool',
]
```

- Reference: `main.spec:9`–`main.spec:39` contains all existing dynamic tool packages.

## Notes

- Display name: The key used in `TOOL_REGISTRY` (e.g., "JSON Diff" or "My Tool") is what the UI shows to users.
- Scratch Pad: Most tools accept `scratch_pad_widget`. If your tool does not use it, simply ignore the parameter. Special cases like "Block Editor" and "Scratch Pad" are handled in `create_tool_widget` (`devboost/tools/lazy_loader.py:115`–`devboost/tools/lazy_loader.py:117`).
- Exports: Ensure your package’s `__init__.py` re-exports the factory; the lazy loader imports the package (not the module file) and accesses the factory via `getattr`.
- Logging: Use `logging.getLogger(__name__)` and add info/debug logs around key actions for consistency across tools.
- Styling: Apply `get_tool_style()` on the root widget for consistent theming (`devboost/tools/json_diff/json_diff.py:141`). Use `get_status_style(kind)` for status areas.
- Packaging data: If your tool needs non-code assets, adjust `main.spec` `datas` or use `collect_data_files` for your package. The current spec sets `datas=[]`.
- Verification: Run `make check` before opening a PR and `make run` to manually test the new tool.
