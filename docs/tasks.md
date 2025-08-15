# Dev Boost Improvement Tasks

This enumerated checklist captures actionable, repository-specific improvements. Each item is designed to be independently checkable and is ordered from foundational hygiene to architectural refactors, code-level enhancements, UX, performance, and release/operations.

## Foundational Project Hygiene

1. [ ] Establish code style, typing, and quality gates

   - [x] Add ruff config to pyproject.toml (lint + import sort) and fix violations
   - [ ] Add black or ruff format step and format entire codebase
   - [ ] Introduce mypy with strict-ish settings and add/adjust type hints incrementally
   - [ ] Enforce pytest -q with coverage thresholds (e.g., 85%)

2. [ ] Continuous Integration (CI)

   - [ ] Add GitHub Actions workflow (lint, type-check, tests on 3.10–3.12, macOS + Ubuntu)
   - [ ] Cache dependencies (uv/pip) and test artifacts
   - [ ] Upload coverage to codecov (optional) and fail on threshold drop

3. [ ] Dependency management and reproducibility

   - [ ] Audit runtime/test deps; pin and group in pyproject.toml
   - [ ] Validate uv.lock is current; document uv commands in README
   - [ ] Add safety or pip-audit step to CI for vulnerability checks

4. [ ] Developer workflows
   - [ ] Add Makefile targets (lint, format, typecheck, test, package)
   - [ ] Add a pre-commit config to run ruff/black/mypy on changed files
   - [ ] Create CONTRIBUTING.md with dev setup, coding standards, and commit style

## Architecture and Cross-Cutting Concerns

