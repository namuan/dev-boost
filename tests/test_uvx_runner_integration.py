import tempfile
from pathlib import Path
from unittest.mock import patch

from devboost.config import ConfigManager
from devboost.tools.uvx_runner import UvxRunner


class TestUvxRunnerIntegration:
    """Integration tests for UVX Runner with ConfigManager."""

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

    def teardown_method(self):
        """Clean up after each test method."""
        # Stop the appdirs patcher
        self.appdirs_patcher.stop()

        # Reset global config manager
        import devboost.config

        devboost.config._config_manager = None

        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_uvx_runner_loads_default_config_on_initialization(self):
        """Test that UVX Runner loads default configuration on initialization."""
        uvx_runner = UvxRunner()

        # Verify default values are loaded
        assert uvx_runner.uvx_path == "/opt/homebrew/bin/uvx"
        assert "temp" in str(uvx_runner.working_directory)

        # Verify config file was created
        assert self.config_file.exists()

    def test_uvx_runner_loads_existing_config(self):
        """Test that UVX Runner loads existing configuration."""
        # Create a config manager and set custom values using temp directories
        config_manager = ConfigManager()
        custom_work_dir = str(Path(self.temp_dir) / "custom_work_dir")

        config_manager.set("uvx_runner.uvx_path", "/custom/path/uvx")
        config_manager.set("uvx_runner.working_directory", custom_work_dir)
        config_manager.set("uvx_runner.tools_list", ["custom_tool1", "custom_tool2"])

        # Create UVX Runner - it should load the existing config
        uvx_runner = UvxRunner()

        # Verify custom values are loaded
        assert uvx_runner.uvx_path == "/custom/path/uvx"
        assert str(uvx_runner.working_directory) == custom_work_dir
        assert uvx_runner.get_tools_list() == ["custom_tool1", "custom_tool2"]

    def test_uvx_runner_parameter_overrides_config(self):
        """Test that UVX Runner constructor parameter overrides config."""
        # Create a config manager and set custom values
        config_manager = ConfigManager()
        config_manager.set("uvx_runner.uvx_path", "/config/path/uvx")

        # Create UVX Runner with explicit parameter
        uvx_runner = UvxRunner(uvx_path="/param/path/uvx")

        # Verify parameter takes precedence
        assert uvx_runner.uvx_path == "/param/path/uvx"

    def test_set_uvx_path_persists_to_config(self):
        """Test that setting UVX path persists to configuration."""
        uvx_runner = UvxRunner()
        new_path = "/new/uvx/path"

        # Set new path
        uvx_runner.set_uvx_path(new_path)

        # Verify it's updated in the runner
        assert uvx_runner.uvx_path == new_path

        # Verify it's persisted to config
        config_manager = ConfigManager()
        assert config_manager.get("uvx_runner.uvx_path") == new_path

        # Create a new runner instance to verify persistence
        new_uvx_runner = UvxRunner()
        assert new_uvx_runner.uvx_path == new_path

    def test_set_working_directory_persists_to_config(self):
        """Test that setting working directory persists to configuration."""
        uvx_runner = UvxRunner()
        new_dir = "/new/work/directory"

        # Mock Path.mkdir to avoid creating actual directories
        with patch("pathlib.Path.mkdir"):
            uvx_runner.set_working_directory(new_dir)

        # Verify it's updated in the runner
        assert str(uvx_runner.working_directory) == new_dir

        # Verify it's persisted to config
        config_manager = ConfigManager()
        assert config_manager.get("uvx_runner.working_directory") == new_dir

        # Create a new runner instance to verify persistence
        with patch("pathlib.Path.mkdir"):
            new_uvx_runner = UvxRunner()
            assert str(new_uvx_runner.working_directory) == new_dir

    def test_tools_list_persistence(self):
        """Test that tools list operations persist to configuration."""
        uvx_runner = UvxRunner()

        # Initially empty
        assert uvx_runner.get_tools_list() == []

        # Add tools
        uvx_runner.add_tool_to_list("custom_tool1")
        uvx_runner.add_tool_to_list("custom_tool2")

        # Verify tools are added
        tools_list = uvx_runner.get_tools_list()
        assert "custom_tool1" in tools_list
        assert "custom_tool2" in tools_list

        # Verify persistence by getting the global config manager
        from devboost.config import get_config_manager

        config_manager = get_config_manager()
        persisted_tools = config_manager.get("uvx_runner.tools_list")
        assert "custom_tool1" in persisted_tools
        assert "custom_tool2" in persisted_tools

        # Remove a tool
        uvx_runner.remove_tool_from_list("custom_tool1")

        # Verify removal
        updated_tools = uvx_runner.get_tools_list()
        assert "custom_tool1" not in updated_tools
        assert "custom_tool2" in updated_tools

        # Verify persistence of removal using the same config manager
        updated_persisted_tools = config_manager.get("uvx_runner.tools_list")
        assert "custom_tool1" not in updated_persisted_tools
        assert "custom_tool2" in updated_persisted_tools

    def test_get_all_available_tools_includes_custom_tools(self):
        """Test that get_all_available_tools includes both predefined and custom tools."""
        uvx_runner = UvxRunner()

        # Add custom tools
        uvx_runner.add_tool_to_list("my_custom_tool")
        uvx_runner.add_tool_to_list("another_custom_tool")

        # Get all available tools
        all_tools = uvx_runner.get_all_available_tools()

        # Verify predefined tools are included
        assert "bump2version" in all_tools  # From UVX_TOOLS
        assert "cookiecutter" in all_tools  # From UVX_TOOLS

        # Verify custom tools are included
        assert "my_custom_tool" in all_tools
        assert "another_custom_tool" in all_tools

        # Verify custom tools have descriptions
        assert all_tools["my_custom_tool"] == "Custom tool (no description available)"
        assert all_tools["another_custom_tool"] == "Custom tool (no description available)"

    def test_duplicate_tool_addition_prevention(self):
        """Test that adding duplicate tools is prevented."""
        uvx_runner = UvxRunner()

        # Add a tool twice
        uvx_runner.add_tool_to_list("duplicate_tool")
        uvx_runner.add_tool_to_list("duplicate_tool")

        # Verify only one instance exists
        tools_list = uvx_runner.get_tools_list()
        assert tools_list.count("duplicate_tool") == 1

    def test_remove_nonexistent_tool_handling(self):
        """Test that removing non-existent tools is handled gracefully."""
        uvx_runner = UvxRunner()

        # Try to remove a tool that doesn't exist
        initial_tools = uvx_runner.get_tools_list()
        uvx_runner.remove_tool_from_list("nonexistent_tool")
        final_tools = uvx_runner.get_tools_list()

        # Verify no changes occurred
        assert initial_tools == final_tools

    def test_config_sharing_between_instances(self):
        """Test that configuration changes are properly shared between instances."""
        # Create first instance and modify config
        uvx_runner1 = UvxRunner()
        uvx_runner1.set_uvx_path("/shared/path/uvx")
        uvx_runner1.add_tool_to_list("shared_tool")

        # Create second instance
        uvx_runner2 = UvxRunner()

        # Verify second instance sees the changes
        assert uvx_runner2.uvx_path == "/shared/path/uvx"
        assert "shared_tool" in uvx_runner2.get_tools_list()

        # Modify config through second instance
        shared_work_dir = str(Path(self.temp_dir) / "shared_work_dir")
        uvx_runner2.set_working_directory(shared_work_dir)

        # Create a third instance to verify persistence
        uvx_runner3 = UvxRunner()
        assert str(uvx_runner3.working_directory) == shared_work_dir
        assert uvx_runner3.uvx_path == "/shared/path/uvx"
        assert "shared_tool" in uvx_runner3.get_tools_list()

    def test_config_thread_safety_with_uvx_runner(self):
        """Test that UVX Runner operations are thread-safe."""
        import threading
        import time

        uvx_runner = UvxRunner()
        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(5):
                    tool_name = f"worker_{worker_id}_tool_{i}"
                    uvx_runner.add_tool_to_list(tool_name)
                    tools = uvx_runner.get_tools_list()
                    results.append(tool_name in tools)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(str(e))

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert not errors, f"Thread safety errors: {errors}"

        # Verify all operations succeeded
        assert all(results), "Some thread operations failed"

        # Verify all tools were added
        final_tools = uvx_runner.get_tools_list()
        expected_tools = [f"worker_{i}_tool_{j}" for i in range(3) for j in range(5)]
        for tool in expected_tools:
            assert tool in final_tools, f"Tool {tool} was not found in final list"
