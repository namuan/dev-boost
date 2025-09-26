"""
Unit tests for optimization settings and configuration management.
"""

import tempfile
import unittest
from pathlib import Path

from devboost.tools.file_optimization import OptimizationPreset, OptimizationSettings, QualityPreset, SettingsManager


class TestOptimizationSettings(unittest.TestCase):
    """Test cases for OptimizationSettings class."""

    def test_default_settings(self):
        """Test default settings creation."""
        settings = OptimizationSettings()

        self.assertEqual(settings.quality_preset, QualityPreset.MEDIUM)
        self.assertTrue(settings.create_backup)
        self.assertFalse(settings.preserve_metadata)
        self.assertIsNone(settings.image_quality)
        self.assertIsNone(settings.max_width)
        self.assertIsNone(settings.max_height)
        self.assertIsNone(settings.output_format)
        self.assertTrue(settings.progressive_jpeg)

    def test_custom_settings(self):
        """Test custom settings creation."""
        settings = OptimizationSettings(
            quality_preset=QualityPreset.HIGH,
            image_quality=85,
            max_width=1920,
            max_height=1080,
            output_format="jpeg",
            create_backup=False,
            preserve_metadata=True,
        )

        self.assertEqual(settings.quality_preset, QualityPreset.HIGH)
        self.assertEqual(settings.image_quality, 85)
        self.assertEqual(settings.max_width, 1920)
        self.assertEqual(settings.max_height, 1080)
        self.assertEqual(settings.output_format, "jpeg")
        self.assertFalse(settings.create_backup)
        self.assertTrue(settings.preserve_metadata)

    def test_to_dict(self):
        """Test settings serialization to dictionary."""
        settings = OptimizationSettings(quality_preset=QualityPreset.HIGH, image_quality=85, max_width=1920)

        data = settings.to_dict()

        self.assertEqual(data["quality_preset"], "high")
        self.assertEqual(data["image_quality"], 85)
        self.assertEqual(data["max_width"], 1920)
        self.assertTrue(data["create_backup"])

    def test_from_dict(self):
        """Test settings deserialization from dictionary."""
        data = {
            "quality_preset": "high",
            "image_quality": 85,
            "max_width": 1920,
            "create_backup": False,
            "preserve_metadata": True,
        }

        settings = OptimizationSettings.from_dict(data)

        self.assertEqual(settings.quality_preset, QualityPreset.HIGH)
        self.assertEqual(settings.image_quality, 85)
        self.assertEqual(settings.max_width, 1920)
        self.assertFalse(settings.create_backup)
        self.assertTrue(settings.preserve_metadata)

    def test_get_quality_for_type_preset(self):
        """Test quality retrieval based on preset."""
        settings = OptimizationSettings(quality_preset=QualityPreset.HIGH)

        self.assertEqual(settings.get_quality_for_type("image"), 85)
        self.assertEqual(settings.get_quality_for_type("video"), 23)
        self.assertEqual(settings.get_quality_for_type("pdf"), 80)

    def test_get_quality_for_type_custom(self):
        """Test quality retrieval with custom values."""
        settings = OptimizationSettings(
            quality_preset=QualityPreset.MEDIUM, image_quality=90, video_quality=20, pdf_quality=85
        )

        # Custom values should override preset
        self.assertEqual(settings.get_quality_for_type("image"), 90)
        self.assertEqual(settings.get_quality_for_type("video"), 20)
        self.assertEqual(settings.get_quality_for_type("pdf"), 85)

    def test_get_quality_for_unknown_type(self):
        """Test quality retrieval for unknown file type."""
        settings = OptimizationSettings(quality_preset=QualityPreset.HIGH)

        # Should return default value for unknown types
        self.assertEqual(settings.get_quality_for_type("unknown"), 75)


