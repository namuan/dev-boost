import logging
import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont
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

from .tools import (
    create_base64_string_encodec_widget,
    create_color_converter_widget,
    create_json_formatter_widget,
    create_jwt_debugger_widget,
    create_regexp_tester_widget,
    create_string_case_converter_widget,
    create_unix_time_converter_widget,
    create_url_codec_widget,
    create_uuid_ulid_tool_widget,
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
        logger.info("DevDriverWindow initialization completed successfully")

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
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search...   ⌘⇧F")
        search_input.setFixedHeight(38)
        logger.info("Search input field created")

        search_layout.addWidget(search_input)

        self.tool_list = QListWidget()
        self.tool_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tool_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        logger.info("Tool list widget created")

        self.tools = [
            ("🕒", "Unix Time Converter"),
            ("{}", "JSON Format/Validate"),
            ("64", "Base64 String Encode/Decode"),
            ("✴️", "JWT Debugger"),
            ("✳️", "RegExp Tester"),
            ("%", "URL Encode/Decode"),
            ("🆔", "UUID/ULID Generate/Decode"),
            ("⇄", "YAML to JSON"),
            ("✏️", "String Case Converter"),
            ("🎨", "Color Converter"),
        ]
        logger.info(f"Defined {len(self.tools)} tools for the sidebar")

        for icon_text, tool_name in self.tools:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 32))
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
        logger.info("Creating YAML to JSON screen")
        self.yaml_to_json_screen = create_yaml_to_json_widget(self.style)
        logger.info("Creating String Case Converter screen")
        self.string_case_converter_screen = create_string_case_converter_widget(self.style)
        logger.info("Creating Color Converter screen")
        self.color_converter_screen = create_color_converter_widget()

        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.unix_time_converter_screen)
        self.stacked_widget.addWidget(self.json_format_validate_screen)
        self.stacked_widget.addWidget(self.base64_string_encodec_screen)
        self.stacked_widget.addWidget(self.jwt_debugger_screen)
        self.stacked_widget.addWidget(self.regexp_tester_screen)
        self.stacked_widget.addWidget(self.url_codec_screen)
        self.stacked_widget.addWidget(self.uuid_ulid_generator_screen)
        self.stacked_widget.addWidget(self.yaml_to_json_screen)
        self.stacked_widget.addWidget(self.string_case_converter_screen)
        self.stacked_widget.addWidget(self.color_converter_screen)

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
        else:
            self.top_bar_title.setText("Work in Progress 🚧")
            self.stacked_widget.setCurrentWidget(self.welcome_screen)
            logger.info("Switched to welcome screen .. Tool not implemented")

    def _apply_styles(self):
        logger.info("Applying application styles")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E8E8E8;
            }
            #sidebar {
                background-color: #E8E8E8;
                border-right: 1px solid #DCDCDC;
            }
            #contentArea {
                background-color: #F3F3F3;
            }
            #topBar {
                background-color: #E8E8E8;
                border-bottom: 1px solid #DCDCDC;
            }
            #topBarTitle {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }

            /* Welcome Screen Specific */
            #appName {
                font-size: 28px;
                font-weight: bold;
                color: #333;
            }
            #infoLabel {
                font-size: 14px;
                color: #757575;
            }

            /* General Sidebar styles */
            #sidebar QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
                color: #555;
            }
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item { border-radius: 5px; padding: 4px; }
            QListWidget::item:hover { background-color: #DCDCDC; }
            QListWidget::item:selected { background-color: #C9C9C9; color: black;}
            #toolIcon { font-size: 15px; color: #333; }
            #toolText { font-size: 14px; color: #212121; }
            #feedbackButton {
                background-color: #D8D8D8; border: 1px solid #C0C0C0; border-radius: 6px;
                font-size: 13px; text-align: left; padding-left: 10px;
            }
            #feedbackButton:hover { background-color: #C8C8C8; }

            /* Unix Time Converter styles */
            QWidget {
                color: #212121;
                font-size: 13px;
            }
            #tipsLabel {
                color: #888;
                font-size: 12px;
            }
            QFrame[frameShape="4"] { /* HLine */
                border: none;
                border-top: 1px solid #DCDCDC;
            }
            QLineEdit, QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #C6C6C6;
                border-radius: 4px;
                padding: 5px;
                min-height: 24px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                /* Blue circle with up/down arrows */
                image: url(placeholder.png); /* Placeholder for custom arrow */
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background-color: #FDFDFD;
                border: 1px solid #C6C6C6;
                border-radius: 4px;
                padding: 5px 12px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
            #iconButton {
                border: none;
                background-color: transparent;
                padding: 4px;
                min-height: 0px;
            }
            #iconButton QAbstractButton::icon {
                color: black; /* This won't work, standard icons are pixmaps */
            }

        """)
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
