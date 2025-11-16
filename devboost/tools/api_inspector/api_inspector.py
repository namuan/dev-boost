import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import parse_qs, urlparse

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devboost.styles import get_tool_style

# Logger for debugging
logger = logging.getLogger(__name__)


@dataclass
class HTTPRequestData:
    """Data structure for captured HTTP requests."""

    timestamp: datetime
    method: str
    url: str
    headers: dict[str, str]
    query_params: dict[str, list[str]]
    body: str
    client_ip: str
    request_id: str
    content_length: int
    user_agent: str


@dataclass
class RequestStatistics:
    """Statistics data structure for request analysis."""

    total_requests: int = 0
    method_breakdown: dict[str, int] = field(default_factory=dict)
    requests_per_hour: list[int] = field(default_factory=list)
    average_body_size: float = 0.0
    top_endpoints: list[tuple[str, int]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class RequestStorage:
    """Thread-safe in-memory storage for captured HTTP requests."""

    def __init__(self, max_requests: int = 10000):
        self.max_requests = max_requests
        self._requests: list[HTTPRequestData] = []
        self._lock = threading.RLock()
        self._request_counter = 0

    def add_request(self, request_data: HTTPRequestData) -> None:
        """Add a new request to storage with thread safety."""
        with self._lock:
            # Implement circular buffer to prevent unlimited memory growth
            if len(self._requests) >= self.max_requests:
                self._requests.pop(0)

            self._requests.append(request_data)
            self._request_counter += 1
            logger.debug("Added request %s, total: %s", request_data.request_id, len(self._requests))

    def get_requests(self, filters: dict[str, Any] | None = None) -> list[HTTPRequestData]:
        """Get requests with optional filtering."""
        with self._lock:
            requests = self._requests.copy()

            if not filters:
                return requests

            # Apply filters
            if filters.get("method"):
                requests = [r for r in requests if r.method.upper() == filters["method"].upper()]

            if filters.get("url_pattern"):
                pattern = filters["url_pattern"].lower()
                requests = [r for r in requests if pattern in r.url.lower()]

            if filters.get("time_range"):
                # Filter by time range (last hour, day, etc.)
                now = datetime.now()
                if filters["time_range"] == "last_hour":
                    cutoff = now.replace(hour=now.hour - 1) if now.hour > 0 else now.replace(day=now.day - 1, hour=23)
                    requests = [r for r in requests if r.timestamp >= cutoff]
                elif filters["time_range"] == "last_day":
                    cutoff = now.replace(day=now.day - 1) if now.day > 1 else now.replace(month=now.month - 1, day=30)
                    requests = [r for r in requests if r.timestamp >= cutoff]

            return requests

    def get_statistics(self) -> RequestStatistics:
        """Calculate and return current statistics."""
        with self._lock:
            if not self._requests:
                return RequestStatistics()

            # Calculate method breakdown
            method_breakdown = {}
            total_body_size = 0
            endpoint_counts = {}

            for request in self._requests:
                # Method breakdown
                method = request.method.upper()
                method_breakdown[method] = method_breakdown.get(method, 0) + 1

                # Body size calculation
                total_body_size += request.content_length

                # Endpoint counting
                path = urlparse(request.url).path
                endpoint_counts[path] = endpoint_counts.get(path, 0) + 1

            # Calculate average body size
            avg_body_size = total_body_size / len(self._requests) if self._requests else 0

            # Get top endpoints
            top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return RequestStatistics(
                total_requests=len(self._requests),
                method_breakdown=method_breakdown,
                average_body_size=avg_body_size,
                top_endpoints=top_endpoints,
                last_updated=datetime.now(),
            )

    def clear_requests(self) -> None:
        """Clear all stored requests."""
        with self._lock:
            self._requests.clear()
            self._request_counter = 0
            logger.info("Cleared all stored requests")

    def get_request_count(self) -> int:
        """Get current request count."""
        with self._lock:
            return len(self._requests)


class APIInspectorRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that captures all incoming requests."""

    def __init__(self, request, client_address, server):
        self.storage = getattr(server, "storage", None)
        super().__init__(request, client_address, server)

    def _capture_request(self):
        """Capture and store the current request."""
        if not self.storage:
            return

        try:
            # Parse URL and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = ""
            if content_length > 0:
                body = self.rfile.read(content_length).decode("utf-8", errors="ignore")

            # Create request data
            request_data = HTTPRequestData(
                timestamp=datetime.now(),
                method=self.command,
                url=self.path,
                headers=dict(self.headers),
                query_params=query_params,
                body=body,
                client_ip=self.client_address[0],
                request_id=f"{int(time.time() * 1000)}_{id(self)}",
                content_length=content_length,
                user_agent=self.headers.get("User-Agent", ""),
            )

            # Store the request
            self.storage.add_request(request_data)

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

            response = {
                "status": "captured",
                "request_id": request_data.request_id,
                "method": self.command,
                "timestamp": request_data.timestamp.isoformat(),
            }
            self.wfile.write(json.dumps(response).encode())

        except Exception:
            logger.exception("Error capturing request")
            self.send_error(500, "Internal server error")

    def do_GET(self):
        self._capture_request()

    def do_POST(self):
        self._capture_request()

    def do_PUT(self):
        self._capture_request()

    def do_DELETE(self):
        self._capture_request()

    def do_PATCH(self):
        self._capture_request()

    def do_OPTIONS(self):
        self._capture_request()

    def do_HEAD(self):
        self._capture_request()

    def log_message(self, fmt, *args):
        """Override to use our logger instead of stderr."""
        logger.debug("HTTP Server: %s", fmt % args)


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server for handling concurrent requests."""

    daemon_threads = True
    allow_reuse_address = True


class APIInspectorServer(QObject):
    """HTTP capture server that runs in a separate thread."""

    request_captured = pyqtSignal(object)  # Signal emitted when request is captured
    server_started = pyqtSignal(int)  # Signal emitted when server starts (with port)
    server_stopped = pyqtSignal()  # Signal emitted when server stops
    server_error = pyqtSignal(str)  # Signal emitted on server error

    def __init__(self, port: int = 9010, storage: RequestStorage | None = None):
        super().__init__()
        self.port = port
        self.storage = storage or RequestStorage()
        self.server = None
        self.server_thread = None
        self._running = False

    def start_server(self) -> bool:
        """Start the HTTP server."""
        if self._running:
            logger.warning("Server is already running")
            return True

        try:
            # Try to start server on specified port, fallback to available port
            for port_attempt in range(self.port, self.port + 10):
                try:
                    self.server = ThreadingHTTPServer(("localhost", port_attempt), APIInspectorRequestHandler)
                    self.server.storage = self.storage
                    self.port = port_attempt
                    break
                except OSError:
                    if port_attempt == self.port + 9:  # Last attempt
                        raise
                    continue

            # Start server in separate thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

            self._running = True
            self.server_started.emit(self.port)
            logger.info("API Inspector server started on port %s", self.port)
            return True

        except Exception as e:
            error_msg = f"Failed to start server: {e}"
            logger.exception("Failed to start server")
            self.server_error.emit(error_msg)
            return False

    def _run_server(self):
        """Run the server (called in separate thread)."""
        try:
            self.server.serve_forever()
        except Exception:
            logger.exception("Server error")
            self.server_error.emit("Server error occurred")

    def stop_server(self) -> None:
        """Stop the HTTP server."""
        if not self._running:
            return

        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()

            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2.0)

            self._running = False
            self.server_stopped.emit()
            logger.info("API Inspector server stopped")

        except Exception:
            logger.exception("Error stopping server")

    def get_server_info(self) -> dict[str, Any]:
        """Get server information."""
        return {
            "running": self._running,
            "port": self.port,
            "url": f"http://localhost:{self.port}",
            "request_count": self.storage.get_request_count() if self.storage else 0,
        }

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running


