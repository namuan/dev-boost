from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QApplication, QListWidget

from devboost.main_cli import DevDriverWindow


class TestSearchFiltering:
    """Test cases for search filtering functionality."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        return QApplication.instance() or QApplication([])

    @pytest.fixture
    def window(self, app):
        """Create DevDriverWindow instance for testing."""
        return DevDriverWindow()

    def test_filter_tools_empty_query(self, window):
        """Test that empty query shows all tools."""
        # Mock the tool_list to avoid GUI operations
        window.tool_list = Mock(spec=QListWidget)

        # Test empty string
        window.filter_tools("")

        # Should clear and repopulate with all tools
        window.tool_list.clear.assert_called_once()
        assert window.tool_list.addItem.call_count == len(window.tools)

    def test_filter_tools_whitespace_query(self, window):
        """Test that whitespace-only query shows all tools."""
        window.tool_list = Mock(spec=QListWidget)

        # Test whitespace string
        window.filter_tools("   ")

        # Should clear and repopulate with all tools
        window.tool_list.clear.assert_called_once()
        assert window.tool_list.addItem.call_count == len(window.tools)

    def test_filter_tools_by_name(self, window):
        """Test filtering by tool name."""
        window.tool_list = Mock(spec=QListWidget)

        # Test filtering by "JSON" - should find 3 tools: JSON Format/Validate, JWT Debugger, YAML to JSON
        window.filter_tools("JSON")

        # Should find 3 tools containing "json"
        window.tool_list.clear.assert_called_once()
        assert window.tool_list.addItem.call_count == 3

    def test_filter_tools_by_keywords(self, window):
        """Test filtering by keywords/descriptions."""
        window.tool_list = Mock(spec=QListWidget)

        # Test filtering by "regex" keyword
        window.filter_tools("regex")

        # Should find RegExp Tester tool
        window.tool_list.clear.assert_called_once()
        assert window.tool_list.addItem.call_count == 1

    def test_filter_tools_case_insensitive(self, window):
        """Test that filtering is case-insensitive."""
        window.tool_list = Mock(spec=QListWidget)

        # Test with different cases
        test_cases = ["json", "JSON", "Json", "jSoN"]

        for query in test_cases:
            window.tool_list.reset_mock()
            window.filter_tools(query)

            # Should find 3 tools containing "json" regardless of case
            window.tool_list.clear.assert_called_once()
            assert window.tool_list.addItem.call_count == 3

    def test_filter_tools_partial_match(self, window):
        """Test partial matching in tool names and keywords."""
        window.tool_list = Mock(spec=QListWidget)

        # Test partial match in name
        window.filter_tools("Time")
        window.tool_list.clear.assert_called_once()
        assert window.tool_list.addItem.call_count == 1  # Unix Time Converter

        # Reset mock
        window.tool_list.reset_mock()

        # Test partial match in keywords
        window.filter_tools("encode")
        window.tool_list.clear.assert_called_once()
        # Should find Base64 and URL tools
        assert window.tool_list.addItem.call_count == 2

    def test_filter_tools_no_matches(self, window):
        """Test filtering with query that matches no tools."""
        window.tool_list = Mock(spec=QListWidget)

        # Test with query that shouldn't match anything
        window.filter_tools("nonexistent")

        # Should clear but add no items
        window.tool_list.clear.assert_called_once()
        assert window.tool_list.addItem.call_count == 0

    def test_filter_tools_multiple_matches(self, window):
        """Test filtering that returns multiple matches."""
        window.tool_list = Mock(spec=QListWidget)

        # Test with "convert" which should match multiple tools
        window.filter_tools("convert")

        # Should find multiple converter tools
        window.tool_list.clear.assert_called_once()
        assert window.tool_list.addItem.call_count > 1

    @patch("devboost.main_cli.logger")
    def test_filter_tools_logging(self, mock_logger, window):
        """Test that filtering operations are properly logged."""
        window.tool_list = Mock(spec=QListWidget)

        # Test filtering
        window.filter_tools("test")

        # Should log the filtering operation
        mock_logger.info.assert_any_call("Filtering tools with query: 'test'")
        # Should log the results
        assert any("Filtered tools:" in str(call) for call in mock_logger.info.call_args_list)
