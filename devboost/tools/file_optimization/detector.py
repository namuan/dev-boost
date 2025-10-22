import logging
import mimetypes
from pathlib import Path
from typing import ClassVar

from .models import FileInfo

logger = logging.getLogger(__name__)


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
        "image": [
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/webp",
            "image/tiff",
            "image/heic",
            "image/bmp",
        ],
        "video": [
            "video/mp4",
            "video/quicktime",
            "video/avi",
            "video/x-matroska",
            "video/webm",
            "video/x-msvideo",
        ],
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
