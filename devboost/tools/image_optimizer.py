import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageFile, ImageOps
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import COLORS, get_status_style, get_tool_style

# Enable loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)


class ImageOptimizer(QObject):
    """
    Backend image optimization logic with compression and quality control.
    """

    optimization_completed = pyqtSignal(str, bool, str, dict)  # output_path, success, error_message, stats

    def __init__(self):
        super().__init__()

    def optimize_image(
        self,
        input_path: str,
        output_path: str | None = None,
        quality: int = 85,
        format_type: str | None = None,
        max_width: int | None = None,
        max_height: int | None = None,
        optimize: bool = True,
        progressive: bool = True,
        preserve_exif: bool = False,
    ) -> tuple[bool, str, str, dict[str, Any]]:
        """
        Optimize image with compression and resizing options.

        Args:
            input_path: Path to input image
            output_path: Path for optimized output (auto-generated if None)
            quality: JPEG quality (1-100, higher = better quality/larger file)
            format_type: Output format (JPEG, PNG, WEBP, auto-detect if None)
            max_width: Maximum width for resizing (maintains aspect ratio)
            max_height: Maximum height for resizing (maintains aspect ratio)
            optimize: Enable PIL optimization algorithms
            progressive: Enable progressive JPEG for web
            preserve_exif: Keep EXIF metadata (increases file size)

        Returns:
            Tuple of (success, output_path, error_message, stats_dict)
        """
        try:
            if not Path(input_path).exists():
                return False, "", "Input file does not exist", {}

            # Get original file stats
            original_size = Path(input_path).stat().st_size

            # Load image
            with Image.open(input_path) as img:
                original_format = img.format

                # Determine output format
                format_type = original_format or "JPEG" if format_type is None else format_type.upper()

                # Resize if dimensions provided
                if max_width or max_height:
                    img = self._resize_image(img, max_width, max_height)

                # Prepare output path
                if output_path is None:
                    input_path_obj = Path(input_path)
                    ext_map = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
                    new_ext = ext_map.get(format_type, input_path_obj.suffix)
                    output_path = str(input_path_obj.with_name(f"{input_path_obj.stem}_optimized{new_ext}"))

                # Save with optimization
                save_kwargs = {
                    "optimize": optimize,
                    "quality": quality,
                }

                if format_type == "JPEG":
                    save_kwargs["progressive"] = progressive
                    if img.mode in ("RGBA", "LA", "P"):
                        # Convert to RGB for JPEG
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                        img = background
                elif format_type == "PNG":
                    save_kwargs["optimize"] = optimize
                    if not preserve_exif:
                        save_kwargs["icc_profile"] = None
                elif format_type == "WEBP":
                    save_kwargs["method"] = 6  # Best compression
                    save_kwargs["lossless"] = False

                # Remove EXIF if not preserving
                if not preserve_exif and hasattr(img, "info"):
                    img.info.clear()

                # Save optimized image
                img.save(output_path, format=format_type, **save_kwargs)

                # Get optimization stats
                optimized_size = Path(output_path).stat().st_size
                compression_ratio = ((original_size - optimized_size) / original_size) * 100

                stats = {
                    "original_size": original_size,
                    "optimized_size": optimized_size,
                    "compression_ratio": compression_ratio,
                    "original_format": original_format,
                    "output_format": format_type,
                    "dimensions": img.size,
                    "mode": img.mode,
                }

                return True, output_path, "", stats

        except Exception as e:
            error_msg = f"Optimization failed: {e!s}"
            logger.exception("Image optimization failed: %s", error_msg)
            return False, "", error_msg, {}

    def _resize_image(self, img: Image.Image, max_width: int | None, max_height: int | None) -> Image.Image:
        """Resize image while maintaining aspect ratio."""
        if not max_width and not max_height:
            return img

        original_width, original_height = img.size

        # Calculate new dimensions
        if max_width and max_height:
            # Fit within bounds
            ratio = min(max_width / original_width, max_height / original_height)
        elif max_width:
            ratio = max_width / original_width
        else:  # max_height
            ratio = max_height / original_height

        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        # Ensure minimum size
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def get_supported_formats(self) -> list:
        """Return list of supported output formats."""
        return ["JPEG", "PNG", "WEBP", "Auto-detect"]

    def get_quality_presets(self) -> dict[str, int]:
        """Return quality presets mapping."""
        return {
            "Maximum (95)": 95,
            "High (85)": 85,
            "Medium (75)": 75,
            "Low (60)": 60,
            "Minimum (40)": 40,
        }


class ImageProcessingError(Exception):
    """Custom exception for image processing failures."""

    pass


