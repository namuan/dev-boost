from unittest.mock import patch

import pytest
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication

from devboost.main_cli import DevDriverWindow


class TestKeyboardShortcuts:
    """Test keyboard shortcut functionality."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()

    @pytest.fixture
    def window(self, app):
        """Create DevDriverWindow instance for testing."""
        return DevDriverWindow()

    def test_setup_keyboard_shortcuts_called(self, window):
        """Test that _setup_keyboard_shortcuts is called during initialization."""
        # The method should have been called during __init__
        # We can verify by checking that shortcuts exist
        shortcuts = window.findChildren(QShortcut)
        assert len(shortcuts) > 0, "No keyboard shortcuts found"

    def test_ctrl_shift_f_shortcut_exists(self, window):
        """Test that Ctrl+Shift+F shortcut is created."""
        shortcuts = window.findChildren(QShortcut)
        ctrl_shift_f_shortcuts = [s for s in shortcuts if s.key() == QKeySequence("Ctrl+Shift+F")]
        assert len(ctrl_shift_f_shortcuts) >= 1, "Ctrl+Shift+F shortcut not found"

    @patch("sys.platform", "darwin")
    def test_cmd_shift_f_shortcut_exists_on_macos(self, window):
        """Test that Cmd+Shift+F shortcut is created on macOS."""
        # Create a new window with mocked platform
        window_mac = DevDriverWindow()
        shortcuts = window_mac.findChildren(QShortcut)
        cmd_shift_f_shortcuts = [s for s in shortcuts if s.key() == QKeySequence("Cmd+Shift+F")]
        assert len(cmd_shift_f_shortcuts) >= 1, "Cmd+Shift+F shortcut not found on macOS"

    def test_focus_search_input_method_exists(self, window):
        """Test that _focus_search_input method exists."""
        assert hasattr(window, "_focus_search_input"), "_focus_search_input method not found"
        assert callable(window._focus_search_input), "_focus_search_input is not callable"

    def test_focus_search_input_functionality(self, window):
        """Test that _focus_search_input focuses and selects text in search input."""
        # Set some text in the search input
        window.search_input.setText("test search")

        # Ensure search input doesn't have focus initially
        window.search_input.clearFocus()
        assert not window.search_input.hasFocus(), "Search input should not have focus initially"

        # Call the focus method
        window._focus_search_input()

        # Verify search input has focus
        assert window.search_input.hasFocus(), "Search input should have focus after calling _focus_search_input"

        # Verify text is selected
        assert window.search_input.selectedText() == "test search", "Search input text should be selected"

    def test_shortcut_activation_focuses_search(self, window):
        """Test that activating the shortcut focuses the search input."""
        # Set some text in the search input
        window.search_input.setText("shortcut test")
        window.search_input.clearFocus()

        # Find the Ctrl+Shift+F shortcut
        shortcuts = window.findChildren(QShortcut)
        ctrl_shift_f_shortcut = next((s for s in shortcuts if s.key() == QKeySequence("Ctrl+Shift+F")), None)
        assert ctrl_shift_f_shortcut is not None, "Ctrl+Shift+F shortcut not found"

        # Activate the shortcut
        ctrl_shift_f_shortcut.activated.emit()

        # Verify search input has focus and text is selected
        assert window.search_input.hasFocus(), "Search input should have focus after shortcut activation"
        assert (
            window.search_input.selectedText() == "shortcut test"
        ), "Search input text should be selected after shortcut activation"

    def test_search_input_exists(self, window):
        """Test that search_input attribute exists and is accessible."""
        assert hasattr(window, "search_input"), "search_input attribute not found"
        assert window.search_input is not None, "search_input should not be None"

        # Verify it's a QLineEdit
        from PyQt6.QtWidgets import QLineEdit

        assert isinstance(window.search_input, QLineEdit), "search_input should be a QLineEdit"

    def test_multiple_shortcut_activations(self, window):
        """Test that the shortcut can be activated multiple times."""
        # Set initial text
        window.search_input.setText("first text")
        window.search_input.clearFocus()

        # Find and activate shortcut first time
        shortcuts = window.findChildren(QShortcut)
        ctrl_shift_f_shortcut = next((s for s in shortcuts if s.key() == QKeySequence("Ctrl+Shift+F")), None)

        ctrl_shift_f_shortcut.activated.emit()
        assert window.search_input.hasFocus(), "First activation should focus search input"

        # Change text and clear focus
        window.search_input.setText("second text")
        window.search_input.clearFocus()

        # Activate shortcut second time
        ctrl_shift_f_shortcut.activated.emit()
        assert window.search_input.hasFocus(), "Second activation should focus search input"
        assert window.search_input.selectedText() == "second text", "Second activation should select new text"
