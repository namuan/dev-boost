import time
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from devboost.main_cli import DevDriverWindow


class TestSearchDebouncing:
    """Test cases for search input debouncing functionality."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance for testing."""
        return QApplication.instance() or QApplication([])

    @pytest.fixture
    def window(self, app):
        """Create DevDriverWindow instance for testing."""
        return DevDriverWindow()

    def test_debounce_timer_exists(self, window):
        """Test that debounce timer is created and configured properly."""
        assert hasattr(window, "search_debounce_timer")
        assert isinstance(window.search_debounce_timer, QTimer)
        assert window.search_debounce_timer.isSingleShot()

    def test_on_search_text_changed_method_exists(self, window):
        """Test that on_search_text_changed method exists."""
        assert hasattr(window, "on_search_text_changed")
        assert callable(window.on_search_text_changed)

    def test_debounced_search_functionality(self, window):
        """Test that debounced search works correctly."""
        # Mock the filter_tools method to track calls
        with patch.object(window, "filter_tools") as mock_filter:
            # Simulate rapid typing
            window.on_search_text_changed("j")
            window.on_search_text_changed("js")
            window.on_search_text_changed("jso")
            window.on_search_text_changed("json")

            # Process events but don't wait for timer
            QApplication.processEvents()

            # Should not have called filter_tools yet due to debouncing
            assert mock_filter.call_count == 0

            # Wait for debounce delay and process events
            time.sleep(0.35)  # Wait longer than 300ms debounce
            QApplication.processEvents()

            # Now filter_tools should have been called once with the last text
            assert mock_filter.call_count == 1
            mock_filter.assert_called_with("json")

    def test_search_text_storage(self, window):
        """Test that current search text is stored correctly."""
        test_text = "test search"
        window.on_search_text_changed(test_text)

        assert hasattr(window, "current_search_text")
        assert window.current_search_text == test_text

    def test_timer_restart_on_new_input(self, window):
        """Test that timer restarts when new input is received."""
        with (
            patch.object(window.search_debounce_timer, "stop") as mock_stop,
            patch.object(window.search_debounce_timer, "start") as mock_start,
        ):
            window.on_search_text_changed("test")

            # Timer should be stopped and restarted
            mock_stop.assert_called_once()
            mock_start.assert_called_once_with(300)

    def test_perform_search_method(self, window):
        """Test the _perform_search method directly."""
        with patch.object(window, "filter_tools") as mock_filter:
            # Set up current search text
            window.current_search_text = "test query"

            # Call _perform_search directly
            window._perform_search()

            # Should call filter_tools with the stored text
            mock_filter.assert_called_once_with("test query")

    def test_perform_search_without_current_text(self, window):
        """Test _perform_search when no current_search_text is set."""
        with patch.object(window, "filter_tools") as mock_filter:
            # Ensure no current_search_text attribute
            if hasattr(window, "current_search_text"):
                delattr(window, "current_search_text")

            # Call _perform_search
            window._perform_search()

            # Should not call filter_tools
            mock_filter.assert_not_called()

    def test_real_time_filtering_integration(self, window):
        """Test that real-time filtering works when user types in search input."""
        with patch.object(window, "filter_tools") as mock_filter:
            # Simulate typing in the search input field
            window.search_input.setText("json")

            # Process events but don't wait for timer
            QApplication.processEvents()

            # Should not have called filter_tools yet due to debouncing
            assert mock_filter.call_count == 0

            # Wait for debounce delay and process events
            time.sleep(0.35)  # Wait longer than 300ms debounce
            QApplication.processEvents()

            # Now filter_tools should have been called with the search text
            assert mock_filter.call_count == 1
            mock_filter.assert_called_with("json")

            # Test clearing the search
            mock_filter.reset_mock()
            window.search_input.clear()

            # Process events and wait for debounce
            QApplication.processEvents()
            time.sleep(0.35)
            QApplication.processEvents()

            # Should call filter_tools with empty string
            assert mock_filter.call_count == 1
            mock_filter.assert_called_with("")