# ruff: noqa: C901
def create_image_optimizer_widget(style_func, scratch_pad=None):
    """
    Creates the main widget for the image optimization tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The main widget for the tool.
    """
    optimizer = ImageOptimizer()

    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    # Main layout
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Splitter
    splitter = QSplitter(Qt.Orientation.Horizontal)
    main_layout.addWidget(splitter, 1)

    # --- Left Pane (Input) ---
    left_pane = QWidget()
    left_layout = QVBoxLayout(left_pane)
    left_layout.setContentsMargins(10, 5, 5, 10)
    left_layout.setSpacing(5)

    # Upload Toolbar
    upload_toolbar_layout = QHBoxLayout()
    upload_toolbar_layout.setSpacing(8)

    upload_button = QPushButton("Upload Image")
    upload_toolbar_layout.addWidget(upload_button)
    upload_toolbar_layout.addStretch()

    left_layout.addLayout(upload_toolbar_layout)

    # Image Preview Area
    preview_label = QLabel()
    preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    preview_label.setStyleSheet(
        f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border_secondary']};"
    )
    left_layout.addWidget(preview_label)
    splitter.addWidget(left_pane)

    # --- Right Pane (Controls) ---
    right_pane = QWidget()
    right_layout = QVBoxLayout(right_pane)
    right_layout.setContentsMargins(10, 5, 5, 10)
    right_layout.setSpacing(10)

    # Optimization Controls
    controls_frame = QFrame()
    controls_frame.setFrameShape(QFrame.Shape.StyledPanel)
    controls_layout = QVBoxLayout(controls_frame)
    controls_layout.setSpacing(8)

    # Quality Preset
    quality_layout = QHBoxLayout()
    quality_label = QLabel("Quality Preset:")
    quality_combo = QComboBox()
    quality_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
    quality_combo.addItems(optimizer.get_quality_presets().keys())
    quality_combo.setCurrentText("High (85)")
    quality_layout.addWidget(quality_label)
    quality_layout.addWidget(quality_combo)
    controls_layout.addLayout(quality_layout)

    # Format Selection
    format_layout = QHBoxLayout()
    format_label = QLabel("Output Format:")
    format_combo = QComboBox()
    format_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
    format_combo.addItems(optimizer.get_supported_formats())
    format_combo.setCurrentText("Auto-detect")
    format_layout.addWidget(format_label)
    format_layout.addWidget(format_combo)
    controls_layout.addLayout(format_layout)

    # Resize Options
    resize_layout = QHBoxLayout()
    resize_label = QLabel("Max Dimensions:")
    width_input = QLineEdit()
    width_input.setPlaceholderText("Width")
    width_input.setFixedWidth(80)
    height_input = QLineEdit()
    height_input.setPlaceholderText("Height")
    height_input.setFixedWidth(80)
    resize_layout.addWidget(resize_label)
    resize_layout.addWidget(width_input)
    resize_layout.addWidget(QLabel("x"))
    resize_layout.addWidget(height_input)
    resize_layout.addStretch()
    controls_layout.addLayout(resize_layout)

    # Advanced Options
    advanced_layout = QHBoxLayout()
    preserve_exif_check = QCheckBox("Preserve EXIF")
    progressive_check = QCheckBox("Progressive JPEG")
    progressive_check.setChecked(True)
    advanced_layout.addWidget(preserve_exif_check)
    advanced_layout.addWidget(progressive_check)
    controls_layout.addLayout(advanced_layout)

    right_layout.addWidget(controls_frame)

    # Action Buttons
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(8)

    optimize_button = QPushButton("Optimize")
    save_button = QPushButton("Save As")
    reset_button = QPushButton("Reset")

    buttons_layout.addWidget(optimize_button)
    buttons_layout.addWidget(save_button)
    buttons_layout.addWidget(reset_button)

    right_layout.addLayout(buttons_layout)
    splitter.addWidget(right_pane)

    splitter.setSizes([400, 200])

    # --- Bottom Bar (Status) ---
    bottom_bar = QFrame()
    bottom_bar.setFrameShape(QFrame.Shape.NoFrame)
    bottom_bar.setFixedHeight(35)
    bottom_bar.setStyleSheet(
        f"background-color: {COLORS['bg_secondary']}; border-top: 1px solid {COLORS['border_secondary']};"
    )

    bottom_layout = QHBoxLayout(bottom_bar)
    bottom_layout.setContentsMargins(5, 0, 5, 0)

    status_label = QLabel()
    bottom_layout.addWidget(status_label)

    main_layout.addWidget(bottom_bar)

    # State variables
    current_image_path = ""
    optimized_image_path = ""

    def update_status(message: str, is_error: bool = False):
        """Update status bar with message."""
        status_label.setText(message)
        status_label.setStyleSheet(get_status_style("error" if is_error else "info"))

    def clear_preview():
        """Clear image preview and reset controls."""
        nonlocal current_image_path, optimized_image_path
        preview_label.clear()
        current_image_path = ""
        optimized_image_path = ""
        quality_combo.setCurrentIndex(1)  # High (85)
        format_combo.setCurrentIndex(3)  # Auto-detect
        width_input.clear()
        height_input.clear()
        preserve_exif_check.setChecked(False)
        progressive_check.setChecked(True)
        update_status("Ready")

    def load_image(image_path: str):
        """Load image and update preview."""
        nonlocal current_image_path
        try:
            with Image.open(image_path) as img:
                # Apply EXIF orientation if needed
                img = ImageOps.exif_transpose(img)
                preview_image = img.copy()
                preview_image.thumbnail((400, 400), Image.Resampling.LANCZOS)

                # Convert image to compatible format
                if preview_image.mode == "RGBA":
                    # Preserve alpha channel
                    preview_image = preview_image.convert("RGBA")
                    data = preview_image.tobytes("raw", "RGBA")
                    qimage = QImage(
                        data,
                        preview_image.size[0],
                        preview_image.size[1],
                        QImage.Format.Format_RGBA8888,
                    )
                elif preview_image.mode in ("RGB", "L"):
                    # Convert grayscale to RGB and RGB remains RGB
                    if preview_image.mode == "L":
                        preview_image = preview_image.convert("RGB")
                    data = preview_image.tobytes("raw", "RGB")
                    qimage = QImage(
                        data,
                        preview_image.size[0],
                        preview_image.size[1],
                        QImage.Format.Format_RGB888,
                    )
                else:
                    # Convert unsupported modes to RGB
                    preview_image = preview_image.convert("RGB")
                    data = preview_image.tobytes("raw", "RGB")
                    qimage = QImage(
                        data,
                        preview_image.size[0],
                        preview_image.size[1],
                        QImage.Format.Format_RGB888,
                    )

                preview_label.setPixmap(QPixmap.fromImage(qimage))
                current_image_path = image_path
                update_status(f"Loaded: {Path(image_path).name}")
        except Exception as e:
            update_status(f"Error loading image: {e!s}", True)

    def optimize_current_image():
        """Optimize the currently loaded image."""
        nonlocal optimized_image_path
        if not current_image_path:
            update_status("No image loaded", True)
            return

        try:
            quality_preset = optimizer.get_quality_presets()[quality_combo.currentText()]
            format_type = format_combo.currentText() if format_combo.currentText() != "Auto-detect" else None
            max_width = int(width_input.text()) if width_input.text() else None
            max_height = int(height_input.text()) if height_input.text() else None

            success, output_path, error_msg, stats = optimizer.optimize_image(
                input_path=current_image_path,
                quality=quality_preset,
                format_type=format_type,
                max_width=max_width,
                max_height=max_height,
                progressive=progressive_check.isChecked(),
                preserve_exif=preserve_exif_check.isChecked(),
            )

            if success:
                optimized_image_path = output_path
                compression = stats["compression_ratio"]
                update_status(f"Optimized {Path(output_path).name}! Size reduced by {compression:.1f}%")
            else:
                update_status(error_msg, True)

        except ValueError as e:
            update_status(f"Invalid dimensions: {e!s}", True)
        except Exception as e:
            update_status(f"Optimization error: {e!s}", True)

    def save_optimized_image():
        """Save optimized image to specified location."""
        if not optimized_image_path:
            update_status("No optimized image available", True)
            return

        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                try:
                    import shutil

                    shutil.copy2(optimized_image_path, selected_files[0])
                    update_status(f"Saved: {Path(selected_files[0]).name}")
                except Exception as e:
                    update_status(f"Save error: {e!s}", True)

    # Connect button functionality
    upload_button.clicked.connect(lambda: load_image(QFileDialog.getOpenFileName(widget, "Select Image")[0]))
    optimize_button.clicked.connect(optimize_current_image)
    save_button.clicked.connect(save_optimized_image)
    reset_button.clicked.connect(clear_preview)

    return widget


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("Image Optimizer")
    main_window.setGeometry(100, 100, 800, 600)

    central_widget = create_image_optimizer_widget(app.style)
    main_window.setCentralWidget(central_widget)

    main_window.show()
    sys.exit(app.exec())
