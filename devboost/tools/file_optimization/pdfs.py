import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from devboost.config import get_config, set_config

if TYPE_CHECKING:
    from . import OptimizationSettings


class PDFOptimizationEngine:
    """
    PDF optimization engine with support for ghostscript.

    This class provides a unified interface for optimizing PDF files using ghostscript
    for compression, quality control, and metadata preservation.
    """

    def __init__(self):
        """Initialize the PDF optimization engine."""
        self.logger = logging.getLogger(__name__)
        self._available_tools = self._detect_available_tools()

    def set_ghostscript_path(self, path: str) -> bool:
        """
        Set a custom Ghostscript path and save it to user configuration.

        Args:
            path: Path to the Ghostscript executable

        Returns:
            bool: True if the path is valid and working, False otherwise
        """
        if not path.strip():
            # Clear the custom path
            set_config("file_optimization.ghostscript_path", "")
            self.logger.info("Cleared custom Ghostscript path, will use auto-detection")
            # Re-detect available tools
            self._available_tools = self._detect_available_tools()
            return True

        # Test if the provided path works
        try:
            resolved = self._resolve_executable(path)
            if resolved and self._verify_ghostscript(resolved):
                # Save to configuration
                set_config("file_optimization.ghostscript_path", path)
                self.logger.info("Set custom Ghostscript path: %s", path)
                # Re-detect available tools to update status
                self._available_tools = self._detect_available_tools()
                return True
            self.logger.error("Invalid Ghostscript path: %s", path)
            return False
        except Exception:
            self.logger.exception("Error setting Ghostscript path '%s'", path)
            return False

    def get_ghostscript_path(self) -> str:
        """
        Get the currently configured Ghostscript path.

        Returns:
            str: The configured path, or empty string if using auto-detection
        """
        path = get_config("file_optimization.ghostscript_path", "")
        return path if path is not None else ""

    def _detect_available_tools(self) -> dict[str, bool]:
        """Detect which PDF optimization tools are available on the system."""
        tools = {
            "ghostscript": self._check_ghostscript_available(),
        }

        self.logger.info("Available PDF tools: %s", {tool: status for tool, status in tools.items() if status})
        return tools

    def _check_ghostscript_available(self) -> bool:
        """Check if ghostscript is available, preferring user-configured path and explicit Homebrew path."""
        # First check if user has configured a custom Ghostscript path
        if self._check_custom_ghostscript_path():
            return True

        # Compatibility: quick PATH-based check
        if self._check_ghostscript_in_path():
            return True

        # Check environment variables and common paths
        return self._check_ghostscript_candidates()

    def _check_custom_ghostscript_path(self) -> bool:
        """Check user-configured custom Ghostscript path."""
        custom_gs_path_raw = get_config("file_optimization.ghostscript_path", "")
        custom_gs_path = custom_gs_path_raw.strip() if custom_gs_path_raw else ""

        if not custom_gs_path:
            return False

        try:
            resolved = self._resolve_executable(custom_gs_path)
            if resolved and self._verify_ghostscript(resolved):
                self._gs_command = resolved
                self.logger.info(
                    "Using user-configured Ghostscript: command=%s version=%s", self._gs_command, self._gs_version
                )
                return True
            self.logger.warning("User-configured Ghostscript path is invalid or not working: %s", custom_gs_path)
        except Exception as e:
            self.logger.warning("Error checking user-configured Ghostscript path '%s': %s", custom_gs_path, e)

        return False

    def _check_ghostscript_in_path(self) -> bool:
        """Check for Ghostscript using PATH-based lookup."""
        try:
            cmd_check = subprocess.run(  # noqa: S602
                "command -v gs",  # noqa: S607
                capture_output=True,
                text=True,
                timeout=5,
                shell=True,
            )
            if cmd_check.returncode == 0:
                return self._verify_gs_command()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.logger.debug("PATH-based gs check failed: %s", e)

        return False

    def _verify_gs_command(self) -> bool:
        """Verify the 'gs' command works and get version."""
        try:
            version_proc = subprocess.run(  # noqa: S603
                ["gs", "--version"],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=5,
                shell=False,
            )
            if version_proc.returncode == 0:
                stdout_text = version_proc.stdout.strip() if version_proc.stdout else ""
                stderr_text = version_proc.stderr.strip() if version_proc.stderr else ""
                version_text = stdout_text if stdout_text else stderr_text
                self._gs_command = "gs"
                self._gs_version = version_text if version_text else None
                self.logger.info(
                    "Ghostscript detected via PATH: command=%s version=%s", self._gs_command, self._gs_version
                )
                return True
            self.logger.debug("gs --version returned non-zero: %s", version_proc.returncode)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            self.logger.debug("Ghostscript version check failed: %s", e)

        return False

    def _check_ghostscript_candidates(self) -> bool:
        """Check environment variables and common installation paths."""
        # Allow explicit override via environment variables
        env_override = os.environ.get("DEVBOOST_GS") or os.environ.get("GHOSTSCRIPT_PATH")

        candidates: list[str] = []
        if env_override:
            candidates.append(env_override)

        # Prefer Homebrew on Apple Silicon first, then common absolute paths, then names resolved via PATH
        candidates.extend([
            "/opt/homebrew/bin/gs",
            "/usr/local/bin/gs",
            "/usr/bin/gs",
            "/opt/local/bin/gs",
            "gs",
            "ghostscript",
        ])

        checked: list[str] = []
        for cand in candidates:
            try:
                resolved = self._resolve_executable(cand)
                checked.append(cand if resolved is None else resolved)
                if not resolved:
                    self.logger.debug("Ghostscript candidate not found or not executable: %s", cand)
                    continue

                if self._verify_ghostscript(resolved):
                    self._gs_command = resolved
                    self.logger.info("Ghostscript detected: command=%s version=%s", self._gs_command, self._gs_version)
                    return True

            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
                self.logger.debug("Error probing ghostscript candidate '%s': %s", cand, e)
                continue

        self.logger.warning("Ghostscript not found. Checked candidates: %s", checked)
        return False

    def _resolve_executable(self, path_like: str) -> str | None:
        """Resolve executable path, handling both absolute paths and PATH lookups."""
        # If it looks like a path, verify it; otherwise resolve via PATH using shutil.which
        if os.path.sep in path_like:
            p = Path(path_like)
            if p.is_file() and os.access(str(p), os.X_OK):
                return str(p.resolve())
            return None
        resolved = shutil.which(path_like)
        return str(Path(resolved).resolve()) if resolved else None

    def _verify_ghostscript(self, executable_path: str) -> bool:
        """Verify that the given executable is a working Ghostscript installation."""
        try:
            # Verify by checking version/help output; avoid invoking shell aliases by passing list and shell=False
            # The executable_path is validated before this function is called
            version_proc = subprocess.run(  # noqa: S603
                [executable_path, "--version"], capture_output=True, text=True, timeout=5, shell=False
            )
            help_proc = subprocess.run([executable_path, "-h"], capture_output=True, text=True, timeout=5, shell=False)  # noqa: S603

            if version_proc.returncode == 0 or help_proc.returncode == 0:
                stdout_text = version_proc.stdout.strip() if version_proc.stdout else ""
                stderr_text = version_proc.stderr.strip() if version_proc.stderr else ""
                version_text = stdout_text if stdout_text else stderr_text
                if self._looks_like_ghostscript(version_text, help_proc.stdout, help_proc.stderr):
                    self._gs_version = version_text if version_text else None
                    return True

            self.logger.debug(
                "Candidate failed ghostscript verification: %s (version_rc=%s help_rc=%s)",
                executable_path,
                version_proc.returncode,
                help_proc.returncode,
            )
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
            self.logger.debug("Error verifying ghostscript candidate '%s': %s", executable_path, e)
            return False

    def _looks_like_ghostscript(self, version_out: str, help_out: str, help_err: str) -> bool:
        """Check if the output looks like it's from Ghostscript."""
        version_ok = bool(re.match(r"^\d+(?:\.\d+)+$", version_out.strip()))
        mentions_gs = ("Ghostscript" in help_out) or ("Ghostscript" in help_err)
        return version_ok or mentions_gs

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Get supported PDF formats for optimization."""
        return {
            "input": [".pdf"],
            "output": [".pdf"],
        }

    def optimize_pdf(self, input_path: Path, output_path: Path, settings: "OptimizationSettings") -> dict[str, Any]:
        """
        Optimize a PDF using ghostscript.

        Args:
            input_path: Path to the input PDF
            output_path: Path for the optimized output PDF
            settings: Optimization settings

        Returns:
            Dictionary with optimization results including file sizes and method used
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        if not self._available_tools.get("ghostscript", False):
            raise RuntimeError("Ghostscript is required for PDF optimization but not available")

        original_size = input_path.stat().st_size

        self.logger.info("Optimizing PDF: %s -> %s", input_path, output_path)

        try:
            result = self._optimize_with_ghostscript(input_path, output_path, settings)

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
            self.logger.exception("Failed to optimize PDF")
            raise RuntimeError(f"PDF optimization failed: {e!s}") from e

    def _optimize_with_ghostscript(
        self, input_path: Path, output_path: Path, settings: "OptimizationSettings"
    ) -> dict[str, Any]:
        """Optimize PDF using ghostscript with comprehensive settings."""
        self.logger.debug("Using ghostscript for PDF optimization")

        # Import here to avoid circular dependency at module import time
        from devboost.tools.file_optimization import QualityPreset

        # Build ghostscript command
        cmd = [self._gs_command]

        # Minimal ghostscript options for reliable PDF compression
        cmd.extend([
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dNOPAUSE",
            "-dBATCH",
        ])

        # Add quality-based settings
        if settings.quality_preset == QualityPreset.HIGH:
            cmd.extend(["-dPDFSETTINGS=/prepress"])
        elif settings.quality_preset == QualityPreset.MEDIUM:
            cmd.extend(["-dPDFSETTINGS=/printer"])
        elif settings.quality_preset == QualityPreset.LOW:
            cmd.extend(["-dPDFSETTINGS=/ebook"])
        elif settings.quality_preset == QualityPreset.MINIMUM:
            cmd.extend(["-dPDFSETTINGS=/screen"])

        # Output file
        cmd.extend([f"-sOutputFile={output_path}", str(input_path)])

        try:
            # Log the full command for debugging
            cmd_str = " ".join(cmd)
            self.logger.info("Executing Ghostscript command: %s", cmd_str)
            self.logger.debug("Running ghostscript command: %s", cmd_str)
            # The command is constructed from trusted sources (validated ghostscript executable)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, shell=False)  # noqa: S603

            if result.returncode != 0:
                self.logger.error("Ghostscript command failed with return code %d", result.returncode)
                self.logger.error("Ghostscript stderr: %s", result.stderr)
                self.logger.error("Ghostscript stdout: %s", result.stdout)
                raise RuntimeError(f"Ghostscript failed: {result.stderr}")

            self.logger.info("Ghostscript command completed successfully")
            if result.stdout:
                self.logger.debug("Ghostscript stdout: %s", result.stdout)

            return {
                "method": "ghostscript",
                "success": True,
                "format": ".pdf",
                "quality_setting": "minimal",
                "dpi": settings.pdf_dpi,
                "metadata_preserved": settings.preserve_metadata,
            }

        except subprocess.TimeoutExpired as e:
            raise RuntimeError("PDF optimization timed out (2 minutes)") from e

    def get_pdf_info(self, pdf_path: Path) -> dict[str, Any]:
        """Get PDF information using ghostscript."""
        if not self._available_tools.get("ghostscript", False):
            return {}

        cmd = [self._gs_command, "-sDEVICE=bbox", "-dNOPAUSE", "-dBATCH", "-dQUIET", str(pdf_path)]

        try:
            # The command is constructed from trusted sources (validated ghostscript executable)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)  # noqa: S603

            info = {"pages": 0, "has_images": False, "has_fonts": False}

            # Parse ghostscript output for basic info
            if result.stderr:
                lines = result.stderr.split("\n")
                for line in lines:
                    if "Page" in line:
                        info["pages"] += 1

            # Try to get more detailed info with a different approach
            info_cmd = [
                self._gs_command,
                "-sDEVICE=nullpage",
                "-dNOPAUSE",
                "-dBATCH",
                "-dQUIET",
                "-c",
                "currentpagedevice /PageCount get ==",
                str(pdf_path),
            ]

            try:
                info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=15, shell=False)  # noqa: S603
                stdout_text = info_result.stdout.strip() if info_result.stdout else ""
                if info_result.returncode == 0 and stdout_text.isdigit():
                    info["pages"] = int(stdout_text)
            except (subprocess.TimeoutExpired, ValueError):
                pass

            return info

        except subprocess.TimeoutExpired:
            return {}

    def get_optimization_info(self) -> dict[str, Any]:
        """Get information about available PDF optimization methods."""
        return {
            "available_tools": self._available_tools,
            "supported_formats": self.get_supported_formats(),
            "ghostscript_command": getattr(self, "_gs_command", None),
            "ghostscript_version": getattr(self, "_gs_version", None),
            "quality_presets": {
                "maximum": "/prepress - Best quality for printing",
                "high": "/printer - High quality for printing",
                "medium": "/ebook - Good quality for screen viewing",
                "low": "/screen - Optimized for web/screen viewing",
            },
        }
