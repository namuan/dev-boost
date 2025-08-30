import subprocess
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import QProcess

from devboost.tools.uvx_runner import (
    UVX_TOOLS,
    UvxRunner,
    create_uvx_runner_widget,
)


class TestUvxRunner:
    """Test cases for UvxRunner class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.uvx_runner = UvxRunner()

    def test_uvx_runner_initialization(self):
        """Test UvxRunner initialization."""
        assert self.uvx_runner is not None
        assert self.uvx_runner.process is None
        assert hasattr(self.uvx_runner, "command_started")
        assert hasattr(self.uvx_runner, "command_finished")
        assert hasattr(self.uvx_runner, "command_failed")
        assert hasattr(self.uvx_runner, "output_received")
        assert hasattr(self.uvx_runner, "help_received")

    def test_uvx_tools_constant(self):
        """Test that UVX_TOOLS constant is properly defined."""
        assert isinstance(UVX_TOOLS, dict)
        assert len(UVX_TOOLS) > 0

        # Check that all expected tools are present
        expected_tools = ["bump2version", "catsql", "cookiecutter", "gallery-dl", "grip"]
        for tool in expected_tools:
            assert tool in UVX_TOOLS
            assert isinstance(UVX_TOOLS[tool], str)
            assert len(UVX_TOOLS[tool]) > 0

    @patch("subprocess.run")
    def test_get_tool_help_tool_not_installed(self, mock_subprocess_run):
        """Test getting help for a tool that returns an error."""
        # Mock tool help command that fails
        help_result = Mock(stdout="", stderr="command not found", returncode=1)

        mock_subprocess_run.return_value = help_result

        help_text = None

        def capture_help(text):
            nonlocal help_text
            help_text = text

        self.uvx_runner.help_received.connect(capture_help)

        # Test getting help for bump2version
        self.uvx_runner.get_tool_help("bump2version")

        # Verify subprocess was called to get help
        mock_subprocess_run.assert_called_with(
            ["uvx", "bump2version", "--help"], capture_output=True, text=True, timeout=15
        )

        # Verify help text contains error information
        assert help_text is not None
        assert "Could not get help for bump2version" in help_text
        assert "Version-bump your software with a single command" in help_text

    @patch("subprocess.run")
    def test_get_tool_help_tool_installed(self, mock_subprocess_run):
        """Test getting help for a tool."""
        # Mock tool help command
        help_result = Mock(
            stdout="bump2version - Version-bump your software with a single command\nUsage: bump2version [OPTIONS]\n",
            stderr="",
            returncode=0,
        )

        mock_subprocess_run.return_value = help_result

        help_text = None

        def capture_help(text):
            nonlocal help_text
            help_text = text

        self.uvx_runner.help_received.connect(capture_help)

        # Test getting help for bump2version
        self.uvx_runner.get_tool_help("bump2version")

        # Verify subprocess was called to get help
        mock_subprocess_run.assert_called_with(
            ["uvx", "bump2version", "--help"], capture_output=True, text=True, timeout=15
        )

        # Verify help text contains tool help
        assert help_text is not None
        assert "Help for bump2version" in help_text
        assert "Version-bump your software with a single command" in help_text

    def test_get_tool_help_invalid_tool(self):
        """Test getting help for an invalid tool name."""
        help_text = None

        def capture_help(text):
            nonlocal help_text
            help_text = text

        self.uvx_runner.help_received.connect(capture_help)

        # Test with empty tool name
        self.uvx_runner.get_tool_help("")
        assert help_text == "Please select a valid tool from the dropdown."

        # Test with invalid tool name
        self.uvx_runner.get_tool_help("invalid-tool")
        assert help_text == "Please select a valid tool from the dropdown."

    @patch("subprocess.run")
    def test_get_tool_help_timeout(self, mock_subprocess_run):
        """Test handling of timeout when getting tool help."""
        # Mock timeout exception
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired("uvx", 10)

        help_text = None

        def capture_help(text):
            nonlocal help_text
            help_text = text

        self.uvx_runner.help_received.connect(capture_help)

        # Test getting help for bump2version
        self.uvx_runner.get_tool_help("bump2version")

        # Verify error message for timeout
        assert help_text is not None
        assert "Timeout" in help_text
        assert "bump2version" in help_text

    def test_run_tool_invalid_tool(self):
        """Test running an invalid tool."""
        error_message = None

        def capture_error(message):
            nonlocal error_message
            error_message = message

        self.uvx_runner.command_failed.connect(capture_error)

        # Test with empty tool name
        self.uvx_runner.run_tool("", "--help")
        assert error_message == "Please select a valid tool from the dropdown."

        # Test with invalid tool name
        self.uvx_runner.run_tool("invalid-tool", "--help")
        assert error_message == "Please select a valid tool from the dropdown."

    @patch("devboost.tools.uvx_runner.QProcess")
    def test_run_command_success(self, mock_qprocess_class):
        """Test successful command execution."""
        # Create mock QProcess instance
        mock_process = Mock()
        mock_process.state.return_value = QProcess.ProcessState.NotRunning
        mock_process.waitForStarted.return_value = True
        mock_qprocess_class.return_value = mock_process

        command_started = False

        def capture_started():
            nonlocal command_started
            command_started = True

        self.uvx_runner.command_started.connect(capture_started)

        # Test running a command
        self.uvx_runner._run_command(["pgcli", "--help"])

        # Verify QProcess was created and configured
        mock_qprocess_class.assert_called_once()
        mock_process.start.assert_called_once_with("pgcli", ["--help"])
        mock_process.waitForStarted.assert_called_once_with(5000)

        # Verify signal connections
        assert mock_process.readyReadStandardOutput.connect.called
        assert mock_process.readyReadStandardError.connect.called
        assert mock_process.finished.connect.called
        assert mock_process.errorOccurred.connect.called

        # Verify command started signal was emitted
        assert command_started

    @patch("devboost.tools.uvx_runner.QProcess")
    def test_run_command_already_running(self, mock_qprocess_class):
        """Test running a command when another is already running."""
        # Set up existing process
        existing_process = Mock()
        existing_process.state.return_value = QProcess.ProcessState.Running
        self.uvx_runner.process = existing_process

        error_message = None

        def capture_error(message):
            nonlocal error_message
            error_message = message

        self.uvx_runner.command_failed.connect(capture_error)

        # Try to run another command
        self.uvx_runner._run_command(["pgcli", "--help"])

        # Verify error message
        assert error_message == "Another command is already running. Please wait for it to finish."

        # Verify no new QProcess was created
        mock_qprocess_class.assert_not_called()

    def test_stop_command_no_process(self):
        """Test stopping command when no process is running."""
        # Should not raise any exception
        self.uvx_runner.stop_command()
        assert self.uvx_runner.process is None

    def test_stop_command_with_process(self):
        """Test stopping a running command."""
        # Set up mock process
        mock_process = Mock()
        mock_process.state.return_value = QProcess.ProcessState.Running
        mock_process.waitForFinished.return_value = True
        self.uvx_runner.process = mock_process

        # Stop the command
        self.uvx_runner.stop_command()

        # Verify process was killed
        mock_process.kill.assert_called_once()
        mock_process.waitForFinished.assert_called_once_with(3000)

        # Verify process was cleared
        assert self.uvx_runner.process is None

    def test_handle_stdout(self):
        """Test handling stdout from process."""
        # Set up mock process with stdout data
        mock_process = Mock()
        mock_stdout_data = Mock()
        mock_stdout_data.data.return_value = b"Test output\n"
        mock_process.readAllStandardOutput.return_value = mock_stdout_data
        self.uvx_runner.process = mock_process

        output_text = None

        def capture_output(text):
            nonlocal output_text
            output_text = text

        self.uvx_runner.output_received.connect(capture_output)

        # Call the handler
        self.uvx_runner._handle_stdout()

        # Verify output was captured
        assert output_text == "Test output\n"

    def test_handle_stderr(self):
        """Test handling stderr from process."""
        # Set up mock process with stderr data
        mock_process = Mock()
        mock_stderr_data = Mock()
        mock_stderr_data.data.return_value = b"Error message\n"
        mock_process.readAllStandardError.return_value = mock_stderr_data
        self.uvx_runner.process = mock_process

        output_text = None

        def capture_output(text):
            nonlocal output_text
            output_text = text

        self.uvx_runner.output_received.connect(capture_output)

        # Call the handler
        self.uvx_runner._handle_stderr()

        # Verify stderr output was captured with prefix
        assert output_text == "[STDERR] Error message\n"

    def test_handle_finished(self):
        """Test handling process completion."""
        exit_code = None

        def capture_finished(code):
            nonlocal exit_code
            exit_code = code

        self.uvx_runner.command_finished.connect(capture_finished)

        # Set up a mock process
        self.uvx_runner.process = Mock()

        # Call the handler
        self.uvx_runner._handle_finished(0)

        # Verify exit code was captured and process was cleared
        assert exit_code == 0
        assert self.uvx_runner.process is None

    def test_handle_error(self):
        """Test handling process errors."""
        error_message = None

        def capture_error(message):
            nonlocal error_message
            error_message = message

        self.uvx_runner.command_failed.connect(capture_error)

        # Set up a mock process
        self.uvx_runner.process = Mock()

        # Call the handler with a mock error
        mock_error = QProcess.ProcessError.FailedToStart
        self.uvx_runner._handle_error(mock_error)

        # Verify error was captured and process was cleared
        assert error_message is not None
        assert "Process error" in error_message
        assert self.uvx_runner.process is None


class TestUvxRunnerWidget:
    """Test cases for uvx runner widget creation and functionality."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self):
        """Ensure QApplication is available for widget tests."""
        import sys

        from PyQt6.QtWidgets import QApplication

        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        self.qapp = app

    def test_create_uvx_runner_widget(self):
        """Test creating the uvx runner widget."""
        # Mock style function
        style_func = Mock()

        # Create widget
        widget = create_uvx_runner_widget(style_func)

        # Verify widget was created
        assert widget is not None
        assert hasattr(widget, "setStyleSheet")

        # Verify widget has expected children (basic structure check)
        children = widget.findChildren(object)
        assert len(children) > 0

    def test_create_uvx_runner_widget_with_scratch_pad(self):
        """Test creating the uvx runner widget with scratch pad integration."""
        # Mock style function and scratch pad
        style_func = Mock()
        scratch_pad = Mock()
        scratch_pad.append_text = Mock()

        # Create widget
        widget = create_uvx_runner_widget(style_func, scratch_pad)

        # Verify widget was created
        assert widget is not None

        # Verify scratch pad integration is available
        # (This would require more detailed testing of button presence)
        children = widget.findChildren(object)
        assert len(children) > 0

    def test_uvx_tools_in_widget(self):
        """Test that the widget is created with proper tool selection components."""
        from PyQt6.QtWidgets import QLineEdit, QListWidget

        # Mock style function
        style_func = Mock()

        # Create widget
        widget = create_uvx_runner_widget(style_func)

        # Find the tool input and suggestions list
        tool_inputs = widget.findChildren(QLineEdit)
        tool_suggestions = widget.findChildren(QListWidget)

        # Should have at least one line edit (tool input) and one list widget (suggestions)
        assert len(tool_inputs) > 0
        assert len(tool_suggestions) > 0

        # Get the tool input (assuming it's the one with placeholder text related to tools)
        tool_input = None
        for inp in tool_inputs:
            if "tool" in inp.placeholderText().lower() or "search" in inp.placeholderText().lower():
                tool_input = inp
                break

        assert tool_input is not None

        # Verify the tool input has appropriate placeholder text
        assert "tool" in tool_input.placeholderText().lower() or "search" in tool_input.placeholderText().lower()

        # Verify the suggestions list exists
        assert len(tool_suggestions) > 0

        # Verify UVX_TOOLS constant is accessible (imported from the module)
        assert len(UVX_TOOLS) > 0
