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

from devboost.config import get_config, set_config
from devboost.tools.file_rename import create_file_rename_widget

from .styles import get_main_app_style
from .tools import (
    create_base64_string_encodec_widget,
    create_color_converter_widget,
    create_cron_expression_editor_widget,
    create_file_optimization_widget,
    create_graphql_client_widget,
    create_http_client_widget,
    create_image_optimizer_widget,
    create_ip_subnet_calculator_widget,
    create_json_formatter_widget,
    create_jwt_debugger_widget,
    create_llm_client_widget,
    create_lorem_ipsum_tool_widget,
    create_markdown_preview_widget,
    create_openapi_mock_server_widget,
    create_random_string_tool_widget,
    create_regexp_tester_widget,
    create_scratch_pad_widget,
    create_string_case_converter_widget,
    create_timezone_converter_widget,
    create_unit_converter_widget,
    create_unix_time_converter_widget,
    create_url_codec_widget,
    create_uuid_ulid_tool_widget,
    create_uvx_runner_widget,
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
        # Set a larger default width for the scratch pad dock using resizeDocks
        self.resizeDocks([self.scratch_pad_dock], [400], Qt.Orientation.Horizontal)
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

        # Load last opened tool or show welcome screen
        self._load_last_opened_tool()
        logger.info("Last opened tool loaded or welcome screen displayed")

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
            ("⏰", "Cron Expression Editor", "cron expression schedule job task automation time"),
            ("📝", "Lorem Ipsum Generator", "lorem ipsum text placeholder dummy"),
            ("📋", "Markdown Viewer", "markdown preview render view md"),
            ("🗜️", "Image Optimizer", "image optimize compression quality reduce size"),
            ("🗂️", "File Optimization Tool", "file optimize compression pdf image video batch drag drop"),
            ("🌐", "IP Subnet Calculator", "ip subnet calculator cidr network ipv4 ipv6 subnetting"),
            ("🎲", "Random String Generator", "random string generator password characters"),
            ("🌍", "TimeZone Converter", "timezone time zone convert world clock city time"),
            ("📐", "Unit Converter", "unit convert measurement length weight temperature volume"),
            ("📁", "File Rename Tool", "file rename batch slugify transliterate numbering date pattern"),
            ("🌐", "HTTP Client", "http client request api rest get post put delete"),
            ("🔗", "GraphQL Client", "graphql client query mutation subscription schema introspection"),
            ("🤖", "LLM Client", "llm client ai chat openai anthropic google model"),
            ("📦", "Uvx Runner", "uvx tools runner install execute command line utilities"),
            ("🎭", "OpenAPI Mock Server", "openapi mock server api swagger spec endpoint response"),
        ]
        logger.info("Defined %d tools for the sidebar", len(self.tools))

        for icon_text, tool_name, _keywords in self.tools:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 36))
            item_widget = self._create_tool_item_widget(icon_text, tool_name)
            item.setData(Qt.ItemDataRole.UserRole, tool_name)
            self.tool_list.addItem(item)
            self.tool_list.setItemWidget(item, item_widget)
        logger.info("Populated tool list with %d items", len(self.tools))

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
        logger.info("Creating Cron Expression Editor screen")
        self.cron_expression_editor_screen = create_cron_expression_editor_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Lorem Ipsum Generator screen")
        self.lorem_ipsum_generator_screen = create_lorem_ipsum_tool_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Markdown Viewer screen")
        self.markdown_viewer_screen = create_markdown_preview_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Random String Generator screen")
        self.random_string_generator_screen = create_random_string_tool_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating TimeZone Converter screen")
        self.timezone_converter_screen = create_timezone_converter_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Unit Converter screen")
        self.unit_converter_screen = create_unit_converter_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating File Rename Tool screen")
        self.file_rename_tool_screen = create_file_rename_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Image Optimizer screen")
        self.image_optimizer_screen = create_image_optimizer_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating IP Subnet Calculator screen")
        self.ip_subnet_calculator_screen = create_ip_subnet_calculator_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating HTTP Client screen")
        self.http_client_screen = create_http_client_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating GraphQL Client screen")
        self.graphql_client_screen = create_graphql_client_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating Uvx Runner screen")
        self.uvx_runner_screen = create_uvx_runner_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating LLM Client screen")
        self.llm_client_screen = create_llm_client_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating File Optimization Tool screen")
        self.file_optimization_tool_screen = create_file_optimization_widget(self.style, self.scratch_pad_widget)
        logger.info("Creating OpenAPI Mock Server screen")
        self.openapi_mock_server_screen = create_openapi_mock_server_widget(self.style, self.scratch_pad_widget)

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
        self.stacked_widget.addWidget(self.cron_expression_editor_screen)
        self.stacked_widget.addWidget(self.lorem_ipsum_generator_screen)
        self.stacked_widget.addWidget(self.markdown_viewer_screen)
        self.stacked_widget.addWidget(self.random_string_generator_screen)
        self.stacked_widget.addWidget(self.timezone_converter_screen)
        self.stacked_widget.addWidget(self.unit_converter_screen)
        self.stacked_widget.addWidget(self.file_rename_tool_screen)
        self.stacked_widget.addWidget(self.image_optimizer_screen)
        self.stacked_widget.addWidget(self.ip_subnet_calculator_screen)
        self.stacked_widget.addWidget(self.http_client_screen)
        self.stacked_widget.addWidget(self.graphql_client_screen)
        self.stacked_widget.addWidget(self.llm_client_screen)
        self.stacked_widget.addWidget(self.uvx_runner_screen)
        self.stacked_widget.addWidget(self.file_optimization_tool_screen)
        self.stacked_widget.addWidget(self.openapi_mock_server_screen)

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

    def _on_tool_selected(self, item):
        """Handle tool selection from the sidebar."""
        tool_name = item.data(Qt.ItemDataRole.UserRole)
        logger.info("Tool selected: %s", tool_name)

        # Map tool names to their corresponding widgets
        tool_widgets = {
            "Unix Time Converter": self.unix_time_converter_screen,
            "JSON Format/Validate": self.json_format_validate_screen,
            "Base64 String Encode/Decode": self.base64_string_encodec_screen,
            "JWT Debugger": self.jwt_debugger_screen,
            "RegExp Tester": self.regexp_tester_screen,
            "URL Encode/Decode": self.url_codec_screen,
            "UUID/ULID Generate/Decode": self.uuid_ulid_generator_screen,
            "XML Beautifier": self.xml_formatter_screen,
            "YAML to JSON": self.yaml_to_json_screen,
            "String Case Converter": self.string_case_converter_screen,
            "Color Converter": self.color_converter_screen,
            "Cron Expression Editor": self.cron_expression_editor_screen,
            "Lorem Ipsum Generator": self.lorem_ipsum_generator_screen,
            "Markdown Viewer": self.markdown_viewer_screen,
            "Random String Generator": self.random_string_generator_screen,
            "TimeZone Converter": self.timezone_converter_screen,
            "Unit Converter": self.unit_converter_screen,
            "File Rename Tool": self.file_rename_tool_screen,
            "Image Optimizer": self.image_optimizer_screen,
            "File Optimization Tool": self.file_optimization_tool_screen,
            "IP Subnet Calculator": self.ip_subnet_calculator_screen,
            "HTTP Client": self.http_client_screen,
            "GraphQL Client": self.graphql_client_screen,
            "Uvx Runner": self.uvx_runner_screen,
            "LLM Client": self.llm_client_screen,
            "OpenAPI Mock Server": self.openapi_mock_server_screen,
        }

        self._switch_to_tool(tool_name, tool_widgets)

    def _switch_to_tool(self, tool_name: str, tool_widgets: dict):
        """Switch to the selected tool widget."""
        widget = tool_widgets.get(tool_name)

        if widget:
            self.top_bar_title.setText(tool_name)
            self.stacked_widget.setCurrentWidget(widget)
            # Save the last opened tool to configuration
            set_config("global.last_used_tool", tool_name)
            logger.info("Switched to %s view and saved to config", tool_name)
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

    def _load_last_opened_tool(self):
        """Load the last opened tool from configuration or show welcome screen."""
        last_tool = get_config("global.last_used_tool", "")
        logger.info("Loading last opened tool from config: '%s'", last_tool)

        if last_tool:
            # Map tool names to their corresponding widgets
            tool_widgets = {
                "Unix Time Converter": self.unix_time_converter_screen,
                "JSON Format/Validate": self.json_format_validate_screen,
                "Base64 String Encode/Decode": self.base64_string_encodec_screen,
                "JWT Debugger": self.jwt_debugger_screen,
                "RegExp Tester": self.regexp_tester_screen,
                "URL Encode/Decode": self.url_codec_screen,
                "UUID/ULID Generate/Decode": self.uuid_ulid_generator_screen,
                "XML Beautifier": self.xml_formatter_screen,
                "YAML to JSON": self.yaml_to_json_screen,
                "String Case Converter": self.string_case_converter_screen,
                "Color Converter": self.color_converter_screen,
                "Cron Expression Editor": self.cron_expression_editor_screen,
                "Lorem Ipsum Generator": self.lorem_ipsum_generator_screen,
                "Markdown Viewer": self.markdown_viewer_screen,
                "Random String Generator": self.random_string_generator_screen,
                "TimeZone Converter": self.timezone_converter_screen,
                "Unit Converter": self.unit_converter_screen,
                "File Rename Tool": self.file_rename_tool_screen,
                "Image Optimizer": self.image_optimizer_screen,
                "File Optimization Tool": self.file_optimization_tool_screen,
                "IP Subnet Calculator": self.ip_subnet_calculator_screen,
                "HTTP Client": self.http_client_screen,
                "GraphQL Client": self.graphql_client_screen,
                "Uvx Runner": self.uvx_runner_screen,
                "LLM Client": self.llm_client_screen,
                "OpenAPI Mock Server": self.openapi_mock_server_screen,
            }

            widget = tool_widgets.get(last_tool)
            if widget:
                self.top_bar_title.setText(last_tool)
                self.stacked_widget.setCurrentWidget(widget)

                # Also select the corresponding item in the tool list
                for i in range(self.tool_list.count()):
                    item = self.tool_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == last_tool:
                        self.tool_list.setCurrentItem(item)
                        break

                logger.info("Successfully loaded last opened tool: %s", last_tool)
            else:
                logger.info("Last opened tool '%s' not found, showing welcome screen", last_tool)
                self._show_welcome_screen()
        else:
            logger.info("No last opened tool found, showing welcome screen")
            self._show_welcome_screen()

    def _show_welcome_screen(self):
        """Show the welcome screen."""
        self.top_bar_title.setText("")
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        self.tool_list.clearSelection()


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
