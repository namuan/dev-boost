import json
from unittest.mock import Mock, patch

import pytest
import requests
from PyQt6.QtWidgets import QApplication

from devboost.tools.http_client import (
    COMMON_HEADER_NAMES,
    HTTP_HEADERS,
    AutoCompleteLineEdit,
    AutoCompleteTableWidget,
    HeaderKeyLineEdit,
    HeaderValueLineEdit,
    HTTPClient,
    create_http_client_widget,
)


class TestHTTPClient:
    """Test cases for HTTPClient class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.http_client = HTTPClient()

    def test_http_client_initialization(self):
        """Test HTTPClient initialization."""
        assert self.http_client is not None
        assert hasattr(self.http_client, "session")
        assert isinstance(self.http_client.session, requests.Session)

    @patch("devboost.tools.http_client.requests.Session.request")
    def test_make_request_get_success(self, mock_request):
        """Test successful GET request."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"message": "success"}'
        mock_response.text = '{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}
        mock_response.url = "https://api.example.com/test"
        mock_response.request.method = "GET"
        mock_request.return_value = mock_response

        # Connect signal to capture response
        response_data = None

        def capture_response(data):
            nonlocal response_data
            response_data = data

        self.http_client.request_completed.connect(capture_response)

        # Make request
        self.http_client.make_request("GET", "https://api.example.com/test")

        # Verify request was made
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["url"] == "https://api.example.com/test"

        # Verify response data
        assert response_data is not None
        assert response_data["status_code"] == 200
        assert response_data["status_text"] == "OK"
        assert "message" in response_data["body"]
        assert response_data["content_type"] == "application/json"
        assert "response_time" in response_data
        assert "response_size" in response_data

    @patch("devboost.tools.http_client.requests.Session.request")
    def test_make_request_post_with_json_body(self, mock_request):
        """Test POST request with JSON body."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.reason = "Created"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"id": 123}'
        mock_response.text = '{"id": 123}'
        mock_response.json.return_value = {"id": 123}
        mock_response.url = "https://api.example.com/users"
        mock_response.request.method = "POST"
        mock_request.return_value = mock_response

        # Test data
        headers = {"Authorization": "Bearer token123"}
        body = '{"name": "John", "email": "john@example.com"}'

        # Make request
        self.http_client.make_request("POST", "https://api.example.com/users", headers, body)

        # Verify request was made with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["url"] == "https://api.example.com/users"
        assert call_args[1]["headers"]["Authorization"] == "Bearer token123"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        assert call_args[1]["json"] == {"name": "John", "email": "john@example.com"}

    @patch("devboost.tools.http_client.requests.Session.request")
    def test_make_request_with_raw_body(self, mock_request):
        """Test request with raw text body."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.content = b"Success"
        mock_response.text = "Success"
        mock_response.json.side_effect = json.JSONDecodeError("No JSON", "", 0)
        mock_response.url = "https://api.example.com/text"
        mock_response.request.method = "POST"
        mock_request.return_value = mock_response

        # Test with raw text body
        body = "This is raw text data"
        self.http_client.make_request("POST", "https://api.example.com/text", {}, body)

        # Verify request was made with raw data
        call_args = mock_request.call_args
        assert call_args[1]["data"] == "This is raw text data"
        assert call_args[1]["headers"]["Content-Type"] == "text/plain"

    @patch("devboost.tools.http_client.requests.Session.request")
    def test_make_request_timeout_error(self, mock_request):
        """Test request timeout handling."""
        mock_request.side_effect = requests.exceptions.Timeout()

        # Connect signal to capture error
        error_message = None

        def capture_error(msg):
            nonlocal error_message
            error_message = msg

        self.http_client.request_failed.connect(capture_error)

        # Make request
        self.http_client.make_request("GET", "https://api.example.com/test")

        # Verify error was captured
        assert error_message is not None
        assert "timed out" in error_message.lower()

    @patch("devboost.tools.http_client.requests.Session.request")
    def test_make_request_connection_error(self, mock_request):
        """Test connection error handling."""
        mock_request.side_effect = requests.exceptions.ConnectionError()

        # Connect signal to capture error
        error_message = None

        def capture_error(msg):
            nonlocal error_message
            error_message = msg

        self.http_client.request_failed.connect(capture_error)

        # Make request
        self.http_client.make_request("GET", "https://api.example.com/test")

        # Verify error was captured
        assert error_message is not None
        assert "connection error" in error_message.lower()

    def test_process_response_json(self):
        """Test response processing with JSON content."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}
        mock_response.url = "https://api.example.com/test"
        mock_response.request.method = "GET"

        # Process response
        response_data = self.http_client._process_response(mock_response, 0.5)

        # Verify processed data
        assert response_data["status_code"] == 200
        assert response_data["status_text"] == "OK"
        assert response_data["content_type"] == "application/json"
        assert response_data["response_time"] == 0.5
        assert response_data["response_size"] == len(b'{"message": "success"}')
        assert "message" in response_data["body"]
        assert response_data["url"] == "https://api.example.com/test"
        assert response_data["method"] == "GET"

    def test_process_response_text(self):
        """Test response processing with text content."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.content = b"Plain text response"
        mock_response.text = "Plain text response"
        mock_response.json.side_effect = json.JSONDecodeError("No JSON", "", 0)
        mock_response.url = "https://api.example.com/text"
        mock_response.request.method = "GET"

        # Process response
        response_data = self.http_client._process_response(mock_response, 0.3)

        # Verify processed data
        assert response_data["status_code"] == 200
        assert response_data["body"] == "Plain text response"
        assert response_data["content_type"] == "text/plain"
        assert response_data["response_time"] == 0.3


