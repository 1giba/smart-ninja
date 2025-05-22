"""
Unit tests for the price analyzer module.
Tests the implementation of analyzing prices using OpenAI LLM.
"""
import unittest
from unittest.mock import Mock, patch

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import PriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer


class TestPriceAnalyzer(unittest.TestCase):
    """Test suite for the price analyzer module with proper dependency injection"""

    def setUp(self):
        """Set up test dependencies"""
        # Create mocks for dependencies
        self.mock_formatter = Mock(spec=PriceFormatter)
        self.mock_prompt_generator = Mock(spec=PriceAnalysisPromptGenerator)
        self.mock_llm_client = Mock(spec=OpenAIClient)
        self.mock_fallback_analyzer = Mock(spec=FallbackAnalyzer)

        # Sample price data for tests
        self.sample_data = [
            {
                "price": 999.99,
                "date": "2025-05-15",
                "model": "iPhone 15",
                "region": "US",
            },
            {
                "price": 989.99,
                "date": "2025-05-16",
                "model": "iPhone 15",
                "region": "US",
            },
            {
                "price": 979.99,
                "date": "2025-05-17",
                "model": "iPhone 15",
                "region": "US",
            },
        ]

        # Import function under test
        from app.core.ai_agent import analyze_prices

        self.analyze_function = analyze_prices

    def test_analyze_prices_empty_data(self):
        """Test behavior when data is empty"""
        # Set up mocks
        self.mock_formatter.format_price_data.return_value = ""
        self.mock_fallback_analyzer.generate_analysis.return_value = (
            "No price data available for analysis."
        )

        # Test with empty data
        result = self.analyze_function(
            [],
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Assertions
        self.mock_formatter.format_price_data.assert_not_called()
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with([])
        self.assertEqual(result, "No price data available for analysis.")

    def test_analyze_prices_success_path(self):
        """Test the happy path with all components working correctly"""
        # Set up mocks
        self.mock_formatter.format_price_data.return_value = "Formatted price data"
        self.mock_prompt_generator.generate_prompt.return_value = "Analysis prompt"
        self.mock_llm_client.generate_response.return_value = (
            "The prices are decreasing. Good time to buy."
        )

        # Test with sample data
        result = self.analyze_function(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Assertions
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            "Formatted price data"
        )
        self.mock_llm_client.generate_response.assert_called_once_with(
            "Analysis prompt"
        )
        self.mock_fallback_analyzer.generate_analysis.assert_not_called()
        self.assertEqual(result, "The prices are decreasing. Good time to buy.")

    def test_analyze_prices_llm_failure(self):
        """Test behavior when LLM client fails"""
        # Set up mocks
        self.mock_formatter.format_price_data.return_value = "Formatted price data"
        self.mock_prompt_generator.generate_prompt.return_value = "Analysis prompt"
        self.mock_llm_client.generate_response.side_effect = Exception("API error")
        self.mock_fallback_analyzer.generate_analysis.return_value = (
            "Fallback analysis: prices trending down."
        )

        # Test with LLM failure
        result = self.analyze_function(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Assertions
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            "Formatted price data"
        )
        self.mock_llm_client.generate_response.assert_called_once_with(
            "Analysis prompt"
        )
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with(
            self.sample_data
        )
        self.assertEqual(result, "Fallback analysis: prices trending down.")

    def test_analyze_prices_formatter_failure(self):
        """Test behavior when formatter fails"""
        # Set up mocks
        self.mock_formatter.format_price_data.side_effect = Exception(
            "Formatting error"
        )
        self.mock_fallback_analyzer.generate_analysis.return_value = (
            "Fallback analysis: prices trending down."
        )

        # Test with formatter failure
        result = self.analyze_function(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Assertions
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with(
            self.sample_data
        )
        self.assertEqual(result, "Fallback analysis: prices trending down.")


if __name__ == "__main__":
    unittest.main()
