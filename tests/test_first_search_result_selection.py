"""Tests for first search result selection logic.

This module tests the functionality that identifies and selects the first visible
tool item when Enter is pressed in the search input, and automatically triggers
the tool selection to switch to the corresponding tool view.
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from devboost.main_cli import DevDriverWindow


class TestFirstSearchResultSelection:
    """Test class for first search result selection logic."""

    @pytest.fixture
    def window(self):
        """Create a DevDriverWindow instance for testing."""
        window = DevDriverWindow()
        yield window
        window.close()

    def test_enter_key_switches_to_tool_view(self, window):
        """Test that pressing Enter switches to the first visible tool's view."""
        # Set a search query that will show specific tools
        window.search_input.setText("JSON")
        QApplication.processEvents()

        # Find the first visible tool
        first_visible_item = None
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            if item.sizeHint().height() > 0:
                first_visible_item = item
                break

        assert first_visible_item is not None, "Should have at least one visible tool"

        # Get the tool name and expected title
        tool_name = first_visible_item.data(Qt.ItemDataRole.UserRole)

        # Simulate pressing Enter in the search input
        QTest.keyPress(window.search_input, Qt.Key.Key_Return)
        QApplication.processEvents()

        # Verify that the tool is selected
        assert window.tool_list.currentItem() == first_visible_item

        # Verify that the top bar title is updated to match the selected tool
        assert window.top_bar_title.text() == tool_name

        # Verify that the stacked widget shows the correct tool view
        current_widget = window.stacked_widget.currentWidget()
        assert current_widget is not None

    def test_enter_key_with_unix_time_search(self, window):
        """Test Enter key with Unix Time search specifically."""
        # Search for Unix Time Converter
        window.search_input.setText("Unix")
        QApplication.processEvents()

        # Simulate pressing Enter
        QTest.keyPress(window.search_input, Qt.Key.Key_Return)
        QApplication.processEvents()

        # Verify that Unix Time Converter is selected and view is switched
        assert window.top_bar_title.text() == "Unix Time Converter"
        assert window.stacked_widget.currentWidget() == window.unix_time_converter_screen

    def test_enter_key_with_json_search(self, window):
        """Test Enter key with JSON search specifically."""
        # Search for JSON Format/Validate
        window.search_input.setText("JSON")
        QApplication.processEvents()

        # Simulate pressing Enter
        QTest.keyPress(window.search_input, Qt.Key.Key_Return)
        QApplication.processEvents()

        # Verify that JSON Format/Validate is selected and view is switched
        assert window.top_bar_title.text() == "JSON Format/Validate"
        assert window.stacked_widget.currentWidget() == window.json_format_validate_screen

    def test_enter_key_with_base64_search(self, window):
        """Test Enter key with Base64 search specifically."""
        # Search for Base64 String Encode/Decode
        window.search_input.setText("Base64")
        QApplication.processEvents()

        # Simulate pressing Enter
        QTest.keyPress(window.search_input, Qt.Key.Key_Return)
        QApplication.processEvents()

        # Verify that Base64 String Encode/Decode is selected and view is switched
        assert window.top_bar_title.text() == "Base64 String Encode/Decode"
        assert window.stacked_widget.currentWidget() == window.base64_string_encodec_screen

    def test_enter_key_with_no_matching_tools(self, window):
        """Test Enter key behavior when no tools match the search."""
        # Search for something that won't match any tools
        window.search_input.setText("NonExistentTool")
        QApplication.processEvents()

        # Store the current state before pressing Enter
        original_title = window.top_bar_title.text()
        original_widget = window.stacked_widget.currentWidget()

        # Simulate pressing Enter
        QTest.keyPress(window.search_input, Qt.Key.Key_Return)
        QApplication.processEvents()

        # Verify that nothing changes when no tools are visible
        assert window.top_bar_title.text() == original_title
        assert window.stacked_widget.currentWidget() == original_widget

    def test_focus_first_visible_tool_method_triggers_selection(self, window):
        """Test that _focus_first_visible_tool method triggers tool selection."""
        # Set a search query
        window.search_input.setText("JWT")
        QApplication.processEvents()

        # Call the method directly
        window._focus_first_visible_tool()
        QApplication.processEvents()

        # Verify that a tool is selected and view is switched
        current_item = window.tool_list.currentItem()
        assert current_item is not None

        tool_name = current_item.data(Qt.ItemDataRole.UserRole)
        assert window.top_bar_title.text() == tool_name

        # Verify that the stacked widget shows the correct tool view
        current_widget = window.stacked_widget.currentWidget()
        assert current_widget is not None