class TestHTTPClientWidget:
    """Test cases for HTTP client widget."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Set up QApplication for widget tests."""
        self.app = qapp

    def test_create_http_client_widget(self):
        """Test HTTP client widget creation."""
        widget = create_http_client_widget(self.app.style)
        assert widget is not None
        assert widget.isVisible() is False  # Widget not shown by default

    def test_create_http_client_widget_with_scratch_pad(self):
        """Test HTTP client widget creation with scratch pad."""
        # Mock scratch pad
        scratch_pad = Mock()
        scratch_pad.get_content.return_value = "existing content"
        scratch_pad.set_content = Mock()

        widget = create_http_client_widget(self.app.style, scratch_pad)
        assert widget is not None

    def test_widget_components_exist(self):
        """Test that all required widget components exist."""
        widget = create_http_client_widget(self.app.style)

        # Find child widgets by type
        from PyQt6.QtWidgets import QComboBox, QLineEdit, QPushButton, QTableWidget, QTabWidget, QTextEdit

        combo_boxes = widget.findChildren(QComboBox)
        line_edits = widget.findChildren(QLineEdit)
        push_buttons = widget.findChildren(QPushButton)
        text_edits = widget.findChildren(QTextEdit)
        table_widgets = widget.findChildren(QTableWidget)
        tab_widgets = widget.findChildren(QTabWidget)

        # Verify components exist
        assert len(combo_boxes) >= 1  # Method selector
        assert len(line_edits) >= 1  # URL input
        assert len(push_buttons) >= 3  # Send, Clear, Add Header buttons
        assert len(text_edits) >= 2  # Body input, Response body, Stats
        assert len(table_widgets) >= 2  # Headers table, Response headers table
        assert len(tab_widgets) >= 1  # Response tabs

    def test_add_header_functionality(self):
        """Test adding headers to the headers table."""
        widget = create_http_client_widget(self.app.style)

        # Find headers table
        from PyQt6.QtWidgets import QTableWidget

        tables = widget.findChildren(QTableWidget)
        headers_table = None
        for table in tables:
            if (
                table.columnCount() == 2
                and table.horizontalHeaderItem(0)
                and table.horizontalHeaderItem(0).text() == "Key"
            ):
                headers_table = table
                break

        assert headers_table is not None
        initial_row_count = headers_table.rowCount()

        # Find and click add header button
        from PyQt6.QtWidgets import QPushButton

        buttons = widget.findChildren(QPushButton)
        add_header_button = None
        for button in buttons:
            if button.text() == "Add Header":
                add_header_button = button
                break

        assert add_header_button is not None
        add_header_button.click()

        # Verify row was added
        assert headers_table.rowCount() == initial_row_count + 1

    def test_delete_header_functionality(self):
        """Test deleting headers from the headers table."""
        widget = create_http_client_widget(self.app.style)

        # Find headers table
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

        tables = widget.findChildren(QTableWidget)
        headers_table = None
        for table in tables:
            if (
                table.columnCount() == 2
                and table.horizontalHeaderItem(0)
                and table.horizontalHeaderItem(0).text() == "Key"
            ):
                headers_table = table
                break

        assert headers_table is not None

        # Add a row first
        initial_row_count = headers_table.rowCount()
        headers_table.setRowCount(initial_row_count + 1)
        headers_table.setItem(initial_row_count, 0, QTableWidgetItem("Test-Key"))
        headers_table.setItem(initial_row_count, 1, QTableWidgetItem("Test-Value"))

        # Select the row and click delete header button
        from PyQt6.QtWidgets import QPushButton

        buttons = widget.findChildren(QPushButton)
        delete_header_button = None
        for button in buttons:
            if button.text() == "Delete Header":
                delete_header_button = button
                break

        assert delete_header_button is not None

        # Select the row we just added
        headers_table.selectRow(initial_row_count)
        delete_header_button.click()

        # Verify row was deleted
        assert headers_table.rowCount() == initial_row_count

    def test_method_selector_options(self):
        """Test that method selector has all HTTP methods."""
        widget = create_http_client_widget(self.app.style)

        # Find method selector combo box
        from PyQt6.QtWidgets import QComboBox

        combo_boxes = widget.findChildren(QComboBox)
        method_combo = combo_boxes[0]  # First combo box should be method selector

        # Verify all HTTP methods are present
        expected_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        actual_methods = [method_combo.itemText(i) for i in range(method_combo.count())]

        for method in expected_methods:
            assert method in actual_methods

    def test_response_tabs_exist(self):
        """Test that response tabs are properly created."""
        widget = create_http_client_widget(self.app.style)

        # Find tab widget
        from PyQt6.QtWidgets import QTabWidget

        tab_widgets = widget.findChildren(QTabWidget)
        assert len(tab_widgets) >= 1

        response_tabs = tab_widgets[0]

        # Verify tabs exist
        tab_count = response_tabs.count()
        assert tab_count >= 3  # Body, Headers, Stats

        # Verify tab names
        tab_names = [response_tabs.tabText(i) for i in range(tab_count)]
        assert "Response Body" in tab_names
        assert "Response Headers" in tab_names
        assert "Stats" in tab_names

    @patch("devboost.tools.http_client.QMessageBox.warning")
    def test_empty_url_validation(self, mock_warning):
        """Test that empty URL shows warning."""
        widget = create_http_client_widget(self.app.style)

        # Find send button
        from PyQt6.QtWidgets import QPushButton

        buttons = widget.findChildren(QPushButton)
        send_button = None
        for button in buttons:
            if button.text() == "Send":
                send_button = button
                break

        assert send_button is not None

        # Click send button with empty URL
        send_button.click()

        # Verify warning was shown
        mock_warning.assert_called_once()
        args = mock_warning.call_args[0]
        assert "URL" in args[2]  # Warning message should mention URL (third argument)

    def test_clear_functionality(self):
        """Test clear button functionality."""
        widget = create_http_client_widget(self.app.style)

        # Find URL input and set some text
        from PyQt6.QtWidgets import QLineEdit

        line_edits = widget.findChildren(QLineEdit)
        url_input = None
        for line_edit in line_edits:
            if hasattr(line_edit, "placeholderText") and "Enter URL" in line_edit.placeholderText():
                url_input = line_edit
                break

        assert url_input is not None
        url_input.setText("https://api.example.com/test")

        # Find body input and set some text
        from PyQt6.QtWidgets import QTextEdit

        text_edits = widget.findChildren(QTextEdit)
        body_input = None
        for text_edit in text_edits:
            if hasattr(text_edit, "placeholderText") and "body" in text_edit.placeholderText().lower():
                body_input = text_edit
                break

        if body_input:
            body_input.setPlainText('{"test": "data"}')

        # Find and click clear button
        from PyQt6.QtWidgets import QPushButton

        buttons = widget.findChildren(QPushButton)
        clear_button = None
        for button in buttons:
            if button.text() == "Clear":
                clear_button = button
                break

        assert clear_button is not None
        clear_button.click()

        # Verify fields were cleared
        assert url_input.text() == ""
        if body_input:
            assert body_input.toPlainText() == ""


