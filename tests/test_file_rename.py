"""Tests for the file rename tool."""

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication

from devboost.tools.file_rename import (
    FileRenameProcessor,
    FileRenameWorker,
    create_file_rename_widget,
)

logger = logging.getLogger(__name__)


class TestFileRenameProcessor(unittest.TestCase):
    """Test cases for FileRenameProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = FileRenameProcessor()
        self.temp_dir = tempfile.mkdtemp()

        # Create test files
        self.test_files = []
        test_filenames = [
            "Test File 1.txt",
            "Another Test File.pdf",
            "Special Chars éñ.doc",
            "file with spaces.jpg",
            "UPPERCASE.PNG",
        ]

        for filename in test_filenames:
            file_path = Path(self.temp_dir) / filename
            file_path.write_text("test content")
            self.test_files.append(str(file_path))

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_slugify_basic(self):
        """Test basic slugification functionality."""
        test_cases = [
            ("Hello World", "hello-world"),
            ("Test File", "test-file"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("Special!@#$%Chars", "specialchars"),
            ("", ""),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.processor.slugify(input_text)
                self.assertEqual(result, expected)

    def test_transliterate(self):
        """Test transliteration functionality."""
        test_cases = [
            ("café", "cafe"),
            ("naïve", "naive"),
            ("résumé", "resume"),
            ("Москва", "Moskva"),
            ("北京", "Bei Jing"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.processor.transliterate(input_text)
                # Remove trailing spaces that unidecode might add
                result = result.strip()
                self.assertEqual(result, expected)

    def test_generate_numbering_pattern(self):
        """Test numbering pattern generation."""
        # Test with default padding (3)
        result = self.processor.generate_numbering_pattern(0, 10)
        self.assertEqual(result, "001")

        result = self.processor.generate_numbering_pattern(9, 10)
        self.assertEqual(result, "010")

        # Test with custom padding
        result = self.processor.generate_numbering_pattern(0, 10, padding=2)
        self.assertEqual(result, "01")

    def test_generate_date_pattern(self):
        """Test date pattern generation."""
        # Test current date pattern
        result = self.processor.generate_date_pattern("current_date")
        self.assertRegex(result, r"\d{4}-\d{2}-\d{2}")

        # Test current datetime pattern
        result = self.processor.generate_date_pattern("current_datetime")
        self.assertRegex(result, r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}")

    def test_add_files(self):
        """Test adding files to processor."""
        self.processor.add_files(self.test_files)
        self.assertEqual(len(self.processor.files), len(self.test_files))

        # Test that all files are Path objects
        for file_path in self.processor.files:
            self.assertIsInstance(file_path, Path)

    def test_clear_files(self):
        """Test clearing files from processor."""
        self.processor.add_files(self.test_files)
        self.processor.clear_files()
        self.assertEqual(len(self.processor.files), 0)

    def test_generate_preview_slugify(self):
        """Test preview generation with slugify pattern."""
        self.processor.add_files(self.test_files[:3])

        config = {"pattern_type": "slugify"}
        preview = self.processor.generate_preview(config)

        self.assertEqual(len(preview), 3)

        # Check that each preview item has 3 elements (original, new, status)
        for item in preview:
            self.assertEqual(len(item), 3)
            original, new, status = item
            self.assertIsInstance(original, str)
            self.assertIsInstance(new, str)
            self.assertIn(status, ["OK", "CONFLICT", "DUPLICATE"])

    def test_generate_preview_numbering(self):
        """Test preview generation with numbering pattern."""
        self.processor.add_files(self.test_files[:2])

        config = {"pattern_type": "numbering", "prefix": "file", "padding": 3}
        preview = self.processor.generate_preview(config)

        self.assertEqual(len(preview), 2)

        # Check numbering is applied
        _, first_new, _ = preview[0]
        _, second_new, _ = preview[1]
        self.assertTrue(first_new.startswith("file_001"))
        self.assertTrue(second_new.startswith("file_002"))

    def test_generate_preview_date_prefix(self):
        """Test preview generation with date prefix pattern."""
        self.processor.add_files(self.test_files[:1])

        config = {"pattern_type": "date_prefix", "date_pattern": "current_date"}
        preview = self.processor.generate_preview(config)

        self.assertEqual(len(preview), 1)

        _, new_name, _ = preview[0]
        self.assertRegex(new_name, r"\d{4}-\d{2}-\d{2}_")

    def test_execute_rename_dry_run_simulation(self):
        """Test rename execution simulation (without actual file operations)."""
        self.processor.add_files(self.test_files[:2])

        config = {"pattern_type": "slugify"}

        # Test that the method exists and can be called
        success, errors = self.processor.execute_rename(config, create_backup=False)

        # Should return boolean and list
        self.assertIsInstance(success, bool)
        self.assertIsInstance(errors, list)


class TestFileRenameWorker(unittest.TestCase):
    """Test cases for FileRenameWorker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

    def test_worker_initialization(self):
        """Test worker thread initialization."""
        processor = FileRenameProcessor()
        config = {"pattern_type": "slugify"}
        worker = FileRenameWorker(processor, config, create_backup=False)

        self.assertEqual(worker.processor, processor)
        self.assertEqual(worker.pattern_config, config)
        self.assertFalse(worker.create_backup)
        self.assertIsInstance(worker, QThread)


class TestFileRenameWidget(unittest.TestCase):
    """Test cases for the file rename widget creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

    def test_widget_creation(self):
        """Test that the widget is created successfully."""
        widget = create_file_rename_widget()

        self.assertIsNotNone(widget)
        # The widget should have a layout and be properly initialized
        self.assertIsNotNone(widget.layout())

    def test_widget_creation_with_parameters(self):
        """Test widget creation with style and scratch pad parameters."""
        mock_style = MagicMock()
        mock_scratch_pad = MagicMock()

        widget = create_file_rename_widget(mock_style, mock_scratch_pad)

        self.assertIsNotNone(widget)
        self.assertIsNotNone(widget.layout())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
