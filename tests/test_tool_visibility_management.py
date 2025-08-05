import pytest
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QListWidgetItem

from devboost.main_cli import DevDriverWindow


class TestToolVisibilityManagement:
    """Test cases for tool list visibility management functionality."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        return QApplication.instance() or QApplication([])

    @pytest.fixture
    def window(self, app):
        """Create DevDriverWindow instance for testing."""
        return DevDriverWindow()

    def test_set_item_visibility_show(self, window):
        """Test that _set_item_visibility correctly shows an item."""
        # Create a test item
        item = QListWidgetItem("Test Item")
        item.setSizeHint(QSize(0, 0))  # Start hidden
        window.tool_list.addItem(item)

        # Show the item
        window._set_item_visibility(item, True)

        # Check that size hint is restored
        assert item.sizeHint().height() == 36
        assert item.sizeHint().width() == 0

    def test_set_item_visibility_hide(self, window):
        """Test that _set_item_visibility correctly hides an item."""
        # Create a test item
        item = QListWidgetItem("Test Item")
        item.setSizeHint(QSize(0, 36))  # Start visible
        window.tool_list.addItem(item)

        # Hide the item
        window._set_item_visibility(item, False)

        # Check that size hint is set to 0
        assert item.sizeHint().height() == 0
        assert item.sizeHint().width() == 0

    def test_matches_search_criteria_empty_query(self, window):
        """Test that empty search query matches all items."""
        result = window._matches_search_criteria("JSON Formatter", "json format", "")
        assert result is True

        result = window._matches_search_criteria("JSON Formatter", "json format", None)
        assert result is True

        result = window._matches_search_criteria("JSON Formatter", "json format", "   ")
        assert result is True

    def test_matches_search_criteria_name_match(self, window):
        """Test that search criteria matches tool names."""
        result = window._matches_search_criteria("JSON Formatter", "json format", "json")
        assert result is True

        result = window._matches_search_criteria("JSON Formatter", "json format", "JSON")
        assert result is True

        result = window._matches_search_criteria("JSON Formatter", "json format", "formatter")
        assert result is True

    def test_matches_search_criteria_keywords_match(self, window):
        """Test that search criteria matches tool keywords."""
        result = window._matches_search_criteria("JSON Formatter", "json format validate", "format")
        assert result is True

        result = window._matches_search_criteria("JSON Formatter", "json format validate", "validate")
        assert result is True

    def test_matches_search_criteria_no_match(self, window):
        """Test that search criteria correctly identifies non-matches."""
        result = window._matches_search_criteria("JSON Formatter", "json format", "xml")
        assert result is False

        result = window._matches_search_criteria("JSON Formatter", "json format", "regex")
        assert result is False

    def test_matches_search_criteria_case_insensitive(self, window):
        """Test that search criteria is case insensitive."""
        result = window._matches_search_criteria("JSON Formatter", "json format", "JSON")
        assert result is True

        result = window._matches_search_criteria("json formatter", "JSON FORMAT", "json")
        assert result is True

    def test_populate_tool_list(self, window):
        """Test that _populate_tool_list creates all tool items."""
        # Ensure tool list is empty
        window.tool_list.clear()
        assert window.tool_list.count() == 0

        # Populate the tool list
        window._populate_tool_list()

        # Check that all tools are added
        assert window.tool_list.count() == len(window.tools)

        # Check that each item has the correct data
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            tool_name = item.data(Qt.ItemDataRole.UserRole)

            # Verify tool name exists in tools list
            tool_names = [name for _, name, _ in window.tools]
            assert tool_name in tool_names

    def test_update_tool_visibility_show_all(self, window):
        """Test that _update_tool_visibility shows all items for empty query."""
        # Tool list is already populated during window initialization
        assert window.tool_list.count() == len(window.tools)

        # Update visibility with empty query
        visible_count = window._update_tool_visibility("")

        # All items should be visible
        assert visible_count == len(window.tools)

        # Check that all items are actually visible
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            assert item.sizeHint().height() == 36

    def test_update_tool_visibility_filter_json(self, window):
        """Test that _update_tool_visibility correctly filters for 'json'."""
        # Populate the tool list first
        window._populate_tool_list()

        # Update visibility with 'json' query
        visible_count = window._update_tool_visibility("json")

        # Should have at least one visible item (JSON Format/Validate)
        assert visible_count > 0
        assert visible_count < len(window.tools)

        # Check that JSON tool is visible
        json_tool_visible = False
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            tool_name = item.data(Qt.ItemDataRole.UserRole)
            if "JSON" in tool_name:
                assert item.sizeHint().height() == 36
                json_tool_visible = True

        assert json_tool_visible

    def test_update_tool_visibility_no_matches(self, window):
        """Test that _update_tool_visibility hides all items for non-matching query."""
        # Populate the tool list first
        window._populate_tool_list()

        # Update visibility with query that matches nothing
        visible_count = window._update_tool_visibility("nonexistentquery123")

        # No items should be visible
        assert visible_count == 0

        # Check that all items are actually hidden
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            assert item.sizeHint().height() == 0

    def test_filter_tools_integration(self, window):
        """Test the complete filter_tools method integration."""
        # Tool list is already populated during window initialization
        assert window.tool_list.count() == len(window.tools)

        window.filter_tools("json")

        # Should have same number of items but some hidden
        assert window.tool_list.count() == len(window.tools)

        # Should have some visible items
        visible_items = 0
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            if item.sizeHint().height() > 0:
                visible_items += 1

        assert visible_items > 0
        assert visible_items < len(window.tools)

    def test_filter_tools_clear_search(self, window):
        """Test that clearing search shows all tools."""
        # Populate and filter first
        window.filter_tools("json")

        # Clear the search
        window.filter_tools("")

        # All items should be visible
        visible_items = 0
        for i in range(window.tool_list.count()):
            item = window.tool_list.item(i)
            if item.sizeHint().height() > 0:
                visible_items += 1

        assert visible_items == len(window.tools)

    def test_list_widget_updates_after_visibility_changes(self, window):
        """Test that the list widget properly updates after visibility changes."""
        # Initial state - all items visible
        initial_visible = sum(
            1 for i in range(window.tool_list.count()) if window.tool_list.item(i).sizeHint().height() > 0
        )
        assert initial_visible == len(window.tools)

        # Filter to hide some items
        window.filter_tools("json")

        # Check that some items are hidden
        filtered_visible = sum(
            1 for i in range(window.tool_list.count()) if window.tool_list.item(i).sizeHint().height() > 0
        )
        assert filtered_visible < initial_visible

        # Clear filter to show all items again
        window.filter_tools("")

        # Check that all items are visible again
        final_visible = sum(
            1 for i in range(window.tool_list.count()) if window.tool_list.item(i).sizeHint().height() > 0
        )
        assert final_visible == len(window.tools)

        # Verify that the list widget update was called
        # This ensures the widget properly refreshes after visibility changes
        assert window.tool_list.count() == len(window.tools)