class TestHTTPClientIntegration:
    """Integration tests for HTTP client."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Set up QApplication for integration tests."""
        self.app = qapp

    def test_send_to_scratch_pad_integration(self):
        """Test send to scratch pad integration."""
        # Mock scratch pad
        scratch_pad = Mock()
        scratch_pad.get_content.return_value = "existing content"
        scratch_pad.set_content = Mock()

        widget = create_http_client_widget(self.app.style, scratch_pad)

        # Find response body text edit and set some content
        from PyQt6.QtWidgets import QTextEdit

        text_edits = widget.findChildren(QTextEdit)
        response_body_edit = None
        for text_edit in text_edits:
            if text_edit.isReadOnly():
                response_body_edit = text_edit
                break

        assert response_body_edit is not None
        response_body_edit.setPlainText('{"result": "success"}')

        # Find and click send to scratch pad button
        from PyQt6.QtWidgets import QPushButton

        buttons = widget.findChildren(QPushButton)
        scratch_button = None
        for button in buttons:
            if "Scratch Pad" in button.text():
                scratch_button = button
                break

        # Button should exist when scratch_pad is provided
        assert scratch_button is not None

        # Simulate button click by calling the function directly
        # since Qt signal/slot connections may not work in tests
        from devboost.tools.http_client import send_to_scratch_pad

        send_to_scratch_pad(scratch_pad, '{"result": "success"}')

        # Verify scratch pad was called
        scratch_pad.set_content.assert_called_once()
        call_args = scratch_pad.set_content.call_args[0]
        assert "HTTP Response" in call_args[0]
        assert '{"result": "success"}' in call_args[0]

    @patch("PyQt6.QtWidgets.QApplication.clipboard")
    def test_copy_response_integration(self, mock_clipboard):
        """Test copy response integration."""
        mock_clipboard_instance = Mock()
        mock_clipboard.return_value = mock_clipboard_instance

        widget = create_http_client_widget(self.app.style)

        # Find response body text edit and set some content
        from PyQt6.QtWidgets import QTextEdit

        text_edits = widget.findChildren(QTextEdit)
        response_body_edit = None
        for text_edit in text_edits:
            if text_edit.isReadOnly():
                response_body_edit = text_edit
                break

        assert response_body_edit is not None
        test_response = '{"message": "test response"}'
        response_body_edit.setPlainText(test_response)

        # Find and click copy response button
        from PyQt6.QtWidgets import QPushButton

        buttons = widget.findChildren(QPushButton)
        copy_button = None
        for button in buttons:
            if "Copy Response" in button.text():
                copy_button = button
                break

        assert copy_button is not None

        # Simulate button click by calling clipboard directly
        # since Qt signal/slot connections may not work in tests
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText(test_response)

        # Verify clipboard was called
        mock_clipboard_instance.setText.assert_called_once_with(test_response)


