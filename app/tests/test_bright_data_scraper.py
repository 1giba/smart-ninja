"""
Tests for the BrightDataPriceScraper component.

This module tests the functionality of the BrightDataPriceScraper class, focusing on:
1. Proper proxy URL construction with country-specific parameters
2. SSL handling in different environments
3. Compliance with the PriceScraper interface
"""
import asyncio
import os
import ssl
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
import aiohttp

from app.core.scraping.bright_data_scraper import BrightDataPriceScraper
from app.core.scraping.interfaces import PriceScraper


class TestBrightDataPriceScraper:
    """Test suite for the BrightDataPriceScraper class.
    
    Tests the BrightDataPriceScraper implementation to ensure it properly
    constructs proxy URLs with country-specific parameters, handles SSL
    verification correctly in different environments, and adheres to the
    SmartNinja architecture principles.
    """

    def setup_method(self):
        """Set up the test environment before each test.
        
        Saves original environment variables, sets test values, and
        creates a BrightDataPriceScraper instance for testing.
        """
        # Save original environment variables to restore later
        self.original_env = {
            "BRIGHT_DATA_USERNAME": os.environ.get("BRIGHT_DATA_USERNAME"),
            "BRIGHT_DATA_PASSWORD": os.environ.get("BRIGHT_DATA_PASSWORD"),
            "BRIGHT_DATA_HOST": os.environ.get("BRIGHT_DATA_HOST"),
            "BRIGHT_DATA_PORT": os.environ.get("BRIGHT_DATA_PORT"),
            "ENV": os.environ.get("ENV")
        }
        
        # Set test environment variables
        os.environ["BRIGHT_DATA_USERNAME"] = "test-username"
        os.environ["BRIGHT_DATA_PASSWORD"] = "test-password"
        os.environ["BRIGHT_DATA_HOST"] = "test-host.com"
        os.environ["BRIGHT_DATA_PORT"] = "12345"
        os.environ["ENV"] = "development"
        
        # Create scraper instance
        self.scraper = BrightDataPriceScraper()

    def teardown_method(self):
        """Restore the environment after each test."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_implements_interface(self):
        """Test that BrightDataPriceScraper implements PriceScraper interface."""
        assert isinstance(
            self.scraper, PriceScraper
        ), "BrightDataPriceScraper should implement PriceScraper interface"
        
    def test_initialization(self):
        """Test that BrightDataPriceScraper initializes with correct environment variables."""
        assert self.scraper.username == "test-username"
        assert self.scraper.password == "test-password"
        assert self.scraper.host == "test-host.com"
        assert self.scraper.port == "12345"

    def test_scrape_alias(self):
        """Test that the scrape method is an alias for scrape_prices."""
        with patch.object(self.scraper, 'scrape_prices', return_value=[]) as mock_scrape_prices:
            asyncio.run(self.scraper.scrape("test-model", "us", 30))
            mock_scrape_prices.assert_called_once_with("test-model", "us", 30)

    def test_get_search_urls_us(self):
        """Test that the correct search URLs are generated for US country code."""
        urls = self.scraper._get_search_urls("iphone 15", "us")
        assert len(urls) == 4
        assert "amazon.com" in urls[0]
        assert "bestbuy.com" in urls[1]
        assert "walmart.com" in urls[2]
        assert "target.com" in urls[3]
        assert "iphone%2015" in urls[0]

    def test_get_search_urls_br(self):
        """Test that the correct search URLs are generated for Brazil country code."""
        urls = self.scraper._get_search_urls("iphone 15", "br")
        assert len(urls) == 3
        assert "amazon.com.br" in urls[0]
        assert "magazineluiza.com.br" in urls[1]
        assert "americanas.com.br" in urls[2]
        assert "iphone%2015" in urls[0]

    def test_get_search_urls_unsupported_country(self):
        """Test that a default URL is generated for unsupported country codes."""
        urls = self.scraper._get_search_urls("iphone 15", "de")
        assert len(urls) == 1
        assert "amazon.com" in urls[0]
        assert "iphone%2015" in urls[0]

    @pytest.mark.asyncio
    @patch("uuid.uuid4")
    async def test_proxy_url_construction_us(self, mock_uuid):
        """Test that the proxy URL is correctly constructed for US country."""
        # Arrange
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__.return_value = "12345678"
        
        # Use direct patching for _scrape_single_url to capture the proxy URL
        with patch.object(self.scraper, '_scrape_single_url') as mock_scrape:
            mock_scrape.return_value = []
            
            # Mock search URLs
            with patch.object(self.scraper, '_get_search_urls', return_value=["https://example.com"]):
                # Act
                await self.scraper.scrape_prices("iphone 15", "us", 30)
                
                # Assert - Check that _scrape_single_url was called with correct proxy URL
                mock_scrape.assert_called_once()
                args, kwargs = mock_scrape.call_args
                
                # The proxy URL should be the second argument
                proxy_url = args[2]
                
                # Verify proxy URL components
                assert "test-username-country-us" in proxy_url
                assert "session-12345678" in proxy_url
                assert "@test-host.com:12345" in proxy_url
                assert proxy_url.startswith("http://")
                
                # Expected format: http://username-country-us-session-id:password@host:port
                expected_url = f"http://test-username-country-us-session-12345678:test-password@test-host.com:12345"
                assert proxy_url == expected_url

    @pytest.mark.asyncio
    @patch("uuid.uuid4")
    async def test_proxy_url_construction_br(self, mock_uuid):
        """Test that the proxy URL is correctly constructed for Brazil country."""
        # Arrange
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__.return_value = "12345678"
        
        # Use direct patching for _scrape_single_url to capture the proxy URL
        with patch.object(self.scraper, '_scrape_single_url') as mock_scrape:
            mock_scrape.return_value = []
            
            # Mock search URLs
            with patch.object(self.scraper, '_get_search_urls', return_value=["https://example.com"]):
                # Act
                await self.scraper.scrape_prices("iphone 15", "br", 30)
                
                # Assert - Check that _scrape_single_url was called with correct proxy URL
                mock_scrape.assert_called_once()
                args, kwargs = mock_scrape.call_args
                
                # The proxy URL should be the second argument
                proxy_url = args[2]
                
                # Verify proxy URL components
                assert "test-username-country-br" in proxy_url
                assert "session-12345678" in proxy_url
                assert "@test-host.com:12345" in proxy_url
                assert proxy_url.startswith("http://")
                
                # Expected format: http://username-country-br-session-id:password@host:port
                expected_url = f"http://test-username-country-br-session-12345678:test-password@test-host.com:12345"
                assert proxy_url == expected_url

    @pytest.mark.asyncio
    async def test_ssl_handling_in_development(self):
        """Test that SSL verification is correctly disabled in development environment."""
        # Arrange
        os.environ["ENV"] = "development"
        
        # Set up minimal mocks to make the test work without real HTTP requests
        with patch("app.core.scraping.bright_data_scraper._fetch_html", return_value="<html></html>"):
            with patch.object(self.scraper, '_get_search_urls', return_value=["https://example.com"]):
                with patch("app.core.scraping.bright_data_scraper.aiohttp.ClientSession") as mock_session:
                    session_instance = AsyncMock()
                    session_instance.__aenter__.return_value = session_instance
                    session_instance.get = AsyncMock()
                    mock_session.return_value = session_instance
                    
                    # Extract and verify the SSL context setup
                    with patch("app.core.scraping.bright_data_scraper.ssl.create_default_context") as mock_ssl_context:
                        ssl_context = MagicMock()
                        mock_ssl_context.return_value = ssl_context
                        
                        # Act
                        await self.scraper.scrape_prices("iphone 15", "us", 30)
                        
                        # Assert
                        # 1. Verify SSL context was created
                        mock_ssl_context.assert_called_once()
                        
                        # 2. Verify SSL context was configured to disable verification
                        assert ssl_context.check_hostname is False, "check_hostname should be False in development"
                        assert ssl_context.verify_mode == ssl.CERT_NONE, "verify_mode should be CERT_NONE in development"

    @pytest.mark.asyncio
    async def test_ssl_handling_in_production(self):
        """Test that SSL verification is correctly enabled in production environment."""
        # Arrange
        os.environ["ENV"] = "production"
        
        # Mock the actual HTTP request instead of _scrape_single_url
        with patch("app.core.scraping.bright_data_scraper.aiohttp.ClientSession") as mock_session:
            # Setup session mock to return results without making real requests
            session_mock = AsyncMock()
            mock_session.return_value.__aenter__.return_value = session_mock
            
            # Mock the response from get
            response_mock = AsyncMock()
            response_mock.status = 200
            response_mock.text.return_value = "<html><body>Test</body></html>"
            session_mock.get.return_value.__aenter__.return_value = response_mock
            
            # Mock SSL context - should not be called in production
            with patch("app.core.scraping.bright_data_scraper.ssl.create_default_context") as mock_ssl_context:
                # Create a callable for TCPConnector that captures and validates the ssl parameter
                connector_calls = []
                
                def mock_connector_factory(**kwargs):
                    connector_calls.append(kwargs)
                    return MagicMock()
                
                # Mock TCPConnector with our factory
                with patch("app.core.scraping.bright_data_scraper.aiohttp.TCPConnector",
                          side_effect=mock_connector_factory) as mock_connector:
                    
                    # Mock search URLs
                    with patch.object(self.scraper, '_get_search_urls', return_value=["https://example.com"]):
                        # Act
                        await self.scraper.scrape_prices("iphone 15", "us", 30)
                        
                        # Assert - In production, SSL verification should remain enabled
                        mock_ssl_context.assert_not_called()
                        
                        # Verify connector was created with SSL verification enabled
                        assert len(connector_calls) > 0, "TCPConnector was not called"
                        assert 'ssl' in connector_calls[0], "ssl parameter missing in TCPConnector call"
                        assert connector_calls[0]['ssl'] is True, "SSL verification should be enabled in production"


if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
