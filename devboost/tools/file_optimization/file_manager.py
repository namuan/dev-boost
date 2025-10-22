import base64
import logging
import mimetypes
import shutil
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.error import URLError

from .detector import FileTypeDetector
from .models import FileInfo
from .settings import OptimizationSettings

logger = logging.getLogger(__name__)


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
        import os
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
        Process a local file path and return file information.

        Args:
            input_data: Local file path string

        Returns:
            List of FileInfo objects for processed files
        """
        input_data = input_data.strip()
        # Only treat input as a local file path. URL/Base64 inputs are no longer supported.
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
            "images": [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".heic",
                ".tiff",
                ".tif",
                ".webp",
                ".bmp",
            ],
            "videos": [".mov", ".mp4", ".avi", ".mkv", ".webm"],
            "pdfs": [".pdf"],
        }

    def __del__(self):
        """Cleanup temporary files when FileManager is destroyed."""
        self.cleanup_temp_files()
