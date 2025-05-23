"""
Tests for UI insights section handling.

This module tests the handling of different data types in the insights_section
function to ensure proper error handling and type checking.
"""
import unittest
from unittest.mock import patch, MagicMock

import streamlit as st

# Mock streamlit
st.empty = MagicMock(return_value=MagicMock())
st.error = MagicMock()
st.warning = MagicMock()
st.checkbox = MagicMock(return_value=False)


class TestInsightsHandling(unittest.TestCase):
    """Test suite for UI insights section handling."""

    @patch("app.ui.pages.home.AnalysisAgentAdapter")
    @patch("app.ui.pages.home.RecommendationAgentAdapter")
    @patch("app.ui.pages.home.display_ai_insights")
    def test_insights_section_with_string_analysis(self, mock_display, mock_rec_adapter, mock_analysis_adapter):
        """Test insights_section properly handles string analysis results."""
        from app.ui.pages.home import insights_section
        
        # Setup
        mock_analysis_instance = MagicMock()
        mock_analysis_adapter.return_value = mock_analysis_instance
        # Return string instead of dict to simulate the error
        mock_analysis_instance.analyze_prices.return_value = "Analysis as a string"
        
        mock_rec_instance = MagicMock()
        mock_rec_adapter.return_value = mock_rec_instance
        mock_rec_instance.execute.return_value = {"recommendation": "Test recommendation"}
        
        # Execute
        results = [{"price": 999.99, "store": "Test Store"}]
        insights_section("Test Model", results)
        
        # Assert display was called with correct parameters
        mock_display.assert_called_once()
        # We don't expect an error to be raised
        st.error.assert_not_called()

    @patch("app.ui.pages.home.AnalysisAgentAdapter")
    @patch("app.ui.pages.home.RecommendationAgentAdapter")
    @patch("app.ui.pages.home.display_ai_insights")
    def test_insights_section_with_dict_analysis(self, mock_display, mock_rec_adapter, mock_analysis_adapter):
        """Test insights_section properly handles dictionary analysis results."""
        from app.ui.pages.home import insights_section
        
        # Setup
        mock_analysis_instance = MagicMock()
        mock_analysis_adapter.return_value = mock_analysis_instance
        # Return a dictionary as expected
        mock_analysis_instance.analyze_prices.return_value = {"average_price": 999.99, "price_trend": "stable"}
        
        mock_rec_instance = MagicMock()
        mock_rec_adapter.return_value = mock_rec_instance
        mock_rec_instance.execute.return_value = {"recommendation": "Test recommendation"}
        
        # Execute
        results = [{"price": 999.99, "store": "Test Store"}]
        insights_section("Test Model", results)
        
        # Assert display was called with correct parameters
        mock_display.assert_called_once()
        # We don't expect an error to be raised
        st.error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