5. [ ] Define a standardized Tool interface and registration system

   - [ ] Create a Tool base class (name, icon, widget factory, optional CLI hooks)
   - [ ] Implement dynamic discovery/registration in devboost/tools/**init**.py
   - [ ] Replace ad-hoc tool wiring in main.py with registry-driven menu/launcher

6. [ ] Centralized state and messaging

   - [ ] Introduce an AppState object for shared state (theme, recent tools, settings)
   - [ ] Add a lightweight event bus/signals for tool-to-app notifications
   - [ ] Remove direct widget-to-widget coupling in favor of events/state

7. [ ] Configuration management

   - [ ] Implement persistent settings in user config dir (platform-aware)
   - [ ] Add per-tool settings schema with validation and defaults
   - [ ] Expose settings UI and import/export (JSON/YAML)

8. [ ] Logging and error handling

   - [ ] Configure structured logging (logging.config) with levels and handlers
   - [ ] Standardize error boundaries in tools with user-friendly dialogs
   - [ ] Central exception hook for PyQt to avoid hard crashes; log with context

9. [ ] Threading and responsiveness (PyQt6)
   - [ ] Offload long-running work to QThread/QThreadPool (no blocking UI)
   - [ ] Ensure signal/slot thread-safety and avoid direct cross-thread widget access
   - [ ] Add busy indicators/cancellation for background tasks

## Targeted Refactors (Module-Level)

10. [ ] Unix Time Converter (devboost/tools/unix_time_converter.py ~644 lines)

    - [x] Extract pure conversion/parsing logic into a separate module/class
    - [ ] Split widget layout code into smaller functions or classes
    - [ ] Improve date/time parsing with clear error messages and unit tests
    - [x] Add timezone handling tests; validate against python datetime/zoneinfo
    - [ ] Reduce side effects; inject logger and settings instead of globals

11. [ ] Tools UI standardization

    - [ ] Create reusable UI components (Header, InputPanel, OutputPanel, Footer)
    - [ ] Apply consistent spacing, icons (assets/icon.icns), and styles via devboost/styles.py
    - [ ] Introduce common actions: Copy, Clear, Send to Scratch Pad, Help

12. [ ] Tools Search (devboost/tools_search.py)

    - [ ] Improve indexing to support tags/categories and fuzzy matching
    - [x] Add debounce for search input to reduce UI churn
    - [ ] Expand tests (tests/test_tools_search.py) to cover edge cases and scale

13. [ ] Error-prone utilities
    - [ ] Review url_encode_decode.py and json_format_validate.py for edge cases
    - [ ] Add robust error messages and unit tests for invalid inputs
    - [ ] Ensure consistent Unicode handling across tools

## Testing Strategy and Coverage

14. [ ] Expand unit tests for untested/under-tested tools

    - [ ] Add tests for markdown_viewer.py, lorem_ipsum_generator.py, xml_beautifier.py
    - [ ] Increase test coverage for color_converter, regex_tester edge cases
    - [x] Add tests for uuid_ulid_generator random/ULID invariants

15. [ ] Integration and UI tests

    - [ ] Smoke test main.py app boot and tool registry wiring (headless/offscreen)
    - [ ] Use QtTest or pytest-qt to test critical UI flows (open tool, copy output)
    - [ ] Snapshot test widget rendering where feasible

16. [ ] Test infrastructure improvements
    - [ ] Introduce factory/helpers for building tool widgets in tests
    - [ ] Add fixtures for temp dirs, clipboard, timezone overrides
    - [ ] Run tests under multiple locales/timezones to catch time-related bugs

## User Experience and Accessibility

17. [ ] Keyboard and shortcuts

    - [ ] Define global and per-tool shortcuts; show in menus/tooltips
    - [ ] Add a keyboard shortcuts help overlay

18. [ ] Accessibility (a11y)

    - [ ] Ensure focus order, tab navigation, and accessible names/labels
    - [ ] High-contrast theme and font scaling; respect OS accessibility settings

19. [ ] Internationalization (i18n)

    - [ ] Externalize user-facing strings; prepare for translations
    - [ ] Add locale selection and RTL layout support where applicable

20. [ ] Scratch Pad improvements (devboost/tools/scratch_pad.py)
    - [ ] Add timestamps, sections, and search within scratch pad
    - [ ] Export/import scratch content; autosave option

## Performance and Reliability

21. [ ] Startup and memory

    - [ ] Lazy-load tool widgets; only import heavy deps on demand
    - [ ] Profile startup; defer non-critical work until idle

22. [ ] Robustness

    - [ ] Guard clipboard operations and provide fallbacks per OS
    - [ ] Validate file I/O paths; sandbox where possible

23. [ ] Time and timezone correctness
    - [ ] Validate DST transitions, leap seconds handling strategies
    - [x] Add regression tests for historical timestamps and extreme future dates

## Packaging, Distribution, and Release

24. [ ] Packaging

    - [ ] Review/modernize main.spec (PyInstaller) for reproducible builds
    - [ ] Add platform-specific icons/resources and verify signing/notarization steps (macOS)
    - [ ] Create distributable artifacts via CI (macOS .app/.dmg, Linux AppImage)

25. [ ] Versioning and changelog

    - [ ] Adopt semantic versioning; store version in devboost/**init**.py
    - [ ] Automate changelog generation (e.g., towncrier or keep a CHANGELOG.md)

26. [ ] Documentation

    - [ ] Expand README with installation, CLI usage (main_cli.py), and troubleshooting
    - [ ] Add architecture overview diagrams and tool authoring guide
    - [ ] Document settings, themes, and per-tool configuration

27. [ ] Security and privacy
    - [ ] Add a SECURITY.md and disclosure policy
    - [ ] Document data handling; ensure sensitive data (e.g., JWTs) isn’t logged

## Future Enhancements (Optional Roadmap)

28. [ ] Tool interoperability

    - [ ] Allow tools to pass data via a shared clipboard/bus with typed payloads
    - [ ] Define simple workflow compositions between tools

29. [ ] Plugin ecosystem

    - [ ] Define plugin packaging spec and manifest
    - [ ] Build an in-app plugin browser with install/update/remove

30. [ ] Cloud sync (opt-in)
    - [ ] Sync settings/history via a provider-agnostic backend
    - [ ] Provide offline-first conflict resolution
