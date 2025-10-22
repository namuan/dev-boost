import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image, ImageFile

from .process_runner import run_process

if TYPE_CHECKING:
    from . import OptimizationSettings


class ImageOptimizationEngine:
    """
    Image optimization engine with support for PIL/Pillow, pngquant, jpegoptim, gifsicle, and libvips.

    This class provides a unified interface for optimizing images using various tools and libraries.
    It automatically detects available optimization tools and falls back gracefully when tools are not available.
    """

    def __init__(self):
        """Initialize the image optimization engine."""
        self.logger = logging.getLogger(__name__)
        self._available_tools = self._detect_available_tools()

        # Enable loading of truncated images
        ImageFile.LOAD_TRUNCATED_IMAGES = True

    def _detect_available_tools(self) -> dict[str, bool]:
        """Detect which optimization tools are available on the system."""
        tools = {
            "pil": True,  # PIL/Pillow is always available since it's a dependency
            "pngquant": self._check_command_available("pngquant"),
            "jpegoptim": self._check_command_available("jpegoptim"),
            "gifsicle": self._check_command_available("gifsicle"),
            "libvips": self._check_libvips_available(),
        }

        self.logger.info("Available optimization tools: %s", {tool: status for tool, status in tools.items() if status})
        return tools

    def _check_command_available(self, command: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            # S603: subprocess call with validated input - command is a trusted tool name
            result = run_process([command, "--version"], timeout=5, shell=False)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_libvips_available(self) -> bool:
        """Check if libvips is available."""
        try:
            import importlib.util

            spec = importlib.util.find_spec("pyvips")
            return spec is not None
        except ImportError:
            return False

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported image formats for optimization."""
        formats = {
            "input": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
            "output": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        }

        # Add additional formats if libvips is available
        if self._available_tools.get("libvips", False):
            formats["input"].extend([".svg", ".pdf", ".heic", ".avif"])
            formats["output"].extend([".avif", ".heic"])

        return formats

    def optimize_image(self, input_path: Path, output_path: Path, settings: "OptimizationSettings") -> dict[str, Any]:
        """
        Optimize an image using the best available method.

        Args:
            input_path: Path to the input image
            output_path: Path for the optimized output image
            settings: Optimization settings

        Returns:
            Dictionary with optimization results including file sizes and method used
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        original_size = input_path.stat().st_size
        input_ext = input_path.suffix.lower()
        output_path.suffix.lower() if output_path.suffix else input_ext

        self.logger.info("Optimizing image: %s -> %s", input_path, output_path)

        try:
            # Choose optimization method based on format and available tools
            if input_ext == ".png" and self._available_tools.get("pngquant", False):
                result = self._optimize_with_pngquant(input_path, output_path, settings)
            elif input_ext in [".jpg", ".jpeg"] and self._available_tools.get("jpegoptim", False):
                result = self._optimize_with_jpegoptim(input_path, output_path, settings)
            elif input_ext == ".gif" and self._available_tools.get("gifsicle", False):
                result = self._optimize_with_gifsicle(input_path, output_path, settings)
            elif self._available_tools.get("libvips", False):
                result = self._optimize_with_libvips(input_path, output_path, settings)
            else:
                # Fallback to PIL/Pillow
                result = self._optimize_with_pil(input_path, output_path, settings)

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
            self.logger.exception("Failed to optimize image")
            raise RuntimeError(f"Image optimization failed: {e!s}") from e

    def _optimize_with_pil(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Optimize image using PIL/Pillow with enhanced format conversion support."""
        self.logger.debug("Using PIL/Pillow for optimization")

        with Image.open(input_path) as img:
            # Handle format-specific conversions
            output_format = output_path.suffix.lower()

            # Convert HEIC/TIFF to appropriate formats with proper color mode handling
            if input_path.suffix.lower() in [".heic", ".tiff", ".tif"]:
                self.logger.info("Converting %s to %s format", input_path.suffix.lower(), output_format)

                # Convert to RGB if needed for JPEG output
                if output_format in [".jpg", ".jpeg"] and img.mode in ["RGBA", "LA", "P"]:
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    # Create white background for transparency
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                elif output_format == ".png" and img.mode not in ["RGBA", "RGB", "L", "LA"]:
                    # Convert to RGBA for PNG to preserve transparency if present
                    img = img.convert("RGBA")

            # Convert RGBA to RGB if saving as JPEG (existing logic)
            elif output_format in [".jpg", ".jpeg"] and img.mode in ["RGBA", "LA"]:
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background

            # Resize if dimensions are specified
            if settings.max_width or settings.max_height:
                img = self._resize_image(img, settings.max_width, settings.max_height)

            # Prepare save options
            save_kwargs = {}

            if output_format in [".jpg", ".jpeg"]:
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"quality": quality, "optimize": True, "progressive": settings.progressive_jpeg})
            elif output_format == ".png":
                save_kwargs.update({"optimize": True, "compress_level": 9})
            elif output_format == ".webp":
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"quality": quality, "optimize": True})

            # Remove metadata if not preserving
            if not settings.preserve_metadata:
                # Create new image without EXIF data
                img_data = img.getdata()
                img_clean = Image.new(img.mode, img.size)
                img_clean.putdata(img_data)
                img = img_clean

            # Save optimized image
            img.save(output_path, **save_kwargs)

        return {
            "method": "PIL/Pillow",
            "success": True,
            "format": output_format,
            "converted": input_path.suffix.lower() != output_format,
        }

    def _optimize_with_pngquant(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Optimize PNG image using pngquant."""
        self.logger.debug("Using pngquant for PNG optimization")

        quality = settings.get_quality_for_type("image")
        # Convert quality (0-100) to pngquant range (0-100)
        min_quality = max(0, quality - 10)
        max_quality = min(100, quality + 5)

        cmd = [
            "pngquant",
            "--quality",
            "%d-%d" % (min_quality, max_quality),
            "--output",
            str(output_path),
            str(input_path),
        ]

        if not settings.preserve_metadata:
            cmd.append("--strip")

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = run_process(cmd, timeout=30, shell=False)
            if result.returncode != 0:
                # Fallback to PIL if pngquant fails
                self.logger.warning("pngquant failed, falling back to PIL: %s", result.stderr)
                return self._optimize_with_pil(input_path, output_path, settings)

            return {"method": "pngquant", "success": True, "format": ".png"}
        except subprocess.TimeoutExpired:
            self.logger.warning("pngquant timed out, falling back to PIL")
            return self._optimize_with_pil(input_path, output_path, settings)

    def _optimize_with_jpegoptim(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Optimize JPEG image using jpegoptim."""
        self.logger.debug("Using jpegoptim for JPEG optimization")

        quality = settings.get_quality_for_type("image")

        # Copy file first since jpegoptim modifies in place
        shutil.copy2(input_path, output_path)

        cmd = [
            "jpegoptim",
            "--max=%d" % quality,
            "--strip-all" if not settings.preserve_metadata else "--preserve",
            str(output_path),
        ]

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = run_process(cmd, timeout=30, shell=False)
            if result.returncode != 0:
                # Fallback to PIL if jpegoptim fails
                self.logger.warning("jpegoptim failed, falling back to PIL: %s", result.stderr)
                return self._optimize_with_pil(input_path, output_path, settings)

            return {"method": "jpegoptim", "success": True, "format": input_path.suffix.lower()}
        except subprocess.TimeoutExpired:
            self.logger.warning("jpegoptim timed out, falling back to PIL")
            return self._optimize_with_pil(input_path, output_path, settings)

    def _optimize_with_gifsicle(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Optimize GIF image using gifsicle."""
        self.logger.debug("Using gifsicle for GIF optimization")

        cmd = [
            "gifsicle",
            "--optimize=3",  # Maximum optimization
            "--output",
            str(output_path),
            str(input_path),
        ]

        try:
            # S603: subprocess call with validated input - cmd is constructed from trusted sources
            result = run_process(cmd, timeout=30, shell=False)
            if result.returncode != 0:
                # Fallback to PIL if gifsicle fails
                self.logger.warning("gifsicle failed, falling back to PIL: %s", result.stderr)
                return self._optimize_with_pil(input_path, output_path, settings)

            return {"method": "gifsicle", "success": True, "format": ".gif"}
        except subprocess.TimeoutExpired:
            self.logger.warning("gifsicle timed out, falling back to PIL")
            return self._optimize_with_pil(input_path, output_path, settings)

    def _optimize_with_libvips(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Optimize image using libvips (pyvips)."""
        self.logger.debug("Using libvips for optimization")

        try:
            import pyvips

            # Load image
            img = pyvips.Image.new_from_file(str(input_path))

            # Resize if dimensions are specified
            if settings.max_width or settings.max_height:
                current_width = img.width
                current_height = img.height

                # Calculate new dimensions maintaining aspect ratio
                if settings.max_width and settings.max_height:
                    scale_w = settings.max_width / current_width
                    scale_h = settings.max_height / current_height
                    scale = min(scale_w, scale_h)
                elif settings.max_width:
                    scale = settings.max_width / current_width
                else:
                    scale = settings.max_height / current_height

                if scale < 1.0:  # Only downscale
                    img = img.resize(scale)

            # Prepare save options
            save_kwargs = {}
            output_format = output_path.suffix.lower()

            if output_format in [".jpg", ".jpeg"]:
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"Q": quality, "optimize_coding": True, "interlace": settings.progressive_jpeg})
            elif output_format == ".png":
                save_kwargs.update({"compression": 9, "interlace": True})
            elif output_format == ".webp":
                quality = settings.get_quality_for_type("image")
                save_kwargs.update({"Q": quality, "lossless": quality >= 90})

            # Remove metadata if not preserving
            if not settings.preserve_metadata:
                save_kwargs["strip"] = True

            # Save optimized image
            img.write_to_file(str(output_path), **save_kwargs)

            return {"method": "libvips", "success": True, "format": output_format}

        except Exception as e:
            self.logger.warning("libvips optimization failed, falling back to PIL: %s", str(e))
            return self._optimize_with_pil(input_path, output_path, settings)

    def _resize_image(self, img: Image.Image, max_width: int | None, max_height: int | None) -> Image.Image:
        """Resize image maintaining aspect ratio, supporting both fixed dimensions and percentage scaling."""
        current_width, current_height = img.size

        # Check if percentage-based scaling is active
        if hasattr(self, "resize_percentage") and self.resize_percentage:
            # Use percentage-based scaling
            scale = self.resize_percentage
            new_width = int(current_width * scale)
            new_height = int(current_height * scale)
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate new dimensions using fixed max dimensions
        if max_width and max_height:
            # Fit within both constraints
            scale_w = max_width / current_width
            scale_h = max_height / current_height
            scale = min(scale_w, scale_h)
        elif max_width:
            scale = max_width / current_width
        elif max_height:
            scale = max_height / current_height
        else:
            return img

        if scale < 1.0:  # Only downscale
            new_width = int(current_width * scale)
            new_height = int(current_height * scale)
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def get_optimization_info(self) -> dict[str, Any]:
        """Get information about available optimization tools and capabilities."""
        return {
            "available_tools": self._available_tools,
            "supported_formats": self.get_supported_formats(),
            "recommended_tools": {
                "png": "pngquant" if self._available_tools.get("pngquant") else "PIL",
                "jpeg": "jpegoptim" if self._available_tools.get("jpegoptim") else "PIL",
                "gif": "gifsicle" if self._available_tools.get("gifsicle") else "PIL",
                "webp": "libvips" if self._available_tools.get("libvips") else "PIL",
                "other": "libvips" if self._available_tools.get("libvips") else "PIL",
            },
        }
