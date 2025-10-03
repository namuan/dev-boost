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

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
)

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
    """Create and return the API Inspector widget."""
    from .api_inspector_ui import APIInspectorDashboard

    # Create storage and server
    storage = RequestStorage()
    server = APIInspectorServer(storage=storage)

    # Create and return dashboard
    return APIInspectorDashboard(server, storage, scratch_pad_widget)
