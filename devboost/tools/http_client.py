import json
import logging
import time
from typing import Any

import requests
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import get_status_style, get_tool_style

# Logger for debugging
logger = logging.getLogger(__name__)


class HTTPClient(QObject):
    """
    Backend HTTP client logic with proper error handling and response processing.
    """

    request_completed = pyqtSignal(dict)  # response_data
    request_started = pyqtSignal()
    request_failed = pyqtSignal(str)  # error_message

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        logger.info("HTTPClient initialized")

    def make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: str | None = None,
        timeout: int = 30,
    ) -> None:
        """
        Makes an HTTP request with proper error handling and timing.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Complete URL for the request
            headers: Optional dictionary of headers
            body: Optional request body as string
            timeout: Request timeout in seconds
        """
        logger.info(f"Making {method} request to {url}")
        self.request_started.emit()

        try:
            # Prepare request data
            request_headers = headers or {}
            request_data = None
            json_data = None

            # Handle request body
            if body and body.strip():
                # Try to parse as JSON first
                try:
                    json_data = json.loads(body)
                    if "Content-Type" not in request_headers:
                        request_headers["Content-Type"] = "application/json"
                    logger.debug("Request body parsed as JSON")
                except json.JSONDecodeError:
                    # Treat as raw data
                    request_data = body
                    if "Content-Type" not in request_headers:
                        request_headers["Content-Type"] = "text/plain"
                    logger.debug("Request body treated as raw data")

            # Record start time
            start_time = time.time()

            # Make the request
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                data=request_data,
                json=json_data,
                timeout=timeout,
                allow_redirects=True,
            )

            # Calculate response time
            response_time = time.time() - start_time

            # Process response
            response_data = self._process_response(response, response_time)
            logger.info(f"Request completed with status {response.status_code}")
            self.request_completed.emit(response_data)

        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after {timeout} seconds"
            logger.exception(error_msg)
            self.request_failed.emit(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - please check the URL and your internet connection"
            logger.exception(error_msg)
            self.request_failed.emit(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {e!s}"
            logger.exception(error_msg)
            self.request_failed.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e!s}"
            logger.exception(error_msg)
            self.request_failed.emit(error_msg)

    def _process_response(self, response: requests.Response, response_time: float) -> dict[str, Any]:
        """
        Processes the HTTP response and extracts relevant information.

        Args:
            response: The requests Response object
            response_time: Time taken for the request in seconds

        Returns:
            Dictionary containing processed response data
        """
        # Get response body
        try:
            # Try to get JSON response
            response_json = response.json()
            response_body = json.dumps(response_json, indent=2)
            content_type = "application/json"
        except (json.JSONDecodeError, ValueError):
            # Fallback to text
            response_body = response.text
            content_type = response.headers.get("content-type", "text/plain")

        # Calculate response size
        response_size = len(response.content)

        # Format headers
        response_headers = dict(response.headers)

        return {
            "status_code": response.status_code,
            "status_text": response.reason,
            "headers": response_headers,
            "body": response_body,
            "content_type": content_type,
            "response_time": response_time,
            "response_size": response_size,
            "url": response.url,
            "method": response.request.method,
        }


# ruff: noqa: C901
def create_http_client_widget(style_func, scratch_pad=None):
    """
    Creates the main widget for the HTTP client tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The main widget for the tool.
    """
    http_client = HTTPClient()

    widget = QWidget()
    widget.setStyleSheet(get_tool_style())

    # Main layout
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Request section
    request_frame = QFrame()
    request_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    request_layout = QVBoxLayout(request_frame)
    request_layout.setContentsMargins(10, 10, 10, 10)
    request_layout.setSpacing(8)

    # URL and method row
    url_layout = QHBoxLayout()
    url_layout.setSpacing(8)

    # Method selector
    method_combo = QComboBox()
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    method_combo.addItems(methods)
    method_combo.setFixedWidth(120)  # Expanded from 100 to 120
    url_layout.addWidget(method_combo)

    # URL input
    url_input = QLineEdit()
    url_input.setPlaceholderText("Enter URL (e.g., https://api.example.com/users)")
    url_layout.addWidget(url_input)

    # Send button
    send_button = QPushButton("Send")
    send_button.setFixedWidth(80)
    url_layout.addWidget(send_button)

    request_layout.addLayout(url_layout)

    # Headers section
    headers_label = QLabel("Headers:")
    request_layout.addWidget(headers_label)

    headers_table = QTableWidget(0, 2)
    headers_table.setHorizontalHeaderLabels(["Key", "Value"])
    # Set column widths - give more space to the Key column
    headers_table.setColumnWidth(0, 200)  # Key column width
    headers_table.horizontalHeader().setStretchLastSection(True)  # Value column stretches
    headers_table.setMaximumHeight(150)
    request_layout.addWidget(headers_table)

    # Header buttons layout
    header_buttons_layout = QHBoxLayout()

    # Add header button
    add_header_button = QPushButton("Add Header")
    add_header_button.setFixedWidth(100)
    header_buttons_layout.addWidget(add_header_button)

    # Delete header button
    delete_header_button = QPushButton("Delete Header")
    delete_header_button.setFixedWidth(120)
    header_buttons_layout.addWidget(delete_header_button)

    # Add stretch to push buttons to the left
    header_buttons_layout.addStretch()

    request_layout.addLayout(header_buttons_layout)

    # Body section
    body_label = QLabel("Request Body:")
    request_layout.addWidget(body_label)

    body_input = QTextEdit()
    body_input.setPlaceholderText("Enter request body (JSON, text, etc.)")
    body_input.setMaximumHeight(150)
    request_layout.addWidget(body_input)

    main_layout.addWidget(request_frame)

    # Progress bar
    progress_bar = QProgressBar()
    progress_bar.setVisible(False)
    main_layout.addWidget(progress_bar)

    # Response section with tabs
    response_tabs = QTabWidget()
    main_layout.addWidget(response_tabs, 1)

    # Response body tab
    response_body_edit = QTextEdit()
    response_body_edit.setReadOnly(True)
    response_tabs.addTab(response_body_edit, "Response Body")

    # Response headers tab
    response_headers_table = QTableWidget(0, 2)
    response_headers_table.setHorizontalHeaderLabels(["Header", "Value"])
    response_headers_table.horizontalHeader().setStretchLastSection(True)
    response_tabs.addTab(response_headers_table, "Response Headers")

    # Response stats tab
    stats_widget = QWidget()
    stats_layout = QVBoxLayout(stats_widget)
    stats_text = QTextEdit()
    stats_text.setReadOnly(True)
    stats_layout.addWidget(stats_text)
    response_tabs.addTab(stats_widget, "Stats")

    # Action buttons
    action_layout = QHBoxLayout()
    action_layout.addStretch()

    clear_button = QPushButton("Clear")
    copy_response_button = QPushButton("Copy Response")
    send_to_scratch_button = QPushButton("Send to Scratch Pad")

    action_layout.addWidget(clear_button)
    action_layout.addWidget(copy_response_button)
    if scratch_pad:
        action_layout.addWidget(send_to_scratch_button)

    main_layout.addLayout(action_layout)

    # Event handlers
    def add_header_row():
        """Add a new header row to the table."""
        row_count = headers_table.rowCount()
        headers_table.insertRow(row_count)
        headers_table.setItem(row_count, 0, QTableWidgetItem(""))
        headers_table.setItem(row_count, 1, QTableWidgetItem(""))
        logger.debug(f"Added header row {row_count}")

    def delete_header_row():
        """Delete selected header row(s) from the table."""
        selected_rows = set()
        for item in headers_table.selectedItems():
            selected_rows.add(item.row())

        # Delete rows in reverse order to maintain correct indices
        for row in sorted(selected_rows, reverse=True):
            headers_table.removeRow(row)

        logger.debug(f"Deleted header row(s) {selected_rows}")

    def get_headers() -> dict[str, str]:
        """Extract headers from the table."""
        headers = {}
        for row in range(headers_table.rowCount()):
            key_item = headers_table.item(row, 0)
            value_item = headers_table.item(row, 1)
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                if key and value:
                    headers[key] = value
        logger.debug(f"Extracted headers: {headers}")
        return headers

    def make_request():
        """Make HTTP request with current form data."""
        method = method_combo.currentText()
        url = url_input.text().strip()
        headers = get_headers()
        body = body_input.toPlainText().strip()

        if not url:
            QMessageBox.warning(widget, "Warning", "Please enter a URL")
            return

        logger.info(f"Initiating {method} request to {url}")
        http_client.make_request(method, url, headers, body)

    def on_request_started():
        """Handle request start."""
        send_button.setEnabled(False)
        send_button.setText("Sending...")
        progress_bar.setVisible(True)
        progress_bar.setRange(0, 0)  # Indeterminate progress
        logger.debug("Request started - UI updated")

    def on_request_completed(response_data):
        """Handle successful request completion."""
        send_button.setEnabled(True)
        send_button.setText("Send")
        progress_bar.setVisible(False)

        # Update response body
        response_body_edit.setPlainText(response_data["body"])

        # Update response headers
        headers = response_data["headers"]
        response_headers_table.setRowCount(len(headers))
        for row, (key, value) in enumerate(headers.items()):
            response_headers_table.setItem(row, 0, QTableWidgetItem(key))
            response_headers_table.setItem(row, 1, QTableWidgetItem(str(value)))

        # Update stats
        stats_info = f"""Status: {response_data["status_code"]} {response_data["status_text"]}
URL: {response_data["url"]}
Method: {response_data["method"]}
Response Time: {response_data["response_time"]:.3f} seconds
Response Size: {response_data["response_size"]} bytes
Content Type: {response_data["content_type"]}"""
        stats_text.setPlainText(stats_info)

        # Set status color based on response code
        if 200 <= response_data["status_code"] < 300:
            response_body_edit.setStyleSheet(get_status_style("success"))
        elif 400 <= response_data["status_code"] < 500:
            response_body_edit.setStyleSheet(get_status_style("warning"))
        else:
            response_body_edit.setStyleSheet(get_status_style("error"))

        logger.info(f"Request completed successfully with status {response_data['status_code']}")

    def on_request_failed(error_message):
        """Handle request failure."""
        send_button.setEnabled(True)
        send_button.setText("Send")
        progress_bar.setVisible(False)

        # Show error in response body
        response_body_edit.setPlainText(f"Error: {error_message}")
        response_body_edit.setStyleSheet(get_status_style("error"))

        # Clear other tabs
        response_headers_table.setRowCount(0)
        stats_text.setPlainText(f"Request failed: {error_message}")

        logger.error(f"Request failed: {error_message}")

    def clear_all():
        """Clear all form data and responses."""
        url_input.clear()
        method_combo.setCurrentIndex(0)
        headers_table.setRowCount(0)
        body_input.clear()
        response_body_edit.clear()
        response_body_edit.setStyleSheet("")
        response_headers_table.setRowCount(0)
        stats_text.clear()
        logger.debug("All fields cleared")

    def copy_response():
        """Copy response body to clipboard."""
        response_text = response_body_edit.toPlainText()
        if response_text:
            QApplication.clipboard().setText(response_text)
            logger.debug("Response copied to clipboard")

    def send_to_scratch_pad_func():
        """Send response to scratch pad."""
        if scratch_pad:
            response_text = response_body_edit.toPlainText()
            if response_text:
                send_to_scratch_pad(scratch_pad, response_text)
                logger.debug("Response sent to scratch pad")

    # Connect signals
    add_header_button.clicked.connect(add_header_row)
    delete_header_button.clicked.connect(delete_header_row)
    send_button.clicked.connect(make_request)
    clear_button.clicked.connect(clear_all)
    copy_response_button.clicked.connect(copy_response)
    if scratch_pad:
        send_to_scratch_button.clicked.connect(send_to_scratch_pad_func)

    # Connect HTTP client signals
    http_client.request_started.connect(on_request_started)
    http_client.request_completed.connect(on_request_completed)
    http_client.request_failed.connect(on_request_failed)

    # Add some default headers
    add_header_row()
    headers_table.setItem(0, 0, QTableWidgetItem("Content-Type"))
    headers_table.setItem(0, 1, QTableWidgetItem("application/json"))

    # Add keyboard shortcuts
    send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), widget)
    send_shortcut.activated.connect(make_request)
    logger.debug("Send shortcut (Ctrl+Enter) created")

    clear_shortcut = QShortcut(QKeySequence("Ctrl+R"), widget)
    clear_shortcut.activated.connect(clear_all)
    logger.debug("Clear shortcut (Ctrl+R) created")

    # Add macOS shortcuts as well
    send_shortcut_mac = QShortcut(QKeySequence("Cmd+Return"), widget)
    send_shortcut_mac.activated.connect(make_request)
    logger.debug("Send shortcut (Cmd+Enter) created for macOS")

    clear_shortcut_mac = QShortcut(QKeySequence("Cmd+R"), widget)
    clear_shortcut_mac.activated.connect(clear_all)
    logger.debug("Clear shortcut (Cmd+R) created for macOS")

    logger.info("HTTP Client widget created successfully with keyboard shortcuts")
    return widget


def send_to_scratch_pad(scratch_pad, content):
    """
    Send content to the scratch pad.

    Args:
        scratch_pad: The scratch pad widget.
        content (str): The content to send.
    """
    if scratch_pad and content:
        # Append content to the scratch pad with a separator
        current_content = scratch_pad.get_content()
        new_content = f"{current_content}\n\n--- HTTP Response ---\n{content}" if current_content else content
        scratch_pad.set_content(new_content)
        logger.debug("Content sent to scratch pad")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # In a real app, style_func would be a method of the main window,
    # but for a standalone test, we can just use the app's style.
    main_window = QMainWindow()
    main_window.setWindowTitle("HTTP Client")
    main_window.setGeometry(100, 100, 1000, 700)

    central_widget = create_http_client_widget(app.style)
    main_window.setCentralWidget(central_widget)

    main_window.show()
    sys.exit(app.exec())
