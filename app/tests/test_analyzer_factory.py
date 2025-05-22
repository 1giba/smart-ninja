"""
Unit tests for the analyzer factory module.
Tests the factory functions for creating analyzer components and services.
"""
import unittest
from unittest.mock import Mock, patch

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.factory import create_analyzer_service
from app.core.analyzer.formatting.price_formatter import BasicPriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.market_analyzer import MarketRuleBasedAnalyzer
from app.core.analyzer.service import PriceAnalyzerService


class TestAnalyzerFactory(unittest.TestCase):
    """Test suite for the analyzer factory module"""

    def test_create_analyzer_service_default(self):
        """Test creating analyzer service with default components"""
        with patch(
            "app.core.analyzer.factory.get_default_llm_client", create=True
        ) as mock_get_default_client:
            with patch(
                "app.core.scraping.get_default_llm_client"
            ) as mock_get_default_client_actual:
                # Setup mock for the default LLM client
                mock_llm_client = Mock(spec=OpenAIClient)
                mock_get_default_client.return_value = mock_llm_client
                mock_get_default_client_actual.return_value = mock_llm_client

                # Call the factory function with defaults
                analyzer = create_analyzer_service()

                # Verify type and components
                self.assertIsInstance(analyzer, PriceAnalyzerService)
                self.assertIsInstance(analyzer.formatter, BasicPriceFormatter)
                self.assertIsInstance(
                    analyzer.prompt_generator, PriceAnalysisPromptGenerator
                )
                self.assertIsInstance(
                    analyzer.rule_based_analyzer, MarketRuleBasedAnalyzer
                )

    def test_create_analyzer_service_with_custom_components(self):
        """Test creating analyzer service with custom components"""
        # Create mock components
        mock_formatter = Mock(spec=BasicPriceFormatter)
        mock_prompt_generator = Mock(spec=PriceAnalysisPromptGenerator)
        mock_llm_client = Mock(spec=OpenAIClient)
        mock_rule_based_analyzer = Mock(spec=MarketRuleBasedAnalyzer)

        # Call factory with custom components
        analyzer = create_analyzer_service(
            formatter=mock_formatter,
            prompt_generator=mock_prompt_generator,
            llm_client=mock_llm_client,
            rule_based_analyzer=mock_rule_based_analyzer,
        )

        # Verify components are correctly assigned
        self.assertIsInstance(analyzer, PriceAnalyzerService)
        self.assertEqual(analyzer.formatter, mock_formatter)
        self.assertEqual(analyzer.prompt_generator, mock_prompt_generator)
        self.assertEqual(analyzer.llm_client, mock_llm_client)
        self.assertEqual(analyzer.rule_based_analyzer, mock_rule_based_analyzer)

    def test_create_analyzer_with_some_custom_components(self):
        """Test creating analyzer with a mix of default and custom components"""
        # Create some mock components, but not all
        mock_formatter = Mock(spec=BasicPriceFormatter)
        mock_llm_client = Mock(spec=OpenAIClient)

        # Patch the imported function inside the factory module
        with patch(
            "app.core.scraping.get_default_llm_client"
        ) as mock_get_default_client:
            mock_get_default_client.return_value = mock_llm_client

            # Call with partial custom components
            analyzer = create_analyzer_service(formatter=mock_formatter)

            # Verify mix of default and custom components
            self.assertIsInstance(analyzer, PriceAnalyzerService)
            self.assertEqual(analyzer.formatter, mock_formatter)  # Custom
            self.assertIsInstance(
                analyzer.prompt_generator, PriceAnalysisPromptGenerator
            )  # Default
            self.assertIsInstance(
                analyzer.rule_based_analyzer, MarketRuleBasedAnalyzer
            )  # Default

    def test_create_analyzer_with_api_parameters(self):
        """Test that API parameters are correctly passed (if implemented)"""
        # Test that API parameters are properly handled when creating an analyzer
        with patch(
            "app.core.scraping.get_default_llm_client"
        ) as mock_get_default_client:
            # Mock the LLM client
            mock_llm_client = Mock(spec=OpenAIClient)
            mock_get_default_client.return_value = mock_llm_client

            # Call with API parameters
            analyzer = create_analyzer_service(
                api_url="https://test.api", model="test-model", timeout=60
            )

            # Verify the analyzer was created successfully
            self.assertIsInstance(analyzer, PriceAnalyzerService)
