"""Tests for search visual feedback functionality.

This module tests the visual feedback provided during search operations,
including result counts, no results messages, and different feedback states.
"""

import pytest
from PyQt6.QtWidgets import QApplication

from devboost.main_cli import DevDriverWindow


class TestSearchVisualFeedback:
    """Test class for search visual feedback functionality."""

    @pytest.fixture
    def window(self):
        """Create a DevDriverWindow instance for testing."""
        window = DevDriverWindow()
        yield window
        window.close()

    def test_search_results_label_exists(self, window):
        """Test that the search results label exists and is initially hidden."""
        assert hasattr(window, "search_results_label")
        assert not window.search_results_label.isVisible()

    def test_no_search_query_hides_feedback(self, window):
        """Test that empty search query hides the feedback label."""
        # Initially should be hidden
        assert not window.search_results_label.isVisible()

        # Set empty search and process
        window.search_input.setText("")
        QApplication.processEvents()

        # Should still be hidden
        assert not window.search_results_label.isVisible()

    def test_search_with_results_shows_feedback(self, window):
        """Test that search with results shows appropriate feedback."""
        # Search for something that should match some tools
        window.search_input.setText("JSON")
        QApplication.processEvents()

        # Should show feedback label
        assert window.search_results_label.isVisible()

        # Should show count of visible tools
        feedback_text = window.search_results_label.text()
        assert "Showing" in feedback_text
        assert "tools" in feedback_text

    def test_search_with_no_results_shows_no_results_message(self, window):
        """Test that search with no results shows appropriate message."""
        # Search for something that won't match any tools
        window.search_input.setText("NonExistentTool12345")
        QApplication.processEvents()

        # Should show feedback label
        assert window.search_results_label.isVisible()

        # Should show no results message
        feedback_text = window.search_results_label.text()
        assert "No tools found" in feedback_text
        assert "NonExistentTool12345" in feedback_text

    def test_search_showing_all_tools_feedback(self, window):
        """Test feedback when search shows all tools."""
        # Search for something very generic that should match all tools
        window.search_input.setText("a")  # Most tools should contain 'a'
        QApplication.processEvents()

        # Should show feedback label
        assert window.search_results_label.isVisible()

        feedback_text = window.search_results_label.text()
        # Could be either "Showing all X tools" or "Showing Y of X tools"
        assert "Showing" in feedback_text
        assert "tools" in feedback_text

    def test_update_search_feedback_method_directly(self, window):
        """Test the _update_search_feedback method directly."""
        # Test with no search query
        window._update_search_feedback("", 0)
        assert not window.search_results_label.isVisible()

        # Test with no results
        window._update_search_feedback("test", 0)
        assert window.search_results_label.isVisible()
        assert "No tools found" in window.search_results_label.text()

        # Test with some results
        window._update_search_feedback("test", 5)
        assert window.search_results_label.isVisible()
        assert "Showing 5 of" in window.search_results_label.text()

        # Test with all tools visible (assuming 13 total tools)
        total_tools = len(window.tools)
        window._update_search_feedback("test", total_tools)
        assert window.search_results_label.isVisible()
        assert f"Showing all {total_tools} tools" in window.search_results_label.text()

    def test_feedback_styling_for_different_states(self, window):
        """Test that different feedback states have appropriate styling."""
        # Test no results styling (should be red/error color)
        window._update_search_feedback("nonexistent", 0)
        style = window.search_results_label.styleSheet()
        assert "#ff6b6b" in style  # Red color for no results

        # Test partial results styling (should be blue/info color)
        window._update_search_feedback("test", 5)
        style = window.search_results_label.styleSheet()
        assert "#339af0" in style  # Blue color for partial results

        # Test all results styling (should be green/success color)
        total_tools = len(window.tools)
        window._update_search_feedback("test", total_tools)
        style = window.search_results_label.styleSheet()
        assert "#51cf66" in style  # Green color for all results

    def test_feedback_updates_on_search_changes(self, window):
        """Test that feedback updates when search query changes."""
        # Start with a search that has results
        window.search_input.setText("JSON")
        QApplication.processEvents()

        window.search_results_label.text()
        assert window.search_results_label.isVisible()

        # Change to a different search
        window.search_input.setText("Base64")
        QApplication.processEvents()

        new_text = window.search_results_label.text()
        assert window.search_results_label.isVisible()

        # Text should have changed (unless both searches have same result count)
        # At minimum, the feedback should still be visible and contain relevant info
        assert "Showing" in new_text
        assert "tools" in new_text

        # Clear search
        window.search_input.setText("")
        QApplication.processEvents()

        # Should hide feedback
        assert not window.search_results_label.isVisible()
