import json
import logging
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class QualityPreset(Enum):
    """Quality presets for optimization."""

    MAXIMUM = "maximum"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMUM = "minimum"


@dataclass
class OptimizationSettings:
    """Settings for file optimization operations."""

    # General settings
    quality_preset: QualityPreset = QualityPreset.MEDIUM
    create_backup: bool = True
    preserve_metadata: bool = False

    # Image settings
    image_quality: int | None = None  # Custom quality (0-100)
    max_width: int | None = None
    max_height: int | None = None
    output_format: str | None = None  # Force specific output format
    progressive_jpeg: bool = True

    # Video settings
    video_quality: int | None = None  # Custom quality (0-51 for x264)
    video_bitrate: str | None = None  # e.g., "1M", "500k"
    video_fps: int | None = None

    # PDF settings
    pdf_quality: int | None = None  # Custom quality (0-100)
    pdf_dpi: int | None = None  # DPI for images in PDF

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        data = asdict(self)
        # Convert enum to string
        data["quality_preset"] = self.quality_preset.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationSettings":
        """Create settings from dictionary."""
        # Convert string back to enum
        if "quality_preset" in data:
            data["quality_preset"] = QualityPreset(data["quality_preset"])
        return cls(**data)

    def get_quality_for_type(self, file_type: str) -> int:
        """Get quality value for specific file type based on preset."""
        quality_map = {
            QualityPreset.MAXIMUM: {"image": 95, "video": 18, "pdf": 90},
            QualityPreset.HIGH: {"image": 85, "video": 23, "pdf": 80},
            QualityPreset.MEDIUM: {"image": 75, "video": 28, "pdf": 70},
            QualityPreset.LOW: {"image": 60, "video": 35, "pdf": 60},
            QualityPreset.MINIMUM: {"image": 40, "video": 45, "pdf": 50},
        }

        # Use custom quality if specified
        if file_type == "image" and self.image_quality is not None:
            return self.image_quality
        if file_type == "video" and self.video_quality is not None:
            return self.video_quality
        if file_type == "pdf" and self.pdf_quality is not None:
            return self.pdf_quality

        # Use preset quality
        return quality_map[self.quality_preset].get(file_type, 75)


