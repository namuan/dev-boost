"""
Desktop File Optimization Tool for DevBoost.

This tool provides comprehensive file optimization capabilities for images, videos, and PDFs
with an intuitive drag-and-drop interface, real-time feedback, and seamless desktop integration.
"""

import base64
import json
import logging
import mimetypes
import os
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar
from urllib.error import URLError

from PIL import Image, ImageFile
from PyQt6.QtCore import QMutex, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import COLORS, get_status_style, get_tool_style

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file including type detection results."""

    path: Path
    size: int
    mime_type: str
    file_type: str  # 'image', 'video', 'pdf', 'unknown'
    extension: str
    is_supported: bool
    magic_detected: bool = False


@dataclass
class BatchOperationResult:
    """Result of a batch optimization operation."""

    file_path: Path
    success: bool
    original_size: int = 0
    optimized_size: int = 0
    compression_ratio: float = 0.0
    error_message: str | None = None
    processing_time: float = 0.0
    method_used: str | None = None


@dataclass
class BatchProgress:
    """Progress information for batch operations."""

    total_files: int
    completed_files: int
    current_file: str | None = None
    success_count: int = 0
    error_count: int = 0
    total_original_size: int = 0
    total_optimized_size: int = 0
    start_time: float = 0.0
    current_file_start_time: float = 0.0
    estimated_completion_time: float = 0.0
    average_processing_time: float = 0.0
    current_operation: str = ""
    bytes_processed: int = 0

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100

    @property
    def total_compression_ratio(self) -> float:
        """Calculate total compression ratio."""
        if self.total_original_size == 0:
            return 0.0
        return ((self.total_original_size - self.total_optimized_size) / self.total_original_size) * 100

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time since start."""
        if self.start_time == 0:
            return 0.0
        return time.time() - self.start_time

    @property
    def remaining_time(self) -> float:
        """Estimate remaining time based on current progress."""
        if self.completed_files == 0 or self.total_files == 0:
            return 0.0

        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0

        files_remaining = self.total_files - self.completed_files
        if files_remaining <= 0:
            return 0.0

        time_per_file = elapsed / self.completed_files
        return files_remaining * time_per_file

    @property
    def processing_speed(self) -> float:
        """Calculate processing speed in files per second."""
        elapsed = self.elapsed_time
        if elapsed == 0 or self.completed_files == 0:
            return 0.0
        return self.completed_files / elapsed

    @property
    def bytes_per_second(self) -> float:
        """Calculate processing speed in bytes per second."""
        elapsed = self.elapsed_time
        if elapsed == 0 or self.bytes_processed == 0:
            return 0.0
        return self.bytes_processed / elapsed

    def format_time(self, seconds: float) -> str:
        """Format time in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

    def format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def get_detailed_status(self) -> dict[str, str]:
        """Get detailed status information for display."""
        return {
            "progress": f"{self.completed_files}/{self.total_files} files ({self.progress_percentage:.1f}%)",
            "success_rate": f"{self.success_count}/{self.completed_files}" if self.completed_files > 0 else "0/0",
            "compression": f"{self.total_compression_ratio:.1f}%" if self.total_original_size > 0 else "0%",
            "elapsed": self.format_time(self.elapsed_time),
            "remaining": self.format_time(self.remaining_time) if self.remaining_time > 0 else "Calculating...",
            "speed": f"{self.processing_speed:.1f} files/s" if self.processing_speed > 0 else "0 files/s",
            "data_processed": self.format_size(self.bytes_processed),
            "data_speed": f"{self.format_size(self.bytes_per_second)}/s" if self.bytes_per_second > 0 else "0 B/s",
            "current_file": Path(self.current_file).name if self.current_file else "None",
            "operation": self.current_operation or "Processing",
        }


class QualityPreset(Enum):
    """Quality presets for optimization."""

    MAXIMUM = "maximum"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMUM = "minimum"


@dataclass
class OptimizationSettings:
    """Settings for file optimization operations."""

    # General settings
    quality_preset: QualityPreset = QualityPreset.MEDIUM
    create_backup: bool = True
    preserve_metadata: bool = False

    # Image settings
    image_quality: int | None = None  # Custom quality (0-100)
    max_width: int | None = None
    max_height: int | None = None
    output_format: str | None = None  # Force specific output format
    progressive_jpeg: bool = True

    # Video settings
    video_quality: int | None = None  # Custom quality (0-51 for x264)
    video_bitrate: str | None = None  # e.g., "1M", "500k"
    video_fps: int | None = None

    # PDF settings
    pdf_quality: int | None = None  # Custom quality (0-100)
    pdf_dpi: int | None = None  # DPI for images in PDF

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        data = asdict(self)
        # Convert enum to string
        data["quality_preset"] = self.quality_preset.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationSettings":
        """Create settings from dictionary."""
        # Convert string back to enum
        if "quality_preset" in data:
            data["quality_preset"] = QualityPreset(data["quality_preset"])
        return cls(**data)

    def get_quality_for_type(self, file_type: str) -> int:
        """Get quality value for specific file type based on preset."""
        quality_map = {
            QualityPreset.MAXIMUM: {"image": 95, "video": 18, "pdf": 90},
            QualityPreset.HIGH: {"image": 85, "video": 23, "pdf": 80},
            QualityPreset.MEDIUM: {"image": 75, "video": 28, "pdf": 70},
            QualityPreset.LOW: {"image": 60, "video": 35, "pdf": 60},
            QualityPreset.MINIMUM: {"image": 40, "video": 45, "pdf": 50},
        }

        # Use custom quality if specified
        if file_type == "image" and self.image_quality is not None:
            return self.image_quality
        if file_type == "video" and self.video_quality is not None:
            return self.video_quality
        if file_type == "pdf" and self.pdf_quality is not None:
            return self.pdf_quality

        # Use preset quality
        return quality_map[self.quality_preset].get(file_type, 75)


@dataclass
class OptimizationPreset:
    """Predefined optimization preset with settings and metadata."""

    name: str
    description: str
    settings: OptimizationSettings
    is_builtin: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert preset to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "settings": self.settings.to_dict(),
            "is_builtin": self.is_builtin,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationPreset":
        """Create preset from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            settings=OptimizationSettings.from_dict(data["settings"]),
            is_builtin=data.get("is_builtin", False),
        )


