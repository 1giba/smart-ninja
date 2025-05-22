"""
Tests for the analyze_prices MCP service.

This module tests the functionality of the MCP service that provides price analysis
using async/await patterns for non-blocking operations.
"""
import asyncio
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import PriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer
from app.mcp.analyze_prices.service import create_analyzer_components, analyze_prices_service


class TestAnalyzePricesMCPService(unittest.IsolatedAsyncioTestCase):
    """Test suite for the analyze_prices MCP service with async implementation."""

    def setUp(self):
        """Set up test data"""
        self.sample_prices = [
            {
                "model": "iPhone 15 Pro",
                "region": "US",
                "price": 999.99,
                "currency": "USD",
                "timestamp": "2025-05-01T12:00:00Z",
                "source": "Amazon",
            },
            {
                "model": "iPhone 15 Pro",
                "region": "US",
                "price": 949.99,
                "currency": "USD",
                "timestamp": "2025-05-08T12:00:00Z",
                "source": "BestBuy",
            },
            {
                "model": "iPhone 15 Pro",
                "region": "US",
                "price": 899.99,
                "currency": "USD",
                "timestamp": "2025-05-15T12:00:00Z",
                "source": "Walmart",
            },
        ]

    async def test_analyze_prices_service_with_valid_data(self):
        """Test handling a valid request with price data"""
        # Arrange
        params = {"prices": self.sample_prices}

        # Act
        response = await analyze_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("status", response)
        self.assertIn("message", response)
        self.assertIn("data", response)
        self.assertIn("processing_time_ms", response)
        
        self.assertEqual(response["status"], "success")
        self.assertIn("analysis", response["data"])
        self.assertIsInstance(response["data"]["analysis"], str)
        self.assertTrue(len(response["data"]["analysis"]) > 0)
        
        # Verificar que a análise tem pelo menos 2 sentenças (critério de aceitação)
        sentences = response["data"]["analysis"].split(". ")
        self.assertTrue(
            len([sentence for sentence in sentences if sentence]) >= 2,
            (
                f"A análise deve ter pelo menos 2 sentenças, "
                f"mas tem {len([sentence for sentence in sentences if sentence])}"
            ),
        )

    async def test_analyze_prices_service_with_missing_parameters(self):
        """Test handling a request with missing required parameters"""
        # Arrange
        params = {}

        # Act
        response = await analyze_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("status", response)
        self.assertIn("message", response)
        self.assertIn("data", response)
        self.assertIn("processing_time_ms", response)
        
        self.assertEqual(response["status"], "error")
        self.assertIn("Missing", response["message"])
        self.assertEqual(response["data"], [])

    async def test_analyze_prices_service_with_invalid_prices_parameter(self):
        """Test handling a request with invalid 'prices' parameter"""
        # Arrange
        params = {"prices": "not a list"}

        # Act
        response = await analyze_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("status", response)
        self.assertIn("message", response)
        self.assertIn("data", response)
        self.assertIn("processing_time_ms", response)
        
        self.assertEqual(response["status"], "error")
        self.assertIn("list", response["message"].lower())
        self.assertEqual(response["data"], [])

    async def test_analyze_prices_service_with_empty_prices_list(self):
        """Test handling a request with empty prices list"""
        # Arrange
        params = {"prices": []}

        # Act
        response = await analyze_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("status", response)
        self.assertIn("message", response)
        self.assertIn("data", response)
        self.assertIn("processing_time_ms", response)
        
        self.assertEqual(response["status"], "error")
        self.assertIn("Empty", response["message"])
        self.assertEqual(response["data"], [])

    @patch("app.mcp.analyze_prices.service.create_analyzer_components")
    async def test_with_component_integration(self, mock_create_components):
        """Test integration with the AI agent for price analysis"""
        # Arrange - Setup mocked components
        mock_formatter = Mock(spec=PriceFormatter)
        mock_prompt_generator = Mock(spec=PriceAnalysisPromptGenerator)
        mock_llm_client = AsyncMock(spec=OpenAIClient)
        mock_fallback_analyzer = Mock(spec=FallbackAnalyzer)

        # Configure component behavior
        mock_formatter.format_for_analysis.return_value = "Formatted price data"
        mock_prompt_generator.generate_prompt.return_value = "Analysis prompt"
        
        # Configure async mock with direct result (no Future needed)
        mock_llm_client.generate_text.return_value = "The prices are decreasing. Now is a good time to buy."

        # Set up the mock to return our mocked components directly (no Future needed)
        mock_create_components.return_value = (
            mock_formatter,
            mock_prompt_generator,
            mock_llm_client,
            mock_fallback_analyzer,
        )

        params = {"prices": self.sample_prices}

        # Act
        response = await analyze_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("status", response)
        self.assertIn("message", response)
        self.assertIn("data", response)
        self.assertIn("processing_time_ms", response)
        
        self.assertEqual(response["status"], "success")
        self.assertIn("analysis", response["data"])
        self.assertEqual(
            response["data"]["analysis"],
            "The prices are decreasing. Now is a good time to buy.",
        )

    @unittest.skip("Temporariamente desabilitado durante a migração do FastAPI para módulos async puros")
    @patch("app.mcp.analyze_prices.service.create_analyzer_components")
    async def test_with_llm_error(self, mock_create_components):
        """Test fallback behavior when AI analysis fails"""
        # Arrange - Setup mocked components
        mock_formatter = Mock(spec=PriceFormatter)
        mock_prompt_generator = Mock(spec=PriceAnalysisPromptGenerator)
        mock_llm_client = AsyncMock(spec=OpenAIClient)
        mock_fallback_analyzer = Mock(spec=FallbackAnalyzer)

        # Configure component behavior
        mock_formatter.format_for_analysis.return_value = "Formatted price data"
        mock_prompt_generator.generate_prompt.return_value = "Analysis prompt"
        
        # Configure async mock to raise exception
        mock_llm_client.generate_text.side_effect = Exception("AI service unavailable")
        
        # Configure fallback analyzer
        mock_fallback_analyzer.generate_analysis.return_value = (
            "[FALLBACK ANALYSIS] Analysis with price trends for iPhone"
        )

        # Set up the mock to return our mocked components directly (no Future needed)
        mock_create_components.return_value = (
            mock_formatter,
            mock_prompt_generator,
            mock_llm_client,
            mock_fallback_analyzer,
        )

        params = {"prices": self.sample_prices}

        # Act
        response = await analyze_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("status", response)
        self.assertIn("message", response)
        self.assertIn("data", response)
        self.assertIn("processing_time_ms", response)
        
        self.assertEqual(response["status"], "success")
        self.assertIn("analysis", response["data"])
        self.assertIn("fallback", response["data"]["analysis"].lower())
        self.assertIn("Fallback", response["message"])


if __name__ == "__main__":
    unittest.main()
