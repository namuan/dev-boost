import time
from dataclasses import dataclass
from pathlib import Path


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
