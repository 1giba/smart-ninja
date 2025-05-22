"""Unit tests for the scrape_prices MCP service.

This module tests the functionality and components of the MCP service
that provides smartphone price scraping capabilities.
Supports testing the asynchronous implementation of direct async services.
"""
import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.scraping.bright_data_scraper import BrightDataPriceScraper
from app.core.scraping.error_handler import DefaultScrapingErrorHandler
from app.core.scraping.interfaces import PriceScraper, ResultNormalizer, ScrapingErrorHandler
from app.core.scraping.normalizer import PriceResultNormalizer
from app.mcp.scrape_prices.service import create_scraping_components, scrape_prices_service


class TestScrapePricesMCPService(unittest.TestCase):
    """Test cases for the scrape_prices MCP server."""

    def setUp(self):
        """Set up test fixtures."""
        # Set up an event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.sample_model = "iPhone 13"
        self.sample_country = "us"

        # Sample scraper results
        self.sample_results = [
            {
                "title": "iPhone 13 128GB",
                "price": 799.99,
                "currency": "USD",
                "url": "https://example.com/iphone13",
                "store": "Example Store",
                "date": "2025-05-18",
            },
            {
                "name": "iPhone 13 Pro",
                "price": 999.99,
                "currency": "USD",
                "url": "https://example.com/iphone13pro",
                "source": "Another Store",
                "date": "2025-05-18",
            },
        ]

    def tearDown(self):
        """Clean up after each test."""
        self.loop.close()

    @pytest.mark.asyncio
    @patch("app.mcp.scrape_prices.service.create_scraping_components")
    async def test_scrape_prices_service_with_valid_data(self, mock_create_components):
        """Test handling a request with valid data using DI components asynchronously."""
        # Arrange - Setup mocked components
        mock_scraper = AsyncMock(spec=PriceScraper)
        mock_normalizer = Mock(spec=ResultNormalizer)
        mock_error_handler = Mock(spec=ScrapingErrorHandler)

        # Configure component behavior
        mock_scraper.scrape_prices.return_value = self.sample_results
        mock_normalizer.normalize_results.return_value = [
            {
                "product": "iPhone 13 128GB",
                "price": "$799.99",
                "currency": "USD",
                "link": "https://example.com/iphone13",
                "store": "Example Store",
                "region": "US",
                "date": "2025-05-18",
            },
            {
                "product": "iPhone 13 Pro",
                "price": "$999.99",
                "currency": "USD",
                "link": "https://example.com/iphone13pro",
                "store": "Another Store",
                "region": "US",
                "date": "2025-05-18",
            },
        ]

        # Set up the mock to return our mocked components
        mock_create_components.return_value = (
            mock_scraper,
            mock_normalizer,
            mock_error_handler,
        )

        params = {"model": self.sample_model, "country": self.sample_country}

        # Act
        response = await scrape_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response["data"]), 2)
        mock_scraper.scrape_prices.assert_called_once_with(
            self.sample_model, self.sample_country
        )
        mock_normalizer.normalize_results.assert_called_once_with(
            self.sample_results, self.sample_model, self.sample_country
        )

    @pytest.mark.asyncio
    @patch("app.mcp.scrape_prices.service.create_scraping_components")
    async def test_scrape_prices_service_with_scraping_error(self, mock_create_components):
        """Test handling when the scraper raises an exception asynchronously."""
        # Arrange - Setup mocked components
        mock_scraper = AsyncMock(spec=PriceScraper)
        mock_normalizer = Mock(spec=ResultNormalizer)
        mock_error_handler = Mock(spec=ScrapingErrorHandler)

        # Configure component behavior - Scraper raises exception
        mock_scraper.scrape_prices.side_effect = Exception("Scraping failed")
        mock_error_handler.handle_error.return_value = {
            "status": "error",
            "message": "Failed to scrape prices: Scraping failed",
            "data": [],
        }

        # Set up the mock to return our mocked components
        mock_create_components.return_value = (
            mock_scraper,
            mock_normalizer,
            mock_error_handler,
        )

        params = {"model": self.sample_model, "country": self.sample_country}

        # Act
        response = await scrape_prices_service(params)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertEqual(response["status"], "error")
        self.assertIn("Failed to scrape prices", response["message"])
        self.assertEqual(response["data"], [])
        mock_error_handler.handle_error.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.mcp.scrape_prices.service.BrightDataPriceScraper")
    @patch("app.mcp.scrape_prices.service.PriceResultNormalizer")
    @patch("app.mcp.scrape_prices.service.DefaultScrapingErrorHandler")
    @patch.dict(os.environ, {"BRIGHT_DATA_USERNAME": "test_user", "BRIGHT_DATA_PASSWORD": "test_pass"})
    async def test_create_scraping_components_with_credentials(self, mock_error_handler, mock_normalizer, mock_scraper):
        """Test the creation of scraping components when credentials are available."""
        # Arrange
        mock_scraper_instance = AsyncMock(spec=PriceScraper)
        mock_normalizer_instance = Mock(spec=ResultNormalizer)
        mock_error_handler_instance = Mock(spec=ScrapingErrorHandler)
        
        mock_scraper.return_value = mock_scraper_instance
        mock_normalizer.return_value = mock_normalizer_instance
        mock_error_handler.return_value = mock_error_handler_instance
        
        # Act
        result = await create_scraping_components()
        
        # Assert
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], mock_scraper_instance)
        self.assertEqual(result[1], mock_normalizer_instance)
        self.assertEqual(result[2], mock_error_handler_instance)
        mock_scraper.assert_called_once()
        mock_normalizer.assert_called_once()
        mock_error_handler.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.mcp.scrape_prices.service.create_scraping_components")
    async def test_scrape_prices_service_with_missing_parameters(self, mock_create_components):
        """Test handling a request with missing required parameters asynchronously."""
        # No mocks setup needed as the function should return early

        # Act - Call with missing model
        response = await scrape_prices_service({"country": "us"})

        # Assert
        self.assertIsInstance(response, dict)
        self.assertEqual(response["status"], "error")
        self.assertIn("Missing required parameter", response["message"])


    @pytest.mark.asyncio
    @patch("app.mcp.scrape_prices.service.os.getenv")
    async def test_create_scraping_components_without_credentials(self, mock_getenv):
        """Test that create_scraping_components raises ValueError when credentials are missing."""
        # Arrange - Simulate missing credentials
        def getenv_side_effect(key, default=None):
            if key in ["BRIGHT_DATA_USERNAME", "BRIGHT_DATA_PASSWORD"]:
                return None
            return default
            
        mock_getenv.side_effect = getenv_side_effect
        
        # Act & Assert - Should raise ValueError when credentials aren't available
        with self.assertRaises(ValueError) as context:
            await create_scraping_components()
            
        self.assertIn("Bright Data credentials are required", str(context.exception))


    @pytest.mark.asyncio
    @patch("app.mcp.scrape_prices.service.BrightDataPriceScraper")
    @patch("app.mcp.scrape_prices.service.PriceResultNormalizer")
    @patch("app.mcp.scrape_prices.service.DefaultScrapingErrorHandler")
    @patch.dict(os.environ, {"BRIGHT_DATA_USERNAME": "test_user", "BRIGHT_DATA_PASSWORD": "test_pass"})
    async def test_lazy_loading_bright_data_scraper(self, mock_error_handler, mock_normalizer, mock_scraper):
        """Test that BrightDataPriceScraper is properly lazy-loaded in the create_scraping_components function."""
        # Arrange
        mock_scraper_instance = AsyncMock(spec=PriceScraper)
        mock_scraper.return_value = mock_scraper_instance
        
        # Act
        components = await create_scraping_components()
        scraper = components[0]
        
        # Assert
        self.assertEqual(scraper, mock_scraper_instance)
        mock_scraper.assert_called_once()


    @pytest.mark.asyncio
    @patch("app.mcp.scrape_prices.service.PriceResultNormalizer")
    @patch.dict(os.environ, {"BRIGHT_DATA_USERNAME": "test_user", "BRIGHT_DATA_PASSWORD": "test_pass"})
    async def test_normalizer_component(self, mock_normalizer):
        """Test that the normalizer component is properly initialized and used."""
        # Arrange
        mock_normalizer_instance = Mock(spec=ResultNormalizer)
        test_results = [{"key": "value"}]
        normalized_results = [{"normalized": "data"}]
        
        # Configure mock
        mock_normalizer.return_value = mock_normalizer_instance
        mock_normalizer_instance.normalize_results.return_value = normalized_results
        
        # Use context to avoid actually creating real components for scraper and error_handler
        with patch("app.mcp.scrape_prices.service.BrightDataPriceScraper") as mock_scraper, \
             patch("app.mcp.scrape_prices.service.DefaultScrapingErrorHandler"):
            # Create a mock scraper that returns test results
            mock_scraper_instance = AsyncMock(spec=PriceScraper)
            mock_scraper_instance.scrape_prices.return_value = test_results
            mock_scraper.return_value = mock_scraper_instance
            
            # Act - Create components and simulate scrape_prices_service calling normalizer
            components = await create_scraping_components()
            normalizer = components[1]
            
            # Assert
            self.assertEqual(normalizer, mock_normalizer_instance)
            mock_normalizer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
