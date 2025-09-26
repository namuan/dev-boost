import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from devboost.config import ConfigManager, get_config, get_config_manager, set_config


class TestConfigManager:
    """Test cases for the ConfigManager class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset global config manager to avoid conflicts
        import devboost.config

        devboost.config._config_manager = None

        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "config.json"

        # Start patching appdirs for the entire test
        self.appdirs_patcher = patch("appdirs.user_data_dir", return_value=self.temp_dir)
        self.appdirs_patcher.start()

        # Create ConfigManager with test directory
        self.config_manager = ConfigManager()

    def teardown_method(self):
        """Clean up after each test method."""
        # Stop the appdirs patcher
        self.appdirs_patcher.stop()

        # Reset global config manager
        import devboost.config

        devboost.config._config_manager = None

        # Clean up temporary files
        if self.config_file.exists():
            self.config_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_initialization_creates_default_config(self):
        """Test that ConfigManager creates default configuration on initialization."""
        assert self.config_file.exists()

        with self.config_file.open("r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Check that default sections exist
        assert "uvx_runner" in config_data
        assert "scratch_pad" in config_data
        assert "global" in config_data

        # Check default values
        assert config_data["uvx_runner"]["uvx_path"] == "/opt/homebrew/bin/uvx"
        assert "temp" in config_data["uvx_runner"]["working_directory"]
        assert config_data["uvx_runner"]["tools_list"] == []
        assert config_data["scratch_pad"]["auto_save"] is True
        assert config_data["scratch_pad"]["font_size"] == 12

    def test_get_existing_key(self):
        """Test getting an existing configuration key."""
        value = self.config_manager.get("uvx_runner.uvx_path")
        assert value == "/opt/homebrew/bin/uvx"

    def test_get_nonexistent_key_returns_default(self):
        """Test getting a non-existent key returns the default value."""
        value = self.config_manager.get("nonexistent.key", "default_value")
        assert value == "default_value"

    def test_get_nonexistent_key_returns_none(self):
        """Test getting a non-existent key without default returns None."""
        value = self.config_manager.get("nonexistent.key")
        assert value is None

    def test_set_new_key(self):
        """Test setting a new configuration key."""
        # Create a fresh temporary directory for this test
        import shutil
        import tempfile

        test_temp_dir = tempfile.mkdtemp()
        test_config_file = Path(test_temp_dir) / "config.json"

        try:
            # Create a completely isolated ConfigManager
            with patch("appdirs.user_data_dir", return_value=test_temp_dir):
                isolated_config = ConfigManager()

                # Set a new key
                isolated_config.set("test.new_key", "test_value")

                # Verify it was saved
                value = isolated_config.get("test.new_key")
                assert value == "test_value"

                # Verify it was persisted to file
                assert test_config_file.exists()
                with test_config_file.open("r", encoding="utf-8") as f:
                    config_data = json.load(f)
                assert config_data["test"]["new_key"] == "test_value"
        finally:
            # Clean up
            shutil.rmtree(test_temp_dir, ignore_errors=True)

    def test_set_existing_key(self):
        """Test updating an existing configuration key."""
        self.config_manager.set("uvx_runner.uvx_path", "/custom/path/uvx")

        value = self.config_manager.get("uvx_runner.uvx_path")
        assert value == "/custom/path/uvx"

    def test_get_section(self):
        """Test getting an entire configuration section."""
        section = self.config_manager.get_section("uvx_runner")

        assert isinstance(section, dict)
        assert "uvx_path" in section
        assert "working_directory" in section
        assert "tools_list" in section

    def test_get_nonexistent_section(self):
        """Test getting a non-existent section returns empty dict."""
        section = self.config_manager.get_section("nonexistent_section")
        assert section == {}

    def test_update_section(self):
        """Test updating multiple values in a configuration section."""
        updates = {"uvx_path": "/new/path/uvx", "working_directory": "/new/work/dir"}

        self.config_manager.update_section("uvx_runner", updates)

        # Verify updates
        assert self.config_manager.get("uvx_runner.uvx_path") == "/new/path/uvx"
        assert self.config_manager.get("uvx_runner.working_directory") == "/new/work/dir"
        # Verify existing values are preserved
        assert self.config_manager.get("uvx_runner.tools_list") == []

    def test_update_nonexistent_section(self):
        """Test updating a non-existent section creates it."""
        updates = {"key1": "value1", "key2": "value2"}

        self.config_manager.update_section("new_section", updates)

        assert self.config_manager.get("new_section.key1") == "value1"
        assert self.config_manager.get("new_section.key2") == "value2"

    def test_reset_to_defaults(self):
        """Test resetting configuration to default values."""
        # Modify some values
        self.config_manager.set("uvx_runner.uvx_path", "/custom/path")
        self.config_manager.set("custom.key", "custom_value")

        # Reset to defaults
        self.config_manager.reset_to_defaults()

        # Verify defaults are restored
        assert self.config_manager.get("uvx_runner.uvx_path") == "/opt/homebrew/bin/uvx"
        assert self.config_manager.get("custom.key") is None

    def test_get_config_file_path(self):
        """Test getting the configuration file path."""
        path = self.config_manager.get_config_file_path()
        assert path == self.config_file
        assert isinstance(path, Path)

    def test_thread_safety(self):
        """Test that configuration operations are thread-safe."""
        import threading
        import time

        results = []

        def worker(worker_id):
            for i in range(10):
                key = f"thread_test.worker_{worker_id}.item_{i}"
                value = f"value_{worker_id}_{i}"
                self.config_manager.set(key, value)
                retrieved = self.config_manager.get(key)
                results.append(retrieved == value)
                time.sleep(0.001)  # Small delay to increase chance of race conditions

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should have succeeded
        assert all(results)

    def test_load_existing_config_file(self):
        """Test loading configuration from an existing file."""
        # Create a custom config file
        custom_config = {
            "uvx_runner": {
                "uvx_path": "/custom/uvx",
                "working_directory": "/custom/work",
                "tools_list": ["custom_tool"],
            },
            "custom_section": {"custom_key": "custom_value"},
        }

        with self.config_file.open("w", encoding="utf-8") as f:
            json.dump(custom_config, f)

        # Create new ConfigManager instance
        with patch("appdirs.user_data_dir", return_value=self.temp_dir):
            new_config_manager = ConfigManager()

        # Verify custom values are loaded
        assert new_config_manager.get("uvx_runner.uvx_path") == "/custom/uvx"
        assert new_config_manager.get("uvx_runner.working_directory") == "/custom/work"
        assert new_config_manager.get("uvx_runner.tools_list") == ["custom_tool"]
        assert new_config_manager.get("custom_section.custom_key") == "custom_value"

    def test_corrupted_config_file_fallback(self):
        """Test that corrupted config file falls back to defaults."""
        # Create corrupted config file
        with self.config_file.open("w", encoding="utf-8") as f:
            f.write("invalid json content")

        # Create new ConfigManager instance
        with patch("appdirs.user_data_dir", return_value=self.temp_dir):
            new_config_manager = ConfigManager()

        # Should fall back to defaults
        assert new_config_manager.get("uvx_runner.uvx_path") == "/opt/homebrew/bin/uvx"


class TestCrossPlatformStorage:
    """Test cases for cross-platform configuration storage."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after each test method."""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_macos_config_location(self):
        """Test configuration storage location on macOS."""
        # Use a temporary directory that mimics macOS structure
        macos_temp = Path(self.temp_dir) / "Users" / "testuser" / "Library" / "Application Support" / "DevBoost"
        expected_path = str(macos_temp)

        with patch("appdirs.user_data_dir", return_value=expected_path):
            config_manager = ConfigManager()
            config_path = config_manager.get_config_file_path()

            assert str(config_path) == f"{expected_path}/config.json"
            assert config_path.parent.name == "DevBoost"

    def test_windows_config_location(self):
        """Test configuration storage location on Windows."""
        windows_temp = Path(self.temp_dir) / "Users" / "testuser" / "AppData" / "Roaming" / "DeskRiders" / "DevBoost"
        expected_path = str(windows_temp)

        with patch("appdirs.user_data_dir", return_value=expected_path):
            config_manager = ConfigManager()
            config_path = config_manager.get_config_file_path()

            assert str(config_path) == f"{expected_path}/config.json"
            assert "DevBoost" in str(config_path)

    def test_linux_config_location(self):
        """Test configuration storage location on Linux."""
        # Use a temporary directory that mimics Linux structure
        linux_temp = Path(self.temp_dir) / "home" / "testuser" / ".local" / "share" / "DevBoost"
        expected_path = str(linux_temp)

        with patch("appdirs.user_data_dir", return_value=expected_path):
            config_manager = ConfigManager()
            config_path = config_manager.get_config_file_path()

            assert str(config_path) == f"{expected_path}/config.json"
            assert config_path.parent.name == "DevBoost"

    def test_config_file_permissions_handling(self):
        """Test handling of configuration file permissions across platforms."""
        with patch("appdirs.user_data_dir", return_value=self.temp_dir):
            config_manager = ConfigManager()

            # Test setting and getting values
            config_manager.set("test.permission_test", "test_value")
            value = config_manager.get("test.permission_test")

            assert value == "test_value"

            # Verify config file was created
            config_file = config_manager.get_config_file_path()
            assert config_file.exists()

            # Test that file is readable and writable
            assert config_file.is_file()
            with config_file.open("r", encoding="utf-8") as f:
                content = f.read()
                assert "test_value" in content


class TestGlobalFunctions:
    """Test cases for global convenience functions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset global config manager
        import devboost.config

        devboost.config._config_manager = None

    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns the same instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ConfigManager)

    def test_get_config_convenience_function(self):
        """Test the get_config convenience function."""
        value = get_config("uvx_runner.uvx_path")
        assert value == "/opt/homebrew/bin/uvx"

        # Test with default
        value = get_config("nonexistent.key", "default")
        assert value == "default"

    def test_set_config_convenience_function(self):
        """Test the set_config convenience function."""
        set_config("test.key", "test_value")

        value = get_config("test.key")
        assert value == "test_value"

    def teardown_method(self):
        """Clean up after each test method."""
        # Reset global config manager
        import devboost.config

        devboost.config._config_manager = None
