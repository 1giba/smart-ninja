"""
Test the BrightDataPriceScraper functionality.

This module tests the core functionality of the BrightDataPriceScraper,
ensuring it correctly handles scraping operations, HTML parsing, and error conditions.
"""
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import aiohttp
from bs4 import BeautifulSoup

from app.core.scraping.bright_data_scraper import BrightDataPriceScraper


class TestBrightDataScraperFunctionality(unittest.IsolatedAsyncioTestCase):
    """Test suite for BrightDataPriceScraper functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a scraper with mock credentials
        with patch.dict('os.environ', {
            'BRIGHT_DATA_USERNAME': 'test_username',
            'BRIGHT_DATA_PASSWORD': 'test_password'
        }):
            self.scraper = BrightDataPriceScraper()
            self.scraper.username = 'test_username'  # Ensure credentials are set
            self.scraper.password = 'test_password'

        # Sample HTML for testing
        self.sample_html = """
        <html>
            <body>
                <div class="product-container">
                    <h2 class="product-title">Test iPhone 15</h2>
                    <div class="price">$999.99</div>
                    <a href="https://example.com/product">View Details</a>
                </div>
            </body>
        </html>
        """

    @pytest.mark.asyncio
    @patch('app.core.scraping.bright_data_scraper.aiohttp.ClientSession')
    async def test_fetch_html_success(self, mock_session_class):
        """Test successful HTML fetching."""
        # Set up mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=self.sample_html)
        
        # Set up mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Call the method
        result = await self.scraper._fetch_html(
            mock_session, 
            "https://example.com", 
            "http://proxy:1234", 
            aiohttp.ClientTimeout(total=10)
        )
        
        # Verify results
        self.assertEqual(result, self.sample_html)
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.core.scraping.bright_data_scraper.aiohttp.ClientSession')
    async def test_fetch_html_error_status(self, mock_session_class):
        """Test HTML fetching with error status code."""
        # Set up mock response with error status
        mock_response = AsyncMock()
        mock_response.status = 404
        
        # Set up mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Call the method
        result = await self.scraper._fetch_html(
            mock_session, 
            "https://example.com", 
            "http://proxy:1234", 
            aiohttp.ClientTimeout(total=10)
        )
        
        # Verify results
        self.assertEqual(result, "")  # Empty string on error

    @pytest.mark.asyncio
    @patch('app.core.scraping.bright_data_scraper.aiohttp.ClientSession')
    async def test_fetch_html_network_error(self, mock_session_class):
        """Test HTML fetching with network error."""
        # Set up mock session with network error
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(side_effect=aiohttp.ClientError("Network error"))
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        # Call the method
        result = await self.scraper._fetch_html(
            mock_session, 
            "https://example.com", 
            "http://proxy:1234", 
            aiohttp.ClientTimeout(total=10)
        )
        
        # Verify results
        self.assertEqual(result, "")  # Empty string on error

    def test_parse_product_data_success(self):
        """Test successful product data parsing."""
        # Parse sample HTML
        result = self.scraper._parse_product_data(
            self.sample_html, 
            "Example Store", 
            "https://example.com"
        )
        
        # Verify results
        self.assertEqual(len(result), 1)
        product = result[0]
        self.assertEqual(product["title"], "Test iPhone 15")
        self.assertEqual(product["price"], 999.99)
        self.assertEqual(product["currency"], "$")
        self.assertEqual(product["store"], "Example Store")
        self.assertTrue(product["in_stock"])

    def test_parse_product_data_empty_html(self):
        """Test product data parsing with empty HTML."""
        # Parse empty HTML
        result = self.scraper._parse_product_data(
            "", 
            "Example Store", 
            "https://example.com"
        )
        
        # Verify results
        self.assertEqual(len(result), 0)

    def test_extract_store_name(self):
        """Test store name extraction from URL."""
        # Test various URLs
        self.assertEqual(self.scraper._extract_store_name("https://www.amazon.com/s?k=test"), "Amazon")
        self.assertEqual(self.scraper._extract_store_name("https://www.bestbuy.com/site/test"), "Best Buy")
        self.assertEqual(self.scraper._extract_store_name("https://www.walmart.com/search"), "Walmart")
        self.assertEqual(self.scraper._extract_store_name("https://unknown-store.com"), "unknown-store.com")

    @pytest.mark.asyncio
    @patch('app.core.scraping.bright_data_scraper.BrightDataPriceScraper._get_search_urls')
    @patch('app.core.scraping.bright_data_scraper.BrightDataPriceScraper._scrape_single_url')
    @patch('app.core.scraping.bright_data_scraper.aiohttp.ClientSession')
    async def test_scrape_prices_success(self, mock_session_class, mock_scrape_single_url, mock_get_search_urls):
        """Test successful price scraping."""
        # Set up mocks
        mock_get_search_urls.return_value = ["https://example.com/1", "https://example.com/2"]
        mock_scrape_single_url.side_effect = [
            [{"title": "Product 1", "price": 999.99}],
            [{"title": "Product 2", "price": 899.99}]
        ]
        
        # Call the method
        result = await self.scraper.scrape_prices("iPhone 15", "US")
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Product 1")
        self.assertEqual(result[1]["title"], "Product 2")
        self.assertEqual(mock_scrape_single_url.call_count, 2)

    @pytest.mark.asyncio
    @patch('app.core.scraping.bright_data_scraper.BrightDataPriceScraper._get_search_urls')
    @patch('app.core.scraping.bright_data_scraper.aiohttp.ClientSession')
    async def test_scrape_prices_no_urls(self, mock_session_class, mock_get_search_urls):
        """Test price scraping with no search URLs."""
        # Set up mocks
        mock_get_search_urls.return_value = []
        
        # Call the method
        result = await self.scraper.scrape_prices("iPhone 15", "US")
        
        # Verify results
        self.assertEqual(len(result), 0)

    @pytest.mark.asyncio
    @patch('app.core.scraping.bright_data_scraper.BrightDataPriceScraper._get_search_urls')
    @patch('app.core.scraping.bright_data_scraper.BrightDataPriceScraper._scrape_single_url')
    @patch('app.core.scraping.bright_data_scraper.aiohttp.ClientSession')
    async def test_scrape_prices_partial_failure(self, mock_session_class, mock_scrape_single_url, mock_get_search_urls):
        """Test price scraping with some URL failures."""
        # Set up mocks
        mock_get_search_urls.return_value = ["https://example.com/1", "https://example.com/2"]
        mock_scrape_single_url.side_effect = [
            [{"title": "Product 1", "price": 999.99}],
            []  # Empty result represents a failure
        ]
        
        # Call the method
        result = await self.scraper.scrape_prices("iPhone 15", "US")
        
        # Verify results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Product 1")

    @pytest.mark.asyncio
    @patch('app.core.scraping.bright_data_scraper.BrightDataPriceScraper._get_search_urls')
    @patch('app.core.scraping.bright_data_scraper.BrightDataPriceScraper._scrape_single_url')
    @patch('app.core.scraping.bright_data_scraper.aiohttp.ClientSession')
    async def test_scrape_prices_exception_handling(self, mock_session_class, mock_scrape_single_url, mock_get_search_urls):
        """Test price scraping with exceptions in tasks."""
        # Set up mocks
        mock_get_search_urls.return_value = ["https://example.com/1", "https://example.com/2"]
        mock_scrape_single_url.side_effect = [
            [{"title": "Product 1", "price": 999.99}],
            Exception("Scraping error")  # Exception in second task
        ]
        
        # Call the method
        result = await self.scraper.scrape_prices("iPhone 15", "US")
        
        # Verify results - should handle the exception and still return the successful results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Product 1")


if __name__ == "__main__":
    unittest.main()
