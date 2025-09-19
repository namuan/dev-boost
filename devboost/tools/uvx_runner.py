import logging
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.config import get_config_manager
from devboost.styles import get_autocomplete_dropdown_style, get_status_style, get_tool_style

# Logger for debugging
logger = logging.getLogger(__name__)

# Predefined uvx tools with descriptions
UVX_TOOLS = {
    "bump2version": "Version-bump your software with a single command",
    "catsql": "Filter and analyze CSV, TSV, JSON, and SQLite files",
    "cookiecutter": "Command-line utility for creating projects from templates",
    "gallery-dl": "Download image galleries and collections from websites",
    "grip": "GitHub Readme Instant Preview - render local README files",
    "hjson": "Human JSON - a user interface for JSON",
    "ini2toml": "Convert INI files to TOML format",
    "jc": "Converts command output to JSON for easier parsing",
    "jello": "CLI tool to filter JSON and JSON Lines with Python syntax",
    "keyring": "Store and access your passwords safely",
    "lice": "Generate software licenses",
    "lineinfile": "Add/remove lines from files",
    "locust": "Scalable user load testing tool",
    "mammoth": "Convert Word documents to HTML",
    "markdown-toc": "Generate table of contents for Markdown files",
    "netaddr": "Network address manipulation library",
    "nt2": "Network troubleshooting tools",
    "pip-audit": "Audit Python environments for known vulnerabilities",
    "pip-deptree": "Display dependency tree of installed Python packages",
    "pip-rot": "Check for outdated requirements",
    "pip-show": "Show package information",
    "pip-tools": "Utilities to manage Python package dependencies",
    "prospector": "Analyse Python code and output information",
    "pudb": "Full-screen console debugger for Python",
    "pur": "Update requirements.txt files to latest versions",
    "py-spy": "Sampling profiler for Python programs",
    "rainbow": "Colorize text with ANSI escape codes",
    "rbtools": "CLI for code review workflows",
    "req2toml": "Convert requirements.txt to pyproject.toml format",
    "restview": "ReStructuredText viewer with live preview",
    "rich-cli": "Rich text and beautiful formatting in the terminal",
    "scriv": "Changelog management tool",
    "subdl": "Subtitle downloader for movies and TV shows",
    "taskipy": "Task runner for Python projects",
    "tldr": "Simplified man pages",
    "videogrep": "Search and create video clips based on subtitle content",
    "watchdog": "File system events monitoring",
    "wheezy.template": "Lightweight template engine",
    "yamlpath": "Command-line tools for YAML/JSON querying",
    "yolk3k": "Query PyPI and retrieve package information",
    "yt-dlp": "YouTube downloader with enhanced features",
}


