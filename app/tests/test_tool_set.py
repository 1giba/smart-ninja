"""
Test cases for the SmartNinjaToolSet interface.
Tests the functionality of the ToolSet interface and implementation.
"""
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import unittest
import asyncio

from app.core.analyzer.interfaces import (
    LLMClient,
    PriceFormatter,
    PromptGenerator,
    RuleBasedAnalyzer,
)
from app.core.interfaces.scraping import IPriceAnalyzer, IPriceScraper, IScraperService
from app.core.interfaces.tool_set import ISmartNinjaToolSet, SmartNinjaToolSet


class TestSmartNinjaToolSet(unittest.IsolatedAsyncioTestCase):
    """Tests for the SmartNinjaToolSet implementation."""
    
    # Using IsolatedAsyncioTestCase to properly test async methods

    async def asyncSetUp(self):
        """Set up test fixtures for each test case."""
        # Create mock scraper service
        self.mock_scraper = AsyncMock(spec=IScraperService)
        self.mock_scraper.get_prices.return_value = [
            {"model": "iPhone 15", "price": 999.99, "currency": "USD"}
        ]
        
        # Create mock price formatter - note: real implementation uses run_in_executor
        self.mock_formatter = MagicMock()
        self.mock_formatter.format_price_data = MagicMock(return_value="Formatted price data")
        
        # Create mock prompt generator - note: real implementation uses run_in_executor
        self.mock_prompt_generator = MagicMock()
        self.mock_prompt_generator.generate_prompt = MagicMock(return_value="Analysis prompt")
        
        # Create mock LLM client
        self.mock_llm_client = MagicMock()
        self.mock_llm_client.generate_response = MagicMock(return_value="Analysis response")
        
        # Create mock rule-based analyzer - note: real implementation is synchronous
        self.mock_rule_analyzer = MagicMock()
        self.mock_rule_analyzer.analyze = MagicMock(return_value="Rule-based analysis")
        
        # Mock analyze_prices_service
        self.analyze_prices_patch = patch('app.core.interfaces.tool_set.analyze_prices_service')
        self.mock_analyze_prices = self.analyze_prices_patch.start()
        self.mock_analyze_prices.return_value = {
            "status": "success",
            "data": {"analysis": "Analysis response"}
        }
        
        # Create the tool set with all mock components
        self.tool_set = SmartNinjaToolSet(
            scraper_service=self.mock_scraper,
            price_formatter=self.mock_formatter,
            prompt_generator=self.mock_prompt_generator,
            llm_client=self.mock_llm_client,
            rule_based_analyzer=self.mock_rule_analyzer,
        )

    async def test_scrape_prices(self):
        """Test the scrape_prices method."""
        # Act
        result = await self.tool_set.scrape_prices("iPhone 15", "US")

        # Assert
        self.mock_scraper.get_prices.assert_awaited_once_with("iPhone 15", "US")
        self.assertEqual(result, [{"model": "iPhone 15", "price": 999.99, "currency": "USD"}])

    async def test_normalize_data(self):
        """Test the normalize_data method."""
        # Arrange
        price_data = [{"model": "iPhone 15", "price": 999.99, "currency": "USD"}]

        # Act
        result = await self.tool_set.normalize_data(price_data)

        # Assert
        # Since we're using a thread pool, we call assert_called_once
        self.mock_formatter.format_price_data.assert_called_once_with(price_data)
        self.assertEqual(result, "Formatted price data")

    async def test_generate_prompt(self):
        """Test the generate_prompt method."""
        # Arrange
        formatted_data = "Formatted price data"

        # Act
        result = await self.tool_set.generate_prompt(formatted_data)

        # Assert
        # Since we're using a thread pool, we call assert_called_once
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(formatted_data)
        self.assertEqual(result, "Analysis prompt")

    async def test_get_ai_analysis(self):
        """Test the get_ai_analysis method."""
        # Arrange
        prompt = "Analysis prompt"

        # Act
        result = await self.tool_set.get_ai_analysis(prompt)

        # Assert
        # This method uses analyze_prices_service directly
        self.mock_analyze_prices.assert_awaited_once()
        self.assertEqual(result, "Analysis response")

    async def test_get_rule_analysis(self):
        """Test the get_rule_analysis method."""
        # Arrange
        price_data = [{"model": "iPhone 15", "price": 999.99, "currency": "USD"}]

        # Act
        result = await self.tool_set.get_rule_analysis(price_data)

        # Assert
        # This is a synchronous method in the real implementation
        self.mock_rule_analyzer.analyze.assert_called_once_with(price_data)
        self.assertEqual(result, "Rule-based analysis")

    async def test_process_price_analysis_end_to_end(self):
        """Test the end-to-end price analysis workflow."""
        # Act
        result = await self.tool_set.process_price_analysis("iPhone 15", "US")

        # Assert
        self.mock_scraper.get_prices.assert_awaited_once_with("iPhone 15", "US")
        # process_price_analysis calls analyze_prices_service directly
        self.mock_analyze_prices.assert_awaited_once()
        self.assertEqual(result, "Analysis response")

    def test_interface_compliance(self):
        """Test that the SmartNinjaToolSet correctly implements the ISmartNinjaToolSet interface."""
        self.assertTrue(issubclass(SmartNinjaToolSet, ISmartNinjaToolSet))
        
    async def asyncTearDown(self):
        """Clean up after each test."""
        self.analyze_prices_patch.stop()
