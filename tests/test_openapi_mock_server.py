import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from devboost.tools.openapi_mock_server import (
    MockServerHandler,
    MockServerThread,
    OpenAPIParser,
    create_openapi_mock_server_widget,
)


class TestOpenAPIParser:
    """Test cases for OpenAPIParser class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.parser = OpenAPIParser()

    def test_openapi_parser_initialization(self):
        """Test OpenAPIParser initialization."""
        assert self.parser is not None
        assert hasattr(self.parser, "spec")
        assert self.parser.spec is None

    def test_parse_valid_openapi_spec(self):
        """Test parsing a valid OpenAPI specification."""
        valid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                                            },
                                        }
                                    }
                                },
                            }
                        }
                    }
                }
            },
        }

        result = self.parser.parse_spec(valid_spec)
        assert result is True
        assert self.parser.spec == valid_spec

    def test_parse_invalid_openapi_spec(self):
        """Test parsing an invalid OpenAPI specification."""
        invalid_spec = {"invalid": "spec"}

        result = self.parser.parse_spec(invalid_spec)
        assert result is False
        assert self.parser.spec is None

    def test_get_endpoints_empty_spec(self):
        """Test getting endpoints from empty specification."""
        endpoints = self.parser.get_endpoints()
        assert endpoints == []

    def test_get_endpoints_valid_spec(self):
        """Test getting endpoints from valid specification."""
        valid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {"responses": {"200": {"description": "Success"}}},
                    "post": {"responses": {"201": {"description": "Created"}}},
                },
                "/users/{id}": {"get": {"responses": {"200": {"description": "Success"}}}},
            },
        }

        self.parser.parse_spec(valid_spec)
        endpoints = self.parser.get_endpoints()

        assert len(endpoints) == 3
        assert ("GET", "/users") in endpoints
        assert ("POST", "/users") in endpoints
        assert ("GET", "/users/{id}") in endpoints

    def test_generate_mock_response_simple_object(self):
        """Test generating mock response for simple object schema."""
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"}, "active": {"type": "boolean"}},
        }

        response = self.parser.generate_mock_response(schema)

        assert isinstance(response, dict)
        assert "id" in response
        assert "name" in response
        assert "active" in response
        assert isinstance(response["id"], int)
        assert isinstance(response["name"], str)
        assert isinstance(response["active"], bool)

    def test_generate_mock_response_array(self):
        """Test generating mock response for array schema."""
        schema = {
            "type": "array",
            "items": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}},
        }

        response = self.parser.generate_mock_response(schema)

        assert isinstance(response, list)
        assert len(response) >= 1
        assert len(response) <= 5
        for item in response:
            assert isinstance(item, dict)
            assert "id" in item
            assert "name" in item

    def test_generate_mock_response_primitive_types(self):
        """Test generating mock responses for primitive types."""
        # String
        string_response = self.parser.generate_mock_response({"type": "string"})
        assert isinstance(string_response, str)

        # Integer
        int_response = self.parser.generate_mock_response({"type": "integer"})
        assert isinstance(int_response, int)

        # Number
        number_response = self.parser.generate_mock_response({"type": "number"})
        assert isinstance(number_response, int | float)

        # Boolean
        bool_response = self.parser.generate_mock_response({"type": "boolean"})
        assert isinstance(bool_response, bool)


class TestMockServerHandler:
    """Test cases for MockServerHandler class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.parser = OpenAPIParser()
        self.handler = MockServerHandler(self.parser)

    def test_mock_server_handler_initialization(self):
        """Test MockServerHandler initialization."""
        assert self.handler is not None
        assert self.handler.parser == self.parser
        assert hasattr(self.handler, "enable_cors")
        assert hasattr(self.handler, "latency_min")
        assert hasattr(self.handler, "latency_max")

    @patch("http.server.BaseHTTPRequestHandler.end_headers")
    @patch("http.server.BaseHTTPRequestHandler.send_header")
    @patch("http.server.BaseHTTPRequestHandler.send_response")
    def test_cors_headers(self, mock_send_response, mock_send_header, mock_end_headers):
        """Test CORS headers are sent when enabled."""
        self.handler.enable_cors = True
        self.handler.wfile = Mock()

        # Mock the path and method
        self.handler.path = "/test"
        self.handler.command = "GET"

        # Call the method that should send CORS headers
        self.handler.do_OPTIONS()

        # Verify CORS headers were sent
        mock_send_response.assert_called_with(200)
        mock_send_header.assert_any_call("Access-Control-Allow-Origin", "*")
        mock_send_header.assert_any_call("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        mock_send_header.assert_any_call("Access-Control-Allow-Headers", "Content-Type, Authorization")


class TestMockServerThread:
    """Test cases for MockServerThread class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.parser = OpenAPIParser()
        self.thread = MockServerThread(self.parser, port=0)  # Use port 0 for automatic assignment

    def test_mock_server_thread_initialization(self):
        """Test MockServerThread initialization."""
        assert self.thread is not None
        assert self.thread.parser == self.parser
        assert self.thread.port == 0
        assert hasattr(self.thread, "server")
        assert hasattr(self.thread, "server_started")
        assert hasattr(self.thread, "server_stopped")
        assert hasattr(self.thread, "server_error")

    def test_thread_signals_exist(self):
        """Test that required signals exist."""
        assert hasattr(self.thread, "server_started")
        assert hasattr(self.thread, "server_stopped")
        assert hasattr(self.thread, "server_error")


class TestCreateOpenAPIMockServerWidget:
    """Test cases for create_openapi_mock_server_widget function."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Ensure QApplication is available for widget tests."""
        self.qapp = qapp

    def test_create_widget_returns_widget(self):
        """Test that create_openapi_mock_server_widget returns a widget."""
        style = Mock()
        scratch_pad = Mock()

        widget = create_openapi_mock_server_widget(style, scratch_pad)

        assert widget is not None
        assert hasattr(widget, "show")  # Basic widget property

    def test_create_widget_with_none_parameters(self):
        """Test widget creation with None parameters."""
        widget = create_openapi_mock_server_widget(None, None)

        assert widget is not None

    @patch("devboost.tools.openapi_mock_server.QFileDialog")
    def test_widget_file_upload_functionality(self, mock_file_dialog):
        """Test file upload functionality in the widget."""
        # Create a temporary OpenAPI spec file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}, f)
            temp_file = f.name

        try:
            mock_file_dialog.getOpenFileName.return_value = (temp_file, "JSON files (*.json)")

            style = Mock()
            scratch_pad = Mock()
            widget = create_openapi_mock_server_widget(style, scratch_pad)

            # The widget should be created successfully
            assert widget is not None

        finally:
            # Clean up
            Path(temp_file).unlink(missing_ok=True)


class TestIntegration:
    """Integration tests for the OpenAPI Mock Server tool."""

    @pytest.fixture(autouse=True)
    def setup_qapp(self, qapp):
        """Ensure QApplication is available for integration tests."""
        self.qapp = qapp

    def test_full_workflow_with_valid_spec(self):
        """Test the complete workflow with a valid OpenAPI specification."""
        # Create parser and parse a valid spec
        parser = OpenAPIParser()
        valid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object", "properties": {"message": {"type": "string"}}}
                                    }
                                },
                            }
                        }
                    }
                }
            },
        }

        # Parse the specification
        assert parser.parse_spec(valid_spec) is True

        # Get endpoints
        endpoints = parser.get_endpoints()
        assert len(endpoints) == 1
        assert ("GET", "/test") in endpoints

        # Generate mock response
        schema = valid_spec["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        response = parser.generate_mock_response(schema)
        assert isinstance(response, dict)
        assert "message" in response
        assert isinstance(response["message"], str)

    def test_widget_creation_and_basic_functionality(self):
        """Test widget creation and basic functionality."""
        style = Mock()
        scratch_pad = Mock()

        # Create the widget
        widget = create_openapi_mock_server_widget(style, scratch_pad)
        assert widget is not None

        # Widget should be showable
        widget.show()

        # Process events to ensure widget is properly initialized
        QTimer.singleShot(100, self.qapp.quit)
        self.qapp.exec()


@pytest.fixture
def qapp():
    """Provide a QApplication instance for tests that need it."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app here as it might be used by other tests