class UvxRunner(QObject):
    """
    Backend uvx runner logic with proper process management and output handling.
    """

    command_started = pyqtSignal()
    command_finished = pyqtSignal(int)  # exit_code
    command_failed = pyqtSignal(str)  # error_message
    output_received = pyqtSignal(str)  # output_text
    help_received = pyqtSignal(str)  # help_text

    def __init__(self, uvx_path: str | None = None):
        super().__init__()
        self.process = None
        # Load configuration
        config_manager = get_config_manager()

        # Set up working directory from config or default
        self.working_directory = Path(config_manager.get("uvx_runner.working_directory", str(Path.home() / "temp")))
        # Create the directory if it doesn't exist
        Path(self.working_directory).mkdir(parents=True, exist_ok=True)

        # Set uvx path from config, parameter, or default
        if uvx_path is not None:
            self.uvx_path = uvx_path
        else:
            self.uvx_path = config_manager.get("uvx_runner.uvx_path", "/opt/homebrew/bin/uvx")

        logger.info(
            "UvxRunner initialized with working directory: %s and uvx path: %s", self.working_directory, self.uvx_path
        )

    def _parse_installed_tools(self, uvx_output: str) -> list[str]:
        """Parse uvx list output to extract installed tool names."""
        installed_tools = []
        if uvx_output.strip():
            for line in uvx_output.strip().split("\n"):
                line = line.strip()
                # Skip empty lines and warning messages
                if (
                    line
                    and not line.startswith("   ")
                    and not line.startswith("One or more")
                    and not line.startswith("They were likely")
                    and not line.startswith("Please uninstall")
                    and "⚠️" not in line
                ):
                    # Extract package name (first word before version)
                    package_name = line.split()[0]
                    installed_tools.append(package_name)
        return installed_tools

    def _get_tool_help_text(self, tool_name: str, help_result) -> str:
        """Generate help text from tool --help command result."""
        if help_result.returncode == 0:
            help_text = f"Help for {tool_name}:\n\n{help_result.stdout}"
            if help_result.stderr:
                help_text += f"\n\nAdditional info:\n{help_result.stderr}"
        else:
            help_text = f"Could not get help for {tool_name}.\n\n"
            help_text += f"Description: {UVX_TOOLS[tool_name]}\n\n"
            if help_result.stderr:
                help_text += f"Error: {help_result.stderr}"
        return help_text

    def get_tool_help(self, tool_name: str) -> None:
        """
        Get help information for a specific uvx tool.

        Args:
            tool_name: Name of the uvx tool to get help for
        """
        logger.info("Getting help for uvx tool: %s", tool_name)

        available_tools = self.get_all_available_tools()
        if not tool_name or tool_name not in available_tools:
            self.help_received.emit("Please select a valid tool from the dropdown.")
            return

        try:
            # Get help directly from the tool using uvx
            # ruff: noqa: S603
            help_result = subprocess.run(
                [self.uvx_path, tool_name, "--help"], capture_output=True, text=True, timeout=15
            )

            help_text = self._get_tool_help_text(tool_name, help_result)
            self.help_received.emit(help_text)
            logger.debug("Help retrieved successfully for %s", tool_name)

        except subprocess.TimeoutExpired:
            error_msg = f"Timeout while getting help for {tool_name}"
            logger.exception(error_msg)
            self.help_received.emit(f"Error: {error_msg}")
        except Exception as e:
            error_msg = f"Error getting help for {tool_name}: {e!s}"
            logger.exception(error_msg)
            self.help_received.emit(f"Error: {error_msg}")

    def run_tool(self, tool_name: str, arguments: str) -> None:
        """
        Run a uvx tool with the provided arguments.

        Args:
            tool_name: Name of the tool to run
            arguments: Command line arguments for the tool
        """
        available_tools = self.get_all_available_tools()
        if not tool_name or tool_name not in available_tools:
            self.command_failed.emit("Please select a valid tool from the dropdown.")
            return

        logger.info("Running uvx tool: %s with arguments: %s", tool_name, arguments)

        # Build command
        cmd = [self.uvx_path, tool_name]
        if arguments.strip():
            # Simple argument splitting - could be enhanced for more complex cases
            cmd.extend(arguments.strip().split())

        self._run_command(cmd)

    def _run_command(self, cmd: list[str]) -> None:
        """
        Execute a command using QProcess for non-blocking execution.

        Args:
            cmd: Command and arguments as a list
        """
        # Validate that the command executable exists or is discoverable
        exe = cmd[0] if cmd else ""
        if not exe:
            self.command_failed.emit("Error: Command not found: ")
            return
        exe_path = Path(exe)
        if not (exe_path.exists() or shutil.which(exe) is not None):
            self.command_failed.emit(f"Error: Command not found: {exe}")
            return

        # Ensure we don't start if another process is already running
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.command_failed.emit("Another command is already running. Please wait for it to finish.")
            return

        self.process = QProcess()
        # Set the working directory
        self.process.setWorkingDirectory(str(self.working_directory))
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)
        self.process.errorOccurred.connect(self._handle_error)

        # Start the process directly without shell wrapping
        exe = cmd[0]
        args = cmd[1:]
        logger.info("Starting process: %s %s in directory: %s", exe, " ".join(args), self.working_directory)
        self.command_started.emit()
        self.process.start(exe, args)

        if not self.process.waitForStarted(5000):
            error_msg = f"Failed to start command: {exe} {' '.join(args)}"
            logger.error(error_msg)
            self.command_failed.emit(error_msg)

    def set_uvx_path(self, uvx_path: str) -> None:
        """
        Set the path to the uvx executable and save to configuration.

        Args:
            uvx_path: Path to the uvx executable
        """
        self.uvx_path = uvx_path
        # Save to configuration
        config_manager = get_config_manager()
        config_manager.set("uvx_runner.uvx_path", uvx_path)
        logger.info("Uvx path updated to: %s", uvx_path)

    def set_working_directory(self, working_directory: str) -> None:
        """
        Set the working directory and save to configuration.

        Args:
            working_directory: Path to the working directory
        """
        self.working_directory = Path(working_directory)
        # Ensure working directory exists
        Path(self.working_directory).mkdir(parents=True, exist_ok=True)
        # Save to configuration
        config_manager = get_config_manager()
        config_manager.set("uvx_runner.working_directory", str(self.working_directory))
        logger.info("Working directory updated to: %s", self.working_directory)

    def get_tools_list(self) -> list[str]:
        """
        Get the user's custom tools list from configuration.

        Returns:
            List of custom tool names
        """
        config_manager = get_config_manager()
        return config_manager.get("uvx_runner.tools_list", [])

    def add_tool_to_list(self, tool_name: str) -> None:
        """
        Add a tool to the user's custom tools list and save to configuration.

        Args:
            tool_name: Name of the tool to add
        """
        config_manager = get_config_manager()
        tools_list = self.get_tools_list()
        if tool_name not in tools_list:
            tools_list.append(tool_name)
            config_manager.set("uvx_runner.tools_list", tools_list)
            logger.info("Added tool '%s' to custom tools list", tool_name)

    def remove_tool_from_list(self, tool_name: str) -> None:
        """
        Remove a tool from the user's custom tools list and save to configuration.

        Args:
            tool_name: Name of the tool to remove
        """
        config_manager = get_config_manager()
        tools_list = self.get_tools_list()
        if tool_name in tools_list:
            tools_list.remove(tool_name)
            config_manager.set("uvx_runner.tools_list", tools_list)
            logger.info("Removed tool '%s' from custom tools list", tool_name)

    def get_all_available_tools(self) -> dict[str, str]:
        """
        Get all available tools including predefined and custom tools.

        Returns:
            Dictionary mapping tool names to descriptions
        """
        all_tools = UVX_TOOLS.copy()
        custom_tools = self.get_tools_list()
        for tool in custom_tools:
            if tool not in all_tools:
                all_tools[tool] = "Custom tool (no description available)"
        return all_tools

    def _handle_stdout(self):
        """Handle standard output from the running process."""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            if data:
                logger.debug("Stdout received: %s...", data[:100])
                self.output_received.emit(data)

    def _handle_stderr(self):
        """Handle standard error from the running process."""
        if self.process:
            data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
            if data:
                logger.debug("Stderr received: %s...", data[:100])
                self.output_received.emit(f"[STDERR] {data}")

    def _handle_finished(self, exit_code: int):
        """Handle process completion."""
        logger.info("Command finished with exit code: %d", exit_code)
        self.command_finished.emit(exit_code)
        self.process = None

    def _handle_error(self, error):
        """Handle process errors."""
        error_msg = f"Process error: {error}"
        logger.error(error_msg)
        self.command_failed.emit(error_msg)
        self.process = None

    def stop_command(self):
        """Stop the currently running command."""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            logger.info("Stopping running command")
            self.process.kill()
            self.process.waitForFinished(3000)
            self.process = None


