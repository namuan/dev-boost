import logging

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem

logger = logging.getLogger(__name__)


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
            self.search_results_label.setText(f"Showing {visible_count} of {total_tools} tools")
            self.search_results_label.setStyleSheet("""
                QLabel {
                    color: #339af0;
                    font-size: 12px;
                    padding: 2px 4px;
                }
            """)

        logger.info(f"Search feedback updated: '{self.search_results_label.text()}'")
