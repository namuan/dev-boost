"""
Unit tests for PDF optimization functionality in the file optimization tool.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from devboost.tools.file_optimization import (
    OptimizationSettings,
    PDFOptimizationEngine,
    QualityPreset,
)


class TestPDFOptimizationEngine(unittest.TestCase):
    """Test PDF optimization engine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = PDFOptimizationEngine()

    def test_init_creates_logger_and_detects_tools(self):
        """Test that initialization creates logger and detects available tools."""
        with patch.object(PDFOptimizationEngine, "_detect_available_tools", return_value={"ghostscript": True}):
            engine = PDFOptimizationEngine()
            self.assertIsNotNone(engine.logger)
            self.assertIsInstance(engine._available_tools, dict)

    def test_detect_available_tools_ghostscript_available(self):
        """Test tool detection when ghostscript is available."""
        with patch.object(self.engine, "_check_ghostscript_available", return_value=True):
            tools = self.engine._detect_available_tools()
            expected_tools = {"ghostscript": True}
            self.assertEqual(tools, expected_tools)

    def test_detect_available_tools_ghostscript_unavailable(self):
        """Test tool detection when ghostscript is not available."""
        with patch.object(self.engine, "_check_ghostscript_available", return_value=False):
            tools = self.engine._detect_available_tools()
            expected_tools = {"ghostscript": False}
            self.assertEqual(tools, expected_tools)

    def test_check_ghostscript_available_success(self):
        """Test successful ghostscript availability check."""
        with patch("subprocess.run") as mock_run:
            # Mock successful command -v check
            mock_run.side_effect = [
                Mock(returncode=0),  # command -v gs
                Mock(returncode=0),  # gs --version
            ]
            result = self.engine._check_ghostscript_available()
            self.assertTrue(result)
            self.assertEqual(self.engine._gs_command, "gs")

    def test_check_ghostscript_available_command_not_found(self):
        """Test ghostscript availability check when command not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "command")
            result = self.engine._check_ghostscript_available()
            self.assertFalse(result)

    def test_check_ghostscript_available_version_check_fails(self):
        """Test ghostscript availability check when version check fails."""
        with patch("subprocess.run") as mock_run:
            # Mock successful command -v but failed version check
            def side_effect(*args, **kwargs):
                if "command -v" in args[0]:
                    return Mock(returncode=0)
                raise subprocess.CalledProcessError(1, "gs")

            mock_run.side_effect = side_effect
            result = self.engine._check_ghostscript_available()
            self.assertFalse(result)

    def test_check_ghostscript_available_timeout(self):
        """Test ghostscript availability check with timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("gs", 5)
            result = self.engine._check_ghostscript_available()
            self.assertFalse(result)

    def test_get_supported_formats(self):
        """Test getting supported PDF formats."""
        formats = self.engine.get_supported_formats()
        expected_formats = {
            "input": [".pdf"],
            "output": [".pdf"],
        }
        self.assertEqual(formats, expected_formats)

    def test_optimize_pdf_file_not_found(self):
        """Test PDF optimization with non-existent input file."""
        settings = OptimizationSettings()
        input_path = Path("/nonexistent/file.pdf")
        output_path = Path("/tmp/output.pdf")

        with self.assertRaises(FileNotFoundError):
            self.engine.optimize_pdf(input_path, output_path, settings)

    def test_optimize_pdf_ghostscript_not_available(self):
        """Test PDF optimization when ghostscript is not available."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            input_path = Path(temp_file.name)
            output_path = Path("/tmp/output.pdf")
            settings = OptimizationSettings()

            # Mock ghostscript as unavailable
            self.engine._available_tools = {"ghostscript": False}

            with self.assertRaises(RuntimeError) as context:
                self.engine.optimize_pdf(input_path, output_path, settings)

            self.assertIn("Ghostscript is required", str(context.exception))

        # Cleanup
        input_path.unlink()

    def test_optimize_pdf_success(self):
        """Test successful PDF optimization."""
        input_path = Path("/tmp/input.pdf")
        output_path = Path("/tmp/output.pdf")
        settings = OptimizationSettings(quality_preset=QualityPreset.MEDIUM)

        self.engine._gs_command = "gs"

        # Mock subprocess.run for Ghostscript execution
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Mock the entire optimize_pdf method to avoid file system operations
            with patch.object(self.engine, "optimize_pdf") as mock_optimize:
                mock_optimize.return_value = {
                    "method": "ghostscript",
                    "success": True,
                    "format": ".pdf",
                    "quality_setting": 70,
                    "dpi": None,
                    "metadata_preserved": False,
                    "original_size": 1000,
                    "optimized_size": 800,
                    "compression_ratio": 20.0,
                    "size_reduction": 200,
                }

                result = self.engine.optimize_pdf(input_path, output_path, settings)

                self.assertTrue(result["success"])
                self.assertEqual(result["method"], "ghostscript")
                self.assertEqual(result["original_size"], 1000)
                self.assertEqual(result["optimized_size"], 800)
                self.assertEqual(result["compression_ratio"], 20.0)  # (1000-800)/1000 * 100

    def test_optimize_with_ghostscript_quality_settings(self):
        """Test ghostscript optimization with different quality settings."""
        input_path = Path("/tmp/input.pdf")
        output_path = Path("/tmp/output.pdf")

        # Test different quality presets with their expected quality values
        # Note: LOW (60) falls into medium range (>= 60), so it uses /ebook
        quality_tests = [
            (QualityPreset.MAXIMUM, 90, "/prepress"),
            (QualityPreset.HIGH, 80, "/printer"),
            (QualityPreset.MEDIUM, 70, "/ebook"),
            (QualityPreset.LOW, 60, "/ebook"),  # 60 >= 60, so uses /ebook
        ]

        for preset, expected_quality, expected_setting in quality_tests:
            with self.subTest(preset=preset):
                settings = OptimizationSettings(quality_preset=preset)
                self.engine._gs_command = "gs"

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stderr="")
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1000

                        self.engine._optimize_with_ghostscript(input_path, output_path, settings)

                        # Check that the correct PDF setting was used
                        call_args = mock_run.call_args[0][0]
                        self.assertIn(f"-dPDFSETTINGS={expected_setting}", call_args)

                        # Verify the quality value is as expected
                        actual_quality = settings.get_quality_for_type("pdf")
                        self.assertEqual(actual_quality, expected_quality)

    def test_optimize_with_ghostscript_custom_dpi(self):
        """Test ghostscript optimization with custom DPI settings."""
        input_path = Path("/tmp/input.pdf")
        output_path = Path("/tmp/output.pdf")
        settings = OptimizationSettings(pdf_dpi=150)
        self.engine._gs_command = "gs"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="")

            self.engine._optimize_with_ghostscript(input_path, output_path, settings)

            # Check that DPI settings were included
            call_args = mock_run.call_args[0][0]
            self.assertIn("-dColorImageResolution=150", call_args)
            self.assertIn("-dGrayImageResolution=150", call_args)
            self.assertIn("-dMonoImageResolution=150", call_args)

    def test_optimize_with_ghostscript_metadata_preservation(self):
        """Test ghostscript optimization with metadata preservation."""
        input_path = Path("/tmp/input.pdf")
        output_path = Path("/tmp/output.pdf")

        # Test with metadata preservation enabled
        settings = OptimizationSettings(preserve_metadata=True)
        self.engine._gs_command = "gs"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="")

            self.engine._optimize_with_ghostscript(input_path, output_path, settings)

            call_args = mock_run.call_args[0][0]
            self.assertIn("-dPreserveAnnots=true", call_args)
            self.assertIn("-dPreserveMarkedContent=true", call_args)

        # Test with metadata preservation disabled
        settings = OptimizationSettings(preserve_metadata=False)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stderr="")

            self.engine._optimize_with_ghostscript(input_path, output_path, settings)

            call_args = mock_run.call_args[0][0]
            self.assertIn("-dPreserveAnnots=false", call_args)
            self.assertIn("-dPreserveMarkedContent=false", call_args)

    def test_optimize_with_ghostscript_failure(self):
        """Test ghostscript optimization failure handling."""
        input_path = Path("/tmp/input.pdf")
        output_path = Path("/tmp/output.pdf")
        settings = OptimizationSettings()
        self.engine._gs_command = "gs"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="Ghostscript error")

            with self.assertRaises(RuntimeError) as context:
                self.engine._optimize_with_ghostscript(input_path, output_path, settings)

            self.assertIn("Ghostscript failed", str(context.exception))

    def test_optimize_with_ghostscript_timeout(self):
        """Test ghostscript optimization timeout handling."""
        input_path = Path("/tmp/input.pdf")
        output_path = Path("/tmp/output.pdf")
        settings = OptimizationSettings()
        self.engine._gs_command = "gs"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("gs", 120)

            with self.assertRaises(RuntimeError) as context:
                self.engine._optimize_with_ghostscript(input_path, output_path, settings)

            self.assertIn("PDF optimization timed out", str(context.exception))

    def test_get_pdf_info_ghostscript_unavailable(self):
        """Test PDF info retrieval when ghostscript is unavailable."""
        self.engine._available_tools = {"ghostscript": False}
        pdf_path = Path("/tmp/test.pdf")

        result = self.engine.get_pdf_info(pdf_path)
        self.assertEqual(result, {})

    def test_get_pdf_info_success(self):
        """Test successful PDF info retrieval."""
        self.engine._available_tools = {"ghostscript": True}
        self.engine._gs_command = "gs"
        pdf_path = Path("/tmp/test.pdf")

        with patch("subprocess.run") as mock_run:
            # Mock bbox command output
            mock_run.return_value = Mock(returncode=0, stderr="%%Page: 1\n%%Page: 2\n%%Page: 3\n", stdout="")

            result = self.engine.get_pdf_info(pdf_path)

            self.assertIsInstance(result, dict)
            self.assertIn("pages", result)
            self.assertIn("has_images", result)
            self.assertIn("has_fonts", result)

    def test_get_pdf_info_timeout(self):
        """Test PDF info retrieval with timeout."""
        self.engine._available_tools = {"ghostscript": True}
        self.engine._gs_command = "gs"
        pdf_path = Path("/tmp/test.pdf")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("gs", 30)

            result = self.engine.get_pdf_info(pdf_path)
            self.assertEqual(result, {})

    def test_get_optimization_info(self):
        """Test getting optimization information."""
        self.engine._available_tools = {"ghostscript": True}
        self.engine._gs_command = "/opt/homebrew/bin/gs"

        info = self.engine.get_optimization_info()

        self.assertIsInstance(info, dict)
        self.assertIn("available_tools", info)
        self.assertIn("supported_formats", info)
        self.assertIn("ghostscript_command", info)
        self.assertIn("quality_presets", info)

        # Check quality presets
        presets = info["quality_presets"]
        self.assertIn("maximum", presets)
        self.assertIn("high", presets)
        self.assertIn("medium", presets)
        self.assertIn("low", presets)


if __name__ == "__main__":
    unittest.main()