class DataExporter:
    """Export captured request data in various formats."""

    def __init__(self, storage: RequestStorage):
        self.storage = storage

    def export_json(self, filters: dict[str, Any] | None = None) -> str:
        """Export requests as JSON string."""
        requests = self.storage.get_requests(filters)

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_requests": len(requests),
            "filters_applied": filters or {},
            "requests": [],
        }

        for request in requests:
            export_data["requests"].append({
                "timestamp": request.timestamp.isoformat(),
                "method": request.method,
                "url": request.url,
                "headers": request.headers,
                "query_params": request.query_params,
                "body": request.body,
                "client_ip": request.client_ip,
                "request_id": request.request_id,
                "content_length": request.content_length,
                "user_agent": request.user_agent,
            })

        return json.dumps(export_data, indent=2)

    def export_csv(self, filters: dict[str, Any] | None = None) -> str:
        """Export requests as CSV string."""
        requests = self.storage.get_requests(filters)

        # CSV header
        csv_lines = ["timestamp,method,url,client_ip,content_length,user_agent,headers,query_params,body"]

        for request in requests:
            # Escape and format fields for CSV
            headers_str = json.dumps(request.headers).replace('"', '""')
            query_params_str = json.dumps(request.query_params).replace('"', '""')
            body_str = request.body.replace('"', '""').replace("\n", "\\n")

            csv_line = f'"{request.timestamp.isoformat()}","{request.method}","{request.url}","{request.client_ip}",{request.content_length},"{request.user_agent}","{headers_str}","{query_params_str}","{body_str}"'
            csv_lines.append(csv_line)

        return "\n".join(csv_lines)

    def save_export(self, data: str, filename: str) -> bool:
        """Save export data to file."""
        try:
            Path(filename).write_text(data, encoding="utf-8")
            logger.info("Export saved to %s", filename)
            return True
        except Exception:
            logger.exception("Failed to save export")
            return False


