from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from devboost.styles import COLORS
from devboost.tools.file_optimization.detector import FileTypeDetector

logger = logging.getLogger(__name__)


class FileDropArea(QWidget):
    """
    Custom widget that accepts file drops and displays drop feedback.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("fileDropArea")
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
        self.browse_button.setStyleSheet(
            f"""
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
            """
        )

        layout.addWidget(self.drop_label)
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.browse_button)

        # Set drop area styling
        self.setStyleSheet(
            f"""
            #fileDropArea {{
                border: 2px solid {COLORS["border_primary"]};
                border-radius: 8px;
            }}
            #fileDropArea[dragActive="true"] {{
                border-color: {COLORS["info"]};
            }}
            """
        )

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
