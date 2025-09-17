import json
import logging
import time
from typing import Any

import requests
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
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

# Common GraphQL queries for autocomplete
COMMON_GRAPHQL_QUERIES = {
    "introspection": """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
    directives {
      name
      description
      locations
      args {
        ...InputValue
      }
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
      }
    }
  }
}""",
    "simple_query": """
query {
  # Add your query fields here
}""",
    "simple_mutation": """
mutation {
  # Add your mutation fields here
}""",
    "simple_subscription": """
subscription {
  # Add your subscription fields here
}""",
}


class GraphQLWorkerThread(QThread):
    """
    Worker thread for handling GraphQL requests asynchronously to keep UI responsive.

    This thread performs the actual GraphQL request in the background and emits
    signals to communicate with the main UI thread.
    """

    # Signals to communicate with main thread
    request_completed = pyqtSignal(dict)  # response_data
    request_failed = pyqtSignal(str)  # error_message
    request_cancelled = pyqtSignal()  # request was cancelled
    request_progress = pyqtSignal(str)  # progress message

    def __init__(
        self,
        url: str,
        query: str,
        variables: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ):
        """
        Initialize the GraphQL worker thread with request parameters.

        Args:
            url: GraphQL endpoint URL
            query: GraphQL query, mutation, or subscription
            variables: Optional dictionary of GraphQL variables
            headers: Optional dictionary of headers
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.url = url
        self.query = query
        self.variables = variables or {}
        self.headers = headers or {}
        self.timeout = timeout
        self.session = requests.Session()
        self._cancelled = False
        logger.debug("GraphQLWorkerThread initialized for %s", url)

    def cancel(self):
        """
        Cancel the current request by setting the cancelled flag and closing the session.

        This will interrupt any ongoing GraphQL request and prevent new ones from starting.
        """
        self._cancelled = True
        logger.info("GraphQL request cancellation requested")

        # Close the session to interrupt any ongoing requests
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
                logger.debug("GraphQL session closed for cancellation")
        except Exception as e:
            logger.warning("Error closing GraphQL session during cancellation: %s", e)

    def run(self):
        """
        Execute the GraphQL request in the worker thread.

        This method runs in the background thread and emits signals
        to communicate results back to the main thread.
        """
        if self._cancelled:
            logger.info("GraphQL request cancelled before execution")
            self.request_cancelled.emit()
            return

        try:
            logger.info("Worker thread making GraphQL request to %s", self.url)
            self.request_progress.emit("Preparing GraphQL request...")

            # Prepare GraphQL request payload
            payload = {
                "query": self.query,
            }

            # Add variables if provided
            if self.variables:
                payload["variables"] = self.variables
                logger.debug("GraphQL variables added: %s", self.variables)

            # Prepare headers
            request_headers = self.headers.copy()
            if "Content-Type" not in request_headers:
                request_headers["Content-Type"] = "application/json"

            # Record start time
            start_time = time.time()

            # Check for cancellation before making request
            if self._cancelled:
                logger.info("GraphQL request cancelled before execution")
                self.request_cancelled.emit()
                return

            self.request_progress.emit("Sending GraphQL request...")

            # Make the GraphQL request (always POST)
            response = self.session.post(
                url=self.url,
                json=payload,
                headers=request_headers,
                timeout=self.timeout,
                allow_redirects=True,
            )

            # Check for cancellation after request
            if self._cancelled:
                logger.info("GraphQL request cancelled after execution")
                self.request_cancelled.emit()
                return

            # Calculate response time
            response_time = time.time() - start_time
            self.request_progress.emit("Processing GraphQL response...")

            # Process response
            response_data = self._process_graphql_response(response, response_time)
            logger.info("Worker thread GraphQL request completed with status %d", response.status_code)
            self.request_progress.emit("GraphQL request completed successfully")
            self.request_completed.emit(response_data)

        except requests.exceptions.Timeout:
            if not self._cancelled:
                error_msg = f"GraphQL request timed out after {self.timeout} seconds"
                logger.exception(error_msg)
                self.request_failed.emit(error_msg)
        except requests.exceptions.ConnectionError:
            if not self._cancelled:
                error_msg = "Connection error - please check the GraphQL endpoint URL and your internet connection"
                logger.exception(error_msg)
                self.request_failed.emit(error_msg)
        except requests.exceptions.RequestException as e:
            if not self._cancelled:
                error_msg = f"GraphQL request failed: {e!s}"
                logger.exception(error_msg)
                self.request_failed.emit(error_msg)
        except Exception as e:
            if not self._cancelled:
                error_msg = f"Unexpected error in GraphQL request: {e!s}"
                logger.exception(error_msg)
                self.request_failed.emit(error_msg)

    def _process_graphql_response(self, response: requests.Response, response_time: float) -> dict[str, Any]:
        """
        Processes the GraphQL response and extracts relevant information.

        Args:
            response: The requests Response object
            response_time: Time taken for the request in seconds

        Returns:
            Dictionary containing processed GraphQL response data
        """
        # Calculate response size
        response_size = len(response.content)

        # Format headers
        response_headers = dict(response.headers)

        # Parse GraphQL response
        try:
            response_json = response.json()

            # GraphQL responses should always be JSON
            response_body = json.dumps(response_json, indent=2)
            content_type = "application/json"

            # Extract GraphQL-specific data
            graphql_data = response_json.get("data")
            graphql_errors = response_json.get("errors", [])
            graphql_extensions = response_json.get("extensions")

            logger.debug(
                "GraphQL response parsed - data: %s, errors: %d",
                "present" if graphql_data else "null",
                len(graphql_errors),
            )

        except (json.JSONDecodeError, ValueError) as e:
            # Fallback for non-JSON responses (shouldn't happen with GraphQL)
            response_body = response.text
            content_type = response.headers.get("content-type", "text/plain")
            graphql_data = None
            graphql_errors = [{"message": f"Invalid JSON response: {e!s}"}]
            graphql_extensions = None
            logger.warning("GraphQL response is not valid JSON: %s", e)

        return {
            "status_code": response.status_code,
            "status_text": response.reason,
            "headers": response_headers,
            "body": response_body,
            "content_type": content_type,
            "response_time": response_time,
            "response_size": response_size,
            "url": response.url,
            "method": "POST",  # GraphQL is always POST
            # GraphQL-specific fields
            "graphql_data": graphql_data,
            "graphql_errors": graphql_errors,
            "graphql_extensions": graphql_extensions,
        }


class GraphQLClient(QObject):
    """
    Backend GraphQL client logic with proper error handling and response processing.
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
        logger.info("GraphQLClient initialized with async worker support and request queue")

    def make_request(
        self,
        url: str,
        query: str,
        variables: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> str:
        """
        Makes a GraphQL request asynchronously using a worker thread to keep UI responsive.
        Supports request queuing for multiple concurrent requests.

        Args:
            url: GraphQL endpoint URL
            query: GraphQL query, mutation, or subscription
            variables: Optional dictionary of GraphQL variables
            headers: Optional dictionary of headers
            timeout: Request timeout in seconds

        Returns:
            str: Request ID for tracking the request
        """
        # Generate unique request ID
        self._request_id_counter += 1
        request_id = f"gql_req_{self._request_id_counter}"

        logger.info("Queuing async GraphQL request to %s (ID: %s)", url, request_id)

        # Create request data
        request_data = {
            "id": request_id,
            "url": url,
            "query": query,
            "variables": variables,
            "headers": headers,
            "timeout": timeout,
        }

        # Add to queue
        self.request_queue.append(request_data)

        # Process queue
        self._process_request_queue()

        return request_id

    def cancel_request(self, request_id: str | None = None) -> bool:
        """
        Cancel a GraphQL request. If request_id is provided, cancels that specific request.
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
                    logger.info("Cancelling GraphQL request %s", request_id)
                    worker.cancel()
                    cancelled = True

            # Remove from queue if not yet started
            self.request_queue = [req for req in self.request_queue if req["id"] != request_id]
        else:
            # Cancel all active requests
            for req_id, worker in self.active_workers.items():
                if worker.isRunning():
                    logger.info("Cancelling GraphQL request %s", req_id)
                    worker.cancel()
                    cancelled = True

            # Clear queue
            if self.request_queue:
                logger.info("Clearing %d queued GraphQL requests", len(self.request_queue))
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

            logger.info("Starting worker for GraphQL request %s", request_id)

            # Create and configure worker thread
            worker = GraphQLWorkerThread(
                request_data["url"],
                request_data["query"],
                request_data["variables"],
                request_data["headers"],
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
            logger.debug("Worker thread started for GraphQL request %s", request_id)

    def _handle_request_completed(self, request_id: str, data: dict):
        """Handle request completion with request ID context."""
        logger.info("GraphQL request %s completed successfully", request_id)
        data["request_id"] = request_id
        self.request_completed.emit(data)

    def _handle_request_failed(self, request_id: str, error: str):
        """Handle request failure with request ID context."""
        logger.info("GraphQL request %s failed: %s", request_id, error)
        self.request_failed.emit(f"[{request_id}] {error}")

    def _handle_request_cancelled(self, request_id: str):
        """Handle request cancellation with request ID context."""
        logger.info("GraphQL request %s was cancelled", request_id)
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
            logger.debug("Worker thread for GraphQL request %s cleaned up", request_id)

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
def create_graphql_client_widget(style_func, scratch_pad=None):
    """
    Creates the main widget for the GraphQL client tool.

    Args:
        style_func: A function that returns a QStyle object to fetch standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The main widget for the tool.
    """
    graphql_client = GraphQLClient()

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
    copy_query_button = QPushButton("Copy Query")
    introspect_button = QPushButton("Introspect Schema")

    action_layout.addWidget(clear_button)
    action_layout.addWidget(copy_response_button)
    action_layout.addWidget(introspect_button)
    if scratch_pad:
        action_layout.addWidget(send_to_scratch_button)
        action_layout.addWidget(copy_query_button)

    request_layout.addLayout(action_layout)

    # URL row
    url_layout = QHBoxLayout()
    url_layout.setSpacing(8)

    # GraphQL endpoint label
    endpoint_label = QLabel("GraphQL Endpoint:")
    endpoint_label.setFixedWidth(120)
    url_layout.addWidget(endpoint_label)

    # URL input
    url_input = QLineEdit()
    url_input.setPlaceholderText("Enter GraphQL endpoint (e.g., https://api.example.com/graphql)")
    url_layout.addWidget(url_input)

    # Send button
    send_button = QPushButton("Execute")
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

    # Simple headers table (reusing HTTP client's AutoCompleteTableWidget)
    from devboost.tools.http_client import AutoCompleteTableWidget

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

    # GraphQL Query section
    query_label = QLabel("GraphQL Query:")
    request_layout.addWidget(query_label)

    # Query type selector
    query_type_layout = QHBoxLayout()
    query_type_combo = QComboBox()
    query_types = ["Custom Query", "Simple Query", "Simple Mutation", "Simple Subscription", "Schema Introspection"]
    query_type_combo.addItems(query_types)
    query_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

    query_type_label = QLabel("Template:")
    query_type_label.setFixedWidth(60)
    query_type_layout.addWidget(query_type_label)
    query_type_layout.addWidget(query_type_combo)
    query_type_layout.addStretch()

    request_layout.addLayout(query_type_layout)

    # Query input
    query_input = QTextEdit()
    query_input.setPlaceholderText("Enter your GraphQL query, mutation, or subscription here...")
    query_input.setMaximumHeight(200)
    request_layout.addWidget(query_input)

    # Variables section
    variables_label = QLabel("Variables (JSON):")
    request_layout.addWidget(variables_label)

    variables_input = QTextEdit()
    variables_input.setPlaceholderText('Enter variables as JSON (e.g., {"id": "123", "name": "example"})')
    variables_input.setMaximumHeight(100)
    request_layout.addWidget(variables_input)

    main_layout.addWidget(request_frame)

    # Progress section with enhanced visual feedback
    progress_frame = QFrame()
    progress_frame.setVisible(False)
    progress_layout = QVBoxLayout(progress_frame)
    progress_layout.setContentsMargins(10, 5, 10, 5)
    progress_layout.setSpacing(5)

    # Progress label for status text
    progress_label = QLabel("Preparing GraphQL request...")
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

    # Response data tab
    response_data_edit = QTextEdit()
    response_data_edit.setReadOnly(True)
    response_tabs.addTab(response_data_edit, "Response Data")

    # Response errors tab
    response_errors_edit = QTextEdit()
    response_errors_edit.setReadOnly(True)
    response_tabs.addTab(response_errors_edit, "Errors")

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
        logger.debug("Added header row %d", row_index)

    def delete_header_row():
        """Delete selected header row(s) from the table."""
        deleted_count = headers_table.delete_selected_rows()
        logger.debug("Deleted %d header row(s)", deleted_count)

    def get_headers() -> dict[str, str]:
        """Extract headers from the table."""
        headers = headers_table.get_headers()
        logger.debug("Extracted headers: %s", headers)
        return headers

    def load_query_template():
        """Load a query template based on selection."""
        template_name = query_type_combo.currentText()
        logger.debug("Loading query template: %s", template_name)

        if template_name == "Simple Query":
            query_input.setPlainText(COMMON_GRAPHQL_QUERIES["simple_query"])
        elif template_name == "Simple Mutation":
            query_input.setPlainText(COMMON_GRAPHQL_QUERIES["simple_mutation"])
        elif template_name == "Simple Subscription":
            query_input.setPlainText(COMMON_GRAPHQL_QUERIES["simple_subscription"])
        elif template_name == "Schema Introspection":
            query_input.setPlainText(COMMON_GRAPHQL_QUERIES["introspection"])
        # "Custom Query" doesn't change the text

    def make_request():
        """Make GraphQL request with current form data."""
        url = url_input.text().strip()
        query = query_input.toPlainText().strip()
        variables_text = variables_input.toPlainText().strip()
        headers = get_headers()

        if not url:
            QMessageBox.warning(widget, "Warning", "Please enter a GraphQL endpoint URL")
            return

        if not query:
            QMessageBox.warning(widget, "Warning", "Please enter a GraphQL query")
            return

        # Parse variables
        variables = {}
        if variables_text:
            try:
                variables = json.loads(variables_text)
                logger.debug("Parsed variables: %s", variables)
            except json.JSONDecodeError as e:
                QMessageBox.warning(widget, "Warning", f"Invalid JSON in variables: {e!s}")
                return

        logger.info("Initiating GraphQL request to %s", url)
        graphql_client.make_request(url, query, variables, headers)

    def on_request_started():
        """Handle request start."""
        send_button.setEnabled(False)
        send_button.setText("Executing...")
        cancel_button.setVisible(True)
        progress_frame.setVisible(True)
        progress_bar.setRange(0, 0)  # Indeterminate progress
        progress_label.setText("Starting GraphQL request...")
        status_label.setText("Executing query...")
        status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
        start_request_timer()
        logger.debug("GraphQL request started - UI updated")

    def on_request_completed(response_data):
        """Handle successful request completion."""
        send_button.setEnabled(True)
        send_button.setText("Execute")
        cancel_button.setVisible(False)
        stop_request_timer()

        # Update status based on response code
        status_code = response_data.get("status_code", 0)
        graphql_errors = response_data.get("graphql_errors", [])

        if 200 <= status_code < 300 and not graphql_errors:
            status_label.setText(f"Success ({status_code})")
            status_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
        elif graphql_errors:
            status_label.setText(f"GraphQL Errors ({status_code})")
            status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
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

        # Update response data tab
        graphql_data = response_data.get("graphql_data")
        if graphql_data is not None:
            formatted_data = json.dumps(graphql_data, indent=2)
            response_data_edit.setPlainText(formatted_data)
        else:
            response_data_edit.setPlainText("No data returned")

        # Update response errors tab
        if graphql_errors:
            formatted_errors = json.dumps(graphql_errors, indent=2)
            response_errors_edit.setPlainText(formatted_errors)
            response_errors_edit.setStyleSheet(get_status_style("error"))
        else:
            response_errors_edit.setPlainText("No errors")
            response_errors_edit.setStyleSheet("")

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
Content Type: {response_data["content_type"]}
GraphQL Errors: {len(graphql_errors)}"""
        stats_text.setPlainText(stats_info)

        # Set status color based on response
        if 200 <= status_code < 300 and not graphql_errors:
            response_data_edit.setStyleSheet(get_status_style("success"))
        elif graphql_errors:
            response_data_edit.setStyleSheet(get_status_style("warning"))
        else:
            response_data_edit.setStyleSheet(get_status_style("error"))

        logger.info("GraphQL request completed with status %d, %d errors", status_code, len(graphql_errors))

    def on_request_failed(error_message):
        """Handle request failure."""
        send_button.setEnabled(True)
        send_button.setText("Execute")
        cancel_button.setVisible(False)
        stop_request_timer()

        # Update status for error
        status_label.setText("Request Failed")
        status_label.setStyleSheet("color: #f44336; font-size: 12px; font-weight: bold;")

        progress_frame.setVisible(False)

        # Show error in response tabs
        response_data_edit.setPlainText(f"Error: {error_message}")
        response_data_edit.setStyleSheet(get_status_style("error"))
        response_errors_edit.setPlainText(f"Request Error: {error_message}")
        response_errors_edit.setStyleSheet(get_status_style("error"))

        # Clear other tabs
        response_headers_table.setRowCount(0)
        stats_text.setPlainText(f"Request failed: {error_message}")

        logger.error("GraphQL request failed: %s", error_message)

    def clear_all():
        """Clear all form data and responses."""
        url_input.clear()
        query_input.clear()
        variables_input.clear()
        headers_table.clear_headers()
        response_data_edit.clear()
        response_errors_edit.clear()
        response_data_edit.setStyleSheet("")
        response_errors_edit.setStyleSheet("")
        response_headers_table.setRowCount(0)
        stats_text.clear()

        # Reset status indicators
        status_label.setText("Ready")
        status_label.setStyleSheet("color: #666666; font-size: 12px;")
        elapsed_time_label.setText("")
        elapsed_timer.stop()

        # Reset to default headers
        headers_table.add_header_row("Content-Type", "application/json")

        logger.debug("All fields and status indicators cleared")

    def copy_response():
        """Copy response data to clipboard."""
        response_text = response_data_edit.toPlainText()
        if response_text:
            QApplication.clipboard().setText(response_text)
            logger.debug("Response copied to clipboard")

    def copy_query():
        """Copy current query to clipboard."""
        query_text = query_input.toPlainText()
        if query_text:
            QApplication.clipboard().setText(query_text)
            logger.debug("Query copied to clipboard")

    def send_to_scratch_pad_func():
        """Send response to scratch pad."""
        if scratch_pad:
            response_text = response_data_edit.toPlainText()
            if response_text:
                send_to_scratch_pad(scratch_pad, response_text)
                logger.debug("Response sent to scratch pad")

    def introspect_schema():
        """Load schema introspection query."""
        query_input.setPlainText(COMMON_GRAPHQL_QUERIES["introspection"])
        logger.debug("Schema introspection query loaded")

    def cancel_request():
        """Cancel the current GraphQL request."""
        if graphql_client.cancel_request():
            send_button.setEnabled(True)
            send_button.setText("Execute")
            cancel_button.setVisible(False)
            stop_request_timer()
            status_label.setText("Cancelled")
            status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
            progress_frame.setVisible(False)
            logger.debug("GraphQL request cancelled by user")

    def on_request_cancelled():
        """Handle request cancellation."""
        send_button.setEnabled(True)
        send_button.setText("Execute")
        cancel_button.setVisible(False)
        stop_request_timer()
        status_label.setText("Cancelled")
        status_label.setStyleSheet("color: #ff9800; font-size: 12px; font-weight: bold;")
        progress_frame.setVisible(False)
        logger.debug("GraphQL request was cancelled")

    def on_request_progress(message):
        """Handle request progress updates."""
        progress_label.setText(message)
        logger.debug("Progress update: %s", message)

    # Connect GraphQL client signals
    graphql_client.request_started.connect(on_request_started)
    graphql_client.request_completed.connect(on_request_completed)
    graphql_client.request_failed.connect(on_request_failed)
    graphql_client.request_cancelled.connect(on_request_cancelled)
    graphql_client.request_progress.connect(on_request_progress)

    # Connect UI signals
    query_type_combo.currentTextChanged.connect(lambda: load_query_template())
    add_header_button.clicked.connect(add_header_row)
    delete_header_button.clicked.connect(delete_header_row)
    send_button.clicked.connect(make_request)
    cancel_button.clicked.connect(cancel_request)
    clear_button.clicked.connect(clear_all)
    copy_response_button.clicked.connect(copy_response)
    introspect_button.clicked.connect(introspect_schema)

    if scratch_pad:
        send_to_scratch_button.clicked.connect(send_to_scratch_pad_func)
        copy_query_button.clicked.connect(copy_query)

    # Add keyboard shortcuts
    execute_shortcut = QShortcut(QKeySequence("Ctrl+Return"), widget)
    execute_shortcut.activated.connect(make_request)
    logger.debug("Execute shortcut (Ctrl+Enter) created")

    clear_shortcut = QShortcut(QKeySequence("Ctrl+R"), widget)
    clear_shortcut.activated.connect(clear_all)
    logger.debug("Clear shortcut (Ctrl+R) created")

    # Add macOS shortcuts as well
    execute_shortcut_mac = QShortcut(QKeySequence("Cmd+Return"), widget)
    execute_shortcut_mac.activated.connect(make_request)
    logger.debug("Execute shortcut (Cmd+Enter) created for macOS")

    clear_shortcut_mac = QShortcut(QKeySequence("Cmd+R"), widget)
    clear_shortcut_mac.activated.connect(clear_all)
    logger.debug("Clear shortcut (Cmd+R) created for macOS")

    # Add some default headers
    headers_table.add_header_row("Content-Type", "application/json")

    logger.info("GraphQL Client widget created successfully with keyboard shortcuts")
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
        new_content = f"{current_content}\n\n--- GraphQL Response ---\n{content}" if current_content else content
        scratch_pad.set_content(new_content)
        logger.debug("Content sent to scratch pad")
