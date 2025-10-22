import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .process_runner import run_process

if TYPE_CHECKING:
    from . import OptimizationSettings


class VideoOptimizationEngine:
    """
    Video optimization engine with support for ffmpeg and gifski.

    This class provides a unified interface for optimizing videos using ffmpeg for compression
    and format conversion, with special support for high-quality video-to-GIF conversion using gifski.
    """

    def __init__(self):
        """Initialize the video optimization engine."""
        self.logger = logging.getLogger(__name__)
        self._available_tools = self._detect_available_tools()

    def _detect_available_tools(self) -> dict[str, bool]:
        """Detect which video optimization tools are available on the system."""
        tools = {
            "ffmpeg": self._check_command_available("ffmpeg"),
            "ffprobe": self._check_command_available("ffprobe"),
            "gifski": self._check_command_available("gifski"),
        }

        self.logger.info("Available video tools: %s", {tool: status for tool, status in tools.items() if status})
        return tools

    def _check_command_available(self, command: str) -> bool:
        """Check if a command-line tool is available."""
        result = run_process([command, "-version"], timeout=5, shell=False)
        return result.success

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported video formats for optimization."""
        formats = {
            "input": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"],
            "output": [".mp4", ".webm", ".gif"],
        }

        # Add additional formats if ffmpeg is available
        if self._available_tools.get("ffmpeg", False):
            formats["input"].extend([".3gp", ".asf", ".rm", ".rmvb", ".vob"])
            formats["output"].extend([".avi", ".mkv", ".mov"])

        return formats

    def optimize_video(self, input_path: Path, output_path: Path, settings: "OptimizationSettings") -> dict[str, Any]:
        """
        Optimize a video using the best available method.

        Args:
            input_path: Path to the input video
            output_path: Path for the optimized output video
            settings: Optimization settings

        Returns:
            Dictionary with optimization results including file sizes and method used
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        if not self._available_tools.get("ffmpeg", False):
            raise RuntimeError("ffmpeg is required for video optimization but not available")

        original_size = input_path.stat().st_size
        input_ext = input_path.suffix.lower()
        output_ext = output_path.suffix.lower()

        self.logger.info("Optimizing video: %s -> %s", input_path, output_path)

        try:
            # Choose optimization method based on output format
            if output_ext == ".gif":
                result = self._convert_to_gif(input_path, output_path, settings)
            elif input_ext == ".mov" and output_ext == ".mp4":
                result = self._convert_mov_to_mp4(input_path, output_path, settings)
            else:
                result = self._optimize_with_ffmpeg(input_path, output_path, settings)

            # Calculate compression ratio
            if output_path.exists():
                optimized_size = output_path.stat().st_size
                compression_ratio = (original_size - optimized_size) / original_size * 100
                result.update({
                    "original_size": original_size,
                    "optimized_size": optimized_size,
                    "compression_ratio": compression_ratio,
                    "size_reduction": original_size - optimized_size,
                })

            return result

        except Exception as e:
            self.logger.exception("Failed to optimize video")
            raise RuntimeError(f"Video optimization failed: {e!s}") from e

    def _optimize_with_ffmpeg(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Optimize video using ffmpeg with comprehensive settings."""
        self.logger.debug("Using ffmpeg for video optimization")

        # Get video info first
        video_info = self._get_video_info(input_path)

        # Check if input and output paths are the same (in-place editing)
        temp_output = None
        actual_output_path = output_path

        if input_path.resolve() == output_path.resolve():
            # Create temporary output file to avoid FFmpeg in-place editing error
            temp_output = output_path.with_suffix(f".tmp{output_path.suffix}")
            actual_output_path = temp_output
            self.logger.debug("Using temporary output file to avoid in-place editing: %s", temp_output)

        # Build ffmpeg command
        cmd = ["ffmpeg", "-i", str(input_path)]

        # Video codec and quality settings
        output_ext = output_path.suffix.lower()

        if output_ext in [".mp4", ".m4v"]:
            cmd.extend(["-c:v", "libx264"])
            # Use CRF (Constant Rate Factor) for quality
            crf = settings.get_quality_for_type("video")
            cmd.extend(["-crf", str(crf)])

            # Add preset for encoding speed vs compression efficiency
            cmd.extend(["-preset", "medium"])

        elif output_ext == ".webm":
            cmd.extend(["-c:v", "libvpx-vp9"])
            # VP9 uses different quality scale
            crf = settings.get_quality_for_type("video")
            cmd.extend(["-crf", str(crf)])

        # Audio codec
        cmd.extend(["-c:a", "aac", "-b:a", "128k"])

        # Custom bitrate if specified
        if settings.video_bitrate and settings.video_bitrate != "Auto":
            cmd.extend(["-b:v", settings.video_bitrate])

        # Frame rate if specified
        if settings.video_fps and settings.video_fps > 0:
            cmd.extend(["-r", str(settings.video_fps)])

        # Resolution if specified
        if settings.max_width or settings.max_height:
            scale_filter = self._build_scale_filter(video_info, settings.max_width, settings.max_height)
            if scale_filter:
                cmd.extend(["-vf", scale_filter])

        # Output settings
        cmd.extend(["-movflags", "+faststart"])  # Optimize for web streaming
        cmd.extend(["-y"])  # Overwrite output file
        cmd.append(str(actual_output_path))

        try:
            self.logger.debug("Running ffmpeg command: %s", " ".join(cmd))
            result = run_process(cmd, timeout=300, shell=False)

            if not result.success:
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")

            # If we used a temporary file, replace the original
            if temp_output and temp_output.exists():
                self.logger.debug("Replacing original file with optimized version")
                shutil.move(str(temp_output), str(output_path))

            return {
                "method": "ffmpeg",
                "success": True,
                "format": output_ext,
                "codec": "libx264" if output_ext in [".mp4", ".m4v"] else "libvpx-vp9",
                "converted": input_path.suffix.lower() != output_ext,
            }

        except subprocess.TimeoutExpired as e:
            raise RuntimeError("Video optimization timed out (5 minutes)") from e

    def _convert_mov_to_mp4(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Convert MOV to MP4 with optimization."""
        self.logger.debug("Converting MOV to MP4")

        # Use the general optimization method but ensure MP4 output
        if output_path.suffix.lower() != ".mp4":
            output_path = output_path.with_suffix(".mp4")

        return self._optimize_with_ffmpeg(input_path, output_path, settings)

    def _convert_to_gif(self, input_path: Path, output_path: Path, settings: "OptimizationSettings") -> dict[str, Any]:
        """Convert video to GIF using gifski for high quality or ffmpeg as fallback."""
        self.logger.debug("Converting video to GIF")

        if self._available_tools.get("gifski", False):
            return self._convert_to_gif_with_gifski(input_path, output_path, settings)
        return self._convert_to_gif_with_ffmpeg(input_path, output_path, settings)

    def _convert_to_gif_with_gifski(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Convert video to GIF using gifski for high quality."""
        self.logger.debug("Using gifski for high-quality GIF conversion")

        # First extract frames using ffmpeg
        with tempfile.TemporaryDirectory() as temp_dir:
            frames_pattern = Path(temp_dir) / "frame_%04d.png"

            # Extract frames with ffmpeg
            extract_cmd = ["ffmpeg", "-i", str(input_path)]

            # Frame rate for extraction
            fps = settings.video_fps if settings.video_fps and settings.video_fps > 0 else 10
            extract_cmd.extend(["-vf", f"fps={fps}"])

            # Resolution if specified
            video_info = self._get_video_info(input_path)
            if settings.max_width or settings.max_height:
                scale_filter = self._build_scale_filter(video_info, settings.max_width, settings.max_height)
                if scale_filter:
                    # Combine with fps filter
                    extract_cmd[-1] = f"fps={fps},{scale_filter}"

            extract_cmd.extend(["-y", str(frames_pattern)])

            try:
                # S603: subprocess call with validated input - cmd is constructed from trusted sources
                result = run_process(extract_cmd, timeout=120, shell=False)

                if result.returncode != 0:
                    raise RuntimeError(f"Frame extraction failed: {result.stderr}")

                # Convert frames to GIF with gifski
                gifski_cmd = ["gifski", "-o", str(output_path)]

                # Quality settings for gifski (1-100, higher is better)
                quality = settings.get_quality_for_type("image")  # Use image quality for GIF
                gifski_cmd.extend(["--quality", str(quality)])

                # FPS for gifski
                gifski_cmd.extend(["--fps", str(fps)])

                # Add frame files
                frame_files = sorted(Path(temp_dir).glob("frame_*.png"))
                if not frame_files:
                    raise RuntimeError("No frames were extracted")

                gifski_cmd.extend([str(f) for f in frame_files])

                # S603: subprocess call with validated input - cmd is constructed from trusted sources
                result = run_process(gifski_cmd, timeout=180, shell=False)

                if result.returncode != 0:
                    raise RuntimeError(f"gifski conversion failed: {result.stderr}")

                return {
                    "method": "gifski",
                    "success": True,
                    "format": ".gif",
                    "fps": fps,
                    "quality": quality,
                    "converted": True,
                }

            except subprocess.TimeoutExpired as e:
                raise RuntimeError("GIF conversion timed out") from e

    def _convert_to_gif_with_ffmpeg(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Convert video to GIF using ffmpeg as fallback."""
        self.logger.debug("Using ffmpeg for GIF conversion (fallback)")

        # Check if input and output paths are the same (in-place editing)
        temp_output = None
        actual_output_path = output_path

        if input_path.resolve() == output_path.resolve():
            # Create temporary output file to avoid FFmpeg in-place editing error
            temp_output = output_path.with_suffix(f".tmp{output_path.suffix}")
            actual_output_path = temp_output
            self.logger.debug("Using temporary output file to avoid in-place editing: %s", temp_output)

        cmd = ["ffmpeg", "-i", str(input_path)]

        # Build filter for GIF conversion
        filters = []

        # Frame rate
        fps = settings.video_fps if settings.video_fps and settings.video_fps > 0 else 10
        filters.append(f"fps={fps}")

        # Resolution
        video_info = self._get_video_info(input_path)
        if settings.max_width or settings.max_height:
            scale_filter = self._build_scale_filter(video_info, settings.max_width, settings.max_height)
            if scale_filter:
                filters.append(scale_filter)

        # Palette generation for better quality
        filters.append("split[s0][s1]")
        filters.append("[s0]palettegen[p]")
        filters.append("[s1][p]paletteuse")

        cmd.extend(["-vf", ",".join(filters)])
        cmd.extend(["-y", str(actual_output_path)])

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = run_process(cmd, timeout=180, shell=False)

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg GIF conversion failed: {result.stderr}")

            # If we used a temporary file, replace the original
            if temp_output and temp_output.exists():
                self.logger.debug("Replacing original file with optimized version")
                shutil.move(str(temp_output), str(output_path))

            return {
                "method": "ffmpeg",
                "success": True,
                "format": ".gif",
                "fps": fps,
                "converted": True,
            }

        except subprocess.TimeoutExpired as e:
            raise RuntimeError("GIF conversion timed out") from e

    def _get_video_info(self, video_path: Path) -> dict[str, Any]:
        """Get video information using ffprobe."""
        if not self._available_tools.get("ffprobe", False):
            return {}

        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video_path)]

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = run_process(cmd, timeout=30, shell=False)

            if result.returncode == 0:
                info = json.loads(result.stdout)

                # Extract video stream info
                video_stream = None
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break

                if video_stream:
                    return {
                        "width": int(video_stream.get("width", 0)),
                        "height": int(video_stream.get("height", 0)),
                        "duration": float(info.get("format", {}).get("duration", 0)),
                        "fps": eval(video_stream.get("r_frame_rate", "0/1")),  # noqa: S307
                        "codec": video_stream.get("codec_name", "unknown"),
                    }
        except (subprocess.TimeoutExpired, json.JSONDecodeError, ZeroDivisionError):
            pass

        return {}

    def _build_scale_filter(
        self, video_info: dict[str, Any], max_width: int | None, max_height: int | None
    ) -> str | None:
        """Build ffmpeg scale filter maintaining aspect ratio."""
        if not max_width and not max_height:
            return None

        current_width = video_info.get("width", 0)
        current_height = video_info.get("height", 0)

        if not current_width or not current_height:
            # Fallback if we don't have video info
            if max_width and max_height:
                return f"scale={max_width}:{max_height}:force_original_aspect_ratio=decrease"
            if max_width:
                return f"scale={max_width}:-1"
            return f"scale=-1:{max_height}"

        # Calculate new dimensions maintaining aspect ratio
        if max_width and max_height:
            scale_w = max_width / current_width
            scale_h = max_height / current_height
            scale = min(scale_w, scale_h)
        elif max_width:
            scale = max_width / current_width
        else:
            scale = max_height / current_height

        if scale >= 1.0:  # Don't upscale
            return None

        new_width = int(current_width * scale)
        new_height = int(current_height * scale)

        # Ensure dimensions are even (required for some codecs)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)

        return f"scale={new_width}:{new_height}"

    def get_optimization_info(self) -> dict[str, Any]:
        """Get information about available optimization methods."""
        return {
            "available_tools": self._available_tools,
            "supported_formats": self.get_supported_formats(),
            "recommended_methods": {
                "mp4": "ffmpeg" if self._available_tools.get("ffmpeg") else "not_available",
                "webm": "ffmpeg" if self._available_tools.get("ffmpeg") else "not_available",
                "gif": "gifski" if self._available_tools.get("gifski") else "ffmpeg",
                "mov_to_mp4": "ffmpeg" if self._available_tools.get("ffmpeg") else "not_available",
            },
        }
