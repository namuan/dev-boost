import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class DevDriverWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dev Driver")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(950, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar_widget = self._create_sidebar()
        self.content_widget = self._create_content_area()

        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.content_widget)

        self._apply_styles()

        self.tool_list.itemClicked.connect(self._on_tool_selected)

    def _create_sidebar(self):
        sidebar_container = QWidget()
        sidebar_container.setObjectName("sidebar")
        sidebar_container.setFixedWidth(300)

        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)

        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search...   ⌘⇧F")
        search_input.setFixedHeight(38)

        search_layout.addWidget(search_input)

        self.tool_list = QListWidget()
        self.tool_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tool_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.tools = [
            ("🕒", "Unix Time Converter"),
            ("{}", "JSON Format/Validate"),
            ("64", "Base64 String Encode/Decode"),
            ("🖼️", "Base64 Image Encode/Decode"),
            ("✴️", "JWT Debugger"),
            ("✳️", "RegExp Tester"),
            ("%", "URL Encode/Decode"),
            ("&", "URL Parser"),
            ("#;", "HTML Entity Encode/Decode"),
            ("\\n", "Backslash Escape/Unescape"),
            ("🆔", "UUID/ULID Generate/Decode"),
            ("</>", "HTML Preview"),
            ("±", "Text Diff Checker"),
            ("⇄", "YAML to JSON"),
            ("⇄", "JSON to YAML"),
            ("¹⁰₁", "Number Base Converter"),
            ("✨", "HTML Beautify/Minify"),
            ("✨", "CSS Beautify/Minify"),
            ("✨", "JS Beautify/Minify"),
            ("✨", "ERB Beautify/Minify"),
            ("✨", "LESS Beautify/Minify"),
            ("✨", "SCSS Beautify/Minify"),
            ("✨", "XML Beautify/Minify"),
            ("IP", "Lorem Ipsum Generator"),
            ("🔲", "QR Code Reader/Generator"),
            ("Aa", "String Inspector"),
            ("⇄", "JSON to CSV"),
            ("⇄", "CSV to JSON"),
            ("🔑", "Hash Generator"),
            ("⇄", "HTML to JSX"),
            ("M↓", "Markdown Preview"),
            ("✨", "SQL Formatter"),
            ("✏️", "String Case Converter"),
            ("🗓️", "Cron Job Parser"),
            ("🎨", "Color Converter"),
            ("⇄", "PHP to JSON"),
        ]

        for icon_text, tool_name in self.tools:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 32))
            item_widget = self._create_tool_item_widget(icon_text, tool_name)
            item.setData(Qt.ItemDataRole.UserRole, tool_name)
            self.tool_list.addItem(item)
            self.tool_list.setItemWidget(item, item_widget)

        sidebar_layout.addWidget(search_container)
        sidebar_layout.addWidget(self.tool_list)

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
        content_container = QWidget()
        content_container.setObjectName("contentArea")

        main_content_layout = QVBoxLayout(content_container)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)

        # Top bar
        self.top_bar = QWidget()
        self.top_bar.setObjectName("topBar")
        self.top_bar.setFixedHeight(44)
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(15, 0, 15, 0)

        self.top_bar_title = QLabel("Dev Driver")
        self.top_bar_title.setObjectName("topBarTitle")

        top_bar_layout.addWidget(self.top_bar_title)
        top_bar_layout.addStretch()

        # Stacked widget for different tool views
        self.stacked_widget = QStackedWidget()
        self.welcome_screen = self._create_welcome_screen()
        self.unix_time_converter_screen = self._create_unix_time_converter_widget()

        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.unix_time_converter_screen)

        main_content_layout.addWidget(self.top_bar)
        main_content_layout.addWidget(self.stacked_widget)

        return content_container

    def _create_welcome_screen(self):
        center_stage = QWidget()
        center_layout = QVBoxLayout(center_stage)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        v_box = QVBoxLayout()
        v_box.setSpacing(15)
        v_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Image Description: A flat-style application icon. It's a slightly rounded pentagon with a vertical orientation.
        # The color of the pentagon is a solid green, hex code approximately #2ECC71.
        # Inside the pentagon, there are two symbols: a less-than sign '<' and a greater-than sign '>'
        # combined to look like code brackets '</>'. The symbols are white.
        app_icon_label = QLabel()
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.moveTo(50, 5)
        path.lineTo(95, 35)
        path.lineTo(80, 95)
        path.lineTo(20, 95)
        path.lineTo(5, 35)
        path.closeSubpath()
        painter.fillPath(path, QBrush(QColor("#2ECC71")))
        font = QFont("Menlo", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "</>")
        painter.end()
        app_icon_label.setPixmap(pixmap)
        app_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_name_label = QLabel("Dev Driver")
        app_name_label.setObjectName("appName")
        app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        v_box.addWidget(app_icon_label)
        v_box.addWidget(app_name_label)
        v_box.addSpacing(20)

        center_layout.addLayout(v_box)
        return center_stage

    def _create_unix_time_converter_widget(self):
        converter_widget = QWidget()
        main_layout = QVBoxLayout(converter_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Input Section ---
        input_section_layout = QVBoxLayout()
        input_section_layout.setSpacing(8)

        top_controls_layout = QHBoxLayout()
        top_controls_layout.setSpacing(8)

        top_controls_layout.addWidget(QLabel("Input:"))
        top_controls_layout.addWidget(QPushButton("Now"))
        top_controls_layout.addWidget(QPushButton("Clipboard"))
        top_controls_layout.addWidget(QPushButton("Clear"))
        top_controls_layout.addStretch()

        settings_button = QPushButton()
        settings_button.setObjectName("iconButton")
        # Image description: A gear icon for settings. Black, simple cogwheel shape.
        settings_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        top_controls_layout.addWidget(settings_button)

        input_fields_layout = QHBoxLayout()
        input_fields_layout.setSpacing(8)

        input_line_edit = QLineEdit()

        time_unit_combo = QComboBox()
        time_unit_combo.addItem("Unix time (seconds since epoch)")
        time_unit_combo.setFixedWidth(250)

        input_fields_layout.addWidget(input_line_edit)
        input_fields_layout.addWidget(time_unit_combo)

        tips_label = QLabel("Tips: Mathematical operators + - * / are supported")
        tips_label.setObjectName("tipsLabel")

        input_section_layout.addLayout(top_controls_layout)
        input_section_layout.addLayout(input_fields_layout)
        input_section_layout.addWidget(tips_label)

        main_layout.addLayout(input_section_layout)

        # --- Separator ---
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator1)

        # --- Results Section ---
        results_grid = QGridLayout()
        results_grid.setSpacing(15)

        # Helper to create an output field with a copy button
        def create_output_field():
            field_widget = QWidget()
            field_layout = QHBoxLayout(field_widget)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(4)
            field_layout.addWidget(QLineEdit())
            copy_button = QPushButton()
            copy_button.setObjectName("iconButton")
            # Image description: A copy icon. Two overlapping squares. Black outlines.
            copy_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))  # Placeholder
            field_layout.addWidget(copy_button)
            return field_widget

        # Grid items
        results_grid.addWidget(QLabel("Local:"), 0, 0)
        results_grid.addWidget(create_output_field(), 0, 1)
        results_grid.addWidget(QLabel("Day of year"), 0, 2)
        results_grid.addWidget(create_output_field(), 0, 3)
        results_grid.addWidget(QLabel("Other formats (local)"), 0, 4)
        results_grid.addWidget(create_output_field(), 0, 5)

        results_grid.addWidget(QLabel("UTC (ISO 8601):"), 1, 0)
        results_grid.addWidget(create_output_field(), 1, 1)
        results_grid.addWidget(QLabel("Week of year"), 1, 2)
        results_grid.addWidget(create_output_field(), 1, 3)
        results_grid.addWidget(create_output_field(), 1, 5)

        results_grid.addWidget(QLabel("Relative:"), 2, 0)
        results_grid.addWidget(create_output_field(), 2, 1)
        results_grid.addWidget(QLabel("Is leap year?"), 2, 2)
        results_grid.addWidget(create_output_field(), 2, 3)
        results_grid.addWidget(create_output_field(), 2, 5)

        results_grid.addWidget(QLabel("Unix time:"), 3, 0)
        results_grid.addWidget(create_output_field(), 3, 1)
        results_grid.addWidget(create_output_field(), 3, 5)

        results_grid.setColumnStretch(1, 1)
        results_grid.setColumnStretch(3, 1)
        results_grid.setColumnStretch(5, 1)

        main_layout.addLayout(results_grid)

        # --- Separator ---
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator2)

        # --- Timezone Section ---
        timezone_section_layout = QVBoxLayout()
        timezone_section_layout.setSpacing(8)

        timezone_controls_layout = QHBoxLayout()
        timezone_controls_layout.setSpacing(8)

        timezone_controls_layout.addWidget(QLabel("Other timezones:"))
        tz_combo = QComboBox()
        tz_combo.setEditable(True)
        tz_combo.lineEdit().setPlaceholderText("Add timezone...")
        timezone_controls_layout.addWidget(tz_combo, 1)
        timezone_controls_layout.addWidget(QPushButton("Add"))

        timezone_section_layout.addLayout(timezone_controls_layout)

        tz_info_label = QLabel("(Pick a timezone to get started...)")
        tz_info_label.setObjectName("tipsLabel")
        timezone_section_layout.addWidget(tz_info_label)

        main_layout.addLayout(timezone_section_layout)

        main_layout.addStretch()  # Push everything up

        return converter_widget

    def _on_tool_selected(self, item):
        tool_name = item.data(Qt.ItemDataRole.UserRole)
        if tool_name == "Unix Time Converter":
            self.top_bar_title.setText("Unix Time Converter")
            self.stacked_widget.setCurrentWidget(self.unix_time_converter_screen)
        else:
            # You can add logic for other tools here
            self.top_bar_title.setText("Dev Driver")
            self.stacked_widget.setCurrentWidget(self.welcome_screen)

    def _apply_styles(self):
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


def main():
    app = QApplication(sys.argv)
    font = QFont("Inter")  # A nice modern system font, falls back to default
    app.setFont(font)
    window = DevDriverWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
