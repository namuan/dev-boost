from unittest.mock import patch

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from devboost.main_cli import DevDriverWindow


class TestSearchInputConnection:
    """Test cases for search input text change event connection."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        return QApplication.instance() or QApplication([])

    @pytest.fixture
    def window(self, app):
        """Create DevDriverWindow instance for testing."""
        return DevDriverWindow()

    def test_search_input_exists(self, window):
        """Test that search input widget is created and accessible."""
        assert hasattr(window, "search_input")
        assert window.search_input is not None
        assert window.search_input.placeholderText() == "Search...   ⌘⇧F"
        assert window.search_input.height() == 38

    def test_text_changed_signal_connected(self, window):
        """Test that textChanged signal is connected to on_search_text_changed method."""
        # Patch the on_search_text_changed method after window creation
        with patch.object(window, "on_search_text_changed") as mock_handler:
            # Simulate typing in the search input
            test_text = "json"
            window.search_input.setText(test_text)

            # Process events to ensure signal is emitted
            QApplication.processEvents()

            # Verify that on_search_text_changed was called with the text
            mock_handler.assert_called_with(test_text)

    def test_multiple_text_changes(self, window):
        """Test that multiple text changes trigger multiple handler calls."""
        # Patch the on_search_text_changed method after window creation
        with patch.object(window, "on_search_text_changed") as mock_handler:
            test_texts = ["j", "js", "jso", "json"]

            for text in test_texts:
                window.search_input.setText(text)
                QApplication.processEvents()

            # Verify that on_search_text_changed was called for each text change
            assert mock_handler.call_count == len(test_texts)

            # Verify the calls were made with the correct arguments
            expected_calls = [((text,),) for text in test_texts]
            actual_calls = [call.args for call in mock_handler.call_args_list]
            assert actual_calls == expected_calls

    def test_clear_text_triggers_filter(self, window):
        """Test that clearing text triggers handler with empty string."""
        # Patch the on_search_text_changed method after window creation
        with patch.object(window, "on_search_text_changed") as mock_handler:
            # Set some text first
            window.search_input.setText("test")
            QApplication.processEvents()

            # Clear the text
            window.search_input.clear()
            QApplication.processEvents()

            # Verify that on_search_text_changed was called with empty string
            mock_handler.assert_called_with("")

    def test_real_time_filtering_integration(self, window):
        """Test real-time filtering integration with debouncing."""
        # Get initial tool count
        initial_count = window.tool_list.count()

        # Type a search query that should filter results
        window.search_input.setText("json")
        QApplication.processEvents()

        # Wait for debounce timer to trigger
        QTimer.singleShot(350, lambda: None)  # Wait longer than debounce delay
        QApplication.processEvents()

        # Process events again to ensure timer callback is executed
        import time

        time.sleep(0.4)  # Wait for debounce delay
        QApplication.processEvents()

        # Verify that the tool list has been filtered
        filtered_count = window.tool_list.count()
        assert filtered_count < initial_count
        assert filtered_count > 0  # Should find some JSON-related tools

        # Clear the search to show all tools again
        window.search_input.clear()
        QApplication.processEvents()

        # Wait for debounce timer again
        time.sleep(0.4)
        QApplication.processEvents()

        # Verify that all tools are shown again
        final_count = window.tool_list.count()
        assert final_count == initial_count

    def test_case_insensitive_real_time_filtering(self, window):
        """Test that real-time filtering is case-insensitive."""
        test_cases = ["JSON", "json", "Json", "jSoN"]

        for query in test_cases:
            window.search_input.setText(query)
            QApplication.processEvents()

            # All cases should return the same number of results
            count = window.tool_list.count()
            assert count > 0  # Should find JSON-related tools

            # Store first result for comparison
            if query == test_cases[0]:
                expected_count = count
            else:
                assert count == expected_count

    def test_partial_match_real_time_filtering(self, window):
        """Test that real-time filtering supports partial matches."""
        # Test progressive typing
        progressive_queries = ["j", "js", "jso", "json"]

        for query in progressive_queries:
            window.search_input.setText(query)
            QApplication.processEvents()

            # Each query should return some results
            count = window.tool_list.count()
            assert count >= 0  # May be 0 for very short queries

            # "json" should definitely return results
            if query == "json":
                assert count > 0