def create_uvx_runner_widget(style_func, scratch_pad=None):
    """
    Creates the main widget for the Uvx Runner tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The main widget for the tool.
    """
    uvx_runner = UvxRunner()

    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    # Main layout
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Control section
    control_frame = QFrame()
    control_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    control_layout = QVBoxLayout(control_frame)
    control_layout.setContentsMargins(10, 10, 10, 10)
    control_layout.setSpacing(8)

    # Working directory selection
    dir_layout = QHBoxLayout()
    dir_layout.setSpacing(8)

    dir_label = QLabel("Working Directory:")
    dir_label.setFixedWidth(120)
    dir_layout.addWidget(dir_label)

    dir_input = QLineEdit()
    dir_input.setText(str(uvx_runner.working_directory))
    dir_layout.addWidget(dir_input)

    dir_button = QPushButton("Browse...")
    dir_layout.addWidget(dir_button)

    control_layout.addLayout(dir_layout)

    # Uvx path selection
    uvx_layout = QHBoxLayout()
    uvx_layout.setSpacing(8)

    uvx_label = QLabel("Uvx Path:")
    uvx_label.setFixedWidth(120)
    uvx_layout.addWidget(uvx_label)

    uvx_input = QLineEdit()
    uvx_input.setText(uvx_runner.uvx_path)
    uvx_layout.addWidget(uvx_input)

    uvx_button = QPushButton("Browse...")
    uvx_layout.addWidget(uvx_button)

    control_layout.addLayout(uvx_layout)

    # Tool selection with auto-completion
    tool_layout = QVBoxLayout()
    tool_layout.setSpacing(4)

    # Tool label
    tool_label = QLabel("Tool:")
    tool_layout.addWidget(tool_label)

    # Auto-completion input
    tool_input = QLineEdit()
    tool_input.setPlaceholderText("Type to search for tools...")
    tool_layout.addWidget(tool_input)

    # Tool suggestion list (hidden by default)
    tool_suggestions = QListWidget()
    tool_suggestions.setVisible(False)
    tool_suggestions.setMaximumHeight(150)  # Limit height to prevent overwhelming UI
    # Add custom styling to make the dropdown more visible
    tool_suggestions.setStyleSheet(get_autocomplete_dropdown_style())
    tool_layout.addWidget(tool_suggestions)

    # Focus event handlers
    def on_tool_input_focus_in(event):
        """Show all tools when input gains focus and is empty"""
        logger.debug("Tool input gained focus")
        if not tool_input.text().strip():
            show_suggestions("")  # Show all tools
        QLineEdit.focusInEvent(tool_input, event)

    def on_tool_input_focus_out(event):
        """Hide suggestions when input loses focus (with slight delay to allow clicks)"""
        logger.debug("Tool input lost focus")
        # Use a timer to delay hiding suggestions to allow clicking on items
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(150, lambda: tool_suggestions.setVisible(False) if not tool_suggestions.hasFocus() else None)
        QLineEdit.focusOutEvent(tool_input, event)

    # Override focus events for the tool_input
    tool_input.focusInEvent = on_tool_input_focus_in
    tool_input.focusOutEvent = on_tool_input_focus_out

    # Also hide suggestions when clicking elsewhere
    def on_tool_suggestions_focus_out(event):
        """Hide suggestions when they lose focus"""
        logger.debug("Tool suggestions lost focus")
        QListWidget.focusOutEvent(tool_suggestions, event)
        tool_suggestions.setVisible(False)

    tool_suggestions.focusOutEvent = on_tool_suggestions_focus_out

    # Store tool items with name and description for better filtering
    tool_items = []
    for tool_name, description in uvx_runner.get_all_available_tools().items():
        display_text = f"{tool_name} - {description}"
        tool_items.append((tool_name, display_text))

    # Current selected tool
    current_selected_tool = {"name": "", "display": ""}

    # Filter and show suggestions function
    def show_suggestions(text):
        logger.debug("show_suggestions called with text: '%s'", text)
        filter_text = text.lower().strip()
        logger.debug("Filter text after processing: '%s'", filter_text)

        # Clear current suggestions
        tool_suggestions.clear()
        logger.debug("Cleared tool suggestions")

        # Find matching tools
        matched_items = []
        for tool_name, display_text in tool_items:
            if not filter_text or filter_text in tool_name.lower() or filter_text in display_text.lower():
                matched_items.append((tool_name, display_text))

        logger.debug("Found %d matching items", len(matched_items))

        # Add matched items to suggestion list
        for tool_name, display_text in matched_items:
            tool_suggestions.addItem(display_text)
            list_item = tool_suggestions.item(tool_suggestions.count() - 1)
            if list_item:
                list_item.setData(Qt.ItemDataRole.UserRole, tool_name)
                logger.debug("Added item: '%s' with tool name: '%s'", display_text, tool_name)

        # Show/hide suggestions based on matches
        # Show all tools when input is focused but empty, otherwise filter
        if matched_items and (filter_text or tool_input.hasFocus()):
            tool_suggestions.setVisible(True)
            logger.debug("Set tool suggestions visible")
        else:
            tool_suggestions.setVisible(False)
            current_selected_tool["name"] = ""
            current_selected_tool["display"] = ""
            logger.debug("Set tool suggestions hidden and cleared current selection")

        # Auto-select first item if only one match
        if len(matched_items) == 1:
            tool_suggestions.setCurrentRow(0)
            current_selected_tool["name"] = matched_items[0][0]
            current_selected_tool["display"] = matched_items[0][1]
            logger.debug("Auto-selected single match: '%s'", matched_items[0][1])
        elif len(matched_items) == 0 and filter_text:
            # No matches found
            tool_suggestions.addItem("No matching tools found")
            tool_suggestions.setCurrentRow(0)
            current_selected_tool["name"] = ""
            current_selected_tool["display"] = ""
            logger.debug("Added 'No matching tools found' item")

    # Handle selection from suggestions
    def on_suggestion_selected():
        logger.debug("on_suggestion_selected called")
        selected_items = tool_suggestions.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            tool_name = selected_item.data(Qt.ItemDataRole.UserRole)
            display_text = selected_item.text()
            logger.debug("Selected tool: name='%s', display='%s'", tool_name, display_text)
            if tool_name:  # Make sure it's not the "no results" item
                tool_input.setText(display_text)
                current_selected_tool["name"] = tool_name
                current_selected_tool["display"] = display_text
                tool_suggestions.setVisible(False)
                tool_input.setFocus()  # Return focus to input field
                logger.debug("Tool selection completed and suggestions hidden")
            else:
                logger.debug("Selected item was 'no results' item, not setting tool")
        else:
            logger.debug("No selected items found")

    # Handle keyboard navigation in suggestions
    def on_tool_input_key_press(event):
        logger.debug("Key press event received: key=%d, text='%s'", event.key(), event.text())

        if tool_suggestions.isVisible():
            logger.debug("Tool suggestions are visible")
            if event.key() == Qt.Key.Key_Down:
                logger.debug("Down arrow key pressed")
                current_row = tool_suggestions.currentRow()
                logger.debug("Current row: %d, Total rows: %d", current_row, tool_suggestions.count())
                if current_row < tool_suggestions.count() - 1:
                    tool_suggestions.setCurrentRow(current_row + 1)
                    logger.debug("Set current row to: %d", current_row + 1)
                return
            if event.key() == Qt.Key.Key_Up:
                logger.debug("Up arrow key pressed")
                current_row = tool_suggestions.currentRow()
                logger.debug("Current row: %d", current_row)
                if current_row > 0:
                    tool_suggestions.setCurrentRow(current_row - 1)
                    logger.debug("Set current row to: %d", current_row - 1)
                return
            if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
                logger.debug("Enter key pressed")
                on_suggestion_selected()
                return
            if event.key() == Qt.Key.Key_Escape:
                logger.debug("Escape key pressed - executing reset logic")
                logger.debug("Hiding tool suggestions")
                tool_suggestions.setVisible(False)
                logger.debug("Clearing tool input")
                tool_input.clear()
                logger.debug("Resetting current selected tool")
                current_selected_tool["name"] = ""
                current_selected_tool["display"] = ""
                logger.debug("ESC key handling completed")
                return
            logger.debug("Other key pressed while suggestions visible: %d", event.key())
        else:
            logger.debug("Tool suggestions are NOT visible")
            if event.key() == Qt.Key.Key_Escape:
                logger.debug("Escape key pressed while suggestions hidden - executing reset logic")
                logger.debug("Clearing tool input")
                tool_input.clear()
                logger.debug("Resetting current selected tool")
                current_selected_tool["name"] = ""
                current_selected_tool["display"] = ""
                logger.debug("ESC key handling completed")
                return

        logger.debug("Calling default key press event handler")
        # For all other keys, let the default behavior happen
        QLineEdit.keyPressEvent(tool_input, event)

        # After processing the key, update suggestions
        # This ensures that as the user types, the list filters properly
        show_suggestions(tool_input.text())

    # Override keyPressEvent for the tool_input
    tool_input.keyPressEvent = on_tool_input_key_press

    # Connect signals
    tool_input.textChanged.connect(show_suggestions)
    tool_suggestions.itemClicked.connect(on_suggestion_selected)
    tool_suggestions.itemActivated.connect(on_suggestion_selected)

    # Show all tools when the input field gains focus
    def on_tool_input_focus_in_wrapper(event):
        on_tool_input_focus_in(event)
        # If the input is empty, show all tools
        if not tool_input.text().strip():
            show_suggestions("")

    # Show all tools when input gains focus and is empty
    def on_tool_input_focus_in(event):
        QLineEdit.focusInEvent(tool_input, event)  # Call the original event handler
        if not tool_input.text().strip():
            show_suggestions("")  # Show all tools when empty and focused

    tool_input.focusInEvent = on_tool_input_focus_in

    # Also show all tools when the user clicks on the input field
    def on_tool_input_mouse_press(event):
        QLineEdit.mousePressEvent(tool_input, event)
        if not tool_input.text().strip():
            show_suggestions("")  # Show all tools when empty

    tool_input.mousePressEvent = on_tool_input_mouse_press

    control_layout.addLayout(tool_layout)

    # Arguments input
    args_layout = QHBoxLayout()
    args_layout.setSpacing(8)

    args_label = QLabel("Arguments:")
    args_label.setFixedWidth(80)
    args_layout.addWidget(args_label)

    args_input = QLineEdit()
    args_input.setPlaceholderText("Enter command line arguments (optional)")
    args_layout.addWidget(args_input)

    control_layout.addLayout(args_layout)

    # Action buttons
    button_layout = QHBoxLayout()
    button_layout.setSpacing(8)

    get_help_button = QPushButton("Get Help")
    run_button = QPushButton("Run Tool")
    stop_button = QPushButton("Stop")
    stop_button.setEnabled(False)

    button_layout.addWidget(get_help_button)
    button_layout.addWidget(run_button)
    button_layout.addWidget(stop_button)
    button_layout.addStretch()

    control_layout.addLayout(button_layout)

    # Progress bar
    progress_bar = QProgressBar()
    progress_bar.setVisible(False)
    progress_bar.setRange(0, 0)  # Indeterminate progress
    control_layout.addWidget(progress_bar)

    # Status label
    status_label = QLabel("Ready")
    status_label.setStyleSheet(get_status_style("info"))
    control_layout.addWidget(status_label)

    main_layout.addWidget(control_frame)

    # Output section
    output_frame = QFrame()
    output_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    output_layout = QVBoxLayout(output_frame)
    output_layout.setContentsMargins(10, 10, 10, 10)
    output_layout.setSpacing(8)

    # Output controls
    output_controls_layout = QHBoxLayout()
    output_label = QLabel("Output:")

    clear_output_button = QPushButton("Clear Output")
    copy_output_button = QPushButton("Copy Output")
    send_to_scratch_button = QPushButton("Send to Scratch Pad")

    output_controls_layout.addWidget(output_label)
    output_controls_layout.addStretch()
    output_controls_layout.addWidget(clear_output_button)
    output_controls_layout.addWidget(copy_output_button)
    if scratch_pad:
        output_controls_layout.addWidget(send_to_scratch_button)

    output_layout.addLayout(output_controls_layout)

    # Output text area
    output_text = QTextEdit()
    output_text.setReadOnly(True)
    output_text.setPlaceholderText("Command output will appear here...")
    output_layout.addWidget(output_text)

    main_layout.addWidget(output_frame)

    # Event handlers
    def on_browse_directory():
        directory = QFileDialog.getExistingDirectory(widget, "Select Working Directory", dir_input.text())
        if directory:
            dir_input.setText(directory)
            uvx_runner.set_working_directory(directory)
            status_label.setText(f"Working directory set to: {directory}")

    def on_browse_uvx():
        uvx_file, _ = QFileDialog.getOpenFileName(
            widget, "Select Uvx Executable", uvx_input.text(), "Executable Files (*)"
        )
        if uvx_file:
            uvx_input.setText(uvx_file)
            uvx_runner.set_uvx_path(uvx_file)
            status_label.setText(f"Uvx path set to: {uvx_file}")

    def on_get_help():
        logger.debug("on_get_help called. Current selected tool: %s", current_selected_tool)
        logger.debug("Tool input text: '%s'", tool_input.text())
        tool_name = (
            current_selected_tool["name"] if current_selected_tool["name"] else tool_input.text().split(" - ")[0]
        )
        logger.debug("Tool name to get help for: '%s'", tool_name)
        available_tools = uvx_runner.get_all_available_tools()
        if tool_name and tool_name in available_tools:
            logger.info("Getting help for tool: %s", tool_name)
            status_label.setText(f"Getting help for {tool_name}...")
            uvx_runner.get_tool_help(tool_name)
        else:
            logger.warning("Cannot get help - invalid tool: '%s'", tool_name)
            QMessageBox.warning(widget, "Warning", "Please select a valid tool first.")

    def on_install_tool():
        logger.debug("on_install_tool called. Current selected tool: %s", current_selected_tool)
        logger.debug("Tool input text: '%s'", tool_input.text())
        tool_name = (
            current_selected_tool["name"] if current_selected_tool["name"] else tool_input.text().split(" - ")[0]
        )
        logger.debug("Tool name to install: '%s'", tool_name)
        if tool_name and tool_name in UVX_TOOLS:
            logger.info("Installing tool: %s", tool_name)
            status_label.setText(f"Installing {tool_name}...")
            uvx_runner.install_tool(tool_name)
        else:
            logger.warning("Cannot install - invalid tool: '%s'", tool_name)
            QMessageBox.warning(widget, "Warning", "Please select a valid tool first.")

    def on_run_tool():
        logger.debug("on_run_tool called. Current selected tool: %s", current_selected_tool)
        logger.debug("Tool input text: '%s'", tool_input.text())
        # Update working directory from input field
        uvx_runner.set_working_directory(dir_input.text())

        tool_name = (
            current_selected_tool["name"] if current_selected_tool["name"] else tool_input.text().split(" - ")[0]
        )
        logger.debug("Tool name to run: '%s'", tool_name)
        available_tools = uvx_runner.get_all_available_tools()
        if tool_name and tool_name in available_tools:
            arguments = args_input.text().strip()
            logger.info(
                "Running tool: %s with args: %s in directory: %s",
                tool_name,
                arguments,
                uvx_runner.working_directory,
            )
            status_label.setText(f"Running {tool_name} in {uvx_runner.working_directory}...")
            uvx_runner.run_tool(tool_name, arguments)
        else:
            logger.warning("Cannot run - invalid tool: '%s'", tool_name)
            QMessageBox.warning(widget, "Warning", "Please select a valid tool first.")

    def on_stop_command():
        logger.info("Stopping command")
        uvx_runner.stop_command()
        status_label.setText("Command stopped")

    def on_clear_output():
        logger.debug("Clearing output")
        output_text.clear()

    def on_copy_output():
        text = output_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            status_label.setText("Output copied to clipboard")
            logger.debug("Output copied to clipboard")
        else:
            QMessageBox.information(widget, "Info", "No output to copy.")

    def on_send_to_scratch():
        if scratch_pad:
            text = output_text.toPlainText()
            if text:
                current_content = scratch_pad.get_content()
                new_content = f"{current_content}\n=== Uvx Runner Output ===\n{text}\n"
                scratch_pad.set_content(new_content)
                status_label.setText("Output sent to scratch pad")
                logger.debug("Output sent to scratch pad")
            else:
                QMessageBox.information(widget, "Info", "No output to send.")

    # Signal connections
    dir_button.clicked.connect(on_browse_directory)
    uvx_button.clicked.connect(on_browse_uvx)
    uvx_input.textChanged.connect(lambda text: uvx_runner.set_uvx_path(text) if text else None)
    get_help_button.clicked.connect(on_get_help)
    run_button.clicked.connect(on_run_tool)
    stop_button.clicked.connect(on_stop_command)
    clear_output_button.clicked.connect(on_clear_output)
    copy_output_button.clicked.connect(on_copy_output)
    if scratch_pad:
        send_to_scratch_button.clicked.connect(on_send_to_scratch)

    # Uvx runner signal connections
    def on_command_started():
        logger.debug("Command started - updating UI")
        progress_bar.setVisible(True)
        run_button.setEnabled(False)
        stop_button.setEnabled(True)
        status_label.setText(f"Command running in {uvx_runner.working_directory}...")

    def on_command_finished(exit_code):
        logger.debug("Command finished with exit code %d - updating UI", exit_code)
        progress_bar.setVisible(False)
        run_button.setEnabled(True)
        stop_button.setEnabled(False)
        if exit_code == 0:
            status_label.setText(f"Command completed successfully in {uvx_runner.working_directory}")
        else:
            status_label.setText(f"Command failed with exit code {exit_code} in {uvx_runner.working_directory}")

    def on_command_failed(error_message):
        logger.error("Command failed: %s", error_message)
        progress_bar.setVisible(False)
        run_button.setEnabled(True)
        stop_button.setEnabled(False)
        status_label.setText(f"Error: {error_message}")
        output_text.append(f"\n[ERROR] {error_message}\n")

    def on_output_received(text):
        logger.debug("Output received: %s...", text[:50])
        output_text.append(text)
        # Auto-scroll to bottom
        cursor = output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        output_text.setTextCursor(cursor)

    def on_help_received(help_text):
        logger.debug("Help text received")
        output_text.clear()
        output_text.append(help_text)
        status_label.setText("Help information displayed")

    uvx_runner.command_started.connect(on_command_started)
    uvx_runner.command_finished.connect(on_command_finished)
    uvx_runner.command_failed.connect(on_command_failed)
    uvx_runner.output_received.connect(on_output_received)
    uvx_runner.help_received.connect(on_help_received)

    logger.info("Uvx Runner widget created successfully")
    return widget