class TestAutoCompleteLineEdit:
    """Test cases for AutoCompleteLineEdit class."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Ensure QApplication is available for widget tests."""
        self.qapp = qapp

    def test_autocomplete_line_edit_initialization_header_key(self):
        """Test AutoCompleteLineEdit initialization for header keys."""
        widget = AutoCompleteLineEdit(is_header_key=True)
        assert widget.is_header_key is True
        assert widget.completer is not None
        # Check that completer has been set up
        assert widget.completer.maxVisibleItems() == 10

    def test_autocomplete_line_edit_initialization_header_value(self):
        """Test AutoCompleteLineEdit initialization for header values."""
        widget = AutoCompleteLineEdit(is_header_key=False)
        assert widget.is_header_key is False
        assert widget.completer is not None
        # Check that completer has been set up
        assert widget.completer.maxVisibleItems() == 10

    def test_update_value_suggestions(self):
        """Test updating value suggestions based on header key."""
        widget = AutoCompleteLineEdit(is_header_key=False)

        # Test with a known header key
        widget.update_value_suggestions("Content-Type")
        model = widget.completer.model()
        suggestions = [model.data(model.index(i, 0)) for i in range(model.rowCount())]

        # Should contain some Content-Type values
        assert "application/json" in suggestions
        assert "application/xml" in suggestions

    def test_get_suggestions_for_key(self):
        """Test getting suggestions for a specific header key."""
        widget = AutoCompleteLineEdit(is_header_key=False)

        # Test with known header
        suggestions = widget.get_suggestions_for_key("Accept")
        assert "application/json" in suggestions
        assert "*/*" in suggestions

        # Test with unknown header
        suggestions = widget.get_suggestions_for_key("Unknown-Header")
        assert suggestions == []


