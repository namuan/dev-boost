"""
Desktop File Optimization Tool for DevBoost.

This tool provides comprehensive file optimization capabilities for images, videos, and PDFs
with an intuitive drag-and-drop interface, real-time feedback, and seamless desktop integration.
"""

import logging
import shutil
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent as QDragEnterEvent
from PyQt6.QtGui import QDropEvent as QDropEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import COLORS, get_status_style, get_tool_style

from .detector import FileTypeDetector as FileTypeDetector
from .file_manager import FileManager
from .images import ImageOptimizationEngine
from .manager import OptimizationManager
from .models import BatchOperationResult, BatchProgress, FileInfo
from .pdfs import PDFOptimizationEngine
from .settings import OptimizationPreset, OptimizationSettings, QualityPreset, SettingsManager
from .ui.file_drop_area import FileDropArea
from .ui.results_dialog import OptimizationResultsDialog
from .videos import VideoOptimizationEngine

logger = logging.getLogger(__name__)


# Convenience wrapper functions for backward compatibility and simple usage.
def optimize_image(input_path: Path | str, output_path: Path | str, settings: "OptimizationSettings") -> dict[str, Any]:
    engine = ImageOptimizationEngine()
    in_path = Path(input_path)
    out_path = Path(output_path)
    return engine.optimize_image(in_path, out_path, settings)


def optimize_video(input_path: Path | str, output_path: Path | str, settings: "OptimizationSettings") -> dict[str, Any]:
    engine = VideoOptimizationEngine()
    in_path = Path(input_path)
    out_path = Path(output_path)
    return engine.optimize_video(in_path, out_path, settings)


def optimize_pdf(input_path: Path | str, output_path: Path | str, settings: "OptimizationSettings") -> dict[str, Any]:
    engine = PDFOptimizationEngine()
    in_path = Path(input_path)
    out_path = Path(output_path)
    return engine.optimize_pdf(in_path, out_path, settings)


