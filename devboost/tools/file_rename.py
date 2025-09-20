import logging
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from unidecode import unidecode

from devboost.styles import get_tool_style

logger = logging.getLogger(__name__)


class FileRenameProcessor:
    """Backend processor for file renaming operations with various pattern types."""

    def __init__(self):
        self.files: list[Path] = []
        self.rename_operations: list[tuple[Path, Path]] = []
        self.backup_operations: list[tuple[Path, Path]] = []

    def add_files(self, file_paths: list[str]) -> None:
        """Add files to the processing list."""
        logger.info("Adding %d files for processing", len(file_paths))
        self.files = [Path(path) for path in file_paths if Path(path).is_file()]
        logger.debug("Valid files added: %d", len(self.files))

    def clear_files(self) -> None:
        """Clear all files from processing list."""
        logger.info("Clearing all files from processing list")
        self.files.clear()
        self.rename_operations.clear()
        self.backup_operations.clear()

    def slugify(self, text: str) -> str:
        """Convert text to slug format (lowercase, hyphens for spaces/special chars)."""
        # Remove or replace special characters
        text = re.sub(r"[^\w\s-]", "", text.strip())
        # Replace spaces and underscores with hyphens
        text = re.sub(r"[\s_]+", "-", text)
        # Convert to lowercase
        text = text.lower()
        # Remove multiple consecutive hyphens
        text = re.sub(r"-+", "-", text)
        # Remove leading/trailing hyphens
        text = text.strip("-")
        logger.debug("Slugified text: %s", text)
        return text

    def transliterate(self, text: str) -> str:
        """Convert accented characters to ASCII equivalents."""
        result = unidecode(text)
        logger.debug("Transliterated '%s' to '%s'", text, result)
        return result

    def generate_numbering_pattern(self, index: int, total: int, padding: int = 3) -> str:
        """Generate numbered pattern with configurable padding."""
        number = str(index + 1).zfill(padding)
        logger.debug("Generated number pattern: %s", number)
        return number

    def generate_date_pattern(self, pattern_type: str, file_path: Path | None = None) -> str:
        """Generate date pattern based on type."""
        if pattern_type == "current_date":
            date_str = datetime.now().strftime("%Y-%m-%d")
        elif pattern_type == "current_datetime":
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        elif pattern_type == "file_modified" and file_path:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            date_str = mod_time.strftime("%Y-%m-%d")
        elif pattern_type == "file_modified_datetime" and file_path:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            date_str = mod_time.strftime("%Y-%m-%d_%H-%M-%S")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        logger.debug("Generated date pattern: %s", date_str)
        return date_str

    def generate_preview(self, pattern_config: dict) -> list[tuple[str, str, str]]:
        """Generate preview of rename operations without executing them."""
        logger.info("Generating preview for %d files", len(self.files))
        preview_data = []
        conflicts = set()

        for i, file_path in enumerate(self.files):
            original_name = file_path.name
            new_name = self._apply_pattern(file_path, i, len(self.files), pattern_config)

            # Check for conflicts
            status = "OK"
            new_path = file_path.parent / new_name
            if new_path.exists() and new_path != file_path:
                status = "CONFLICT"
                conflicts.add(new_name)
            elif new_name in [item[1] for item in preview_data]:
                status = "DUPLICATE"
                conflicts.add(new_name)

            preview_data.append((original_name, new_name, status))

        logger.info("Preview generated with %d conflicts", len(conflicts))
        return preview_data

    def _apply_pattern(self, file_path: Path, index: int, total: int, config: dict) -> str:
        """Apply the selected pattern to generate new filename."""
        stem = file_path.stem
        suffix = file_path.suffix

        pattern_type = config.get("pattern_type", "slugify")

        if pattern_type == "slugify":
            new_stem = self.slugify(stem)
        elif pattern_type == "transliterate":
            new_stem = self.transliterate(stem)
        elif pattern_type == "numbering":
            padding = config.get("padding", 3)
            prefix = config.get("prefix", "file")
            new_stem = f"{prefix}_{self.generate_numbering_pattern(index, total, padding)}"
        elif pattern_type == "date_prefix":
            date_pattern = config.get("date_pattern", "current_date")
            date_str = self.generate_date_pattern(date_pattern, file_path)
            new_stem = f"{date_str}_{stem}"
        elif pattern_type == "date_suffix":
            date_pattern = config.get("date_pattern", "current_date")
            date_str = self.generate_date_pattern(date_pattern, file_path)
            new_stem = f"{stem}_{date_str}"
        elif pattern_type == "custom":
            find_pattern = config.get("find_pattern", "")
            replace_pattern = config.get("replace_pattern", "")
            new_stem = re.sub(find_pattern, replace_pattern, stem) if find_pattern else stem
        else:
            new_stem = stem

        # Apply additional transformations if enabled
        if config.get("apply_slugify", False) and pattern_type != "slugify":
            new_stem = self.slugify(new_stem)

        if config.get("apply_transliterate", False) and pattern_type != "transliterate":
            new_stem = self.transliterate(new_stem)

        return f"{new_stem}{suffix}"

    def execute_rename(self, pattern_config: dict, create_backup: bool = False) -> tuple[bool, list[str]]:
        """Execute the rename operations with optional backup."""
        logger.info("Executing rename operations for %d files", len(self.files))
        errors = []
        success_count = 0

        try:
            # Generate operations
            operations = []
            for i, file_path in enumerate(self.files):
                new_name = self._apply_pattern(file_path, i, len(self.files), pattern_config)
                new_path = file_path.parent / new_name

                if new_path != file_path:
                    operations.append((file_path, new_path))

            # Create backups if requested
            if create_backup:
                backup_dir = Path.cwd() / "file_rename_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Creating backups in %s", backup_dir)

            # Execute operations
            for original_path, new_path in operations:
                try:
                    if create_backup:
                        backup_path = backup_dir / original_path.name
                        original_path.rename(backup_path)
                        self.backup_operations.append((backup_path, original_path))
                        backup_path.rename(new_path)
                    else:
                        original_path.rename(new_path)

                    success_count += 1
                    logger.debug("Renamed %s to %s", original_path.name, new_path.name)

                except Exception as e:
                    error_msg = f"Failed to rename {original_path.name}: {e!s}"
                    errors.append(error_msg)
                    logger.exception(error_msg)

            logger.info("Rename operation completed: %d successful, %d errors", success_count, len(errors))
            return len(errors) == 0, errors

        except Exception as e:
            error_msg = f"Rename operation failed: {e!s}"
            logger.exception(error_msg)
            return False, [error_msg]

    def rollback_operations(self) -> tuple[bool, list[str]]:
        """Rollback the last rename operations using backups."""
        if not self.backup_operations:
            return False, ["No backup operations available for rollback"]

        logger.info("Rolling back %d operations", len(self.backup_operations))
        errors = []
        success_count = 0

        for backup_path, original_path in reversed(self.backup_operations):
            try:
                if backup_path.exists():
                    backup_path.rename(original_path)
                    success_count += 1
                    logger.debug("Restored %s", original_path.name)
                else:
                    errors.append(f"Backup file not found: {backup_path.name}")
            except Exception as e:
                error_msg = f"Failed to restore {original_path.name}: {e!s}"
                errors.append(error_msg)
                logger.exception(error_msg)

        self.backup_operations.clear()
        logger.info("Rollback completed: %d successful, %d errors", success_count, len(errors))
        return len(errors) == 0, errors


