"""
Unit tests for the Scraping Agent.
Tests the agent that retrieves raw price data from MCP service.

The tests have been updated to work with the new async implementation
that calls the MCP scrape_prices service.
"""
import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch
from unittest.async_case import IsolatedAsyncioTestCase
from typing import Dict, Any, List

import pytest

from app.core.agents.scraping_agent import ScrapingAgent


class TestScrapingAgent(IsolatedAsyncioTestCase):
    """Test suite for the Scraping Agent implementation"""

    def setUp(self):
        """Set up test dependencies"""
        # Create the scraping agent with a specific timeout for testing
        self.scraping_agent = ScrapingAgent(mcp_timeout=10)

        # Sample planning data for the scraping service
        self.planning_data = {
            "model": "iPhone 15",
            "country": "US",
        }
        
        # Sample test response data (used across multiple tests)
        self.mock_mcp_response = {
            "status": "success",
            "message": "Found 2 results for iPhone 15 in US",
            "data": [
                {
                    "price": 999.99,
                    "store": "Amazon",
                    "region": "US",
                    "model": "iPhone 15",
                    "currency": "USD",
                    "timestamp": "2025-05-17",
                    "url": "https://amazon.com/product/iphone-15",
                },
                {
                    "price": 989.99,
                    "store": "BestBuy",
                    "region": "US",
                    "model": "iPhone 15",
                    "currency": "USD",
                    "timestamp": "2025-05-17",
                    "url": "https://bestbuy.com/product/iphone-15",
                }
            ],
            "processing_time_ms": 1200
        }

    async def test_execute_with_valid_input(self):
        """Test scraping agent execution with valid input"""
        # Mock the scrape_prices_service function to return our mock response
        with patch("app.core.agents.scraping_agent.scrape_prices_service") as mock_service:
            mock_service.return_value = self.mock_mcp_response

            # Execute the agent
            result = await self.scraping_agent.execute(self.planning_data)

            # Verify service was called with the right arguments
            mock_service.assert_called_once()
            args, kwargs = mock_service.call_args
            payload = args[0]
            self.assertEqual(payload["model"], "iPhone 15")
            self.assertEqual(payload["country"], "us")
            self.assertEqual(payload["timeout"], 10)  # Our custom timeout

            # Verify the result contains our mock data
            self.assertEqual(len(result), 2)  # Two mocked results
            self.assertEqual(result[0]["price"], 999.99)
            self.assertEqual(result[1]["price"], 989.99)

    async def test_execute_with_mcp_error_response(self):
        """Test handling of error responses from MCP service"""
        # Create an error response from the MCP service
        error_response = {
            "status": "error",
            "message": "Failed to scrape prices",
            "data": None
        }

        # Mock the scrape_prices_service to return our error response
        with patch("app.core.agents.scraping_agent.scrape_prices_service") as mock_service:
            mock_service.return_value = error_response

            # Execute the agent
            result = await self.scraping_agent.execute(self.planning_data)

            # Should return empty list on MCP service error
            self.assertEqual(result, [])

    async def test_execute_with_missing_model(self):
        """Test scraping agent execution with missing model"""
        # Create input without model
        invalid_input = {"country": "US"}

        # Mock the scrape_prices_service as it should not be called
        with patch("app.core.agents.scraping_agent.scrape_prices_service") as mock_service:
            # Should raise ValueError
            with self.assertRaises(ValueError) as context:
                await self.scraping_agent.execute(invalid_input)

            # Verify the error message
            self.assertIn("model", str(context.exception).lower())

            # Verify service was NOT called
            mock_service.assert_not_called()

    async def test_execute_with_missing_country(self):
        """Test scraping agent execution with missing country"""
        # Create input without country
        invalid_input = {"model": "iPhone 15"}

        # Mock the scrape_prices_service as it should not be called
        with patch("app.core.agents.scraping_agent.scrape_prices_service") as mock_service:
            # Should raise ValueError
            with self.assertRaises(ValueError) as context:
                await self.scraping_agent.execute(invalid_input)

            # Verify the error message
            self.assertIn("country", str(context.exception).lower())

            # Verify service was NOT called
            mock_service.assert_not_called()

    async def test_execute_with_http_error(self):
        """Test handling of errors during scraping"""
        # Mock the scrape_prices_service to raise an exception
        with patch("app.core.agents.scraping_agent.scrape_prices_service") as mock_service:
            mock_service.side_effect = Exception("Service Error")

            # Execute the agent
            result = await self.scraping_agent.execute(self.planning_data)

            # Should return empty list on error
            self.assertEqual(result, [])

    async def test_execute_with_timeout(self):
        """Test handling of timeout during scraping"""
        # Mock the scrape_prices_service to raise a timeout error
        with patch("app.core.agents.scraping_agent.scrape_prices_service") as mock_service:
            mock_service.side_effect = asyncio.TimeoutError()

            # Execute the agent
            result = await self.scraping_agent.execute(self.planning_data)

            # Should return empty list on timeout
            self.assertEqual(result, [])

    async def test_execute_with_empty_result(self):
        """Test handling of empty results from MCP service"""
        # Create a success response but with empty data
        empty_response = {
            "status": "success",
            "message": "No results found",
            "data": []
        }

        # Mock the scrape_prices_service to return the empty response
        with patch("app.core.agents.scraping_agent.scrape_prices_service") as mock_service:
            mock_service.return_value = empty_response

            # Execute the agent
            result = await self.scraping_agent.execute(self.planning_data)

            # Should return empty list from MCP service
            self.assertEqual(result, [])
            mock_service.assert_called_once()

if __name__ == "__main__":
    unittest.main()
