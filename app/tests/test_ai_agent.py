"""
Unit tests for the refactored AI agent module.
Tests the DI-based implementation of analyzing prices using OpenAI LLM.
"""
import unittest
from unittest.mock import Mock, patch

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import PriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer


class TestAIAgentRefactored(unittest.TestCase):
    """Test suite for the refactored AI agent module with proper dependency injection"""

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

        # Import function under test - we'll mock this in the test_function
        from app.core.ai_agent import analyze_prices

        self.analyze_function = analyze_prices

    def test_analyze_prices_empty_data(self):
        """Test behavior when data is empty"""
        # Set up mocks
        self.mock_formatter.format_price_data.return_value = ""
        self.mock_fallback_analyzer.generate_analysis.return_value = (
            "No price data available for analysis."
        )

        # Call function with empty data
        result = self.analyze_function(
            [],
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify result and interactions
        self.assertEqual(result, "No price data available for analysis.")
        self.mock_formatter.format_price_data.assert_not_called()
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with([])

    def test_analyze_prices_success(self):
        """Test successful response from OpenAI with DI pattern"""
        # Set up mocks
        formatted_data = "Formatted price data: $999.99 (2025-05-15), $989.99 (2025-05-16), $979.99 (2025-05-17)"
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these prices: " + formatted_data
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        ai_response = (
            "Prices are trending downward. Consider waiting for further drops."
        )
        self.mock_llm_client.generate_response.return_value = ai_response

        # Call function with sample data
        result = self.analyze_function(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify result and interactions
        self.assertEqual(result, ai_response)
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            formatted_data
        )
        self.mock_llm_client.generate_response.assert_called_once_with(prompt)
        self.mock_fallback_analyzer.generate_analysis.assert_not_called()

    def test_analyze_prices_client_error(self):
        """Test behavior when LLM client raises an exception"""
        # Set up mocks
        formatted_data = "Formatted price data: $999.99, $989.99, $979.99"
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these prices: " + formatted_data
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        # Simulate API error
        self.mock_llm_client.generate_response.side_effect = Exception("API Error")

        fallback_response = "Prices are showing a slight downward trend."
        self.mock_fallback_analyzer.generate_analysis.return_value = fallback_response

        # Call function with sample data
        result = self.analyze_function(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify fallback was used
        self.assertEqual(result, fallback_response)
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            formatted_data
        )
        self.mock_llm_client.generate_response.assert_called_once_with(prompt)
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with(
            self.sample_data
        )

    def test_analyze_prices_empty_response(self):
        """Test behavior when LLM returns an empty response"""
        # Set up mocks
        formatted_data = "Formatted price data: $999.99"
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these prices: " + formatted_data
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        # Empty response from AI
        self.mock_llm_client.generate_response.return_value = ""

        fallback_response = "Current price information shows stable pricing."
        self.mock_fallback_analyzer.generate_analysis.return_value = fallback_response

        # Call function with sample data
        result = self.analyze_function(
            self.sample_data[:1],
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify fallback was used for empty response
        self.assertEqual(result, fallback_response)
        self.mock_formatter.format_price_data.assert_called_once_with(
            self.sample_data[:1]
        )
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            formatted_data
        )
        self.mock_llm_client.generate_response.assert_called_once_with(prompt)
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with(
            self.sample_data[:1]
        )

    def test_analyze_prices_formatter_error(self):
        """Test behavior when formatter raises an exception"""
        # Set up mocks - formatter fails
        self.mock_formatter.format_price_data.side_effect = Exception(
            "Formatting error"
        )

        fallback_response = "Unable to analyze prices due to data formatting issues."
        self.mock_fallback_analyzer.generate_analysis.return_value = fallback_response

        # Call function with sample data
        result = self.analyze_function(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verify fallback was used and other components weren't called
        self.assertEqual(result, fallback_response)
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with(
            self.sample_data
        )


if __name__ == "__main__":
    unittest.main()