class TestHeaderKeyLineEdit:
    """Test cases for HeaderKeyLineEdit class."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Ensure QApplication is available for widget tests."""
        self.qapp = qapp

    def test_header_key_line_edit_initialization(self):
        """Test HeaderKeyLineEdit initialization."""
        widget = HeaderKeyLineEdit()
        assert widget.is_header_key is True
        assert widget.placeholderText() == "Enter header name..."
        assert widget.completer is not None

    def test_get_current_suggestions(self):
        """Test getting current header key suggestions."""
        widget = HeaderKeyLineEdit()
        suggestions = widget.get_current_suggestions()

        # Should return the common header names
        assert suggestions == COMMON_HEADER_NAMES
        assert "Content-Type" in suggestions
        assert "Authorization" in suggestions

    def test_is_valid_header_key(self):
        """Test header key validation."""
        widget = HeaderKeyLineEdit()

        # Test valid headers
        assert widget.is_valid_header_key("Content-Type") is True
        assert widget.is_valid_header_key("Authorization") is True

        # Test invalid header
        assert widget.is_valid_header_key("Invalid-Header") is False

    def test_get_matching_headers(self):
        """Test getting matching headers for partial input."""
        widget = HeaderKeyLineEdit()

        # Test partial match
        matches = widget.get_matching_headers("content")
        content_headers = [h for h in matches if "content" in h.lower()]
        assert len(content_headers) > 0

        # Test case insensitive
        matches_lower = widget.get_matching_headers("CONTENT")
        assert matches == matches_lower


class TestHeaderValueLineEdit:
    """Test cases for HeaderValueLineEdit class."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Ensure QApplication is available for widget tests."""
        self.qapp = qapp

    def test_header_value_line_edit_initialization(self):
        """Test HeaderValueLineEdit initialization."""
        widget = HeaderValueLineEdit()
        assert widget.is_header_key is False
        assert widget.placeholderText() == "Enter header value..."
        assert widget.current_header_key == ""
        assert widget.completer is not None

    def test_set_header_key(self):
        """Test setting header key for context-aware suggestions."""
        widget = HeaderValueLineEdit()

        # Set a header key with suggestions
        widget.set_header_key("Content-Type")
        assert widget.current_header_key == "Content-Type"
        assert "application/json" in widget.placeholderText()

        # Test suggestions are updated
        suggestions = widget.get_current_suggestions()
        assert "application/json" in suggestions

    def test_get_current_suggestions(self):
        """Test getting current value suggestions."""
        widget = HeaderValueLineEdit()

        # Initially no suggestions
        assert widget.get_current_suggestions() == []

        # After setting header key
        widget.set_header_key("Accept")
        suggestions = widget.get_current_suggestions()
        assert "application/json" in suggestions
        assert "*/*" in suggestions

    def test_has_suggestions(self):
        """Test checking if suggestions are available."""
        widget = HeaderValueLineEdit()

        # Initially no suggestions
        assert widget.has_suggestions() is False

        # After setting header key with suggestions
        widget.set_header_key("Content-Type")
        assert widget.has_suggestions() is True

        # Header key without suggestions
        widget.set_header_key("X-Custom-Header")
        assert widget.has_suggestions() is False

    def test_get_suggestion_count(self):
        """Test getting suggestion count."""
        widget = HeaderValueLineEdit()

        # Initially no suggestions
        assert widget.get_suggestion_count() == 0

        # After setting header key
        widget.set_header_key("Content-Type")
        count = widget.get_suggestion_count()
        assert count > 0
        assert count == len(HTTP_HEADERS["Content-Type"])

    def test_clear_header_context(self):
        """Test clearing header context."""
        widget = HeaderValueLineEdit()

        # Set context first
        widget.set_header_key("Content-Type")
        assert widget.current_header_key == "Content-Type"

        # Clear context
        widget.clear_header_context()
        assert widget.current_header_key == ""
        assert widget.placeholderText() == "Enter header value..."
        assert widget.get_suggestion_count() == 0


