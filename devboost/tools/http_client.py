import json
import logging
import time
from typing import Any

import requests
from PyQt6.QtCore import QObject, QStringListModel, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
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

from devboost.styles import get_status_style, get_tool_style

# Logger for debugging
logger = logging.getLogger(__name__)

# HTTP Header Data Dictionaries for Autocomplete
HTTP_HEADERS = {
    # Authentication headers
    "Authorization": ["Bearer ", "Basic ", "Digest ", "OAuth ", "JWT ", "Token ", "ApiKey "],
    # Content headers
    "Content-Type": [
        "application/json",
        "application/xml",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain",
        "text/html",
        "text/css",
        "text/javascript",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/svg+xml",
        "application/octet-stream",
    ],
    "Accept": [
        "application/json",
        "application/xml",
        "text/html",
        "text/plain",
        "*/*",
        "application/pdf",
        "image/*",
        "text/css",
        "application/javascript",
    ],
    "Accept-Encoding": ["gzip, deflate, br", "gzip, deflate", "gzip", "deflate", "br", "identity"],
    "Accept-Language": ["en-US,en;q=0.9", "en-US", "en-GB", "fr-FR", "de-DE", "es-ES", "zh-CN", "ja-JP"],
    # Cache headers
    "Cache-Control": [
        "no-cache",
        "no-store",
        "max-age=0",
        "max-age=3600",
        "max-age=86400",
        "public",
        "private",
        "must-revalidate",
    ],
    "Pragma": ["no-cache"],
    "Expires": ["0", "-1"],
    # CORS headers
    "Access-Control-Allow-Origin": ["*", "https://localhost:3000", "https://example.com"],
    "Access-Control-Allow-Methods": ["GET, POST, PUT, DELETE, OPTIONS", "GET, POST, OPTIONS", "*"],
    "Access-Control-Allow-Headers": [
        "Content-Type, Authorization",
        "*",
        "X-Requested-With, Content-Type, Authorization",
    ],
    # Custom headers
    "X-API-Key": [],
    "X-Requested-With": ["XMLHttpRequest"],
    "X-Forwarded-For": [],
    "X-Real-IP": [],
    "X-Frame-Options": ["DENY", "SAMEORIGIN", "ALLOW-FROM"],
    "X-Content-Type-Options": ["nosniff"],
    "X-XSS-Protection": ["1; mode=block", "0"],
    # Connection headers
    "Connection": ["keep-alive", "close"],
    "Keep-Alive": ["timeout=5, max=1000"],
    # User agent
    "User-Agent": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "curl/7.68.0",
        "PostmanRuntime/7.28.0",
    ],
    # Content length and encoding
    "Content-Length": [],
    "Content-Encoding": ["gzip", "deflate", "br"],
    "Transfer-Encoding": ["chunked"],
    # Location and redirect
    "Location": [],
    "Referer": [],
    # Security headers
    "Strict-Transport-Security": ["max-age=31536000; includeSubDomains"],
    "Content-Security-Policy": ["default-src 'self'"],
    # Custom application headers
    "X-Custom-Header": [],
    "X-Request-ID": [],
    "X-Correlation-ID": [],
}

# Common HTTP header names for autocomplete (sorted alphabetically)
COMMON_HEADER_NAMES = sorted(HTTP_HEADERS.keys())


