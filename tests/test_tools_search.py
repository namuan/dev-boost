import unittest
from unittest.mock import Mock, patch

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QLabel, QListWidgetItem

from devboost.tools_search import NavigableToolsList, ToolsSearch


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
        self.tool_list = NavigableToolsList()
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
            mock_set_text.assert_called_once_with("2/4 tools [ENTER to select / ↑↓ to navigate]")
            mock_set_style.assert_called_once()
            # Check that the style contains info color
            style_call = mock_set_style.call_args[0][0]
            self.assertIn("#339af0", style_call)

    def test_update_search_feedback_whitespace_query(self):
        """Test search feedback with whitespace-only query."""
        with patch.object(self.search_results_label, "hide") as mock_hide:
            self.tools_search._update_search_feedback("   \n\t   ", 4)
            mock_hide.assert_called_once()

    def test_focus_tool_list_with_no_current_item(self):
        """Test focusing tool list when no item is currently selected."""
        # Make first item visible, others hidden
        self.tool_list.item(0).setSizeHint(QSize(0, 36))  # visible
        for i in range(1, self.tool_list.count()):
            self.tool_list.item(i).setSizeHint(QSize(0, 0))  # hidden

        # Ensure no current item is selected
        self.tool_list.setCurrentItem(None)

        with patch.object(self.tool_list, "setFocus") as mock_focus:
            self.tools_search.focus_tool_list()

            # Should select first visible item and focus the list
            current_item = self.tool_list.currentItem()
            self.assertIsNotNone(current_item)
            self.assertEqual(current_item.data(Qt.ItemDataRole.UserRole), "Base64 Encoder")
            mock_focus.assert_called_once()

    def test_focus_tool_list_with_current_item(self):
        """Test focusing tool list when an item is already selected."""
        # Set current item
        current_item = self.tool_list.item(1)
        self.tool_list.setCurrentItem(current_item)

        with patch.object(self.tool_list, "setFocus") as mock_focus:
            self.tools_search.focus_tool_list()

            # Should keep the current item and focus the list
            self.assertEqual(self.tool_list.currentItem(), current_item)
            mock_focus.assert_called_once()

    def test_focus_tool_list_no_visible_items(self):
        """Test focusing tool list when no items are visible."""
        # Hide all items
        for i in range(self.tool_list.count()):
            self.tool_list.item(i).setSizeHint(QSize(0, 0))

        # Clear current selection
        self.tool_list.setCurrentItem(None)

        with patch.object(self.tool_list, "setFocus") as mock_focus:
            self.tools_search.focus_tool_list()

            # Should still focus the list even if no items are visible
            self.assertIsNone(self.tool_list.currentItem())
            mock_focus.assert_called_once()


class TestNavigableToolsList(unittest.TestCase):
    """Test cases for NavigableToolsList class."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for testing."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.tool_list = NavigableToolsList()

        # Create test items
        self.test_items = [
            ("Tool 1", True),  # visible
            ("Tool 2", False),  # hidden
            ("Tool 3", True),  # visible
            ("Tool 4", True),  # visible
            ("Tool 5", False),  # hidden
        ]

        for name, visible in self.test_items:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            if visible:
                item.setSizeHint(QSize(0, 36))  # visible
            else:
                item.setSizeHint(QSize(0, 0))  # hidden
            self.tool_list.addItem(item)

    def test_get_visible_items(self):
        """Test getting visible items only."""
        visible_items = self.tool_list._get_visible_items()

        # Should only return visible items (Tool 1, Tool 3, Tool 4)
        self.assertEqual(len(visible_items), 3)
        visible_names = [item.data(Qt.ItemDataRole.UserRole) for item in visible_items]
        self.assertEqual(visible_names, ["Tool 1", "Tool 3", "Tool 4"])

    def test_navigate_visible_items_down(self):
        """Test navigating down through visible items."""
        # Set current item to first visible item (Tool 1)
        first_visible = self.tool_list.item(0)
        self.tool_list.setCurrentItem(first_visible)

        # Navigate down
        self.tool_list._navigate_visible_items(Qt.Key.Key_Down)

        # Should move to Tool 3 (next visible item)
        current_item = self.tool_list.currentItem()
        self.assertEqual(current_item.data(Qt.ItemDataRole.UserRole), "Tool 3")

    def test_navigate_visible_items_up(self):
        """Test navigating up through visible items."""
        # Set current item to Tool 3 (second visible item)
        second_visible = self.tool_list.item(2)
        self.tool_list.setCurrentItem(second_visible)

        # Navigate up
        self.tool_list._navigate_visible_items(Qt.Key.Key_Up)

        # Should move to Tool 1 (previous visible item)
        current_item = self.tool_list.currentItem()
        self.assertEqual(current_item.data(Qt.ItemDataRole.UserRole), "Tool 1")

    def test_navigate_wrap_around_down(self):
        """Test that navigation wraps around when going down from last item."""
        # Set current item to last visible item (Tool 4)
        last_visible = self.tool_list.item(3)
        self.tool_list.setCurrentItem(last_visible)

        # Navigate down (should wrap to first)
        self.tool_list._navigate_visible_items(Qt.Key.Key_Down)

        # Should wrap to Tool 1 (first visible item)
        current_item = self.tool_list.currentItem()
        self.assertEqual(current_item.data(Qt.ItemDataRole.UserRole), "Tool 1")

    def test_navigate_wrap_around_up(self):
        """Test that navigation wraps around when going up from first item."""
        # Set current item to first visible item (Tool 1)
        first_visible = self.tool_list.item(0)
        self.tool_list.setCurrentItem(first_visible)

        # Navigate up (should wrap to last)
        self.tool_list._navigate_visible_items(Qt.Key.Key_Up)

        # Should wrap to Tool 4 (last visible item)
        current_item = self.tool_list.currentItem()
        self.assertEqual(current_item.data(Qt.ItemDataRole.UserRole), "Tool 4")

    def test_key_press_event_arrow_keys(self):
        """Test that arrow key events are handled correctly."""
        with patch.object(self.tool_list, "_navigate_visible_items") as mock_navigate:
            # Test down arrow
            down_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
            self.tool_list.keyPressEvent(down_event)
            mock_navigate.assert_called_with(Qt.Key.Key_Down)

            # Test up arrow
            up_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            self.tool_list.keyPressEvent(up_event)
            mock_navigate.assert_called_with(Qt.Key.Key_Up)

    def test_key_press_event_enter_key(self):
        """Test that Enter key events trigger item selection."""
        # Set a current item
        first_item = self.tool_list.item(0)
        self.tool_list.setCurrentItem(first_item)

        with patch.object(self.tool_list, "itemClicked") as mock_clicked:
            # Test Enter key
            enter_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
            self.tool_list.keyPressEvent(enter_event)
            mock_clicked.emit.assert_called_once_with(first_item)

    def test_key_press_event_other_keys(self):
        """Test that other keys are passed to parent class."""
        with patch("PyQt6.QtWidgets.QListWidget.keyPressEvent") as mock_parent:
            # Test a non-arrow, non-enter key
            other_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
            self.tool_list.keyPressEvent(other_event)
            mock_parent.assert_called_once_with(other_event)

    def test_navigate_with_no_visible_items(self):
        """Test navigation when no items are visible."""
        # Hide all items
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            item.setSizeHint(QSize(0, 0))

        # Navigation should do nothing
        current_before = self.tool_list.currentItem()
        self.tool_list._navigate_visible_items(Qt.Key.Key_Down)
        current_after = self.tool_list.currentItem()

        self.assertEqual(current_before, current_after)


if __name__ == "__main__":
    unittest.main()