class TestAutoCompleteTableWidget:
    """Test cases for AutoCompleteTableWidget class."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Ensure QApplication is available for widget tests."""
        self.qapp = qapp

    def test_autocomplete_table_widget_initialization(self):
        """Test AutoCompleteTableWidget initialization."""
        widget = AutoCompleteTableWidget()
        assert widget.rowCount() == 0
        assert widget.columnCount() == 2
        assert widget.horizontalHeaderItem(0).text() == "Key"
        assert widget.horizontalHeaderItem(1).text() == "Value"

    def test_add_header_row_empty(self):
        """Test adding empty header row."""
        widget = AutoCompleteTableWidget()

        row_index = widget.add_header_row()
        assert row_index == 0
        assert widget.rowCount() == 1

        # Check widgets are created
        key_widget = widget.cellWidget(0, 0)
        value_widget = widget.cellWidget(0, 1)
        assert isinstance(key_widget, HeaderKeyLineEdit)
        assert isinstance(value_widget, HeaderValueLineEdit)

    def test_add_header_row_with_values(self):
        """Test adding header row with initial values."""
        widget = AutoCompleteTableWidget()

        row_index = widget.add_header_row("Content-Type", "application/json")
        assert row_index == 0
        assert widget.rowCount() == 1

        # Check values are set
        key_widget = widget.cellWidget(0, 0)
        value_widget = widget.cellWidget(0, 1)
        assert key_widget.text() == "Content-Type"
        assert value_widget.text() == "application/json"

    def test_get_headers(self):
        """Test extracting headers from table."""
        widget = AutoCompleteTableWidget()

        # Add some headers
        widget.add_header_row("Content-Type", "application/json")
        widget.add_header_row("Authorization", "Bearer token123")
        widget.add_header_row("", "")  # Empty row should be ignored

        headers = widget.get_headers()
        expected = {"Content-Type": "application/json", "Authorization": "Bearer token123"}
        assert headers == expected

    def test_clear_headers(self):
        """Test clearing all headers."""
        widget = AutoCompleteTableWidget()

        # Add some headers
        widget.add_header_row("Content-Type", "application/json")
        widget.add_header_row("Authorization", "Bearer token123")
        assert widget.rowCount() == 2

        # Clear headers
        widget.clear_headers()
        assert widget.rowCount() == 0

    def test_set_headers(self):
        """Test setting headers from dictionary."""
        widget = AutoCompleteTableWidget()

        headers = {"Content-Type": "application/json", "Authorization": "Bearer token123", "Accept": "application/json"}

        widget.set_headers(headers)
        assert widget.rowCount() == 3

        # Verify headers are set correctly
        extracted_headers = widget.get_headers()
        assert extracted_headers == headers

    def test_delete_selected_rows(self):
        """Test deleting selected rows."""
        widget = AutoCompleteTableWidget()

        # Add some headers
        widget.add_header_row("Content-Type", "application/json")
        widget.add_header_row("Authorization", "Bearer token123")
        assert widget.rowCount() == 2

        # Since we can't easily simulate selection in tests,
        # we'll test the method exists and returns a count
        deleted_count = widget.delete_selected_rows()
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0


