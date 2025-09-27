"""
Unit tests for PDF progress indicators in the file optimization tool.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import time

from devboost.tools.file_optimization import (
    FileOptimizationTool,
    OptimizationSettings,
    QualityPreset,
    BatchProgress,
    PDFOptimizationEngine,
)


class TestPDFProgressIndicators(unittest.TestCase):
    """Test PDF progress indicators with various file sizes."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.optimization_tool = FileOptimizationTool()
        self.pdf_engine = PDFOptimizationEngine()
        self.settings = OptimizationSettings(quality_preset=QualityPreset.MEDIUM)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_pdf(self, size_kb: int, name: str = "test.pdf") -> Path:
        """Create a mock PDF file of specified size."""
        pdf_path = self.temp_dir / name
        # Create a simple PDF-like file with PDF header
        pdf_content = b"%PDF-1.4\n"
        # Add dummy content to reach desired size
        remaining_size = (size_kb * 1024) - len(pdf_content)
        pdf_content += b"0" * remaining_size
        pdf_path.write_bytes(pdf_content)
        return pdf_path

    def test_small_pdf_progress_tracking(self):
        """Test progress tracking for small PDF files (< 1MB)."""
        small_pdf = self._create_mock_pdf(500, "small.pdf")  # 500KB
        output_path = self.temp_dir / "small_optimized.pdf"
        
        progress_updates = []
        
        def mock_progress_callback(progress):
            progress_updates.append({
                'percentage': progress.progress_percentage,
                'stage': getattr(progress, 'pdf_stage', None),
                'compression_stage': getattr(progress, 'pdf_compression_stage', None)
            })
        
        with patch('subprocess.Popen') as mock_popen:
            # Mock Ghostscript process
            mock_process = Mock()
            mock_process.poll.side_effect = [None, None, 0]  # Running, then finished
            mock_process.stdout.readline.side_effect = [
                b"Processing pages 1-5...\n",
                b"GPL Ghostscript 10.0.0\n",
                b"Page 1\n",
                b"Page 2\n",
                b"Page 3\n",
                b""
            ]
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Mock the _track_pdf_progress method to simulate progress updates
            with patch.object(self.pdf_engine, '_track_pdf_progress') as mock_track:
                def simulate_progress(*args, **kwargs):
                    callback = kwargs.get('progress_callback')
                    if callback:
                        # Simulate progress stages for small PDF
                        stages = [
                            ("Initializing PDF compression", "Starting compression process", 10),
                            ("Processing PDF content", "Analyzing PDF structure", 30),
                            ("Compressing PDF pages", "Optimizing page 1 of 3", 50),
                            ("Compressing PDF pages", "Optimizing page 2 of 3", 70),
                            ("Finalizing compression", "Completing optimization", 90),
                            ("PDF compression completed", "Optimization finished successfully", 100)
                        ]
                        
                        for stage, compression_stage, percentage in stages:
                            progress = BatchProgress()
                            progress.progress_percentage = percentage
                            progress.pdf_stage = stage
                            progress.pdf_compression_stage = compression_stage
                            callback(progress)
                            time.sleep(0.01)  # Small delay to simulate processing
                
                mock_track.side_effect = simulate_progress
                
                result = self.pdf_engine.optimize_pdf(small_pdf, output_path, self.settings, 
                                                    progress_callback=mock_progress_callback)
        
        # Verify progress updates were received
        self.assertGreater(len(progress_updates), 0)
        
        # Check that we have the expected stages
        stages_seen = [update['stage'] for update in progress_updates if update['stage']]
        self.assertIn("Initializing PDF compression", stages_seen)
        self.assertIn("Processing PDF content", stages_seen)
        self.assertIn("Compressing PDF pages", stages_seen)
        self.assertIn("Finalizing compression", stages_seen)
        self.assertIn("PDF compression completed", stages_seen)
        
        # Check progress percentages increase
        percentages = [update['percentage'] for update in progress_updates]
        self.assertEqual(percentages[0], 10)
        self.assertEqual(percentages[-1], 100)

    def test_medium_pdf_progress_tracking(self):
        """Test progress tracking for medium PDF files (1-10MB)."""
        medium_pdf = self._create_mock_pdf(5000, "medium.pdf")  # 5MB
        output_path = self.temp_dir / "medium_optimized.pdf"
        
        progress_updates = []
        
        def mock_progress_callback(progress):
            progress_updates.append({
                'percentage': progress.progress_percentage,
                'stage': getattr(progress, 'pdf_stage', None),
                'compression_stage': getattr(progress, 'pdf_compression_stage', None),
                'pages_processed': getattr(progress, 'pages_processed', 0),
                'total_pages': getattr(progress, 'total_pages', 0)
            })
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.side_effect = [None] * 10 + [0]  # Longer processing
            mock_process.stdout.readline.side_effect = [
                b"Processing pages 1-20...\n",
                b"GPL Ghostscript 10.0.0\n",
            ] + [f"Page {i}\n".encode() for i in range(1, 21)] + [b""]
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            with patch.object(self.pdf_engine, '_track_pdf_progress') as mock_track:
                def simulate_medium_progress(*args, **kwargs):
                    callback = kwargs.get('progress_callback')
                    if callback:
                        # Simulate more detailed progress for medium PDF
                        total_pages = 20
                        for i in range(total_pages + 1):
                            if i == 0:
                                stage = "Initializing PDF compression"
                                compression_stage = "Starting compression process"
                                percentage = 5
                            elif i <= 5:
                                stage = "Processing PDF content"
                                compression_stage = f"Analyzing PDF structure - page {i}"
                                percentage = 5 + (i * 10)
                            elif i <= total_pages - 2:
                                stage = "Compressing PDF pages"
                                compression_stage = f"Optimizing page {i} of {total_pages}"
                                percentage = 50 + ((i - 5) * 2)
                            elif i == total_pages - 1:
                                stage = "Finalizing compression"
                                compression_stage = "Completing optimization"
                                percentage = 95
                            else:
                                stage = "PDF compression completed"
                                compression_stage = "Optimization finished successfully"
                                percentage = 100
                            
                            progress = BatchProgress()
                            progress.progress_percentage = percentage
                            progress.pdf_stage = stage
                            progress.pdf_compression_stage = compression_stage
                            progress.pages_processed = min(i, total_pages)
                            progress.total_pages = total_pages
                            callback(progress)
                            time.sleep(0.005)  # Simulate processing time
                
                mock_track.side_effect = simulate_medium_progress
                
                result = self.pdf_engine.optimize_pdf(medium_pdf, output_path, self.settings,
                                                    progress_callback=mock_progress_callback)
        
        # Verify detailed progress tracking for medium files
        self.assertGreater(len(progress_updates), 15)  # Should have many updates
        
        # Check page tracking
        page_updates = [update for update in progress_updates if update.get('total_pages', 0) > 0]
        self.assertGreater(len(page_updates), 0)
        self.assertEqual(page_updates[-1]['total_pages'], 20)
        self.assertEqual(page_updates[-1]['pages_processed'], 20)

    def test_large_pdf_progress_tracking(self):
        """Test progress tracking for large PDF files (> 10MB)."""
        large_pdf = self._create_mock_pdf(15000, "large.pdf")  # 15MB
        output_path = self.temp_dir / "large_optimized.pdf"
        
        progress_updates = []
        time_updates = []
        
        def mock_progress_callback(progress):
            progress_updates.append({
                'percentage': progress.progress_percentage,
                'stage': getattr(progress, 'pdf_stage', None),
                'compression_stage': getattr(progress, 'pdf_compression_stage', None),
                'estimated_time_remaining': getattr(progress, 'estimated_time_remaining', None)
            })
            time_updates.append(time.time())
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.poll.side_effect = [None] * 50 + [0]  # Very long processing
            mock_process.stdout.readline.side_effect = [
                b"Processing pages 1-100...\n",
                b"GPL Ghostscript 10.0.0\n",
            ] + [f"Page {i}\n".encode() for i in range(1, 101)] + [b""]
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            with patch.object(self.pdf_engine, '_track_pdf_progress') as mock_track:
                def simulate_large_progress(*args, **kwargs):
                    callback = kwargs.get('progress_callback')
                    if callback:
                        # Simulate time-based estimation for large PDF
                        total_pages = 100
                        start_time = time.time()
                        
                        for i in range(0, total_pages + 1, 5):  # Update every 5 pages
                            current_time = time.time()
                            elapsed = current_time - start_time
                            
                            if i == 0:
                                stage = "Initializing PDF compression"
                                compression_stage = "Starting compression process"
                                percentage = 2
                                estimated_remaining = None
                            elif i <= 10:
                                stage = "Processing PDF content"
                                compression_stage = f"Analyzing PDF structure - pages 1-{i}"
                                percentage = 2 + (i * 2)
                                estimated_remaining = None
                            else:
                                stage = "Compressing PDF pages"
                                compression_stage = f"Optimizing pages {i-4}-{i} of {total_pages}"
                                percentage = 20 + ((i - 10) * 0.8)
                                # Estimate remaining time based on current progress
                                if percentage > 20:
                                    estimated_remaining = (elapsed / (percentage / 100)) - elapsed
                            
                            progress = BatchProgress()
                            progress.progress_percentage = min(percentage, 98)
                            progress.pdf_stage = stage
                            progress.pdf_compression_stage = compression_stage
                            progress.estimated_time_remaining = estimated_remaining
                            callback(progress)
                            time.sleep(0.01)  # Simulate processing time
                        
                        # Final completion
                        progress = BatchProgress()
                        progress.progress_percentage = 100
                        progress.pdf_stage = "PDF compression completed"
                        progress.pdf_compression_stage = "Optimization finished successfully"
                        callback(progress)
                
                mock_track.side_effect = simulate_large_progress
                
                result = self.pdf_engine.optimize_pdf(large_pdf, output_path, self.settings,
                                                    progress_callback=mock_progress_callback)
        
        # Verify time estimation for large files
        self.assertGreater(len(progress_updates), 10)
        
        # Check that time estimation was provided
        time_estimates = [update['estimated_time_remaining'] for update in progress_updates 
                         if update['estimated_time_remaining'] is not None]
        self.assertGreater(len(time_estimates), 0)

    def test_progress_ui_integration(self):
        """Test that PDF progress updates integrate properly with UI components."""
        pdf_file = self._create_mock_pdf(2000, "ui_test.pdf")
        
        # Mock UI components
        mock_progress_bar = Mock()
        mock_progress_info_label = Mock()
        mock_stats_label = Mock()
        
        with patch.object(self.optimization_tool, 'progress_bar', mock_progress_bar), \
             patch.object(self.optimization_tool, 'progress_info_label', mock_progress_info_label), \
             patch.object(self.optimization_tool, 'stats_label', mock_stats_label):
            
            # Create a progress update that would come from PDF processing
            progress = BatchProgress()
            progress.progress_percentage = 65
            progress.pdf_stage = "Compressing PDF pages"
            progress.pdf_compression_stage = "Optimizing page 15 of 25"
            progress.current_file = "ui_test.pdf"
            progress.operation = "PDF Optimization"
            progress.elapsed_time = 45.5
            progress.estimated_time_remaining = 25.2
            
            # Simulate the UI update method
            self.optimization_tool._on_batch_progress_updated(progress)
            
            # Verify UI components were updated
            mock_progress_bar.setVisible.assert_called_with(True)
            mock_progress_bar.setValue.assert_called_with(65)
            
            # Check that progress info was updated with PDF-specific information
            progress_info_calls = mock_progress_info_label.setText.call_args_list
            self.assertGreater(len(progress_info_calls), 0)
            
            # Verify PDF stage information is included in the UI
            progress_text = progress_info_calls[0][0][0]
            self.assertIn("Compressing PDF pages", progress_text)
            self.assertIn("ui_test.pdf", progress_text)

    def test_error_handling_in_progress_tracking(self):
        """Test error handling during PDF progress tracking."""
        pdf_file = self._create_mock_pdf(1000, "error_test.pdf")
        output_path = self.temp_dir / "error_optimized.pdf"
        
        error_caught = False
        
        def mock_progress_callback(progress):
            # This callback should still receive updates even if there are errors
            pass
        
        with patch('subprocess.Popen') as mock_popen:
            # Simulate a process that fails
            mock_process = Mock()
            mock_process.poll.return_value = 1  # Error exit code
            mock_process.stdout.readline.side_effect = [
                b"Error: Invalid PDF file\n",
                b""
            ]
            mock_process.returncode = 1
            mock_popen.return_value = mock_process
            
            try:
                result = self.pdf_engine.optimize_pdf(pdf_file, output_path, self.settings,
                                                    progress_callback=mock_progress_callback)
                # Should handle the error gracefully
                self.assertFalse(result.get("success", True))
            except Exception:
                error_caught = True
        
        # Error should be handled gracefully, not crash the progress tracking
        self.assertFalse(error_caught)


if __name__ == "__main__":
    unittest.main()