class OptimizationResultsDialog(QDialog):
    """Dialog to display detailed optimization results."""

    def __init__(self, results: list[BatchOperationResult], batch_progress: BatchProgress, parent=None):
        super().__init__(parent)
        self.results = results
        self.batch_progress = batch_progress
        self.setWindowTitle("Optimization Results")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        """Setup the results dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Summary section
        summary_frame = self._create_summary_section()
        layout.addWidget(summary_frame)

        # Results table
        results_table = self._create_results_table()
        layout.addWidget(results_table)

        # Button section
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)

    def _create_summary_section(self) -> QFrame:
        """Create the summary section showing overall statistics."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QGridLayout(frame)
        layout.setSpacing(10)

        # Calculate statistics
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        total_original_size = sum(r.original_size for r in successful)
        total_optimized_size = sum(r.optimized_size for r in successful)
        total_size_reduction = total_original_size - total_optimized_size

        overall_compression = total_size_reduction / total_original_size * 100 if total_original_size > 0 else 0.0

        total_processing_time = sum(r.processing_time for r in self.results)

        # Summary labels
        summary_data = [
            ("Total Files:", f"{len(self.results)}"),
            ("Successful:", f"{len(successful)}"),
            ("Failed:", f"{len(failed)}"),
            ("Success Rate:", f"{len(successful) / len(self.results) * 100:.1f}%" if self.results else "0%"),
            ("Total Original Size:", self.batch_progress.format_size(total_original_size)),
            ("Total Optimized Size:", self.batch_progress.format_size(total_optimized_size)),
            ("Space Saved:", self.batch_progress.format_size(total_size_reduction)),
            ("Compression Ratio:", f"{overall_compression:.1f}%"),
            ("Processing Time:", self.batch_progress.format_time(total_processing_time)),
            (
                "Average Speed:",
                f"{len(self.results) / total_processing_time:.1f} files/s" if total_processing_time > 0 else "N/A",
            ),
        ]

        for i, (label, value) in enumerate(summary_data):
            row, col = divmod(i, 2)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #495057;")

            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: #212529;")

            layout.addWidget(label_widget, row, col * 2)
            layout.addWidget(value_widget, row, col * 2 + 1)

        return frame

    def _create_results_table(self) -> QTableWidget:
        """Create the detailed results table."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "File",
            "Status",
            "Original Size",
            "Optimized Size",
            "Compression",
            "Method",
            "Processing Time",
        ])

        # Set table properties
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)

        # Populate table
        table.setRowCount(len(self.results))

        for row, result in enumerate(self.results):
            # File name
            file_item = QTableWidgetItem(result.file_path.name)
            file_item.setToolTip(str(result.file_path))
            table.setItem(row, 0, file_item)

            # Status
            status_item = QTableWidgetItem("✅ Success" if result.success else "❌ Failed")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if result.success:
                status_item.setBackground(QColor("#d4edda"))
            else:
                status_item.setBackground(QColor("#f8d7da"))
                status_item.setToolTip(result.error_message or "Unknown error")
            table.setItem(row, 1, status_item)

            if result.success:
                # Original size
                original_size_item = QTableWidgetItem(self.batch_progress.format_size(result.original_size))
                original_size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                table.setItem(row, 2, original_size_item)

                # Optimized size
                optimized_size_item = QTableWidgetItem(self.batch_progress.format_size(result.optimized_size))
                optimized_size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                table.setItem(row, 3, optimized_size_item)

                # Compression ratio
                compression = (
                    (result.original_size - result.optimized_size) / result.original_size * 100
                    if result.original_size > 0
                    else 0.0
                )
                compression_item = QTableWidgetItem(f"{compression:.1f}%")
                compression_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Color code compression ratio
                if compression > 20:
                    compression_item.setBackground(QColor("#d4edda"))  # Green for good compression
                elif compression > 5:
                    compression_item.setBackground(QColor("#fff3cd"))  # Yellow for moderate compression
                else:
                    compression_item.setBackground(QColor("#f8d7da"))  # Red for poor compression

                table.setItem(row, 4, compression_item)

                # Method
                method_item = QTableWidgetItem(result.method_used or "Unknown")
                method_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 5, method_item)
            else:
                # Fill empty cells for failed files
                for col in range(2, 6):
                    empty_item = QTableWidgetItem("N/A")
                    empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    empty_item.setForeground(QColor("#6c757d"))
                    table.setItem(row, col, empty_item)

            # Processing time
            time_item = QTableWidgetItem(self.batch_progress.format_time(result.processing_time))
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 6, time_item)

        # Resize columns to content
        table.resizeColumnsToContents()

        # Set minimum column widths
        header = table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setStretchLastSection(True)

        return table

    def _create_button_section(self) -> QHBoxLayout:
        """Create the button section."""
        layout = QHBoxLayout()
        layout.addStretch()

        # Export button
        export_button = QPushButton("Export Results")
        export_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        export_button.clicked.connect(self._export_results)
        layout.addWidget(export_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        layout.addWidget(close_button)

        return layout

    def _export_results(self):
        """Export results to a text file."""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Optimization Results",
            f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if not file_path:
            return

        try:
            with Path(file_path).open("w", encoding="utf-8") as f:
                f.write("File Optimization Results\n")
                f.write("=" * 50 + "\n\n")

                # Summary
                successful = [r for r in self.results if r.success]
                failed = [r for r in self.results if not r.success]

                total_original_size = sum(r.original_size for r in successful)
                total_optimized_size = sum(r.optimized_size for r in successful)
                total_size_reduction = total_original_size - total_optimized_size

                overall_compression = (
                    total_size_reduction / total_original_size * 100 if total_original_size > 0 else 0.0
                )

                total_processing_time = sum(r.processing_time for r in self.results)

                f.write("Summary:\n")
                f.write(f"  Total Files: {len(self.results)}\n")
                f.write(f"  Successful: {len(successful)}\n")
                f.write(f"  Failed: {len(failed)}\n")
                f.write(f"  Success Rate: {len(successful) / len(self.results) * 100:.1f}%\n")
                f.write(f"  Total Original Size: {self.batch_progress.format_size(total_original_size)}\n")
                f.write(f"  Total Optimized Size: {self.batch_progress.format_size(total_optimized_size)}\n")
                f.write(f"  Space Saved: {self.batch_progress.format_size(total_size_reduction)}\n")
                f.write(f"  Compression Ratio: {overall_compression:.1f}%\n")
                f.write(f"  Processing Time: {self.batch_progress.format_time(total_processing_time)}\n\n")

                # Detailed results
                f.write("Detailed Results:\n")
                f.write("-" * 50 + "\n")

                for result in self.results:
                    f.write(f"\nFile: {result.file_path.name}\n")
                    f.write(f"  Status: {'Success' if result.success else 'Failed'}\n")

                    if result.success:
                        compression = (
                            (result.original_size - result.optimized_size) / result.original_size * 100
                            if result.original_size > 0
                            else 0.0
                        )
                        f.write(f"  Original Size: {self.batch_progress.format_size(result.original_size)}\n")
                        f.write(f"  Optimized Size: {self.batch_progress.format_size(result.optimized_size)}\n")
                        f.write(f"  Compression: {compression:.1f}%\n")
                        f.write(f"  Method: {result.method_used or 'Unknown'}\n")
                    else:
                        f.write(f"  Error: {result.error_message or 'Unknown error'}\n")

                    f.write(f"  Processing Time: {self.batch_progress.format_time(result.processing_time)}\n")

            # Show success message
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, "Export Successful", f"Results exported successfully to:\n{file_path}")

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Export Failed", f"Failed to export results:\n{e!s}")


class OptimizationManager(QObject):
    """
    Manager class that coordinates different optimization engines and handles batch operations.

    This class provides a unified interface for optimizing multiple files using the appropriate
    engine (Image, Video, PDF) based on file type. It supports batch processing with progress
    tracking, error handling, and recovery mechanisms.
    """

    # Qt signals for progress tracking
    progress_updated = pyqtSignal(BatchProgress)
    file_started = pyqtSignal(str)  # file path
    file_completed = pyqtSignal(BatchOperationResult)
    batch_completed = pyqtSignal(list)  # list of BatchOperationResult
    error_occurred = pyqtSignal(str, str)  # file path, error message

    def __init__(self):
        """Initialize the optimization manager."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Initialize optimization engines (will be created after their classes are defined)
        self.image_engine = None
        self.video_engine = None
        self.pdf_engine = None

        # Thread management
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        self._is_processing = False
        self._cancel_requested = False
        self._progress_mutex = QMutex()

        # Progress tracking
        self._current_progress = BatchProgress(0, 0)

        self.logger.info("OptimizationManager initialized")

    def initialize_engines(self):
        """Initialize optimization engines after their classes are defined."""
        self.image_engine = ImageOptimizationEngine()
        self.video_engine = VideoOptimizationEngine()
        self.pdf_engine = PDFOptimizationEngine()
        self.logger.info("OptimizationManager engines initialized: Image, Video, PDF")

    def get_file_info(self, file_path: Path) -> FileInfo:
        """
        Get information about a file including type detection.

        Args:
            file_path: Path to the file to analyze

        Returns:
            FileInfo object with file details
        """
        if not file_path.exists():
            return FileInfo(path=file_path, size=0, mime_type="", file_type="unknown", extension="", is_supported=False)

        file_size = file_path.stat().st_size
        file_extension = file_path.suffix.lower()

        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        # Determine file type and support
        file_type = "unknown"
        is_supported = False

        # Check image formats
        if self.image_engine:
            image_formats = self.image_engine.get_supported_formats()
            if file_extension in image_formats["input"]:
                file_type = "image"
                is_supported = True

        # Check video formats
        if self.video_engine and file_extension in self.video_engine.get_supported_formats()["input"]:
            file_type = "video"
            is_supported = self.video_engine._available_tools.get("ffmpeg", False)

        # Check PDF format
        elif file_extension == ".pdf":
            file_type = "pdf"
            is_supported = self.pdf_engine._available_tools.get("ghostscript", False) if self.pdf_engine else False

        return FileInfo(
            path=file_path,
            size=file_size,
            mime_type=mime_type,
            file_type=file_type,
            extension=file_extension,
            is_supported=is_supported,
        )

    def optimize_single_file(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> BatchOperationResult:
        """
        Optimize a single file using the appropriate engine.

        Args:
            input_path: Path to input file
            output_path: Path for output file
            settings: Optimization settings

        Returns:
            BatchOperationResult with optimization details
        """
        start_time = time.time()
        file_info = self.get_file_info(input_path)

        if not file_info.is_supported:
            return BatchOperationResult(
                file_path=input_path,
                success=False,
                original_size=file_info.size,
                error_message=f"Unsupported file type: {file_info.file_type}",
            )

        try:
            # Create backup if requested
            if settings.create_backup and input_path == output_path:
                backup_path = input_path.with_suffix(f"{input_path.suffix}.backup")
                shutil.copy2(input_path, backup_path)
                self.logger.info("Created backup: %s", backup_path)

            # Choose appropriate engine and optimize
            result = None
            method_used = ""

            if file_info.file_type == "image" and self.image_engine:
                result = self.image_engine.optimize_image(input_path, output_path, settings)
                method_used = result.get("method", "image")
            elif file_info.file_type == "video" and self.video_engine:
                result = self.video_engine.optimize_video(input_path, output_path, settings)
                method_used = result.get("method", "video")
            elif file_info.file_type == "pdf" and self.pdf_engine:
                result = self.pdf_engine.optimize_pdf(input_path, output_path, settings)
                method_used = result.get("method", "pdf")

            if not result or not result.get("success", False):
                raise RuntimeError("Optimization failed - no result returned")

            processing_time = time.time() - start_time

            return BatchOperationResult(
                file_path=input_path,
                success=True,
                original_size=result.get("original_size", file_info.size),
                optimized_size=result.get("optimized_size", 0),
                compression_ratio=result.get("compression_ratio", 0.0),
                processing_time=processing_time,
                method_used=method_used,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            self.logger.exception("Failed to optimize %s: %s", input_path, error_msg)

            return BatchOperationResult(
                file_path=input_path,
                success=False,
                original_size=file_info.size,
                error_message=error_msg,
                processing_time=processing_time,
            )

    def optimize_batch(
        self,
        file_paths: list[Path],
        output_dir: Path | None = None,
        settings: OptimizationSettings | None = None,
        progress_callback: Callable[[BatchProgress], None] | None = None,
    ) -> list[BatchOperationResult]:
        """
        Optimize multiple files in batch with enhanced progress tracking.

        Args:
            file_paths: List of input file paths
            output_dir: Optional output directory (if None, files are optimized in place)
            settings: Optimization settings (uses default if None)
            progress_callback: Optional callback for progress updates

        Returns:
            List of BatchOperationResult objects
        """
        if self._is_processing:
            raise RuntimeError("Batch operation already in progress")

        if not file_paths:
            return []

        self._is_processing = True
        self._cancel_requested = False

        if settings is None:
            settings = OptimizationSettings()

        # Initialize enhanced progress tracking
        self._progress_mutex.lock()
        try:
            self._current_progress = BatchProgress(
                total_files=len(file_paths), completed_files=0, start_time=time.time(), current_operation="Initializing"
            )
        finally:
            self._progress_mutex.unlock()

        results = []

        try:
            # Process files with thread pool for better performance
            future_to_path = {}

            for file_path in file_paths:
                if self._cancel_requested:
                    break

                # Determine output path
                output_path = output_dir / file_path.name if output_dir else file_path

                # Submit optimization task
                future = self._thread_pool.submit(
                    self._optimize_file_with_progress, file_path, output_path, settings, progress_callback
                )
                future_to_path[future] = file_path

            # Collect results as they complete
            for future in as_completed(future_to_path):
                if self._cancel_requested:
                    break

                try:
                    result = future.result()
                    results.append(result)

                    # Update enhanced progress tracking
                    self._progress_mutex.lock()
                    try:
                        self._current_progress.completed_files += 1
                        if result.success:
                            self._current_progress.success_count += 1
                            self._current_progress.total_original_size += result.original_size
                            if result.optimized_size:
                                self._current_progress.total_optimized_size += result.optimized_size
                            # Update bytes processed
                            self._current_progress.bytes_processed += result.original_size
                        else:
                            self._current_progress.error_count += 1

                        # Update current operation status
                        remaining_files = self._current_progress.total_files - self._current_progress.completed_files
                        if remaining_files > 0:
                            self._current_progress.current_operation = f"Processing ({remaining_files} remaining)"
                        else:
                            self._current_progress.current_operation = "Completing"

                    finally:
                        self._progress_mutex.unlock()

                    # Emit signals
                    self.file_completed.emit(result)
                    self.progress_updated.emit(self._current_progress)

                    if progress_callback:
                        progress_callback(self._current_progress)

                except Exception as e:
                    self.logger.exception("Error processing file")
                    file_path = future_to_path[future]
                    self.error_occurred.emit(str(file_path), str(e))

        finally:
            self._is_processing = False
            # Final progress update
            self._progress_mutex.lock()
            try:
                self._current_progress.current_operation = "Completed"
            finally:
                self._progress_mutex.unlock()
            self.batch_completed.emit(results)

        return results

    def _optimize_file_with_progress(
        self,
        input_path: Path,
        output_path: Path,
        settings: OptimizationSettings,
        progress_callback: Callable[[BatchProgress], None] | None = None,
    ) -> BatchOperationResult:
        """
        Internal method to optimize a file with enhanced progress tracking.

        Args:
            input_path: Input file path
            output_path: Output file path
            settings: Optimization settings
            progress_callback: Progress callback function

        Returns:
            BatchOperationResult
        """
        # Record start time for this file
        file_start_time = time.time()

        # Emit file started signal
        self.file_started.emit(str(input_path))

        # Update current file in progress with enhanced tracking
        self._progress_mutex.lock()
        try:
            self._current_progress.current_file = str(input_path)
            self._current_progress.current_file_start_time = file_start_time
            self._current_progress.current_operation = f"Optimizing {input_path.name}"
        finally:
            self._progress_mutex.unlock()

        # Perform optimization and measure time
        result = self.optimize_single_file(input_path, output_path, settings)

        # Update result with processing time
        result.processing_time = time.time() - file_start_time

        return result

    def cancel_batch_operation(self):
        """Cancel the current batch operation."""
        self._cancel_requested = True
        self.logger.info("Batch operation cancellation requested")

    def is_processing(self) -> bool:
        """Check if a batch operation is currently in progress."""
        return self._is_processing

    def get_current_progress(self) -> BatchProgress:
        """Get the current batch operation progress."""
        self._progress_mutex.lock()
        try:
            return self._current_progress
        finally:
            self._progress_mutex.unlock()

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get all supported file formats across all engines."""
        formats = {"all_input": []}

        if self.image_engine:
            image_formats = self.image_engine.get_supported_formats()
            formats["image"] = image_formats
            formats["all_input"].extend(image_formats["input"])

        if self.video_engine:
            video_formats = self.video_engine.get_supported_formats()
            formats["video"] = video_formats
            formats["all_input"].extend(video_formats["input"])

        # PDF formats
        formats["pdf"] = {"input": [".pdf"], "output": [".pdf"]}
        formats["all_input"].extend([".pdf"])

        formats["all_input"] = sorted(set(formats["all_input"]))

        return formats

    def get_optimization_info(self) -> dict[str, Any]:
        """Get comprehensive information about optimization capabilities."""
        info = {
            "engines": {},
            "supported_formats": self.get_supported_formats(),
            "thread_pool_size": self._thread_pool._max_workers,
            "is_processing": self._is_processing,
        }

        if self.image_engine:
            info["engines"]["image"] = self.image_engine.get_optimization_info()
        if self.video_engine:
            info["engines"]["video"] = self.video_engine.get_optimization_info()
        if self.pdf_engine:
            info["engines"]["pdf"] = self.pdf_engine.get_optimization_info()

        return info

    def cleanup(self):
        """Clean up resources and shutdown thread pool."""
        self._cancel_requested = True
        self._thread_pool.shutdown(wait=True)
        self.logger.info("OptimizationManager cleanup completed")


class ImageOptimizationEngine:
    """
    Image optimization engine with support for PIL/Pillow, pngquant, jpegoptim, gifsicle, and libvips.

    This class provides a unified interface for optimizing images using various tools and libraries.
    It automatically detects available optimization tools and falls back gracefully when tools are not available.
    """

    def __init__(self):
        """Initialize the image optimization engine."""
        self.logger = logging.getLogger(__name__)
        self._available_tools = self._detect_available_tools()

        # Enable loading of truncated images
        ImageFile.LOAD_TRUNCATED_IMAGES = True

    def _detect_available_tools(self) -> dict[str, bool]:
        """Detect which optimization tools are available on the system."""
        tools = {
            "pil": True,  # PIL/Pillow is always available since it's a dependency
            "pngquant": self._check_command_available("pngquant"),
            "jpegoptim": self._check_command_available("jpegoptim"),
            "gifsicle": self._check_command_available("gifsicle"),
            "libvips": self._check_libvips_available(),
        }

        self.logger.info("Available optimization tools: %s", {tool: status for tool, status in tools.items() if status})
        return tools

    def _check_command_available(self, command: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            # S603: subprocess call with validated input - command is a trusted tool name
            result = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=5)  # noqa: S603
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_libvips_available(self) -> bool:
        """Check if libvips is available."""
        try:
            import importlib.util

            spec = importlib.util.find_spec("pyvips")
            return spec is not None
        except ImportError:
            return False

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported image formats for optimization."""
        formats = {
            "input": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
            "output": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        }

        # Add additional formats if libvips is available
        if self._available_tools.get("libvips", False):
            formats["input"].extend([".svg", ".pdf", ".heic", ".avif"])
            formats["output"].extend([".avif", ".heic"])

        return formats

    def optimize_image(self, input_path: Path, output_path: Path, settings: OptimizationSettings) -> dict[str, Any]:
        """
        Optimize an image using the best available method.

        Args:
            input_path: Path to the input image
            output_path: Path for the optimized output image
            settings: Optimization settings

        Returns:
            Dictionary with optimization results including file sizes and method used
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        original_size = input_path.stat().st_size
        input_ext = input_path.suffix.lower()
        output_path.suffix.lower() if output_path.suffix else input_ext

        self.logger.info("Optimizing image: %s -> %s", input_path, output_path)

        try:
            # Choose optimization method based on format and available tools
            if input_ext == ".png" and self._available_tools.get("pngquant", False):
                result = self._optimize_with_pngquant(input_path, output_path, settings)
            elif input_ext in [".jpg", ".jpeg"] and self._available_tools.get("jpegoptim", False):
                result = self._optimize_with_jpegoptim(input_path, output_path, settings)
            elif input_ext == ".gif" and self._available_tools.get("gifsicle", False):
                result = self._optimize_with_gifsicle(input_path, output_path, settings)
            elif self._available_tools.get("libvips", False):
                result = self._optimize_with_libvips(input_path, output_path, settings)
            else:
                # Fallback to PIL/Pillow
                result = self._optimize_with_pil(input_path, output_path, settings)

            # Calculate compression ratio
            if output_path.exists():
                optimized_size = output_path.stat().st_size
                compression_ratio = (original_size - optimized_size) / original_size * 100
                result.update({
                    "original_size": original_size,
                    "optimized_size": optimized_size,
                    "compression_ratio": compression_ratio,
                    "size_reduction": original_size - optimized_size,
                })

            return result

        except Exception as e:
            self.logger.exception("Failed to optimize image")
            raise RuntimeError(f"Image optimization failed: {e!s}") from e

    def _optimize_with_pil(self, input_path: Path, output_path: Path, settings: OptimizationSettings) -> dict[str, Any]:
        """Optimize image using PIL/Pillow with enhanced format conversion support."""
        self.logger.debug("Using PIL/Pillow for optimization")

        with Image.open(input_path) as img:
            # Handle format-specific conversions
            output_format = output_path.suffix.lower()

            # Convert HEIC/TIFF to appropriate formats with proper color mode handling
            if input_path.suffix.lower() in [".heic", ".tiff", ".tif"]:
                self.logger.info("Converting %s to %s format", input_path.suffix.lower(), output_format)

                # Convert to RGB if needed for JPEG output
                if output_format in [".jpg", ".jpeg"] and img.mode in ["RGBA", "LA", "P"]:
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    # Create white background for transparency
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif output_format == ".png" and img.mode not in ["RGBA", "RGB", "L", "LA"]:
                    # Convert to RGBA for PNG to preserve transparency if present
                    img = img.convert("RGBA")

            # Convert RGBA to RGB if saving as JPEG (existing logic)
            elif output_format in [".jpg", ".jpeg"] and img.mode in ["RGBA", "LA"]:
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background

            # Resize if dimensions are specified
            if settings.max_width or settings.max_height:
                img = self._resize_image(img, settings.max_width, settings.max_height)

            # Prepare save options
            save_kwargs = {}

            if output_format in [".jpg", ".jpeg"]:
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"quality": quality, "optimize": True, "progressive": settings.progressive_jpeg})
            elif output_format == ".png":
                save_kwargs.update({"optimize": True, "compress_level": 9})
            elif output_format == ".webp":
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"quality": quality, "optimize": True})

            # Remove metadata if not preserving
            if not settings.preserve_metadata:
                # Create new image without EXIF data
                img_data = img.getdata()
                img_clean = Image.new(img.mode, img.size)
                img_clean.putdata(img_data)
                img = img_clean

            # Save optimized image
            img.save(output_path, **save_kwargs)

        return {
            "method": "PIL/Pillow",
            "success": True,
            "format": output_format,
            "converted": input_path.suffix.lower() != output_format,
        }

    def _optimize_with_pngquant(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Optimize PNG image using pngquant."""
        self.logger.debug("Using pngquant for PNG optimization")

        quality = settings.get_quality_for_type("image")
        # Convert quality (0-100) to pngquant range (0-100)
        min_quality = max(0, quality - 10)
        max_quality = min(100, quality + 5)

        cmd = [
            "pngquant",
            "--quality",
            "%d-%d" % (min_quality, max_quality),
            "--output",
            str(output_path),
            str(input_path),
        ]

        if not settings.preserve_metadata:
            cmd.append("--strip")

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)  # noqa: S603
            if result.returncode != 0:
                # Fallback to PIL if pngquant fails
                self.logger.warning("pngquant failed, falling back to PIL: %s", result.stderr)
                return self._optimize_with_pil(input_path, output_path, settings)

            return {"method": "pngquant", "success": True, "format": ".png"}
        except subprocess.TimeoutExpired:
            self.logger.warning("pngquant timed out, falling back to PIL")
            return self._optimize_with_pil(input_path, output_path, settings)

    def _optimize_with_jpegoptim(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Optimize JPEG image using jpegoptim."""
        self.logger.debug("Using jpegoptim for JPEG optimization")

        quality = settings.get_quality_for_type("image")

        # Copy file first since jpegoptim modifies in place
        shutil.copy2(input_path, output_path)

        cmd = [
            "jpegoptim",
            "--max=%d" % quality,
            "--strip-all" if not settings.preserve_metadata else "--preserve",
            str(output_path),
        ]

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)  # noqa: S603
            if result.returncode != 0:
                # Fallback to PIL if jpegoptim fails
                self.logger.warning("jpegoptim failed, falling back to PIL: %s", result.stderr)
                return self._optimize_with_pil(input_path, output_path, settings)

            return {"method": "jpegoptim", "success": True, "format": input_path.suffix.lower()}
        except subprocess.TimeoutExpired:
            self.logger.warning("jpegoptim timed out, falling back to PIL")
            return self._optimize_with_pil(input_path, output_path, settings)

    def _optimize_with_gifsicle(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Optimize GIF image using gifsicle."""
        self.logger.debug("Using gifsicle for GIF optimization")

        cmd = [
            "gifsicle",
            "--optimize=3",  # Maximum optimization
            "--output",
            str(output_path),
            str(input_path),
        ]

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)  # noqa: S603
            if result.returncode != 0:
                # Fallback to PIL if gifsicle fails
                self.logger.warning("gifsicle failed, falling back to PIL: %s", result.stderr)
                return self._optimize_with_pil(input_path, output_path, settings)

            return {"method": "gifsicle", "success": True, "format": ".gif"}
        except subprocess.TimeoutExpired:
            self.logger.warning("gifsicle timed out, falling back to PIL")
            return self._optimize_with_pil(input_path, output_path, settings)

    def _optimize_with_libvips(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Optimize image using libvips (pyvips)."""
        self.logger.debug("Using libvips for optimization")

        try:
            import pyvips

            # Load image
            img = pyvips.Image.new_from_file(str(input_path))

            # Resize if dimensions are specified
            if settings.max_width or settings.max_height:
                current_width = img.width
                current_height = img.height

                # Calculate new dimensions maintaining aspect ratio
                if settings.max_width and settings.max_height:
                    scale_w = settings.max_width / current_width
                    scale_h = settings.max_height / current_height
                    scale = min(scale_w, scale_h)
                elif settings.max_width:
                    scale = settings.max_width / current_width
                else:
                    scale = settings.max_height / current_height

                if scale < 1.0:  # Only downscale
                    img = img.resize(scale)

            # Prepare save options
            save_kwargs = {}
            output_format = output_path.suffix.lower()

            if output_format in [".jpg", ".jpeg"]:
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"Q": quality, "optimize_coding": True, "interlace": settings.progressive_jpeg})
            elif output_format == ".png":
                save_kwargs.update({"compression": 9, "interlace": True})
            elif output_format == ".webp":
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"Q": quality, "lossless": quality >= 90})

            # Remove metadata if not preserving
            if not settings.preserve_metadata:
                save_kwargs["strip"] = True

            # Save optimized image
            img.write_to_file(str(output_path), **save_kwargs)

            return {"method": "libvips", "success": True, "format": output_format}

        except Exception as e:
            self.logger.warning("libvips optimization failed, falling back to PIL: %s", str(e))
            return self._optimize_with_pil(input_path, output_path, settings)

    def _resize_image(self, img: Image.Image, max_width: int | None, max_height: int | None) -> Image.Image:
        """Resize image maintaining aspect ratio, supporting both fixed dimensions and percentage scaling."""
        current_width, current_height = img.size

        # Check if percentage-based scaling is active
        if hasattr(self, "resize_percentage") and self.resize_percentage:
            # Use percentage-based scaling
            scale = self.resize_percentage
            new_width = int(current_width * scale)
            new_height = int(current_height * scale)
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate new dimensions using fixed max dimensions
        if max_width and max_height:
            # Fit within both constraints
            scale_w = max_width / current_width
            scale_h = max_height / current_height
            scale = min(scale_w, scale_h)
        elif max_width:
            scale = max_width / current_width
        elif max_height:
            scale = max_height / current_height
        else:
            return img

        if scale < 1.0:  # Only downscale
            new_width = int(current_width * scale)
            new_height = int(current_height * scale)
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def get_optimization_info(self) -> dict[str, Any]:
        """Get information about available optimization tools and capabilities."""
        return {
            "available_tools": self._available_tools,
            "supported_formats": self.get_supported_formats(),
            "recommended_tools": {
                "png": "pngquant" if self._available_tools.get("pngquant") else "PIL",
                "jpeg": "jpegoptim" if self._available_tools.get("jpegoptim") else "PIL",
                "gif": "gifsicle" if self._available_tools.get("gifsicle") else "PIL",
                "webp": "libvips" if self._available_tools.get("libvips") else "PIL",
                "other": "libvips" if self._available_tools.get("libvips") else "PIL",
            },
        }


class VideoOptimizationEngine:
    """
    Video optimization engine with support for ffmpeg and gifski.

    This class provides a unified interface for optimizing videos using ffmpeg for compression
    and format conversion, with special support for high-quality video-to-GIF conversion using gifski.
    """

    def __init__(self):
        """Initialize the video optimization engine."""
        self.logger = logging.getLogger(__name__)
        self._available_tools = self._detect_available_tools()

    def _detect_available_tools(self) -> dict[str, bool]:
        """Detect which video optimization tools are available on the system."""
        tools = {
            "ffmpeg": self._check_command_available("ffmpeg"),
            "ffprobe": self._check_command_available("ffprobe"),
            "gifski": self._check_command_available("gifski"),
        }

        self.logger.info("Available video tools: %s", {tool: status for tool, status in tools.items() if status})
        return tools

    def _check_command_available(self, command: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            # S603: subprocess call with validated input - command is a trusted tool name
            result = subprocess.run([command, "-version"], capture_output=True, text=True, timeout=5)  # noqa: S603
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported video formats for optimization."""
        formats = {
            "input": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"],
            "output": [".mp4", ".webm", ".gif"],
        }

        # Add additional formats if ffmpeg is available
        if self._available_tools.get("ffmpeg", False):
            formats["input"].extend([".3gp", ".asf", ".rm", ".rmvb", ".vob"])
            formats["output"].extend([".avi", ".mkv", ".mov"])

        return formats

    def optimize_video(self, input_path: Path, output_path: Path, settings: OptimizationSettings) -> dict[str, Any]:
        """
        Optimize a video using the best available method.

        Args:
            input_path: Path to the input video
            output_path: Path for the optimized output video
            settings: Optimization settings

        Returns:
            Dictionary with optimization results including file sizes and method used
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        if not self._available_tools.get("ffmpeg", False):
            raise RuntimeError("ffmpeg is required for video optimization but not available")

        original_size = input_path.stat().st_size
        input_ext = input_path.suffix.lower()
        output_ext = output_path.suffix.lower()

        self.logger.info("Optimizing video: %s -> %s", input_path, output_path)

        try:
            # Choose optimization method based on output format
            if output_ext == ".gif":
                result = self._convert_to_gif(input_path, output_path, settings)
            elif input_ext == ".mov" and output_ext == ".mp4":
                result = self._convert_mov_to_mp4(input_path, output_path, settings)
            else:
                result = self._optimize_with_ffmpeg(input_path, output_path, settings)

            # Calculate compression ratio
            if output_path.exists():
                optimized_size = output_path.stat().st_size
                compression_ratio = (original_size - optimized_size) / original_size * 100
                result.update({
                    "original_size": original_size,
                    "optimized_size": optimized_size,
                    "compression_ratio": compression_ratio,
                    "size_reduction": original_size - optimized_size,
                })

            return result

        except Exception as e:
            self.logger.exception("Failed to optimize video")
            raise RuntimeError(f"Video optimization failed: {e!s}") from e

    def _optimize_with_ffmpeg(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Optimize video using ffmpeg with comprehensive settings."""
        self.logger.debug("Using ffmpeg for video optimization")

        # Get video info first
        video_info = self._get_video_info(input_path)

        # Check if input and output paths are the same (in-place editing)
        temp_output = None
        actual_output_path = output_path

        if input_path.resolve() == output_path.resolve():
            # Create temporary output file to avoid FFmpeg in-place editing error
            temp_output = output_path.with_suffix(f".tmp{output_path.suffix}")
            actual_output_path = temp_output
            self.logger.debug("Using temporary output file to avoid in-place editing: %s", temp_output)

        # Build ffmpeg command
        cmd = ["ffmpeg", "-i", str(input_path)]

        # Video codec and quality settings
        output_ext = output_path.suffix.lower()

        if output_ext in [".mp4", ".m4v"]:
            cmd.extend(["-c:v", "libx264"])
            # Use CRF (Constant Rate Factor) for quality
            crf = settings.get_quality_for_type("video")
            cmd.extend(["-crf", str(crf)])

            # Add preset for encoding speed vs compression efficiency
            cmd.extend(["-preset", "medium"])

        elif output_ext == ".webm":
            cmd.extend(["-c:v", "libvpx-vp9"])
            # VP9 uses different quality scale
            crf = settings.get_quality_for_type("video")
            cmd.extend(["-crf", str(crf)])

        # Audio codec
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        # Custom bitrate if specified
        if settings.video_bitrate and settings.video_bitrate != "Auto":
            cmd.extend(["-b:v", settings.video_bitrate])

        # Frame rate if specified
        if settings.video_fps and settings.video_fps > 0:
            cmd.extend(["-r", str(settings.video_fps)])

        # Resolution if specified
        if settings.max_width or settings.max_height:
            scale_filter = self._build_scale_filter(video_info, settings.max_width, settings.max_height)
            if scale_filter:
                cmd.extend(["-vf", scale_filter])

        # Output settings
        cmd.extend(["-movflags", "+faststart"])  # Optimize for web streaming
        cmd.extend(["-y"])  # Overwrite output file
        cmd.append(str(actual_output_path))

        try:
            self.logger.debug("Running ffmpeg command: %s", " ".join(cmd))
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, shell=False)  # noqa: S603

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")

            # If we used a temporary file, replace the original
            if temp_output and temp_output.exists():
                self.logger.debug("Replacing original file with optimized version")
                shutil.move(str(temp_output), str(output_path))

            return {
                "method": "ffmpeg",
                "success": True,
                "format": output_ext,
                "codec": "libx264" if output_ext in [".mp4", ".m4v"] else "libvpx-vp9",
                "converted": input_path.suffix.lower() != output_ext,
            }

        except subprocess.TimeoutExpired as e:
            raise RuntimeError("Video optimization timed out (5 minutes)") from e

    def _convert_mov_to_mp4(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Convert MOV to MP4 with optimization."""
        self.logger.debug("Converting MOV to MP4")

        # Use the general optimization method but ensure MP4 output
        if output_path.suffix.lower() != ".mp4":
            output_path = output_path.with_suffix(".mp4")

        return self._optimize_with_ffmpeg(input_path, output_path, settings)

    def _convert_to_gif(self, input_path: Path, output_path: Path, settings: OptimizationSettings) -> dict[str, Any]:
        """Convert video to GIF using gifski for high quality or ffmpeg as fallback."""
        self.logger.debug("Converting video to GIF")

        if self._available_tools.get("gifski", False):
            return self._convert_to_gif_with_gifski(input_path, output_path, settings)
        return self._convert_to_gif_with_ffmpeg(input_path, output_path, settings)

    def _convert_to_gif_with_gifski(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Convert video to GIF using gifski for high quality."""
        self.logger.debug("Using gifski for high-quality GIF conversion")

        # First extract frames using ffmpeg
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_pattern = Path(temp_dir) / "frame_%04d.png"

            # Extract frames with ffmpeg
            extract_cmd = ["ffmpeg", "-i", str(input_path)]

            # Frame rate for extraction
            fps = settings.video_fps if settings.video_fps and settings.video_fps > 0 else 10
            extract_cmd.extend(["-vf", f"fps={fps}"])

            # Resolution if specified
            video_info = self._get_video_info(input_path)
            if settings.max_width or settings.max_height:
                scale_filter = self._build_scale_filter(video_info, settings.max_width, settings.max_height)
                if scale_filter:
                    # Combine with fps filter
                    extract_cmd[-1] = f"fps={fps},{scale_filter}"

            extract_cmd.extend(["-y", str(frames_pattern)])

            try:
                # S603: subprocess call with validated input - cmd is constructed from trusted sources
                result = subprocess.run(extract_cmd, capture_output=True, text=True, timeout=120, shell=False)  # noqa: S603

                if result.returncode != 0:
                    raise RuntimeError(f"Frame extraction failed: {result.stderr}")

                # Convert frames to GIF with gifski
                gifski_cmd = ["gifski", "-o", str(output_path)]

                # Quality settings for gifski (1-100, higher is better)
                quality = settings.get_quality_for_type("image")  # Use image quality for GIF
                gifski_cmd.extend(["--quality", str(quality)])

                # FPS for gifski
                gifski_cmd.extend(["--fps", str(fps)])

                # Add frame files
                frame_files = sorted(Path(temp_dir).glob("frame_*.png"))
                if not frame_files:
                    raise RuntimeError("No frames were extracted")

                gifski_cmd.extend([str(f) for f in frame_files])

                # S603: subprocess call with validated input - cmd is constructed from trusted sources
                result = subprocess.run(gifski_cmd, capture_output=True, text=True, timeout=180, shell=False)  # noqa: S603

                if result.returncode != 0:
                    raise RuntimeError(f"gifski conversion failed: {result.stderr}")

                return {
                    "method": "gifski",
                    "success": True,
                    "format": ".gif",
                    "fps": fps,
                    "quality": quality,
                    "converted": True,
                }

            except subprocess.TimeoutExpired as e:
                raise RuntimeError("GIF conversion timed out") from e

    def _convert_to_gif_with_ffmpeg(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Convert video to GIF using ffmpeg as fallback."""
        self.logger.debug("Using ffmpeg for GIF conversion (fallback)")

        # Check if input and output paths are the same (in-place editing)
        temp_output = None
        actual_output_path = output_path

        if input_path.resolve() == output_path.resolve():
            # Create temporary output file to avoid FFmpeg in-place editing error
            temp_output = output_path.with_suffix(f".tmp{output_path.suffix}")
            actual_output_path = temp_output
            self.logger.debug("Using temporary output file to avoid in-place editing: %s", temp_output)

        cmd = ["ffmpeg", "-i", str(input_path)]

        # Build filter for GIF conversion
        filters = []

        # Frame rate
        fps = settings.video_fps if settings.video_fps and settings.video_fps > 0 else 10
        filters.append(f"fps={fps}")

        # Resolution
        video_info = self._get_video_info(input_path)
        if settings.max_width or settings.max_height:
            scale_filter = self._build_scale_filter(video_info, settings.max_width, settings.max_height)
            if scale_filter:
                filters.append(scale_filter)

        # Palette generation for better quality
        filters.append("split[s0][s1]")
        filters.append("[s0]palettegen[p]")
        filters.append("[s1][p]paletteuse")

        cmd.extend(["-vf", ",".join(filters)])
        cmd.extend(["-y", str(actual_output_path)])

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, shell=False)  # noqa: S603

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg GIF conversion failed: {result.stderr}")

            # If we used a temporary file, replace the original
            if temp_output and temp_output.exists():
                self.logger.debug("Replacing original file with optimized version")
                shutil.move(str(temp_output), str(output_path))

            return {
                "method": "ffmpeg",
                "success": True,
                "format": ".gif",
                "fps": fps,
                "converted": True,
            }

        except subprocess.TimeoutExpired as e:
            raise RuntimeError("GIF conversion timed out") from e

    def _get_video_info(self, video_path: Path) -> dict[str, Any]:
        """Get video information using ffprobe."""
        if not self._available_tools.get("ffprobe", False):
            return {}

        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video_path)]

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)  # noqa: S603

            if result.returncode == 0:
                info = json.loads(result.stdout)

                # Extract video stream info
                video_stream = None
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break

                if video_stream:
                    return {
                        "width": int(video_stream.get("width", 0)),
                        "height": int(video_stream.get("height", 0)),
                        "duration": float(info.get("format", {}).get("duration", 0)),
                        "fps": eval(video_stream.get("r_frame_rate", "0/1")),  # noqa: S307
                        "codec": video_stream.get("codec_name", "unknown"),
                    }
        except (subprocess.TimeoutExpired, json.JSONDecodeError, ZeroDivisionError):
            pass

        return {}

    def _build_scale_filter(
        self, video_info: dict[str, Any], max_width: int | None, max_height: int | None
    ) -> str | None:
        """Build ffmpeg scale filter maintaining aspect ratio."""
        if not max_width and not max_height:
            return None

        current_width = video_info.get("width", 0)
        current_height = video_info.get("height", 0)

        if not current_width or not current_height:
            # Fallback if we don't have video info
            if max_width and max_height:
                return f"scale={max_width}:{max_height}:force_original_aspect_ratio=decrease"
            if max_width:
                return f"scale={max_width}:-1"
            return f"scale=-1:{max_height}"

        # Calculate new dimensions maintaining aspect ratio
        if max_width and max_height:
            scale_w = max_width / current_width
            scale_h = max_height / current_height
            scale = min(scale_w, scale_h)
        elif max_width:
            scale = max_width / current_width
        else:
            scale = max_height / current_height

        if scale >= 1.0:  # Don't upscale
            return None

        new_width = int(current_width * scale)
        new_height = int(current_height * scale)

        # Ensure dimensions are even (required for some codecs)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)

        return f"scale={new_width}:{new_height}"

    def get_optimization_info(self) -> dict[str, Any]:
        """Get information about available optimization methods."""
        return {
            "available_tools": self._available_tools,
            "supported_formats": self.get_supported_formats(),
            "recommended_methods": {
                "mp4": "ffmpeg" if self._available_tools.get("ffmpeg") else "not_available",
                "webm": "ffmpeg" if self._available_tools.get("ffmpeg") else "not_available",
                "gif": "gifski" if self._available_tools.get("gifski") else "ffmpeg",
                "mov_to_mp4": "ffmpeg" if self._available_tools.get("ffmpeg") else "not_available",
            },
        }


class PDFOptimizationEngine:
    """
    PDF optimization engine with support for ghostscript.

    This class provides a unified interface for optimizing PDF files using ghostscript
    for compression, quality control, and metadata preservation.
    """

    def __init__(self):
        """Initialize the PDF optimization engine."""
        self.logger = logging.getLogger(__name__)
        self._available_tools = self._detect_available_tools()

    def _detect_available_tools(self) -> dict[str, bool]:
        """Detect which PDF optimization tools are available on the system."""
        tools = {
            "ghostscript": self._check_ghostscript_available(),
        }

        self.logger.info("Available PDF tools: %s", {tool: status for tool, status in tools.items() if status})
        return tools

    def _check_ghostscript_available(self) -> bool:
        """Check if ghostscript is available."""
        # Try common ghostscript command names and paths
        gs_commands = ["gs", "ghostscript", "/usr/bin/gs", "/usr/local/bin/gs", "/opt/homebrew/bin/gs"]

        for cmd in gs_commands:
            try:
                # Use 'command -v' to avoid shell aliases
                result = subprocess.run(  # noqa: S603
                    ["sh", "-c", f"command -v {cmd}"],  # noqa: S607
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    # Test if it's actually ghostscript by running version command
                    version_result = subprocess.run(  # noqa: S603
                        [cmd, "--version"], capture_output=True, text=True, timeout=5
                    )
                    if version_result.returncode == 0:
                        self._gs_command = cmd
                        return True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue

        return False

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported PDF formats for optimization."""
        return {
            "input": [".pdf"],
            "output": [".pdf"],
        }

    def optimize_pdf(self, input_path: Path, output_path: Path, settings: OptimizationSettings) -> dict[str, Any]:
        """
        Optimize a PDF using ghostscript.

        Args:
            input_path: Path to the input PDF
            output_path: Path for the optimized output PDF
            settings: Optimization settings

        Returns:
            Dictionary with optimization results including file sizes and method used
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        if not self._available_tools.get("ghostscript", False):
            raise RuntimeError("Ghostscript is required for PDF optimization but not available")

        original_size = input_path.stat().st_size

        self.logger.info("Optimizing PDF: %s -> %s", input_path, output_path)

        try:
            result = self._optimize_with_ghostscript(input_path, output_path, settings)

            # Calculate compression ratio
            if output_path.exists():
                optimized_size = output_path.stat().st_size
                compression_ratio = (original_size - optimized_size) / original_size * 100
                result.update({
                    "original_size": original_size,
                    "optimized_size": optimized_size,
                    "compression_ratio": compression_ratio,
                    "size_reduction": original_size - optimized_size,
                })

            return result

        except Exception as e:
            self.logger.exception("Failed to optimize PDF")
            raise RuntimeError(f"PDF optimization failed: {e!s}") from e

    def _optimize_with_ghostscript(
        self, input_path: Path, output_path: Path, settings: OptimizationSettings
    ) -> dict[str, Any]:
        """Optimize PDF using ghostscript with comprehensive settings."""
        self.logger.debug("Using ghostscript for PDF optimization")

        # Build ghostscript command
        cmd = [self._gs_command]

        # Basic ghostscript options
        cmd.extend([
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/default",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
        ])

        # Quality settings based on preset
        quality = settings.get_quality_for_type("pdf")

        if quality >= 90:
            # Maximum quality - use /prepress
            cmd[cmd.index("-dPDFSETTINGS=/default")] = "-dPDFSETTINGS=/prepress"
        elif quality >= 80:
            # High quality - use /printer
            cmd[cmd.index("-dPDFSETTINGS=/default")] = "-dPDFSETTINGS=/printer"
        elif quality >= 60:
            # Medium quality - use /ebook
            cmd[cmd.index("-dPDFSETTINGS=/default")] = "-dPDFSETTINGS=/ebook"
        else:
            # Low quality - use /screen
            cmd[cmd.index("-dPDFSETTINGS=/default")] = "-dPDFSETTINGS=/screen"

        # Custom DPI if specified
        if settings.pdf_dpi and settings.pdf_dpi > 0:
            cmd.extend([
                f"-dColorImageResolution={settings.pdf_dpi}",
                f"-dGrayImageResolution={settings.pdf_dpi}",
                f"-dMonoImageResolution={settings.pdf_dpi}",
            ])

        # Compression settings
        cmd.extend([
            "-dCompressFonts=true",
            "-dSubsetFonts=true",
            "-dCompressPages=true",
            "-dUseFlateCompression=true",
        ])

        # Metadata preservation
        if settings.preserve_metadata:
            cmd.extend([
                "-dPreserveAnnots=true",
                "-dPreserveMarkedContent=true",
            ])
        else:
            cmd.extend([
                "-dPreserveAnnots=false",
                "-dPreserveMarkedContent=false",
            ])

        # Output file
        cmd.extend([f"-sOutputFile={output_path}", str(input_path)])

        try:
            self.logger.debug("Running ghostscript command: %s", " ".join(cmd))
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, shell=False)  # noqa: S603

            if result.returncode != 0:
                raise RuntimeError(f"Ghostscript failed: {result.stderr}")

            return {
                "method": "ghostscript",
                "success": True,
                "format": ".pdf",
                "quality_setting": quality,
                "dpi": settings.pdf_dpi,
                "metadata_preserved": settings.preserve_metadata,
            }

        except subprocess.TimeoutExpired as e:
            raise RuntimeError("PDF optimization timed out (2 minutes)") from e

    def get_pdf_info(self, pdf_path: Path) -> dict[str, Any]:
        """Get PDF information using ghostscript."""
        if not self._available_tools.get("ghostscript", False):
            return {}

        cmd = [self._gs_command, "-sDEVICE=bbox", "-dNOPAUSE", "-dBATCH", "-dQUIET", str(pdf_path)]

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)  # noqa: S603

            info = {"pages": 0, "has_images": False, "has_fonts": False}

            # Parse ghostscript output for basic info
            if result.stderr:
                lines = result.stderr.split("\n")
                for line in lines:
                    if "Page" in line:
                        info["pages"] += 1

            # Try to get more detailed info with a different approach
            info_cmd = [
                self._gs_command,
                "-sDEVICE=nullpage",
                "-dNOPAUSE",
                "-dBATCH",
                "-dQUIET",
                "-c",
                "currentpagedevice /PageCount get ==",
                str(pdf_path),
            ]

            try:
                info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=15, shell=False)  # noqa: S603
                if info_result.returncode == 0 and info_result.stdout.strip().isdigit():
                    info["pages"] = int(info_result.stdout.strip())
            except (subprocess.TimeoutExpired, ValueError):
                pass

            return info

        except subprocess.TimeoutExpired:
            return {}

    def get_optimization_info(self) -> dict[str, Any]:
        """Get information about available PDF optimization methods."""
        return {
            "available_tools": self._available_tools,
            "supported_formats": self.get_supported_formats(),
            "ghostscript_command": getattr(self, "_gs_command", None),
            "quality_presets": {
                "maximum": "/prepress - Best quality for printing",
                "high": "/printer - High quality for printing",
                "medium": "/ebook - Good quality for screen viewing",
                "low": "/screen - Optimized for web/screen viewing",
            },
        }


class SettingsManager:
    """Manages optimization settings and presets."""

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize settings manager.

        Args:
            config_dir: Optional custom config directory path
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.settings_file = self.config_dir / "optimization_settings.json"
        self.presets_file = self.config_dir / "optimization_presets.json"

        self._ensure_config_dir()
        self._current_settings = OptimizationSettings()
        self._presets: dict[str, OptimizationPreset] = {}

        # Load settings and presets
        self._load_builtin_presets()
        self.load_settings()
        self.load_presets()

    def _get_default_config_dir(self) -> Path:
        """Get the default config directory path using standard OS locations."""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "DevBoost" / "file_optimization"
        elif system == "Windows":
            import os

            appdata = os.environ.get("APPDATA")
            if appdata:
                config_dir = Path(appdata) / "DevBoost" / "file_optimization"
            else:
                config_dir = Path.home() / "AppData" / "Roaming" / "DevBoost" / "file_optimization"
        else:  # Linux and other Unix-like systems
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                config_dir = Path(xdg_config) / "DevBoost" / "file_optimization"
            else:
                config_dir = Path.home() / ".config" / "DevBoost" / "file_optimization"

        return config_dir

    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Config directory ensured: %s", self.config_dir)
        except Exception:
            logger.exception("Failed to create config directory %s", self.config_dir)

    def _load_builtin_presets(self):
        """Load built-in optimization presets."""
        builtin_presets = [
            OptimizationPreset(
                name="Web Optimized",
                description="Optimized for web use with good quality and small file sizes",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.MEDIUM,
                    max_width=1920,
                    max_height=1080,
                    progressive_jpeg=True,
                    create_backup=True,
                ),
            ),
            OptimizationPreset(
                name="Email Friendly",
                description="Small file sizes suitable for email attachments",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.LOW, max_width=1024, max_height=768, create_backup=True
                ),
            ),
            OptimizationPreset(
                name="High Quality",
                description="Minimal compression with maximum quality retention",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.HIGH, preserve_metadata=True, create_backup=True
                ),
            ),
            OptimizationPreset(
                name="Maximum Compression",
                description="Aggressive compression for minimum file sizes",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.MINIMUM, max_width=800, max_height=600, create_backup=True
                ),
            ),
            OptimizationPreset(
                name="Social Media",
                description="Optimized for social media platforms",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.MEDIUM,
                    max_width=1200,
                    max_height=1200,
                    progressive_jpeg=True,
                    create_backup=True,
                ),
            ),
        ]

        for preset in builtin_presets:
            self._presets[preset.name] = preset

    def get_current_settings(self) -> OptimizationSettings:
        """Get current optimization settings."""
        return self._current_settings

    def set_current_settings(self, settings: OptimizationSettings):
        """Set current optimization settings."""
        self._current_settings = settings

    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            with self.settings_file.open("w") as f:
                json.dump(self._current_settings.to_dict(), f, indent=2)
            logger.info("Settings saved to %s", self.settings_file)
            return True
        except Exception:
            logger.exception("Failed to save settings")
            return False

    def load_settings(self) -> bool:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with self.settings_file.open() as f:
                    data = json.load(f)
                self._current_settings = OptimizationSettings.from_dict(data)
                logger.info("Settings loaded from %s", self.settings_file)
                return True
        except Exception:
            logger.exception("Failed to load settings")

        # Use default settings if loading fails
        self._current_settings = OptimizationSettings()
        return False

    def get_presets(self) -> dict[str, OptimizationPreset]:
        """Get all available presets."""
        return self._presets.copy()

    def get_preset(self, name: str) -> OptimizationPreset | None:
        """Get a specific preset by name."""
        return self._presets.get(name)

    def add_preset(self, preset: OptimizationPreset) -> bool:
        """Add a new preset."""
        try:
            self._presets[preset.name] = preset
            return self.save_presets()
        except Exception:
            logger.exception("Failed to add preset {preset.name}")
            return False

    def remove_preset(self, name: str) -> bool:
        """Remove a preset (only custom presets can be removed)."""
        try:
            if name in self._presets:
                preset = self._presets[name]
                if not preset.is_builtin:
                    del self._presets[name]
                    return self.save_presets()
                logger.warning("Cannot remove builtin preset: %s", name)
                return False
            return True
        except Exception:
            logger.exception("Failed to remove preset {name}")
            return False

    def save_presets(self) -> bool:
        """Save custom presets to file."""
        try:
            # Only save custom presets
            custom_presets = {name: preset.to_dict() for name, preset in self._presets.items() if not preset.is_builtin}

            with self.presets_file.open("w") as f:
                json.dump(custom_presets, f, indent=2)
            logger.info("Custom presets saved to %s", self.presets_file)
            return True
        except Exception:
            logger.exception("Failed to save presets")
            return False

    def load_presets(self) -> bool:
        """Load custom presets from file."""
        try:
            if self.presets_file.exists():
                with self.presets_file.open() as f:
                    data = json.load(f)

                for name, preset_data in data.items():
                    preset = OptimizationPreset.from_dict(preset_data)
                    preset.is_builtin = False  # Ensure loaded presets are marked as custom
                    self._presets[name] = preset

                logger.info("Custom presets loaded from %s", self.presets_file)
                return True
        except Exception:
            logger.exception("Failed to load custom presets")

        return False

    def apply_preset(self, preset_name: str) -> bool:
        """Apply a preset to current settings."""
        preset = self.get_preset(preset_name)
        if preset:
            self._current_settings = OptimizationSettings.from_dict(preset.settings.to_dict())
            return True
        return False

    def validate_settings(self, settings: OptimizationSettings) -> list[str]:
        """
        Validate optimization settings and return list of errors.

        Args:
            settings: Settings to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate image quality
        if settings.image_quality is not None and not (0 <= settings.image_quality <= 100):
            errors.append("Image quality must be between 0 and 100")

        # Validate video quality (x264 CRF scale)
        if settings.video_quality is not None and not (0 <= settings.video_quality <= 51):
            errors.append("Video quality must be between 0 and 51")

        # Validate PDF quality
        if settings.pdf_quality is not None and not (0 <= settings.pdf_quality <= 100):
            errors.append("PDF quality must be between 0 and 100")

        # Validate dimensions
        if settings.max_width is not None and settings.max_width <= 0:
            errors.append("Maximum width must be positive")

        if settings.max_height is not None and settings.max_height <= 0:
            errors.append("Maximum height must be positive")

        # Validate video FPS
        if settings.video_fps is not None and settings.video_fps <= 0:
            errors.append("Video FPS must be positive")

        # Validate PDF DPI
        if settings.pdf_dpi is not None and not (72 <= settings.pdf_dpi <= 600):
            errors.append("PDF DPI must be between 72 and 600")

        # Validate video bitrate format
        if settings.video_bitrate is not None:
            import re

            if not re.match(r"^\d+[kKmM]?$", settings.video_bitrate):
                errors.append("Video bitrate must be in format like '1M', '500k', or '1000'")

        return errors


class FileTypeDetector:
    """
    Detects file types using both extension and magic number analysis.
    """

    # Magic number signatures for common file types
    MAGIC_SIGNATURES: ClassVar[dict[bytes, str]] = {
        # Images
        b"\x89PNG\r\n\x1a\n": "image/png",
        b"\xff\xd8\xff": "image/jpeg",
        b"GIF87a": "image/gif",
        b"GIF89a": "image/gif",
        b"RIFF": "image/webp",  # WebP files start with RIFF, need special handling
        b"II*\x00": "image/tiff",  # TIFF little-endian
        b"MM\x00*": "image/tiff",  # TIFF big-endian
        b"\x00\x00\x00\x18ftypheic": "image/heic",  # HEIC (offset 4)
        b"\x00\x00\x00\x20ftypheic": "image/heic",  # HEIC variant
        # Videos
        b"\x00\x00\x00\x18ftyp": "video/mp4",  # MP4
        b"\x00\x00\x00\x20ftyp": "video/mp4",  # MP4 variant
        b"\x1aE\xdf\xa3": "video/x-matroska",  # MKV
        # PDFs
        b"%PDF": "application/pdf",
    }

    # File type categories based on MIME types
    TYPE_CATEGORIES: ClassVar[dict[str, list[str]]] = {
        "image": ["image/png", "image/jpeg", "image/gif", "image/webp", "image/tiff", "image/heic", "image/bmp"],
        "video": ["video/mp4", "video/quicktime", "video/avi", "video/x-matroska", "video/webm", "video/x-msvideo"],
        "pdf": ["application/pdf"],
    }

    # Supported file extensions
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        # Images
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".heic",
        ".tiff",
        ".tif",
        ".webp",
        ".bmp",
        # Videos
        ".mov",
        ".mp4",
        ".avi",
        ".mkv",
        ".webm",
        # PDFs
        ".pdf",
    }

    @classmethod
    def detect_file_type(cls, file_path: Path) -> FileInfo:
        """
        Detect file type using both extension and magic number analysis.

        Args:
            file_path: Path to the file to analyze

        Returns:
            FileInfo object with detection results
        """
        try:
            # Get basic file info
            size = file_path.stat().st_size if file_path.exists() else 0
            extension = file_path.suffix.lower()

            # Initialize with extension-based detection
            mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            magic_detected = False

            # Try magic number detection if file exists
            if file_path.exists() and size > 0:
                detected_mime = cls._detect_by_magic_number(file_path)
                if detected_mime:
                    mime_type = detected_mime
                    magic_detected = True

            # Determine file category
            file_type = cls._get_file_category(mime_type)

            # Check if file is supported
            is_supported = extension in cls.SUPPORTED_EXTENSIONS

            return FileInfo(
                path=file_path,
                size=size,
                mime_type=mime_type,
                file_type=file_type,
                extension=extension,
                is_supported=is_supported,
                magic_detected=magic_detected,
            )

        except Exception:
            logger.exception("Error detecting file type for {file_path}")
            return FileInfo(
                path=file_path,
                size=0,
                mime_type="application/octet-stream",
                file_type="unknown",
                extension=file_path.suffix.lower() if file_path.suffix else "",
                is_supported=False,
                magic_detected=False,
            )

    @classmethod
    def _detect_by_magic_number(cls, file_path: Path) -> str | None:
        """
        Detect file type by reading magic numbers from file header.

        Args:
            file_path: Path to the file to analyze

        Returns:
            MIME type if detected, None otherwise
        """
        try:
            with Path(file_path).open("rb") as f:
                # Read first 32 bytes for magic number detection
                header = f.read(32)

                # Check for exact matches first
                for magic_bytes, mime_type in cls.MAGIC_SIGNATURES.items():
                    if header.startswith(magic_bytes):
                        # Special handling for RIFF files (WebP vs AVI)
                        if magic_bytes == b"RIFF" and len(header) >= 12:
                            # Check RIFF subtype
                            if header[8:12] == b"WEBP":
                                return "image/webp"
                            if header[8:12] == b"AVI ":
                                return "video/avi"
                        # Special handling for HEIC files (check at offset 4)
                        elif b"ftypheic" in magic_bytes and len(header) >= 12:
                            if b"heic" in header[4:12]:
                                return "image/heic"
                        else:
                            return mime_type

                # Check for patterns at specific offsets
                if len(header) >= 12 and header[4:12] == b"ftypheic":
                    return "image/heic"

        except Exception as e:
            logger.debug("Could not read magic number from {file_path}: %s", e)

        return None

    @classmethod
    def _get_file_category(cls, mime_type: str) -> str:
        """
        Get file category based on MIME type.

        Args:
            mime_type: MIME type string

        Returns:
            File category ('image', 'video', 'pdf', 'unknown')
        """
        for category, mime_types in cls.TYPE_CATEGORIES.items():
            if mime_type in mime_types:
                return category
        return "unknown"

    @classmethod
    def is_supported_file(cls, file_path: Path) -> bool:
        """
        Check if a file is supported for optimization.

        Args:
            file_path: Path to check

        Returns:
            True if file is supported, False otherwise
        """
        return file_path.suffix.lower() in cls.SUPPORTED_EXTENSIONS


class FileManager:
    """
    Manages file I/O operations, path management, and backup system.
    """

    def __init__(self, backup_dir: Path | None = None):
        """
        Initialize FileManager.

        Args:
            backup_dir: Optional custom backup directory path
        """
        self.logger = logging.getLogger(__name__)
        self.backup_dir = backup_dir or self._get_default_backup_dir()
        self.temp_files: list[Path] = []
        self._ensure_backup_dir()

    def _get_default_backup_dir(self) -> Path:
        """Get the default backup directory path using standard OS locations."""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            backup_dir = Path.home() / "Library" / "Application Support" / "DevBoost" / "file_optimization_backups"
        elif system == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                backup_dir = Path(appdata) / "DevBoost" / "file_optimization_backups"
            else:
                backup_dir = Path.home() / "AppData" / "Roaming" / "DevBoost" / "file_optimization_backups"
        else:  # Linux and other Unix-like systems
            xdg_data = os.environ.get("XDG_DATA_HOME")
            if xdg_data:
                backup_dir = Path(xdg_data) / "DevBoost" / "file_optimization_backups"
            else:
                backup_dir = Path.home() / ".local" / "share" / "DevBoost" / "file_optimization_backups"

        return backup_dir

    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Backup directory ensured: %s", self.backup_dir)
        except Exception:
            logger.exception("Failed to create backup directory {self.backup_dir}")

    def process_input(self, input_data: str) -> list[FileInfo]:
        """
        Process various input types and return file information.

        Args:
            input_data: Can be file path, URL, or base64 encoded data

        Returns:
            List of FileInfo objects for processed files
        """
        input_data = input_data.strip()

        # Check if it's a URL
        if self._is_url(input_data):
            return self._process_url(input_data)

        # Check if it's base64 data
        if self._is_base64_image(input_data):
            return self._process_base64(input_data)

        # Treat as file path
        return self._process_file_path(input_data)

    def _is_url(self, data: str) -> bool:
        """Check if the input is a URL."""
        try:
            result = urllib.parse.urlparse(data)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _is_base64_image(self, data: str) -> bool:
        """Check if the input is base64 encoded image data."""
        # Check for data URL format
        if data.startswith("data:image/"):
            return True

        # Check for plain base64 (basic validation)
        if len(data) > 50:  # Reduced minimum length
            try:
                # Try to decode the entire string to validate
                base64.b64decode(data, validate=True)
                return True
            except Exception:
                self.logger.debug("Invalid base64 data detected")

        return False

    def _process_file_path(self, file_path: str) -> list[FileInfo]:
        """Process a file path input."""
        try:
            path = Path(file_path).resolve()
            if path.exists() and path.is_file():
                file_info = FileTypeDetector.detect_file_type(path)
                return [file_info]
            logger.warning("File not found: %s", file_path)
            return []
        except Exception:
            logger.exception("Error processing file path {file_path}")
            return []

    def _process_url(self, url: str) -> list[FileInfo]:
        """Process a URL input by downloading the file."""
        try:
            # Validate URL scheme for security
            parsed_url = urllib.parse.urlparse(url)
            if parsed_url.scheme not in ("http", "https"):
                logger.warning("Unsupported URL scheme: %s", parsed_url.scheme)
                return []

            # Try to get file extension from URL
            url_path = parsed_url.path
            extension = Path(url_path).suffix if url_path else ""

            # Create temporary file with extension if available
            temp_file = self._create_temp_file(suffix=extension)

            # Download file
            # S310: URL open with validated scheme - only http/https schemes are allowed above
            with urllib.request.urlopen(url, timeout=30) as response, Path(temp_file).open("wb") as f:  # noqa: S310
                shutil.copyfileobj(response, f)

            # Detect file type
            file_info = FileTypeDetector.detect_file_type(temp_file)

            # Add to temp files for cleanup
            self.temp_files.append(temp_file)

            logger.info("Downloaded file from URL: {url} -> %s", temp_file)
            return [file_info]

        except URLError:
            logger.exception("Failed to download from URL {url}")
            return []
        except Exception:
            logger.exception("Error processing URL {url}")
            return []

    def _process_base64(self, base64_data: str) -> list[FileInfo]:
        """Process base64 encoded data."""
        try:
            # Handle data URL format
            if base64_data.startswith("data:"):
                # Extract MIME type and data
                header, data = base64_data.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]

                # Determine file extension from MIME type
                extension = mimetypes.guess_extension(mime_type) or ".bin"
            else:
                # Plain base64 data, assume image
                data = base64_data
                extension = ".png"  # Default to PNG
                mime_type = "image/png"

            # Decode base64 data
            file_data = base64.b64decode(data)

            # Create temporary file
            temp_file = self._create_temp_file(suffix=extension)

            # Write decoded data
            with Path(temp_file).open("wb") as f:
                f.write(file_data)

            # Detect file type (this will override our assumptions with actual detection)
            file_info = FileTypeDetector.detect_file_type(temp_file)

            # Add to temp files for cleanup
            self.temp_files.append(temp_file)

            logger.info("Processed base64 data -> %s", temp_file)
            return [file_info]

        except Exception:
            logger.exception("Error processing base64 data")
            return []

    def _create_temp_file(self, suffix: str = "") -> Path:
        """Create a temporary file and return its path."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="devboost_opt_")
        # Close the file descriptor as we only need the path
        import os

        os.close(temp_fd)
        return Path(temp_path)

    def create_backup(self, file_path: Path) -> Path | None:
        """
        Create a backup copy of the original file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            if not file_path.exists():
                logger.warning("Cannot backup non-existent file: %s", file_path)
                return None

            # Create backup filename with timestamp
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name

            # Copy file to backup location
            shutil.copy2(file_path, backup_path)

            logger.info("Created backup: {file_path} -> %s", backup_path)
            return backup_path

        except Exception:
            logger.exception("Failed to create backup for {file_path}")
            return None

    def generate_output_path(
        self, input_path: Path, suffix: str = "_optimized", settings: OptimizationSettings | None = None
    ) -> Path:
        """
        Generate output path for optimized file with automatic format conversion.

        Args:
            input_path: Original file path
            suffix: Suffix to add to filename
            settings: Optimization settings to determine output format

        Returns:
            Path for the optimized file
        """
        parent = input_path.parent
        stem = input_path.stem
        original_extension = input_path.suffix.lower()

        # Determine output extension based on settings and automatic conversion rules
        output_extension = self._determine_output_extension(original_extension, settings)

        output_name = f"{stem}{suffix}{output_extension}"
        return parent / output_name

    def _determine_output_extension(self, input_extension: str, settings: OptimizationSettings | None = None) -> str:
        """
        Determine the output file extension based on input format and settings.

        Args:
            input_extension: Original file extension (lowercase)
            settings: Optimization settings

        Returns:
            Output file extension
        """
        # If explicit output format is specified in settings
        if settings and settings.output_format:
            format_map = {"jpeg": ".jpg", "jpg": ".jpg", "png": ".png", "webp": ".webp"}
            return format_map.get(settings.output_format.lower(), input_extension)

        # Automatic format conversion rules
        conversion_rules = {
            ".heic": ".jpg",  # HEIC → JPEG (most compatible)
            ".tiff": ".png",  # TIFF → PNG (lossless conversion)
            ".tif": ".png",  # TIF → PNG (lossless conversion)
            ".bmp": ".png",  # BMP → PNG (better compression)
        }

        return conversion_rules.get(input_extension, input_extension)

    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug("Cleaned up temp file: %s", temp_file)
            except Exception as e:
                logger.warning("Failed to clean up temp file {temp_file}: %s", e)

        self.temp_files.clear()

    def get_backup_folder_path(self) -> Path:
        """Get the backup folder path."""
        return self.backup_dir

    def list_backup_files(self) -> list[tuple[Path, dict[str, str | int]]]:
        """
        List all backup files with metadata.

        Returns:
            List of tuples containing (file_path, metadata_dict)
        """
        backup_files = []

        try:
            if not self.backup_dir.exists():
                return backup_files

            for backup_file in self.backup_dir.iterdir():
                if backup_file.is_file():
                    try:
                        stat = backup_file.stat()
                        metadata = {
                            "size": stat.st_size,
                            "created": stat.st_ctime,
                            "modified": stat.st_mtime,
                            "name": backup_file.name,
                        }
                        backup_files.append((backup_file, metadata))
                    except Exception as e:
                        logger.warning("Error getting metadata for {backup_file}: %s", e)

            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x[1]["created"], reverse=True)

        except Exception:
            logger.exception("Error listing backup files")

        return backup_files

    def get_supported_formats(self) -> dict[str, list[str]]:
        """
        Get dictionary of supported file formats by category.

        Returns:
            Dictionary mapping categories to lists of extensions
        """
        return {
            "images": [".png", ".jpg", ".jpeg", ".gif", ".heic", ".tiff", ".tif", ".webp", ".bmp"],
            "videos": [".mov", ".mp4", ".avi", ".mkv", ".webm"],
            "pdfs": [".pdf"],
        }

    def __del__(self):
        """Cleanup temporary files when FileManager is destroyed."""
        self.cleanup_temp_files()