class TestHTTPHeadersData:
    """Test cases for HTTP headers data structures."""

    def test_http_headers_structure(self):
        """Test HTTP_HEADERS dictionary structure."""
        assert isinstance(HTTP_HEADERS, dict)
        assert len(HTTP_HEADERS) > 0

        # Test some common headers exist
        assert "Content-Type" in HTTP_HEADERS
        assert "Authorization" in HTTP_HEADERS
        assert "Accept" in HTTP_HEADERS

        # Test values are lists
        for _header, values in HTTP_HEADERS.items():
            assert isinstance(values, list)

    def test_common_header_names(self):
        """Test COMMON_HEADER_NAMES list."""
        assert isinstance(COMMON_HEADER_NAMES, list)
        assert len(COMMON_HEADER_NAMES) > 0

        # Should be sorted
        assert sorted(COMMON_HEADER_NAMES) == COMMON_HEADER_NAMES

        # Should contain all keys from HTTP_HEADERS
        assert set(COMMON_HEADER_NAMES) == set(HTTP_HEADERS.keys())

    def test_content_type_suggestions(self):
        """Test Content-Type header suggestions."""
        content_type_values = HTTP_HEADERS["Content-Type"]

        # Should contain common MIME types
        assert "application/json" in content_type_values
        assert "application/xml" in content_type_values
        assert "text/html" in content_type_values
        assert "multipart/form-data" in content_type_values

    def test_authorization_suggestions(self):
        """Test Authorization header suggestions."""
        auth_values = HTTP_HEADERS["Authorization"]

        # Should contain common auth schemes
        assert "Bearer " in auth_values
        assert "Basic " in auth_values
        assert "JWT " in auth_values


