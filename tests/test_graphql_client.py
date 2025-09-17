from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from devboost.tools.graphql_client import (
    COMMON_GRAPHQL_QUERIES,
    GraphQLClient,
    GraphQLWorkerThread,
    create_graphql_client_widget,
)


class TestGraphQLClient:
    """Test cases for GraphQLClient class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.graphql_client = GraphQLClient()

    def test_graphql_client_initialization(self):
        """Test GraphQLClient initialization."""
        assert self.graphql_client is not None
        assert hasattr(self.graphql_client, "request_queue")
        assert hasattr(self.graphql_client, "active_workers")
        assert len(self.graphql_client.request_queue) == 0
        assert len(self.graphql_client.active_workers) == 0
        assert self.graphql_client.max_concurrent_requests == 3
        assert self.graphql_client._request_id_counter == 0

    @patch("devboost.tools.graphql_client.GraphQLWorkerThread")
    def test_make_request_success(self, mock_worker_class):
        """Test successful GraphQL request."""
        # Mock worker instance
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker

        # Connect signal to capture response
        response_data = None
        started = False

        def capture_response(data):
            nonlocal response_data
            response_data = data

        def capture_started():
            nonlocal started
            started = True

        self.graphql_client.request_completed.connect(capture_response)
        self.graphql_client.request_started.connect(capture_started)

        # Make request
        url = "https://api.example.com/graphql"
        query = "query { user { id name } }"
        variables = {"id": "123"}
        headers = {"Authorization": "Bearer token"}

        request_id = self.graphql_client.make_request(url, query, variables, headers)

        # Verify request was queued and worker created
        assert request_id.startswith("gql_req_")
        assert len(self.graphql_client.active_workers) == 1
        assert request_id in self.graphql_client.active_workers

        # Verify worker was created with correct parameters
        mock_worker_class.assert_called_once_with(url, query, variables, headers, 30)
        mock_worker.start.assert_called_once()

        # Simulate successful response
        mock_response_data = {
            "status_code": 200,
            "status_text": "OK",
            "graphql_data": {"user": {"id": "123", "name": "Test User"}},
            "graphql_errors": [],
            "response_time": 0.5,
        }

        # Trigger the completion handler
        self.graphql_client._handle_request_completed(request_id, mock_response_data)

        # Verify response was captured
        assert response_data is not None
        assert response_data["request_id"] == request_id
        assert response_data["status_code"] == 200
        assert response_data["graphql_data"]["user"]["name"] == "Test User"

    @patch("devboost.tools.graphql_client.GraphQLWorkerThread")
    def test_make_request_with_minimal_params(self, mock_worker_class):
        """Test GraphQL request with minimal parameters."""
        # Mock worker instance
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker

        url = "https://api.example.com/graphql"
        query = "query { __typename }"

        request_id = self.graphql_client.make_request(url, query)

        assert request_id.startswith("gql_req_")
        # Request should be processed immediately and moved to active workers
        assert len(self.graphql_client.active_workers) == 1
        assert request_id in self.graphql_client.active_workers

        # Verify worker was created with correct parameters (None for optional params)
        mock_worker_class.assert_called_once_with(url, query, None, None, 30)

    def test_cancel_request_specific(self):
        """Test cancelling a specific GraphQL request."""
        # Create mock worker
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True

        # Add to active workers
        request_id = "gql_req_1"
        self.graphql_client.active_workers[request_id] = mock_worker

        # Cancel specific request
        result = self.graphql_client.cancel_request(request_id)

        assert result is True
        mock_worker.cancel.assert_called_once()

    def test_cancel_all_requests(self):
        """Test cancelling all GraphQL requests."""
        # Create mock workers
        mock_worker1 = Mock()
        mock_worker1.isRunning.return_value = True
        mock_worker2 = Mock()
        mock_worker2.isRunning.return_value = True

        # Add to active workers and queue
        self.graphql_client.active_workers["gql_req_1"] = mock_worker1
        self.graphql_client.active_workers["gql_req_2"] = mock_worker2
        self.graphql_client.request_queue = [{"id": "gql_req_3"}]

        # Cancel all requests
        result = self.graphql_client.cancel_request()

        assert result is True
        mock_worker1.cancel.assert_called_once()
        mock_worker2.cancel.assert_called_once()
        assert len(self.graphql_client.request_queue) == 0

    def test_get_active_request_count(self):
        """Test getting active request count."""
        assert self.graphql_client.get_active_request_count() == 0

        # Add mock workers
        self.graphql_client.active_workers["gql_req_1"] = Mock()
        self.graphql_client.active_workers["gql_req_2"] = Mock()

        assert self.graphql_client.get_active_request_count() == 2

    def test_get_queued_request_count(self):
        """Test getting queued request count."""
        assert self.graphql_client.get_queued_request_count() == 0

        # Add requests to queue
        self.graphql_client.request_queue = [{"id": "gql_req_1"}, {"id": "gql_req_2"}]

        assert self.graphql_client.get_queued_request_count() == 2

    def test_get_active_request_ids(self):
        """Test getting active request IDs."""
        assert self.graphql_client.get_active_request_ids() == []

        # Add mock workers
        self.graphql_client.active_workers["gql_req_1"] = Mock()
        self.graphql_client.active_workers["gql_req_2"] = Mock()

        request_ids = self.graphql_client.get_active_request_ids()
        assert "gql_req_1" in request_ids
        assert "gql_req_2" in request_ids
        assert len(request_ids) == 2

    def test_is_request_active(self):
        """Test checking if request is active."""
        request_id = "gql_req_1"
        assert self.graphql_client.is_request_active(request_id) is False

        # Add mock worker
        self.graphql_client.active_workers[request_id] = Mock()
        assert self.graphql_client.is_request_active(request_id) is True


class TestGraphQLWorkerThread:
    """Test cases for GraphQLWorkerThread class."""

    def test_worker_thread_initialization(self):
        """Test GraphQLWorkerThread initialization."""
        url = "https://api.example.com/graphql"
        query = "query { user { id } }"
        variables = {"id": "123"}
        headers = {"Authorization": "Bearer token"}
        timeout = 60

        worker = GraphQLWorkerThread(url, query, variables, headers, timeout)

        assert worker.url == url
        assert worker.query == query
        assert worker.variables == variables
        assert worker.headers == headers
        assert worker.timeout == timeout
        assert worker._cancelled is False

    def test_worker_thread_initialization_with_defaults(self):
        """Test GraphQLWorkerThread initialization with default values."""
        url = "https://api.example.com/graphql"
        query = "query { __typename }"

        worker = GraphQLWorkerThread(url, query)

        assert worker.url == url
        assert worker.query == query
        assert worker.variables == {}
        assert worker.headers == {}
        assert worker.timeout == 30

    def test_worker_thread_cancel(self):
        """Test GraphQLWorkerThread cancellation."""
        worker = GraphQLWorkerThread("https://api.example.com/graphql", "query { __typename }")

        assert worker._cancelled is False
        worker.cancel()
        assert worker._cancelled is True

    @patch("devboost.tools.graphql_client.requests.Session")
    def test_process_graphql_response_success(self, mock_session_class):
        """Test processing successful GraphQL response."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"data": {"user": {"id": "123"}}}'
        mock_response.url = "https://api.example.com/graphql"
        mock_response.json.return_value = {"data": {"user": {"id": "123"}}, "errors": []}

        worker = GraphQLWorkerThread("https://api.example.com/graphql", "query { user { id } }")
        response_data = worker._process_graphql_response(mock_response, 0.5)

        assert response_data["status_code"] == 200
        assert response_data["status_text"] == "OK"
        assert response_data["method"] == "POST"
        assert response_data["response_time"] == 0.5
        assert response_data["graphql_data"] == {"user": {"id": "123"}}
        assert response_data["graphql_errors"] == []

    @patch("devboost.tools.graphql_client.requests.Session")
    def test_process_graphql_response_with_errors(self, mock_session_class):
        """Test processing GraphQL response with errors."""
        # Mock response with GraphQL errors
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"errors": [{"message": "Field not found"}]}'
        mock_response.url = "https://api.example.com/graphql"
        mock_response.json.return_value = {"data": None, "errors": [{"message": "Field not found", "path": ["user"]}]}

        worker = GraphQLWorkerThread("https://api.example.com/graphql", "query { user { invalid } }")
        response_data = worker._process_graphql_response(mock_response, 0.3)

        assert response_data["status_code"] == 200
        assert response_data["graphql_data"] is None
        assert len(response_data["graphql_errors"]) == 1
        assert response_data["graphql_errors"][0]["message"] == "Field not found"