class AutoCompleteLineEdit(QLineEdit):
    """
    Custom QLineEdit widget with autocomplete functionality for HTTP headers.

    This widget provides intelligent autocomplete suggestions based on whether
    it's used for header keys or values, with context-aware suggestions.
    """

    def __init__(self, is_header_key=True, parent=None):
        """
        Initialize the AutoCompleteLineEdit widget.

        Args:
            is_header_key (bool): True if this is for header keys, False for values
            parent: Parent widget
        """
        super().__init__(parent)
        self.is_header_key = is_header_key
        self.completer = None
        self.setup_completer()
        logger.debug("AutoCompleteLineEdit initialized (is_header_key=%s)", is_header_key)

    def setup_completer(self):
        """
        Set up the QCompleter with appropriate data based on widget type.
        """
        if self.is_header_key:
            # For header keys, use the list of common header names
            model = QStringListModel(COMMON_HEADER_NAMES)
            self.completer = QCompleter(model, self)
            logger.debug("Created completer model with %d items: %s...", model.rowCount(), COMMON_HEADER_NAMES[:3])
        else:
            # For header values, start with empty completer
            # Will be populated dynamically based on the selected header key
            model = QStringListModel([])
            self.completer = QCompleter(model, self)
            logger.debug("Created empty completer model for header values")

        # Configure completer behavior
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # Case-insensitive matching
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)  # Substring matching
        self.completer.setMaxVisibleItems(10)  # Limit visible suggestions

        logger.debug(
            "Configured completer: case_sensitive=%s, filter_mode=%s",
            self.completer.caseSensitivity(),
            self.completer.filterMode(),
        )

        # Set the completer for this line edit
        self.setCompleter(self.completer)

        # Ensure completer is activated
        self.completer.setCompletionMode(self.completer.CompletionMode.PopupCompletion)

        # Test the completer with a known prefix
        if self.is_header_key:
            self.completer.setCompletionPrefix("Acc")
            test_count = self.completer.completionCount()
            logger.debug("Test completion for 'Acc': %d matches", test_count)

        # Apply custom styling to the completer popup
        self.apply_completer_styling()

        logger.debug(
            "Completer setup complete for %s field with %d suggestions",
            "key" if self.is_header_key else "value",
            self.completer.model().rowCount() if self.completer.model() else 0,
        )

    def apply_completer_styling(self):
        """
        Apply custom styling to the completer popup for better visual appearance.
        """
        if not self.completer:
            return

        # Get the popup widget
        popup = self.completer.popup()
        if popup:
            # Apply custom stylesheet to the popup using our shared style
            from devboost.styles import get_autocomplete_dropdown_style

            popup.setStyleSheet(get_autocomplete_dropdown_style())

        # Apply styling to the line edit itself using application theme
        from devboost.styles import COLORS, FONTS

        line_edit_style = f"""
            QLineEdit {{
                background-color: {COLORS["bg_primary"]};
                color: {COLORS["text_primary"]};
                border: 1px solid {COLORS["border_primary"]};
                border-radius: 4px;
                padding: 5px 8px;
                font-family: {FONTS["mono"]};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS["border_focus"]};
            }}
            QLineEdit:hover {{
                background-color: {COLORS["bg_secondary"]};
            }}
        """
        self.setStyleSheet(line_edit_style)

        logger.debug("Applied custom styling to completer and line edit")

    def update_value_suggestions(self, header_key: str):
        """
        Update autocomplete suggestions for header values based on the selected key.

        Args:
            header_key (str): The header key to get value suggestions for
        """
        if self.is_header_key:
            return  # This method is only for value fields

        # Get suggestions for the given header key
        suggestions = HTTP_HEADERS.get(header_key, [])

        # Update the completer model
        if self.completer:
            model = QStringListModel(suggestions)
            self.completer.setModel(model)
            logger.debug(
                "Updated value suggestions for '%s': %d items - %s%s",
                header_key,
                len(suggestions),
                suggestions[:3],
                "..." if len(suggestions) > 3 else "",
            )

    def get_suggestions_for_key(self, header_key: str) -> list[str]:
        """
        Get autocomplete suggestions for a specific header key.

        Args:
            header_key (str): The header key to get suggestions for

        Returns:
            List of suggestion strings
        """
        return HTTP_HEADERS.get(header_key, [])

    def keyPressEvent(self, event):
        """
        Override key press event to ensure completer is triggered.
        """
        logger.debug(
            "KeyPress event: key=%d, text='%s', is_header_key=%s", event.key(), event.text(), self.is_header_key
        )

        super().keyPressEvent(event)

        # Log current state after key press
        current_text = self.text()
        logger.debug("After keyPress: current_text='%s', has_completer=%s", current_text, self.completer is not None)

        # Trigger completer for header keys when typing
        if self.is_header_key and self.completer:
            logger.debug("Processing autocomplete for header key widget")
            # Only show completer if we have text and it's not just whitespace
            text = current_text.strip()
            logger.debug("Stripped text: '%s', length: %d", text, len(text))

            if len(text) >= 1:  # Show after 1 character
                logger.debug("Setting completion prefix to: '%s'", text)

                # Check if completer model is empty and recreate if needed
                model = self.completer.model()
                model_row_count = model.rowCount() if model else 0

                # If model is empty, recreate it
                if model_row_count == 0 and self.is_header_key:
                    logger.debug("Model is empty, recreating completer model")
                    new_model = QStringListModel(COMMON_HEADER_NAMES)
                    self.completer.setModel(new_model)
                    model = self.completer.model()
                    model_row_count = model.rowCount() if model else 0
                    logger.debug("Recreated model with %d items", model_row_count)

                self.completer.setCompletionPrefix(text)
                completion_count = self.completer.completionCount()
                logger.debug("Completion count: %d", completion_count)

                if completion_count > 0:
                    self.completer.complete()
                    logger.debug("Triggered completer for '%s' with %d matches", text, completion_count)
                else:
                    logger.debug("No completions found for '%s'", text)
            else:
                logger.debug("Text too short for completion: '%s'", text)
        else:
            if not self.is_header_key:
                logger.debug("Not a header key widget, skipping autocomplete")
            if not self.completer:
                logger.debug("No completer available")