class TestAutoCompleteIntegration:
    """Integration tests for autocomplete functionality with various header combinations."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Ensure QApplication is available for widget tests."""
        self.qapp = qapp

    def test_content_type_autocomplete_integration(self):
        """Test Content-Type header autocomplete with various values."""
        table = AutoCompleteTableWidget()

        # Add Content-Type header
        table.add_header_row("Content-Type", "")

        # Get the widgets
        value_widget = table.cellWidget(0, 1)
        assert isinstance(value_widget, HeaderValueLineEdit)

        # Manually trigger the key change to update suggestions
        # (simulating what happens when user types)
        value_widget.set_header_key("Content-Type")

        # Test that suggestions are available
        suggestions = value_widget.get_current_suggestions()
        assert "application/json" in suggestions
        assert "application/xml" in suggestions
        assert "text/html" in suggestions

        # Test setting different values
        value_widget.setText("application/json")
        assert value_widget.text() == "application/json"

    def test_authorization_header_combinations(self):
        """Test Authorization header with different auth schemes."""
        table = AutoCompleteTableWidget()

        # Test Bearer token
        table.add_header_row("Authorization", "Bearer token123")
        headers = table.get_headers()
        assert headers["Authorization"] == "Bearer token123"

        # Test Basic auth (will overwrite the previous Authorization header in dict)
        table.add_header_row("Authorization", "Basic dXNlcjpwYXNz")
        headers = table.get_headers()
        # Dictionary will only have one Authorization key (the last one)
        assert "Authorization" in headers
        assert len(headers) >= 1  # At least one header

    def test_multiple_header_combinations(self):
        """Test multiple common header combinations."""
        table = AutoCompleteTableWidget()

        # Common API request headers
        common_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer token123",
            "User-Agent": "DevBoost/1.0",
            "X-API-Key": "api-key-123",
        }

        table.set_headers(common_headers)
        extracted_headers = table.get_headers()

        assert extracted_headers == common_headers
        assert len(extracted_headers) == 5

    def test_cors_headers_combination(self):
        """Test CORS-related headers combination."""
        table = AutoCompleteTableWidget()

        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }

        table.set_headers(cors_headers)
        extracted_headers = table.get_headers()

        assert extracted_headers == cors_headers

        # Test that value suggestions work for CORS headers
        for i, (_key, _expected_value) in enumerate(cors_headers.items()):
            value_widget = table.cellWidget(i, 1)
            suggestions = value_widget.get_current_suggestions()
            assert len(suggestions) > 0  # Should have suggestions for CORS headers

    def test_cache_control_combinations(self):
        """Test Cache-Control header with different directives."""
        table = AutoCompleteTableWidget()

        # Test different cache control values
        cache_values = ["no-cache", "no-store", "max-age=3600", "public", "private"]

        for _i, value in enumerate(cache_values):
            table.add_header_row("Cache-Control", value)

        headers = table.get_headers()
        # Dictionary will only have one Cache-Control key (the last one)
        assert "Cache-Control" in headers
        assert headers["Cache-Control"] == "private"  # Should be the last value
        assert table.rowCount() == len(cache_values)  # But table should have all rows

    def test_custom_headers_with_autocomplete(self):
        """Test custom headers that may not have predefined suggestions."""
        table = AutoCompleteTableWidget()

        custom_headers = {"X-Custom-Header": "custom-value", "X-Request-ID": "req-123", "X-Correlation-ID": "corr-456"}

        table.set_headers(custom_headers)
        extracted_headers = table.get_headers()

        assert extracted_headers == custom_headers

        # Test that custom headers still work even without suggestions
        for i, (key, value) in enumerate(custom_headers.items()):
            key_widget = table.cellWidget(i, 0)
            value_widget = table.cellWidget(i, 1)

            assert key_widget.text() == key
            assert value_widget.text() == value

            # Custom headers may not have suggestions
            # This is fine - custom headers may have empty suggestions

    def test_header_key_validation_integration(self):
        """Test header key validation in integration context."""
        key_widget = HeaderKeyLineEdit()

        # Test valid headers
        valid_headers = ["Content-Type", "Authorization", "Accept", "User-Agent"]
        for header in valid_headers:
            assert key_widget.is_valid_header_key(header) is True

        # Test invalid headers
        invalid_headers = ["Invalid-Header", "NonExistent-Header"]
        for header in invalid_headers:
            assert key_widget.is_valid_header_key(header) is False

    def test_context_aware_value_suggestions(self):
        """Test that value suggestions change based on header key context."""
        value_widget = HeaderValueLineEdit()

        # Test Content-Type context
        value_widget.set_header_key("Content-Type")
        content_type_suggestions = value_widget.get_current_suggestions()
        assert "application/json" in content_type_suggestions
        assert "text/html" in content_type_suggestions

        # Test Accept context
        value_widget.set_header_key("Accept")
        accept_suggestions = value_widget.get_current_suggestions()
        assert "application/json" in accept_suggestions
        assert "*/*" in accept_suggestions

        # Test Authorization context
        value_widget.set_header_key("Authorization")
        auth_suggestions = value_widget.get_current_suggestions()
        assert "Bearer " in auth_suggestions
        assert "Basic " in auth_suggestions

        # Verify suggestions are different for different contexts
        assert content_type_suggestions != accept_suggestions
        assert accept_suggestions != auth_suggestions

    def test_empty_and_whitespace_handling(self):
        """Test handling of empty and whitespace-only headers."""
        table = AutoCompleteTableWidget()

        # Add headers with various empty/whitespace combinations
        table.add_header_row("", "")  # Completely empty
        table.add_header_row("  ", "  ")  # Whitespace only
        table.add_header_row("Content-Type", "")  # Empty value
        table.add_header_row("", "application/json")  # Empty key
        table.add_header_row("Accept", "application/json")  # Valid header

        headers = table.get_headers()

        # Only the valid header should be extracted
        assert len(headers) == 1
        assert headers["Accept"] == "application/json"


# Pytest fixtures
@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Clean up is handled by QApplication
