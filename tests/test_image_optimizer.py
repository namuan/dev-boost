import tempfile
import unittest
from pathlib import Path

from PIL import Image

from devboost.tools.image_optimizer import ImageOptimizer


class TestImageOptimizer(unittest.TestCase):
    """Test cases for the ImageOptimizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = ImageOptimizer()

        # Create a test image
        self.test_image = Image.new("RGB", (800, 600), color="red")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            self.temp_input_name = tmp_file.name
        self.test_image.save(self.temp_input_name, "JPEG")

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        temp_path = Path(self.temp_input_name)
        if temp_path.exists():
            temp_path.unlink()

    def test_optimize_image_basic(self):
        """Test basic image optimization."""
        success, output_path, _error_msg, stats = self.optimizer.optimize_image(
            input_path=self.temp_input_name, quality=85
        )

        self.assertTrue(success)
        self.assertTrue(Path(output_path).exists())
        self.assertIsInstance(stats, dict)
        self.assertIn("original_size", stats)
        self.assertIn("optimized_size", stats)
        self.assertIn("compression_ratio", stats)

        # Clean up
        Path(output_path).unlink()

    def test_optimize_image_with_resize(self):
        """Test image optimization with resizing."""
        success, output_path, _error_msg, _stats = self.optimizer.optimize_image(
            input_path=self.temp_input_name, quality=85, max_width=400, max_height=300
        )

        self.assertTrue(success)
        self.assertTrue(Path(output_path).exists())

        # Check that image was resized
        with Image.open(output_path) as img:
            self.assertLessEqual(img.width, 400)
            self.assertLessEqual(img.height, 300)

        # Clean up
        Path(output_path).unlink()

    def test_optimize_image_different_formats(self):
        """Test optimization with different output formats."""
        formats_to_test = ["JPEG", "PNG", "WEBP"]

        for format_type in formats_to_test:
            with self.subTest(format=format_type):
                success, output_path, _error_msg, stats = self.optimizer.optimize_image(
                    input_path=self.temp_input_name, quality=85, format_type=format_type
                )

                self.assertTrue(success)
                self.assertTrue(Path(output_path).exists())
                self.assertEqual(stats["output_format"], format_type)

                # Clean up
                Path(output_path).unlink()

    def test_optimize_image_invalid_input(self):
        """Test optimization with invalid input file."""
        success, output_path, error_msg, _stats = self.optimizer.optimize_image(input_path="nonexistent_file.jpg")

        self.assertFalse(success)
        self.assertEqual(output_path, "")
        self.assertIn("does not exist", error_msg)

    def test_get_supported_formats(self):
        """Test that supported formats are returned correctly."""
        formats = self.optimizer.get_supported_formats()
        expected_formats = ["JPEG", "PNG", "WEBP", "Auto-detect"]

        self.assertEqual(set(formats), set(expected_formats))

    def test_get_quality_presets(self):
        """Test that quality presets are returned correctly."""
        presets = self.optimizer.get_quality_presets()

        self.assertIsInstance(presets, dict)
        self.assertIn("Maximum (95)", presets)
        self.assertIn("High (85)", presets)
        self.assertIn("Medium (75)", presets)
        self.assertIn("Low (60)", presets)
        self.assertIn("Minimum (40)", presets)

        # Check that values are in valid range
        for _preset_name, quality_value in presets.items():
            self.assertIsInstance(quality_value, int)
            self.assertGreaterEqual(quality_value, 1)
            self.assertLessEqual(quality_value, 100)


if __name__ == "__main__":
    unittest.main()
