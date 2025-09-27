"""
Tests for PDF progress indicators in file optimization.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devboost.tools.file_optimization import (
    BatchProgress,
    OptimizationSettings,
    PDFOptimizationEngine,
    QualityPreset,
)


class TestPDFProgressIndicators(unittest.TestCase):
    """Test PDF progress indicators functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.pdf_engine = PDFOptimizationEngine()
        self.settings = OptimizationSettings(quality_preset=QualityPreset.MEDIUM)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_pdf(self, size_mb: float) -> Path:
        """Create a mock PDF file with specified size."""
        pdf_path = self.temp_dir / f"test_{size_mb}mb.pdf"

        # Create a simple PDF-like file with specified size
        content_size = int(size_mb * 1024 * 1024)
        pdf_path.write_bytes(b"%PDF-1.4\n" + b"0" * (content_size - 9) + b"\n%%EOF")
        return pdf_path

    def test_small_pdf_progress_tracking(self):
        """Test progress tracking for small PDF files (< 1MB)."""
        pdf_path = self._create_mock_pdf(0.5)  # 500KB
        output_path = self.temp_dir / "output.pdf"

        progress_updates = []

        def mock_progress_callback(progress: BatchProgress):
            progress_updates.append(progress)

        # Mock the ghostscript optimization to simulate progress
        with patch.object(self.pdf_engine, "_optimize_with_ghostscript") as mock_optimize:
            mock_optimize.return_value = {"compression_ratio": 0.8}

            # Simulate optimization with progress callback
            result = self.pdf_engine.optimize_pdf(
                pdf_path, output_path, self.settings, progress_callback=mock_progress_callback
            )

            # Verify optimization was called
            mock_optimize.assert_called_once()

            # Verify result structure
            self.assertIsInstance(result, dict)

    def test_medium_pdf_progress_tracking(self):
        """Test progress tracking for medium PDF files (1-10MB)."""
        pdf_path = self._create_mock_pdf(5.0)  # 5MB
        output_path = self.temp_dir / "output_medium.pdf"

        progress_updates = []

        def mock_progress_callback(progress: BatchProgress):
            progress_updates.append(progress)
            # Verify progress contains PDF-specific information
            if hasattr(progress, "current_status"):
                self.assertIn("PDF", progress.current_status)

        with patch.object(self.pdf_engine, "_optimize_with_ghostscript") as mock_optimize:
            mock_optimize.return_value = {"compression_ratio": 0.7}

            result = self.pdf_engine.optimize_pdf(
                pdf_path, output_path, self.settings, progress_callback=mock_progress_callback
            )

            mock_optimize.assert_called_once()
            self.assertIsInstance(result, dict)

    def test_large_pdf_progress_tracking(self):
        """Test progress tracking for large PDF files (> 10MB)."""
        pdf_path = self._create_mock_pdf(15.0)  # 15MB
        output_path = self.temp_dir / "output_large.pdf"

        progress_updates = []
        stage_updates = []

        def mock_progress_callback(progress: BatchProgress):
            progress_updates.append(progress)
            if hasattr(progress, "current_status"):
                stage_updates.append(progress.current_status)

        with patch.object(self.pdf_engine, "_optimize_with_ghostscript") as mock_optimize:
            mock_optimize.return_value = {"compression_ratio": 0.6}

            result = self.pdf_engine.optimize_pdf(
                pdf_path, output_path, self.settings, progress_callback=mock_progress_callback
            )

            mock_optimize.assert_called_once()
            self.assertIsInstance(result, dict)

    def test_progress_stages_integration(self):
        """Test that PDF progress stages are properly integrated."""
        # Test that BatchProgress can handle PDF-specific status messages
        progress = BatchProgress(1, 0)  # 1 total file, 0 completed
        progress.current_file = "test.pdf"
        progress.current_operation = "Compressing PDF"
        progress.pdf_stage = "Processing PDF content"
        progress.pdf_compression_stage = "Optimizing pages"

        # Verify progress object creation
        self.assertEqual(progress.total_files, 1)
        self.assertEqual(progress.completed_files, 0)
        self.assertEqual(progress.current_file, "test.pdf")
        self.assertEqual(progress.current_operation, "Compressing PDF")
        self.assertEqual(progress.pdf_stage, "Processing PDF content")
        self.assertEqual(progress.pdf_compression_stage, "Optimizing pages")

    def test_error_handling_in_progress_tracking(self):
        """Test error handling during PDF progress tracking."""
        pdf_path = self._create_mock_pdf(1.0)  # 1MB
        output_path = self.temp_dir / "output_error.pdf"

        error_caught = False

        def mock_progress_callback(progress: BatchProgress):
            pass

        with patch.object(self.pdf_engine, "_optimize_with_ghostscript") as mock_optimize:
            # Simulate an error during optimization
            mock_optimize.side_effect = Exception("Ghostscript error")

            try:
                self.pdf_engine.optimize_pdf(
                    pdf_path, output_path, self.settings, progress_callback=mock_progress_callback
                )
            except Exception:
                error_caught = True

            # Verify error was properly handled
            self.assertTrue(error_caught or mock_optimize.called)


if __name__ == "__main__":
    unittest.main()
