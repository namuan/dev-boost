# Dev Boost Refactoring Plan

## Overview

This document outlines the refactoring plan for Dev Boost codebase following the established refactoring rules: small concise functions, consistent patterns, simplified conditionals, minimized nesting depth, descriptive names, and minimal variable lifespan.

## Phase 1: High-Level Architecture Refactoring

### 1.1 Tool Registration System

**Problem**: Tools are hard-coded in \_on_tool_selected() method
**Location**: devboost/main.py:\_on_tool_selected()
**Impact**: Reduces coupling, improves maintainability

**Refactoring Strategy**:

```python
# Current anti-pattern
if tool_name == "Unix Time Converter":
    widget = create_unix_time_widget(scratch_pad)
elif tool_name == "JSON Formatter":
    widget = create_json_tool_widget(scratch_pad)
# ... 14 more elif statements

# Proposed solution
tool_registry = {
    "Unix Time Converter": create_unix_time_widget,
    "JSON Formatter": create_json_tool_widget,
    # ... ordered dictionary mapping
}

def _on_tool_selected(self, item):
    tool_name = item.data(Qt.ItemDataRole.UserRole)
    if tool_name in self.tool_registry:
        widget_factory = self.tool_registry[tool_name]
        self._display_tool_widget(widget_factory, scratch_pad=self.scratch_pad)
```

### 1.2 UI Component Factories

**Problem**: Individual create_tool_widget() functions are monolithic
**Strategy**: Extract reusable component factories

## Phase 2: Function Decomposition

### 2.1 \_create_sidebar() Refactoring

**File**: devboost/main.py
**Current**: ~175 lines
**Target**: 4 separate functions (25 lines each)

**Proposed Structure**:

```python
def _create_sidebar(self) -> QWidget:
    sidebar = QWidget()
    layout = QVBoxLayout(sidebar)

    # Extracted to separate methods
    search_widget = self._create_search_input()
    tools_list = self._create_tools_list()
    scratch_pad = self._create_scratch_pad_access()

    layout.addWidget(search_widget)
    layout.addWidget(tools_list)
    layout.addWidget(scratch_pad)

    return sidebar

def _create_search_input(self) -> QWidget:
    # ~25 lines: Search box and clear button
    pass

def _create_tools_list(self) -> NavigableToolsList:
    # ~25 lines: Tool list with styling
    pass

def _create_scratch_pad_access(self) -> QPushButton:
    # ~25 lines: Scratch pad quick access
    pass
```

### 2.2 Tool Widget Scaffolding

**File**: JSON Formatter and similar tools
**Strategy**: Create abstract base class for tool widgets

**Benefits**:

- Consistent initialization patterns
- Reduced code duplication
- Easier testing
- Maintained consistency across tools

### 2.3 Color Converter Complexity

**File**: color_converter.py
**Issues Identified**:

- Color format detection chain: 12+ elif statements
- Conversion logic intermixed with UI updates
- Mathematical operations nested in conditional branches

**Refactoring Strategy**:

- Extract color parsers to strategy pattern
- Extract conversion algorithms to separate utility classes
- Separate validation from presentation
- Create ColorConversionError hierarchy

## Phase 3: Pattern Standardization

### 3.1 Consistent Tool Plugin Pattern

**Current Inconsistencies**:

- Some tools have external validation classes (JSONValidator)
- Others integrate validation within widget
- Signal patterns vary between tools

**Standardized Pattern**:

```python
# Base pattern all tools follow
class BaseToolValidator:
    def validate(self, input_data) -> ValidationResult:
        pass

class BaseToolWidget(QWidget):
    def __init__(self, scratch_pad=None):
        super().__init__()
        self.validator = self._get_validator()
        self._setup_ui()
        self._connect_signals()

    def _get_validator(self):
        # Override to provide tool-specific validator
        pass
```

### 3.2 Signal Connection Patterns

**Current**: Inline signal connections mixed with layout code
**Target**: Centralized connection method

**Current**:

```python
# Anti-pattern
def format_json():
    # long inline function
format_button.clicked.connect(format_json)
```

**Refactored**:

```python
def _connect_signals(self):
    self.format_button.clicked.connect(self._handle_format_request)
    self.copy_button.clicked.connect(self._handle_copy_request)
    self.copy_button.clicked.connect(self._handle_clear_request)
```

### 3.3 Input/Output Widget Patterns

**Problem**: Every tool re-creates toolbar layout for copy/save buttons
**Solution**: Reusable ToolbarFactory

## Phase 4: Naming and Structure Improvements

### 4.1 Variable Scope Minimization

**Examples of Long-Lived Variables**:

- Color state variables in ColorConverter
- Regex cache in RegExpTester
- JSONPath caches across tools

**Refactoring**: Bundle into context/operation objects created per operation

### 4.2 Helper Method Naming

**Current**: Generic names like 'format_json', 'validate_xml'
**Target**: Descriptive names like '\_format_json_with_indentation', '\_validate_xml_syntax_only'

## Phase 5: Testing Facilitation

### 5.1 Testable Components

**Goal**: Lower complexity functions for easier unit testing

**Current Challenge**:

- 200+ line create_tool_widget() impossible to test
- Complex tool logic intermixed with UI

**Resolution**:

- Extract business logic to testable validators
- Create UI-agnostic test harnesses
- Use dependency injection for external systems

## Implementation Timeline

### Week 1: Foundation

- [ ] Create base tool widget classes
- [ ] Refactor \_on_tool_selected() to dictionary dispatch
- [ ] Extract \_create_sidebar() components

### Week 2: Tool Standardization

- [ ] Refactor JSON Formatter per plan
- [ ] Apply patterns to 3-4 similar tools
- [ ] Update test suite for extracted validators

### Week 3: Pattern Rollout

- [ ] Refactor remaining tools using established patterns
- [ ] Address color converter complexity
- [ ] Update documentation to reflect new patterns

### Week 4: Testing & Polish

- [ ] Complete remaining refactors
- [ ] Ensure all tests pass with new structure
- [ ] Final code review and consistency check

## Risk Mitigation

### High-Risk Changes:

1. **Tool registration refactoring**: May break tool selection

   - **Mitigation**: Extensive unit testing of dispatch logic
   - **Mitigation**: Manual testing of each tool selection

2. **Widget initialization**: Changes to base classes
   - **Mitigation**: Gradual implementation starting with less complex tools
   - **Mitigation**: Test factory patterns independently

### Backwards Compatibility:

- All refactors will maintain existing public interfaces
- Tool creation functions retain same signatures
- User-facing behavior remains unchanged

### Testing Strategy:

- Before/after comparison testing
- Gradual tool-by-tool refactoring
- Regression test suite preservation
- Interface stability checks

## Success Metrics

**Function Size Reduction**:

- Target: Average function size <25 lines
- Current: Several >150 lines
- Measure: Line count per function post-refactor

**Nesting Depth**:

- Target: Maximum nesting depth of 3
- Some current: 6+ levels

**Pattern Consistency**:

- Measure: Consistent factory usage across tools
- Measure: Signal connection patterns
- Measure: Naming convention adherence

**Testability**:

- New: Extracted validators with >90% code coverage
- New: Reduced UI test complexity
- Measure: Overall test coverage increase
