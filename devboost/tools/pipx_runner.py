import logging
import subprocess

from PyQt6.QtCore import QObject, QProcess, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_status_style, get_tool_style

# Logger for debugging
logger = logging.getLogger(__name__)

# Predefined pipx tools with descriptions
PIPX_TOOLS = {
    "pgcli": "PostgreSQL command line interface with auto-completion and syntax highlighting",
    "req2toml": "Convert requirements.txt to pyproject.toml format",
    "restview": "ReStructuredText viewer with live preview",
    "yt-dlp": "YouTube downloader with enhanced features",
    "videogrep": "Search and create video clips based on subtitle content",
}


class PipxRunner(QObject):
    """
    Backend pipx runner logic with proper process management and output handling.
    """

    command_started = pyqtSignal()
    command_finished = pyqtSignal(int)  # exit_code
    command_failed = pyqtSignal(str)  # error_message
    output_received = pyqtSignal(str)  # output_text
    help_received = pyqtSignal(str)  # help_text

    def __init__(self):
        super().__init__()
        self.process = None
        logger.info("PipxRunner initialized")

    def get_tool_help(self, tool_name: str) -> None:
        """
        Get help information for a specific pipx tool.

        Args:
            tool_name: Name of the pipx tool to get help for
        """
        logger.info(f"Getting help for pipx tool: {tool_name}")

        if not tool_name or tool_name not in PIPX_TOOLS:
            self.help_received.emit("Please select a valid tool from the dropdown.")
            return

        try:
            # First check if tool is installed
            result = subprocess.run(["pipx", "list", "--short"], capture_output=True, text=True, timeout=10)  # noqa: S603, S607

            installed_tools = result.stdout.strip().split("\n") if result.stdout.strip() else []

            if tool_name not in installed_tools:
                help_text = f"Tool '{tool_name}' is not installed.\n\n"
                help_text += f"Description: {PIPX_TOOLS[tool_name]}\n\n"
                help_text += f"To install: pipx install {tool_name}\n\n"
                help_text += "You can install it using the 'Install Tool' button below."
                self.help_received.emit(help_text)
                return

            # Get help for installed tool
            help_result = subprocess.run([tool_name, "--help"], capture_output=True, text=True, timeout=15)  # noqa: S603

            if help_result.returncode == 0:
                help_text = f"Help for {tool_name}:\n\n{help_result.stdout}"
                if help_result.stderr:
                    help_text += f"\n\nAdditional info:\n{help_result.stderr}"
            else:
                help_text = f"Could not get help for {tool_name}.\n\n"
                help_text += f"Description: {PIPX_TOOLS[tool_name]}\n\n"
                if help_result.stderr:
                    help_text += f"Error: {help_result.stderr}"

            self.help_received.emit(help_text)
            logger.debug(f"Help retrieved successfully for {tool_name}")

        except subprocess.TimeoutExpired:
            error_msg = f"Timeout while getting help for {tool_name}"
            logger.exception(error_msg)
            self.help_received.emit(f"Error: {error_msg}")
        except Exception as e:
            error_msg = f"Error getting help for {tool_name}: {e!s}"
            logger.exception(error_msg)
            self.help_received.emit(f"Error: {error_msg}")

    def install_tool(self, tool_name: str) -> None:
        """
        Install a pipx tool.

        Args:
            tool_name: Name of the tool to install
        """
        if not tool_name or tool_name not in PIPX_TOOLS:
            self.command_failed.emit("Please select a valid tool from the dropdown.")
            return

        logger.info(f"Installing pipx tool: {tool_name}")
        self._run_command(["pipx", "install", tool_name])

    def run_tool(self, tool_name: str, arguments: str) -> None:
        """
        Run a pipx tool with the provided arguments.

        Args:
            tool_name: Name of the tool to run
            arguments: Command line arguments for the tool
        """
        if not tool_name or tool_name not in PIPX_TOOLS:
            self.command_failed.emit("Please select a valid tool from the dropdown.")
            return

        logger.info(f"Running pipx tool: {tool_name} with arguments: {arguments}")

        # Build command
        cmd = [tool_name]
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
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.command_failed.emit("Another command is already running. Please wait for it to finish.")
            return

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)
        self.process.errorOccurred.connect(self._handle_error)

        logger.info(f"Starting command: {' '.join(cmd)}")
        self.command_started.emit()

        self.process.start(cmd[0], cmd[1:])

        if not self.process.waitForStarted(5000):
            error_msg = f"Failed to start command: {' '.join(cmd)}"
            logger.error(error_msg)
            self.command_failed.emit(error_msg)

    def _handle_stdout(self):
        """Handle standard output from the running process."""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            if data:
                logger.debug(f"Stdout received: {data[:100]}...")
                self.output_received.emit(data)

    def _handle_stderr(self):
        """Handle standard error from the running process."""
        if self.process:
            data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
            if data:
                logger.debug(f"Stderr received: {data[:100]}...")
                self.output_received.emit(f"[STDERR] {data}")

    def _handle_finished(self, exit_code: int):
        """Handle process completion."""
        logger.info(f"Command finished with exit code: {exit_code}")
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


