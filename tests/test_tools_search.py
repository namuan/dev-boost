import unittest
from unittest.mock import Mock, patch

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QLabel, QListWidget, QListWidgetItem

from devboost.tools_search import ToolsSearch


class TestToolsSearch(unittest.TestCase):
    """Test cases for ToolsSearch class."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tool_list = QListWidget()
        self.search_results_label = QLabel()
        self.tools = [
            ("icon1", "Base64 Encoder", "base64 encode decode string"),
            ("icon2", "JSON Formatter", "json format validate pretty"),
            ("icon3", "UUID Generator", "uuid ulid generate unique"),
            ("icon4", "Color Converter", "color hex rgb hsl convert"),
        ]

        # Create some test items in the tool list
        for _, name, _ in self.tools:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setSizeHint(QSize(0, 36))
            self.tool_list.addItem(item)

        self.tools_search = ToolsSearch(self.tool_list, self.search_results_label, self.tools)

    def test_initialization(self):
        """Test that ToolsSearch initializes correctly."""
        self.assertEqual(self.tools_search.tool_list, self.tool_list)
        self.assertEqual(self.tools_search.search_results_label, self.search_results_label)
        self.assertEqual(self.tools_search.tools, self.tools)
        self.assertEqual(self.tools_search.current_search_text, "")
        self.assertIsInstance(self.tools_search.search_debounce_timer, QTimer)
        self.assertTrue(self.tools_search.search_debounce_timer.isSingleShot())

    def test_on_search_text_changed(self):
        """Test search text change handling with debouncing."""
        with (
            patch.object(self.tools_search.search_debounce_timer, "stop") as mock_stop,
            patch.object(self.tools_search.search_debounce_timer, "start") as mock_start,
        ):
            self.tools_search.on_search_text_changed("test")

            self.assertEqual(self.tools_search.current_search_text, "test")
            mock_stop.assert_called_once()
            mock_start.assert_called_once_with(300)

    def test_perform_search(self):
        """Test the debounced search execution."""
        self.tools_search.current_search_text = "json"

        with patch.object(self.tools_search, "filter_tools") as mock_filter:
            self.tools_search._perform_search()
            mock_filter.assert_called_once_with("json")

    def test_perform_search_without_current_text(self):
        """Test perform search when current_search_text is not set."""
        # Remove the attribute to simulate the condition
        if hasattr(self.tools_search, "current_search_text"):
            delattr(self.tools_search, "current_search_text")

        with patch.object(self.tools_search, "filter_tools") as mock_filter:
            self.tools_search._perform_search()
            mock_filter.assert_not_called()

    def test_set_item_visibility_visible(self):
        """Test setting item visibility to visible."""
        item = self.tool_list.item(0)
        mock_widget = Mock()

        with patch.object(self.tool_list, "itemWidget", return_value=mock_widget):
            self.tools_search._set_item_visibility(item, True)

            self.assertEqual(item.sizeHint(), QSize(0, 36))
            mock_widget.setVisible.assert_called_once_with(True)

    def test_set_item_visibility_hidden(self):
        """Test setting item visibility to hidden."""
        item = self.tool_list.item(0)
        mock_widget = Mock()

        with patch.object(self.tool_list, "itemWidget", return_value=mock_widget):
            self.tools_search._set_item_visibility(item, False)

            self.assertEqual(item.sizeHint(), QSize(0, 0))
            mock_widget.setVisible.assert_called_once_with(False)

    def test_set_item_visibility_no_widget(self):
        """Test setting item visibility when no widget is associated."""
        item = self.tool_list.item(0)

        with patch.object(self.tool_list, "itemWidget", return_value=None):
            # Should not raise an exception
            self.tools_search._set_item_visibility(item, True)
            self.assertEqual(item.sizeHint(), QSize(0, 36))

    def test_matches_search_criteria_empty_query(self):
        """Test search criteria matching with empty query."""
        result = self.tools_search._matches_search_criteria("Test Tool", "test keywords", "")
        self.assertTrue(result)

        result = self.tools_search._matches_search_criteria("Test Tool", "test keywords", "   ")
        self.assertTrue(result)

    def test_matches_search_criteria_name_match(self):
        """Test search criteria matching by tool name."""
        result = self.tools_search._matches_search_criteria("Base64 Encoder", "encode decode", "base64")
        self.assertTrue(result)

        result = self.tools_search._matches_search_criteria("Base64 Encoder", "encode decode", "BASE64")
        self.assertTrue(result)

        result = self.tools_search._matches_search_criteria("Base64 Encoder", "encode decode", "encoder")
        self.assertTrue(result)

    def test_matches_search_criteria_keywords_match(self):
        """Test search criteria matching by keywords."""
        result = self.tools_search._matches_search_criteria("Tool Name", "json format validate", "json")
        self.assertTrue(result)

        result = self.tools_search._matches_search_criteria("Tool Name", "json format validate", "FORMAT")
        self.assertTrue(result)

    def test_matches_search_criteria_no_match(self):
        """Test search criteria with no match."""
        result = self.tools_search._matches_search_criteria("Base64 Encoder", "encode decode", "xml")
        self.assertFalse(result)

    def test_update_tool_visibility(self):
        """Test updating tool visibility based on search query."""
        with (
            patch.object(self.tools_search, "_set_item_visibility") as mock_set_visibility,
            patch.object(self.tool_list, "update") as mock_update,
        ):
            visible_count = self.tools_search._update_tool_visibility("json")

            # Should find 1 match (JSON Formatter)
            self.assertEqual(visible_count, 1)

            # Check that _set_item_visibility was called for each item
            self.assertEqual(mock_set_visibility.call_count, 4)
            mock_update.assert_called_once()

    def test_update_tool_visibility_empty_query(self):
        """Test updating tool visibility with empty query (show all)."""
        with patch.object(self.tools_search, "_set_item_visibility") as mock_set_visibility:
            visible_count = self.tools_search._update_tool_visibility("")

            # Should show all tools
            self.assertEqual(visible_count, 4)

            # All items should be set to visible
            for call in mock_set_visibility.call_args_list:
                self.assertTrue(call[0][1])  # Second argument should be True

    def test_update_tool_visibility_no_match(self):
        """Test updating tool visibility with query that matches nothing."""
        with patch.object(self.tools_search, "_set_item_visibility") as mock_set_visibility:
            visible_count = self.tools_search._update_tool_visibility("nonexistent")

            # Should find no matches
            self.assertEqual(visible_count, 0)

            # All items should be set to hidden
            for call in mock_set_visibility.call_args_list:
                self.assertFalse(call[0][1])  # Second argument should be False

    def test_focus_first_visible_tool(self):
        """Test focusing on the first visible tool."""
        # Set up items with different visibility
        items = [self.tool_list.item(i) for i in range(4)]
        items[0].setSizeHint(QSize(0, 0))  # Hidden
        items[1].setSizeHint(QSize(0, 36))  # Visible
        items[2].setSizeHint(QSize(0, 36))  # Visible
        items[3].setSizeHint(QSize(0, 0))  # Hidden

        mock_callback = Mock()

        with (
            patch.object(self.tool_list, "setCurrentItem") as mock_set_current,
            patch.object(self.tool_list, "setFocus") as mock_set_focus,
        ):
            self.tools_search.focus_first_visible_tool(mock_callback)

            # Should select the first visible item (index 1)
            mock_set_current.assert_called_once_with(items[1])
            mock_set_focus.assert_called_once()
            mock_callback.assert_called_once_with(items[1])

    def test_focus_first_visible_tool_no_visible(self):
        """Test focusing when no tools are visible."""
        # Hide all items
        for i in range(4):
            self.tool_list.item(i).setSizeHint(QSize(0, 0))

        mock_callback = Mock()

        with patch.object(self.tool_list, "setCurrentItem") as mock_set_current:
            self.tools_search.focus_first_visible_tool(mock_callback)

            mock_set_current.assert_not_called()
            mock_callback.assert_not_called()

    def test_filter_tools(self):
        """Test the main filter_tools method."""
        with (
            patch.object(self.tools_search, "_update_tool_visibility", return_value=2) as mock_update_visibility,
            patch.object(self.tools_search, "_update_search_feedback") as mock_update_feedback,
        ):
            self.tools_search.filter_tools("test query")

            mock_update_visibility.assert_called_once_with("test query")
            mock_update_feedback.assert_called_once_with("test query", 2)

    def test_update_search_feedback_empty_query(self):
        """Test search feedback with empty query."""
        with patch.object(self.search_results_label, "hide") as mock_hide:
            self.tools_search._update_search_feedback("", 4)
            mock_hide.assert_called_once()

    def test_update_search_feedback_no_results(self):
        """Test search feedback with no results."""
        with (
            patch.object(self.search_results_label, "show") as mock_show,
            patch.object(self.search_results_label, "setText") as mock_set_text,
            patch.object(self.search_results_label, "setStyleSheet") as mock_set_style,
        ):
            self.tools_search._update_search_feedback("nonexistent", 0)

            mock_show.assert_called_once()
            mock_set_text.assert_called_once_with("No tools found for 'nonexistent'")
            mock_set_style.assert_called_once()
            # Check that the style contains error color
            style_call = mock_set_style.call_args[0][0]
            self.assertIn("#ff6b6b", style_call)

    def test_update_search_feedback_all_tools_visible(self):
        """Test search feedback when all tools are visible."""
        with (
            patch.object(self.search_results_label, "show") as mock_show,
            patch.object(self.search_results_label, "setText") as mock_set_text,
            patch.object(self.search_results_label, "setStyleSheet") as mock_set_style,
            patch.object(self.tool_list, "count", return_value=4),
        ):
            self.tools_search._update_search_feedback("query", 4)

            mock_show.assert_called_once()
            mock_set_text.assert_called_once_with("Showing all 4 tools")
            mock_set_style.assert_called_once()
            # Check that the style contains success color
            style_call = mock_set_style.call_args[0][0]
            self.assertIn("#51cf66", style_call)

    def test_update_search_feedback_partial_results(self):
        """Test search feedback with partial results."""
        with (
            patch.object(self.search_results_label, "show") as mock_show,
            patch.object(self.search_results_label, "setText") as mock_set_text,
            patch.object(self.search_results_label, "setStyleSheet") as mock_set_style,
            patch.object(self.tool_list, "count", return_value=4),
        ):
            self.tools_search._update_search_feedback("json", 2)

            mock_show.assert_called_once()
            mock_set_text.assert_called_once_with("Showing 2 of 4 tools")
            mock_set_style.assert_called_once()
            # Check that the style contains info color
            style_call = mock_set_style.call_args[0][0]
            self.assertIn("#339af0", style_call)

    def test_update_search_feedback_whitespace_query(self):
        """Test search feedback with whitespace-only query."""
        with patch.object(self.search_results_label, "hide") as mock_hide:
            self.tools_search._update_search_feedback("   \n\t   ", 4)
            mock_hide.assert_called_once()


if __name__ == "__main__":
    unittest.main()