class TestOptimizationPreset(unittest.TestCase):
    """Test cases for OptimizationPreset class."""

    def test_preset_creation(self):
        """Test preset creation."""
        settings = OptimizationSettings(quality_preset=QualityPreset.HIGH)
        preset = OptimizationPreset(
            name="Test Preset", description="A test preset", settings=settings, is_builtin=False
        )

        self.assertEqual(preset.name, "Test Preset")
        self.assertEqual(preset.description, "A test preset")
        self.assertEqual(preset.settings.quality_preset, QualityPreset.HIGH)
        self.assertFalse(preset.is_builtin)

    def test_preset_to_dict(self):
        """Test preset serialization."""
        settings = OptimizationSettings(quality_preset=QualityPreset.HIGH)
        preset = OptimizationPreset(
            name="Test Preset", description="A test preset", settings=settings, is_builtin=False
        )

        data = preset.to_dict()

        self.assertEqual(data["name"], "Test Preset")
        self.assertEqual(data["description"], "A test preset")
        self.assertFalse(data["is_builtin"])
        self.assertIn("settings", data)
        self.assertEqual(data["settings"]["quality_preset"], "high")

    def test_preset_from_dict(self):
        """Test preset deserialization."""
        data = {
            "name": "Test Preset",
            "description": "A test preset",
            "is_builtin": False,
            "settings": {
                "quality_preset": "high",
                "image_quality": 85,
                "create_backup": True,
                "preserve_metadata": False,
                "progressive_jpeg": True,
            },
        }

        preset = OptimizationPreset.from_dict(data)

        self.assertEqual(preset.name, "Test Preset")
        self.assertEqual(preset.description, "A test preset")
        self.assertFalse(preset.is_builtin)
        self.assertEqual(preset.settings.quality_preset, QualityPreset.HIGH)
        self.assertEqual(preset.settings.image_quality, 85)


class TestQualityPreset(unittest.TestCase):
    """Test cases for QualityPreset enum."""

    def test_quality_preset_values(self):
        """Test quality preset enum values."""
        self.assertEqual(QualityPreset.MAXIMUM.value, "maximum")
        self.assertEqual(QualityPreset.HIGH.value, "high")
        self.assertEqual(QualityPreset.MEDIUM.value, "medium")
        self.assertEqual(QualityPreset.LOW.value, "low")
        self.assertEqual(QualityPreset.MINIMUM.value, "minimum")

    def test_quality_preset_from_string(self):
        """Test creating quality preset from string."""
        self.assertEqual(QualityPreset("high"), QualityPreset.HIGH)
        self.assertEqual(QualityPreset("medium"), QualityPreset.MEDIUM)


