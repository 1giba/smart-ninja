"""
Integration tests for the agent reasoning and confidence display in the UI.

These tests verify that agent data is properly integrated with the UI components.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.ui.insight_components import display_agent_insights


class TestAgentInsightIntegration:
    """Test class for integration of agent insights with UI components."""

    @patch("app.ui.insight_components.display_agent_reasoning")
    @patch("app.ui.insight_components.display_confidence_metric")
    @patch("app.ui.insight_components.display_explanation_markdown")
    @patch("app.ui.insight_components.display_expanded_insight")
    def test_analysis_agent_insights_display(
        self,
        mock_display_expanded_insight,
        mock_display_explanation_markdown,
        mock_display_confidence_metric,
        mock_display_agent_reasoning,
    ):
        """Test displaying analysis agent insights."""
        # Setup
        agent_data = {
            "analysis": "Prices have been decreasing steadily over the past month.",
            "reasoning": "Based on historical price data, we detected a 15% drop in 30 days.",
            "explanation": "Price dropped 15% in 30 days",
            "confidence": 0.87,
            "detailed_data": {
                "trend": "decreasing",
                "statistics": {
                    "avg_price": 950.25,
                    "min_price": 899.99,
                    "max_price": 1029.99,
                    "price_std_dev": 45.67
                }
            }
        }
        
        # Execute
        display_agent_insights("Analysis", agent_data)
        
        # Assert
        mock_display_agent_reasoning.assert_called_once_with(
            "Analysis", agent_data["reasoning"]
        )
        mock_display_confidence_metric.assert_called_once_with(
            agent_data["confidence"]
        )
        mock_display_explanation_markdown.assert_called_once_with(
            agent_data["explanation"]
        )
        mock_display_expanded_insight.assert_called_once_with(
            agent_data["detailed_data"]
        )

    @patch("app.ui.insight_components.display_agent_reasoning")
    @patch("app.ui.insight_components.display_confidence_metric")
    @patch("app.ui.insight_components.display_explanation_markdown")
    @patch("app.ui.insight_components.display_expanded_insight")
    def test_recommendation_agent_insights_display(
        self,
        mock_display_expanded_insight,
        mock_display_explanation_markdown,
        mock_display_confidence_metric,
        mock_display_agent_reasoning,
    ):
        """Test displaying recommendation agent insights."""
        # Setup
        agent_data = {
            "recommendation": "Wait for a better price as costs are trending down.",
            "reasoning": "Our model predicts a 10% drop within the next 2 weeks based on historical patterns.",
            "explanation": "Predicted 10% price decrease in 2 weeks",
            "confidence": 0.75,
            "detailed_data": {
                "best_offer": {
                    "price": 989.99,
                    "store": "BestBuy",
                    "url": "https://example.com/product",
                    "in_stock": True
                },
                "price_trend": "decreasing",
                "store_count": 5
            }
        }
        
        # Execute
        display_agent_insights("Recommendation", agent_data)
        
        # Assert
        mock_display_agent_reasoning.assert_called_once_with(
            "Recommendation", agent_data["reasoning"]
        )
        mock_display_confidence_metric.assert_called_once_with(
            agent_data["confidence"]
        )
        mock_display_explanation_markdown.assert_called_once_with(
            agent_data["explanation"]
        )
        mock_display_expanded_insight.assert_called_once_with(
            agent_data["detailed_data"]
        )

    @patch("streamlit.error")
    @patch("app.ui.insight_components.display_agent_reasoning")
    @patch("app.ui.insight_components.display_confidence_metric")
    def test_handle_missing_agent_data(
        self,
        mock_display_confidence_metric,
        mock_display_agent_reasoning,
        mock_error,
    ):
        """Test handling of missing agent data."""
        # Setup - incomplete data with minimal required fields
        incomplete_data = {
            "analysis": "Prices have been fluctuating.",
            "confidence": 0.5
        }
        
        # Execute
        display_agent_insights("Analysis", incomplete_data)
        
        # Assert
        # Should still display what's available
        mock_display_confidence_metric.assert_called_once_with(0.5)
        # Should not error even when fields are missing
        mock_error.assert_not_called()
