import json
import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
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


class APIInspectorDashboard(QWidget):
    """Main dashboard widget for the API Inspector tool."""

    def __init__(self, server, storage, scratch_pad_widget=None):
        super().__init__()
        self.server = server
        self.storage = storage
        self.scratch_pad_widget = scratch_pad_widget

        # Connect server signals
        self.server.server_started.connect(self._on_server_started)
        self.server.server_stopped.connect(self._on_server_stopped)
        self.server.server_error.connect(self._on_server_error)

        # UI state
        self.current_filters = {}
        self.selected_request = None

        # Setup UI
        self._setup_ui()
        self._setup_refresh_timer()

        # Apply styling
        self.setStyleSheet(get_tool_style())

    def _setup_ui(self):
        """Setup the main UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Server controls section
        server_frame = self._create_server_controls()
        layout.addWidget(server_frame, 0)  # No stretch - minimal space

        # Statistics section
        stats_frame = self._create_statistics_panel()
        layout.addWidget(stats_frame, 0)  # No stretch - minimal space

        # Filters section
        filters_frame = self._create_filters_panel()
        layout.addWidget(filters_frame, 0)  # No stretch - minimal space

        # Main content area with splitter - this should take most space
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Request list
        self.request_list = self._create_request_list()
        splitter.addWidget(self.request_list)

        # Request details
        self.request_details = self._create_request_details()
        splitter.addWidget(self.request_details)

        # Set splitter proportions
        splitter.setSizes([400, 600])
        layout.addWidget(splitter, 1)  # Stretch factor 1 - takes majority of space

        # Export controls
        export_frame = self._create_export_controls()
        layout.addWidget(export_frame, 0)  # No stretch - minimal space

    def _create_server_controls(self) -> QFrame:
        """Create server control panel."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)

        # Server status label
        self.status_label = QLabel("Server Status: Stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.status_label)

        # Port input
        layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("9010")
        self.port_input.setMaximumWidth(80)
        layout.addWidget(self.port_input)

        # Start/Stop button
        self.start_stop_btn = QPushButton("Start Server")
        self.start_stop_btn.clicked.connect(self._toggle_server)
        layout.addWidget(self.start_stop_btn)

        # Server URL label
        self.url_label = QLabel("")
        layout.addWidget(self.url_label)

        layout.addStretch()

        # Clear requests button
        clear_btn = QPushButton("Clear Requests")
        clear_btn.clicked.connect(self._clear_requests)
        layout.addWidget(clear_btn)

        return frame

    def _create_statistics_panel(self) -> QFrame:
        """Create statistics display panel."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)

        # Total requests
        self.total_label = QLabel("Total: 0")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.total_label)

        # Method breakdown labels
        self.method_labels = {}
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]:
            label = QLabel(f"{method}: 0")
            label.setStyleSheet("margin-left: 15px;")
            self.method_labels[method] = label
            layout.addWidget(label)

        layout.addStretch()

        # Last updated
        self.updated_label = QLabel("Last updated: Never")
        self.updated_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self.updated_label)

        return frame

    def _create_filters_panel(self) -> QFrame:
        """Create filtering controls."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(frame)

        # Search input
        layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by URL pattern...")
        self.search_input.textChanged.connect(self._apply_filters)
        layout.addWidget(self.search_input)

        # Method filter
        layout.addWidget(QLabel("Method:"))
        self.method_filter = QComboBox()
        self.method_filter.addItems(["All", "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
        self.method_filter.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.method_filter)

        # Time range filter
        layout.addWidget(QLabel("Time Range:"))
        self.time_filter = QComboBox()
        self.time_filter.addItems(["All Time", "Last Hour", "Last Day"])
        self.time_filter.currentTextChanged.connect(self._apply_filters)
        layout.addWidget(self.time_filter)

        layout.addStretch()

        return frame

    def _create_request_list(self) -> QTableWidget:
        """Create request list table."""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Time", "Method", "URL", "Status", "Size"])

        # Configure table
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Method
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # URL
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Size

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.itemSelectionChanged.connect(self._on_request_selected)

        return table

    def _create_request_details(self) -> QTabWidget:
        """Create request details viewer."""
        tabs = QTabWidget()

        # Headers tab
        self.headers_text = QTextEdit()
        self.headers_text.setReadOnly(True)
        self.headers_text.setFont(QFont("Courier", 10))
        tabs.addTab(self.headers_text, "Headers")

        # Query Parameters tab
        self.query_text = QTextEdit()
        self.query_text.setReadOnly(True)
        self.query_text.setFont(QFont("Courier", 10))
        tabs.addTab(self.query_text, "Query Params")

        # Body tab
        self.body_text = QTextEdit()
        self.body_text.setReadOnly(True)
        self.body_text.setFont(QFont("Courier", 10))
        tabs.addTab(self.body_text, "Body")

        # Raw tab
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFont(QFont("Courier", 10))
        tabs.addTab(self.raw_text, "Raw Data")

        return tabs

    def _create_export_controls(self) -> QFrame:
        """Create export control buttons."""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        layout.addStretch()

        # Export JSON button
        json_btn = QPushButton("Export JSON")
        json_btn.clicked.connect(lambda: self._export_data("json"))
        layout.addWidget(json_btn)

        # Export CSV button
        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(lambda: self._export_data("csv"))
        layout.addWidget(csv_btn)

        # Send to Scratch Pad button
        if self.scratch_pad_widget:
            scratch_btn = QPushButton("Send to Scratch Pad")
            scratch_btn.clicked.connect(self._send_to_scratch_pad)
            layout.addWidget(scratch_btn)

        return frame

    def _setup_refresh_timer(self):
        """Setup timer for refreshing UI data."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        self.refresh_timer.start(1000)  # Refresh every second

    def _toggle_server(self):
        """Toggle server start/stop."""
        if self.server.is_running():
            self.server.stop_server()
        else:
            try:
                port = int(self.port_input.text())
                self.server.port = port
                self.server.start_server()
            except ValueError:
                QMessageBox.warning(self, "Invalid Port", "Please enter a valid port number.")

    def _clear_requests(self):
        """Clear all stored requests."""
        reply = QMessageBox.question(
            self,
            "Clear Requests",
            "Are you sure you want to clear all captured requests?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.storage.clear_requests()
            self._refresh_request_list()
            self._clear_request_details()

    def _apply_filters(self):
        """Apply current filters and refresh request list."""
        # Build filters dictionary
        filters = {}

        # Search filter
        search_text = self.search_input.text().strip()
        if search_text:
            filters["url_pattern"] = search_text

        # Method filter
        method = self.method_filter.currentText()
        if method != "All":
            filters["method"] = method

        # Time range filter
        time_range = self.time_filter.currentText()
        if time_range == "Last Hour":
            filters["time_range"] = "last_hour"
        elif time_range == "Last Day":
            filters["time_range"] = "last_day"

        self.current_filters = filters
        self._refresh_request_list()

    def _refresh_data(self):
        """Refresh all UI data."""
        self._refresh_statistics()
        self._refresh_request_list()

    def _refresh_statistics(self):
        """Refresh statistics display."""
        stats = self.storage.get_statistics()

        # Update total
        self.total_label.setText(f"Total: {stats.total_requests}")

        # Update method breakdown
        for method, label in self.method_labels.items():
            count = stats.method_breakdown.get(method, 0)
            label.setText(f"{method}: {count}")

        # Update last updated
        self.updated_label.setText(f"Last updated: {stats.last_updated.strftime('%H:%M:%S')}")

    def _refresh_request_list(self):
        """Refresh request list table."""
        requests = self.storage.get_requests(self.current_filters)

        # Clear and populate table
        self.request_list.setRowCount(len(requests))

        for row, request in enumerate(reversed(requests)):  # Show newest first
            # Time
            time_str = request.timestamp.strftime("%H:%M:%S")
            self.request_list.setItem(row, 0, QTableWidgetItem(time_str))

            # Method
            method_item = QTableWidgetItem(request.method)
            if request.method in ["GET"]:
                method_item.setBackground(Qt.GlobalColor.lightGray)
            elif request.method in ["POST", "PUT", "PATCH"]:
                method_item.setBackground(Qt.GlobalColor.yellow)
            elif request.method in ["DELETE"]:
                method_item.setBackground(Qt.GlobalColor.red)
            self.request_list.setItem(row, 1, method_item)

            # URL
            self.request_list.setItem(row, 2, QTableWidgetItem(request.url))

            # Status (always 200 for captured requests)
            self.request_list.setItem(row, 3, QTableWidgetItem("200"))

            # Size
            size_str = (
                f"{request.content_length} B"
                if request.content_length < 1024
                else f"{request.content_length / 1024:.1f} KB"
            )
            self.request_list.setItem(row, 4, QTableWidgetItem(size_str))

            # Store request data in row
            self.request_list.item(row, 0).setData(Qt.ItemDataRole.UserRole, request)

    def _on_request_selected(self):
        """Handle request selection in the list."""
        current_row = self.request_list.currentRow()
        if current_row >= 0:
            item = self.request_list.item(current_row, 0)
            if item:
                request = item.data(Qt.ItemDataRole.UserRole)
                if request:
                    self.selected_request = request
                    self._display_request_details(request)

    def _display_request_details(self, request):
        """Display detailed information for selected request."""
        # Headers
        headers_text = json.dumps(request.headers, indent=2)
        self.headers_text.setPlainText(headers_text)

        # Query parameters
        query_text = json.dumps(request.query_params, indent=2)
        self.query_text.setPlainText(query_text)

        # Body
        body_text = request.body
        # Try to format JSON body
        if body_text.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(body_text)
                body_text = json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                pass  # Keep original text
        self.body_text.setPlainText(body_text)

        # Raw data
        raw_data = {
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
        }
        self.raw_text.setPlainText(json.dumps(raw_data, indent=2))

    def _clear_request_details(self):
        """Clear request details display."""
        self.headers_text.clear()
        self.query_text.clear()
        self.body_text.clear()
        self.raw_text.clear()
        self.selected_request = None

    def _export_data(self, format_type: str):
        """Export data in specified format."""
        from .api_inspector import DataExporter

        exporter = DataExporter(self.storage)

        # Get export data
        if format_type == "json":
            data = exporter.export_json(self.current_filters)
            file_filter = "JSON Files (*.json)"
            default_name = f"api_inspector_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:  # csv
            data = exporter.export_csv(self.current_filters)
            file_filter = "CSV Files (*.csv)"
            default_name = f"api_inspector_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Show save dialog
        filename, _ = QFileDialog.getSaveFileName(self, f"Export {format_type.upper()}", default_name, file_filter)

        if filename:
            if exporter.save_export(data, filename):
                QMessageBox.information(self, "Export Successful", f"Data exported to {filename}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to save export file.")

    def _send_to_scratch_pad(self):
        """Send selected request data to scratch pad."""
        if not self.scratch_pad_widget or not self.selected_request:
            return

        # Format request data for scratch pad
        request = self.selected_request
        scratch_text = f"""API Inspector - Captured Request
=====================================

Timestamp: {request.timestamp.isoformat()}
Method: {request.method}
URL: {request.url}
Client IP: {request.client_ip}
Content Length: {request.content_length}
User Agent: {request.user_agent}

Headers:
{json.dumps(request.headers, indent=2)}

Query Parameters:
{json.dumps(request.query_params, indent=2)}

Body:
{request.body}

Request ID: {request.request_id}
"""

        # Send to scratch pad
        try:
            if hasattr(self.scratch_pad_widget, "append_text"):
                self.scratch_pad_widget.append_text(scratch_text)
            elif hasattr(self.scratch_pad_widget, "text_edit"):
                current_text = self.scratch_pad_widget.text_edit.toPlainText()
                new_text = current_text + "\n\n" + scratch_text if current_text else scratch_text
                self.scratch_pad_widget.text_edit.setPlainText(new_text)

        except Exception:
            logger.exception("Failed to send to scratch pad")
            QMessageBox.warning(self, "Error", "Failed to send data to Scratch Pad")

    @pyqtSlot(int)
    def _on_server_started(self, port: int):
        """Handle server started signal."""
        self.status_label.setText("Server Status: Running")
        self.status_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.start_stop_btn.setText("Stop Server")
        self.url_label.setText(f"URL: http://localhost:{port}")
        self.port_input.setEnabled(False)
        logger.info("Server started on port %s", port)

    @pyqtSlot()
    def _on_server_stopped(self):
        """Handle server stopped signal."""
        self.status_label.setText("Server Status: Stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        self.start_stop_btn.setText("Start Server")
        self.url_label.setText("")
        self.port_input.setEnabled(True)
        logger.info("Server stopped")

    @pyqtSlot(str)
    def _on_server_error(self, error_msg: str):
        """Handle server error signal."""
        self.status_label.setText("Server Status: Error")
        self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        self.start_stop_btn.setText("Start Server")
        self.url_label.setText("")
        self.port_input.setEnabled(True)

        QMessageBox.critical(self, "Server Error", f"Server error: {error_msg}")
        logger.error("Server error: %s", error_msg)
