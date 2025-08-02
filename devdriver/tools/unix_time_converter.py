from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)


def create_unix_time_converter_widget(style_func):
    """Create and return the Unix Time Converter widget.

    Args:
        style_func: Function to get QStyle for standard icons

    Returns:
        QWidget: The complete Unix Time Converter widget
    """
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
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
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
        copy_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))  # Placeholder
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
