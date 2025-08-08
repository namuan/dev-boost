import logging

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem

logger = logging.getLogger(__name__)


class NavigableToolsList(QListWidget):
    """Custom QListWidget that supports arrow key navigation through visible items only."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clear_search_callback = None

    def set_clear_search_callback(self, callback):
        """Set the callback function to clear the search.

        Args:
            callback: Function to call when Escape key is pressed
        """
        self.clear_search_callback = callback
        logger.info("Clear search callback set for NavigableToolsList")

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events for arrow key navigation, Enter selection, and Escape to clear search.

        Args:
            event: The key press event
        """
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self._navigate_visible_items(event.key())
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Trigger item click for the current item
            current_item = self.currentItem()
            if current_item:
                self.itemClicked.emit(current_item)
                logger.info(f"Enter pressed - selected tool: {current_item.data(Qt.ItemDataRole.UserRole)}")
        elif event.key() == Qt.Key.Key_Escape:
            # Clear the search when Escape is pressed
            if self.clear_search_callback:
                logger.info("Escape pressed in tools list - clearing search")
                self.clear_search_callback()
            else:
                logger.warning("Escape pressed but no clear search callback set")
        else:
            # Let the parent handle other keys
            super().keyPressEvent(event)

    def _navigate_visible_items(self, key):
        """Navigate through visible items only.

        Args:
            key: The arrow key pressed (Qt.Key.Key_Up or Qt.Key.Key_Down)
        """
        visible_items = self._get_visible_items()
        if not visible_items:
            return

        current_item = self.currentItem()
        current_index = -1

        # Find current item in visible items list
        if current_item:
            for i, item in enumerate(visible_items):
                if item == current_item:
                    current_index = i
                    break

        # Calculate next index based on key direction
        if key == Qt.Key.Key_Down:
            next_index = (current_index + 1) % len(visible_items)
        else:  # Key_Up
            next_index = (current_index - 1) % len(visible_items)

        # Set the new current item
        next_item = visible_items[next_index]
        self.setCurrentItem(next_item)
        self.scrollToItem(next_item)
        logger.info(f"Navigated to: {next_item.data(Qt.ItemDataRole.UserRole)}")

    def _get_visible_items(self):
        """Get a list of currently visible items.

        Returns:
            List of QListWidgetItem objects that are currently visible
        """
        visible_items = []
        for i in range(self.count()):
            item = self.item(i)
            if item.sizeHint().height() > 0:  # Item is visible
                visible_items.append(item)
        return visible_items


