import logging
import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
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
    create_random_string_tool_widget,
    create_regexp_tester_widget,
    create_scratch_pad_widget,
    create_string_case_converter_widget,
    create_unix_time_converter_widget,
    create_url_codec_widget,
    create_uuid_ulid_tool_widget,
    create_xml_formatter_widget,
    create_yaml_to_json_widget,
)
from .tools_search import NavigableToolsList, ToolsSearch

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

        # Create scratch pad widget
        self.scratch_pad_widget = create_scratch_pad_widget(self.style)
        self.scratch_pad_dock = QDockWidget("Scratch Pad", self)
        self.scratch_pad_dock.setWidget(self.scratch_pad_widget)
        self.scratch_pad_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.scratch_pad_dock)
        self.scratch_pad_dock.hide()  # Initially hidden

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

        # Initialize search functionality after sidebar is created
        self.tools_search = ToolsSearch(self.tool_list, self.search_results_label, self.tools)
        logger.info("Tools search functionality initialized")

        # Set clear search callback for tools list
        self.tool_list.set_clear_search_callback(self.clear_search)
        logger.info("Clear search callback set for tools list")

        # Connect search functionality after tools_search is initialized
        self.search_input.textChanged.connect(self.tools_search.on_search_text_changed)
        logger.info("Search input textChanged signal connected to tools_search.on_search_text_changed")

        self.search_input.returnPressed.connect(
            lambda: self.tools_search.focus_first_visible_tool(self._on_tool_selected)
        )
        logger.info("Search input returnPressed signal connected to tools_search.focus_first_visible_tool")

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

        # Create shortcut for focusing tool list (Cmd+Shift+T on macOS, Ctrl+Shift+T on other platforms)
        tools_shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        tools_shortcut.activated.connect(self._focus_tool_list)
        logger.info("Tool list focus shortcut (Ctrl+Shift+T) created")

        # Create shortcut for toggling scratch pad (Cmd+Shift+S on macOS, Ctrl+Shift+S on other platforms)
        scratch_pad_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        scratch_pad_shortcut.activated.connect(self.toggle_scratch_pad)
        logger.info("Scratch pad toggle shortcut (Ctrl+Shift+S) created")

        # On macOS, also add the Cmd variants
        if sys.platform == "darwin":
            search_shortcut_mac = QShortcut(QKeySequence("Cmd+Shift+F"), self)
            search_shortcut_mac.activated.connect(self._focus_search_input)
            logger.info("Search focus shortcut (Cmd+Shift+F) created for macOS")

            tools_shortcut_mac = QShortcut(QKeySequence("Cmd+Shift+T"), self)
            tools_shortcut_mac.activated.connect(self._focus_tool_list)
            logger.info("Tool list focus shortcut (Cmd+Shift+T) created for macOS")

            scratch_pad_shortcut_mac = QShortcut(QKeySequence("Cmd+Shift+S"), self)
            scratch_pad_shortcut_mac.activated.connect(self.toggle_scratch_pad)
            logger.info("Scratch pad toggle shortcut (Cmd+Shift+S) created for macOS")

    def _focus_search_input(self):
        """Focus the search input and select all text."""
        logger.info("Focusing search input via keyboard shortcut")
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _focus_tool_list(self):
        """Focus the tool list for keyboard navigation."""
        logger.info("Focusing tool list via keyboard shortcut")
        self.tools_search.focus_tool_list()

    def _search_input_key_press_event(self, event):
        """Handle key press events for the search input, including Escape to clear."""
        if event.key() == Qt.Key.Key_Escape:
            logger.info("Escape key pressed in search input - clearing search")
            self.clear_search()
        else:
            # Call the original keyPressEvent for other keys
            QLineEdit.keyPressEvent(self.search_input, event)

    def clear_search(self):
        """Clear the search input and reset the tool list to show all tools."""
        logger.info("Clearing search input")
        self.search_input.clear()
        self.search_input.setFocus()
        # The textChanged signal will automatically trigger the search update
        # which will show all tools when the search is empty

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
        self.search_input.setPlaceholderText("Search...   ⌘⇧F | ESC to clear")
        self.search_input.setFixedHeight(38)
        logger.info("Search input field created")

        # Add Escape key handling to clear search
        self.search_input.keyPressEvent = self._search_input_key_press_event
        logger.info("Search input key press event handler set")

        # Note: Search input connections are made after tools_search initialization

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

        self.tool_list = NavigableToolsList()
        self.tool_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tool_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        logger.info("Navigable tool list widget created")

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
            ("🎲", "Random String Generator", "random string generator password characters"),
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

        # Add scratch pad toggle button
        self.scratch_pad_toggle_button = QPushButton("📝 Scratch Pad")
        self.scratch_pad_toggle_button.setCheckable(True)
        self.scratch_pad_toggle_button.clicked.connect(self.toggle_scratch_pad)
        self.scratch_pad_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:checked {
                background-color: #dcdcdc;
            }
        """)

        top_bar_layout.addWidget(self.top_bar_title)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.scratch_pad_toggle_button)

        # Stacked widget for different tool views
        self.stacked_widget = QStackedWidget()
        logger.info("Stacked widget created for tool views")

        logger.info("Creating welcome screen")
        self.welcome_screen = self._create_welcome_screen()
        logger.info("Creating Unix Time Converter screen")
        self.unix_time_converter_screen = create_unix_time_converter_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating JSON Format/Validate screen")
        self.json_format_validate_screen = create_json_formatter_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Base64 String Encode/Decode screen")
        self.base64_string_encodec_screen = create_base64_string_encodec_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating JWT Debugger screen")
        self.jwt_debugger_screen = create_jwt_debugger_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating RegExp Tester screen")
        self.regexp_tester_screen = create_regexp_tester_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating URL Encode Decode screen")
        self.url_codec_screen = create_url_codec_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating UUID/ULID Generate/Decode screen")
        self.uuid_ulid_generator_screen = create_uuid_ulid_tool_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating XML Beautifier screen")
        self.xml_formatter_screen = create_xml_formatter_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating YAML to JSON screen")
        self.yaml_to_json_screen = create_yaml_to_json_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating String Case Converter screen")
        self.string_case_converter_screen = create_string_case_converter_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Color Converter screen")
        self.color_converter_screen = create_color_converter_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Lorem Ipsum Generator screen")
        self.lorem_ipsum_generator_screen = create_lorem_ipsum_tool_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Markdown Viewer screen")
        self.markdown_viewer_screen = create_markdown_preview_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Random String Generator screen")
        self.random_string_generator_screen = create_random_string_tool_widget(self.style, self.scratch_pad_widget)

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
        self.stacked_widget.addWidget(self.random_string_generator_screen)

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
        elif tool_name == "Random String Generator":
            self.top_bar_title.setText("Random String Generator")
            self.stacked_widget.setCurrentWidget(self.random_string_generator_screen)
            logger.info("Switched to Random String Generator view")
        else:
            self.top_bar_title.setText("Work in Progress 🚧")
            self.stacked_widget.setCurrentWidget(self.welcome_screen)
            logger.info("Switched to welcome screen .. Tool not implemented")

    def _apply_styles(self):
        logger.info("Applying application styles")
        self.setStyleSheet(get_main_app_style())
        logger.info("Application styles applied successfully")

    def toggle_scratch_pad(self):
        """
        Toggle the visibility of the scratch pad dock widget.
        """
        if self.scratch_pad_dock.isVisible():
            self.scratch_pad_dock.hide()
            self.scratch_pad_toggle_button.setChecked(False)
        else:
            self.scratch_pad_dock.show()
            self.scratch_pad_toggle_button.setChecked(True)

    def send_to_scratch_pad(self, content):
        """
        Send content to the scratch pad.

        Args:
            content (str): The content to send to the scratch pad.
        """
        if self.scratch_pad_widget and content:
            # Ensure the scratch pad is visible
            if not self.scratch_pad_dock.isVisible():
                self.scratch_pad_dock.show()
                self.scratch_pad_toggle_button.setChecked(True)

            # Append content to the scratch pad with a separator
            current_content = self.scratch_pad_widget.get_content()
            new_content = f"{current_content}\n\n---\n{content}" if current_content else content
            self.scratch_pad_widget.set_content(new_content)


def main():
    logger.info("Starting DevDriver application")
    app = QApplication(sys.argv)
    logger.info("QApplication created")

    # Use system default font to avoid font loading overhead
    font = QFont()  # Uses system default font
    app.setFont(font)
    logger.info("Application font set to system default")

    logger.info("Creating main window")
    window = DevDriverWindow()
    logger.info("Showing main window")
    window.show()

    logger.info("Starting application event loop")
    sys.exit(app.exec())