def create_pipx_runner_widget(style_func, scratch_pad=None):  # noqa: C901
    """
    Creates the main widget for the Pipx Runner tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The main widget for the tool.
    """
    pipx_runner = PipxRunner()

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

    # Tool selection
    tool_layout = QHBoxLayout()
    tool_layout.setSpacing(8)

    tool_label = QLabel("Tool:")
    tool_label.setFixedWidth(80)
    tool_layout.addWidget(tool_label)

    tool_combo = QComboBox()
    tool_combo.addItem("Select a tool...", "")
    for tool_name, description in PIPX_TOOLS.items():
        tool_combo.addItem(f"{tool_name} - {description}", tool_name)
    tool_layout.addWidget(tool_combo)

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
    install_button = QPushButton("Install Tool")
    run_button = QPushButton("Run Tool")
    stop_button = QPushButton("Stop")
    stop_button.setEnabled(False)

    button_layout.addWidget(get_help_button)
    button_layout.addWidget(install_button)
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
    def on_get_help():
        tool_name = tool_combo.currentData()
        if tool_name:
            logger.info(f"Getting help for tool: {tool_name}")
            status_label.setText(f"Getting help for {tool_name}...")
            pipx_runner.get_tool_help(tool_name)
        else:
            QMessageBox.warning(widget, "Warning", "Please select a tool first.")

    def on_install_tool():
        tool_name = tool_combo.currentData()
        if tool_name:
            logger.info(f"Installing tool: {tool_name}")
            status_label.setText(f"Installing {tool_name}...")
            pipx_runner.install_tool(tool_name)
        else:
            QMessageBox.warning(widget, "Warning", "Please select a tool first.")

    def on_run_tool():
        tool_name = tool_combo.currentData()
        if tool_name:
            arguments = args_input.text().strip()
            logger.info(f"Running tool: {tool_name} with args: {arguments}")
            status_label.setText(f"Running {tool_name}...")
            pipx_runner.run_tool(tool_name, arguments)
        else:
            QMessageBox.warning(widget, "Warning", "Please select a tool first.")

    def on_stop_command():
        logger.info("Stopping command")
        pipx_runner.stop_command()
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
                new_content = f"{current_content}\n=== Pipx Runner Output ===\n{text}\n"
                scratch_pad.set_content(new_content)
                status_label.setText("Output sent to scratch pad")
                logger.debug("Output sent to scratch pad")
            else:
                QMessageBox.information(widget, "Info", "No output to send.")

    # Signal connections
    get_help_button.clicked.connect(on_get_help)
    install_button.clicked.connect(on_install_tool)
    run_button.clicked.connect(on_run_tool)
    stop_button.clicked.connect(on_stop_command)
    clear_output_button.clicked.connect(on_clear_output)
    copy_output_button.clicked.connect(on_copy_output)
    if scratch_pad:
        send_to_scratch_button.clicked.connect(on_send_to_scratch)

    # Pipx runner signal connections
    def on_command_started():
        logger.debug("Command started - updating UI")
        progress_bar.setVisible(True)
        run_button.setEnabled(False)
        install_button.setEnabled(False)
        stop_button.setEnabled(True)
        status_label.setText("Command running...")

    def on_command_finished(exit_code):
        logger.debug(f"Command finished with exit code {exit_code} - updating UI")
        progress_bar.setVisible(False)
        run_button.setEnabled(True)
        install_button.setEnabled(True)
        stop_button.setEnabled(False)
        if exit_code == 0:
            status_label.setText("Command completed successfully")
        else:
            status_label.setText(f"Command failed with exit code {exit_code}")

    def on_command_failed(error_message):
        logger.error(f"Command failed: {error_message}")
        progress_bar.setVisible(False)
        run_button.setEnabled(True)
        install_button.setEnabled(True)
        stop_button.setEnabled(False)
        status_label.setText(f"Error: {error_message}")
        output_text.append(f"\n[ERROR] {error_message}\n")

    def on_output_received(text):
        logger.debug(f"Output received: {text[:50]}...")
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

    pipx_runner.command_started.connect(on_command_started)
    pipx_runner.command_finished.connect(on_command_finished)
    pipx_runner.command_failed.connect(on_command_failed)
    pipx_runner.output_received.connect(on_output_received)
    pipx_runner.help_received.connect(on_help_received)

    logger.info("Pipx Runner widget created successfully")
    return widget