class FileDropArea(QWidget):
    """
    Custom widget that accepts file drops and displays drop feedback.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setup_ui()

    def setup_ui(self):
        """Setup the drop area UI."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        # Drop icon and text
        self.drop_label = QLabel("📁")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("font-size: 48px; color: #999;")

        self.instruction_label = QLabel("Drag and drop files here\nor click to browse")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setStyleSheet(f"font-size: 14px; color: {COLORS['text_muted']};")

        self.browse_button = QPushButton("Browse Files")
        self.browse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["btn_bg"]};
                border: 2px dashed {COLORS["border_primary"]};
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
                border-color: {COLORS["info"]};
            }}
        """)

        layout.addWidget(self.drop_label)
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.browse_button)

        # Set drop area styling
        self.setStyleSheet(f"""
            FileDropArea {{
                background-color: {COLORS["bg_secondary"]};
                border: 2px dashed {COLORS["border_primary"]};
                border-radius: 8px;
            }}
            FileDropArea[dragActive="true"] {{
                border-color: {COLORS["info"]};
                background-color: {COLORS["bg_tertiary"]};
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any of the URLs are files we can handle
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.is_file() and self._is_supported_file(file_path):
                        event.acceptProposedAction()
                        self.setProperty("dragActive", True)
                        self.style().polish(self)
                        return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        self.setProperty("dragActive", False)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        self.setProperty("dragActive", False)
        self.style().polish(self)

        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.is_file() and self._is_supported_file(file_path):
                        file_paths.append(str(file_path))

            if file_paths:
                self.handle_files_dropped(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if the file type is supported."""
        return FileTypeDetector.is_supported_file(file_path)

    def handle_files_dropped(self, file_paths: list[str]):
        """Handle dropped files. Override in subclass."""
        logger.info("Files dropped: %s", file_paths)


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

        # File drop area
        self.drop_area = FileDropArea()
        self.drop_area.handle_files_dropped = self.handle_files_dropped
        self.drop_area.browse_button.clicked.connect(self.browse_files)

        left_layout.addWidget(self.drop_area)

        # URL/Base64 input area
        self.input_frame = QFrame()
        self.input_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
            }}
        """)

        input_layout = QVBoxLayout(self.input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)

        input_label = QLabel("Or paste URL/Base64 data:")
        input_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        input_layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(80)
        self.input_text.setPlaceholderText("Paste file URL or base64 encoded data here...")
        self.input_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS["text_primary"]};
                font-family: monospace;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS["info"]};
            }}
        """)
        input_layout.addWidget(self.input_text)

        input_button_layout = QHBoxLayout()
        self.process_input_button = QPushButton("Process Input")
        self.process_input_button.clicked.connect(self.process_text_input)
        self.process_input_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["btn_bg"]};
                border: 1px solid {COLORS["border_primary"]};
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
        """)

        self.clear_input_button = QPushButton("Clear")
        self.clear_input_button.clicked.connect(lambda: self.input_text.clear())
        self.clear_input_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border_secondary"]};
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["btn_hover"]};
            }}
        """)

        input_button_layout.addWidget(self.process_input_button)
        input_button_layout.addWidget(self.clear_input_button)
        input_button_layout.addStretch()
        input_layout.addLayout(input_button_layout)

        left_layout.addWidget(self.input_frame)

        # File list area (for batch processing)
        self.file_list_frame = QFrame()
        self.file_list_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.file_list_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 6px;
            }}
        """)
        self.file_list_frame.hide()  # Initially hidden

        file_list_layout = QVBoxLayout(self.file_list_frame)
        file_list_layout.setContentsMargins(10, 10, 10, 10)

        self.file_list_label = QLabel("Files to Process:")
        self.file_list_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        file_list_layout.addWidget(self.file_list_label)

        # Placeholder for file list items
        self.file_list_container = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_container)
        self.file_list_layout.setContentsMargins(0, 0, 0, 0)
        self.file_list_layout.setSpacing(5)
        file_list_layout.addWidget(self.file_list_container)

        left_layout.addWidget(self.file_list_frame)

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

        # Create backup checkbox
        self.create_backup_checkbox = QCheckBox("Create backup of original files")
        self.create_backup_checkbox.setChecked(True)
        self.create_backup_checkbox.stateChanged.connect(self._on_settings_changed)
        self.create_backup_checkbox.setStyleSheet(f"""
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

        layout.addWidget(self.create_backup_checkbox)

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

        # Hide file list frame
        self.file_list_frame.hide()

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
        settings.create_backup = self.create_backup_checkbox.isChecked()
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
        self.create_backup_checkbox.setChecked(settings.create_backup)
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
