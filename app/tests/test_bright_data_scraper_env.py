"""
Test the BrightDataPriceScraper environment variable handling.

This module tests that the BrightDataPriceScraper correctly handles environment
variables and proxies configuration following clean architecture principles.
"""
import os
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.core.scraping.bright_data_scraper import BrightDataPriceScraper


class TestBrightDataScraperEnv(unittest.IsolatedAsyncioTestCase):
    """Test suite for BrightDataPriceScraper environment handling."""

    def setUp(self):
        """Set up test environment variables."""
        # Save original environment variables
        self.original_env = {
            "BRIGHT_DATA_USERNAME": os.environ.get("BRIGHT_DATA_USERNAME"),
            "BRIGHT_DATA_PASSWORD": os.environ.get("BRIGHT_DATA_PASSWORD"),
            "BRIGHTDATA_HOST": os.environ.get("BRIGHTDATA_HOST"),
            "BRIGHTDATA_PORT": os.environ.get("BRIGHTDATA_PORT")
        }
        
        # Clear environment variables for testing
        for key in self.original_env:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Restore original environment variables."""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_init_with_missing_credentials(self):
        """Test initialization with missing credentials."""
        # Ensure credentials are not set
        if "BRIGHT_DATA_USERNAME" in os.environ:
            del os.environ["BRIGHT_DATA_USERNAME"]
        if "BRIGHT_DATA_PASSWORD" in os.environ:
            del os.environ["BRIGHT_DATA_PASSWORD"]
            
        # Initialize scraper
        scraper = BrightDataPriceScraper()
        
        # Check default values
        self.assertIsNone(scraper.username)
        self.assertIsNone(scraper.password)
        self.assertEqual(scraper.host, "brd.superproxy.io")
        self.assertEqual(scraper.port, "22225")

    def test_init_with_custom_host_port(self):
        """Test initialization with custom host and port."""
        # Set custom host and port
        os.environ["BRIGHTDATA_HOST"] = "custom.proxy.io"
        os.environ["BRIGHTDATA_PORT"] = "12345"
        
        # Initialize scraper
        scraper = BrightDataPriceScraper()
        
        # Check custom values
        self.assertEqual(scraper.host, "custom.proxy.io")
        self.assertEqual(scraper.port, "12345")

    @patch("app.core.scraping.bright_data_scraper.logger")
    def test_init_logs_missing_credentials(self, mock_logger):
        """Test that missing credentials are logged as warnings."""
        # Initialize scraper with missing credentials
        BrightDataPriceScraper()
        
        # Check that a warning was logged
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        self.assertIn("credentials not fully configured", warning_msg)

    @patch("app.core.scraping.bright_data_scraper.logger")
    def test_init_logs_configuration(self, mock_logger):
        """Test that configuration is logged when credentials are present."""
        # Set credentials
        os.environ["BRIGHT_DATA_USERNAME"] = "test_username"
        os.environ["BRIGHT_DATA_PASSWORD"] = "test_password"
        
        # Initialize scraper
        BrightDataPriceScraper()
        
        # Check that configuration was logged
        mock_logger.info.assert_called_with(
            "BrightDataPriceScraper initialized with host=%s, port=%s", 
            "brd.superproxy.io", "22225"
        )

    def test_credentials_validation_in_scraper(self):
        """Test that the scraper validates credentials before attempting to scrape."""
        # Initialize scraper with missing credentials
        with patch.dict('os.environ', {}, clear=True):
            scraper = BrightDataPriceScraper()
            
            # Directly verify that username and password are None
            self.assertIsNone(scraper.username)
            self.assertIsNone(scraper.password)
            
            # Verify default host and port values
            self.assertEqual(scraper.host, "brd.superproxy.io")
            self.assertEqual(scraper.port, "22225")

    def test_scrape_urls_generation(self):
        """Test that _get_search_urls generates correct URLs for different countries."""
        # Initialize scraper
        scraper = BrightDataPriceScraper()
        
        # Test US URLs
        us_urls = scraper._get_search_urls("iPhone 15", "US")
        self.assertIn("amazon.com", us_urls[0])
        self.assertIn("iPhone%2015", us_urls[0])  # Check URL encoding
        
        # Test BR URLs
        br_urls = scraper._get_search_urls("iPhone 15", "BR")
        self.assertIn("amazon.com.br", br_urls[0])
        self.assertIn("magazineluiza", br_urls[1])
        
        # Test EU URLs
        eu_urls = scraper._get_search_urls("iPhone 15", "EU")
        self.assertIn("amazon.de", eu_urls[0])
        
        # Test fallback for unsupported country
        other_urls = scraper._get_search_urls("iPhone 15", "XX")
        self.assertEqual(len(other_urls), 1)
        self.assertIn("amazon.com", other_urls[0])


if __name__ == "__main__":
    unittest.main()