def create_api_inspector_widget(style=None, scratch_pad_widget=None) -> QWidget:
    """
    Create and return the API Inspector widget using a factory pattern (no QWidget subclass),
    similar to how it's done in the json_diff tool.
    """
    # Core engine components
    storage = RequestStorage()
    server = APIInspectorServer(storage=storage)

    # Root widget and base layout
    root = QWidget()
    root.setStyleSheet(get_tool_style())
    layout = QVBoxLayout(root)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # ----------------- Server controls -----------------
    server_frame = QFrame()
    server_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    server_bar = QHBoxLayout(server_frame)

    status_label = QLabel("Server Status: Stopped")
    status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
    server_bar.addWidget(status_label)

    server_bar.addWidget(QLabel("Port:"))
    port_input = QLineEdit("9010")
    port_input.setMaximumWidth(80)
    server_bar.addWidget(port_input)

    toggle_btn = QPushButton("Start Server")
    clear_btn = QPushButton("Clear")
    refresh_btn = QPushButton("Refresh")
    server_bar.addStretch()
    server_bar.addWidget(toggle_btn)
    server_bar.addWidget(clear_btn)
    server_bar.addWidget(refresh_btn)

    layout.addWidget(server_frame)

    # ----------------- Statistics -----------------
    stats_frame = QFrame()
    stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    stats_bar = QHBoxLayout(stats_frame)
    total_label = QLabel("Total Requests: 0")
    avg_size_label = QLabel("Avg Body Size: 0 B")
    methods_label = QLabel("Methods: {}")
    stats_bar.addWidget(total_label)
    stats_bar.addWidget(avg_size_label)
    stats_bar.addWidget(methods_label)
    stats_bar.addStretch()
    layout.addWidget(stats_frame)

    # ----------------- Filters -----------------
    filters_frame = QFrame()
    filters_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    filters_bar = QHBoxLayout(filters_frame)
    filters_bar.addWidget(QLabel("Method:"))
    method_input = QLineEdit()
    method_input.setPlaceholderText("GET/POST/... (optional)")
    method_input.setMaximumWidth(120)
    filters_bar.addWidget(method_input)
    filters_bar.addWidget(QLabel("URL contains:"))
    url_pattern_input = QLineEdit()
    url_pattern_input.setPlaceholderText("pattern (optional)")
    filters_bar.addWidget(url_pattern_input)
    apply_filters_btn = QPushButton("Apply Filters")
    filters_bar.addStretch()
    filters_bar.addWidget(apply_filters_btn)
    layout.addWidget(filters_frame)

    # ----------------- Main Splitter -----------------
    splitter = QSplitter(Qt.Orientation.Horizontal)

    # Request list (left)
    request_table = QTableWidget()
    request_table.setColumnCount(6)
    request_table.setHorizontalHeaderLabels(["Time", "Method", "URL", "IP", "Length", "Agent"])
    request_table.horizontalHeader().setStretchLastSection(True)
    request_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    request_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    splitter.addWidget(request_table)

    # Request details (right)
    right_panel = QTabWidget()
    headers_view = QTextEdit()
    headers_view.setReadOnly(True)
    headers_view.setFont(QFont("Courier", 11))
    query_view = QTextEdit()
    query_view.setReadOnly(True)
    query_view.setFont(QFont("Courier", 11))
    body_view = QTextEdit()
    body_view.setReadOnly(True)
    body_view.setFont(QFont("Courier", 11))
    right_panel.addTab(headers_view, "Headers")
    right_panel.addTab(query_view, "Query Params")
    right_panel.addTab(body_view, "Body")
    splitter.addWidget(right_panel)
    splitter.setSizes([500, 600])
    layout.addWidget(splitter, 1)

    # ----------------- Export & Scratch -----------------
    export_frame = QFrame()
    export_frame.setFrameStyle(QFrame.Shape.StyledPanel)
    export_bar = QHBoxLayout(export_frame)
    export_json_btn = QPushButton("Export JSON…")
    export_csv_btn = QPushButton("Export CSV…")
    send_to_scratch_btn = QPushButton("Send to Scratch Pad")
    export_bar.addStretch()
    export_bar.addWidget(send_to_scratch_btn)
    export_bar.addWidget(export_json_btn)
    export_bar.addWidget(export_csv_btn)
    layout.addWidget(export_frame)

    # ----------------- Internal state -----------------
    current_filters: dict[str, Any] = {}
    selected_request: HTTPRequestData | None = None

    # ----------------- Helper functions -----------------
    def _collect_filters() -> dict[str, Any]:
        f: dict[str, Any] = {}
        m = method_input.text().strip()
        if m:
            f["method"] = m
        p = url_pattern_input.text().strip()
        if p:
            f["url_pattern"] = p
        return f

    def _refresh_statistics() -> None:
        stats = storage.get_statistics()
        total_label.setText(f"Total Requests: {stats.total_requests}")
        avg_size_label.setText(f"Avg Body Size: {int(stats.average_body_size)} B")
        methods_label.setText(f"Methods: {stats.method_breakdown}")

    def _refresh_table() -> None:
        reqs = storage.get_requests(current_filters or None)
        request_table.setRowCount(len(reqs))
        for row, r in enumerate(reqs):
            request_table.setItem(row, 0, QTableWidgetItem(r.timestamp.strftime("%H:%M:%S")))
            request_table.setItem(row, 1, QTableWidgetItem(r.method))
            request_table.setItem(row, 2, QTableWidgetItem(r.url))
            request_table.setItem(row, 3, QTableWidgetItem(r.client_ip))
            request_table.setItem(row, 4, QTableWidgetItem(str(r.content_length)))
            request_table.setItem(row, 5, QTableWidgetItem(r.user_agent))

    def _clear_details() -> None:
        headers_view.clear()
        query_view.clear()
        body_view.clear()

    def _display_request(r: HTTPRequestData) -> None:
        headers_view.setPlainText(json.dumps(r.headers, indent=2))
        query_view.setPlainText(json.dumps(r.query_params, indent=2))
        body_view.setPlainText(r.body)

    # ----------------- Slots & wiring -----------------
    def on_toggle_server():
        nonlocal current_filters
        try:
            port = int(port_input.text().strip() or "9010")
            server.port = port
        except ValueError:
            QMessageBox.warning(root, "Invalid Port", "Please enter a valid port number.")
            return

        if server.is_running():
            server.stop_server()
        else:
            if not server.start_server():
                QMessageBox.critical(root, "Server Error", "Failed to start the API Inspector server.")

    def on_clear():
        storage.clear_requests()
        _refresh_statistics()
        _refresh_table()
        _clear_details()

    def on_apply_filters():
        nonlocal current_filters
        current_filters = _collect_filters()
        _refresh_table()

    def on_export(fmt: str):
        exporter = DataExporter(storage)
        if fmt == "json":
            data = exporter.export_json(current_filters or None)
            filter_name = "json"
        else:
            data = exporter.export_csv(current_filters or None)
            filter_name = "csv"
        file_path, _ = QFileDialog.getSaveFileName(
            root,
            "Save export",
            f"api_inspector_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{filter_name}",
            f"*.{filter_name}",
        )
        if file_path:
            ok = exporter.save_export(data, file_path)
            if not ok:
                QMessageBox.critical(root, "Save Error", "Failed to save the export file.")

    def on_send_to_scratch():
        if not scratch_pad_widget:
            QMessageBox.information(root, "Scratch Pad", "Scratch Pad is not available.")
            return
        if selected_request is None:
            QMessageBox.information(root, "Scratch Pad", "Select a request to send.")
            return
        r = selected_request
        content = json.dumps(
            {
                "timestamp": r.timestamp.isoformat(),
                "method": r.method,
                "url": r.url,
                "headers": r.headers,
                "query_params": r.query_params,
                "body": r.body,
                "client_ip": r.client_ip,
            },
            indent=2,
        )
        # Assumes scratch pad follows `ScratchPadWidget` API
        if hasattr(scratch_pad_widget, "set_content") and callable(scratch_pad_widget.set_content):
            scratch_pad_widget.set_content(content)

    def on_table_selection_change():
        nonlocal selected_request
        row = request_table.currentRow()
        if row < 0:
            selected_request = None
            _clear_details()
            return
        reqs = storage.get_requests(current_filters or None)
        if 0 <= row < len(reqs):
            selected_request = reqs[row]
            _display_request(selected_request)
        else:
            selected_request = None
            _clear_details()

    # Wire buttons
    toggle_btn.clicked.connect(on_toggle_server)
    clear_btn.clicked.connect(on_clear)
    refresh_btn.clicked.connect(lambda: (_refresh_statistics(), _refresh_table()))
    apply_filters_btn.clicked.connect(on_apply_filters)
    export_json_btn.clicked.connect(lambda: on_export("json"))
    export_csv_btn.clicked.connect(lambda: on_export("csv"))
    send_to_scratch_btn.clicked.connect(on_send_to_scratch)
    request_table.itemSelectionChanged.connect(on_table_selection_change)

    # Server signals
    def _on_server_started(port: int):
        status_label.setText(f"Server Status: Running on port {port}")
        status_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
        # Update toggle button to reflect current action (stop when running)
        try:
            toggle_btn.setText("Stop Server")
            toggle_btn.setToolTip("Click to stop the server")
        except Exception:
            logger.exception("Failed to update toggle button text on server start")

    def _on_server_stopped():
        status_label.setText("Server Status: Stopped")
        status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        # Update toggle button to reflect current action (start when stopped)
        try:
            toggle_btn.setText("Start Server")
            toggle_btn.setToolTip("Click to start the server")
        except Exception:
            logger.exception("Failed to update toggle button text on server stop")

    def _on_server_error(msg: str):
        QMessageBox.critical(root, "Server Error", msg)

    server.server_started.connect(_on_server_started)
    server.server_stopped.connect(_on_server_stopped)
    server.server_error.connect(_on_server_error)

    # Refresh timer
    timer = QTimer(root)
    timer.setInterval(1000)
    timer.timeout.connect(lambda: (_refresh_statistics(), _refresh_table()))
    timer.start()

    # Initial refresh
    _refresh_statistics()
    _refresh_table()
    _clear_details()

    return root