class TestSettingsManager(unittest.TestCase):
    """Test cases for SettingsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.settings_manager = SettingsManager(config_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test settings manager initialization."""
        self.assertTrue(self.temp_dir.exists())
        self.assertEqual(self.settings_manager.config_dir, self.temp_dir)

        # Should have default settings
        settings = self.settings_manager.get_current_settings()
        self.assertIsInstance(settings, OptimizationSettings)

        # Should have builtin presets
        presets = self.settings_manager.get_presets()
        self.assertGreater(len(presets), 0)
        self.assertIn("Web Optimized", presets)
        self.assertIn("High Quality", presets)

    def test_builtin_presets(self):
        """Test builtin presets are loaded correctly."""
        presets = self.settings_manager.get_presets()

        # Check specific builtin presets
        web_preset = presets.get("Web Optimized")
        self.assertIsNotNone(web_preset)
        self.assertTrue(web_preset.is_builtin)
        self.assertEqual(web_preset.settings.quality_preset, QualityPreset.MEDIUM)
        self.assertEqual(web_preset.settings.max_width, 1920)
        self.assertEqual(web_preset.settings.max_height, 1080)

        email_preset = presets.get("Email Friendly")
        self.assertIsNotNone(email_preset)
        self.assertTrue(email_preset.is_builtin)
        self.assertEqual(email_preset.settings.quality_preset, QualityPreset.LOW)
        self.assertEqual(email_preset.settings.max_width, 1024)

    def test_get_set_current_settings(self):
        """Test getting and setting current settings."""
        # Test default settings
        settings = self.settings_manager.get_current_settings()
        self.assertEqual(settings.quality_preset, QualityPreset.MEDIUM)

        # Test setting new settings
        new_settings = OptimizationSettings(quality_preset=QualityPreset.HIGH, image_quality=90, max_width=1920)

        self.settings_manager.set_current_settings(new_settings)
        retrieved_settings = self.settings_manager.get_current_settings()

        self.assertEqual(retrieved_settings.quality_preset, QualityPreset.HIGH)
        self.assertEqual(retrieved_settings.image_quality, 90)
        self.assertEqual(retrieved_settings.max_width, 1920)

    def test_save_load_settings(self):
        """Test settings persistence."""
        # Set custom settings
        custom_settings = OptimizationSettings(
            quality_preset=QualityPreset.HIGH, image_quality=85, max_width=1920, create_backup=False
        )

        self.settings_manager.set_current_settings(custom_settings)

        # Save settings
        self.assertTrue(self.settings_manager.save_settings())
        self.assertTrue(self.settings_manager.settings_file.exists())

        # Create new manager and load settings
        new_manager = SettingsManager(config_dir=self.temp_dir)
        loaded_settings = new_manager.get_current_settings()

        self.assertEqual(loaded_settings.quality_preset, QualityPreset.HIGH)
        self.assertEqual(loaded_settings.image_quality, 85)
        self.assertEqual(loaded_settings.max_width, 1920)
        self.assertFalse(loaded_settings.create_backup)

    def test_apply_preset(self):
        """Test applying presets."""
        # Apply web optimized preset
        self.assertTrue(self.settings_manager.apply_preset("Web Optimized"))

        settings = self.settings_manager.get_current_settings()
        self.assertEqual(settings.quality_preset, QualityPreset.MEDIUM)
        self.assertEqual(settings.max_width, 1920)
        self.assertEqual(settings.max_height, 1080)
        self.assertTrue(settings.progressive_jpeg)

        # Apply high quality preset
        self.assertTrue(self.settings_manager.apply_preset("High Quality"))

        settings = self.settings_manager.get_current_settings()
        self.assertEqual(settings.quality_preset, QualityPreset.HIGH)
        self.assertTrue(settings.preserve_metadata)

    def test_apply_nonexistent_preset(self):
        """Test applying non-existent preset."""
        self.assertFalse(self.settings_manager.apply_preset("Nonexistent Preset"))

    def test_add_custom_preset(self):
        """Test adding custom presets."""
        custom_settings = OptimizationSettings(quality_preset=QualityPreset.HIGH, image_quality=90, max_width=2560)

        custom_preset = OptimizationPreset(
            name="Custom Test", description="A custom test preset", settings=custom_settings, is_builtin=False
        )

        # Add preset
        self.assertTrue(self.settings_manager.add_preset(custom_preset))

        # Verify it was added
        presets = self.settings_manager.get_presets()
        self.assertIn("Custom Test", presets)

        retrieved_preset = presets["Custom Test"]
        self.assertEqual(retrieved_preset.description, "A custom test preset")
        self.assertFalse(retrieved_preset.is_builtin)
        self.assertEqual(retrieved_preset.settings.image_quality, 90)

    def test_remove_custom_preset(self):
        """Test removing custom presets."""
        # Add a custom preset first
        custom_preset = OptimizationPreset(
            name="To Delete", description="Will be deleted", settings=OptimizationSettings(), is_builtin=False
        )

        self.settings_manager.add_preset(custom_preset)
        self.assertIn("To Delete", self.settings_manager.get_presets())

        # Remove it
        self.assertTrue(self.settings_manager.remove_preset("To Delete"))
        self.assertNotIn("To Delete", self.settings_manager.get_presets())

    def test_remove_builtin_preset(self):
        """Test that builtin presets cannot be removed."""
        # Try to remove a builtin preset
        self.assertFalse(self.settings_manager.remove_preset("Web Optimized"))

        # Verify it's still there
        self.assertIn("Web Optimized", self.settings_manager.get_presets())

    def test_save_load_custom_presets(self):
        """Test custom preset persistence."""
        # Add custom preset
        custom_preset = OptimizationPreset(
            name="Persistent Test",
            description="Should persist",
            settings=OptimizationSettings(quality_preset=QualityPreset.HIGH),
            is_builtin=False,
        )

        self.settings_manager.add_preset(custom_preset)

        # Create new manager and verify preset is loaded
        new_manager = SettingsManager(config_dir=self.temp_dir)
        presets = new_manager.get_presets()

        self.assertIn("Persistent Test", presets)
        loaded_preset = presets["Persistent Test"]
        self.assertEqual(loaded_preset.description, "Should persist")
        self.assertFalse(loaded_preset.is_builtin)
        self.assertEqual(loaded_preset.settings.quality_preset, QualityPreset.HIGH)

    def test_validate_settings_valid(self):
        """Test settings validation with valid settings."""
        settings = OptimizationSettings(
            image_quality=85,
            video_quality=25,
            pdf_quality=80,
            max_width=1920,
            max_height=1080,
            video_fps=30,
            pdf_dpi=150,
            video_bitrate="2M",
        )

        errors = self.settings_manager.validate_settings(settings)
        self.assertEqual(len(errors), 0)

    def test_validate_settings_invalid_quality(self):
        """Test settings validation with invalid quality values."""
        settings = OptimizationSettings(
            image_quality=150,  # Invalid: > 100
            video_quality=60,  # Invalid: > 51
            pdf_quality=-10,  # Invalid: < 0
        )

        errors = self.settings_manager.validate_settings(settings)
        self.assertGreater(len(errors), 0)

        # Check specific error messages
        error_text = " ".join(errors)
        self.assertIn("Image quality must be between 0 and 100", error_text)
        self.assertIn("Video quality must be between 0 and 51", error_text)
        self.assertIn("PDF quality must be between 0 and 100", error_text)

    def test_validate_settings_invalid_dimensions(self):
        """Test settings validation with invalid dimensions."""
        settings = OptimizationSettings(
            max_width=-100,  # Invalid: negative
            max_height=0,  # Invalid: zero
            video_fps=-30,  # Invalid: negative
            pdf_dpi=1000,  # Invalid: > 600
        )

        errors = self.settings_manager.validate_settings(settings)
        self.assertGreater(len(errors), 0)

        error_text = " ".join(errors)
        self.assertIn("Maximum width must be positive", error_text)
        self.assertIn("Maximum height must be positive", error_text)
        self.assertIn("Video FPS must be positive", error_text)
        self.assertIn("PDF DPI must be between 72 and 600", error_text)

    def test_validate_settings_invalid_bitrate(self):
        """Test settings validation with invalid bitrate format."""
        settings = OptimizationSettings(video_bitrate="invalid_format")

        errors = self.settings_manager.validate_settings(settings)
        self.assertGreater(len(errors), 0)

        error_text = " ".join(errors)
        self.assertIn("Video bitrate must be in format", error_text)

    def test_validate_settings_valid_bitrate_formats(self):
        """Test settings validation with valid bitrate formats."""
        valid_bitrates = ["1M", "500k", "2000", "10K", "5m"]

        for bitrate in valid_bitrates:
            settings = OptimizationSettings(video_bitrate=bitrate)
            errors = self.settings_manager.validate_settings(settings)
            self.assertEqual(len(errors), 0, f"Bitrate {bitrate} should be valid")

    def test_get_preset(self):
        """Test getting specific presets."""
        preset = self.settings_manager.get_preset("Web Optimized")
        self.assertIsNotNone(preset)
        self.assertEqual(preset.name, "Web Optimized")

        # Test non-existent preset
        preset = self.settings_manager.get_preset("Non-existent")
        self.assertIsNone(preset)

    def test_config_file_creation(self):
        """Test that config files are created properly."""
        # Settings file should be created when saving
        self.settings_manager.save_settings()
        self.assertTrue(self.settings_manager.settings_file.exists())

        # Presets file should be created when saving custom presets
        custom_preset = OptimizationPreset(
            name="Test", description="Test", settings=OptimizationSettings(), is_builtin=False
        )
        self.settings_manager.add_preset(custom_preset)
        self.assertTrue(self.settings_manager.presets_file.exists())

    def test_corrupted_settings_file(self):
        """Test handling of corrupted settings file."""
        # Create corrupted settings file
        self.settings_manager.settings_file.write_text("invalid json content")

        # Should fall back to defaults
        new_manager = SettingsManager(config_dir=self.temp_dir)
        settings = new_manager.get_current_settings()

        # Should have default settings
        self.assertEqual(settings.quality_preset, QualityPreset.MEDIUM)
        self.assertTrue(settings.create_backup)

    def test_corrupted_presets_file(self):
        """Test handling of corrupted presets file."""
        # Create corrupted presets file
        self.settings_manager.presets_file.write_text("invalid json content")

        # Should still load builtin presets
        new_manager = SettingsManager(config_dir=self.temp_dir)
        presets = new_manager.get_presets()

        # Should have builtin presets but no custom ones
        self.assertIn("Web Optimized", presets)
        self.assertGreater(len(presets), 0)


if __name__ == "__main__":
    unittest.main()
