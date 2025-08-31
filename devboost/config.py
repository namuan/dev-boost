import json
import logging
from pathlib import Path
from threading import RLock
from typing import Any

import appdirs

# Logger for debugging
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration manager for DevBoost application.

    Provides thread-safe access to user configuration stored in platform-appropriate
    locations using JSON format. Supports default values, validation, and migration.
    """

    def __init__(self, app_name: str = "DevBoost", app_author: str = "DeskRiders"):
        """
        Initialize the ConfigManager.

        Args:
            app_name: Name of the application for directory creation
            app_author: Author/organization name for directory creation
        """
        self.app_name = app_name
        self.app_author = app_author
        self.data_dir = appdirs.user_data_dir(app_name, app_author)
        self.config_file = Path(self.data_dir) / "config.json"
        self._config_lock = RLock()
        self._config_cache: dict[str, Any] | None = None

        # Ensure data directory exists
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)

        # Load initial configuration
        self._load_config()

        logger.info("ConfigManager initialized with config file: %s", self.config_file)

    def _load_config(self) -> dict[str, Any]:
        """
        Load configuration from file with thread safety.

        Returns:
            Dictionary containing the configuration data
        """
        with self._config_lock:
            if self._config_cache is not None:
                return self._config_cache

            try:
                if self.config_file.exists():
                    with self.config_file.open("r", encoding="utf-8") as f:
                        self._config_cache = json.load(f)
                        logger.debug("Configuration loaded from file")
                else:
                    self._config_cache = self._get_default_config()
                    self._save_config()
                    logger.info("Created new configuration file with defaults")
            except (json.JSONDecodeError, OSError):
                logger.exception("Failed to load configuration. Using defaults.")
                self._config_cache = self._get_default_config()

            return self._config_cache

    def _save_config(self) -> None:
        """
        Save configuration to file with thread safety.
        """
        try:
            with self.config_file.open("w", encoding="utf-8") as f:
                json.dump(self._config_cache, f, indent=2, ensure_ascii=False)
                logger.debug("Configuration saved to file")
        except OSError:
            logger.exception("Failed to save configuration")

    def _get_default_config(self) -> dict[str, Any]:
        """
        Get the default configuration structure.

        Returns:
            Dictionary containing default configuration values
        """
        return {
            "uvx_runner": {
                "uvx_path": "/opt/homebrew/bin/uvx",
                "working_directory": str(Path.home() / "temp"),
                "tools_list": [],
            },
            "scratch_pad": {"auto_save": True, "font_size": 12},
            "global": {"theme": "default", "last_used_tool": ""},
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the configuration key (e.g., "uvx_runner.uvx_path")
            default: Default value to return if key is not found

        Returns:
            The configuration value or default if not found
        """
        config = self._load_config()

        try:
            keys = key_path.split(".")
            value = config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            logger.debug("Configuration key '%s' not found, returning default: %s", key_path, default)
            return default

    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the configuration key (e.g., "uvx_runner.uvx_path")
            value: Value to set
        """
        with self._config_lock:
            config = self._load_config()

            keys = key_path.split(".")
            current = config

            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set the final value
            current[keys[-1]] = value

            # Save the updated configuration
            self._save_config()

            logger.debug("Configuration key '%s' set to: %s", key_path, value)

    def get_section(self, section: str) -> dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            section: Name of the configuration section

        Returns:
            Dictionary containing the section data or empty dict if not found
        """
        return self.get(section, {})

    def update_section(self, section: str, updates: dict[str, Any]) -> None:
        """
        Update multiple values in a configuration section.

        Args:
            section: Name of the configuration section
            updates: Dictionary of key-value pairs to update
        """
        with self._config_lock:
            config = self._load_config()

            if section not in config:
                config[section] = {}

            config[section].update(updates)
            self._save_config()

            logger.debug("Configuration section '%s' updated with: %s", section, updates)

    def reset_to_defaults(self) -> None:
        """
        Reset configuration to default values.
        """
        with self._config_lock:
            self._config_cache = self._get_default_config()
            self._save_config()
            logger.info("Configuration reset to defaults")

    def get_config_file_path(self) -> Path:
        """
        Get the path to the configuration file.

        Returns:
            Path object pointing to the configuration file
        """
        return self.config_file


# Global configuration manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.

    Returns:
        ConfigManager instance (singleton)
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(key_path: str, default: Any = None) -> Any:
    """
    Convenience function to get a configuration value.

    Args:
        key_path: Dot-separated path to the configuration key
        default: Default value to return if key is not found

    Returns:
        The configuration value or default if not found
    """
    return get_config_manager().get(key_path, default)


def set_config(key_path: str, value: Any) -> None:
    """
    Convenience function to set a configuration value.

    Args:
        key_path: Dot-separated path to the configuration key
        value: Value to set
    """
    get_config_manager().set(key_path, value)
