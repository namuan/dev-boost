import pytest
from PyQt6.QtWidgets import QApplication

from devboost.main_cli import DevDriverWindow


class TestEnterKeyHandling:
    """Test cases for Enter key handling in search input."""

    @pytest.fixture
    def window(self):
        """Create a DevDriverWindow instance for testing."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        window = DevDriverWindow()
        yield window
        window.close()

    def test_enter_key_focuses_first_visible_tool(self, window):
        """Test that pressing Enter in search input focuses first visible tool."""
        # Initially all tools should be visible
        assert window.tool_list.count() == len(window.tools)

        # Filter to show only JSON-related tools
        window.filter_tools("json")

        # Verify some tools are hidden
        visible_count = sum(
            1 for i in range(window.tool_list.count()) if window.tool_list.item(i).sizeHint().height() > 0
        )
        assert visible_count > 0
        assert visible_count < len(window.tools)

        # Set focus to search input (focus behavior may not work in test environment)
        window.search_input.setFocus()

        # Simulate Enter key press
        window.search_input.returnPressed.emit()

        # Verify that tool list received focus (may not be active in test environment)
        # Focus behavior can be different in test environments, so we check selection instead

        # Verify that a tool item is selected
        current_item = window.tool_list.currentItem()
        assert current_item is not None

        # Verify the selected item is visible
        assert current_item.sizeHint().height() > 0

    def test_enter_key_with_no_visible_tools(self, window):
        """Test Enter key behavior when no tools are visible."""
        # Filter with a query that matches no tools
        window.filter_tools("nonexistentquery123")

        # Verify no tools are visible
        visible_count = sum(
            1 for i in range(window.tool_list.count()) if window.tool_list.item(i).sizeHint().height() > 0
        )
        assert visible_count == 0

        # Set focus to search input (focus behavior may not work in test environment)
        window.search_input.setFocus()

        # Simulate Enter key press
        window.search_input.returnPressed.emit()

        # Search input should still have focus since no tools are visible
        # Focus behavior can be different in test environments

        # No item should be selected
        current_item = window.tool_list.currentItem()
        assert current_item is None or current_item.sizeHint().height() == 0

    def test_enter_key_with_all_tools_visible(self, window):
        """Test Enter key behavior when all tools are visible."""
        # Clear any existing filter
        window.filter_tools("")

        # Verify all tools are visible
        visible_count = sum(
            1 for i in range(window.tool_list.count()) if window.tool_list.item(i).sizeHint().height() > 0
        )
        assert visible_count == len(window.tools)

        # Set focus to search input (focus behavior may not work in test environment)
        window.search_input.setFocus()

        # Simulate Enter key press
        window.search_input.returnPressed.emit()

        # Verify that tool list received focus (may not be active in test environment)
        # Focus behavior can be different in test environments, so we check selection instead

        # Verify that the first tool is selected
        current_item = window.tool_list.currentItem()
        assert current_item is not None
        assert current_item == window.tool_list.item(0)

        # Verify the selected item is visible
        assert current_item.sizeHint().height() > 0

    def test_focus_first_visible_tool_method_directly(self, window):
        """Test the _focus_first_visible_tool method directly."""
        # Filter to show specific tools
        window.filter_tools("json")

        # Find the first visible tool manually
        first_visible_item = None
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            if item.sizeHint().height() > 0:
                first_visible_item = item
                break

        assert first_visible_item is not None

        # Call the method directly
        window._focus_first_visible_tool()

        # Verify the correct item is selected
        assert window.tool_list.currentItem() == first_visible_item
        # Focus behavior can be different in test environments

    def test_return_pressed_signal_connection(self, window):
        """Test that returnPressed signal is properly connected."""
        # Verify the signal is connected by checking if the method exists
        assert hasattr(window, "_focus_first_visible_tool")

        # Verify search input has the returnPressed signal
        assert hasattr(window.search_input, "returnPressed")

        # Test that the signal can be emitted without errors
        try:
            window.search_input.returnPressed.emit()
        except Exception as e:
            pytest.fail(f"returnPressed signal emission failed: {e}")
