"""
Tests for the insight UI components that display agent reasoning and confidence.

These tests verify that agent reasoning and confidence metrics are properly
displayed in the Streamlit UI.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.ui.insight_components import (
    display_agent_reasoning,
    display_confidence_metric,
    display_explanation_markdown,
    display_expanded_insight
)


class TestAgentReasoningComponents:
    """Test class for the agent reasoning UI components."""

    @patch("streamlit.container")
    @patch("streamlit.expander")
    def test_display_agent_reasoning(self, mock_expander, mock_container):
        """Test that agent reasoning is displayed correctly."""
        # Setup
        mock_expander_instance = MagicMock()
        mock_expander.return_value.__enter__.return_value = mock_expander_instance
        reasoning = "The price dropped 15% over the last week, indicating a downward trend."
        
        # Execute
        display_agent_reasoning("Analysis", reasoning)
        
        # Assert
        mock_expander.assert_called_once()
        mock_expander_instance.markdown.assert_called_once()
        # Check that the reasoning is in the markdown content
        assert reasoning in mock_expander_instance.markdown.call_args[0][0]

    @patch("streamlit.metric")
    def test_display_confidence_metric_high(self, mock_metric):
        """Test that high confidence is displayed with correct color."""
        # Execute
        display_confidence_metric(0.85)
        
        # Assert
        mock_metric.assert_called_once()
        args, kwargs = mock_metric.call_args
        assert "85%" in args[1]  # The value should be formatted as 85%
        assert kwargs.get("delta_color") == "normal"  # High confidence should be green/normal

    @patch("streamlit.metric")
    def test_display_confidence_metric_low(self, mock_metric):
        """Test that low confidence is displayed with correct color."""
        # Execute
        display_confidence_metric(0.35)
        
        # Assert
        mock_metric.assert_called_once()
        args, kwargs = mock_metric.call_args
        assert "35%" in args[1]  # The value should be formatted as 35%
        assert kwargs.get("delta_color") == "inverse"  # Low confidence should be red/inverse

    @patch("streamlit.markdown")
    def test_display_explanation_markdown(self, mock_markdown):
        """Test that explanations are formatted as markdown with highlighting."""
        # Setup
        explanation = "Price dropped 15% in 7 days"
        
        # Execute
        display_explanation_markdown(explanation)
        
        # Assert
        mock_markdown.assert_called_once()
        # Verify markdown contains the explanation
        assert explanation in mock_markdown.call_args[0][0]
        # Verify styling is applied
        assert "style=" in mock_markdown.call_args[0][0]
        assert "unsafe_allow_html=True" in str(mock_markdown.call_args)

    @patch("streamlit.json")
    @patch("streamlit.expander")
    def test_display_expanded_insight(self, mock_expander, mock_json):
        """Test that expanded insights are displayed in JSON format."""
        # Setup
        mock_expander_instance = MagicMock()
        mock_expander.return_value.__enter__.return_value = mock_expander_instance
        insight_data = {
            "trend": "decreasing",
            "analysis": "Price is dropping",
            "statistics": {"avg_price": 100, "min_price": 90}
        }
        
        # Execute
        display_expanded_insight(insight_data)
        
        # Assert
        mock_expander.assert_called_once()
        mock_expander_instance.json.assert_called_once_with(insight_data)
