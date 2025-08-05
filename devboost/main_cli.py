import logging
import sys

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .styles import get_main_app_style
from .tools import (
    create_base64_string_encodec_widget,
    create_color_converter_widget,
    create_json_formatter_widget,
    create_jwt_debugger_widget,
    create_lorem_ipsum_tool_widget,
    create_markdown_preview_widget,
    create_regexp_tester_widget,
    create_string_case_converter_widget,
    create_unix_time_converter_widget,
    create_url_codec_widget,
    create_uuid_ulid_tool_widget,
    create_xml_formatter_widget,
    create_yaml_to_json_widget,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class DevDriverWindow(QMainWindow):
    def __init__(self):
        logger.info("Initializing DevDriverWindow")
        super().__init__()
        self.setWindowTitle("Dev Boost")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(950, 600)
        logger.info("Window properties set: title='Dev Boost', geometry=(100,100,1200,800), min_size=(950,600)")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        logger.info("Central widget created and set")

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        logger.info("Main layout configured")

        logger.info("Creating sidebar widget")
        sidebar_widget = self._create_sidebar()
        logger.info("Creating content area widget")
        self.content_widget = self._create_content_area()

        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.content_widget)
        logger.info("Sidebar and content area added to main layout")

        logger.info("Applying styles")
        self._apply_styles()

        self.tool_list.itemClicked.connect(self._on_tool_selected)
        logger.info("Tool selection event handler connected")

        # Initialize debounce timer for search input
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self._perform_search)
        logger.info("Search debounce timer initialized")

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        logger.info("Keyboard shortcuts initialized")

        logger.info("DevDriverWindow initialization completed successfully")

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the application."""
        logger.info("Setting up keyboard shortcuts")

        # Create shortcut for focusing search input (Cmd+Shift+F on macOS, Ctrl+Shift+F on other platforms)
        search_shortcut = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        search_shortcut.activated.connect(self._focus_search_input)
        logger.info("Search focus shortcut (Ctrl+Shift+F) created")

        # On macOS, also add the Cmd+Shift+F variant
        if sys.platform == "darwin":
            search_shortcut_mac = QShortcut(QKeySequence("Cmd+Shift+F"), self)
            search_shortcut_mac.activated.connect(self._focus_search_input)
            logger.info("Search focus shortcut (Cmd+Shift+F) created for macOS")

    def _focus_search_input(self):
        """Focus the search input and select all text."""
        logger.info("Focusing search input via keyboard shortcut")
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _create_sidebar(self):
        logger.info("Starting sidebar creation")
        sidebar_container = QWidget()
        sidebar_container.setObjectName("sidebar")
        sidebar_container.setFixedWidth(300)
        logger.info("Sidebar container created with width=300")

        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)

        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(5)

        # Search input row
        search_input_container = QWidget()
        search_input_layout = QHBoxLayout(search_input_container)
        search_input_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...   ⌘⇧F")
        self.search_input.setFixedHeight(38)
        logger.info("Search input field created")

        # Connect text change signal to filtering logic
        self.search_input.textChanged.connect(self.on_search_text_changed)
        logger.info("Search input textChanged signal connected to on_search_text_changed")

        # Connect Enter key press to focus first visible tool
        self.search_input.returnPressed.connect(self._focus_first_visible_tool)
        logger.info("Search input returnPressed signal connected to _focus_first_visible_tool")

        search_input_layout.addWidget(self.search_input)

        # Search results feedback label
        self.search_results_label = QLabel()
        self.search_results_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 2px 4px;
            }
        """)
        self.search_results_label.hide()  # Initially hidden
        logger.info("Search results feedback label created")

        search_layout.addWidget(search_input_container)
        search_layout.addWidget(self.search_results_label)

        self.tool_list = QListWidget()
        self.tool_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tool_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        logger.info("Tool list widget created")

        self.tools = [
            ("🕒", "Unix Time Converter", "timestamp epoch time date convert unix"),
            ("{}", "JSON Format/Validate", "json format validate pretty print beautify"),
            ("64", "Base64 String Encode/Decode", "base64 encode decode string text"),
            ("✴️", "JWT Debugger", "jwt token debug decode verify json web token"),
            ("✳️", "RegExp Tester", "regex regexp regular expression test match pattern"),
            ("%", "URL Encode/Decode", "url encode decode percent encoding uri"),
            ("🆔", "UUID/ULID Generate/Decode", "uuid ulid generate decode identifier unique"),
            ("📄", "XML Beautifier", "xml format beautify pretty print"),
            ("⇄", "YAML to JSON", "yaml json convert transform"),
            ("✏️", "String Case Converter", "string case convert upper lower camel snake"),
            ("🎨", "Color Converter", "color convert hex rgb hsl css"),
            ("📝", "Lorem Ipsum Generator", "lorem ipsum text placeholder dummy"),
            ("📋", "Markdown Viewer", "markdown preview render view md"),
        ]
        logger.info(f"Defined {len(self.tools)} tools for the sidebar")

        for icon_text, tool_name, _keywords in self.tools:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 36))
            item_widget = self._create_tool_item_widget(icon_text, tool_name)
            item.setData(Qt.ItemDataRole.UserRole, tool_name)
            self.tool_list.addItem(item)
            self.tool_list.setItemWidget(item, item_widget)
        logger.info(f"Populated tool list with {len(self.tools)} items")

        sidebar_layout.addWidget(search_container)
        sidebar_layout.addWidget(self.tool_list)
        logger.info("Sidebar creation completed successfully")

        return sidebar_container

    def _create_tool_item_widget(self, icon_text, tool_name):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(12)

        icon_label = QLabel(icon_text)
        icon_label.setObjectName("toolIcon")
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(tool_name)
        text_label.setObjectName("toolText")

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()

        return widget

    def _create_content_area(self):
        logger.info("Starting content area creation")
        content_container = QWidget()
        content_container.setObjectName("contentArea")
        logger.info("Content container created")

        main_content_layout = QVBoxLayout(content_container)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)

        # Top bar
        self.top_bar = QWidget()
        self.top_bar.setObjectName("topBar")
        self.top_bar.setFixedHeight(44)
        top_bar_layout = QHBoxLayout(self.top_bar)
        logger.info("Top bar created")
        top_bar_layout.setContentsMargins(15, 0, 15, 0)

        self.top_bar_title = QLabel("")
        self.top_bar_title.setObjectName("topBarTitle")

        top_bar_layout.addWidget(self.top_bar_title)
        top_bar_layout.addStretch()

        # Stacked widget for different tool views
        self.stacked_widget = QStackedWidget()
        logger.info("Stacked widget created for tool views")

        logger.info("Creating welcome screen")
        self.welcome_screen = self._create_welcome_screen()
        logger.info("Creating Unix Time Converter screen")
        self.unix_time_converter_screen = create_unix_time_converter_widget(self.style)
        logger.info("Creating JSON Format/Validate screen")
        self.json_format_validate_screen = create_json_formatter_widget(self.style)
        logger.info("Creating Base64 String Encode/Decode screen")
        self.base64_string_encodec_screen = create_base64_string_encodec_widget(self.style)
        logger.info("Creating JWT Debugger screen")
        self.jwt_debugger_screen = create_jwt_debugger_widget(self.style)
        logger.info("Creating RegExp Tester screen")
        self.regexp_tester_screen = create_regexp_tester_widget(self.style)
        logger.info("Creating URL Encode Decode screen")
        self.url_codec_screen = create_url_codec_widget(self.style)
        logger.info("Creating UUID/ULID Generate/Decode screen")
        self.uuid_ulid_generator_screen = create_uuid_ulid_tool_widget(self.style)
        logger.info("Creating XML Beautifier screen")
        self.xml_formatter_screen = create_xml_formatter_widget(self.style)
        logger.info("Creating YAML to JSON screen")
        self.yaml_to_json_screen = create_yaml_to_json_widget(self.style)
        logger.info("Creating String Case Converter screen")
        self.string_case_converter_screen = create_string_case_converter_widget(self.style)
        logger.info("Creating Color Converter screen")
        self.color_converter_screen = create_color_converter_widget(self.style)
        logger.info("Creating Lorem Ipsum Generator screen")
        self.lorem_ipsum_generator_screen = create_lorem_ipsum_tool_widget(self.style)
        logger.info("Creating Markdown Viewer screen")
        self.markdown_viewer_screen = create_markdown_preview_widget()

        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.unix_time_converter_screen)
        self.stacked_widget.addWidget(self.json_format_validate_screen)
        self.stacked_widget.addWidget(self.base64_string_encodec_screen)
        self.stacked_widget.addWidget(self.jwt_debugger_screen)
        self.stacked_widget.addWidget(self.regexp_tester_screen)
        self.stacked_widget.addWidget(self.url_codec_screen)
        self.stacked_widget.addWidget(self.uuid_ulid_generator_screen)
        self.stacked_widget.addWidget(self.xml_formatter_screen)
        self.stacked_widget.addWidget(self.yaml_to_json_screen)
        self.stacked_widget.addWidget(self.string_case_converter_screen)
        self.stacked_widget.addWidget(self.color_converter_screen)
        self.stacked_widget.addWidget(self.lorem_ipsum_generator_screen)
        self.stacked_widget.addWidget(self.markdown_viewer_screen)

        main_content_layout.addWidget(self.top_bar)
        main_content_layout.addWidget(self.stacked_widget)
        logger.info("Content area creation completed successfully")

        return content_container

    def _create_welcome_screen(self):
        logger.info("Creating welcome screen widget")
        center_stage = QWidget()
        center_layout = QVBoxLayout(center_stage)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        v_box = QVBoxLayout()
        v_box.setSpacing(15)
        v_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_name_label = QLabel("👈 Welcome to Dev Boost ... Select any tool")
        app_name_label.setObjectName("appName")
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        v_box.addWidget(app_name_label)
        v_box.addSpacing(20)

        center_layout.addLayout(v_box)
        logger.info("Welcome screen creation completed")
        return center_stage

    # ruff: noqa: C901
    def _on_tool_selected(self, item):
        tool_name = item.data(Qt.ItemDataRole.UserRole)
        logger.info(f"Tool selected: {tool_name}")
        if tool_name == "Unix Time Converter":
            self.top_bar_title.setText("Unix Time Converter")
            self.stacked_widget.setCurrentWidget(self.unix_time_converter_screen)
            logger.info("Switched to Unix Time Converter view")
        elif tool_name == "JSON Format/Validate":
            self.top_bar_title.setText("JSON Format/Validate")
            self.stacked_widget.setCurrentWidget(self.json_format_validate_screen)
            logger.info("Switched to JSON Format/Validate view")
        elif tool_name == "Base64 String Encode/Decode":
            self.top_bar_title.setText("Base64 String Encode/Decode")
            self.stacked_widget.setCurrentWidget(self.base64_string_encodec_screen)
            logger.info("Switched to Base64 String Encode/Decode view")
        elif tool_name == "JWT Debugger":
            self.top_bar_title.setText("JWT Debugger")
            self.stacked_widget.setCurrentWidget(self.jwt_debugger_screen)
            logger.info("Switched to JWT Debugger view")
        elif tool_name == "RegExp Tester":
            self.top_bar_title.setText("RegExp Tester")
            self.stacked_widget.setCurrentWidget(self.regexp_tester_screen)
            logger.info("Switched to RegExp Tester view")
        elif tool_name == "URL Encode/Decode":
            self.top_bar_title.setText("URL Encode/Decode")
            self.stacked_widget.setCurrentWidget(self.url_codec_screen)
            logger.info("Switched to URL Encode/Decode view")
        elif tool_name == "UUID/ULID Generate/Decode":
            self.top_bar_title.setText("UUID/ULID Generate/Decode")
            self.stacked_widget.setCurrentWidget(self.uuid_ulid_generator_screen)
            logger.info("Switched to UUID/ULID Generate/Decode view")
        elif tool_name == "XML Beautifier":
            self.top_bar_title.setText("XML Beautifier")
            self.stacked_widget.setCurrentWidget(self.xml_formatter_screen)
            logger.info("Switched to XML Beautifier view")
        elif tool_name == "YAML to JSON":
            self.top_bar_title.setText("YAML to JSON")
            self.stacked_widget.setCurrentWidget(self.yaml_to_json_screen)
            logger.info("Switched to YAML to JSON view")
        elif tool_name == "String Case Converter":
            self.top_bar_title.setText("String Case Converter")
            self.stacked_widget.setCurrentWidget(self.string_case_converter_screen)
            logger.info("Switched to String Case Converter view")
        elif tool_name == "Color Converter":
            self.top_bar_title.setText("Color Converter")
            self.stacked_widget.setCurrentWidget(self.color_converter_screen)
            logger.info("Switched to Color Converter view")
        elif tool_name == "Lorem Ipsum Generator":
            self.top_bar_title.setText("Lorem Ipsum Generator")
            self.stacked_widget.setCurrentWidget(self.lorem_ipsum_generator_screen)
            logger.info("Switched to Lorem Ipsum Generator view")
        elif tool_name == "Markdown Viewer":
            self.top_bar_title.setText("Markdown Viewer")
            self.stacked_widget.setCurrentWidget(self.markdown_viewer_screen)
            logger.info("Switched to Markdown Viewer view")
        else:
            self.top_bar_title.setText("Work in Progress 🚧")
            self.stacked_widget.setCurrentWidget(self.welcome_screen)
            logger.info("Switched to welcome screen .. Tool not implemented")

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

    def _focus_first_visible_tool(self):
        """Focus on the first visible tool in the filtered results and switch to its view.

        This method is called when the user presses Enter in the search input.
        It finds the first tool item that is currently visible, selects it, and
        automatically triggers the tool selection to switch to the corresponding tool view.
        """
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            # Check if the item is visible (size hint height > 0)
            if item.sizeHint().height() > 0:
                # Set the current item and focus on it
                self.tool_list.setCurrentItem(item)
                self.tool_list.setFocus()
                # Trigger tool selection to switch to the tool view
                self._on_tool_selected(item)
                logger.info(f"Selected and switched to first visible tool: {item.data(Qt.ItemDataRole.UserRole)}")
                return

        logger.info("No visible tools found to focus on")

    def filter_tools(self, search_query: str):
        """Filter the tools list based on search query using visibility management.

        Args:
            search_query: The search string to filter tools by
        """
        logger.info(f"Filtering tools with query: '{search_query}'")

        # If the tool list is empty, populate it first
        if self.tool_list.count() == 0:
            self._populate_tool_list()

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

    def _populate_tool_list(self):
        """Populate the tool list with all available tools."""
        logger.info("Populating tool list with all tools")

        for icon_text, tool_name, _keywords in self.tools:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 36))
            item_widget = self._create_tool_item_widget(icon_text, tool_name)
            item.setData(Qt.ItemDataRole.UserRole, tool_name)
            self.tool_list.addItem(item)
            self.tool_list.setItemWidget(item, item_widget)

        logger.info(f"Tool list populated with {len(self.tools)} tools")

    def _apply_styles(self):
        logger.info("Applying application styles")
        self.setStyleSheet(get_main_app_style())
        logger.info("Application styles applied successfully")


def main():
    logger.info("Starting DevDriver application")
    app = QApplication(sys.argv)
    logger.info("QApplication created")

    font = QFont("Inter")  # A nice modern system font, falls back to default
    app.setFont(font)
    logger.info("Application font set to Inter")

    logger.info("Creating main window")
    window = DevDriverWindow()
    logger.info("Showing main window")
    window.show()

    logger.info("Starting application event loop")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