class HeaderKeyLineEdit(AutoCompleteLineEdit):
    """
    Specialized line edit widget for HTTP header keys with autocomplete.

    This widget is specifically designed for header key input and provides
    autocomplete suggestions from the list of common HTTP header names.
    """

    def __init__(self, parent=None):
        """
        Initialize the HeaderKeyLineEdit widget.

        Args:
            parent: Parent widget
        """
        logger.debug("Creating HeaderKeyLineEdit widget")
        super().__init__(is_header_key=True, parent=parent)
        self.setPlaceholderText("Enter header name...")
        logger.debug(
            "HeaderKeyLineEdit initialized with completer: %s, suggestions: %d",
            self.completer is not None,
            len(COMMON_HEADER_NAMES),
        )

        # Log some sample suggestions for debugging
        sample_suggestions = COMMON_HEADER_NAMES[:5]
        logger.debug("Sample header suggestions: %s", sample_suggestions)

    def get_current_suggestions(self) -> list[str]:
        """
        Get the current list of header key suggestions.

        Returns:
            List of header key suggestions
        """
        return COMMON_HEADER_NAMES

    def is_valid_header_key(self, key: str) -> bool:
        """
        Check if the provided key is a valid/known HTTP header.

        Args:
            key (str): The header key to validate

        Returns:
            bool: True if the key is a known header, False otherwise
        """
        return key in HTTP_HEADERS

    def get_matching_headers(self, partial_key: str) -> list[str]:
        """
        Get header names that match the partial input.

        Args:
            partial_key (str): Partial header key to match

        Returns:
            List of matching header names
        """
        partial_lower = partial_key.lower()
        return [header for header in COMMON_HEADER_NAMES if partial_lower in header.lower()]


class HeaderValueLineEdit(AutoCompleteLineEdit):
    """
    Specialized line edit widget for HTTP header values with context-aware autocomplete.

    This widget provides intelligent autocomplete suggestions based on the selected
    header key, offering relevant values for each specific header type.
    """

    def __init__(self, parent=None):
        """
        Initialize the HeaderValueLineEdit widget.

        Args:
            parent: Parent widget
        """
        super().__init__(is_header_key=False, parent=parent)
        self.setPlaceholderText("Enter header value...")
        self.current_header_key = ""
        logger.debug("HeaderValueLineEdit initialized")

    def set_header_key(self, header_key: str):
        """
        Set the current header key to provide context-aware value suggestions.

        Args:
            header_key (str): The header key to provide suggestions for
        """
        self.current_header_key = header_key.strip()
        self.update_value_suggestions(self.current_header_key)

        # Update placeholder text based on header key
        if self.current_header_key:
            suggestions = self.get_suggestions_for_key(self.current_header_key)
            placeholder = f"e.g., {suggestions[0]}" if suggestions else f"Enter value for {self.current_header_key}..."
        else:
            placeholder = "Enter header value..."

        self.setPlaceholderText(placeholder)
        suggestion_count = len(self.get_suggestions_for_key(self.current_header_key))
        logger.debug(
            "HeaderValueLineEdit updated for key: '%s' with %d suggestions, placeholder: '%s'",
            self.current_header_key,
            suggestion_count,
            placeholder,
        )

    def get_current_suggestions(self) -> list[str]:
        """
        Get the current list of value suggestions based on the selected header key.

        Returns:
            List of value suggestions for the current header key
        """
        return self.get_suggestions_for_key(self.current_header_key)

    def has_suggestions(self) -> bool:
        """
        Check if the current header key has predefined value suggestions.

        Returns:
            bool: True if suggestions are available, False otherwise
        """
        return len(self.get_current_suggestions()) > 0

    def get_suggestion_count(self) -> int:
        """
        Get the number of available suggestions for the current header key.

        Returns:
            int: Number of available suggestions
        """
        return len(self.get_current_suggestions())

    def clear_header_context(self):
        """
        Clear the header key context and reset to default state.
        """
        self.current_header_key = ""
        self.setPlaceholderText("Enter header value...")
        # Clear the completer model
        if self.completer:
            model = QStringListModel([])
            self.completer.setModel(model)
        logger.debug("HeaderValueLineEdit context cleared")