class FileOptimizationWidget(QWidget):
    """
    Main file optimization widget following DevBoost patterns.
    """

    def __init__(self, style_func, scratch_pad=None):
        super().__init__()
        self.style_func = style_func
        self.scratch_pad = scratch_pad
        self.file_manager = FileManager()
        self.settings_manager = SettingsManager()
        self.current_files: list[FileInfo] = []
        self.resize_percentage = None  # For percentage-based scaling
        self.batch_progress = None  # Store current batch progress for results dialog

        # Initialize optimization engines
        self.image_engine = ImageOptimizationEngine()
        self.video_engine = VideoOptimizationEngine()
        self.pdf_engine = PDFOptimizationEngine()

        # Initialize optimization manager
        self.optimization_manager = OptimizationManager()
        self.optimization_manager.initialize_engines()

        # Connect optimization manager signals
        self.optimization_manager.progress_updated.connect(self._on_batch_progress_updated)
        self.optimization_manager.file_started.connect(self._on_file_started)
        self.optimization_manager.file_completed.connect(self._on_file_completed)
        self.optimization_manager.batch_completed.connect(self._on_batch_completed)
        self.optimization_manager.error_occurred.connect(self._on_optimization_error)

        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI layout."""
        self.setStyleSheet(get_tool_style())

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # --- Left Pane (File Input and Preview) ---
        left_pane = self._create_left_pane()
        splitter.addWidget(left_pane)

        # --- Right Pane (Controls and Settings) ---
        right_pane = self._create_right_pane()
        splitter.addWidget(right_pane)

        # Set initial splitter sizes
        splitter.setSizes([500, 300])

        # --- Bottom Status Bar ---
        self.status_bar = self._create_status_bar()
        main_layout.addWidget(self.status_bar)

        # Initialize status
        self.update_status("Ready - Drop files or click Browse to get started")

        # Initialize UI from current settings
        self._update_ui_from_settings()

    def _create_left_pane(self) -> QWidget:
        """Create the left pane with file drop area and preview."""
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(10, 10, 5, 10)
        left_layout.setSpacing(10)

        # File drop area - Fixed at top
        self.drop_area = FileDropArea()
        self.drop_area.handle_files_dropped = self.handle_files_dropped
        self.drop_area.browse_button.clicked.connect(self.browse_files)

        # Set fixed size policy for drop area to prevent it from expanding
        self.drop_area.setMinimumHeight(200)
        self.drop_area.setMaximumHeight(200)
        self.drop_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Add drop area with no stretch factor (0) to keep it fixed at top
        left_layout.addWidget(self.drop_area, 0)

        # Note: URL/Base64 paste input has been removed; only drag-and-drop or Browse are supported.

        # File list area (for batch processing) - Takes remaining space
        self.file_list_frame = QFrame()
        self.file_list_frame.setFrameShape(QFrame.Shape.NoFrame)  # Hide outline
        self.file_list_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["bg_primary"]};
                border: none;
                border-radius: 6px;
            }}
        """)

        # Set expanding size policy for file list to take remaining space
        self.file_list_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        file_list_layout = QVBoxLayout(self.file_list_frame)
        file_list_layout.setContentsMargins(10, 10, 10, 10)

        # Placeholder for file list items - Use scroll area for large lists
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.file_list_container = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_container)
        self.file_list_layout.setContentsMargins(0, 0, 0, 0)
        self.file_list_layout.setSpacing(5)
        # Align items to the top by adding stretch at the bottom
        self.file_list_layout.addStretch()

        scroll_area.setWidget(self.file_list_container)
        file_list_layout.addWidget(scroll_area)

        # Add file list frame with stretch factor to take remaining space
        left_layout.addWidget(self.file_list_frame, 1)

        return left_pane

    def _create_right_pane(self) -> QWidget:
        """Create the right pane with optimization controls."""
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(5, 10, 10, 10)
        right_layout.setSpacing(10)

        # Tabbed interface for different file types
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                background-color: {COLORS["bg_primary"]};
            }}
            QTabBar::tab {{
                background: {COLORS["bg_secondary"]};
                color: {COLORS["text_secondary"]};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {COLORS["bg_primary"]};
                color: {COLORS["text_primary"]};
                border-bottom: 2px solid {COLORS["info"]};
            }}
            QTabBar::tab:!selected:hover {{
                background: {COLORS["btn_hover"]};
            }}
        """)

        # Create tabs for different file types
        self.image_tab = self._create_image_tab()
        self.video_tab = self._create_video_tab()
        self.pdf_tab = self._create_pdf_tab()

        self.tab_widget.addTab(self.image_tab, "🖼️ Images")
        self.tab_widget.addTab(self.video_tab, "🎬 Videos")
        self.tab_widget.addTab(self.pdf_tab, "📄 PDFs")

        right_layout.addWidget(self.tab_widget)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.optimize_button = QPushButton("🚀 Optimize Files")
        self.optimize_button.setEnabled(False)
        self.optimize_button.clicked.connect(self.optimize_files)

        self.clear_button = QPushButton("🗑️ Clear All")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_files)

        buttons_layout.addWidget(self.optimize_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()

        right_layout.addLayout(buttons_layout)

        return right_pane

    def _create_image_tab(self) -> QWidget:
        """Create the image optimization tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)

        # Preset selection
        preset_group = self._create_preset_group()
        layout.addWidget(preset_group)

        # Quality settings
        quality_group = self._create_image_quality_group()
        layout.addWidget(quality_group)

        # Resize settings
        resize_group = self._create_resize_group()
        layout.addWidget(resize_group)

        # Format settings
        format_group = self._create_format_group()
        layout.addWidget(format_group)

        # General settings
        general_group = self._create_general_settings_group()
        layout.addWidget(general_group)

        layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        return tab

    def _create_video_tab(self) -> QWidget:
        """Create the video optimization tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)

        # Preset selection (shared)
        preset_group = self._create_preset_group()
        layout.addWidget(preset_group)

        # Video quality settings
        video_quality_group = self._create_video_quality_group()
        layout.addWidget(video_quality_group)

        # Video resize settings (shared)
        resize_group = self._create_resize_group()
        layout.addWidget(resize_group)

        # General settings (shared)
        general_group = self._create_general_settings_group()
        layout.addWidget(general_group)

        layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        return tab

    def _create_pdf_tab(self) -> QWidget:
        """Create the PDF optimization tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)

        # Preset selection (shared)
        preset_group = self._create_preset_group()
        layout.addWidget(preset_group)

        # PDF quality settings
        pdf_quality_group = self._create_pdf_quality_group()
        layout.addWidget(pdf_quality_group)

        # General settings (shared)
        general_group = self._create_general_settings_group()
        layout.addWidget(general_group)

        layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        return tab

    def _create_preset_group(self) -> QGroupBox:
        """Create preset selection group."""
        group = QGroupBox("Optimization Presets")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Preset combo box
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_label.setMinimumWidth(80)

        self.preset_combo = QComboBox()
        self.preset_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 6px;
                color: {COLORS["text_primary"]};
            }}
            QComboBox:focus {{
                border-color: {COLORS["info"]};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {COLORS["text_secondary"]};
            }}
        """)

        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_layout)

        # Preset description
        self.preset_description = QLabel()
        self.preset_description.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        self.preset_description.setWordWrap(True)
        layout.addWidget(self.preset_description)

        # Populate presets (after UI elements are created)
        self._populate_presets()
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)

        # Custom preset buttons
        button_layout = QHBoxLayout()

        self.save_preset_btn = QPushButton("Save as Preset")
        self.save_preset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["btn_bg"]};
                border: 1px solid {COLORS["border_primary"]};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
        """)
        self.save_preset_btn.clicked.connect(self._save_custom_preset)

        self.delete_preset_btn = QPushButton("Delete Preset")
        self.delete_preset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
        """)
        self.delete_preset_btn.clicked.connect(self._delete_custom_preset)

        button_layout.addWidget(self.save_preset_btn)
        button_layout.addWidget(self.delete_preset_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        return group

    def _create_image_quality_group(self) -> QGroupBox:
        """Create image quality settings group."""
        group = QGroupBox("Image Quality")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QGridLayout(group)
        layout.setSpacing(8)

        # Quality preset slider
        layout.addWidget(QLabel("Quality Level:"), 0, 0)

        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 4)  # 5 quality levels
        self.quality_slider.setValue(2)  # Medium default
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(1)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)

        self.quality_label = QLabel("Medium")
        self.quality_label.setMinimumWidth(80)
        self.quality_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.quality_slider, 1)
        quality_layout.addWidget(self.quality_label)
        layout.addLayout(quality_layout, 0, 1)

        # Custom quality
        layout.addWidget(QLabel("Custom Quality:"), 1, 0)

        self.custom_quality_spin = QSpinBox()
        self.custom_quality_spin.setRange(0, 100)
        self.custom_quality_spin.setSuffix("%")
        self.custom_quality_spin.setSpecialValueText("Auto")
        self.custom_quality_spin.setValue(0)  # 0 means auto
        self.custom_quality_spin.valueChanged.connect(self._on_custom_quality_changed)
        self.custom_quality_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.custom_quality_spin, 1, 1)

        # Progressive JPEG
        self.progressive_checkbox = QCheckBox("Progressive JPEG")
        self.progressive_checkbox.setChecked(True)
        self.progressive_checkbox.stateChanged.connect(self._on_settings_changed)
        self.progressive_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS["text_primary"]};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {COLORS["border_secondary"]};
                background-color: {COLORS["bg_secondary"]};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {COLORS["info"]};
                background-color: {COLORS["info"]};
                border-radius: 3px;
            }}
        """)

        layout.addWidget(self.progressive_checkbox, 2, 0, 1, 2)

        return group

    def _create_video_quality_group(self) -> QGroupBox:
        """Create video quality settings group."""
        group = QGroupBox("Video Quality")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QGridLayout(group)
        layout.setSpacing(8)

        # Video quality (CRF)
        layout.addWidget(QLabel("Quality (CRF):"), 0, 0)

        self.video_quality_spin = QSpinBox()
        self.video_quality_spin.setRange(0, 51)
        self.video_quality_spin.setValue(28)  # Default medium quality
        self.video_quality_spin.setSpecialValueText("Auto")
        self.video_quality_spin.valueChanged.connect(self._on_settings_changed)
        self.video_quality_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.video_quality_spin, 0, 1)

        # Bitrate
        layout.addWidget(QLabel("Bitrate:"), 1, 0)

        self.video_bitrate_combo = QComboBox()
        self.video_bitrate_combo.setEditable(True)
        self.video_bitrate_combo.addItems(["Auto", "500k", "1M", "2M", "5M", "10M"])
        self.video_bitrate_combo.setCurrentText("Auto")
        self.video_bitrate_combo.currentTextChanged.connect(self._on_settings_changed)
        self.video_bitrate_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 6px;
                color: {COLORS["text_primary"]};
            }}
            QComboBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.video_bitrate_combo, 1, 1)

        # FPS
        layout.addWidget(QLabel("Frame Rate:"), 2, 0)

        self.video_fps_spin = QSpinBox()
        self.video_fps_spin.setRange(0, 120)
        self.video_fps_spin.setValue(0)  # 0 means auto
        self.video_fps_spin.setSpecialValueText("Auto")
        self.video_fps_spin.setSuffix(" fps")
        self.video_fps_spin.valueChanged.connect(self._on_settings_changed)
        self.video_fps_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.video_fps_spin, 2, 1)

        return group

    def _create_pdf_quality_group(self) -> QGroupBox:
        """Create PDF quality settings group."""
        group = QGroupBox("PDF Quality")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QGridLayout(group)
        layout.setSpacing(8)

        # PDF quality
        layout.addWidget(QLabel("Quality:"), 0, 0)

        self.pdf_quality_spin = QSpinBox()
        self.pdf_quality_spin.setRange(0, 100)
        self.pdf_quality_spin.setValue(0)  # 0 means auto
        self.pdf_quality_spin.setSpecialValueText("Auto")
        self.pdf_quality_spin.setSuffix("%")
        self.pdf_quality_spin.valueChanged.connect(self._on_settings_changed)
        self.pdf_quality_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.pdf_quality_spin, 0, 1)

        # PDF DPI
        layout.addWidget(QLabel("Image DPI:"), 1, 0)

        self.pdf_dpi_spin = QSpinBox()
        self.pdf_dpi_spin.setRange(0, 600)
        self.pdf_dpi_spin.setValue(0)  # 0 means auto
        self.pdf_dpi_spin.setSpecialValueText("Auto")
        self.pdf_dpi_spin.setSuffix(" dpi")
        self.pdf_dpi_spin.valueChanged.connect(self._on_settings_changed)
        self.pdf_dpi_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.pdf_dpi_spin, 1, 1)

        # Ghostscript path configuration
        layout.addWidget(QLabel("Ghostscript Path:"), 2, 0)

        ghostscript_layout = QHBoxLayout()

        self.ghostscript_path_edit = QLineEdit()
        self.ghostscript_path_edit.setPlaceholderText("Auto-detect (leave empty for default)")
        self.ghostscript_path_edit.setText(self.pdf_engine.get_ghostscript_path())
        self.ghostscript_path_edit.textChanged.connect(self._on_ghostscript_path_changed)
        self.ghostscript_path_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QLineEdit:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        self.ghostscript_browse_btn = QPushButton("Browse...")
        self.ghostscript_browse_btn.clicked.connect(self._browse_ghostscript_path)
        self.ghostscript_browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["btn_bg"]};
                border: 1px solid {COLORS["border_primary"]};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
        """)

        self.ghostscript_test_btn = QPushButton("Test")
        self.ghostscript_test_btn.clicked.connect(self._test_ghostscript_path)
        self.ghostscript_test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["btn_bg"]};
                border: 1px solid {COLORS["border_primary"]};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
        """)

        ghostscript_layout.addWidget(self.ghostscript_path_edit, 1)
        ghostscript_layout.addWidget(self.ghostscript_browse_btn)
        ghostscript_layout.addWidget(self.ghostscript_test_btn)

        layout.addLayout(ghostscript_layout, 2, 1)

        # Ghostscript status label
        self.ghostscript_status_label = QLabel()
        self.ghostscript_status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        self.ghostscript_status_label.setWordWrap(True)
        layout.addWidget(self.ghostscript_status_label, 3, 0, 1, 2)

        # Update status initially
        self._update_ghostscript_status()

        return group

    def _create_resize_group(self) -> QGroupBox:
        """Create resize settings group."""
        group = QGroupBox("Resize Options")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QGridLayout(group)
        layout.setSpacing(8)

        # Quick resize buttons
        layout.addWidget(QLabel("Quick Resize:"), 0, 0, 1, 2)

        button_layout = QHBoxLayout()
        resize_percentages = [90, 75, 50, 25, 10]
        self.resize_buttons = []

        for percentage in resize_percentages:
            btn = QPushButton(f"{percentage}%")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS["btn_bg"]};
                    border: 1px solid {COLORS["border_primary"]};
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    min-width: 40px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["btn_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS["info"]};
                }}
            """)
            btn.clicked.connect(lambda checked, p=percentage: self._set_resize_percentage(p))
            button_layout.addWidget(btn)
            self.resize_buttons.append(btn)

        button_layout.addStretch()
        layout.addLayout(button_layout, 1, 0, 1, 2)

        # Custom dimensions
        layout.addWidget(QLabel("Max Width:"), 2, 0)

        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(0, 10000)
        self.max_width_spin.setValue(0)  # 0 means no limit
        self.max_width_spin.setSpecialValueText("No limit")
        self.max_width_spin.setSuffix(" px")
        self.max_width_spin.valueChanged.connect(self._on_settings_changed)
        self.max_width_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.max_width_spin, 2, 1)

        layout.addWidget(QLabel("Max Height:"), 3, 0)

        self.max_height_spin = QSpinBox()
        self.max_height_spin.setRange(0, 10000)
        self.max_height_spin.setValue(0)  # 0 means no limit
        self.max_height_spin.setSpecialValueText("No limit")
        self.max_height_spin.setSuffix(" px")
        self.max_height_spin.valueChanged.connect(self._on_settings_changed)
        self.max_height_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.max_height_spin, 3, 1)

        # Custom resolution controls with aspect ratio preservation
        layout.addWidget(QLabel("Custom Resolution:"), 4, 0, 1, 2)

        # Resolution input layout
        resolution_layout = QHBoxLayout()

        self.custom_width_spin = QSpinBox()
        self.custom_width_spin.setRange(1, 10000)
        self.custom_width_spin.setValue(1920)
        self.custom_width_spin.setSuffix(" px")
        self.custom_width_spin.valueChanged.connect(self._on_custom_resolution_changed)
        self.custom_width_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        resolution_layout.addWidget(QLabel("W:"))
        resolution_layout.addWidget(self.custom_width_spin)

        resolution_layout.addWidget(QLabel("x"))

        self.custom_height_spin = QSpinBox()
        self.custom_height_spin.setRange(1, 10000)
        self.custom_height_spin.setValue(1080)
        self.custom_height_spin.setSuffix(" px")
        self.custom_height_spin.valueChanged.connect(self._on_custom_resolution_changed)
        self.custom_height_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS["text_primary"]};
            }}
            QSpinBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        resolution_layout.addWidget(QLabel("H:"))
        resolution_layout.addWidget(self.custom_height_spin)

        # Aspect ratio preservation checkbox
        self.preserve_aspect_checkbox = QCheckBox("Preserve aspect ratio")
        self.preserve_aspect_checkbox.setChecked(True)
        self.preserve_aspect_checkbox.stateChanged.connect(self._on_aspect_ratio_changed)
        self.preserve_aspect_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS["text_primary"]};
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 3px;
                background-color: {COLORS["bg_secondary"]};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS["info"]};
                border-color: {COLORS["info"]};
            }}
        """)

        resolution_layout.addWidget(self.preserve_aspect_checkbox)
        resolution_layout.addStretch()

        layout.addLayout(resolution_layout, 5, 0, 1, 2)

        # Apply custom resolution button
        self.apply_resolution_btn = QPushButton("Apply Custom Resolution")
        self.apply_resolution_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["btn_bg"]};
                border: 1px solid {COLORS["border_primary"]};
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {COLORS["info"]};
            }}
        """)
        self.apply_resolution_btn.clicked.connect(self._apply_custom_resolution)

        layout.addWidget(self.apply_resolution_btn, 6, 0, 1, 2)

        return group

    def _create_format_group(self) -> QGroupBox:
        """Create format conversion settings group."""
        group = QGroupBox("Format Options")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QGridLayout(group)
        layout.setSpacing(8)

        # Output format
        layout.addWidget(QLabel("Output Format:"), 0, 0)

        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["Auto", "JPEG", "PNG", "WebP"])
        self.output_format_combo.setCurrentText("Auto")
        self.output_format_combo.currentTextChanged.connect(self._on_settings_changed)
        self.output_format_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 6px;
                color: {COLORS["text_primary"]};
            }}
            QComboBox:focus {{
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.output_format_combo, 0, 1)

        return group

    def _create_general_settings_group(self) -> QGroupBox:
        """Create general settings group."""
        group = QGroupBox("General Settings")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Preserve metadata checkbox
        self.preserve_metadata_checkbox = QCheckBox("Preserve file metadata")
        self.preserve_metadata_checkbox.setChecked(False)
        self.preserve_metadata_checkbox.stateChanged.connect(self._on_settings_changed)
        self.preserve_metadata_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS["text_primary"]};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {COLORS["border_secondary"]};
                background-color: {COLORS["bg_secondary"]};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {COLORS["info"]};
                background-color: {COLORS["info"]};
                border-radius: 3px;
            }}
        """)

        layout.addWidget(self.preserve_metadata_checkbox)

        return group

    def _create_status_bar(self) -> QFrame:
        """Create the bottom status bar with enhanced progress display."""
        status_bar = QFrame()
        status_bar.setFrameShape(QFrame.Shape.NoFrame)
        status_bar.setFixedHeight(60)  # Increased height for progress bar
        status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["bg_secondary"]};
                border-top: 1px solid {COLORS["border_secondary"]};
            }}
        """)

        status_layout = QVBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_layout.setSpacing(3)

        # Top row with status message and progress info
        top_row = QHBoxLayout()

        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        top_row.addWidget(self.status_label)

        top_row.addStretch()

        # Progress info labels
        self.progress_info_label = QLabel()
        self.progress_info_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        self.progress_info_label.setVisible(False)
        top_row.addWidget(self.progress_info_label)

        status_layout.addLayout(top_row)

        # Bottom row with progress bar and detailed stats
        bottom_row = QHBoxLayout()

        # Progress bar

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 3px;
                text-align: center;
                background-color: {COLORS["bg_primary"]};
                color: {COLORS["text_primary"]};
                font-size: 11px;
                height: 18px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS["info"]};
                border-radius: 2px;
            }}
        """)
        bottom_row.addWidget(self.progress_bar, 1)

        # Detailed stats labels
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; margin-left: 10px;")
        self.stats_label.setVisible(False)
        bottom_row.addWidget(self.stats_label)

        status_layout.addLayout(bottom_row)

        return status_bar

    def update_status(self, message: str, status_type: str = "info"):
        """Update the status bar message."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(get_status_style(status_type))
        logger.info("Status updated: %s", message)

    def handle_files_dropped(self, file_paths: list[str]):
        """Handle files dropped onto the drop area."""
        logger.info("Handling dropped files: %s", file_paths)

        # Process files through FileManager
        new_files = []
        for file_path in file_paths:
            file_infos = self.file_manager.process_input(file_path)
            new_files.extend(file_infos)

        # Filter supported files
        supported_files = [f for f in new_files if f.is_supported]
        unsupported_files = [f for f in new_files if not f.is_supported]

        if not supported_files and not unsupported_files:
            self.update_status("No valid files found", "error")
            return

        # Add supported files to current list
        self.current_files.extend(supported_files)

        # Show file list frame
        self.file_list_frame.show()

        # Add files to the UI list
        for file_info in supported_files:
            self._add_file_to_list(file_info)

        # Show warnings for unsupported files
        if unsupported_files:
            unsupported_names = [f.path.name for f in unsupported_files]
            logger.warning("Unsupported files skipped: %s", unsupported_names)
            self.update_status(f"Skipped {len(unsupported_files)} unsupported file(s)", "warning")

        # Enable action buttons if we have supported files
        if supported_files:
            self.optimize_button.setEnabled(True)
            self.clear_button.setEnabled(True)

            # Update status
            total_supported = len(self.current_files)
            file_suffix = "s" if total_supported != 1 else ""
        self.update_status(f"Ready to optimize {total_supported} file{file_suffix}")

    def _add_file_to_list(self, file_info: FileInfo):
        """Add a file to the UI file list."""
        # Create file item widget
        file_widget = QWidget()
        file_widget.setFixedHeight(50)  # Set consistent height for all file items
        file_layout = QHBoxLayout(file_widget)
        file_layout.setContentsMargins(5, 5, 5, 5)
        file_layout.setSpacing(8)

        # File type icon
        type_icons = {"image": "🖼️", "video": "🎬", "pdf": "📄", "unknown": "❓"}
        icon = type_icons.get(file_info.file_type, "📄")

        # File info label
        file_size_mb = file_info.size / (1024 * 1024) if file_info.size > 0 else 0
        size_text = f"{file_size_mb:.1f} MB" if file_size_mb >= 0.1 else f"{file_info.size} bytes"

        file_label = QLabel(f"{icon} {file_info.path.name}")
        file_label.setStyleSheet(f"font-weight: 500; color: {COLORS['text_primary']};")

        size_label = QLabel(f"({size_text})")
        size_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")

        # Magic number detection indicator
        if file_info.magic_detected:
            magic_label = QLabel("✓")
            magic_label.setToolTip("File type verified by content analysis")
            magic_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
            file_layout.addWidget(magic_label)

        file_layout.addWidget(file_label)
        file_layout.addWidget(size_label)

        # Remove button per item
        remove_button = QPushButton("🗑️ Remove")
        remove_button.setToolTip("Remove this file from the list")
        remove_button.clicked.connect(lambda _=False, w=file_widget, p=file_info.path: self._on_remove_clicked(w, p))
        file_layout.addWidget(remove_button)

        file_layout.addStretch()

        # Style the file widget
        file_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS["bg_tertiary"]};
                border-radius: 4px;
                border: 1px solid {COLORS["border_secondary"]};
            }}
            QWidget:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
        """)

        self.file_list_layout.addWidget(file_widget)

    def browse_files(self):
        """Open file browser to select files."""

        # Get supported formats from FileManager
        formats = self.file_manager.get_supported_formats()

        # Build filter strings
        all_extensions = []
        filter_parts = []

        for category, extensions in formats.items():
            ext_patterns = [f"*{ext}" for ext in extensions]
            all_extensions.extend(ext_patterns)
            category_name = category.title()
            filter_parts.append(f"{category_name} ({' '.join(ext_patterns)})")

        # Create complete filter string
        all_filter = f"All Supported Files ({' '.join(all_extensions)})"
        name_filter = f"{all_filter};;{';'.join(filter_parts)}"

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(name_filter)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.handle_files_dropped(selected_files)

    def process_text_input(self):
        """Process URL or base64 input from text field."""
        input_text = self.input_text.toPlainText().strip()

        if not input_text:
            self.update_status("Please enter a URL or base64 data", "warning")
            return

        self.update_status("Processing input...", "info")

        try:
            # Process input through FileManager
            file_infos = self.file_manager.process_input(input_text)

            if not file_infos:
                self.update_status("Could not process input - invalid URL or data", "error")
                return

            # Filter supported files
            supported_files = [f for f in file_infos if f.is_supported]

            if not supported_files:
                self.update_status("Input processed but file type not supported", "warning")
                return

            # Add to current files and UI
            self.current_files.extend(supported_files)

            # Show file list frame
            self.file_list_frame.show()

            # Add files to UI
            for file_info in supported_files:
                self._add_file_to_list(file_info)

            # Enable action buttons
            self.optimize_button.setEnabled(True)
            self.clear_button.setEnabled(True)

            # Clear input and update status
            self.input_text.clear()
            total_files = len(self.current_files)
            self.update_status(
                f"Added file from input. Ready to optimize {total_files} file{'s' if total_files != 1 else ''}"
            )

        except Exception as e:
            logger.exception("Error processing text input")
            self.update_status(f"Error processing input: {e}", "error")

    def optimize_files(self):
        """Start the optimization process using batch processing."""
        if not self.current_files:
            self.update_status("No files to optimize", "warning")
            return

        try:
            self.optimize_button.setEnabled(False)
            self.update_status("Starting batch optimization...", "info")

            # Get current settings
            settings = self.settings_manager.get_current_settings()

            # Prepare file paths for batch processing
            file_paths = [file_info.path for file_info in self.current_files]

            # Start batch optimization using OptimizationManager
            self.optimization_manager.optimize_batch(file_paths, None, settings)

        except Exception as e:
            logger.exception("Error starting batch optimization")
            self.update_status(f"Batch optimization failed to start: {e}", "error")
            self.optimize_button.setEnabled(True)

    def _optimize_single_file(self, file_info: FileInfo) -> dict[str, Any]:
        """Optimize a single file based on its type."""
        settings = self.settings_manager.get_current_settings()

        # Generate output path
        output_path = self._generate_output_path(file_info.path)

        try:
            if file_info.file_type == "image":
                return self.image_engine.optimize_image(file_info.path, output_path, settings)
            if file_info.file_type == "video":
                return self.video_engine.optimize_video(file_info.path, output_path, settings)
            if file_info.file_type == "pdf":
                return self.pdf_engine.optimize_pdf(file_info.path, output_path, settings)
            return {"success": False, "error": f"Unsupported file type: {file_info.file_type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_output_path(self, input_path: Path) -> Path:
        """Generate output path for optimized file."""
        settings = self.settings_manager.get_current_settings()

        if settings.create_backup:
            # Create backup of original
            backup_path = input_path.with_suffix(f".backup{input_path.suffix}")
            if not backup_path.exists():
                shutil.copy2(input_path, backup_path)

        # For now, overwrite the original file
        # In a more advanced implementation, this could be configurable
        return input_path

    def _on_remove_clicked(self, file_widget: QWidget, file_path: Path):
        """Remove a single file item from the list and state."""
        # Remove the widget from the layout
        for i in range(self.file_list_layout.count()):
            item = self.file_list_layout.itemAt(i)
            if item and item.widget() is file_widget:
                self.file_list_layout.takeAt(i)
                file_widget.deleteLater()
                break

        # Remove from current_files (first match)
        for i, fi in enumerate(self.current_files):
            if fi.path == file_path:
                del self.current_files[i]
                break

        # Update controls and status
        if not self.current_files:
            self.optimize_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.update_status("Ready - Drop files or click Browse to get started")
        else:
            total_supported = len(self.current_files)
            file_suffix = "s" if total_supported != 1 else ""
            self.update_status(f"Ready to optimize {total_supported} file{file_suffix}")

    def clear_files(self):
        """Clear all files from the list."""
        # Clear file list
        while self.file_list_layout.count():
            child = self.file_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Clear current files list
        self.current_files.clear()

        # Cleanup temporary files
        self.file_manager.cleanup_temp_files()

        # Disable action buttons
        self.optimize_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        # Update status
        self.update_status("Ready - Drop files or click Browse to get started")
        logger.info("Files cleared")

    def _populate_presets(self):
        """Populate the preset combo box."""
        self.preset_combo.clear()
        presets = self.settings_manager.get_presets()

        for name, _preset in presets.items():
            self.preset_combo.addItem(name)

        # Set current preset if it exists
        current_settings = self.settings_manager.get_current_settings()
        # Try to find matching preset
        for name, preset in presets.items():
            if preset.settings.quality_preset == current_settings.quality_preset:
                self.preset_combo.setCurrentText(name)
                break

        # Update description
        self._update_preset_description()

    def _update_preset_description(self):
        """Update the preset description label."""
        current_preset_name = self.preset_combo.currentText()
        preset = self.settings_manager.get_preset(current_preset_name)

        if preset:
            self.preset_description.setText(preset.description)
        else:
            self.preset_description.setText("")

    def _on_preset_changed(self, preset_name: str):
        """Handle preset selection change."""
        if preset_name and self.settings_manager.apply_preset(preset_name):
            self._update_ui_from_settings()
            self._update_preset_description()
            logger.info("Applied preset: %s", preset_name)

    def _on_quality_changed(self, value: int):
        """Handle quality slider change."""
        quality_names = ["Minimum", "Low", "Medium", "High", "Maximum"]
        quality_presets = [
            QualityPreset.MINIMUM,
            QualityPreset.LOW,
            QualityPreset.MEDIUM,
            QualityPreset.HIGH,
            QualityPreset.MAXIMUM,
        ]

        if 0 <= value < len(quality_names):
            self.quality_label.setText(quality_names[value])

            # Update settings
            settings = self.settings_manager.get_current_settings()
            settings.quality_preset = quality_presets[value]
            self.settings_manager.set_current_settings(settings)

    def _on_ghostscript_path_changed(self):
        """Handle Ghostscript path changes."""
        path = self.ghostscript_path_edit.text().strip()
        self.pdf_engine.set_ghostscript_path(path)
        self._update_ghostscript_status()

    def _browse_ghostscript_path(self):
        """Browse for Ghostscript executable."""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Ghostscript Executable",
            "",
            "Executable files (*)" if sys.platform != "win32" else "Executable files (*.exe)",
        )

        if file_path:
            self.ghostscript_path_edit.setText(file_path)

    def _test_ghostscript_path(self):
        """Test the current Ghostscript path."""
        try:
            # Force re-check of Ghostscript availability
            self.pdf_engine._gs_command = None
            self.pdf_engine._gs_version = None
            available = self.pdf_engine._check_ghostscript_available()

            if available:
                self.ghostscript_status_label.setText("✓ Ghostscript is working correctly")
                self.ghostscript_status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px;")
            else:
                self.ghostscript_status_label.setText("✗ Ghostscript not found or not working")
                self.ghostscript_status_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 11px;")

        except Exception as e:
            self.ghostscript_status_label.setText(f"✗ Error testing Ghostscript: {e!s}")
            self.ghostscript_status_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 11px;")

    def _update_ghostscript_status(self):
        """Update the Ghostscript status display."""
        try:
            # Check if Ghostscript is available
            available = self.pdf_engine._check_ghostscript_available()

            if available:
                gs_path = getattr(self.pdf_engine, "_gs_command", None) or "gs (system path)"
                self.ghostscript_status_label.setText(f"✓ Using: {gs_path}")
                self.ghostscript_status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px;")
            else:
                self.ghostscript_status_label.setText("⚠ Ghostscript not found - PDF optimization unavailable")
                self.ghostscript_status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px;")

        except Exception as e:
            self.ghostscript_status_label.setText(f"⚠ Error checking Ghostscript: {e!s}")
            self.ghostscript_status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px;")

            # Reset custom quality when preset changes
            self.custom_quality_spin.setValue(0)

    def _on_custom_quality_changed(self, value: int):
        """Handle custom quality change."""
        settings = self.settings_manager.get_current_settings()
        settings.image_quality = value if value > 0 else None
        self.settings_manager.set_current_settings(settings)

    def _on_settings_changed(self):
        """Handle general settings changes."""
        settings = self.settings_manager.get_current_settings()

        # Update settings from UI controls
        settings.create_backup = False  # Always disabled - create new compressed files
        settings.preserve_metadata = self.preserve_metadata_checkbox.isChecked()
        settings.progressive_jpeg = self.progressive_checkbox.isChecked()

        # Dimensions
        settings.max_width = self.max_width_spin.value() if self.max_width_spin.value() > 0 else None
        settings.max_height = self.max_height_spin.value() if self.max_height_spin.value() > 0 else None

        # Clear percentage mode if manual dimensions are set
        if settings.max_width or settings.max_height:
            self.resize_percentage = None

        # Output format
        format_text = self.output_format_combo.currentText()
        settings.output_format = format_text.lower() if format_text != "Auto" else None

        # Video settings (if controls exist)
        if hasattr(self, "video_quality_spin"):
            settings.video_quality = self.video_quality_spin.value() if self.video_quality_spin.value() > 0 else None

        if hasattr(self, "video_bitrate_combo"):
            bitrate_text = self.video_bitrate_combo.currentText()
            settings.video_bitrate = bitrate_text if bitrate_text != "Auto" else None

        if hasattr(self, "video_fps_spin"):
            settings.video_fps = self.video_fps_spin.value() if self.video_fps_spin.value() > 0 else None

        # PDF settings (if controls exist)
        if hasattr(self, "pdf_quality_spin"):
            settings.pdf_quality = self.pdf_quality_spin.value() if self.pdf_quality_spin.value() > 0 else None

        if hasattr(self, "pdf_dpi_spin"):
            settings.pdf_dpi = self.pdf_dpi_spin.value() if self.pdf_dpi_spin.value() > 0 else None

        self.settings_manager.set_current_settings(settings)

    def _update_ui_from_settings(self):
        """Update UI controls from current settings."""
        settings = self.settings_manager.get_current_settings()

        # Quality preset
        quality_values = {
            QualityPreset.MINIMUM: 0,
            QualityPreset.LOW: 1,
            QualityPreset.MEDIUM: 2,
            QualityPreset.HIGH: 3,
            QualityPreset.MAXIMUM: 4,
        }

        if settings.quality_preset in quality_values:
            self.quality_slider.setValue(quality_values[settings.quality_preset])

        # Custom quality
        self.custom_quality_spin.setValue(settings.image_quality or 0)

        # Checkboxes
        # create_backup_checkbox removed - always create new compressed files
        self.preserve_metadata_checkbox.setChecked(settings.preserve_metadata)
        self.progressive_checkbox.setChecked(settings.progressive_jpeg)

        # Dimensions
        self.max_width_spin.setValue(settings.max_width or 0)
        self.max_height_spin.setValue(settings.max_height or 0)

        # Output format
        format_text = settings.output_format.upper() if settings.output_format else "Auto"
        index = self.output_format_combo.findText(format_text)
        if index >= 0:
            self.output_format_combo.setCurrentIndex(index)

        # Video settings (if controls exist)
        if hasattr(self, "video_quality_spin"):
            self.video_quality_spin.setValue(settings.video_quality or 0)

        if hasattr(self, "video_bitrate_combo"):
            bitrate_text = settings.video_bitrate or "Auto"
            self.video_bitrate_combo.setCurrentText(bitrate_text)

        if hasattr(self, "video_fps_spin"):
            self.video_fps_spin.setValue(settings.video_fps or 0)

        # PDF settings (if controls exist)
        if hasattr(self, "pdf_quality_spin"):
            self.pdf_quality_spin.setValue(settings.pdf_quality or 0)

        if hasattr(self, "pdf_dpi_spin"):
            self.pdf_dpi_spin.setValue(settings.pdf_dpi or 0)

    def _set_resize_percentage(self, percentage: int):
        """Set resize percentage using quick buttons with actual percentage-based scaling."""
        # Store the selected percentage for use during optimization
        self.resize_percentage = percentage / 100.0  # Convert to decimal (0.1 to 0.9)

        # Clear the max width/height spinboxes to indicate percentage mode
        self.max_width_spin.setValue(0)  # 0 means no fixed limit
        self.max_height_spin.setValue(0)

        # Update UI to show percentage mode is active
        self.update_status(f"Resize mode: Scale to {percentage}% of original dimensions")

        self._on_settings_changed()

    def _on_custom_resolution_changed(self):
        """Handle custom resolution input changes with aspect ratio preservation."""
        if not hasattr(self, "preserve_aspect_checkbox") or not self.preserve_aspect_checkbox.isChecked():
            return

        sender = self.sender()
        if sender == self.custom_width_spin:
            # Width changed, update height to maintain aspect ratio (16:9 default)
            width = self.custom_width_spin.value()
            height = int(width * 9 / 16)
            self.custom_height_spin.blockSignals(True)
            self.custom_height_spin.setValue(height)
            self.custom_height_spin.blockSignals(False)
        elif sender == self.custom_height_spin:
            # Height changed, update width to maintain aspect ratio (16:9 default)
            height = self.custom_height_spin.value()
            width = int(height * 16 / 9)
            self.custom_width_spin.blockSignals(True)
            self.custom_width_spin.setValue(width)
            self.custom_width_spin.blockSignals(False)

    def _on_aspect_ratio_changed(self):
        """Handle aspect ratio preservation checkbox changes."""
        if self.preserve_aspect_checkbox.isChecked():
            # When enabling aspect ratio preservation, sync height to width
            self._on_custom_resolution_changed()

    def _apply_custom_resolution(self):
        """Apply the custom resolution settings to max width/height controls."""
        width = self.custom_width_spin.value()
        height = self.custom_height_spin.value()

        # Set the max dimensions
        self.max_width_spin.setValue(width)
        self.max_height_spin.setValue(height)

        # Clear percentage mode
        self.resize_percentage = None

        # Update status
        self.update_status(f"Custom resolution applied: {width}x{height} pixels")

        # Trigger settings update
        self._on_settings_changed()

    def _save_custom_preset(self):
        """Save current settings as a custom preset."""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")

        if ok and name.strip():
            name = name.strip()

            # Check if name already exists
            if self.settings_manager.get_preset(name):
                from PyQt6.QtWidgets import QMessageBox

                reply = QMessageBox.question(
                    self,
                    "Preset Exists",
                    f"Preset '{name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Create preset
            current_settings = self.settings_manager.get_current_settings()
            preset = OptimizationPreset(
                name=name, description="Custom preset", settings=current_settings, is_builtin=False
            )

            if self.settings_manager.add_preset(preset):
                self._populate_presets()
                self.preset_combo.setCurrentText(name)
                self.update_status(f"Preset '{name}' saved successfully")
            else:
                self.update_status(f"Failed to save preset '{name}'", "error")

    def _delete_custom_preset(self):
        """Delete the currently selected custom preset."""
        current_preset_name = self.preset_combo.currentText()
        preset = self.settings_manager.get_preset(current_preset_name)

        if not preset:
            return

        if preset.is_builtin:
            self.update_status("Cannot delete built-in presets", "warning")
            return

        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Delete preset '{current_preset_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.settings_manager.remove_preset(current_preset_name):
                self._populate_presets()
                self.update_status(f"Preset '{current_preset_name}' deleted")
            else:
                self.update_status(f"Failed to delete preset '{current_preset_name}'", "error")

    def get_current_settings(self) -> OptimizationSettings:
        """Get current optimization settings."""
        return self.settings_manager.get_current_settings()

    def save_settings(self):
        """Save current settings to file."""
        if self.settings_manager.save_settings():
            logger.info("Settings saved successfully")
        else:
            logger.error("Failed to save settings")

    # Signal handlers for OptimizationManager
    def _on_batch_progress_updated(self, progress: BatchProgress):
        """Handle batch progress updates with enhanced display."""
        # Store the current batch progress for use in results dialog
        self.batch_progress = progress

        # Update progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(int(progress.progress_percentage))

        # Get detailed status information
        status_info = progress.get_detailed_status()

        # Update main status message
        current_file_name = status_info["current_file"]
        operation = status_info["operation"]
        status_msg = f"{operation}: {current_file_name} ({status_info['progress']})"
        self.update_status(status_msg, "info")

        # Update progress info label
        progress_text = f"⏱️ {status_info['elapsed']} | 🔮 {status_info['remaining']} | 📊 {status_info['compression']}"
        self.progress_info_label.setText(progress_text)
        self.progress_info_label.setVisible(True)

        # Update detailed stats
        stats_text = (
            f"✅ {status_info['success_rate']} | "
            f"⚡ {status_info['speed']} | "
            f"💾 {status_info['data_processed']} | "
            f"🚀 {status_info['data_speed']}"
        )
        self.stats_label.setText(stats_text)
        self.stats_label.setVisible(True)

        logger.info("Progress: %s - %s", status_info["progress"], status_info["compression"])

    def _on_file_started(self, file_path: Path):
        """Handle file processing start."""
        # Handle both Path objects and strings
        if isinstance(file_path, Path):
            logger.info("Started processing: %s", file_path.name)
        else:
            logger.info("Started processing: %s", Path(file_path).name)

    def _on_file_completed(self, result: BatchOperationResult):
        """Handle file processing completion with detailed logging."""
        if result.success:
            # Calculate size reduction
            size_reduction = result.original_size - result.optimized_size
            size_reduction_mb = size_reduction / (1024 * 1024)

            # Format processing time
            time_str = (
                f"{result.processing_time:.2f}s"
                if result.processing_time < 60
                else f"{result.processing_time / 60:.1f}m"
            )

            logger.info(
                "✅ Completed: %s | Compression: %.1f%% | Size reduced: %.2f MB | Time: %s | Method: %s",
                result.file_path.name,
                result.compression_ratio,
                size_reduction_mb,
                time_str,
                result.method_used or "default",
            )
        else:
            logger.warning("❌ Failed: %s - %s", result.file_path.name, result.error_message)

    def _on_batch_completed(self, results: list[BatchOperationResult]):
        """Handle batch processing completion with comprehensive results display."""
        self.optimize_button.setEnabled(True)

        # Hide progress indicators
        self.progress_bar.setVisible(False)
        self.progress_info_label.setVisible(False)
        self.stats_label.setVisible(False)

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        # Calculate comprehensive statistics
        total_original_size = sum(r.original_size for r in successful)
        total_optimized_size = sum(r.optimized_size for r in successful)
        total_size_reduction = total_original_size - total_optimized_size

        overall_compression = total_size_reduction / total_original_size * 100 if total_original_size > 0 else 0.0

        total_processing_time = sum(r.processing_time for r in results)

        # Format size reduction
        size_reduction_mb = total_size_reduction / (1024 * 1024)

        if len(successful) == len(results):
            # All files processed successfully
            self.update_status(
                f"✅ Successfully optimized all {len(results)} files | "
                f"Compression: {overall_compression:.1f}% | "
                f"Space saved: {size_reduction_mb:.2f} MB | "
                f"Time: {total_processing_time:.1f}s",
                "success",
            )
        elif successful:
            # Some files failed
            self.update_status(
                f"⚠️ Optimized {len(successful)}/{len(results)} files | "
                f"Compression: {overall_compression:.1f}% | "
                f"Space saved: {size_reduction_mb:.2f} MB | "
                f"{len(failed)} failed",
                "warning",
            )
        else:
            # All files failed
            self.update_status(f"❌ Failed to optimize all {len(results)} files", "error")

        # Log detailed results summary
        logger.info(
            "Batch completed: %d successful, %d failed | "
            "Total compression: %.1f%% | "
            "Space saved: %.2f MB | "
            "Processing time: %.1f seconds",
            len(successful),
            len(failed),
            overall_compression,
            size_reduction_mb,
            total_processing_time,
        )

        # Log failed files
        for result in failed:
            logger.error("Failed to optimize %s: %s", result.file_path.name, result.error_message)

        # Show results dialog if there are results to display
        if results:
            results_dialog = OptimizationResultsDialog(results, self.batch_progress, self)
            results_dialog.exec()

    def _on_optimization_error(self, error_message: str):
        """Handle optimization errors."""
        self.optimize_button.setEnabled(True)
        self.update_status(f"Optimization error: {error_message}", "error")
        logger.error("Optimization error: %s", error_message)


def create_file_optimization_widget(style_func, scratch_pad=None):
    """
    Create the file optimization widget following DevBoost patterns.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The main widget for the file optimization tool.
    """
    return FileOptimizationWidget(style_func, scratch_pad)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("File Optimization Tool")
    main_window.setGeometry(100, 100, 1000, 700)

    central_widget = create_file_optimization_widget(app.style)
    main_window.setCentralWidget(central_widget)

    main_window.show()
    sys.exit(app.exec())