class TestGraphQLQueries:
    """Test cases for GraphQL query templates."""

    def test_common_graphql_queries_exist(self):
        """Test that common GraphQL query templates exist."""
        assert "introspection" in COMMON_GRAPHQL_QUERIES
        assert "simple_query" in COMMON_GRAPHQL_QUERIES
        assert "simple_mutation" in COMMON_GRAPHQL_QUERIES
        assert "simple_subscription" in COMMON_GRAPHQL_QUERIES

    def test_introspection_query_content(self):
        """Test that introspection query contains expected content."""
        introspection = COMMON_GRAPHQL_QUERIES["introspection"]
        assert "__schema" in introspection
        assert "queryType" in introspection
        assert "mutationType" in introspection
        assert "subscriptionType" in introspection
        assert "FullType" in introspection

    def test_simple_query_template(self):
        """Test simple query template."""
        simple_query = COMMON_GRAPHQL_QUERIES["simple_query"]
        assert "query {" in simple_query
        assert "# Add your query fields here" in simple_query

    def test_simple_mutation_template(self):
        """Test simple mutation template."""
        simple_mutation = COMMON_GRAPHQL_QUERIES["simple_mutation"]
        assert "mutation {" in simple_mutation
        assert "# Add your mutation fields here" in simple_mutation

    def test_simple_subscription_template(self):
        """Test simple subscription template."""
        simple_subscription = COMMON_GRAPHQL_QUERIES["simple_subscription"]
        assert "subscription {" in simple_subscription
        assert "# Add your subscription fields here" in simple_subscription