class AutoCompleteTableWidget(QTableWidget):
    """
    Custom table widget for HTTP headers with autocomplete functionality.

    This widget replaces the standard QTableWidget and provides autocomplete
    functionality for both header keys and values using custom line edit widgets.
    """

    def __init__(self, parent=None):
        """
        Initialize the AutoCompleteTableWidget.

        Args:
            parent: Parent widget
        """
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["Key", "Value"])
        self.setup_table()
        logger.debug("AutoCompleteTableWidget initialized")

    def setup_table(self):
        """
        Set up the table with proper column widths and behavior.
        """
        # Set column widths - give more space to the Key column
        self.setColumnWidth(0, 200)  # Key column width
        self.horizontalHeader().setStretchLastSection(True)  # Value column stretches
        self.setMaximumHeight(150)

        # Enable selection of entire rows
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        logger.debug("AutoCompleteTableWidget setup complete")

    def add_header_row(self, key: str = "", value: str = ""):
        """
        Add a new header row with autocomplete widgets.

        Args:
            key (str): Initial key value
            value (str): Initial value
        """
        row_count = self.rowCount()
        self.insertRow(row_count)

        # Create autocomplete widgets
        logger.debug("Creating autocomplete widgets for row %d", row_count)
        key_widget = HeaderKeyLineEdit(self)
        value_widget = HeaderValueLineEdit(self)
        logger.debug("Created key_widget: %s, value_widget: %s", type(key_widget).__name__, type(value_widget).__name__)

        # Set initial values if provided
        if key:
            key_widget.setText(key)
        if value:
            value_widget.setText(value)
            value_widget.set_header_key(key)

        # Connect key changes to update value suggestions
        def on_key_changed(text, value_widget=value_widget, row=row_count):
            logger.debug("Header key changed in row %d: '%s' - updating value suggestions", row, text)
            value_widget.set_header_key(text)

        key_widget.textChanged.connect(on_key_changed)

        # Set the widgets in the table
        self.setCellWidget(row_count, 0, key_widget)
        self.setCellWidget(row_count, 1, value_widget)

        logger.debug("Added autocomplete header row %d (key='%s', value='%s')", row_count, key, value)

        return row_count

    def get_headers(self) -> dict[str, str]:
        """
        Extract headers from the table widgets.

        Returns:
            Dictionary of header key-value pairs
        """
        headers = {}

        for row in range(self.rowCount()):
            key_widget = self.cellWidget(row, 0)
            value_widget = self.cellWidget(row, 1)

            if isinstance(key_widget, HeaderKeyLineEdit) and isinstance(value_widget, HeaderValueLineEdit):
                key = key_widget.text().strip()
                value = value_widget.text().strip()

                if key and value:
                    headers[key] = value

        logger.debug("Extracted headers from autocomplete table: %s", headers)
        return headers

    def clear_headers(self):
        """
        Clear all header rows from the table.
        """
        self.setRowCount(0)
        logger.debug("Cleared all headers from autocomplete table")

    def set_headers(self, headers: dict[str, str]):
        """
        Set headers in the table from a dictionary.

        Args:
            headers (dict): Dictionary of header key-value pairs
        """
        self.clear_headers()

        for key, value in headers.items():
            self.add_header_row(key, value)

        logger.debug("Set %d headers in autocomplete table", len(headers))

    def delete_selected_rows(self):
        """
        Delete the currently selected rows.
        """
        selected_rows = set()
        for item in self.selectedItems():
            if item:
                selected_rows.add(item.row())

        # Also check for selected cell widgets
        for row in range(self.rowCount()):
            key_widget = self.cellWidget(row, 0)
            value_widget = self.cellWidget(row, 1)
            if (key_widget and key_widget.hasFocus()) or (value_widget and value_widget.hasFocus()):
                selected_rows.add(row)

        # Delete rows in reverse order to maintain correct indices
        for row in sorted(selected_rows, reverse=True):
            self.removeRow(row)

        logger.debug("Deleted selected header rows: %s", selected_rows)
        return len(selected_rows)


