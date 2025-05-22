"""
Unit tests for the price decision justification feature.

Tests the AI-generated explanations that justify "Buy" or "Wait" decisions
based on price history, variation, and trend comparison.
"""
import unittest
from unittest.mock import Mock, patch

from app.core.ai_agent import analyze_prices_with_justification
from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import PriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer


class TestPriceDecisionJustification(unittest.TestCase):
    """Test suite for the price decision justification module with dependency injection"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mocks for dependencies
        self.mock_formatter = Mock(spec=PriceFormatter)
        self.mock_prompt_generator = Mock(spec=PriceAnalysisPromptGenerator)
        self.mock_llm_client = Mock(spec=OpenAIClient)
        self.mock_fallback_analyzer = Mock(spec=FallbackAnalyzer)

        # Sample data for tests with historical price points
        self.sample_data = [
            {
                "price": 999.99,
                "date": "2025-05-01",
                "model": "iPhone 15",
                "region": "US",
                "store": "Store A",
            },
            {
                "price": 989.99,
                "date": "2025-05-08",
                "model": "iPhone 15",
                "region": "US",
                "store": "Store B",
            },
            {
                "price": 979.99,
                "date": "2025-05-15",
                "model": "iPhone 15",
                "region": "US",
                "store": "Store C",
            },
        ]

    def test_should_include_decision_justification_in_analysis(self):
        """Verifies that price analysis includes decision justification"""
        # Configure mocks
        self.mock_formatter.format_price_data.return_value = "Formatted price data"
        self.mock_prompt_generator.generate_prompt_with_justification.return_value = (
            "Analysis prompt with justification request"
        )
        self.mock_llm_client.generate_response.return_value = """
        Analysis with decision.
        
        DECISION: BUY
        JUSTIFICATION: The price has been steadily decreasing over the past two weeks, showing a 2% drop. 
        Current price is 5% below the 30-day average of $1,029.99.
        """

        # Test the analysis with justification
        result = analyze_prices_with_justification(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify the decision and justification are included
        self.assertIn("DECISION: BUY", result)
        self.assertIn("JUSTIFICATION:", result)
        self.assertIn("5% below the 30-day average", result)

        # Verify the prompt generator was called with the right parameters
        self.mock_prompt_generator.generate_prompt_with_justification.assert_called_once_with(
            "Formatted price data"
        )

        # Verify that trend comparison was requested
        self.mock_llm_client.generate_response.assert_called_once_with(
            "Analysis prompt with justification request"
        )

    def test_should_format_decision_with_trend_comparisons(self):
        """Verifies that decision includes trend comparisons and is properly formatted"""
        # Configure mocks
        self.mock_formatter.format_price_data.return_value = (
            "Formatted price data with history"
        )
        self.mock_prompt_generator.generate_prompt.return_value = (
            "Analysis prompt requesting trend comparisons"
        )
        self.mock_llm_client.generate_response.return_value = """
        Analysis of iPhone 15 prices.
        
        DECISION: WAIT
        JUSTIFICATION: The price is currently 3% above the 7-day average of $950.99.
        Historical data shows prices tend to drop 5-10% in the next month.
        """

        # Test the analysis with justification
        result = analyze_prices_with_justification(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify trend comparisons are included
        self.assertIn("DECISION: WAIT", result)
        self.assertIn("3% above the 7-day average", result)
        self.assertIn("prices tend to drop 5-10%", result)

    def test_should_return_fallback_analysis_with_basic_justification_when_llm_fails(
        self,
    ):
        """Verifies that fallback analysis includes basic justification when LLM fails"""
        # Configure mocks
        self.mock_formatter.format_price_data.return_value = "Formatted price data"
        self.mock_prompt_generator.generate_prompt_with_justification.return_value = (
            "Analysis prompt with justification request"
        )
        self.mock_llm_client.generate_response.side_effect = Exception("API Error")

        # Configure fallback to include basic justification
        self.mock_fallback_analyzer.generate_analysis_with_justification.return_value = """
        [FALLBACK ANALYSIS] Based on the available data for iPhone 15, prices are trending downward.
        
        DECISION: BUY
        JUSTIFICATION: Prices have decreased by 2% over the observed period.
        This suggests it may be a good time to buy.
        """

        # Test with LLM failure
        result = analyze_prices_with_justification(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify fallback includes justification
        self.assertIn("[FALLBACK ANALYSIS]", result)
        self.assertIn("DECISION: BUY", result)
        self.assertIn("JUSTIFICATION:", result)
        self.assertIn("decreased by 2%", result)

        # Verify the correct methods were called
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt_with_justification.assert_called_once_with(
            "Formatted price data"
        )
        self.mock_llm_client.generate_response.assert_called_once_with(
            "Analysis prompt with justification request"
        )
        self.mock_fallback_analyzer.generate_analysis_with_justification.assert_called_once_with(
            self.sample_data
        )

    def test_should_extract_structured_decision_information(self):
        """Verifies that structured decision information can be extracted"""
        # Configure mocks with structured response
        self.mock_formatter.format_price_data.return_value = "Formatted price data"
        self.mock_prompt_generator.generate_prompt_with_justification.return_value = (
            "Analysis prompt with justification request"
        )
        self.mock_llm_client.generate_response.return_value = """
        Analysis of the iPhone 15 pricing data.

        DECISION: BUY
        JUSTIFICATION: 
        - Current price: $979.99
        - 7-day average: $989.99 (0.9% lower)
        - 30-day average: $1,029.99 (4.8% lower)
        - Price trend: Decreasing (2% over two weeks)
        - Market context: New model release expected in 4 months
        
        The current price point represents good value with a consistent downward trend.
        """

        # Test the analysis with structured justification
        result = analyze_prices_with_justification(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify structured information is present
        self.assertIn("Current price:", result)
        self.assertIn("7-day average:", result)
        self.assertIn("30-day average:", result)
        self.assertIn("Price trend:", result)
        self.assertIn("Market context:", result)


if __name__ == "__main__":
    unittest.main()