class ToolsSearch:
    """Handles search functionality for the tools list."""

    def __init__(self, tool_list: QListWidget, search_results_label: QLabel, tools: list[tuple[str, str, str]]):
        """
        Initialize the ToolsSearch with required UI components.

        Args:
            tool_list: The QListWidget containing the tools
            search_results_label: The QLabel for displaying search feedback
            tools: List of tuples containing (icon, name, keywords) for each tool
        """
        self.tool_list = tool_list
        self.search_results_label = search_results_label
        self.tools = tools
        self.current_search_text = ""

        # Initialize debounce timer for search input
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self._perform_search)
        logger.info("Search debounce timer initialized")

    def on_search_text_changed(self, text: str):
        """Handle search input text change events with debouncing.

        Args:
            text: The current text in the search input field
        """
        logger.info(f"Search text changed: '{text}'")
        # Store the current search text for the debounced search
        self.current_search_text = text
        # Stop any existing timer and start a new one
        self.search_debounce_timer.stop()
        self.search_debounce_timer.start(300)  # 300ms debounce delay

    def _perform_search(self):
        """Perform the actual search filtering after debounce delay."""
        if hasattr(self, "current_search_text"):
            logger.info(f"Performing debounced search for: '{self.current_search_text}'")
            self.filter_tools(self.current_search_text)

    def _set_item_visibility(self, item: QListWidgetItem, visible: bool):
        """Set the visibility of a QListWidget item.

        Args:
            item: The QListWidgetItem to show or hide
            visible: True to show the item, False to hide it
        """
        if visible:
            item.setSizeHint(QSize(0, 36))  # Restore original size
        else:
            item.setSizeHint(QSize(0, 0))  # Hide by setting size to 0

        # Also hide/show the item widget if it exists
        widget = self.tool_list.itemWidget(item)
        if widget:
            widget.setVisible(visible)

    def _matches_search_criteria(self, tool_name: str, tool_keywords: str, search_query: str) -> bool:
        """Check if a tool matches the search criteria.

        Args:
            tool_name: The name of the tool
            tool_keywords: The keywords associated with the tool
            search_query: The search query to match against

        Returns:
            True if the tool matches the search criteria, False otherwise
        """
        if not search_query or not search_query.strip():
            return True  # Empty search shows all items

        query_lower = search_query.lower().strip()
        name_lower = tool_name.lower()
        keywords_lower = tool_keywords.lower()

        # Check for partial matches in name or keywords
        return query_lower in name_lower or query_lower in keywords_lower

    def _update_tool_visibility(self, search_query: str) -> int:
        """Update the visibility of all tool items based on search query.

        Args:
            search_query: The search query to filter tools by

        Returns:
            The number of visible tools after filtering
        """
        visible_count = 0

        # Iterate through all tool items and set visibility
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            tool_name = item.data(Qt.ItemDataRole.UserRole)

            # Find the corresponding tool data
            tool_data = None
            for icon, name, keywords in self.tools:
                if name == tool_name:
                    tool_data = (icon, name, keywords)
                    break

            if tool_data:
                icon, name, keywords = tool_data
                # Check if item matches search query using the dedicated method
                if self._matches_search_criteria(name, keywords, search_query):
                    self._set_item_visibility(item, True)
                    visible_count += 1
                else:
                    self._set_item_visibility(item, False)
            else:
                # If tool data not found, hide the item
                self._set_item_visibility(item, False)

        # Force the list widget to update its layout
        self.tool_list.update()

        return visible_count

    def focus_first_visible_tool(self, on_tool_selected_callback):
        """Focus on the first visible tool in the filtered results and switch to its view.

        This method is called when the user presses Enter in the search input.
        It finds the first tool item that is currently visible, selects it, and
        automatically triggers the tool selection to switch to the corresponding tool view.

        Args:
            on_tool_selected_callback: Callback function to handle tool selection
        """
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            # Check if the item is visible (size hint height > 0)
            if item.sizeHint().height() > 0:
                # Set the current item and focus on it
                self.tool_list.setCurrentItem(item)
                self.tool_list.setFocus()
                # Trigger tool selection to switch to the tool view
                on_tool_selected_callback(item)
                logger.info(f"Selected and switched to first visible tool: {item.data(Qt.ItemDataRole.UserRole)}")
                return

    def focus_tool_list(self):
        """Focus the tool list widget for keyboard navigation.

        This method sets focus to the tool list and ensures the first visible
        item is selected if no item is currently selected.
        """
        # If no current item is selected, select the first visible one
        if not self.tool_list.currentItem():
            for i in range(self.tool_list.count()):
                item = self.tool_list.item(i)
                if item.sizeHint().height() > 0:  # Item is visible
                    self.tool_list.setCurrentItem(item)
                    break

        self.tool_list.setFocus()
        logger.info("Tool list focused for keyboard navigation")

        logger.info("No visible tools found to focus on")

    def filter_tools(self, search_query: str):
        """Filter the tools list based on search query using visibility management.

        Args:
            search_query: The search string to filter tools by
        """
        logger.info(f"Filtering tools with query: '{search_query}'")

        # Update tool visibility based on search query
        visible_count = self._update_tool_visibility(search_query)

        # Update visual feedback for search results
        self._update_search_feedback(search_query, visible_count)

        logger.info(f"Visible tools: {visible_count} out of {self.tool_list.count()} tools")

    def _update_search_feedback(self, search_query: str, visible_count: int):
        """Update visual feedback for search results.

        Args:
            search_query: The current search query
            visible_count: Number of visible tools after filtering
        """
        if not search_query.strip():
            # No search query - hide feedback label
            self.search_results_label.hide()
            return

        # Show feedback label when searching
        self.search_results_label.show()

        total_tools = self.tool_list.count()

        if visible_count == 0:
            # No results found
            self.search_results_label.setText(f"No tools found for '{search_query}'")
            self.search_results_label.setStyleSheet("""
                QLabel {
                    color: #ff6b6b;
                    font-size: 12px;
                    padding: 2px 4px;
                    font-style: italic;
                }
            """)
        elif visible_count == total_tools:
            # All tools visible
            self.search_results_label.setText(f"Showing all {total_tools} tools")
            self.search_results_label.setStyleSheet("""
                QLabel {
                    color: #51cf66;
                    font-size: 12px;
                    padding: 2px 4px;
                }
            """)
        else:
            # Some tools filtered
            self.search_results_label.setText(
                f"{visible_count}/{total_tools} tools" f" [ENTER to select / ↑↓ to navigate]"
            )
            self.search_results_label.setStyleSheet("""
                QLabel {
                    color: #339af0;
                    font-size: 12px;
                    padding: 2px 4px;
                }
            """)

        logger.info(f"Search feedback updated: '{self.search_results_label.text()}'")
