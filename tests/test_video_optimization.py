"""
Unit tests for video optimization functionality in the file optimization tool.
"""

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from devboost.tools.file_optimization import (
    OptimizationSettings,
    QualityPreset,
    VideoOptimizationEngine,
)


class TestVideoOptimizationEngine(unittest.TestCase):
    """Test video optimization engine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = VideoOptimizationEngine()

    def test_init_creates_logger_and_detects_tools(self):
        """Test that initialization creates logger and detects available tools."""
        with patch.object(VideoOptimizationEngine, "_detect_available_tools", return_value={"ffmpeg": True}):
            engine = VideoOptimizationEngine()
            self.assertIsNotNone(engine.logger)
            self.assertIsInstance(engine._available_tools, dict)

    def test_detect_available_tools_all_available(self):
        """Test tool detection when all tools are available."""
        with patch.object(self.engine, "_check_command_available", return_value=True):
            tools = self.engine._detect_available_tools()
            expected_tools = {"ffmpeg": True, "ffprobe": True, "gifski": True}
            self.assertEqual(tools, expected_tools)

    def test_detect_available_tools_none_available(self):
        """Test tool detection when no tools are available."""
        with patch.object(self.engine, "_check_command_available", return_value=False):
            tools = self.engine._detect_available_tools()
            expected_tools = {"ffmpeg": False, "ffprobe": False, "gifski": False}
            self.assertEqual(tools, expected_tools)

    def test_check_command_available_success(self):
        """Test successful command availability check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.engine._check_command_available("ffmpeg")
            self.assertTrue(result)
            mock_run.assert_called_once_with(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)

    def test_check_command_available_failure(self):
        """Test command availability check when command fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = self.engine._check_command_available("nonexistent")
            self.assertFalse(result)

    def test_check_command_available_timeout(self):
        """Test command availability check with timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            result = self.engine._check_command_available("slow_command")
            self.assertFalse(result)

    def test_check_command_available_file_not_found(self):
        """Test command availability check when command not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = self.engine._check_command_available("missing_command")
            self.assertFalse(result)

    def test_get_supported_formats_basic(self):
        """Test getting supported formats without ffmpeg."""
        self.engine._available_tools = {"ffmpeg": False}
        formats = self.engine.get_supported_formats()

        expected_input = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"]
        expected_output = [".mp4", ".webm", ".gif"]

        self.assertEqual(formats["input"], expected_input)
        self.assertEqual(formats["output"], expected_output)

    def test_get_supported_formats_with_ffmpeg(self):
        """Test getting supported formats with ffmpeg available."""
        self.engine._available_tools = {"ffmpeg": True}
        formats = self.engine.get_supported_formats()

        # Should include additional formats when ffmpeg is available
        self.assertIn(".3gp", formats["input"])
        self.assertIn(".avi", formats["output"])
        self.assertIn(".mkv", formats["output"])

    def test_optimize_video_file_not_found(self):
        """Test video optimization with non-existent input file."""
        input_path = Path("nonexistent.mp4")
        output_path = Path("output.mp4")
        settings = OptimizationSettings()

        with self.assertRaises(FileNotFoundError):
            self.engine.optimize_video(input_path, output_path, settings)

    def test_optimize_video_ffmpeg_not_available(self):
        """Test video optimization when ffmpeg is not available."""
        input_path = Path("test.mp4")
        output_path = Path("output.mp4")
        settings = OptimizationSettings()

        self.engine._available_tools = {"ffmpeg": False}

        with patch("pathlib.Path.exists", return_value=True):
            with self.assertRaises(RuntimeError) as context:
                self.engine.optimize_video(input_path, output_path, settings)
            self.assertIn("ffmpeg is required", str(context.exception))

    def test_optimize_video_gif_conversion(self):
        """Test video optimization for GIF conversion."""
        input_path = Path("test.mp4")
        output_path = Path("output.gif")
        settings = OptimizationSettings()

        self.engine._available_tools = {"ffmpeg": True}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
            patch.object(
                self.engine, "_convert_to_gif", return_value={"success": True, "method": "gifski"}
            ) as mock_convert,
        ):
            mock_stat.return_value.st_size = 1000
            result = self.engine.optimize_video(input_path, output_path, settings)

            self.assertTrue(result["success"])
            mock_convert.assert_called_once_with(input_path, output_path, settings)

    def test_optimize_video_mov_to_mp4(self):
        """Test MOV to MP4 conversion."""
        input_path = Path("test.mov")
        output_path = Path("output.mp4")
        settings = OptimizationSettings()

        self.engine._available_tools = {"ffmpeg": True}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
            patch.object(
                self.engine, "_convert_mov_to_mp4", return_value={"success": True, "method": "ffmpeg"}
            ) as mock_convert,
        ):
            mock_stat.return_value.st_size = 1000
            result = self.engine.optimize_video(input_path, output_path, settings)

            self.assertTrue(result["success"])
            mock_convert.assert_called_once_with(input_path, output_path, settings)

    def test_optimize_video_general_optimization(self):
        """Test general video optimization."""
        input_path = Path("test.mp4")
        output_path = Path("output.webm")
        settings = OptimizationSettings()

        self.engine._available_tools = {"ffmpeg": True}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
            patch.object(
                self.engine, "_optimize_with_ffmpeg", return_value={"success": True, "method": "ffmpeg"}
            ) as mock_optimize,
        ):
            mock_stat.return_value.st_size = 1000
            result = self.engine.optimize_video(input_path, output_path, settings)

            self.assertTrue(result["success"])
            mock_optimize.assert_called_once_with(input_path, output_path, settings)

    def test_optimize_video_compression_ratio_calculation(self):
        """Test compression ratio calculation in video optimization."""
        input_path = Path("test.mp4")
        output_path = Path("output.mp4")
        settings = OptimizationSettings()

        self.engine._available_tools = {"ffmpeg": True}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
            patch.object(self.engine, "_optimize_with_ffmpeg", return_value={"success": True}),
        ):
            # Mock file sizes: original 1000 bytes, optimized 800 bytes
            mock_stat.side_effect = lambda: Mock(st_size=1000) if mock_stat.call_count == 1 else Mock(st_size=800)

            result = self.engine.optimize_video(input_path, output_path, settings)

            self.assertEqual(result["original_size"], 1000)
            self.assertEqual(result["optimized_size"], 800)
            self.assertEqual(result["compression_ratio"], 20.0)  # (1000-800)/1000 * 100
            self.assertEqual(result["size_reduction"], 200)

    def test_optimize_with_ffmpeg_mp4_output(self):
        """Test ffmpeg optimization for MP4 output."""
        input_path = Path("test.avi")
        output_path = Path("output.mp4")
        settings = OptimizationSettings(quality_preset=QualityPreset.HIGH)

        with (
            patch.object(self.engine, "_get_video_info", return_value={"width": 1920, "height": 1080}),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            result = self.engine._optimize_with_ffmpeg(input_path, output_path, settings)

            self.assertTrue(result["success"])
            self.assertEqual(result["method"], "ffmpeg")
            self.assertEqual(result["codec"], "libx264")

            # Verify ffmpeg command structure
            args = mock_run.call_args[0][0]
            self.assertIn("ffmpeg", args)
            self.assertIn("-c:v", args)
            self.assertIn("libx264", args)

    def test_optimize_with_ffmpeg_webm_output(self):
        """Test ffmpeg optimization for WebM output."""
        input_path = Path("test.mp4")
        output_path = Path("output.webm")
        settings = OptimizationSettings()

        with (
            patch.object(self.engine, "_get_video_info", return_value={}),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            result = self.engine._optimize_with_ffmpeg(input_path, output_path, settings)

            self.assertTrue(result["success"])
            self.assertEqual(result["codec"], "libvpx-vp9")

            # Verify VP9 codec is used
            args = mock_run.call_args[0][0]
            self.assertIn("libvpx-vp9", args)

    def test_optimize_with_ffmpeg_custom_settings(self):
        """Test ffmpeg optimization with custom settings."""
        input_path = Path("test.mp4")
        output_path = Path("output.mp4")
        settings = OptimizationSettings(video_bitrate="2M", video_fps=30, max_width=1280, max_height=720)

        with (
            patch.object(self.engine, "_get_video_info", return_value={"width": 1920, "height": 1080}),
            patch.object(self.engine, "_build_scale_filter", return_value="scale=1280:720"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            result = self.engine._optimize_with_ffmpeg(input_path, output_path, settings)

            self.assertTrue(result["success"])

            # Verify custom settings are applied
            args = mock_run.call_args[0][0]
            self.assertIn("-b:v", args)
            self.assertIn("2M", args)
            self.assertIn("-r", args)
            self.assertIn("30", args)
            self.assertIn("-vf", args)

    def test_optimize_with_ffmpeg_failure(self):
        """Test ffmpeg optimization failure handling."""
        input_path = Path("test.mp4")
        output_path = Path("output.mp4")
        settings = OptimizationSettings()

        with (
            patch.object(self.engine, "_get_video_info", return_value={}),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "ffmpeg error"

            with self.assertRaises(RuntimeError) as context:
                self.engine._optimize_with_ffmpeg(input_path, output_path, settings)
            self.assertIn("ffmpeg failed", str(context.exception))

    def test_optimize_with_ffmpeg_timeout(self):
        """Test ffmpeg optimization timeout handling."""
        input_path = Path("test.mp4")
        output_path = Path("output.mp4")
        settings = OptimizationSettings()

        with (
            patch.object(self.engine, "_get_video_info", return_value={}),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 300)),
        ):
            with self.assertRaises(RuntimeError) as context:
                self.engine._optimize_with_ffmpeg(input_path, output_path, settings)
            self.assertIn("timed out", str(context.exception))

    def test_convert_mov_to_mp4(self):
        """Test MOV to MP4 conversion."""
        input_path = Path("test.mov")
        output_path = Path("output.webm")  # Different extension
        settings = OptimizationSettings()

        with patch.object(self.engine, "_optimize_with_ffmpeg", return_value={"success": True}) as mock_optimize:
            result = self.engine._convert_mov_to_mp4(input_path, output_path, settings)

            self.assertTrue(result["success"])
            # Should call with MP4 extension
            mock_optimize.assert_called_once()
            called_output_path = mock_optimize.call_args[0][1]
            self.assertEqual(called_output_path.suffix, ".mp4")

    def test_convert_to_gif_with_gifski_available(self):
        """Test GIF conversion when gifski is available."""
        input_path = Path("test.mp4")
        output_path = Path("output.gif")
        settings = OptimizationSettings()

        self.engine._available_tools = {"gifski": True}

        with patch.object(
            self.engine, "_convert_to_gif_with_gifski", return_value={"success": True, "method": "gifski"}
        ) as mock_gifski:
            result = self.engine._convert_to_gif(input_path, output_path, settings)

            self.assertTrue(result["success"])
            self.assertEqual(result["method"], "gifski")
            mock_gifski.assert_called_once_with(input_path, output_path, settings)

    def test_convert_to_gif_with_ffmpeg_fallback(self):
        """Test GIF conversion fallback to ffmpeg when gifski is not available."""
        input_path = Path("test.mp4")
        output_path = Path("output.gif")
        settings = OptimizationSettings()

        self.engine._available_tools = {"gifski": False}

        with patch.object(
            self.engine, "_convert_to_gif_with_ffmpeg", return_value={"success": True, "method": "ffmpeg"}
        ) as mock_ffmpeg:
            result = self.engine._convert_to_gif(input_path, output_path, settings)

            self.assertTrue(result["success"])
            self.assertEqual(result["method"], "ffmpeg")
            mock_ffmpeg.assert_called_once_with(input_path, output_path, settings)

    def test_convert_to_gif_with_gifski_success(self):
        """Test successful GIF conversion with gifski."""
        input_path = Path("test.mp4")
        output_path = Path("output.gif")
        settings = OptimizationSettings(video_fps=15, image_quality=90)

        with (
            patch.object(self.engine, "_get_video_info", return_value={"width": 640, "height": 480}),
            patch("tempfile.TemporaryDirectory") as mock_temp_dir,
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.glob", return_value=[Path("frame_0001.png"), Path("frame_0002.png")]),
        ):
            mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"
            mock_run.return_value.returncode = 0

            result = self.engine._convert_to_gif_with_gifski(input_path, output_path, settings)

            self.assertTrue(result["success"])
            self.assertEqual(result["method"], "gifski")
            self.assertEqual(result["fps"], 15)
            self.assertEqual(result["quality"], 90)

    def test_convert_to_gif_with_ffmpeg_success(self):
        """Test successful GIF conversion with ffmpeg."""
        input_path = Path("test.mp4")
        output_path = Path("output.gif")
        settings = OptimizationSettings(video_fps=12)

        with (
            patch.object(self.engine, "_get_video_info", return_value={"width": 640, "height": 480}),
            patch.object(self.engine, "_build_scale_filter", return_value="scale=320:240"),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0

            result = self.engine._convert_to_gif_with_ffmpeg(input_path, output_path, settings)

            self.assertTrue(result["success"])
            self.assertEqual(result["method"], "ffmpeg")
            self.assertEqual(result["fps"], 12)

            # Verify palette generation is used
            args = mock_run.call_args[0][0]
            filter_arg = next((arg for i, arg in enumerate(args) if args[i - 1] == "-vf"), None)
            self.assertIn("palettegen", filter_arg)
            self.assertIn("paletteuse", filter_arg)

    def test_get_video_info_success(self):
        """Test successful video info extraction."""
        video_path = Path("test.mp4")

        mock_ffprobe_output = {
            "streams": [
                {"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1", "codec_name": "h264"}
            ],
            "format": {"duration": "120.5"},
        }

        self.engine._available_tools = {"ffprobe": True}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(mock_ffprobe_output)

            info = self.engine._get_video_info(video_path)

            self.assertEqual(info["width"], 1920)
            self.assertEqual(info["height"], 1080)
            self.assertEqual(info["duration"], 120.5)
            self.assertEqual(info["fps"], 30.0)
            self.assertEqual(info["codec"], "h264")

    def test_get_video_info_no_ffprobe(self):
        """Test video info extraction when ffprobe is not available."""
        video_path = Path("test.mp4")
        self.engine._available_tools = {"ffprobe": False}

        info = self.engine._get_video_info(video_path)
        self.assertEqual(info, {})

    def test_get_video_info_failure(self):
        """Test video info extraction failure handling."""
        video_path = Path("test.mp4")
        self.engine._available_tools = {"ffprobe": True}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1

            info = self.engine._get_video_info(video_path)
            self.assertEqual(info, {})

    def test_build_scale_filter_no_constraints(self):
        """Test scale filter building with no size constraints."""
        video_info = {"width": 1920, "height": 1080}

        result = self.engine._build_scale_filter(video_info, None, None)
        self.assertIsNone(result)

    def test_build_scale_filter_width_only(self):
        """Test scale filter building with width constraint only."""
        video_info = {"width": 1920, "height": 1080}

        result = self.engine._build_scale_filter(video_info, 1280, None)
        self.assertEqual(result, "scale=1280:720")

    def test_build_scale_filter_height_only(self):
        """Test scale filter building with height constraint only."""
        video_info = {"width": 1920, "height": 1080}

        result = self.engine._build_scale_filter(video_info, None, 720)
        self.assertEqual(result, "scale=1280:720")

    def test_build_scale_filter_both_constraints(self):
        """Test scale filter building with both width and height constraints."""
        video_info = {"width": 1920, "height": 1080}

        result = self.engine._build_scale_filter(video_info, 1280, 720)
        self.assertEqual(result, "scale=1280:720")

    def test_build_scale_filter_no_upscaling(self):
        """Test that scale filter doesn't upscale videos."""
        video_info = {"width": 640, "height": 480}

        result = self.engine._build_scale_filter(video_info, 1920, 1080)
        self.assertIsNone(result)

    def test_build_scale_filter_even_dimensions(self):
        """Test that scale filter produces even dimensions."""
        video_info = {"width": 1921, "height": 1081}  # Odd dimensions

        result = self.engine._build_scale_filter(video_info, 1280, 720)
        # Should produce even dimensions while maintaining aspect ratio
        # With 1921x1081 -> scale to fit 1280x720 -> 1278x720 (maintains aspect ratio)
        self.assertIn("1278:720", result)

    def test_build_scale_filter_no_video_info(self):
        """Test scale filter building without video info."""
        video_info = {}

        result = self.engine._build_scale_filter(video_info, 1280, 720)
        self.assertEqual(result, "scale=1280:720:force_original_aspect_ratio=decrease")

    def test_get_optimization_info(self):
        """Test getting optimization information."""
        self.engine._available_tools = {"ffmpeg": True, "ffprobe": True, "gifski": False}

        with patch.object(self.engine, "get_supported_formats", return_value={"input": [".mp4"], "output": [".webm"]}):
            info = self.engine.get_optimization_info()

            self.assertEqual(info["available_tools"], {"ffmpeg": True, "ffprobe": True, "gifski": False})
            self.assertEqual(info["supported_formats"], {"input": [".mp4"], "output": [".webm"]})
            self.assertEqual(info["recommended_methods"]["mp4"], "ffmpeg")
            self.assertEqual(info["recommended_methods"]["gif"], "ffmpeg")  # fallback when gifski not available


if __name__ == "__main__":
    unittest.main()