class HTTPWorkerThread(QThread):
    """
    Worker thread for handling HTTP requests asynchronously to keep UI responsive.

    This thread performs the actual HTTP request in the background and emits
    signals to communicate with the main UI thread.
    """

    # Signals to communicate with main thread
    request_completed = pyqtSignal(dict)  # response_data
    request_failed = pyqtSignal(str)  # error_message
    request_cancelled = pyqtSignal()  # request was cancelled
    request_progress = pyqtSignal(str)  # progress message

    def __init__(
        self, method: str, url: str, headers: dict[str, str] | None = None, body: str | None = None, timeout: int = 30
    ):
        """
        Initialize the worker thread with request parameters.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Complete URL for the request
            headers: Optional dictionary of headers
            body: Optional request body as string
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.timeout = timeout
        self.session = requests.Session()
        self._cancelled = False
        logger.debug("HTTPWorkerThread initialized for %s %s", method, url)

    def cancel(self):
        """
        Cancel the current request by setting the cancelled flag and closing the session.

        This will interrupt any ongoing HTTP request and prevent new ones from starting.
        """
        self._cancelled = True
        logger.info("HTTP request cancellation requested")

        # Close the session to interrupt any ongoing requests
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
                logger.debug("HTTP session closed for cancellation")
        except Exception as e:
            logger.warning("Error closing HTTP session during cancellation: %s", e)

    def run(self):
        """
        Execute the HTTP request in the worker thread.

        This method runs in the background thread and emits signals
        to communicate results back to the main thread.
        """
        if self._cancelled:
            logger.info("Request cancelled before execution")
            self.request_cancelled.emit()
            return

        try:
            logger.info("Worker thread making %s request to %s", self.method, self.url)
            self.request_progress.emit("Preparing request...")

            # Prepare request data
            request_headers = self.headers.copy()
            request_data = None
            json_data = None

            # Handle request body
            if self.body and self.body.strip():
                # Try to parse as JSON first
                try:
                    json_data = json.loads(self.body)
                    if "Content-Type" not in request_headers:
                        request_headers["Content-Type"] = "application/json"
                    logger.debug("Request body parsed as JSON")
                except json.JSONDecodeError:
                    # Treat as raw data
                    request_data = self.body
                    if "Content-Type" not in request_headers:
                        request_headers["Content-Type"] = "text/plain"
                    logger.debug("Request body treated as raw data")

            # Record start time
            start_time = time.time()

            # Check for cancellation before making request
            if self._cancelled:
                logger.info("Request cancelled before execution")
                self.request_cancelled.emit()
                return

            self.request_progress.emit(f"Sending {self.method} request...")
            # Make the request
            response = self.session.request(
                method=self.method.upper(),
                url=self.url,
                headers=request_headers,
                data=request_data,
                json=json_data,
                timeout=self.timeout,
                allow_redirects=True,
            )

            # Check for cancellation after request
            if self._cancelled:
                logger.info("Request cancelled after execution")
                self.request_cancelled.emit()
                return

            # Calculate response time
            response_time = time.time() - start_time
            self.request_progress.emit("Processing response...")

            # Process response
            response_data = self._process_response(response, response_time)
            logger.info("Worker thread request completed with status %d", response.status_code)
            self.request_progress.emit("Request completed successfully")
            self.request_completed.emit(response_data)

        except requests.exceptions.Timeout:
            if not self._cancelled:
                error_msg = f"Request timed out after {self.timeout} seconds"
                logger.exception(error_msg)
                self.request_failed.emit(error_msg)
        except requests.exceptions.ConnectionError:
            if not self._cancelled:
                error_msg = "Connection error - please check the URL and your internet connection"
                logger.exception(error_msg)
                self.request_failed.emit(error_msg)
        except requests.exceptions.RequestException as e:
            if not self._cancelled:
                error_msg = f"Request failed: {e!s}"
                logger.exception(error_msg)
                self.request_failed.emit(error_msg)
        except Exception as e:
            if not self._cancelled:
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


class HTTPClient(QObject):
    """
    Backend HTTP client logic with proper error handling and response processing.
    """

    request_completed = pyqtSignal(dict)  # response_data
    request_started = pyqtSignal()
    request_failed = pyqtSignal(str)  # error_message
    request_cancelled = pyqtSignal()  # request was cancelled
    request_progress = pyqtSignal(str)  # progress message

    def __init__(self):
        super().__init__()
        self.request_queue = []
        self.active_workers = {}
        self.max_concurrent_requests = 3
        self._request_id_counter = 0
        logger.info("HTTPClient initialized with async worker support and request queue")

    def make_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: str | None = None,
        timeout: int = 30,
    ) -> str:
        """
        Makes an HTTP request asynchronously using a worker thread to keep UI responsive.
        Supports request queuing for multiple concurrent requests.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Complete URL for the request
            headers: Optional dictionary of headers
            body: Optional request body as string
            timeout: Request timeout in seconds

        Returns:
            str: Request ID for tracking the request
        """
        # Generate unique request ID
        self._request_id_counter += 1
        request_id = f"req_{self._request_id_counter}"

        logger.info("Queuing async %s request to %s (ID: %s)", method, url, request_id)

        # Create request data
        request_data = {
            "id": request_id,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body,
            "timeout": timeout,
        }

        # Add to queue
        self.request_queue.append(request_data)

        # Process queue
        self._process_request_queue()

        return request_id

    def cancel_request(self, request_id: str | None = None) -> bool:
        """
        Cancel an HTTP request. If request_id is provided, cancels that specific request.
        Otherwise, cancels all active requests.

        Args:
            request_id: Optional specific request ID to cancel

        Returns:
            bool: True if any request was cancelled, False otherwise
        """
        cancelled = False

        if request_id:
            # Cancel specific request
            if request_id in self.active_workers:
                worker = self.active_workers[request_id]
                if worker.isRunning():
                    logger.info("Cancelling HTTP request %s", request_id)
                    worker.cancel()
                    cancelled = True

            # Remove from queue if not yet started
            self.request_queue = [req for req in self.request_queue if req["id"] != request_id]
        else:
            # Cancel all active requests
            for req_id, worker in self.active_workers.items():
                if worker.isRunning():
                    logger.info("Cancelling HTTP request %s", req_id)
                    worker.cancel()
                    cancelled = True

            # Clear queue
            if self.request_queue:
                logger.info("Clearing %d queued requests", len(self.request_queue))
                self.request_queue.clear()
                cancelled = True

        return cancelled

    def _process_request_queue(self):
        """
        Process the request queue by starting workers for queued requests
        up to the maximum concurrent limit.
        """
        # Start new workers for queued requests if we have capacity
        while len(self.active_workers) < self.max_concurrent_requests and self.request_queue:
            request_data = self.request_queue.pop(0)
            request_id = request_data["id"]

            logger.info("Starting worker for request %s", request_id)

            # Create and configure worker thread
            worker = HTTPWorkerThread(
                request_data["method"],
                request_data["url"],
                request_data["headers"],
                request_data["body"],
                request_data["timeout"],
            )

            # Store worker with request ID
            self.active_workers[request_id] = worker

            # Connect worker signals with request ID context
            worker.request_completed.connect(
                lambda data, req_id=request_id: self._handle_request_completed(req_id, data)
            )
            worker.request_failed.connect(lambda error, req_id=request_id: self._handle_request_failed(req_id, error))
            worker.request_cancelled.connect(lambda req_id=request_id: self._handle_request_cancelled(req_id))
            worker.request_progress.connect(lambda msg, req_id=request_id: self._handle_request_progress(req_id, msg))

            # Clean up worker when finished
            worker.finished.connect(lambda req_id=request_id: self._cleanup_worker(req_id))

            # Emit started signal and start worker
            self.request_started.emit()
            worker.start()
            logger.debug("Worker thread started for request %s", request_id)

    def _handle_request_completed(self, request_id: str, data: dict):
        """Handle request completion with request ID context."""
        logger.info("Request %s completed successfully", request_id)
        data["request_id"] = request_id
        self.request_completed.emit(data)

    def _handle_request_failed(self, request_id: str, error: str):
        """Handle request failure with request ID context."""
        logger.info("Request %s failed: %s", request_id, error)
        self.request_failed.emit(f"[{request_id}] {error}")

    def _handle_request_cancelled(self, request_id: str):
        """Handle request cancellation with request ID context."""
        logger.info("Request %s was cancelled", request_id)
        self.request_cancelled.emit()

    def _handle_request_progress(self, request_id: str, message: str):
        """Handle request progress with request ID context."""
        self.request_progress.emit(f"[{request_id}] {message}")

    def _cleanup_worker(self, request_id: str | None = None):
        """
        Clean up a worker thread after it finishes.

        Args:
            request_id: ID of the request to clean up, or None for legacy cleanup
        """
        if request_id and request_id in self.active_workers:
            worker = self.active_workers[request_id]
            worker.deleteLater()
            del self.active_workers[request_id]
            logger.debug("Worker thread for request %s cleaned up", request_id)

            # Process queue to start next request if any
            self._process_request_queue()

    def get_active_request_count(self) -> int:
        """Get the number of currently active requests."""
        return len(self.active_workers)

    def get_queued_request_count(self) -> int:
        """Get the number of requests waiting in the queue."""
        return len(self.request_queue)

    def get_active_request_ids(self) -> list[str]:
        """Get list of active request IDs."""
        return list(self.active_workers.keys())

    def is_request_active(self, request_id: str) -> bool:
        """Check if a specific request is currently active."""
        return request_id in self.active_workers


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

    # Action buttons
    action_layout = QHBoxLayout()
    action_layout.addStretch()

    clear_button = QPushButton("Clear")
    copy_response_button = QPushButton("Copy Response")
    send_to_scratch_button = QPushButton("Send to Scratch Pad")
    copy_curl_button = QPushButton("Copy Curl")

    action_layout.addWidget(clear_button)
    action_layout.addWidget(copy_response_button)
    if scratch_pad:
        action_layout.addWidget(send_to_scratch_button)
        action_layout.addWidget(copy_curl_button)

    request_layout.addLayout(action_layout)

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

    # Cancel button (initially hidden)
    cancel_button = QPushButton("Cancel")
    cancel_button.setFixedWidth(80)
    cancel_button.setVisible(False)
    url_layout.addWidget(cancel_button)

    request_layout.addLayout(url_layout)

    # Headers section
    headers_label = QLabel("Headers:")
    request_layout.addWidget(headers_label)

    headers_table = AutoCompleteTableWidget()
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

    # Progress section with enhanced visual feedback
    progress_frame = QFrame()
    progress_frame.setVisible(False)
    progress_layout = QVBoxLayout(progress_frame)
    progress_layout.setContentsMargins(10, 5, 10, 5)
    progress_layout.setSpacing(5)

    # Progress label for status text
    progress_label = QLabel("Preparing request...")
    progress_label.setStyleSheet("color: #0066cc; font-weight: bold;")
    progress_layout.addWidget(progress_label)

    # Status and timing layout
    status_layout = QHBoxLayout()

    # Request status indicator
    status_label = QLabel("Ready")
    status_label.setStyleSheet("color: #666666; font-size: 12px;")
    status_layout.addWidget(status_label)

    status_layout.addStretch()

    # Elapsed time display
    elapsed_time_label = QLabel("")
    elapsed_time_label.setStyleSheet("color: #666666; font-size: 12px; font-family: monospace;")
    status_layout.addWidget(elapsed_time_label)

    progress_layout.addLayout(status_layout)

    # Progress bar with enhanced styling
    progress_bar = QProgressBar()
    progress_bar.setStyleSheet("""
        QProgressBar {
            border: 2px solid #cccccc;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            background-color: #f0f0f0;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4CAF50, stop:1 #45a049);
            border-radius: 3px;
        }
    """)
    progress_layout.addWidget(progress_bar)

    main_layout.addWidget(progress_frame)

    # Timer for elapsed time tracking
    elapsed_timer = QTimer()
    elapsed_timer.timeout.connect(lambda: update_elapsed_time())
    request_start_time = None

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

    # Timer and status management functions
    def update_elapsed_time():
        """Update the elapsed time display."""
        nonlocal request_start_time
        if request_start_time:
            elapsed = time.time() - request_start_time
            elapsed_time_label.setText(f"Elapsed: {elapsed:.1f}s")

    def start_request_timer():
        """Start the request timer."""
        nonlocal request_start_time
        request_start_time = time.time()
        elapsed_timer.start(100)  # Update every 100ms
        elapsed_time_label.setText("Elapsed: 0.0s")

    def stop_request_timer():
        """Stop the request timer."""
        elapsed_timer.stop()
        if request_start_time:
            final_elapsed = time.time() - request_start_time
            elapsed_time_label.setText(f"Completed in: {final_elapsed:.1f}s")

    # Event handlers
    def add_header_row():
        """Add a new header row to the table."""
        row_index = headers_table.add_header_row()
        logger.debug("Added autocomplete header row %d", row_index)

    def delete_header_row():
        """Delete selected header row(s) from the table."""
        deleted_count = headers_table.delete_selected_rows()
        logger.debug("Deleted %d header row(s)", deleted_count)

    def get_headers() -> dict[str, str]:
        """Extract headers from the table."""
        headers = headers_table.get_headers()
        logger.debug("Extracted headers: %s", headers)
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

        logger.info("Initiating %s request to %s", method, url)
        http_client.make_request(method, url, headers, body)

    def on_request_started():
        """Handle request start."""
        send_button.setEnabled(False)
        send_button.setText("Sending...")
        cancel_button.setVisible(True)
        progress_frame.setVisible(True)
        progress_bar.setRange(0, 0)  # Indeterminate progress
        progress_label.setText("Starting request...")
        status_label.setText("Sending request...")
        status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
        start_request_timer()
        logger.debug("Request started - UI updated with enhanced progress and timing")

    def on_request_completed(response_data):
        """Handle successful request completion."""
        send_button.setEnabled(True)
        send_button.setText("Send")
        cancel_button.setVisible(False)
        stop_request_timer()

        # Update status based on response code
        status_code = response_data.get("status_code", 0)
        if 200 <= status_code < 300:
            status_label.setText(f"Success ({status_code})")
            status_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
        elif 400 <= status_code < 500:
            status_label.setText(f"Client Error ({status_code})")
            status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
        elif 500 <= status_code < 600:
            status_label.setText(f"Server Error ({status_code})")
            status_label.setStyleSheet("color: #f44336; font-size: 12px; font-weight: bold;")
        else:
            status_label.setText(f"Response ({status_code})")
            status_label.setStyleSheet("color: #666666; font-size: 12px; font-weight: bold;")

        progress_frame.setVisible(False)

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

        logger.info("Request completed successfully with status %d", response_data["status_code"])

    def on_request_failed(error_message):
        """Handle request failure."""
        send_button.setEnabled(True)
        send_button.setText("Send")
        cancel_button.setVisible(False)
        stop_request_timer()

        # Update status for error
        status_label.setText("Request Failed")
        status_label.setStyleSheet("color: #f44336; font-size: 12px; font-weight: bold;")

        progress_frame.setVisible(False)

        # Show error in response body
        response_body_edit.setPlainText(f"Error: {error_message}")
        response_body_edit.setStyleSheet(get_status_style("error"))

        # Clear other tabs
        response_headers_table.setRowCount(0)
        stats_text.setPlainText(f"Request failed: {error_message}")

        logger.error("Request failed: %s", error_message)

    def clear_all():
        """Clear all form data and responses."""
        url_input.clear()
        method_combo.setCurrentIndex(0)
        headers_table.clear_headers()
        body_input.clear()
        response_body_edit.clear()
        response_body_edit.setStyleSheet("")
        response_headers_table.setRowCount(0)
        stats_text.clear()

        # Reset status indicators
        status_label.setText("Ready")
        status_label.setStyleSheet("color: #666666; font-size: 12px;")
        elapsed_time_label.setText("")
        elapsed_timer.stop()

        logger.debug("All fields and status indicators cleared")

    def copy_response():
        """Copy response body to clipboard."""
        response_text = response_body_edit.toPlainText()
        if response_text:
            QApplication.clipboard().setText(response_text)
            logger.debug("Response copied to clipboard")

    def generate_curl_command() -> str:
        """Generate curl command from current request parameters."""
        method = method_combo.currentText()
        url = url_input.text().strip()
        if not url:
            return ""

        headers = get_headers()
        body = body_input.toPlainText().strip()

        curl_cmd = [f"curl -X {method}"]

        # Add headers with proper escaping
        for key, value in headers.items():
            # Escape double quotes in header values
            escaped_value = value.replace('"', '\\"')
            curl_cmd.append(f'-H "{key}: {escaped_value}"')

        # Add request body if present
        if body:
            # Escape double quotes and newlines in body
            escaped_body = body.replace('"', '\\"').replace("\n", "\\n")

            # Check if body is JSON
            try:
                json.loads(body)
                curl_cmd.append(f'-d "{escaped_body}"')
            except json.JSONDecodeError:
                # Handle form data
                if "x-www-form-urlencoded" in headers.get("Content-Type", ""):
                    curl_cmd.append(f'--data-urlencode "{escaped_body}"')
                else:
                    curl_cmd.append(f'-d "{escaped_body}"')

        # Escape URL special characters
        escaped_url = url.replace('"', '\\"')
        curl_cmd.append(f'"{escaped_url}"')

        logger.debug("Generated curl command: %s", " ".join(curl_cmd))
        return " ".join(curl_cmd)

    def copy_curl_to_scratch_pad():
        """Generate curl command and send to scratch pad."""
        if not scratch_pad:
            return

        curl_cmd = generate_curl_command()
        if not curl_cmd:
            logger.debug("No request parameters to generate curl command")
            return

        QApplication.clipboard().setText(curl_cmd)
        send_to_scratch_pad(scratch_pad, curl_cmd)
        logger.debug("cURL command copied to clipboard and scratch pad")

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
        copy_curl_button.clicked.connect(copy_curl_to_scratch_pad)

    def cancel_request():
        """Cancel the current HTTP request."""
        if http_client.cancel_request():
            send_button.setEnabled(True)
            send_button.setText("Send")
            cancel_button.setVisible(False)
            stop_request_timer()
            status_label.setText("Cancelled")
            status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
            progress_frame.setVisible(False)
            logger.debug("Request cancelled by user")

    def on_request_cancelled():
        """Handle request cancellation."""
        send_button.setEnabled(True)
        send_button.setText("Send")
        cancel_button.setVisible(False)
        stop_request_timer()
        status_label.setText("Cancelled")
        status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
        progress_frame.setVisible(False)
        logger.debug("Request was cancelled")

    def on_request_progress(message):
        """Handle request progress updates."""
        progress_label.setText(message)
        logger.debug("Progress update: %s", message)

    # Connect HTTP client signals
    http_client.request_started.connect(on_request_started)
    http_client.request_completed.connect(on_request_completed)
    http_client.request_failed.connect(on_request_failed)
    http_client.request_cancelled.connect(on_request_cancelled)
    http_client.request_progress.connect(on_request_progress)
    cancel_button.clicked.connect(cancel_request)

    # Add some default headers
    headers_table.add_header_row("Content-Type", "application/json")

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