@pytest.fixture
def qapp():
    """Create QApplication instance for widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestGraphQLClientWidget:
    """Test cases for GraphQL client widget creation."""

    def test_create_graphql_client_widget(self, qapp):
        """Test GraphQL client widget creation."""

        # Mock style function
        def mock_style_func():
            return Mock()

        # Create widget
        widget = create_graphql_client_widget(mock_style_func)

        assert widget is not None
        assert hasattr(widget, "layout")

    def test_create_graphql_client_widget_with_scratch_pad(self, qapp):
        """Test GraphQL client widget creation with scratch pad."""

        # Mock style function and scratch pad
        def mock_style_func():
            return Mock()

        mock_scratch_pad = Mock()
        mock_scratch_pad.get_content.return_value = ""
        mock_scratch_pad.set_content = Mock()

        # Create widget with scratch pad
        widget = create_graphql_client_widget(mock_style_func, mock_scratch_pad)

        assert widget is not None
        assert hasattr(widget, "layout")


class TestGraphQLClientIntegration:
    """Integration test cases for GraphQL client."""

    def test_send_to_scratch_pad_function(self):
        """Test send_to_scratch_pad function."""
        from devboost.tools.graphql_client import send_to_scratch_pad

        # Mock scratch pad
        mock_scratch_pad = Mock()
        mock_scratch_pad.get_content.return_value = "existing content"

        # Test sending content
        content = '{"data": {"user": {"id": "123"}}}'
        send_to_scratch_pad(mock_scratch_pad, content)

        # Verify scratch pad was updated
        mock_scratch_pad.set_content.assert_called_once()
        call_args = mock_scratch_pad.set_content.call_args[0][0]
        assert "--- GraphQL Response ---" in call_args
        assert content in call_args

    def test_send_to_scratch_pad_empty_content(self):
        """Test send_to_scratch_pad with empty content."""
        from devboost.tools.graphql_client import send_to_scratch_pad

        # Mock scratch pad
        mock_scratch_pad = Mock()

        # Test sending empty content
        send_to_scratch_pad(mock_scratch_pad, "")

        # Verify scratch pad was not updated
        mock_scratch_pad.set_content.assert_not_called()

    def test_send_to_scratch_pad_no_scratch_pad(self):
        """Test send_to_scratch_pad with no scratch pad."""
        from devboost.tools.graphql_client import send_to_scratch_pad

        # Test with None scratch pad - should not raise exception
        send_to_scratch_pad(None, "some content")
        # No assertion needed, just verify no exception is raised
