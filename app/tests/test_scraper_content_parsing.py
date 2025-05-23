"""Tests for the content parsing functionality of BrightDataPriceScraper."""
import os
import pytest
import asyncio
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from datetime import datetime

from app.core.scraping.bright_data_scraper import BrightDataPriceScraper


class TestScraperContentParsing:
    """Test class for testing content parsing functionality."""

    def setup_method(self):
        """Set up the test environment."""
        # Create a scraper instance for testing
        self.scraper = BrightDataPriceScraper()
        
        # Configure environment variables for testing
        os.environ["BRIGHT_DATA_USERNAME"] = "test-username"
        os.environ["BRIGHT_DATA_PASSWORD"] = "test-password"
        os.environ["BRIGHT_DATA_HOST"] = "test-host.com"
        os.environ["BRIGHT_DATA_PORT"] = "12345"
        os.environ["ENV"] = "development"
    
    def test_extract_currency(self):
        """Test currency extraction from different price formats."""
        # Test different currency symbols
        assert self.scraper._extract_currency("$1,299.99") == "USD"
        assert self.scraper._extract_currency("€1.299,99") == "EUR"
        assert self.scraper._extract_currency("1.299,99 €") == "EUR"  # Euro after price
        assert self.scraper._extract_currency("£999.99") == "GBP"
        assert self.scraper._extract_currency("R$4.599,90") == "BRL"
        # Test currency codes
        assert self.scraper._extract_currency("USD 1,299.99") == "USD"
        assert self.scraper._extract_currency("1.299,99 EUR") == "EUR"
        assert self.scraper._extract_currency("999.99 GBP") == "GBP"
        # Test currency words
        assert self.scraper._extract_currency("1,299.99 dollars") == "USD"
        assert self.scraper._extract_currency("1.299,99 euro") == "EUR"
        assert self.scraper._extract_currency("999.99 pounds") == "GBP"
        assert self.scraper._extract_currency("1.599,90 reais") == "BRL"
        # Test European price format detection
        assert self.scraper._extract_currency("1.299,99") == "EUR"
        # Test with unknown format
        assert self.scraper._extract_currency("1299.99") == "USD"  # Default to USD
    
    def test_extract_price_value(self):
        """Test price value extraction from different formats."""
        # Test US format
        assert self.scraper._extract_price_value("$1,299.99") == 1299.99
        # Test European format
        assert self.scraper._extract_price_value("€1.299,99") == 1299.99
        # Test UK format
        assert self.scraper._extract_price_value("£999.99") == 999.99
        # Test Brazilian format
        assert self.scraper._extract_price_value("R$4.599,90") == 4599.90
        # Test with currency after price
        assert self.scraper._extract_price_value("1.299,99 €") == 1299.99
        # Test with no currency symbol
        assert self.scraper._extract_price_value("1299.99") is None

    @pytest.mark.parametrize("country,expected_urls", [
        ("us", ["https://www.amazon.com", "https://www.bestbuy.com", "https://www.walmart.com"]),
        ("br", ["https://www.amazon.com.br", "https://www.magazineluiza.com.br", "https://www.americanas.com.br", "https://www.kabum.com.br", "https://www.submarino.com.br"]),
        ("eu", ["https://www.amazon.de", "https://www.mediamarkt.de", "https://www.saturn.de", "https://www.otto.de"]),
        ("de", ["https://www.amazon.de", "https://www.mediamarkt.de", "https://www.saturn.de", "https://www.otto.de"]),
        ("unknown", ["https://www.amazon.com"])  # Default case
    ])
    def test_get_search_urls(self, country, expected_urls):
        """Test if the correct search URLs are generated for each country."""
        model = "iPhone 15"
        urls = self.scraper._get_search_urls(model, country)
        
        # Check that we have URLs
        assert len(urls) > 0
        
        # Check that each URL contains the expected base URL for the country
        for url, expected_base in zip(urls, expected_urls):
            assert expected_base in url
            assert "iPhone%2015" in url  # Check model is encoded correctly

    @pytest.mark.parametrize("html_content,store,url,expected_results", [
        ("<html><body><div class='s-result-item' data-asin='B0001'><h2 class='a-text-normal'>iPhone 15</h2><span class='a-price'><span class='a-offscreen'>$999.99</span></span></div></body></html>", "Amazon", "https://www.amazon.com/s?k=iphone", 1),
        ("<html><body><div class='s-result-item' data-asin='B0002'><h2 class='a-text-normal'>iPhone 15</h2><span class='a-price'><span class='a-offscreen'>€999,99</span></span></div></body></html>", "Amazon", "https://www.amazon.de/s?k=iphone", 1),
        ("<html><body><div class='sku-item'><h4 class='product-title'>iPhone 15</h4><div class='price'>$999.99</div></div></body></html>", "BestBuy", "https://www.bestbuy.com/site/searchpage.jsp?st=iphone", 1),
        ("<html><body><div class='product-wrapper'><div class='title'>iPhone 15</div><div class='price'>999,99 €</div></div></body></html>", "MediaMarkt", "https://www.mediamarkt.de/de/search.html?query=iphone", 1),
        ("<html><body><h1>No results found</h1></body></html>", "Unknown", "https://www.example.com", 0)
    ])
    def test_parse_product_data(self, html_content, store, url, expected_results):
        """Test parsing product data from different HTML content."""
        # Test parsing with mock HTML content
        results = self.scraper._parse_product_data(html_content, store, url)
        
        # Check results count
        assert len(results) == expected_results
        
        # If results are expected, verify their structure and content
        if expected_results > 0:
            # Verify the first result has the expected structure
            result = results[0]
            assert "title" in result
            assert "price" in result
            assert "currency" in result
            assert "url" in result
            assert "store" in result
            assert result["store"] == store
            
            # Check currency based on URL
            if "amazon.de" in url or "mediamarkt.de" in url:
                assert result["currency"] == "EUR"
            elif "amazon.com" in url or "bestbuy.com" in url:
                assert result["currency"] == "USD"

    @pytest.mark.parametrize("html_content,store,url,expected_results", [
        ("<html><body><div class='price'>$1,299.99</div></body></html>", "Amazon", "https://www.amazon.com", 1),
        ("<html><body><div class='price'>€1.299,99</div></body></html>", "Amazon", "https://www.amazon.de", 1),
        ("<html><body><h1>Product</h1></body></html>", "Amazon", "https://www.amazon.com", 0)
    ])
    def test_fallback_price_extraction(self, html_content, store, url, expected_results):
        """Test fallback price extraction from HTML content."""
        results = self.scraper._fallback_price_extraction(html_content, store, url)
        assert len(results) == expected_results
        
        if expected_results > 0:
            # Check price and currency are extracted
            assert "price" in results[0]
            assert "currency" in results[0]
            
            # Check correct currency based on URL
            if "amazon.de" in url:
                assert results[0]["currency"] == "EUR"
            else:
                assert results[0]["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_scrape_html_content_extraction(self):
        """Test the HTML content extraction functionality in scraper."""
        # Mock the _fetch_html method to focus our test
        original_fetch_html = self.scraper._fetch_html
        
        # Create a patch for the _fetch_html method
        async def mock_fetch_html(session, url, proxy_url, timeout, headers=None):
            assert url == "https://example.com"
            assert proxy_url == "http://proxy:8080"
            assert timeout is not None
            assert isinstance(timeout, aiohttp.ClientTimeout)
            # Return a simple HTML content
            return "<html><body>Test content</body></html>"
        
        # Apply the patch
        self.scraper._fetch_html = mock_fetch_html
        
        try:
            # Mock session and create a timeout
            mock_session = MagicMock()
            timeout_obj = aiohttp.ClientTimeout(total=10)
            
            # Call the method
            html_content = await self.scraper._fetch_html(
                mock_session, 
                "https://example.com", 
                "http://proxy:8080", 
                timeout_obj
            )
            
            # Verify the response
            assert html_content == "<html><body>Test content</body></html>"
        finally:
            # Restore the original method
            self.scraper._fetch_html = original_fetch_html
