import logging
import mimetypes
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QMutex, QObject, pyqtSignal

from .models import BatchOperationResult, BatchProgress, FileInfo
from .settings import OptimizationSettings


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
        # Local import to avoid circular dependencies during module import
        from . import ImageOptimizationEngine, PDFOptimizationEngine, VideoOptimizationEngine

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
            # No backup creation - always create new compressed file

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

                # Determine output path - always create new file with -compressed suffix
                if output_dir:
                    output_path = output_dir / f"{file_path.stem}-compressed{file_path.suffix}"
                else:
                    output_path = file_path.parent / f"{file_path.stem}-compressed{file_path.suffix}"

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