@dataclass
class OptimizationPreset:
    """Predefined optimization preset with settings and metadata."""

    name: str
    description: str
    settings: OptimizationSettings
    is_builtin: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert preset to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "settings": self.settings.to_dict(),
            "is_builtin": self.is_builtin,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationPreset":
        """Create preset from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            settings=OptimizationSettings.from_dict(data["settings"]),
            is_builtin=data.get("is_builtin", False),
        )


logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages optimization settings and presets."""

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize settings manager.

        Args:
            config_dir: Optional custom config directory path
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.settings_file = self.config_dir / "optimization_settings.json"
        self.presets_file = self.config_dir / "optimization_presets.json"

        self._ensure_config_dir()
        self._current_settings = OptimizationSettings()
        self._presets: dict[str, OptimizationPreset] = {}

        # Load settings and presets
        self._load_builtin_presets()
        self.load_settings()
        self.load_presets()

    def _get_default_config_dir(self) -> Path:
        """Get the default config directory path using standard OS locations."""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "DevBoost" / "file_optimization"
        elif system == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                config_dir = Path(appdata) / "DevBoost" / "file_optimization"
            else:
                config_dir = Path.home() / "AppData" / "Roaming" / "DevBoost" / "file_optimization"
        else:  # Linux and other Unix-like systems
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                config_dir = Path(xdg_config) / "DevBoost" / "file_optimization"
            else:
                config_dir = Path.home() / ".config" / "DevBoost" / "file_optimization"

        return config_dir

    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Config directory ensured: %s", self.config_dir)
        except Exception:
            logger.exception("Failed to create config directory %s", self.config_dir)

    def _load_builtin_presets(self):
        """Load built-in optimization presets."""
        builtin_presets = [
            OptimizationPreset(
                name="Web Optimized",
                description="Optimized for web use with good quality and small file sizes",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.MEDIUM,
                    max_width=1920,
                    max_height=1080,
                    progressive_jpeg=True,
                    create_backup=True,
                ),
            ),
            OptimizationPreset(
                name="Email Friendly",
                description="Small file sizes suitable for email attachments",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.LOW, max_width=1024, max_height=768, create_backup=True
                ),
            ),
            OptimizationPreset(
                name="High Quality",
                description="Minimal compression with maximum quality retention",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.HIGH, preserve_metadata=True, create_backup=True
                ),
            ),
            OptimizationPreset(
                name="Maximum Compression",
                description="Aggressive compression for minimum file sizes",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.MINIMUM, max_width=800, max_height=600, create_backup=True
                ),
            ),
            OptimizationPreset(
                name="Social Media",
                description="Optimized for social media platforms",
                settings=OptimizationSettings(
                    quality_preset=QualityPreset.MEDIUM,
                    max_width=1200,
                    max_height=1200,
                    progressive_jpeg=True,
                    create_backup=True,
                ),
            ),
        ]

        for preset in builtin_presets:
            self._presets[preset.name] = preset

    def get_current_settings(self) -> OptimizationSettings:
        """Get current optimization settings."""
        return self._current_settings

    def set_current_settings(self, settings: OptimizationSettings):
        """Set current optimization settings."""
        self._current_settings = settings

    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            with self.settings_file.open("w") as f:
                json.dump(self._current_settings.to_dict(), f, indent=2)
            logger.info("Settings saved to %s", self.settings_file)
            return True
        except Exception:
            logger.exception("Failed to save settings")
            return False

    def load_settings(self) -> bool:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with self.settings_file.open() as f:
                    data = json.load(f)
                self._current_settings = OptimizationSettings.from_dict(data)
                logger.info("Settings loaded from %s", self.settings_file)
                return True
        except Exception:
            logger.exception("Failed to load settings")

        # Use default settings if loading fails
        self._current_settings = OptimizationSettings()
        return False

    def get_presets(self) -> dict[str, OptimizationPreset]:
        """Get all available presets."""
        return self._presets.copy()

    def get_preset(self, name: str) -> OptimizationPreset | None:
        """Get a specific preset by name."""
        return self._presets.get(name)

    def add_preset(self, preset: OptimizationPreset) -> bool:
        """Add a new preset."""
        try:
            self._presets[preset.name] = preset
            return self.save_presets()
        except Exception:
            logger.exception("Failed to add preset {preset.name}")
            return False

    def remove_preset(self, name: str) -> bool:
        """Remove a preset (only custom presets can be removed)."""
        try:
            if name in self._presets:
                preset = self._presets[name]
                if not preset.is_builtin:
                    del self._presets[name]
                    return self.save_presets()
                logger.warning("Cannot remove builtin preset: %s", name)
                return False
            return True
        except Exception:
            logger.exception("Failed to remove preset {name}")
            return False

    def save_presets(self) -> bool:
        """Save custom presets to file."""
        try:
            # Only save custom presets
            custom_presets = {name: preset.to_dict() for name, preset in self._presets.items() if not preset.is_builtin}

            with self.presets_file.open("w") as f:
                json.dump(custom_presets, f, indent=2)
            logger.info("Custom presets saved to %s", self.presets_file)
            return True
        except Exception:
            logger.exception("Failed to save presets")
            return False

    def load_presets(self) -> bool:
        """Load custom presets from file."""
        try:
            if self.presets_file.exists():
                with self.presets_file.open() as f:
                    data = json.load(f)

                for name, preset_data in data.items():
                    preset = OptimizationPreset.from_dict(preset_data)
                    preset.is_builtin = False  # Ensure loaded presets are marked as custom
                    self._presets[name] = preset

                logger.info("Custom presets loaded from %s", self.presets_file)
                return True
        except Exception:
            logger.exception("Failed to load custom presets")

        return False

    def apply_preset(self, preset_name: str) -> bool:
        """Apply a preset to current settings."""
        preset = self.get_preset(preset_name)
        if preset:
            self._current_settings = OptimizationSettings.from_dict(preset.settings.to_dict())
            return True
        return False

    def validate_settings(self, settings: OptimizationSettings) -> list[str]:
        """
        Validate optimization settings and return list of errors.

        Args:
            settings: Settings to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate image quality
        if settings.image_quality is not None and not (0 <= settings.image_quality <= 100):
            errors.append("Image quality must be between 0 and 100")

        # Validate video quality (x264 CRF scale)
        if settings.video_quality is not None and not (0 <= settings.video_quality <= 51):
            errors.append("Video quality must be between 0 and 51")

        # Validate PDF quality
        if settings.pdf_quality is not None and not (0 <= settings.pdf_quality <= 100):
            errors.append("PDF quality must be between 0 and 100")

        # Validate dimensions
        if settings.max_width is not None and settings.max_width <= 0:
            errors.append("Maximum width must be positive")

        if settings.max_height is not None and settings.max_height <= 0:
            errors.append("Maximum height must be positive")

        # Validate video FPS
        if settings.video_fps is not None and settings.video_fps <= 0:
            errors.append("Video FPS must be positive")

        # Validate PDF DPI
        if settings.pdf_dpi is not None and not (72 <= settings.pdf_dpi <= 600):
            errors.append("PDF DPI must be between 72 and 600")

        # Validate video bitrate format
        if settings.video_bitrate is not None:
            import re

            if not re.match(r"^\d+[kKmM]?$", settings.video_bitrate):
                errors.append("Video bitrate must be in format like '1M', '500k', or '1000'")

        return errors
