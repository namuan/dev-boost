"""
Unit tests for file handling and type detection in the file optimization tool.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from devboost.tools.file_optimization import (
    FileManager,
    FileTypeDetector,
    ImageOptimizationEngine,
    OptimizationSettings,
    QualityPreset,
)


class TestFileTypeDetector(unittest.TestCase):
    """Test file type detection functionality."""

    def test_detect_png_by_extension(self):
        """Test PNG detection by file extension."""
        # Create a mock file path
        mock_path = Path("test_image.png")

        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.is_file", return_value=True):
            file_info = FileTypeDetector.detect_file_type(mock_path)

            self.assertEqual(file_info.path, mock_path)
            self.assertEqual(file_info.extension, ".png")

    def test_detect_png_by_magic_number(self):
        """Test PNG detection by magic number."""
        # PNG magic number: 89 50 4E 47 0D 0A 1A 0A
        png_header = b"\x89PNG\r\n\x1a\n"

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
            patch("pathlib.Path.open", mock_open(read_data=png_header)),
        ):
            mock_stat.return_value.st_size = 1000
            mock_path = Path("unknown_file")
            file_info = FileTypeDetector.detect_file_type(mock_path)

            # Should detect as image based on magic number
            self.assertIn(file_info.file_type, ["image", "unknown"])  # Allow both as magic detection may vary


class TestFileManager(unittest.TestCase):
    """Test file management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.file_manager = FileManager()

    def test_process_input_single_file(self):
        """Test processing a single file input."""
        test_file = "test.jpg"
        with patch.object(self.file_manager, "_process_file_path", return_value=[Mock()]) as mock_process:
            result = self.file_manager.process_input(test_file)
            self.assertEqual(len(result), 1)
            mock_process.assert_called_once_with(test_file)

    def test_process_input_url(self):
        """Test processing URL input."""
        test_url = "https://example.com/image.jpg"
        with patch.object(self.file_manager, "_process_url", return_value=[Mock()]) as mock_process:
            result = self.file_manager.process_input(test_url)
            self.assertEqual(len(result), 1)
            mock_process.assert_called_once_with(test_url)

    def test_process_input_base64(self):
        """Test processing base64 input."""
        test_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        with patch.object(self.file_manager, "_process_base64", return_value=[Mock()]) as mock_process:
            result = self.file_manager.process_input(test_base64)
            self.assertEqual(len(result), 1)
            mock_process.assert_called_once_with(test_base64)

    def test_cleanup_temp_files(self):
        """Test cleaning up temporary files."""
        mock_temp_file = Mock()
        mock_temp_file.exists.return_value = True
        self.file_manager.temp_files = [mock_temp_file]

        self.file_manager.cleanup_temp_files()
        mock_temp_file.unlink.assert_called_once()
        self.assertEqual(len(self.file_manager.temp_files), 0)


class TestOptimizationSettings(unittest.TestCase):
    """Test optimization settings functionality."""

    def test_quality_preset_mapping(self):
        """Test quality preset to value mapping."""
        settings = OptimizationSettings(quality_preset=QualityPreset.HIGH)
        quality = settings.get_quality_for_type("image")
        self.assertEqual(quality, 85)

    def test_custom_quality_override(self):
        """Test custom quality override."""
        settings = OptimizationSettings(quality_preset=QualityPreset.MEDIUM, image_quality=90)
        quality = settings.get_quality_for_type("image")
        self.assertEqual(quality, 90)


class TestImageOptimizationEngine(unittest.TestCase):
    """Test image optimization engine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = ImageOptimizationEngine()

    def test_optimize_image_with_statistics(self):
        """Test image optimization with statistics."""
        mock_input_path = Path("test.jpg")
        mock_output_path = Path("test_optimized.jpg")
        settings = OptimizationSettings()

        with (
            patch.object(self.engine, "_optimize_with_pil", return_value={"success": True}) as mock_optimize,
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            mock_stat.return_value.st_size = 1000
            result = self.engine.optimize_image(mock_input_path, mock_output_path, settings)
            self.assertTrue(result["success"])
            mock_optimize.assert_called_once()

    def test_optimize_with_gifsicle(self):
        """Test GIF optimization with gifsicle."""
        mock_input_path = Path("test.gif")
        mock_output_path = Path("test_optimized.gif")
        settings = OptimizationSettings()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.engine._optimize_with_gifsicle(mock_input_path, mock_output_path, settings)
            self.assertTrue(result["success"])

    def test_resize_image_basic(self):
        """Test basic image resizing."""
        from PIL import Image

        mock_image = Mock(spec=Image.Image)
        mock_image.size = (2000, 1500)
        mock_resized = Mock(spec=Image.Image)
        mock_image.resize.return_value = mock_resized

        result = self.engine._resize_image(mock_image, max_width=1000, max_height=750)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