class FileRenameWorker(QThread):
    """Worker thread for file rename operations to prevent UI blocking."""

    progress_updated = pyqtSignal(int)
    operation_completed = pyqtSignal(bool, list)

    def __init__(self, processor: FileRenameProcessor, pattern_config: dict, create_backup: bool = False):
        super().__init__()
        self.processor = processor
        self.pattern_config = pattern_config
        self.create_backup = create_backup

    def run(self):
        """Execute the rename operation in background thread."""
        try:
            success, errors = self.processor.execute_rename(self.pattern_config, self.create_backup)
            self.operation_completed.emit(success, errors)
        except Exception as e:
            logger.exception("Worker thread error")
            self.operation_completed.emit(False, [str(e)])


def create_file_rename_widget(style_func=None, scratch_pad=None) -> QWidget:
    """Create and return the file rename tool widget."""
    logger.info("Creating file rename tool widget")

    widget = QWidget()
    widget.setStyleSheet(get_tool_style())
    layout = QVBoxLayout(widget)

    # Initialize processor
    processor = FileRenameProcessor()

    # File selection section
    file_section = QGroupBox("File Selection")
    file_layout = QVBoxLayout(file_section)

    # File selection controls
    file_controls = QHBoxLayout()
    select_files_btn = QPushButton("Select Files")
    select_folder_btn = QPushButton("Select Folder")
    clear_files_btn = QPushButton("Clear All")
    file_count_label = QLabel("No files selected")

    file_controls.addWidget(select_files_btn)
    file_controls.addWidget(select_folder_btn)
    file_controls.addWidget(clear_files_btn)
    file_controls.addStretch()
    file_controls.addWidget(file_count_label)

    file_layout.addLayout(file_controls)

    # Pattern configuration section
    pattern_section = QGroupBox("Rename Pattern")
    pattern_layout = QVBoxLayout(pattern_section)

    # Pattern type selection
    pattern_type_layout = QHBoxLayout()
    pattern_type_label = QLabel("Pattern Type:")
    pattern_type_combo = QComboBox()
    pattern_type_combo.addItems([
        "Slugify (lowercase, hyphens)",
        "Transliterate (remove accents)",
        "Numbering (sequential)",
        "Date Prefix",
        "Date Suffix",
        "Custom (regex)",
    ])

    pattern_type_layout.addWidget(pattern_type_label)
    pattern_type_layout.addWidget(pattern_type_combo)
    pattern_type_layout.addStretch()

    pattern_layout.addLayout(pattern_type_layout)

    # Pattern-specific options (will be shown/hidden based on selection)
    options_widget = QWidget()
    options_layout = QVBoxLayout(options_widget)

    # Numbering options
    numbering_options = QWidget()
    numbering_layout = QHBoxLayout(numbering_options)
    numbering_layout.addWidget(QLabel("Prefix:"))
    prefix_input = QLineEdit("file")
    numbering_layout.addWidget(prefix_input)
    numbering_layout.addWidget(QLabel("Padding:"))
    padding_spin = QSpinBox()
    padding_spin.setRange(1, 10)
    padding_spin.setValue(3)
    numbering_layout.addWidget(padding_spin)
    numbering_layout.addStretch()

    # Date options
    date_options = QWidget()
    date_layout = QHBoxLayout(date_options)
    date_layout.addWidget(QLabel("Date Type:"))
    date_type_combo = QComboBox()
    date_type_combo.addItems(["Current Date", "Current Date & Time", "File Modified Date", "File Modified Date & Time"])
    date_layout.addWidget(date_type_combo)
    date_layout.addStretch()

    # Custom pattern options
    custom_options = QWidget()
    custom_layout = QVBoxLayout(custom_options)
    find_layout = QHBoxLayout()
    find_layout.addWidget(QLabel("Find Pattern (regex):"))
    find_input = QLineEdit()
    find_layout.addWidget(find_input)
    replace_layout = QHBoxLayout()
    replace_layout.addWidget(QLabel("Replace With:"))
    replace_input = QLineEdit()
    replace_layout.addWidget(replace_input)
    custom_layout.addLayout(find_layout)
    custom_layout.addLayout(replace_layout)

    options_layout.addWidget(numbering_options)
    options_layout.addWidget(date_options)
    options_layout.addWidget(custom_options)

    # Additional options
    additional_options = QHBoxLayout()
    apply_slugify_cb = QCheckBox("Also apply slugify")
    apply_transliterate_cb = QCheckBox("Also apply transliterate")
    additional_options.addWidget(apply_slugify_cb)
    additional_options.addWidget(apply_transliterate_cb)
    additional_options.addStretch()

    pattern_layout.addWidget(options_widget)
    pattern_layout.addLayout(additional_options)

    # Preview section
    preview_section = QGroupBox("Preview")
    preview_layout = QVBoxLayout(preview_section)

    # Preview controls
    preview_controls = QHBoxLayout()
    generate_preview_btn = QPushButton("Generate Preview")
    create_backup_cb = QCheckBox("Create backup before rename")
    create_backup_cb.setChecked(True)

    preview_controls.addWidget(generate_preview_btn)
    preview_controls.addWidget(create_backup_cb)
    preview_controls.addStretch()

    preview_layout.addLayout(preview_controls)

    # Preview table
    preview_table = QTableWidget()
    preview_table.setColumnCount(3)
    preview_table.setHorizontalHeaderLabels(["Original Name", "New Name", "Status"])
    preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    preview_layout.addWidget(preview_table)

    # Action buttons
    action_layout = QHBoxLayout()
    execute_btn = QPushButton("Execute Rename")
    execute_btn.setEnabled(False)
    rollback_btn = QPushButton("Rollback Last Operation")
    rollback_btn.setEnabled(False)

    action_layout.addWidget(execute_btn)
    action_layout.addWidget(rollback_btn)
    action_layout.addStretch()

    preview_layout.addLayout(action_layout)

    # Progress and status
    progress_bar = QProgressBar()
    progress_bar.setVisible(False)
    status_text = QTextEdit()
    status_text.setMaximumHeight(100)
    status_text.setPlaceholderText("Status messages will appear here...")

    # Add all sections to main layout
    layout.addWidget(file_section)
    layout.addWidget(pattern_section)
    layout.addWidget(preview_section)
    layout.addWidget(progress_bar)
    layout.addWidget(status_text)

    # Widget is already styled via main_widget.setStyleSheet(get_tool_style())

    # Helper functions for UI updates
    def update_file_count():
        count = len(processor.files)
        file_count_label.setText(f"{count} files selected")
        generate_preview_btn.setEnabled(count > 0)

    def update_pattern_options():
        # Hide all options first
        numbering_options.setVisible(False)
        date_options.setVisible(False)
        custom_options.setVisible(False)

        # Show relevant options based on selection
        current_text = pattern_type_combo.currentText()
        if "Numbering" in current_text:
            numbering_options.setVisible(True)
        elif "Date" in current_text:
            date_options.setVisible(True)
        elif "Custom" in current_text:
            custom_options.setVisible(True)

    def get_pattern_config() -> dict:
        """Get current pattern configuration from UI."""
        current_text = pattern_type_combo.currentText()

        config = {
            "apply_slugify": apply_slugify_cb.isChecked(),
            "apply_transliterate": apply_transliterate_cb.isChecked(),
        }

        if "Slugify" in current_text:
            config["pattern_type"] = "slugify"
        elif "Transliterate" in current_text:
            config["pattern_type"] = "transliterate"
        elif "Numbering" in current_text:
            config.update({"pattern_type": "numbering", "prefix": prefix_input.text(), "padding": padding_spin.value()})
        elif "Date Prefix" in current_text:
            config.update({
                "pattern_type": "date_prefix",
                "date_pattern": date_type_combo.currentText().lower().replace(" ", "_").replace("&", ""),
            })
        elif "Date Suffix" in current_text:
            config.update({
                "pattern_type": "date_suffix",
                "date_pattern": date_type_combo.currentText().lower().replace(" ", "_").replace("&", ""),
            })
        elif "Custom" in current_text:
            config.update({
                "pattern_type": "custom",
                "find_pattern": find_input.text(),
                "replace_pattern": replace_input.text(),
            })

        return config

    def add_status_message(message: str, is_error: bool = False):
        """Add a status message to the status text area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "ERROR" if is_error else "INFO"
        formatted_message = f"[{timestamp}] {prefix}: {message}"
        status_text.append(formatted_message)
        logger.info(formatted_message)

    # Event handlers
    def select_files():
        file_paths, _ = QFileDialog.getOpenFileNames(widget, "Select Files to Rename", "", "All Files (*.*)")
        if file_paths:
            processor.add_files(file_paths)
            update_file_count()
            add_status_message(f"Selected {len(file_paths)} files")

    def select_folder():
        folder_path = QFileDialog.getExistingDirectory(widget, "Select Folder")
        if folder_path:
            folder = Path(folder_path)
            file_paths = [str(f) for f in folder.iterdir() if f.is_file()]
            processor.add_files(file_paths)
            update_file_count()
            add_status_message(f"Selected {len(file_paths)} files from folder")

    def clear_files():
        processor.clear_files()
        update_file_count()
        preview_table.setRowCount(0)
        execute_btn.setEnabled(False)
        add_status_message("Cleared all files")

    def generate_preview():
        if not processor.files:
            add_status_message("No files selected", True)
            return

        try:
            config = get_pattern_config()
            preview_data = processor.generate_preview(config)

            # Update preview table
            preview_table.setRowCount(len(preview_data))
            has_conflicts = False

            for row, (original, new_name, status) in enumerate(preview_data):
                preview_table.setItem(row, 0, QTableWidgetItem(original))
                preview_table.setItem(row, 1, QTableWidgetItem(new_name))

                status_item = QTableWidgetItem(status)
                if status in ["CONFLICT", "DUPLICATE"]:
                    status_item.setBackground(status_item.background().color().lighter(120))
                    has_conflicts = True

                preview_table.setItem(row, 2, status_item)

            execute_btn.setEnabled(not has_conflicts)

            if has_conflicts:
                add_status_message("Preview generated with conflicts - resolve before executing", True)
            else:
                add_status_message(f"Preview generated successfully for {len(preview_data)} files")

        except Exception as e:
            add_status_message(f"Failed to generate preview: {e!s}", True)

    def execute_rename():
        if not processor.files:
            add_status_message("No files selected", True)
            return

        try:
            config = get_pattern_config()
            create_backup = create_backup_cb.isChecked()

            # Show progress bar
            progress_bar.setVisible(True)
            progress_bar.setRange(0, 0)  # Indeterminate progress
            execute_btn.setEnabled(False)

            # Create and start worker thread
            worker = FileRenameWorker(processor, config, create_backup)

            def on_operation_completed(success: bool, errors: list[str]):
                progress_bar.setVisible(False)
                execute_btn.setEnabled(True)

                if success:
                    add_status_message("Rename operation completed successfully")
                    rollback_btn.setEnabled(create_backup)
                    # Refresh preview to show new state
                    generate_preview()
                else:
                    add_status_message("Rename operation failed", True)
                    for error in errors:
                        add_status_message(error, True)

            worker.operation_completed.connect(on_operation_completed)
            worker.start()

            add_status_message("Starting rename operation...")

        except Exception as e:
            progress_bar.setVisible(False)
            execute_btn.setEnabled(True)
            add_status_message(f"Failed to start rename operation: {e!s}", True)

    def rollback_operation():
        try:
            success, errors = processor.rollback_operations()

            if success:
                add_status_message("Rollback completed successfully")
                rollback_btn.setEnabled(False)
                generate_preview()  # Refresh preview
            else:
                add_status_message("Rollback failed", True)
                for error in errors:
                    add_status_message(error, True)

        except Exception as e:
            add_status_message(f"Rollback operation failed: {e!s}", True)

    # Connect signals
    select_files_btn.clicked.connect(select_files)
    select_folder_btn.clicked.connect(select_folder)
    clear_files_btn.clicked.connect(clear_files)
    pattern_type_combo.currentTextChanged.connect(update_pattern_options)
    generate_preview_btn.clicked.connect(generate_preview)
    execute_btn.clicked.connect(execute_rename)
    rollback_btn.clicked.connect(rollback_operation)

    # Initialize UI state
    update_pattern_options()
    update_file_count()

    logger.info("File rename tool widget created successfully")
    return widget
